"""Freight Rate Models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class VesselCategory(str, enum.Enum):
    HANDYSIZE = "handysize"
    SUPRAMAX = "supramax"
    PANAMAX = "panamax"
    CAPESIZE = "capesize"


class FreightRate(Base):
    """Current freight rates for different vessel types and routes"""
    __tablename__ = "freight_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    vessel_type = Column(Enum(VesselCategory), nullable=False)
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    destination_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    rate_per_ton = Column(Float, nullable=False)  # USD per metric ton
    total_cost = Column(Float, nullable=True)  # Total voyage cost
    fuel_surcharge = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    effective_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])


class FreightHistory(Base):
    """Historical freight rate data for ML training"""
    __tablename__ = "freight_history"
    
    id = Column(Integer, primary_key=True, index=True)
    vessel_type = Column(Enum(VesselCategory), nullable=False)
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    destination_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    rate_per_ton = Column(Float, nullable=False)
    cargo_volume = Column(Float, nullable=True)  # Metric tons
    voyage_duration_days = Column(Integer, nullable=True)
    fuel_price = Column(Float, nullable=True)  # USD per ton
    bunker_consumption = Column(Float, nullable=True)  # Tons per day
    market_index = Column(Float, nullable=True)  # Baltic Dry Index or similar
    coal_price = Column(Float, nullable=True)  # Commodity price
    season = Column(String(20), nullable=True)  # monsoon, winter, summer
    congestion_level = Column(Float, nullable=True)  # 0-1 scale
    record_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
