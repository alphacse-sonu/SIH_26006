import numpy as np
import pandas as pd
import os
import json
from typing import Dict, List, Tuple, Optional

import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

import torch
import torch.nn as nn

# ============================================================
# LSTM Model Definition
# ============================================================

class FreightLSTM(nn.Module):
    """
    LSTM network for capturing sequential dependencies in freight rate residuals.
    Used as a refinement layer on top of the XGBoost/LightGBM ensemble.
    
    Architecture:
        Input -> LSTM(hidden=64, layers=2) -> Dropout(0.2) -> Linear -> Output
    """
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(FreightLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        # Take last time step output
        last_output = lstm_out[:, -1, :]
        out = self.dropout(last_output)
        out = self.fc(out)
        return out


# ============================================================
# Feature columns used for training
# ============================================================

FEATURE_COLS = [
    "rate_lag_1", "rate_lag_3", "rate_lag_7", "rate_lag_14", "rate_lag_30",
    "rate_lag_60", "rate_lag_90",
    "rate_rolling_mean_7", "rate_rolling_std_7", "rate_rolling_min_7", "rate_rolling_max_7",
    "rate_rolling_mean_14", "rate_rolling_std_14", "rate_rolling_min_14", "rate_rolling_max_14",
    "rate_rolling_mean_30", "rate_rolling_std_30", "rate_rolling_min_30", "rate_rolling_max_30",
    "rate_return_1d", "rate_return_7d", "rate_return_30d",
    "month", "quarter", "day_of_week", "day_of_year",
    "sin_annual", "cos_annual", "sin_semi_annual", "cos_semi_annual",
    "sin_quarterly", "cos_quarterly",
    "bdi", "bunker_price", "trade_volume",
    "bdi_lag_1", "bdi_lag_7", "bdi_lag_14", "bdi_lag_30",
    "bunker_lag_1", "bunker_lag_7", "bunker_lag_14", "bunker_lag_30",
    "bdi_change_7d", "bdi_change_30d",
    "bunker_change_7d", "bunker_change_30d",
    "realized_vol_7", "realized_vol_14", "realized_vol_30",
    "momentum_30d", "momentum_90d",
]

TARGET_COL = "target_rate_1d"


# ============================================================
# Forecasting Engine
# ============================================================

class FreightForecaster:
    """
    Ensemble freight rate forecaster.
    
    Training pipeline:
    1. Load feature-engineered data for the specified route
    2. Train XGBoost models (median + quantile regressors)
    3. Train LightGBM model
    4. Train LSTM on residuals from the tree ensemble
    5. Store all models for inference
    
    Prediction pipeline:
    1. XGBoost predicts median + quantile bounds
    2. LightGBM predicts median
    3. Ensemble median = 0.5 * XGB_median + 0.5 * LGB_median
    4. LSTM corrects residual pattern
    5. Final = ensemble + LSTM_correction
    6. CI bounds scaled by sqrt(horizon) for multi-step forecasts
    """
    
    def __init__(self):
        self.xgb_median = None
        self.xgb_q10 = None
        self.xgb_q90 = None
        self.xgb_q025 = None
        self.xgb_q975 = None
        self.lgb_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        self.lstm_scaler = StandardScaler()
        self.is_trained = False
        self.route_code = None
        self.training_metrics = {}
    
    def _load_data(self, route_code: str) -> pd.DataFrame:
        """Load feature-engineered dataset for a route."""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        filepath = os.path.join(data_dir, f"features_{route_code}.csv")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Feature file not found: {filepath}. "
                f"Run 'python data/generate_synthetic_data.py' first."
            )
        
        return pd.read_csv(filepath)
    
    def train(self, route_code: str) -> Dict:
        """
        Train the full ensemble for a given route.
        
        Returns training metrics dict.
        """
        self.route_code = route_code
        df = self._load_data(route_code)
        
        # Prepare features and target
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values
        
        # Time-series split: last 20% for validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # ---- 1. Train XGBoost models ----
        
        # Median (50th percentile)
        self.xgb_median = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
        )
        self.xgb_median.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
        
        # Quantile regressors for confidence intervals
        quantile_params = {
            "n_estimators": 200,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
        }
        
        # 80% CI bounds
        self.xgb_q10 = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.10, **quantile_params
        )
        self.xgb_q10.fit(X_train_scaled, y_train, verbose=False)
        
        self.xgb_q90 = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.90, **quantile_params
        )
        self.xgb_q90.fit(X_train_scaled, y_train, verbose=False)
        
        # 95% CI bounds
        self.xgb_q025 = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.025, **quantile_params
        )
        self.xgb_q025.fit(X_train_scaled, y_train, verbose=False)
        
        self.xgb_q975 = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.975, **quantile_params
        )
        self.xgb_q975.fit(X_train_scaled, y_train, verbose=False)
        
        # ---- 2. Train LightGBM ----
        
        self.lgb_model = lgb.LGBMRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1,
        )
        self.lgb_model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)])
        
        # ---- 3. Train LSTM on residuals ----
        
        # Get ensemble predictions on training data
        xgb_pred_train = self.xgb_median.predict(X_train_scaled)
        lgb_pred_train = self.lgb_model.predict(X_train_scaled)
        ensemble_pred_train = 0.5 * xgb_pred_train + 0.5 * lgb_pred_train
        
        # Residuals = actual - ensemble prediction
        residuals_train = y_train - ensemble_pred_train
        
        # Prepare LSTM sequences (lookback = 30 days)
        lookback = 30
        lstm_X, lstm_y = self._create_sequences(X_train_scaled, residuals_train, lookback)
        
        if len(lstm_X) > 0:
            # Scale LSTM inputs
            lstm_X_flat = lstm_X.reshape(-1, lstm_X.shape[-1])
            self.lstm_scaler.fit(lstm_X_flat)
            lstm_X_scaled = np.array([
                self.lstm_scaler.transform(seq) for seq in lstm_X
            ])
            
            # Convert to tensors
            X_tensor = torch.FloatTensor(lstm_X_scaled)
            y_tensor = torch.FloatTensor(lstm_y).unsqueeze(1)
            
            # Initialize and train LSTM
            self.lstm_model = FreightLSTM(
                input_size=X_train_scaled.shape[1],
                hidden_size=64,
                num_layers=2,
                dropout=0.2
            )
            
            optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            self.lstm_model.train()
            for epoch in range(50):
                optimizer.zero_grad()
                output = self.lstm_model(X_tensor)
                loss = criterion(output, y_tensor)
                loss.backward()
                optimizer.step()
            
            self.lstm_model.eval()
        
        # ---- 4. Calculate validation metrics ----
        
        xgb_pred_val = self.xgb_median.predict(X_val_scaled)
        lgb_pred_val = self.lgb_model.predict(X_val_scaled)
        ensemble_pred_val = 0.5 * xgb_pred_val + 0.5 * lgb_pred_val
        
        self.training_metrics = {
            "mae": float(mean_absolute_error(y_val, ensemble_pred_val)),
            "rmse": float(np.sqrt(mean_squared_error(y_val, ensemble_pred_val))),
            "mape": float(np.mean(np.abs((y_val - ensemble_pred_val) / (y_val + 1e-8))) * 100),
            "val_samples": len(y_val),
            "train_samples": len(y_train),
        }
        
        self.is_trained = True
        return self.training_metrics
    
    def _create_sequences(self, X: np.ndarray, y: np.ndarray, lookback: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create overlapping sequences for LSTM training."""
        sequences_X, sequences_y = [], []
        for i in range(lookback, len(X)):
            sequences_X.append(X[i - lookback:i])
            sequences_y.append(y[i])
        return np.array(sequences_X), np.array(sequences_y)
    
    def predict(self, route_code: str, horizon_days: int = 30) -> Dict:
        """
        Generate freight rate forecast with confidence intervals.
        
        Args:
            route_code: Shipping route code (e.g., 'C5')
            horizon_days: Number of days to forecast (1-90)
        
        Returns:
            Dict with forecast, confidence intervals, and metadata
        
        Mathematical approach for multi-step forecasting:
        - 1-step model is applied iteratively
        - Confidence intervals widen with sqrt(horizon) to reflect
          increasing uncertainty: CI(h) = CI(1) * sqrt(h)
        - This follows from the random walk property of forecast errors
        """
        if not self.is_trained or self.route_code != route_code:
            self.train(route_code)
        
        # Load latest data for the route
        df = self._load_data(route_code)
        
        # Use last available data point as starting state
        last_row = df[FEATURE_COLS].iloc[-1:].values
        last_rate = df["rate"].iloc[-1]
        last_scaled = self.scaler.transform(last_row)
        
        # Historical rates for context
        historical_rates = df["rate"].iloc[-90:].tolist()
        historical_dates = df["date"].iloc[-90:].tolist()
        
        # Generate forecasts
        forecasts = []
        ci_80_lower, ci_80_upper = [], []
        ci_95_lower, ci_95_upper = [], []
        
        current_features = last_scaled.copy()
        current_rate = last_rate
        
        for h in range(1, horizon_days + 1):
            # XGBoost predictions
            xgb_med = float(self.xgb_median.predict(current_features)[0])
            xgb_lo80 = float(self.xgb_q10.predict(current_features)[0])
            xgb_hi80 = float(self.xgb_q90.predict(current_features)[0])
            xgb_lo95 = float(self.xgb_q025.predict(current_features)[0])
            xgb_hi95 = float(self.xgb_q975.predict(current_features)[0])
            
            # LightGBM prediction
            lgb_med = float(self.lgb_model.predict(current_features)[0])
            
            # Ensemble median
            ensemble_med = 0.5 * xgb_med + 0.5 * lgb_med
            
            # LSTM residual correction (if available)
            lstm_correction = 0.0
            if self.lstm_model is not None and h <= 7:
                # LSTM correction is most reliable for short horizons
                try:
                    with torch.no_grad():
                        lstm_input = torch.FloatTensor(current_features).unsqueeze(0).unsqueeze(0)
                        lstm_correction = float(self.lstm_model(lstm_input).item()) * (1.0 - (h - 1) / 7.0)
                except Exception:
                    lstm_correction = 0.0
            
            # Final point forecast
            point_forecast = ensemble_med + lstm_correction
            
            # Scale confidence intervals by sqrt(horizon)
            # This reflects the fundamental uncertainty growth in time series forecasting
            # Var(sum of h steps) = h * Var(1 step) => SD grows as sqrt(h)
            uncertainty_scale = np.sqrt(h)
            
            width_80 = (xgb_hi80 - xgb_lo80) * uncertainty_scale
            width_95 = (xgb_hi95 - xgb_lo95) * uncertainty_scale
            
            forecasts.append(round(point_forecast, 2))
            ci_80_lower.append(round(point_forecast - width_80 / 2, 2))
            ci_80_upper.append(round(point_forecast + width_80 / 2, 2))
            ci_95_lower.append(round(point_forecast - width_95 / 2, 2))
            ci_95_upper.append(round(point_forecast + width_95 / 2, 2))
            
            # Update features for next step (simplified: shift lag features)
            current_rate = point_forecast
            # Update rate_lag_1 position in feature vector
            current_features[0][0] = self.scaler.transform(
                np.array([[current_rate] + [0] * (len(FEATURE_COLS) - 1)])
            )[0][0]
        
        return {
            "route_code": route_code,
            "horizon_days": horizon_days,
            "last_known_rate": round(last_rate, 2),
            "forecasts": forecasts,
            "confidence_intervals": {
                "ci_80": {"lower": ci_80_lower, "upper": ci_80_upper},
                "ci_95": {"lower": ci_95_lower, "upper": ci_95_upper},
            },
            "historical_rates": [round(r, 2) for r in historical_rates],
            "historical_dates": historical_dates,
            "training_metrics": self.training_metrics,
            "model_info": {
                "ensemble": "XGBoost + LightGBM + LSTM",
                "features_used": len(FEATURE_COLS),
                "confidence_method": "Quantile regression with sqrt(h) scaling",
            },
        }


# Singleton forecaster cache
_forecaster_cache: Dict[str, FreightForecaster] = {}


def get_forecast(route_code: str, horizon_days: int = 30) -> Dict:
    """Get freight rate forecast, training model if needed."""
    if route_code not in _forecaster_cache:
        forecaster = FreightForecaster()
        forecaster.train(route_code)
        _forecaster_cache[route_code] = forecaster
    
    return _forecaster_cache[route_code].predict(route_code, horizon_days)
