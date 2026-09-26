import numpy as np
import json
import os
from typing import Dict, List, Optional, Tuple
from .forecasting import get_forecast


def calculate_npv(
    cash_flows: List[float],
    discount_rate: float,
    periods_per_year: int = 12,
) -> float:
    """
    Calculate Net Present Value of a series of cash flows.
    
    NPV = sum_{t=1}^{T} CF_t / (1 + r/n)^t
    
    Args:
        cash_flows: List of periodic cash flows
        discount_rate: Annual discount rate (e.g., 0.08 for 8%)
        periods_per_year: Number of periods per year (12 for monthly)
    
    Returns:
        NPV value
    """
    r_period = discount_rate / periods_per_year
    npv = 0.0
    for t, cf in enumerate(cash_flows, 1):
        npv += cf / (1 + r_period) ** t
    return npv


def calculate_breakeven_rate(
    forecasted_rates: List[float],
    cargo_quantity: float,
    discount_rate: float = 0.08,
    periods_per_year: int = 12,
) -> float:
    """
    Calculate the breakeven charter rate.
    
    The breakeven rate R satisfies:
        sum(R * Q / (1+r)^t) = sum(E[S_t] * Q / (1+r)^t)
    
    Simplifying (Q cancels):
        R = sum(E[S_t] / (1+r)^t) / sum(1 / (1+r)^t)
    
    This is the weighted average of forecasted spot rates,
    weighted by discount factors.
    """
    r_period = discount_rate / periods_per_year
    
    numerator = 0.0
    denominator = 0.0
    
    for t, rate in enumerate(forecasted_rates, 1):
        discount_factor = 1.0 / (1 + r_period) ** t
        numerator += rate * discount_factor
        denominator += discount_factor
    
    return numerator / denominator if denominator > 0 else 0


def monte_carlo_simulation(
    base_forecasts: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    charter_rate: float,
    cargo_quantity: float,
    discount_rate: float = 0.08,
    n_simulations: int = 1000,
    periods_per_year: int = 12,
) -> Dict:
    """
    Monte Carlo simulation comparing charter vs spot outcomes.
    
    For each simulation:
    1. Generate a rate path by sampling from the forecast distribution
       (assumed log-normal with mean = forecast, bounds from CI)
    2. Calculate spot NPV for that path
    3. Compare with charter NPV (fixed)
    
    Args:
        base_forecasts: Point forecasts for each period
        ci_lower: Lower bound of 95% CI
        ci_upper: Upper bound of 95% CI
        charter_rate: Proposed charter rate
        cargo_quantity: Cargo quantity per voyage
        discount_rate: Annual discount rate
        n_simulations: Number of Monte Carlo paths
    
    Returns:
        Simulation results with probability and risk metrics
    """
    r_period = discount_rate / periods_per_year
    n_periods = len(base_forecasts)
    
    # Charter NPV (fixed)
    charter_cash_flows = [charter_rate * cargo_quantity] * n_periods
    charter_npv = calculate_npv(charter_cash_flows, discount_rate, periods_per_year)
    
    # Monte Carlo spot NPVs
    spot_npvs = []
    spot_total_costs = []
    
    for _ in range(n_simulations):
        # Generate random rate path
        # Use truncated normal distribution fitted to CI bounds
        simulated_rates = []
        for i in range(n_periods):
            mean = base_forecasts[i]
            # Estimate std from 95% CI: CI width ≈ 3.92 * std
            std = (ci_upper[i] - ci_lower[i]) / 3.92
            std = max(std, mean * 0.01)  # Minimum 1% volatility
            
            # Sample from normal, clip to reasonable range
            rate = np.random.normal(mean, std)
            rate = max(mean * 0.3, min(mean * 2.5, rate))  # Clip extremes
            simulated_rates.append(rate)
        
        # Calculate spot NPV for this path
        spot_cash_flows = [r * cargo_quantity for r in simulated_rates]
        spot_npv = calculate_npv(spot_cash_flows, discount_rate, periods_per_year)
        spot_npvs.append(spot_npv)
        spot_total_costs.append(sum(spot_cash_flows))
    
    spot_npvs = np.array(spot_npvs)
    spot_total_costs = np.array(spot_total_costs)
    
    # Savings = Spot NPV - Charter NPV (positive means charter saves money)
    savings = spot_npvs - charter_npv
    
    # Probability that charter is cheaper
    prob_charter_wins = float(np.mean(savings > 0))
    
    # Value at Risk (95%): worst-case additional cost of choosing charter
    # VaR = 5th percentile of savings (if negative, charter costs more)
    var_95 = float(np.percentile(savings, 5))
    
    # Maximum potential loss from choosing charter
    max_loss = float(np.min(savings))
    
    # Expected savings from charter
    expected_savings = float(np.mean(savings))
    
    # Distribution of spot costs for histogram
    hist_values, hist_edges = np.histogram(spot_total_costs, bins=30)
    histogram = {
        "counts": hist_values.tolist(),
        "bin_edges": [round(e, 2) for e in hist_edges.tolist()],
    }
    
    return {
        "charter_npv": round(charter_npv, 2),
        "spot_npv_mean": round(float(np.mean(spot_npvs)), 2),
        "spot_npv_std": round(float(np.std(spot_npvs)), 2),
        "spot_npv_median": round(float(np.median(spot_npvs)), 2),
        "prob_charter_cheaper": round(prob_charter_wins, 3),
        "expected_savings_usd": round(expected_savings, 2),
        "var_95_usd": round(var_95, 2),
        "max_potential_loss_usd": round(max_loss, 2),
        "n_simulations": n_simulations,
        "histogram": histogram,
        "charter_total_cost": round(sum(charter_cash_flows), 2),
        "spot_total_cost_mean": round(float(np.mean(spot_total_costs)), 2),
    }



