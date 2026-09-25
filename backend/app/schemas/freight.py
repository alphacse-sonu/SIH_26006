"""Freight Rate Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VesselCategory(str, Enum):
    HANDYSIZE = "handysize"
    SUPRAMAX = "supramax"
    PANAMAX = "panamax"
    CAPESIZE = "capesize"


class FreightRateBase(BaseModel):
    vessel_type: VesselCategory
    origin_port_id: int
    destination_port_id: int
    rate_per_ton: float = Field(..., gt=0, description="Rate in USD per metric ton")
    total_cost: Optional[float] = None
    fuel_surcharge: float = 0.0
    currency: str = "USD"


class FreightRateCreate(FreightRateBase):
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class FreightRateResponse(FreightRateBase):
    id: int
    effective_date: datetime
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FreightHistoryBase(BaseModel):
    vessel_type: VesselCategory
    origin_port_id: int
    destination_port_id: int
    rate_per_ton: float
    cargo_volume: Optional[float] = None
    voyage_duration_days: Optional[int] = None
    fuel_price: Optional[float] = None
    market_index: Optional[float] = None
    coal_price: Optional[float] = None
    season: Optional[str] = None
    congestion_level: Optional[float] = None
    record_date: datetime


class FreightHistoryResponse(FreightHistoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FreightTrendResponse(BaseModel):
    vessel_type: VesselCategory
    origin_port_id: int
    destination_port_id: int
    period_days: int
    average_rate: float
    min_rate: float
    max_rate: float
    trend: str  # up, down, stable
    data_points: int
