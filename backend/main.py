import json
import os
import traceback
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================
# App Configuration
# ============================================================

app = FastAPI(
    title="Maritime Chartering Decision Platform",
    description="AI-powered chartering decision engine for SAIL (SIH 2026)",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Data Loading Helpers
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(filename: str) -> list:
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)


# ============================================================
# Request/Response Models
# ============================================================

class ForecastRequest(BaseModel):
    route_code: str = Field(..., description="Route code, e.g. 'C5'")
    horizon_days: int = Field(default=30, ge=1, le=90, description="Forecast horizon in days")


class CostRequest(BaseModel):
    cargo_quantity_tonnes: float = Field(..., gt=0, description="Cargo quantity in tonnes")
    route_code: str = Field(..., description="Route code")
    vessel_class: str = Field(..., description="Vessel class, e.g. 'Capesize'")
    freight_rate: float = Field(..., gt=0, description="Freight rate (USD/tonne)")
    loading_date_month: int = Field(default=1, ge=1, le=12, description="Loading month")
    cargo_value_per_tonne: float = Field(default=100.0, gt=0)
    bunker_price_per_tonne: float = Field(default=580.0, gt=0)
    vessel_subtype: str = Field(default="Standard")


class LighteringRequest(BaseModel):
    cargo_quantity_tonnes: float = Field(..., gt=0)
    vessel_class: str = Field(..., description="Vessel class")
    port_name: str = Field(..., description="Destination port name")
    month: int = Field(default=1, ge=1, le=12)
    cargo_value_per_tonne: float = Field(default=100.0, gt=0)
    vessel_subtype: str = Field(default="Standard")


class CharterDecisionRequest(BaseModel):
    route_code: str = Field(..., description="Route code")
    cargo_quantity_tonnes: float = Field(..., gt=0)
    contract_months: int = Field(default=6, ge=1, le=24)
    proposed_charter_rate: Optional[float] = Field(default=None, description="Offered charter rate")
    discount_rate: float = Field(default=0.08, gt=0, lt=1)


class FullAnalysisRequest(BaseModel):
    cargo_quantity_tonnes: float = Field(..., gt=0, description="Cargo quantity in tonnes")
    cargo_material: str = Field(default="Coal", description="Bulk cargo material, e.g. Coal or Steel")
    route_code: str = Field(..., description="PS-26006 trade lane route code")
    contract_months: int = Field(default=6, ge=1, le=24)
    loading_date_month: int = Field(default=1, ge=1, le=12)
    cargo_value_per_tonne: float = Field(default=100.0, gt=0)
    bunker_price_per_tonne: float = Field(default=580.0, gt=0)
    proposed_charter_rate: Optional[float] = Field(default=None)


# ============================================================
# Static Data Endpoints
# ============================================================

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    data_exists = os.path.exists(os.path.join(DATA_DIR, "freight_rates.csv"))
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "data_generated": data_exists,
    }


@app.get("/api/routes")
def get_routes():
    """Get all available shipping routes."""
    return load_json("routes.json")


@app.get("/api/vessels")
def get_vessels():
    """Get all available vessel classes."""
    return load_json("vessels.json")


@app.get("/api/ports")
def get_ports():
    """Get all available ports."""
    return load_json("ports.json")


# ============================================================
# Vessel Recommendation
# ============================================================

class VesselRecommendationRequest(BaseModel):
    cargo_quantity_tonnes: float = Field(..., gt=0)
    cargo_material: str = Field(default="Coal")
    route_code: str = Field(...)


