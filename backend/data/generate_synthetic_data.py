"""
Synthetic Freight Rate Data Generator
=====================================
Generates 5 years of daily freight rates for major shipping routes.
Models realistic patterns: seasonality, mean-reversion, volatility clustering,
correlation with BDI and bunker prices.

Methodology:
- Base signal: Ornstein-Uhlenbeck mean-reverting process
- Seasonal component: Fourier series (annual + semi-annual harmonics)
- Volatility: GARCH(1,1)-like clustering
- Correlation: BDI and bunker price co-movement

References:
- Alizadeh & Nomikos (2009), "Shipping Derivatives and Risk Management"
- Kavussanos & Visvikis (2006), "Derivatives and Risk Management in Shipping"
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime, timedelta

np.random.seed(42)


# Route configurations are derived from the PS-26006 trade lanes in routes.json.
# The generated history is deterministic (seeded) synthetic demo data.
ORIGIN_SEASONAL = {
    "Australia":  {"volatility": 0.24, "peak_month": 10, "secondary_peak_month": 3, "seasonal_amplitude": 2.0, "secondary_amplitude": 0.9},
    "US":         {"volatility": 0.28, "peak_month": 9,  "secondary_peak_month": 3, "seasonal_amplitude": 2.5, "secondary_amplitude": 1.2},
    "Mozambique": {"volatility": 0.25, "peak_month": 11, "secondary_peak_month": 6, "seasonal_amplitude": 2.2, "secondary_amplitude": 1.0},
    "Russia":     {"volatility": 0.30, "peak_month": 12, "secondary_peak_month": 5, "seasonal_amplitude": 2.8, "secondary_amplitude": 1.2},
    "Indonesia":  {"volatility": 0.22, "peak_month": 7,  "secondary_peak_month": 12, "seasonal_amplitude": 1.8, "secondary_amplitude": 0.8},
}

def load_route_configs():
    """Create deterministic synthetic-rate configurations for all PS trade lanes."""
    data_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(data_dir, "routes.json"), "r", encoding="utf-8") as f:
        routes = json.load(f)

    configs = {}
    for route in routes:
        season = ORIGIN_SEASONAL.get(route.get("origin_region"), ORIGIN_SEASONAL["Australia"])
        configs[route["route_code"]] = {
            "mean_rate": route["historical_avg_rate"],
            "volatility": season["volatility"],
            "mean_reversion_speed": 0.03,
            "seasonal_amplitude": season["seasonal_amplitude"],
            "peak_month": season["peak_month"],
            "secondary_peak_month": season["secondary_peak_month"],
            "secondary_amplitude": season["secondary_amplitude"],
        }
    return configs

ROUTE_CONFIGS = load_route_configs()


def generate_bdi_index(n_days: int) -> np.ndarray:
    """
    Generate synthetic Baltic Dry Index using Ornstein-Uhlenbeck process.
    BDI typically ranges 500-5000, mean ~1500.
    """
    mu = 1500  # Long-term mean
    theta = 0.02  # Mean reversion speed
    sigma = 80  # Daily volatility
    
    bdi = np.zeros(n_days)
    bdi[0] = mu
    
    for t in range(1, n_days):
        # OU process: dX = theta*(mu - X)*dt + sigma*dW
        dW = np.random.normal(0, 1)
        bdi[t] = bdi[t-1] + theta * (mu - bdi[t-1]) + sigma * dW
        # Add seasonal component
        day_of_year = t % 365
        seasonal = 300 * np.sin(2 * np.pi * (day_of_year - 270) / 365)
        bdi[t] += seasonal * 0.01
        bdi[t] = max(300, bdi[t])  # Floor at 300
    
    return bdi


def generate_bunker_prices(n_days: int) -> np.ndarray:
    """
    Generate synthetic VLSFO bunker prices (USD/tonne).
    Typical range: 400-800 USD/tonne.
    """
    mu = 580
    theta = 0.015
    sigma = 12
    
    prices = np.zeros(n_days)
    prices[0] = mu
    
    for t in range(1, n_days):
        dW = np.random.normal(0, 1)
        prices[t] = prices[t-1] + theta * (mu - prices[t-1]) + sigma * dW
        prices[t] = max(300, min(1000, prices[t]))
    
    return prices


def generate_route_rates(config: dict, n_days: int, bdi: np.ndarray, bunker: np.ndarray) -> np.ndarray:
    """
    Generate freight rates for a single route using:
    1. Ornstein-Uhlenbeck mean-reverting process
    2. Seasonal Fourier components
    3. GARCH-like volatility clustering
    4. Correlation with BDI and bunker prices
    
    Mathematical formulation:
        r(t) = r(t-1) + θ(μ - r(t-1))Δt + σ(t)·ε(t) + S(t) + β_bdi·ΔBDI(t) + β_bunker·ΔBunker(t)
    
    where:
        θ = mean reversion speed
        μ = long-term mean rate
        σ(t) = time-varying volatility (GARCH-like)
        S(t) = seasonal component (Fourier series)
        β_bdi, β_bunker = correlation coefficients
    """
    mu = config["mean_rate"]
    vol = config["volatility"]
    theta = config["mean_reversion_speed"]
    
    rates = np.zeros(n_days)
    rates[0] = mu
    
    # GARCH-like volatility state
    h = np.zeros(n_days)  # Conditional variance
    h[0] = (mu * vol * 0.01) ** 2
    alpha_0 = h[0] * 0.05  # GARCH constant
    alpha_1 = 0.10  # ARCH effect
    beta_1 = 0.85   # GARCH persistence
    
    # Correlation coefficients with BDI and bunker
    beta_bdi = 0.002 * mu / 1500  # Scaled to rate level
    beta_bunker = -0.001 * mu / 580  # Higher bunker = lower net rate
    
    for t in range(1, n_days):
        # Seasonal component: Fourier series with primary and secondary peaks
        day_of_year = t % 365
        primary_seasonal = config["seasonal_amplitude"] * np.sin(
            2 * np.pi * (day_of_year - (config["peak_month"] - 3) * 30.44) / 365
        )
        secondary_seasonal = config["secondary_amplitude"] * np.sin(
            2 * np.pi * (day_of_year - (config["secondary_peak_month"] - 3) * 30.44) / 365
        )
        seasonal = (primary_seasonal + secondary_seasonal) * 0.01  # Daily increment
        
        # GARCH volatility update
        epsilon_prev = rates[t-1] - rates[t-2] if t > 1 else 0
        h[t] = alpha_0 + alpha_1 * epsilon_prev**2 + beta_1 * h[t-1]
        sigma_t = np.sqrt(max(h[t], 1e-8))
        
        # Mean-reverting component
        mean_revert = theta * (mu - rates[t-1])
        
        # BDI and bunker correlation
        bdi_effect = beta_bdi * (bdi[t] - bdi[t-1]) if t > 0 else 0
        bunker_effect = beta_bunker * (bunker[t] - bunker[t-1]) if t > 0 else 0
        
        # Random shock
        shock = sigma_t * np.random.normal(0, 1)
        
        # Combined rate update
        rates[t] = rates[t-1] + mean_revert + seasonal + shock + bdi_effect + bunker_effect
        
        # Ensure rate stays positive (minimum 20% of mean)
        rates[t] = max(mu * 0.2, rates[t])
    
    return rates


def generate_all_data():
    """Generate complete synthetic dataset for all routes."""
    
    # 5 years of daily data
    n_days = 365 * 5
    start_date = datetime(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # Generate common market indicators
    bdi = generate_bdi_index(n_days)
    bunker = generate_bunker_prices(n_days)
    
    # Generate trade volume index (proxy for global trade activity)
    trade_volume = np.zeros(n_days)
    trade_volume[0] = 100
    for t in range(1, n_days):
        day_of_year = t % 365
        seasonal_trade = 5 * np.sin(2 * np.pi * (day_of_year - 60) / 365)
        trade_volume[t] = trade_volume[t-1] + 0.02 * (100 - trade_volume[t-1]) + seasonal_trade * 0.01 + np.random.normal(0, 1.5)
        trade_volume[t] = max(60, min(140, trade_volume[t]))
    
    # Market indicators DataFrame
    market_df = pd.DataFrame({
        "date": dates,
        "bdi": bdi,
        "bunker_price_vlsfo": bunker,
        "trade_volume_index": trade_volume,
    })
    
    data_dir = os.path.dirname(os.path.abspath(__file__))
    market_df.to_csv(os.path.join(data_dir, "market_indicators.csv"), index=False)
    print(f"Generated market_indicators.csv: {len(market_df)} rows")
    
    # Generate rates for each route
    all_rates = {"date": dates}
    
    for route_code, config in ROUTE_CONFIGS.items():
        rates = generate_route_rates(config, n_days, bdi, bunker)
        all_rates[route_code] = rates
    
    rates_df = pd.DataFrame(all_rates)
    rates_df.to_csv(os.path.join(data_dir, "freight_rates.csv"), index=False)
    print(f"Generated freight_rates.csv: {len(rates_df)} rows, {len(ROUTE_CONFIGS)} routes")
    
    # Generate combined feature-engineered dataset for ML training
    for route_code in ROUTE_CONFIGS:
        features_df = build_features(rates_df, market_df, route_code)
        features_df.to_csv(os.path.join(data_dir, f"features_{route_code}.csv"), index=False)
        print(f"Generated features_{route_code}.csv: {len(features_df)} rows, {len(features_df.columns)} features")
    
    print("\nData generation complete!")


def build_features(rates_df: pd.DataFrame, market_df: pd.DataFrame, route_code: str) -> pd.DataFrame:
    """
    Build feature-engineered dataset for a specific route.
    
    Features:
    - Lagged rates: 1, 3, 7, 14, 30, 60, 90 days
    - Rolling statistics: mean, std, min, max for 7, 14, 30 day windows
    - Rate of change: 1-day, 7-day, 30-day returns
    - Seasonal: month, quarter, day_of_week, day_of_year
    - Fourier features: sin/cos transforms for annual and semi-annual cycles
    - Market indicators: BDI, bunker price, trade volume (current + lagged)
    - Volatility: realized volatility over 7, 14, 30 day windows
    - Momentum: rate relative to 30-day and 90-day moving average
    """
    df = pd.DataFrame()
    df["date"] = rates_df["date"]
    df["rate"] = rates_df[route_code]
    
    # Lagged rates
    for lag in [1, 3, 7, 14, 30, 60, 90]:
        df[f"rate_lag_{lag}"] = df["rate"].shift(lag)
    
    # Rolling statistics
    for window in [7, 14, 30]:
        df[f"rate_rolling_mean_{window}"] = df["rate"].rolling(window).mean()
        df[f"rate_rolling_std_{window}"] = df["rate"].rolling(window).std()
        df[f"rate_rolling_min_{window}"] = df["rate"].rolling(window).min()
        df[f"rate_rolling_max_{window}"] = df["rate"].rolling(window).max()
    
    # Rate of change (returns)
    df["rate_return_1d"] = df["rate"].pct_change(1)
    df["rate_return_7d"] = df["rate"].pct_change(7)
    df["rate_return_30d"] = df["rate"].pct_change(30)
    
    # Seasonal features
    df["date_parsed"] = pd.to_datetime(df["date"])
    df["month"] = df["date_parsed"].dt.month
    df["quarter"] = df["date_parsed"].dt.quarter
    df["day_of_week"] = df["date_parsed"].dt.dayofweek
    df["day_of_year"] = df["date_parsed"].dt.dayofyear
    
    # Fourier features for cyclical encoding
    df["sin_annual"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["cos_annual"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["sin_semi_annual"] = np.sin(4 * np.pi * df["day_of_year"] / 365)
    df["cos_semi_annual"] = np.cos(4 * np.pi * df["day_of_year"] / 365)
    df["sin_quarterly"] = np.sin(8 * np.pi * df["day_of_year"] / 365)
    df["cos_quarterly"] = np.cos(8 * np.pi * df["day_of_year"] / 365)
    
    # Market indicators
    df["bdi"] = market_df["bdi"].values
    df["bunker_price"] = market_df["bunker_price_vlsfo"].values
    df["trade_volume"] = market_df["trade_volume_index"].values
    
    # Lagged market indicators
    for lag in [1, 7, 14, 30]:
        df[f"bdi_lag_{lag}"] = df["bdi"].shift(lag)
        df[f"bunker_lag_{lag}"] = df["bunker_price"].shift(lag)
    
    # BDI change
    df["bdi_change_7d"] = df["bdi"].pct_change(7)
    df["bdi_change_30d"] = df["bdi"].pct_change(30)
    df["bunker_change_7d"] = df["bunker_price"].pct_change(7)
    df["bunker_change_30d"] = df["bunker_price"].pct_change(30)
    
    # Realized volatility
    for window in [7, 14, 30]:
        returns = df["rate"].pct_change()
        df[f"realized_vol_{window}"] = returns.rolling(window).std() * np.sqrt(252)
    
    # Momentum indicators
    df["momentum_30d"] = df["rate"] / df["rate_rolling_mean_30"] - 1
    ma_90 = df["rate"].rolling(90).mean()
    df["momentum_90d"] = df["rate"] / ma_90 - 1
    
    # Target: next day rate (for training)
    df["target_rate_1d"] = df["rate"].shift(-1)
    df["target_rate_7d"] = df["rate"].shift(-7)
    df["target_rate_30d"] = df["rate"].shift(-30)
    
    # Drop temporary columns and NaN rows
    df = df.drop(columns=["date_parsed"])
    df = df.dropna()
    
    return df


if __name__ == "__main__":
    generate_all_data()
