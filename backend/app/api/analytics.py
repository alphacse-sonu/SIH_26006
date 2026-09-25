"""Analytics API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.freight import FreightHistory, VesselCategory
from app.models.port import Port, PortConstraint
from app.models.route import Route, TradeRoute
from app.schemas.analytics import (
    DashboardSummary,
    RouteAnalytics,
    MarketOverview,
    CongestionReport,
    SeasonalAnalysis
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary with key metrics"""
    # Get latest rates by vessel type
    latest_rates = {}
    for vessel_type in VesselCategory:
        latest = db.query(FreightHistory).filter(
            FreightHistory.vessel_type == vessel_type
        ).order_by(FreightHistory.record_date.desc()).first()
        
        if latest:
            latest_rates[vessel_type.value] = latest.rate_per_ton
    
    # Get 30-day rate changes
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    rate_changes = {}
    
    for vessel_type in VesselCategory:
        current = db.query(func.avg(FreightHistory.rate_per_ton)).filter(
            FreightHistory.vessel_type == vessel_type,
            FreightHistory.record_date >= datetime.utcnow() - timedelta(days=7)
        ).scalar()
        
        previous = db.query(func.avg(FreightHistory.rate_per_ton)).filter(
            FreightHistory.vessel_type == vessel_type,
            FreightHistory.record_date >= thirty_days_ago,
            FreightHistory.record_date < datetime.utcnow() - timedelta(days=7)
        ).scalar()
        
        if current and previous:
            change = ((current - previous) / previous) * 100
            rate_changes[vessel_type.value] = round(change, 2)
    
    # Get port congestion summary
    congested_ports = db.query(PortConstraint).filter(
        PortConstraint.current_congestion_level > 0.7
    ).count()
    
    # Get active routes count
    active_routes = db.query(Route).count()
    
    return DashboardSummary(
        latest_rates=latest_rates,
        rate_changes_30d=rate_changes,
        congested_ports_count=congested_ports,
        active_routes_count=active_routes,
        last_updated=datetime.utcnow()
    )


@router.get("/market-overview", response_model=MarketOverview)
async def get_market_overview(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """Get overall market overview and trends"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Calculate market indices
    market_data = {}
    
    for vessel_type in VesselCategory:
        history = db.query(FreightHistory).filter(
            FreightHistory.vessel_type == vessel_type,
            FreightHistory.record_date >= start_date
        ).order_by(FreightHistory.record_date).all()
        
        if history:
            rates = [h.rate_per_ton for h in history]
            market_data[vessel_type.value] = {
                "current_rate": rates[-1] if rates else 0,
                "avg_rate": sum(rates) / len(rates),
                "min_rate": min(rates),
                "max_rate": max(rates),
                "volatility": (max(rates) - min(rates)) / (sum(rates) / len(rates)) * 100 if rates else 0
            }
    
    # Determine overall market sentiment
    total_change = 0
    count = 0
    for vessel_type, data in market_data.items():
        if data["avg_rate"] > 0:
            recent_vs_avg = (data["current_rate"] - data["avg_rate"]) / data["avg_rate"]
            total_change += recent_vs_avg
            count += 1
    
    avg_change = total_change / count if count > 0 else 0
    
    if avg_change > 0.05:
        sentiment = "bullish"
    elif avg_change < -0.05:
        sentiment = "bearish"
    else:
        sentiment = "neutral"
    
    return MarketOverview(
        period_days=days,
        vessel_type_data=market_data,
        market_sentiment=sentiment,
        analysis_date=datetime.utcnow()
    )


@router.get("/route/{origin_port_id}/{destination_port_id}", response_model=RouteAnalytics)
async def get_route_analytics(
    origin_port_id: int,
    destination_port_id: int,
    days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific route"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get route info
    route = db.query(Route).filter(
        Route.origin_port_id == origin_port_id,
        Route.destination_port_id == destination_port_id
    ).first()
    
    # Get historical data
    history = db.query(FreightHistory).filter(
        FreightHistory.origin_port_id == origin_port_id,
        FreightHistory.destination_port_id == destination_port_id,
        FreightHistory.record_date >= start_date
    ).order_by(FreightHistory.record_date).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="No data found for this route")
    
    # Calculate analytics by vessel type
    vessel_analytics = {}
    for vessel_type in VesselCategory:
        vessel_history = [h for h in history if h.vessel_type == vessel_type]
        if vessel_history:
            rates = [h.rate_per_ton for h in vessel_history]
            vessel_analytics[vessel_type.value] = {
                "avg_rate": sum(rates) / len(rates),
                "min_rate": min(rates),
                "max_rate": max(rates),
                "data_points": len(rates)
            }
    
    return RouteAnalytics(
        origin_port_id=origin_port_id,
        destination_port_id=destination_port_id,
        route_name=route.route_name if route else None,
        distance_nm=route.distance_nm if route else None,
        period_days=days,
        vessel_analytics=vessel_analytics,
        total_data_points=len(history)
    )


@router.get("/congestion", response_model=List[CongestionReport])
async def get_congestion_report(
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get port congestion report"""
    query = db.query(Port, PortConstraint).join(
        PortConstraint, Port.id == PortConstraint.port_id
    )
    
    if region:
        query = query.filter(Port.region.ilike(f"%{region}%"))
    
    results = query.all()
    
    reports = []
    for port, constraint in results:
        reports.append(CongestionReport(
            port_id=port.id,
            port_name=port.name,
            country=port.country.value,
            region=port.region,
            congestion_level=constraint.current_congestion_level or 0,
            vessels_waiting=constraint.vessels_at_anchorage or 0,
            avg_waiting_hours=constraint.avg_waiting_time_hours or 0,
            status="high" if (constraint.current_congestion_level or 0) > 0.7 else "medium" if (constraint.current_congestion_level or 0) > 0.4 else "low"
        ))
    
    # Sort by congestion level
    reports.sort(key=lambda x: x.congestion_level, reverse=True)
    
    return reports


@router.get("/seasonal", response_model=SeasonalAnalysis)
async def get_seasonal_analysis(
    vessel_type: VesselCategory,
    origin_port_id: int,
    destination_port_id: int,
    db: Session = Depends(get_db)
):
    """Get seasonal analysis for freight rates"""
    # Get all historical data
    history = db.query(FreightHistory).filter(
        FreightHistory.vessel_type == vessel_type,
        FreightHistory.origin_port_id == origin_port_id,
        FreightHistory.destination_port_id == destination_port_id
    ).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="No historical data found")
    
    # Group by month
    monthly_data = {i: [] for i in range(1, 13)}
    for h in history:
        month = h.record_date.month
        monthly_data[month].append(h.rate_per_ton)
    
    # Calculate monthly averages
    monthly_averages = {}
    for month, rates in monthly_data.items():
        if rates:
            monthly_averages[month] = sum(rates) / len(rates)
    
    # Identify peak and low seasons
    if monthly_averages:
        avg_values = list(monthly_averages.values())
        overall_avg = sum(avg_values) / len(avg_values)
        
        peak_months = [m for m, v in monthly_averages.items() if v > overall_avg * 1.1]
        low_months = [m for m, v in monthly_averages.items() if v < overall_avg * 0.9]
    else:
        peak_months = []
        low_months = []
    
    return SeasonalAnalysis(
        vessel_type=vessel_type.value,
        origin_port_id=origin_port_id,
        destination_port_id=destination_port_id,
        monthly_averages=monthly_averages,
        peak_months=peak_months,
        low_months=low_months,
        recommendation=f"Consider chartering during months {low_months} for lower rates" if low_months else "No clear seasonal pattern detected"
    )
