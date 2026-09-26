"""Analytics Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DashboardSummary(BaseModel):
    latest_rates: Dict[str, float]
    rate_changes_30d: Dict[str, float]
    congested_ports_count: int
    active_routes_count: int
    last_updated: datetime


class VesselTypeMarketData(BaseModel):
    current_rate: float
    avg_rate: float
    min_rate: float
    max_rate: float
    volatility: float


class MarketOverview(BaseModel):
    period_days: int
    vessel_type_data: Dict[str, Dict[str, float]]
    market_sentiment: str  # bullish, bearish, neutral
    analysis_date: datetime


class RouteAnalytics(BaseModel):
    origin_port_id: int
    destination_port_id: int
    route_name: Optional[str]
    distance_nm: Optional[float]
    period_days: int
    vessel_analytics: Dict[str, Dict[str, Any]]
    total_data_points: int


class CongestionReport(BaseModel):
    port_id: int
    port_name: str
    country: str
    region: Optional[str]
    congestion_level: float
    vessels_waiting: int
    avg_waiting_hours: float
    status: str  # low, medium, high


class SeasonalAnalysis(BaseModel):
    vessel_type: str
    origin_port_id: int
    destination_port_id: int
    monthly_averages: Dict[int, float]
    peak_months: List[int]
    low_months: List[int]
    recommendation: str


class IdleScenarioAnalysis(BaseModel):
    vessel_type: str
    current_utilization: float
    predicted_idle_periods: List[Dict[str, Any]]
    repositioning_suggestions: List[Dict[str, Any]]
    cost_savings_potential: float
