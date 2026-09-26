import json
import os
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ============================================================
# Data Loading
# ============================================================

def _load_json(filename: str) -> list:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    with open(os.path.join(data_dir, filename), "r") as f:
        return json.load(f)


def get_port_data(port_name: str) -> Optional[Dict]:
    """Look up port data by name."""
    ports = _load_json("ports.json")
    for port in ports:
        if port["name"].lower() == port_name.lower():
            return port
    return None


def get_vessel_data(vessel_class: str, subtype: str = "Standard") -> Optional[Dict]:
    """Look up vessel data by class and subtype."""
    vessels = _load_json("vessels.json")
    for vessel in vessels:
        if vessel["class"].lower() == vessel_class.lower():
            if subtype.lower() == "standard" or vessel["subtype"].lower() == subtype.lower():
                return vessel
    # Fallback: return first match for class
    for vessel in vessels:
        if vessel["class"].lower() == vessel_class.lower():
            return vessel
    return None


def get_route_data(route_code: str) -> Optional[Dict]:
    """Look up route data by code."""
    routes = _load_json("routes.json")
    for route in routes:
        if route["route_code"].lower() == route_code.lower():
            return route
    return None


# ============================================================
# Canal Fee Calculators
# ============================================================

def calculate_suez_canal_fee(dwt: int) -> float:
    """
    Estimate Suez Canal transit fee based on vessel DWT.
    Simplified from Suez Canal Authority tariff schedule.
    Fee = base_rate * SCNT (Suez Canal Net Tonnage)
    SCNT ~ 0.6 * DWT for bulk carriers
    """
    scnt = dwt * 0.6
    if scnt <= 5000:
        rate = 7.88
    elif scnt <= 10000:
        rate = 6.56
    elif scnt <= 20000:
        rate = 5.73
    elif scnt <= 40000:
        rate = 5.08
    else:
        rate = 4.53
    return scnt * rate


def calculate_panama_canal_fee(dwt: int) -> float:
    """
    Estimate Panama Canal transit fee based on vessel DWT.
    PC/UMS tonnage ~ 0.55 * DWT for bulk carriers.
    """
    pcums = dwt * 0.55
    if pcums <= 10000:
        rate = 5.25
    elif pcums <= 20000:
        rate = 5.14
    else:
        rate = 5.01
    return pcums * rate


# ============================================================
# Cost Calculator
# ============================================================