@app.post("/api/recommend-vessel")
def recommend_vessel_endpoint(request: VesselRecommendationRequest):
    """Recommend the most suitable feasible vessel for a PS-26006 trade lane."""
    try:
        from models.vessel_optimizer import recommend_vessel
        return recommend_vessel(
            cargo_material=request.cargo_material,
            cargo_quantity_tonnes=request.cargo_quantity_tonnes,
            route_code=request.route_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vessel recommendation error: {str(e)}")


# ============================================================
# ML Model Endpoints
# ============================================================

@app.post("/api/predict-rates")
def predict_rates(request: ForecastRequest):
    """
    Freight rate forecasting with confidence intervals.
    
    Uses XGBoost + LightGBM + LSTM ensemble model.
    Returns point forecasts and 80%/95% confidence intervals.
    """
    try:
        from models.forecasting import get_forecast
        result = get_forecast(request.route_code, request.horizon_days)
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Training data not found. Run 'python data/generate_synthetic_data.py' first. Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


@app.post("/api/calculate-cost")
def calculate_cost(request: CostRequest):
    """
    Calculate total delivered cost for a voyage.
    
    Includes freight, port charges, waiting time, demurrage,
    weather disruption, canal fees, insurance, and bunker costs.
    """
    try:
        from models.cost_calculator import calculate_total_cost
        result = calculate_total_cost(
            cargo_quantity_tonnes=request.cargo_quantity_tonnes,
            route_code=request.route_code,
            vessel_class=request.vessel_class,
            freight_rate=request.freight_rate,
            loading_date_month=request.loading_date_month,
            cargo_value_per_tonne=request.cargo_value_per_tonne,
            bunker_price_per_tonne=request.bunker_price_per_tonne,
            vessel_subtype=request.vessel_subtype,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost calculation error: {str(e)}")


@app.post("/api/lightering-analysis")
def lightering_analysis(request: LighteringRequest):
    """
    Lightering optimization analysis.
    
    Determines if lightering is needed, calculates costs,
    assesses weather risk, and recommends optimal approach.
    """
    try:
        from models.lightering import full_lightering_analysis
        result = full_lightering_analysis(
            cargo_quantity_tonnes=request.cargo_quantity_tonnes,
            vessel_class=request.vessel_class,
            port_name=request.port_name,
            month=request.month,
            cargo_value_per_tonne=request.cargo_value_per_tonne,
            vessel_subtype=request.vessel_subtype,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lightering analysis error: {str(e)}")


@app.post("/api/charter-decision")
def charter_decision(request: CharterDecisionRequest):
    """
    Charter vs Spot decision analysis.
    
    Uses NPV comparison, breakeven analysis, and Monte Carlo
    simulation to recommend CHARTER or SPOT.
    """
    try:
        from models.decision_engine import charter_decision as run_decision
        result = run_decision(
            route_code=request.route_code,
            cargo_quantity_tonnes=request.cargo_quantity_tonnes,
            contract_months=request.contract_months,
            proposed_charter_rate=request.proposed_charter_rate,
            discount_rate=request.discount_rate,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Training data not found. Run 'python data/generate_synthetic_data.py' first. Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision engine error: {str(e)}")


@app.post("/api/full-analysis")
def full_analysis(request: FullAnalysisRequest):
    """
    Combined analysis running all modules.
    
    Returns:
    - Freight rate forecast
    - Total delivered cost breakdown
    - Lightering analysis (if applicable)
    - Charter vs spot recommendation
    - Risk indicators
    """
    try:
        from models.forecasting import get_forecast
        from models.cost_calculator import calculate_total_cost, compare_vessel_options, get_route_data
        from models.lightering import full_lightering_analysis
        from models.decision_engine import charter_decision as run_decision
        from models.vessel_optimizer import recommend_vessel

        results = {}
        errors = []

        # 1. Vessel optimization comes first: the user does not choose vessel size.
        try:
            vessel_rec = recommend_vessel(
                cargo_material=request.cargo_material,
                cargo_quantity_tonnes=request.cargo_quantity_tonnes,
                route_code=request.route_code,
            )
            results["vessel_recommendation"] = vessel_rec
        except Exception as e:
            errors.append(f"Vessel recommendation: {str(e)}")
            vessel_rec = None
            results["vessel_recommendation"] = None

        selected = (vessel_rec or {}).get("recommended") if vessel_rec else None
        selected_class = selected.get("class") if selected else None
        selected_subtype = selected.get("subtype", "Standard") if selected else "Standard"
        split_voyages = int(selected.get("split_voyages", 1)) if selected else 1
        analysis_cargo_quantity = (
            float(selected.get("per_voyage_cargo_tonnes", request.cargo_quantity_tonnes))
            if selected else request.cargo_quantity_tonnes
        )

        # 2. Freight rate forecast from the route's deterministic synthetic history.
        try:
            forecast = get_forecast(request.route_code, horizon_days=90)
            results["forecast"] = forecast
            forecasted_rate = forecast["forecasts"][0] if forecast["forecasts"] else 10.0
        except Exception as e:
            errors.append(f"Forecast: {str(e)}")
            forecasted_rate = 10.0
            results["forecast"] = None

        # 3. Total delivered cost using the automatically selected vessel.
        if selected_class:
            try:
                cost = calculate_total_cost(
                    cargo_quantity_tonnes=analysis_cargo_quantity,
                    route_code=request.route_code,
                    vessel_class=selected_class,
                    freight_rate=forecasted_rate,
                    loading_date_month=request.loading_date_month,
                    cargo_value_per_tonne=request.cargo_value_per_tonne,
                    bunker_price_per_tonne=request.bunker_price_per_tonne,
                    vessel_subtype=selected_subtype,
                )
                if split_voyages > 1:
                    cost["total_cost_usd"] = round(cost["total_cost_usd"] * split_voyages, 2)
                    cost["cost_per_tonne_usd"] = round(cost["total_cost_usd"] / request.cargo_quantity_tonnes, 2)
                    cost["voyage_plan"] = {
                        "voyages": split_voyages,
                        "cargo_per_voyage_tonnes": analysis_cargo_quantity,
                        "total_cargo_tonnes": request.cargo_quantity_tonnes,
                    }
                results["cost_analysis"] = cost
            except Exception as e:
                errors.append(f"Cost: {str(e)}")
                results["cost_analysis"] = None
        else:
            results["cost_analysis"] = None

        # 4. Compare only vessels that satisfy the same route constraints.
        try:
            vessel_comparison = compare_vessel_options(
                cargo_quantity_tonnes=analysis_cargo_quantity,
                route_code=request.route_code,
                freight_rate=forecasted_rate,
                loading_date_month=request.loading_date_month,
                cargo_material=request.cargo_material,
            )
            results["vessel_comparison"] = vessel_comparison
        except Exception as e:
            errors.append(f"Vessel comparison: {str(e)}")
            results["vessel_comparison"] = None

        # 5. Lightering analysis for the automatically selected vessel.
        if selected_class:
            try:
                route = get_route_data(request.route_code)
                dest_port = route["destination"] if route else None
                lightering = full_lightering_analysis(
                    cargo_quantity_tonnes=analysis_cargo_quantity,
                    vessel_class=selected_class,
                    port_name=dest_port,
                    month=request.loading_date_month,
                    cargo_value_per_tonne=request.cargo_value_per_tonne,
                    vessel_subtype=selected_subtype,
                )
                results["lightering"] = lightering
            except Exception as e:
                errors.append(f"Lightering: {str(e)}")
                results["lightering"] = None
        else:
            results["lightering"] = None

        # 6. Charter vs spot analysis uses the same route forecast.
        try:
            decision = run_decision(
                route_code=request.route_code,
                cargo_quantity_tonnes=analysis_cargo_quantity,
                contract_months=request.contract_months,
                proposed_charter_rate=request.proposed_charter_rate,
            )
            results["charter_decision"] = decision
        except Exception as e:
            errors.append(f"Charter decision: {str(e)}")
            results["charter_decision"] = None

        # 6. Risk Summary
        risk_summary = _calculate_risk_summary(results, request.loading_date_month)
        results["risk_summary"] = risk_summary
        
        if errors:
            results["warnings"] = errors
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full analysis error: {str(e)}\n{traceback.format_exc()}"
        )


def _calculate_risk_summary(results: dict, month: int) -> dict:
    """
    Calculate overall risk indicators from analysis results.
    
    Risk dimensions:
    1. Weather Risk: from lightering weather assessment
    2. Port Congestion: from waiting time data
    3. Rate Volatility: from forecast confidence intervals
    4. Overall Risk Score: weighted average
    """
    weather_score = 50  # Default moderate
    congestion_score = 50
    volatility_score = 50
    
    # Weather risk
    if results.get("lightering") and results["lightering"].get("weather_risk"):
        wr = results["lightering"]["weather_risk"]
        prob = wr.get("weather_delay_probability", 0.1)
        weather_score = min(100, int(prob * 500))  # Scale 0-100
    
    # Port congestion
    if results.get("cost_analysis") and results["cost_analysis"].get("breakdown"):
        wait = results["cost_analysis"]["breakdown"].get("waiting_cost", {})
        total_wait = wait.get("total_wait_days", 5)
        congestion_score = min(100, int(total_wait * 10))  # Scale 0-100
    
    # Rate volatility
    if results.get("forecast") and results["forecast"].get("confidence_intervals"):
        ci = results["forecast"]["confidence_intervals"]
        forecasts = results["forecast"]["forecasts"]
        if forecasts and ci["ci_95"]["upper"] and ci["ci_95"]["lower"]:
            avg_width = sum(
                u - l for u, l in zip(ci["ci_95"]["upper"][:30], ci["ci_95"]["lower"][:30])
            ) / min(30, len(forecasts))
            avg_rate = sum(forecasts[:30]) / min(30, len(forecasts))
            if avg_rate > 0:
                volatility_pct = (avg_width / avg_rate) * 100
                volatility_score = min(100, int(volatility_pct * 2))
    
    # Overall risk (weighted average)
    overall_score = int(0.35 * weather_score + 0.25 * congestion_score + 0.40 * volatility_score)
    
    # Risk level classification
    if overall_score < 30:
        level = "LOW"
        color = "green"
    elif overall_score < 55:
        level = "MODERATE"
        color = "yellow"
    elif overall_score < 75:
        level = "HIGH"
        color = "orange"
    else:
        level = "VERY HIGH"
        color = "red"
    
    return {
        "overall_score": overall_score,
        "overall_level": level,
        "overall_color": color,
        "dimensions": {
            "weather": {"score": weather_score, "label": "Weather Risk"},
            "congestion": {"score": congestion_score, "label": "Port Congestion"},
            "volatility": {"score": volatility_score, "label": "Rate Volatility"},
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
