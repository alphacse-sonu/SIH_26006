"""Port Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PortType(str, Enum):
    LOADING = "loading"
    DISCHARGE = "discharge"
    BOTH = "both"


class Country(str, Enum):
    INDIA = "india"
    AUSTRALIA = "australia"
    USA = "usa"
    MOZAMBIQUE = "mozambique"
    INDONESIA = "indonesia"
    RUSSIA = "russia"


class PortBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)
    country: Country
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    port_type: PortType = PortType.BOTH
    timezone: Optional[str] = None


class PortCreate(PortBase):
    is_active: bool = True


class PortResponse(PortBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortConstraintBase(BaseModel):
    max_loa: Optional[float] = Field(None, description="Maximum Length Overall in meters")
    max_beam: Optional[float] = Field(None, description="Maximum beam in meters")
    max_draft: Optional[float] = Field(None, description="Maximum draft in meters")
    max_dwt: Optional[float] = Field(None, description="Maximum deadweight tonnage")
    max_vessel_size: Optional[str] = None
    berth_count: Optional[int] = None
    anchorage_capacity: Optional[int] = None
    loading_rate: Optional[float] = Field(None, description="Tons per day")
    unloading_rate: Optional[float] = Field(None, description="Tons per day")
    storage_capacity: Optional[float] = None
    cargo_types: Optional[str] = None
    tidal_restriction: bool = False
    tidal_window_hours: Optional[float] = None
    avg_waiting_time_hours: Optional[float] = None
    avg_turnaround_days: Optional[float] = None
    current_congestion_level: Optional[float] = Field(None, ge=0, le=1)
    vessels_at_anchorage: Optional[int] = None


class PortConstraintCreate(PortConstraintBase):
    pass


class PortConstraintResponse(PortConstraintBase):
    id: int
    port_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortDetailResponse(PortResponse):
    constraints: Optional[List[PortConstraintResponse]] = None
    
    class Config:
        from_attributes = True