def calculate_total_cost(
    cargo_quantity_tonnes: float,
    route_code: str,
    vessel_class: str,
    freight_rate: float,
    loading_date_month: int = 1,
    cargo_value_per_tonne: float = 100.0,
    bunker_price_per_tonne: float = 580.0,
    allowed_laytime_days: float = 5.0,
    demurrage_rate_per_day: Optional[float] = None,
    vessel_subtype: str = "Standard",
) -> Dict:
    """
    Calculate total delivered cost for a voyage.
    
    Args:
        cargo_quantity_tonnes: Cargo quantity in metric tonnes
        route_code: Route code (e.g., 'C5')
        vessel_class: Vessel class (e.g., 'Capesize')
        freight_rate: Freight rate (USD/tonne or USD/day depending on route)
        loading_date_month: Month of loading (1-12) for weather risk
        cargo_value_per_tonne: Cargo value for insurance calculation
        bunker_price_per_tonne: Current VLSFO bunker price
        allowed_laytime_days: Allowed laytime before demurrage
        demurrage_rate_per_day: Demurrage rate (defaults to 1.5x daily charter rate)
        vessel_subtype: Vessel subtype (e.g., 'Standard', 'Newcastlemax')
    
    Returns:
        Dict with detailed cost breakdown
    """
    route = get_route_data(route_code)
    vessel = get_vessel_data(vessel_class, vessel_subtype)
    
    if not route:
        raise ValueError(f"Route not found: {route_code}")
    if not vessel:
        raise ValueError(f"Vessel class not found: {vessel_class}")
    
    origin_port = get_port_data(route["origin"])
    dest_port = get_port_data(route["destination"])
    
    if not origin_port or not dest_port:
        raise ValueError(f"Port data not found for route {route_code}")
    
    # ---- 1. Freight Cost ----
    freight_cost = freight_rate * cargo_quantity_tonnes
    
    # ---- 2. Port Charges ----
    loading_port_charges = origin_port["port_charges_usd_per_tonne"] * cargo_quantity_tonnes
    discharge_port_charges = dest_port["port_charges_usd_per_tonne"] * cargo_quantity_tonnes
    total_port_charges = loading_port_charges + discharge_port_charges
    
    # ---- 3. Waiting Time Cost ----
    # Expected waiting = avg_waiting_days * (1 / berth_availability)
    daily_vessel_cost = vessel["daily_charter_rate_usd"]
    
    loading_wait = origin_port["avg_waiting_days"] * (1.0 / origin_port["berth_availability"])
    discharge_wait = dest_port["avg_waiting_days"] * (1.0 / dest_port["berth_availability"])
    total_waiting_days = loading_wait + discharge_wait
    waiting_cost = total_waiting_days * daily_vessel_cost
    
    # ---- 4. Demurrage ----
    if demurrage_rate_per_day is None:
        demurrage_rate_per_day = daily_vessel_cost * 1.5
    
    # Estimate actual port time based on cargo quantity and typical loading rate
    # Typical loading rate: ~50,000 tonnes/day for Capesize, scaled by vessel size
    loading_rate = vessel["typical_dwt"] / 3.5  # tonnes per day
    actual_port_days = (cargo_quantity_tonnes / loading_rate) * 2  # load + discharge
    demurrage_days = max(0, actual_port_days - allowed_laytime_days * 2)
    demurrage_cost = demurrage_days * demurrage_rate_per_day
    
    # ---- 5. Weather Disruption Cost ----
    month_str = str(loading_date_month)
    origin_weather_prob = origin_port["weather_delay_prob"].get(month_str, 0.05)
    dest_weather_prob = dest_port["weather_delay_prob"].get(month_str, 0.05)
    
    # Expected delay = probability * average delay duration (2-5 days)
    avg_weather_delay = 3.0  # days
    expected_weather_delay = (origin_weather_prob + dest_weather_prob) * avg_weather_delay
    disruption_cost = expected_weather_delay * daily_vessel_cost
    
    # ---- 6. Canal Transit Fees ----
    canal_fees = 0.0
    canal_name = None
    if route.get("canal_transit"):
        canal_name = route["canal_transit"]
        if "suez" in canal_name.lower():
            canal_fees = calculate_suez_canal_fee(vessel["typical_dwt"])
        elif "panama" in canal_name.lower():
            canal_fees = calculate_panama_canal_fee(vessel["typical_dwt"])
    
    # ---- 7. Insurance ----
    # Marine cargo insurance: typically 0.1-0.3% of cargo value
    insurance_rate = 0.002  # 0.2%
    total_cargo_value = cargo_value_per_tonne * cargo_quantity_tonnes
    insurance_cost = total_cargo_value * insurance_rate
    
    # ---- 8. Bunker Cost ----
    voyage_days = route["typical_voyage_days"]
    total_fuel_consumption = vessel["fuel_consumption_mt_day"] * voyage_days
    bunker_cost = total_fuel_consumption * bunker_price_per_tonne
    
    # ---- Total ----
    total_cost = (
        freight_cost
        + total_port_charges
        + waiting_cost
        + demurrage_cost
        + disruption_cost
        + canal_fees
        + insurance_cost
        + bunker_cost
    )
    
    cost_per_tonne = total_cost / cargo_quantity_tonnes if cargo_quantity_tonnes > 0 else 0
    
    return {
        "total_cost_usd": round(total_cost, 2),
        "cost_per_tonne_usd": round(cost_per_tonne, 2),
        "breakdown": {
            "freight_cost": round(freight_cost, 2),
            "port_charges": {
                "loading": round(loading_port_charges, 2),
                "discharge": round(discharge_port_charges, 2),
                "total": round(total_port_charges, 2),
            },
            "waiting_cost": {
                "loading_wait_days": round(loading_wait, 1),
                "discharge_wait_days": round(discharge_wait, 1),
                "total_wait_days": round(total_waiting_days, 1),
                "cost": round(waiting_cost, 2),
            },
            "demurrage": {
                "demurrage_days": round(demurrage_days, 1),
                "rate_per_day": round(demurrage_rate_per_day, 2),
                "cost": round(demurrage_cost, 2),
            },
            "weather_disruption": {
                "origin_delay_prob": round(origin_weather_prob, 3),
                "dest_delay_prob": round(dest_weather_prob, 3),
                "expected_delay_days": round(expected_weather_delay, 1),
                "cost": round(disruption_cost, 2),
            },
            "canal_fees": {
                "canal": canal_name,
                "cost": round(canal_fees, 2),
            },
            "insurance": {
                "cargo_value": round(total_cargo_value, 2),
                "rate": insurance_rate,
                "cost": round(insurance_cost, 2),
            },
            "bunker": {
                "voyage_days": voyage_days,
                "fuel_consumption_mt": round(total_fuel_consumption, 1),
                "bunker_price": bunker_price_per_tonne,
                "cost": round(bunker_cost, 2),
            },
        },
        "route_info": {
            "route_code": route_code,
            "origin": route["origin"],
            "destination": route["destination"],
            "distance_nm": route["distance_nm"],
            "voyage_days": voyage_days,
        },
        "vessel_info": {
            "class": vessel["class"],
            "subtype": vessel["subtype"],
            "dwt": vessel["typical_dwt"],
            "daily_cost": daily_vessel_cost,
        },
    }


