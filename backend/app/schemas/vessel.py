"""Vessel Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VesselStatus(str, Enum):
    AVAILABLE = "available"
    CHARTERED = "chartered"
    IN_TRANSIT = "in_transit"
    AT_PORT = "at_port"
    MAINTENANCE = "maintenance"


class VesselTypeBase(BaseModel):
    name: str = Field(..., max_length=50)
    min_dwt: float
    max_dwt: float
    typical_dwt: Optional[float] = None
    typical_loa: Optional[float] = None
    typical_beam: Optional[float] = None
    typical_draft: Optional[float] = None
    speed_knots: Optional[float] = None
    fuel_consumption_per_day: Optional[float] = None
    cargo_capacity: Optional[float] = None
    daily_charter_rate_low: Optional[float] = None
    daily_charter_rate_high: Optional[float] = None
    operating_cost_per_day: Optional[float] = None
    suitable_for_coal: bool = True
    suitable_for_iron_ore: bool = True
    suitable_for_grain: bool = True


class VesselTypeCreate(VesselTypeBase):
    pass


class VesselTypeResponse(VesselTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VesselBase(BaseModel):
    name: str = Field(..., max_length=100)
    imo_number: Optional[str] = None
    vessel_type: str
    dwt: float
    loa: Optional[float] = None
    beam: Optional[float] = None
    draft: Optional[float] = None
    year_built: Optional[int] = None
    flag: Optional[str] = None
    status: VesselStatus = VesselStatus.AVAILABLE
    current_location: Optional[str] = None
    next_available_date: Optional[datetime] = None
    current_charter_rate: Optional[float] = None
    charter_type: Optional[str] = None


class VesselCreate(VesselBase):
    pass


class VesselResponse(VesselBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VesselOptimizationRequest(BaseModel):
    cargo_volume: float = Field(..., gt=0, description="Cargo volume in metric tons")
    origin_port_id: int
    destination_port_id: int
    cargo_type: Optional[str] = "coal"
    preferred_vessel_types: Optional[List[str]] = None


class VesselRecommendation(BaseModel):
    vessel_type: str
    score: float
    issues: List[str]
    estimated_cost: Optional[float]
    capacity_utilization: Optional[float]


class VesselOptimizationResponse(BaseModel):
    cargo_volume: float
    origin_port_id: int
    destination_port_id: int
    recommendations: List[Dict[str, Any]]
    best_choice: Optional[str]
