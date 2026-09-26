"""Route and Trade Route Models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Route(Base):
    """Shipping routes between ports"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    destination_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    
    # Distance and Time
    distance_nm = Column(Float, nullable=False)  # Nautical miles
    typical_duration_days = Column(Float, nullable=True)
    
    # Route Characteristics
    route_name = Column(String(100), nullable=True)  # e.g., "Australia-India East Coast"
    via_points = Column(String(500), nullable=True)  # Key waypoints
    
    # Seasonal Factors
    monsoon_impact = Column(Float, nullable=True)  # Additional days during monsoon
    winter_impact = Column(Float, nullable=True)  # Additional days during winter
    
    # Risk Factors
    piracy_risk_level = Column(Float, nullable=True)  # 0-1 scale
    weather_risk_level = Column(Float, nullable=True)  # 0-1 scale
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])


class TradeRoute(Base):
    """Trade route statistics and analytics"""
    __tablename__ = "trade_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    
    # Volume Statistics
    avg_monthly_volume = Column(Float, nullable=True)  # Metric tons
    peak_season_months = Column(String(50), nullable=True)  # e.g., "Oct,Nov,Dec"
    
    # Rate Statistics
    avg_freight_rate = Column(Float, nullable=True)
    rate_volatility = Column(Float, nullable=True)  # Standard deviation
    
    # Market Share
    market_share_percentage = Column(Float, nullable=True)
    major_charterers = Column(String(500), nullable=True)
    
    # Historical Performance
    on_time_percentage = Column(Float, nullable=True)
    avg_delay_days = Column(Float, nullable=True)
    
    record_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    route = relationship("Route")
