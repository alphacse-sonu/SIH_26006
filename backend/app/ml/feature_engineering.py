"""Feature Engineering for ML Models"""
import numpy as np
import pandas as pd
from typing import Tuple, List
from datetime import datetime


class FeatureEngineer:
    """Feature engineering utilities for freight prediction models"""
    
    def __init__(self):
        self.feature_columns = [
            'month', 'day_of_week', 'year', 'fuel_price', 'market_index',
            'coal_price', 'congestion_level', 'voyage_duration_days',
            'cargo_volume', 'season_encoded', 'origin_encoded', 'dest_encoded'
        ]
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for model training"""
        # Create a copy to avoid modifying original
        data = df.copy()
        
        # Encode categorical variables
        data['season_encoded'] = data['season'].map({
            'summer': 0, 'monsoon': 1, 'winter': 2
        }).fillna(0)
        
        # Encode origin ports
        origin_mapping = {pid: idx for idx, pid in enumerate(data['origin_port_id'].unique())}
        data['origin_encoded'] = data['origin_port_id'].map(origin_mapping)
        
        # Encode destination ports
        dest_mapping = {pid: idx for idx, pid in enumerate(data['destination_port_id'].unique())}
        data['dest_encoded'] = data['destination_port_id'].map(dest_mapping)
        
        # Select features
        feature_cols = [
            'month', 'day_of_week', 'year', 'fuel_price', 'market_index',
            'coal_price', 'congestion_level', 'voyage_duration_days',
            'cargo_volume', 'season_encoded', 'origin_encoded', 'dest_encoded'
        ]
        
        # Handle missing columns
        for col in feature_cols:
            if col not in data.columns:
                data[col] = 0
        
        X = data[feature_cols].fillna(0).values
        y = data['rate_per_ton'].values
        
        return X, y
    
    def create_prediction_features(
        self,
        date: datetime,
        origin_port_id: int,
        destination_port_id: int,
        fuel_price: float = 550,
        market_index: float = 1500,
        coal_price: float = 150,
        congestion_level: float = 0.5,
        voyage_duration: int = 20,
        cargo_volume: float = 50000
    ) -> np.ndarray:
        """Create feature vector for prediction"""
        # Determine season
        month = date.month
        if month in [6, 7, 8, 9]:
            season_encoded = 1  # monsoon
        elif month in [11, 12, 1, 2]:
            season_encoded = 2  # winter
        else:
            season_encoded = 0  # summer
        
        features = np.array([
            month,
            date.weekday(),
            date.year,
            fuel_price,
            market_index,
            coal_price,
            congestion_level,
            voyage_duration,
            cargo_volume,
            season_encoded,
            origin_port_id % 10,  # Simple encoding
            destination_port_id % 10
        ]).reshape(1, -1)
        
        return features
    
    def add_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 7, 30]) -> pd.DataFrame:
        """Add lagged features for time series prediction"""
        data = df.copy()
        data = data.sort_values('record_date')
        
        for lag in lags:
            data[f'rate_lag_{lag}'] = data['rate_per_ton'].shift(lag)
        
        # Rolling statistics
        data['rate_rolling_mean_7'] = data['rate_per_ton'].rolling(window=7).mean()
        data['rate_rolling_std_7'] = data['rate_per_ton'].rolling(window=7).std()
        data['rate_rolling_mean_30'] = data['rate_per_ton'].rolling(window=30).mean()
        
        return data.dropna()
    
    def add_cyclical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cyclical encoding for time features"""
        data = df.copy()
        
        # Month cyclical encoding
        data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
        data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)
        
        # Day of week cyclical encoding
        data['dow_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
        data['dow_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
        
        return data
    
    def calculate_route_features(self, origin_id: int, dest_id: int) -> dict:
        """Calculate route-specific features"""
        # Simplified route features
        # In production, this would use actual route data
        
        # Estimated distances (nautical miles)
        base_distances = {
            (101, 1): 5800,  # Australia to Paradip
            (104, 1): 9500,  # USA to Paradip
            (106, 1): 3200,  # Mozambique to Paradip
            (108, 1): 2800,  # Indonesia to Paradip
        }
        
        distance = base_distances.get((origin_id, dest_id), 5000)
        
        return {
            'distance_nm': distance,
            'distance_normalized': distance / 10000,
            'is_long_haul': 1 if distance > 7000 else 0,
            'is_short_haul': 1 if distance < 3500 else 0
        }