def operational_insights(route_code: str, forecast: Dict, contract_months: int) -> Dict:
    """
    Convert the route forecast into practical timing and idle-management signals.
    These are decision-support signals derived from the synthetic forecast, not
    guarantees about future market prices.
    """
    rates = np.array(forecast.get("forecasts", []), dtype=float)
    if len(rates) == 0:
        return {"market_timing": None, "idle_management": None}

    window = 7 if len(rates) >= 7 else len(rates)
    rolling = np.convolve(rates, np.ones(window) / window, mode="valid")
    low_threshold = float(np.percentile(rolling, 25))
    high_threshold = float(np.percentile(rolling, 75))

    low_idx = int(np.argmin(rolling))
    current = float(rates[0])
    current_window = float(np.mean(rates[:window]))
    low_start = low_idx + 1
    low_end = low_start + window - 1

    if current_window <= low_threshold:
        timing_status = "FAVORABLE_WINDOW"
        timing_text = (
            "The next 7-day forecast is already in the lower quartile of the "
            "90-day synthetic forecast. Review short-term charter offers now."
        )
    elif current_window >= high_threshold:
        timing_status = "WAIT_FOR_WINDOW"
        timing_text = (
            "The next 7-day forecast is in the upper quartile of the synthetic "
            "forecast. For flexible cargo, monitor the forecast for a lower-rate window."
        )
    else:
        timing_status = "MONITOR"
        timing_text = (
            "The next 7-day forecast is between the lower and upper quartiles. "
            "Compare available charter quotes with the rolling forecast before fixing."
        )

    # A low-rate period is treated as a proxy for softer demand in this prototype.
    low_periods = []
    threshold = low_threshold
    in_run = None
    for i, rate in enumerate(rolling):
        if rate <= threshold and in_run is None:
            in_run = i
        if (rate > threshold or i == len(rolling) - 1) and in_run is not None:
            end = i - 1 if rate > threshold else i
            low_periods.append({
                "start_day": in_run + 1,
                "end_day": end + window,
                "avg_rate": round(float(np.mean(rolling[in_run:end + 1])), 2),
            })
            in_run = None

    low_periods = sorted(low_periods, key=lambda x: x["avg_rate"])[:3]

    return {
        "market_timing": {
            "status": timing_status,
            "current_forecast_rate": round(current, 2),
            "next_7_day_average": round(current_window, 2),
            "lower_quartile_threshold": round(low_threshold, 2),
            "upper_quartile_threshold": round(high_threshold, 2),
            "best_7_day_window_start": low_start,
            "best_7_day_window_end": low_end,
            "best_7_day_average_rate": round(float(rolling[low_idx]), 2),
            "contract_horizon_months": contract_months,
            "guidance": timing_text,
        },
        "idle_management": {
            "low_demand_threshold": round(low_threshold, 2),
            "low_demand_windows": low_periods,
            "strategy": (
                "During forecasted low-rate/low-demand windows, avoid unnecessary "
                "ballast repositioning, keep the vessel near the relevant loading "
                "region when practical, and evaluate an alternate employment on "
                "another modeled East Coast trade lane before committing to a long "
                "idle period."
            ),
            "trigger": (
                "Treat a 7-day rolling forecast at or below the synthetic lower "
                "quartile as an early warning for softer demand."
            ),
        },
    }


