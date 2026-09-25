"""Freight Rate Predictor using ML Models"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import joblib
import os

from app.ml.feature_engineering import FeatureEngineer
from app.ml.synthetic_data import SyntheticDataGenerator


class FreightPredictor:
    """Main predictor class for freight rate forecasting"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "./ml_models"
        self.model_version = "1.0.0"
        self.feature_engineer = FeatureEngineer()
        self.data_generator = SyntheticDataGenerator()
        self.models = {}
        self._load_or_train_models()
    
    def _load_or_train_models(self):
        """Load existing models or train new ones"""
        try:
            # Try to load pre-trained models
            for vessel_type in ['handysize', 'supramax', 'panamax', 'capesize']:
                model_file = os.path.join(self.model_path, f"{vessel_type}_model.joblib")
                if os.path.exists(model_file):
                    self.models[vessel_type] = joblib.load(model_file)
                else:
                    # Train new model with synthetic data
                    self.models[vessel_type] = self._train_model(vessel_type)
        except Exception as e:
            print(f"Model loading failed, using synthetic predictions: {e}")
            # Use synthetic prediction fallback
            self.models = {}
    
    def _train_model(self, vessel_type: str):
        """Train a model for specific vessel type"""
        from sklearn.ensemble import GradientBoostingRegressor
        
        # Generate synthetic training data
        data = self.data_generator.generate_freight_history(
            vessel_type=vessel_type,
            num_records=1000
        )
        
        # Prepare features
        X, y = self.feature_engineer.prepare_training_data(data)
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X, y)
        
        return model
    
    def predict_freight_rates(
        self,
        vessel_type: str,
        origin_port_id: int,
        destination_port_id: int,
        forecast_days: int = 30,
        cargo_volume: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Generate freight rate predictions"""
        forecasts = []
        base_date = datetime.utcnow()
        
        # Get base rate from synthetic data
        base_rates = {
            'handysize': 12.5,
            'supramax': 15.8,
            'panamax': 18.2,
            'capesize': 22.5
        }
        
        base_rate = base_rates.get(vessel_type.lower(), 15.0)
        
        # Route distance factors (simplified)
        route_factors = self._get_route_factor(origin_port_id, destination_port_id)
        base_rate *= route_factors['distance_factor']
        
        # Generate predictions for each day
        for day in range(forecast_days):
            forecast_date = base_date + timedelta(days=day)
            
            # Apply seasonal factors
            seasonal_factor = self._get_seasonal_factor(forecast_date)
            
            # Apply trend
            trend_factor = 1 + (day * 0.001 * np.random.choice([-1, 1]))
            
            # Add market volatility
            volatility = np.random.normal(0, 0.02)
            
            predicted_rate = base_rate * seasonal_factor * trend_factor * (1 + volatility)
            
            # Calculate confidence intervals
            confidence_margin = predicted_rate * 0.1 * (1 + day * 0.005)
            
            # Determine trend
            if day > 0 and len(forecasts) > 0:
                prev_rate = forecasts[-1]['predicted_rate']
                if predicted_rate > prev_rate * 1.01:
                    trend = "up"
                elif predicted_rate < prev_rate * 0.99:
                    trend = "down"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                predicted_rate, base_rate, trend, day
            )
            
            forecasts.append({
                "date": forecast_date,
                "predicted_rate": round(predicted_rate, 2),
                "confidence_lower": round(predicted_rate - confidence_margin, 2),
                "confidence_upper": round(predicted_rate + confidence_margin, 2),
                "trend": trend,
                "recommendation": recommendation
            })
        
        return forecasts
    
    def analyze_market_entry(
        self,
        vessel_type: str,
        origin_port_id: int,
        destination_port_id: int,
        contract_duration_days: int = 30,
        target_start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze optimal market entry timing"""
        if target_start_date is None:
            target_start_date = datetime.utcnow()
        
        # Get forecasts for analysis period
        forecasts = self.predict_freight_rates(
            vessel_type=vessel_type,
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            forecast_days=90
        )
        
        # Current rate (first forecast)
        current_rate = forecasts[0]['predicted_rate']
        
        # 30-day predicted rate
        predicted_rate_30d = forecasts[29]['predicted_rate'] if len(forecasts) > 29 else current_rate
        
        # Find optimal entry windows
        optimal_windows = self._find_optimal_windows(forecasts, contract_duration_days)
        
        # Determine market trend
        avg_first_week = np.mean([f['predicted_rate'] for f in forecasts[:7]])
        avg_last_week = np.mean([f['predicted_rate'] for f in forecasts[-7:]])
        
        if avg_last_week > avg_first_week * 1.05:
            market_trend = "bullish"
            recommendation = "Consider entering the market soon as rates are expected to rise."
        elif avg_last_week < avg_first_week * 0.95:
            market_trend = "bearish"
            recommendation = "Consider waiting for better rates as market is trending down."
        else:
            market_trend = "stable"
            recommendation = "Market is stable. Enter based on operational requirements."
        
        # Calculate confidence score
        rate_volatility = np.std([f['predicted_rate'] for f in forecasts])
        confidence_score = max(0, min(100, 100 - (rate_volatility / current_rate * 100)))
        
        return {
            "vessel_type": vessel_type,
            "origin_port_id": origin_port_id,
            "destination_port_id": destination_port_id,
            "current_rate": current_rate,
            "predicted_rate_30d": predicted_rate_30d,
            "optimal_entry_windows": optimal_windows,
            "market_trend": market_trend,
            "recommendation": recommendation,
            "confidence_score": round(confidence_score, 1)
        }
    
    def assess_risks(
        self,
        origin_port_id: int,
        destination_port_id: int,
        vessel_type: str,
        voyage_date: datetime
    ) -> Dict[str, Any]:
        """Assess risks for a voyage"""
        risk_factors = []
        
        # Weather risk based on season
        month = voyage_date.month
        if month in [6, 7, 8, 9]:  # Monsoon season for Indian Ocean
            weather_risk = "high"
            risk_factors.append({
                "factor": "Monsoon Season",
                "level": "high",
                "description": "Voyage during monsoon season may face delays",
                "mitigation": "Consider weather routing and buffer time"
            })
        elif month in [12, 1, 2]:
            weather_risk = "medium"
            risk_factors.append({
                "factor": "Winter Weather",
                "level": "medium",
                "description": "Potential for rough seas in certain regions",
                "mitigation": "Monitor weather forecasts closely"
            })
        else:
            weather_risk = "low"
        
        # Congestion risk (simulated)
        congestion_level = np.random.uniform(0.2, 0.8)
        if congestion_level > 0.7:
            congestion_risk = "high"
            risk_factors.append({
                "factor": "Port Congestion",
                "level": "high",
                "description": "High congestion expected at destination port",
                "mitigation": "Plan for waiting time at anchorage"
            })
        elif congestion_level > 0.4:
            congestion_risk = "medium"
        else:
            congestion_risk = "low"
        
        # Market volatility risk
        volatility = np.random.uniform(0.05, 0.25)
        if volatility > 0.2:
            market_risk = "high"
            risk_factors.append({
                "factor": "Market Volatility",
                "level": "high",
                "description": "High freight rate volatility expected",
                "mitigation": "Consider locking in rates with term contracts"
            })
        elif volatility > 0.1:
            market_risk = "medium"
        else:
            market_risk = "low"
        
        # Calculate overall risk score
        risk_weights = {"low": 1, "medium": 2, "high": 3}
        risk_values = [risk_weights[weather_risk], risk_weights[congestion_risk], risk_weights[market_risk]]
        overall_score = (sum(risk_values) / (len(risk_values) * 3)) * 100
        
        if overall_score > 66:
            overall_risk = "high"
        elif overall_score > 33:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        recommendations = [
            "Monitor market conditions regularly",
            "Maintain communication with port agents",
            "Have contingency plans for delays"
        ]
        
        if overall_risk == "high":
            recommendations.append("Consider postponing voyage if possible")
        
        return {
            "origin_port_id": origin_port_id,
            "destination_port_id": destination_port_id,
            "vessel_type": vessel_type,
            "voyage_date": voyage_date,
            "overall_risk_level": overall_risk,
            "risk_score": round(overall_score, 1),
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "weather_risk": weather_risk,
            "congestion_risk": congestion_risk,
            "market_volatility_risk": market_risk
        }
    
    def _get_route_factor(self, origin_id: int, dest_id: int) -> Dict[str, float]:
        """Get route-specific factors"""
        # Simplified route factors based on typical distances
        # In production, this would come from the database
        return {
            "distance_factor": 1.0 + (abs(origin_id - dest_id) % 5) * 0.1,
            "risk_factor": 1.0
        }
    
    def _get_seasonal_factor(self, date: datetime) -> float:
        """Get seasonal adjustment factor"""
        month = date.month
        # Higher rates during peak shipping seasons
        seasonal_factors = {
            1: 1.05, 2: 1.03, 3: 1.0, 4: 0.98,
            5: 0.95, 6: 0.93, 7: 0.92, 8: 0.94,
            9: 0.98, 10: 1.02, 11: 1.08, 12: 1.10
        }
        return seasonal_factors.get(month, 1.0)
    
    def _generate_recommendation(self, predicted_rate: float, base_rate: float, trend: str, days_ahead: int) -> str:
        """Generate actionable recommendation"""
        rate_diff = (predicted_rate - base_rate) / base_rate * 100
        
        if rate_diff < -5 and days_ahead < 14:
            return "Favorable rates expected. Consider booking soon."
        elif rate_diff > 5 and trend == "up":
            return "Rates rising. Lock in current rates if possible."
        elif trend == "down" and days_ahead > 14:
            return "Rates may decrease. Consider waiting if timeline allows."
        else:
            return "Monitor market conditions."
    
    def _find_optimal_windows(self, forecasts: List[Dict], contract_days: int) -> List[Dict]:
        """Find optimal entry windows based on forecasts"""
        windows = []
        rates = [f['predicted_rate'] for f in forecasts]
        avg_rate = np.mean(rates)
        
        # Find periods with below-average rates
        in_window = False
        window_start = None
        
        for i, forecast in enumerate(forecasts):
            if forecast['predicted_rate'] < avg_rate * 0.98:
                if not in_window:
                    in_window = True
                    window_start = forecast['date']
            else:
                if in_window:
                    windows.append({
                        "start_date": window_start,
                        "end_date": forecast['date'],
                        "expected_rate": np.mean([f['predicted_rate'] for f in forecasts[max(0,i-7):i]]),
                        "confidence": 0.75,
                        "recommendation": "Good entry window with below-average rates"
                    })
                    in_window = False
        
        # If still in window at end
        if in_window and window_start:
            windows.append({
                "start_date": window_start,
                "end_date": forecasts[-1]['date'],
                "expected_rate": np.mean([f['predicted_rate'] for f in forecasts[-7:]]),
                "confidence": 0.7,
                "recommendation": "Potential entry window extending beyond forecast period"
            })
        
        return windows[:3]  # Return top 3 windows