def compare_vessel_options(
    cargo_quantity_tonnes: float,
    route_code: str,
    freight_rate: float,
    loading_date_month: int = 1,
    cargo_material: str = "Coal",
) -> Dict:
    """
    Compare delivered cost across only the vessels that pass the same
    cargo + origin/destination port constraints used by the optimizer.
    """
    route = get_route_data(route_code)
    if not route:
        raise ValueError(f"Route not found: {route_code}")

    from .vessel_optimizer import recommend_vessel
    feasibility = recommend_vessel(
        cargo_material=cargo_material,
        cargo_quantity_tonnes=cargo_quantity_tonnes,
        route_code=route_code,
    )

    if feasibility.get("status") not in {"FEASIBLE", "FEASIBLE_SPLIT"}:
        return {
            "route_code": route_code,
            "cargo_quantity": cargo_quantity_tonnes,
            "cargo_material": cargo_material,
            "options": [],
            "recommended": None,
            "message": feasibility.get("message", "No feasible vessel found."),
            "rejected": feasibility.get("rejected", []),
        }

    feasible_names = {
        (x["class"], x["subtype"]) for x in
        [feasibility["recommended"]] + feasibility.get("alternatives", [])
    }

    results = []
    for vessel in _load_json("vessels.json"):
        if (vessel["class"], vessel["subtype"]) not in feasible_names:
            continue
        try:
            cost = calculate_total_cost(
                cargo_quantity_tonnes=cargo_quantity_tonnes,
                route_code=route_code,
                vessel_class=vessel["class"],
                freight_rate=freight_rate,
                loading_date_month=loading_date_month,
                vessel_subtype=vessel["subtype"],
            )
            results.append({
                "vessel": f"{vessel['class']} ({vessel['subtype']})",
                "class": vessel["class"],
                "subtype": vessel["subtype"],
                "total_cost_usd": cost["total_cost_usd"],
                "cost_per_tonne_usd": cost["cost_per_tonne_usd"],
                "breakdown": cost["breakdown"],
                "feasibility_score": next(
                    (x["feasibility_score"] for x in
                     [feasibility["recommended"]] + feasibility.get("alternatives", [])
                     if x["class"] == vessel["class"] and x["subtype"] == vessel["subtype"]),
                    None,
                ),
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["cost_per_tonne_usd"])

    recommended_key = (
        feasibility["recommended"]["class"],
        feasibility["recommended"]["subtype"],
    )
    optimizer_recommended = next(
        (x for x in results if (x["class"], x["subtype"]) == recommended_key),
        results[0] if results else None,
    )

    return {
        "route_code": route_code,
        "cargo_quantity": cargo_quantity_tonnes,
        "cargo_material": cargo_material,
        "options": results,
        "recommended": optimizer_recommended,
        "selection_basis": "Feasibility first; material/parcel/port constraints determine the recommended vessel.",
    }

