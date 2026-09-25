"""Port and Port Constraint Models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class PortType(str, enum.Enum):
    LOADING = "loading"
    DISCHARGE = "discharge"
    BOTH = "both"


class Country(str, enum.Enum):
    INDIA = "india"
    AUSTRALIA = "australia"
    USA = "usa"
    MOZAMBIQUE = "mozambique"
    INDONESIA = "indonesia"
    RUSSIA = "russia"


class Port(Base):
    """Port information including location and basic details"""
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)  # UN/LOCODE
    country = Column(Enum(Country), nullable=False)
    region = Column(String(100), nullable=True)  # e.g., "East Coast", "Queensland"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    port_type = Column(Enum(PortType), default=PortType.BOTH)
    is_active = Column(Boolean, default=True)
    timezone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    constraints = relationship("PortConstraint", back_populates="port")


class PortConstraint(Base):
    """Port infrastructure constraints and capabilities"""
    __tablename__ = "port_constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(Integer, ForeignKey("ports.id"), nullable=False)
    
    # Physical Constraints
    max_loa = Column(Float, nullable=True)  # Maximum Length Overall (meters)
    max_beam = Column(Float, nullable=True)  # Maximum beam/width (meters)
    max_draft = Column(Float, nullable=True)  # Maximum draft (meters)
    max_dwt = Column(Float, nullable=True)  # Maximum deadweight tonnage
    
    # Operational Constraints
    max_vessel_size = Column(String(50), nullable=True)  # e.g., "capesize", "panamax"
    berth_count = Column(Integer, nullable=True)
    anchorage_capacity = Column(Integer, nullable=True)
    
    # Cargo Handling
    loading_rate = Column(Float, nullable=True)  # Tons per day
    unloading_rate = Column(Float, nullable=True)  # Tons per day
    storage_capacity = Column(Float, nullable=True)  # Metric tons
    cargo_types = Column(String(200), nullable=True)  # Comma-separated: coal, iron ore, etc.
    
    # Tidal Information
    tidal_restriction = Column(Boolean, default=False)
    tidal_window_hours = Column(Float, nullable=True)
    
    # Average Times
    avg_waiting_time_hours = Column(Float, nullable=True)
    avg_turnaround_days = Column(Float, nullable=True)
    
    # Current Status
    current_congestion_level = Column(Float, nullable=True)  # 0-1 scale
    vessels_at_anchorage = Column(Integer, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    port = relationship("Port", back_populates="constraints")
