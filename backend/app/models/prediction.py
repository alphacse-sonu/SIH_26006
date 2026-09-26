"""Prediction and Forecast Models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class PredictionType(str, enum.Enum):
    FREIGHT_RATE = "freight_rate"
    MARKET_ENTRY = "market_entry"
    VESSEL_OPTIMIZATION = "vessel_optimization"
    CONGESTION = "congestion"
    RISK_ASSESSMENT = "risk_assessment"


class Prediction(Base):
    """Prediction requests and metadata"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_type = Column(Enum(PredictionType), nullable=False)
    
    # Request Parameters
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    destination_port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    vessel_type = Column(String(50), nullable=True)
    cargo_volume = Column(Float, nullable=True)  # Metric tons
    target_date = Column(DateTime, nullable=True)
    forecast_horizon_days = Column(Integer, default=30)
    
    # Model Information
    model_version = Column(String(50), nullable=True)
    model_accuracy = Column(Float, nullable=True)
    
    # Request Metadata
    user_id = Column(String(100), nullable=True)
    request_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
    results = relationship("PredictionResult", back_populates="prediction")


class PredictionResult(Base):
    """Prediction results and forecasts"""
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    
    # Forecast Values
    forecast_date = Column(DateTime, nullable=False)
    predicted_rate = Column(Float, nullable=False)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    confidence_level = Column(Float, default=0.95)
    
    # Additional Insights
    trend_direction = Column(String(20), nullable=True)  # up, down, stable
    volatility_score = Column(Float, nullable=True)  # 0-1 scale
    
    # Recommendations
    recommendation = Column(String(500), nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    optimal_entry_score = Column(Float, nullable=True)  # 0-100 score
    
    # Feature Importance (for explainability)
    feature_importance = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prediction = relationship("Prediction", back_populates="results")
