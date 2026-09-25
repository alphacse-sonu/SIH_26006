"""Prediction Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PredictionType(str, Enum):
    FREIGHT_RATE = "freight_rate"
    MARKET_ENTRY = "market_entry"
    VESSEL_OPTIMIZATION = "vessel_optimization"
    CONGESTION = "congestion"
    RISK_ASSESSMENT = "risk_assessment"


class FreightForecastRequest(BaseModel):
    vessel_type: str
    origin_port_id: int
    destination_port_id: int
    forecast_days: int = Field(30, ge=7, le=180)
    cargo_volume: Optional[float] = None


class ForecastPoint(BaseModel):
    date: datetime
    predicted_rate: float
    confidence_lower: float
    confidence_upper: float
    trend: str
    recommendation: Optional[str] = None


class FreightForecastResponse(BaseModel):
    prediction_id: int
    vessel_type: str
    origin_port_id: int
    destination_port_id: int
    forecasts: List[Dict[str, Any]]
    model_version: str
    processing_time_ms: int


class MarketEntryRequest(BaseModel):
    vessel_type: str
    origin_port_id: int
    destination_port_id: int
    contract_duration_days: int = Field(30, ge=7, le=365)
    target_start_date: Optional[datetime] = None
    budget_per_ton: Optional[float] = None


class MarketEntryWindow(BaseModel):
    start_date: datetime
    end_date: datetime
    expected_rate: float
    confidence: float
    recommendation: str


class MarketEntryResponse(BaseModel):
    prediction_id: int
    vessel_type: str
    origin_port_id: int
    destination_port_id: int
    current_rate: float
    predicted_rate_30d: float
    optimal_entry_windows: List[Dict[str, Any]]
    market_trend: str
    recommendation: str
    confidence_score: float


class RiskFactor(BaseModel):
    factor: str
    level: str  # low, medium, high
    description: str
    mitigation: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    origin_port_id: int
    destination_port_id: int
    vessel_type: str
    voyage_date: datetime
    overall_risk_level: str
    risk_score: float  # 0-100
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    weather_risk: str
    congestion_risk: str
    market_volatility_risk: str


class PredictionResultResponse(BaseModel):
    id: int
    forecast_date: datetime
    predicted_rate: float
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    trend_direction: Optional[str]
    recommendation: Optional[str]
    
    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    id: int
    prediction_type: PredictionType
    origin_port_id: Optional[int]
    destination_port_id: Optional[int]
    vessel_type: Optional[str]
    cargo_volume: Optional[float]
    target_date: Optional[datetime]
    forecast_horizon_days: int
    model_version: Optional[str]
    request_timestamp: datetime
    processing_time_ms: Optional[int]
    results: Optional[List[PredictionResultResponse]] = None
    
    class Config:
        from_attributes = True
