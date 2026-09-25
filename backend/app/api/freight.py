"""Freight Rates API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.freight import FreightRate, FreightHistory, VesselCategory
from app.schemas.freight import (
    FreightRateResponse,
    FreightRateCreate,
    FreightHistoryResponse,
    FreightTrendResponse
)

router = APIRouter()


@router.get("/rates", response_model=List[FreightRateResponse])
async def get_freight_rates(
    vessel_type: Optional[VesselCategory] = None,
    origin_port_id: Optional[int] = None,
    destination_port_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get current freight rates with optional filters"""
    query = db.query(FreightRate)
    
    if vessel_type:
        query = query.filter(FreightRate.vessel_type == vessel_type)
    if origin_port_id:
        query = query.filter(FreightRate.origin_port_id == origin_port_id)
    if destination_port_id:
        query = query.filter(FreightRate.destination_port_id == destination_port_id)
    
    rates = query.offset(skip).limit(limit).all()
    return rates


@router.get("/rates/{rate_id}", response_model=FreightRateResponse)
async def get_freight_rate(rate_id: int, db: Session = Depends(get_db)):
    """Get a specific freight rate by ID"""
    rate = db.query(FreightRate).filter(FreightRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Freight rate not found")
    return rate


@router.post("/rates", response_model=FreightRateResponse)
async def create_freight_rate(
    rate_data: FreightRateCreate,
    db: Session = Depends(get_db)
):
    """Create a new freight rate entry"""
    rate = FreightRate(**rate_data.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/history", response_model=List[FreightHistoryResponse])
async def get_freight_history(
    vessel_type: Optional[VesselCategory] = None,
    origin_port_id: Optional[int] = None,
    destination_port_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get historical freight rate data"""
    query = db.query(FreightHistory)
    
    if vessel_type:
        query = query.filter(FreightHistory.vessel_type == vessel_type)
    if origin_port_id:
        query = query.filter(FreightHistory.origin_port_id == origin_port_id)
    if destination_port_id:
        query = query.filter(FreightHistory.destination_port_id == destination_port_id)
    if start_date:
        query = query.filter(FreightHistory.record_date >= start_date)
    if end_date:
        query = query.filter(FreightHistory.record_date <= end_date)
    
    history = query.order_by(FreightHistory.record_date.desc()).offset(skip).limit(limit).all()
    return history


@router.get("/trends", response_model=FreightTrendResponse)
async def get_freight_trends(
    vessel_type: VesselCategory,
    origin_port_id: int,
    destination_port_id: int,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """Get freight rate trends for a specific route"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(FreightHistory).filter(
        FreightHistory.vessel_type == vessel_type,
        FreightHistory.origin_port_id == origin_port_id,
        FreightHistory.destination_port_id == destination_port_id,
        FreightHistory.record_date >= start_date
    ).order_by(FreightHistory.record_date).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="No historical data found for this route")
    
    rates = [h.rate_per_ton for h in history]
    dates = [h.record_date for h in history]
    
    avg_rate = sum(rates) / len(rates)
    min_rate = min(rates)
    max_rate = max(rates)
    
    # Calculate trend
    if len(rates) >= 2:
        recent_avg = sum(rates[-7:]) / len(rates[-7:])
        older_avg = sum(rates[:7]) / len(rates[:7])
        trend = "up" if recent_avg > older_avg * 1.02 else "down" if recent_avg < older_avg * 0.98 else "stable"
    else:
        trend = "stable"
    
    return FreightTrendResponse(
        vessel_type=vessel_type,
        origin_port_id=origin_port_id,
        destination_port_id=destination_port_id,
        period_days=days,
        average_rate=avg_rate,
        min_rate=min_rate,
        max_rate=max_rate,
        trend=trend,
        data_points=len(rates)
    )