def charter_decision(
    route_code: str,
    cargo_quantity_tonnes: float,
    contract_months: int = 6,
    proposed_charter_rate: Optional[float] = None,
    discount_rate: float = 0.08,
    forecast_horizon_days: int = 90,
) -> Dict:
    """
    Full charter vs spot decision analysis.
    
    Pipeline:
    1. Get freight rate forecast for the route
    2. Convert daily forecasts to monthly averages
    3. Calculate breakeven charter rate
    4. Run Monte Carlo simulation
    5. Generate recommendation with confidence level
    
    Args:
        route_code: Shipping route code
        cargo_quantity_tonnes: Cargo per voyage
        contract_months: Charter contract duration in months
        proposed_charter_rate: Offered charter rate (if None, uses breakeven)
        discount_rate: Annual discount rate for NPV
        forecast_horizon_days: Days to forecast (max 90)
    """
    # Step 1: Get forecast
    horizon = min(forecast_horizon_days, 90)
    forecast = get_forecast(route_code, horizon)
    
    # Step 2: Convert daily forecasts to monthly averages
    daily_forecasts = forecast["forecasts"]
    daily_ci95_lower = forecast["confidence_intervals"]["ci_95"]["lower"]
    daily_ci95_upper = forecast["confidence_intervals"]["ci_95"]["upper"]
    
    # Group into monthly periods (30 days each)
    monthly_rates = []
    monthly_ci_lower = []
    monthly_ci_upper = []
    
    for m in range(contract_months):
        start_idx = m * 30
        end_idx = min((m + 1) * 30, len(daily_forecasts))
        
        if start_idx < len(daily_forecasts):
            month_rates = daily_forecasts[start_idx:end_idx]
            month_lower = daily_ci95_lower[start_idx:end_idx]
            month_upper = daily_ci95_upper[start_idx:end_idx]
            
            monthly_rates.append(np.mean(month_rates))
            monthly_ci_lower.append(np.mean(month_lower))
            monthly_ci_upper.append(np.mean(month_upper))
        else:
            # Extrapolate using last known values with increased uncertainty
            last_rate = monthly_rates[-1] if monthly_rates else daily_forecasts[-1]
            last_lower = monthly_ci_lower[-1] if monthly_ci_lower else daily_ci95_lower[-1]
            last_upper = monthly_ci_upper[-1] if monthly_ci_upper else daily_ci95_upper[-1]
            
            # Widen CI for extrapolated months
            extra_months = m - len(daily_forecasts) // 30
            width_factor = 1.0 + 0.15 * extra_months
            center = last_rate
            half_width = (last_upper - last_lower) / 2 * width_factor
            
            monthly_rates.append(center)
            monthly_ci_lower.append(center - half_width)
            monthly_ci_upper.append(center + half_width)
    
    # Step 3: Breakeven rate
    breakeven_rate = calculate_breakeven_rate(
        monthly_rates, cargo_quantity_tonnes, discount_rate
    )
    
    # Use proposed rate or breakeven - 5% as default
    if proposed_charter_rate is None:
        proposed_charter_rate = breakeven_rate * 0.95
    
    # Step 4: Monte Carlo simulation
    mc_results = monte_carlo_simulation(
        base_forecasts=monthly_rates,
        ci_lower=monthly_ci_lower,
        ci_upper=monthly_ci_upper,
        charter_rate=proposed_charter_rate,
        cargo_quantity=cargo_quantity_tonnes,
        discount_rate=discount_rate,
        n_simulations=1000,
    )
    
    # Step 5: Generate recommendation
    prob = mc_results["prob_charter_cheaper"]
    
    if prob >= 0.70:
        decision = "CHARTER"
        confidence = "HIGH" if prob >= 0.85 else "MODERATE"
        reasoning = (
            f"Charter contract at ${proposed_charter_rate:.2f}/tonne is recommended. "
            f"Monte Carlo simulation shows {prob*100:.1f}% probability that charter "
            f"will be cheaper than spot over {contract_months} months. "
            f"Expected savings: ${mc_results['expected_savings_usd']:,.0f}."
        )
    elif prob >= 0.45:
        decision = "NEUTRAL"
        confidence = "LOW"
        reasoning = (
            f"No clear advantage. Charter wins in {prob*100:.1f}% of simulations. "
            f"Consider negotiating a lower charter rate (breakeven: ${breakeven_rate:.2f}/tonne) "
            f"or waiting for more market clarity."
        )
    else:
        decision = "SPOT"
        confidence = "HIGH" if prob <= 0.25 else "MODERATE"
        reasoning = (
            f"Spot market is recommended. Charter only wins in {prob*100:.1f}% of simulations. "
            f"Forecasted rates suggest spot will be cheaper. "
            f"Breakeven charter rate would be ${breakeven_rate:.2f}/tonne."
        )
    
    # NPV comparison
    charter_npv = mc_results["charter_npv"]
    spot_npv = mc_results["spot_npv_mean"]
    insights = operational_insights(route_code, forecast, contract_months)
    
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "proposed_charter_rate": round(proposed_charter_rate, 2),
        "breakeven_rate": round(breakeven_rate, 2),
        "contract_months": contract_months,
        "npv_comparison": {
            "charter_npv": round(charter_npv, 2),
            "spot_npv_mean": round(spot_npv, 2),
            "npv_difference": round(spot_npv - charter_npv, 2),
        },
        "monte_carlo": mc_results,
        "monthly_forecast": {
            "rates": [round(r, 2) for r in monthly_rates],
            "ci_lower": [round(r, 2) for r in monthly_ci_lower],
            "ci_upper": [round(r, 2) for r in monthly_ci_upper],
        },
        "risk_metrics": {
            "var_95": mc_results["var_95_usd"],
            "max_potential_loss": mc_results["max_potential_loss_usd"],
            "probability_charter_cheaper": mc_results["prob_charter_cheaper"],
        },
        "operational_insights": insights,
        "forecast_info": {
            "route_code": route_code,
            "model": forecast.get("model_info", {}),
            "training_metrics": forecast.get("training_metrics", {}),
        },
    }
