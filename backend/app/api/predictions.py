"""Predictions API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import time

from app.database import get_db
from app.models.prediction import Prediction, PredictionResult, PredictionType
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    FreightForecastRequest,
    FreightForecastResponse,
    MarketEntryRequest,
    MarketEntryResponse,
    RiskAssessmentResponse
)
from app.ml.predictor import FreightPredictor

router = APIRouter()

# Initialize predictor
predictor = FreightPredictor()


@router.post("/freight-forecast", response_model=FreightForecastResponse)
async def forecast_freight_rates(
    request: FreightForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate freight rate forecast for specified route and vessel type"""
    start_time = time.time()
    
    try:
        # Generate predictions
        forecasts = predictor.predict_freight_rates(
            vessel_type=request.vessel_type,
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            forecast_days=request.forecast_days,
            cargo_volume=request.cargo_volume
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Store prediction in database
        prediction = Prediction(
            prediction_type=PredictionType.FREIGHT_RATE,
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            vessel_type=request.vessel_type,
            cargo_volume=request.cargo_volume,
            forecast_horizon_days=request.forecast_days,
            model_version=predictor.model_version,
            processing_time_ms=processing_time
        )
        db.add(prediction)
        db.commit()
        
        # Store results
        for forecast in forecasts:
            result = PredictionResult(
                prediction_id=prediction.id,
                forecast_date=forecast["date"],
                predicted_rate=forecast["predicted_rate"],
                confidence_lower=forecast["confidence_lower"],
                confidence_upper=forecast["confidence_upper"],
                trend_direction=forecast["trend"],
                recommendation=forecast.get("recommendation")
            )
            db.add(result)
        db.commit()
        
        return FreightForecastResponse(
            prediction_id=prediction.id,
            vessel_type=request.vessel_type,
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            forecasts=forecasts,
            model_version=predictor.model_version,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/market-entry", response_model=MarketEntryResponse)
async def analyze_market_entry(
    request: MarketEntryRequest,
    db: Session = Depends(get_db)
):
    """Analyze optimal market entry timing for charter contracts"""
    try:
        analysis = predictor.analyze_market_entry(
            vessel_type=request.vessel_type,
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            contract_duration_days=request.contract_duration_days,
            target_start_date=request.target_start_date
        )
        
        # Store prediction
        prediction = Prediction(
            prediction_type=PredictionType.MARKET_ENTRY,
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            vessel_type=request.vessel_type,
            target_date=request.target_start_date,
            model_version=predictor.model_version
        )
        db.add(prediction)
        db.commit()
        
        return MarketEntryResponse(
            prediction_id=prediction.id,
            **analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risks(
    origin_port_id: int,
    destination_port_id: int,
    vessel_type: str,
    voyage_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Assess risks for a specific voyage"""
    try:
        if voyage_date is None:
            voyage_date = datetime.utcnow() + timedelta(days=7)
        
        assessment = predictor.assess_risks(
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            vessel_type=vessel_type,
            voyage_date=voyage_date
        )
        
        return RiskAssessmentResponse(**assessment)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.get("/history", response_model=List[PredictionResponse])
async def get_prediction_history(
    prediction_type: Optional[PredictionType] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get history of predictions"""
    query = db.query(Prediction)
    
    if prediction_type:
        query = query.filter(Prediction.prediction_type == prediction_type)
    
    predictions = query.order_by(
        Prediction.request_timestamp.desc()
    ).limit(limit).all()
    
    return predictions


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get specific prediction with results"""
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return prediction
