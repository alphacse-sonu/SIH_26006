"""Vessel and Vessel Type Models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum
from datetime import datetime
import enum

from app.database import Base


class VesselStatus(str, enum.Enum):
    AVAILABLE = "available"
    CHARTERED = "chartered"
    IN_TRANSIT = "in_transit"
    AT_PORT = "at_port"
    MAINTENANCE = "maintenance"


class VesselType(Base):
    """Vessel type specifications and characteristics"""
    __tablename__ = "vessel_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)  # handysize, supramax, etc.
    
    # Size Specifications
    min_dwt = Column(Float, nullable=False)  # Minimum deadweight tonnage
    max_dwt = Column(Float, nullable=False)  # Maximum deadweight tonnage
    typical_dwt = Column(Float, nullable=True)  # Typical/average DWT
    
    # Dimensions
    typical_loa = Column(Float, nullable=True)  # Typical Length Overall (meters)
    typical_beam = Column(Float, nullable=True)  # Typical beam (meters)
    typical_draft = Column(Float, nullable=True)  # Typical draft (meters)
    
    # Operational Characteristics
    speed_knots = Column(Float, nullable=True)  # Average speed in knots
    fuel_consumption_per_day = Column(Float, nullable=True)  # Tons per day
    cargo_capacity = Column(Float, nullable=True)  # Cubic meters
    
    # Cost Factors
    daily_charter_rate_low = Column(Float, nullable=True)  # USD per day (low market)
    daily_charter_rate_high = Column(Float, nullable=True)  # USD per day (high market)
    operating_cost_per_day = Column(Float, nullable=True)  # USD per day
    
    # Suitability
    suitable_for_coal = Column(Boolean, default=True)
    suitable_for_iron_ore = Column(Boolean, default=True)
    suitable_for_grain = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Vessel(Base):
    """Individual vessel information"""
    __tablename__ = "vessels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    imo_number = Column(String(20), nullable=True, unique=True)
    vessel_type = Column(String(50), nullable=False)
    
    # Specifications
    dwt = Column(Float, nullable=False)
    loa = Column(Float, nullable=True)
    beam = Column(Float, nullable=True)
    draft = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    flag = Column(String(50), nullable=True)
    
    # Current Status
    status = Column(Enum(VesselStatus), default=VesselStatus.AVAILABLE)
    current_location = Column(String(100), nullable=True)
    next_available_date = Column(DateTime, nullable=True)
    
    # Charter Information
    current_charter_rate = Column(Float, nullable=True)
    charter_type = Column(String(50), nullable=True)  # spot, short-term, long-term
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
