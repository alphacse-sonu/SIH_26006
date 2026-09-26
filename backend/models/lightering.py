"""
Lightering Optimization Module
===============================
Handles cases where a vessel's draft exceeds port depth limits.
Calculates optimal lightering quantities using TPC (Tonnes Per Centimetre
Immersion) curves and compares direct berthing vs. lightering costs.

Key Concepts:
- TPC (Tonnes Per Centimetre): The weight required to change a vessel's
  draft by 1 cm. Varies with draft due to hull shape.
- Lightering: Ship-to-ship (STS) cargo transfer at anchorage to reduce
  draft before entering a draft-restricted port.

Mathematical Formulation:
    cargo_to_lighter = integral from port_draft to vessel_draft of TPC(d) dd
    
    Approximated as:
    cargo_to_lighter = sum over each cm from port_draft to vessel_draft of TPC(d)
    
    In practice, using linear interpolation of TPC curve:
    cargo_to_lighter ≈ (vessel_draft - port_draft) * 100 * avg_TPC
    where avg_TPC is the average TPC over the draft range

References:
- Rawson & Tupper (2001), "Basic Ship Theory", 5th Edition
- IMO Guidelines for Ship-to-Ship Transfer Operations
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import os


def _load_json(filename: str) -> list:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    with open(os.path.join(data_dir, filename), "r") as f:
        return json.load(f)


def interpolate_tpc(tpc_curve: Dict, target_draft: float) -> float:
    """
    Interpolate TPC value at a given draft using the vessel's TPC curve.
    Uses linear interpolation between known data points.
    
    Args:
        tpc_curve: Dict with 'draft_m' and 'tpc_tonnes' arrays
        target_draft: Draft in metres to interpolate at
    
    Returns:
        TPC value in tonnes/cm at the target draft
    """
    drafts = tpc_curve["draft_m"]
    tpcs = tpc_curve["tpc_tonnes"]
    
    if target_draft <= drafts[0]:
        return tpcs[0]
    if target_draft >= drafts[-1]:
        return tpcs[-1]
    
    # Find bracketing points
    for i in range(len(drafts) - 1):
        if drafts[i] <= target_draft <= drafts[i + 1]:
            # Linear interpolation
            fraction = (target_draft - drafts[i]) / (drafts[i + 1] - drafts[i])
            return tpcs[i] + fraction * (tpcs[i + 1] - tpcs[i])
    
    return tpcs[-1]


def calculate_lightering_quantity(
    vessel_draft: float,
    port_max_draft: float,
    tpc_curve: Dict,
    safety_margin_m: float = 0.5,
) -> Dict:
    """
    Calculate the quantity of cargo that needs to be lightered.
    
    Uses numerical integration of the TPC curve over the draft range
    that needs to be reduced.
    
    Args:
        vessel_draft: Current vessel draft in metres (fully loaded)
        port_max_draft: Maximum allowable draft at port in metres
        tpc_curve: Vessel's TPC curve data
        safety_margin_m: Under-keel clearance safety margin (default 0.5m)
    
    Returns:
        Dict with lightering quantity and calculation details
    
    Mathematical detail:
        target_draft = port_max_draft - safety_margin
        draft_reduction = vessel_draft - target_draft (in metres)
        
        cargo_to_lighter = integral(TPC(d), d=target_draft to vessel_draft) * 100
        (multiply by 100 to convert metres to centimetres)
        
        We use the trapezoidal rule with 1cm steps for accuracy.
    """
    target_draft = port_max_draft - safety_margin_m
    
    if vessel_draft <= target_draft:
        return {
            "lightering_required": False,
            "vessel_draft_m": vessel_draft,
            "port_max_draft_m": port_max_draft,
            "target_draft_m": target_draft,
            "draft_excess_m": 0,
            "cargo_to_lighter_tonnes": 0,
            "message": "Vessel can berth directly - no lightering needed",
        }
    
    draft_excess = vessel_draft - target_draft
    
    # Numerical integration using trapezoidal rule with 1cm steps
    n_steps = int(draft_excess * 100)  # Number of centimetre steps
    total_cargo = 0.0
    tpc_values = []
    
    for step in range(n_steps):
        current_draft = target_draft + step / 100.0
        tpc_at_draft = interpolate_tpc(tpc_curve, current_draft)
        total_cargo += tpc_at_draft  # Each step is 1 cm, TPC is tonnes/cm
        tpc_values.append({"draft_m": round(current_draft, 2), "tpc": round(tpc_at_draft, 1)})
    
    # Average TPC over the range
    avg_tpc = total_cargo / n_steps if n_steps > 0 else 0
    
    return {
        "lightering_required": True,
        "vessel_draft_m": vessel_draft,
        "port_max_draft_m": port_max_draft,
        "target_draft_m": round(target_draft, 2),
        "safety_margin_m": safety_margin_m,
        "draft_excess_m": round(draft_excess, 2),
        "draft_reduction_cm": n_steps,
        "avg_tpc_tonnes_per_cm": round(avg_tpc, 1),
        "cargo_to_lighter_tonnes": round(total_cargo, 0),
        "tpc_profile": tpc_values[:10],  # Sample points for visualization
    }


def calculate_lightering_cost(
    cargo_to_lighter_tonnes: float,
    feeder_vessel_daily_rate: float = 12000,
    sts_operation_days: float = 2.0,
    sts_fixed_cost: float = 50000,
    cargo_loss_rate: float = 0.002,
    cargo_value_per_tonne: float = 100.0,
) -> Dict:
    """
    Calculate the cost of lightering operations.
    
    Cost components:
    1. Feeder vessel hire = daily_rate * operation_days
    2. STS operation fixed cost (tugs, fenders, mooring)
    3. Cargo loss risk = loss_rate * cargo_quantity * cargo_value
    4. Additional insurance for STS operations
    
    Args:
        cargo_to_lighter_tonnes: Quantity to transfer
        feeder_vessel_daily_rate: Daily hire rate for feeder vessel
        sts_operation_days: Expected duration of STS transfer
        sts_fixed_cost: Fixed costs (tugs, equipment, personnel)
        cargo_loss_rate: Expected cargo loss rate (0.1-0.3%)
        cargo_value_per_tonne: Value of cargo for loss calculation
    """
    feeder_hire = feeder_vessel_daily_rate * sts_operation_days
    cargo_loss_cost = cargo_to_lighter_tonnes * cargo_loss_rate * cargo_value_per_tonne
    sts_insurance = cargo_to_lighter_tonnes * cargo_value_per_tonne * 0.001  # 0.1% additional
    
    total_lightering_cost = feeder_hire + sts_fixed_cost + cargo_loss_cost + sts_insurance
    cost_per_tonne = total_lightering_cost / cargo_to_lighter_tonnes if cargo_to_lighter_tonnes > 0 else 0
    
    return {
        "total_cost_usd": round(total_lightering_cost, 2),
        "cost_per_tonne_usd": round(cost_per_tonne, 2),
        "breakdown": {
            "feeder_vessel_hire": round(feeder_hire, 2),
            "sts_fixed_cost": round(sts_fixed_cost, 2),
            "cargo_loss_cost": round(cargo_loss_cost, 2),
            "sts_insurance": round(sts_insurance, 2),
        },
        "assumptions": {
            "feeder_daily_rate": feeder_vessel_daily_rate,
            "operation_days": sts_operation_days,
            "cargo_loss_rate_pct": cargo_loss_rate * 100,
        },
    }


def assess_weather_risk_for_sts(
    port_name: str,
    month: int,
    wave_height_threshold_m: float = 1.5,
) -> Dict:
    """
    Assess weather risk for ship-to-ship operations.
    
    STS operations are typically suspended when significant wave height
    exceeds 1.5m (Hs > 1.5m) per OCIMF guidelines.
    
    Args:
        port_name: Name of the port/anchorage
        month: Month (1-12)
        wave_height_threshold_m: Max wave height for STS ops
    
    Returns:
        Risk assessment dict
    """
    ports = _load_json("ports.json")
    port = None
    for p in ports:
        if p["name"].lower() == port_name.lower():
            port = p
            break
    
    if not port:
        return {"error": f"Port not found: {port_name}"}
    
    weather_prob = port["weather_delay_prob"].get(str(month), 0.05)
    
    # Risk classification
    if weather_prob < 0.08:
        risk_level = "LOW"
        risk_color = "green"
        recommendation = "Favorable weather window expected. STS operations can proceed."
    elif weather_prob < 0.15:
        risk_level = "MODERATE"
        risk_color = "yellow"
        recommendation = "Some weather risk. Plan for potential 1-2 day delays."
    elif weather_prob < 0.22:
        risk_level = "HIGH"
        risk_color = "orange"
        recommendation = "Significant weather risk. Consider alternative timing or direct berthing if possible."
    else:
        risk_level = "VERY HIGH"
        risk_color = "red"
        recommendation = "Monsoon/storm season. STS operations highly risky. Strongly recommend alternative approach."
    
    # Estimate weather window availability
    # Assume weather events last 2-4 days on average
    avg_event_duration = 3.0
    expected_events_per_month = weather_prob * 30 / avg_event_duration
    available_days = 30 - (expected_events_per_month * avg_event_duration)
    
    return {
        "port": port_name,
        "month": month,
        "weather_delay_probability": round(weather_prob, 3),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "recommendation": recommendation,
        "wave_height_threshold_m": wave_height_threshold_m,
        "estimated_available_days": round(max(0, available_days), 1),
        "estimated_weather_events": round(expected_events_per_month, 1),
    }


def full_lightering_analysis(
    cargo_quantity_tonnes: float,
    vessel_class: str,
    port_name: str,
    month: int = 1,
    cargo_value_per_tonne: float = 100.0,
    vessel_subtype: str = "Standard",
) -> Dict:
    """
    Complete lightering analysis: determine if lightering is needed,
    calculate costs, assess weather risk, and compare options.
    
    Returns comprehensive analysis with recommendation.
    """
    # Get vessel and port data
    vessels = _load_json("vessels.json")
    vessel = None
    for v in vessels:
        if v["class"].lower() == vessel_class.lower():
            if vessel_subtype.lower() == "standard" or v["subtype"].lower() == vessel_subtype.lower():
                vessel = v
                break
    if not vessel:
        for v in vessels:
            if v["class"].lower() == vessel_class.lower():
                vessel = v
                break
    
    if not vessel:
        raise ValueError(f"Vessel class not found: {vessel_class}")
    
    port = None
    ports = _load_json("ports.json")
    for p in ports:
        if p["name"].lower() == port_name.lower():
            port = p
            break
    
    if not port:
        raise ValueError(f"Port not found: {port_name}")
    
    # Calculate vessel draft when loaded with specified cargo
    # Approximate: loaded_draft = max_draft * (cargo / dwt)
    load_factor = min(1.0, cargo_quantity_tonnes / vessel["typical_dwt"])
    min_draft = vessel["tpc_curve"]["draft_m"][0]
    max_draft = vessel["max_draft_m"]
    estimated_draft = min_draft + (max_draft - min_draft) * load_factor
    
    # Calculate lightering quantity
    lighter_calc = calculate_lightering_quantity(
        vessel_draft=estimated_draft,
        port_max_draft=port["max_draft_m"],
        tpc_curve=vessel["tpc_curve"],
    )
    
    # Calculate costs for both options
    direct_berthing_cost = 0.0
    lightering_cost_data = None
    weather_risk = None
    
    if lighter_calc["lightering_required"]:
        # Option A: Lightering
        lightering_cost_data = calculate_lightering_cost(
            cargo_to_lighter_tonnes=lighter_calc["cargo_to_lighter_tonnes"],
            cargo_value_per_tonne=cargo_value_per_tonne,
        )
        
        # Weather risk for STS
        weather_risk = assess_weather_risk_for_sts(port_name, month)
        
        # Option B: Direct berthing (only if port can be dredged or vessel partially loaded)
        # Cost of partial loading = lost revenue from reduced cargo
        reducible_cargo = lighter_calc["cargo_to_lighter_tonnes"]
        lost_revenue_per_tonne = 5.0  # Estimated opportunity cost
        direct_berthing_cost = reducible_cargo * lost_revenue_per_tonne
        
        # Recommendation
        if lightering_cost_data["total_cost_usd"] < direct_berthing_cost:
            recommendation = "LIGHTER"
            reason = f"Lightering is ${direct_berthing_cost - lightering_cost_data['total_cost_usd']:,.0f} cheaper than reducing cargo."
        else:
            recommendation = "REDUCE_CARGO"
            reason = f"Reducing cargo by {reducible_cargo:,.0f} tonnes is ${lightering_cost_data['total_cost_usd'] - direct_berthing_cost:,.0f} cheaper than lightering."
        
        # Override if weather risk is very high
        if weather_risk and weather_risk["risk_level"] == "VERY HIGH":
            recommendation = "REDUCE_CARGO"
            reason = f"Weather risk too high for STS operations in month {month}. Recommend reducing cargo instead."
    else:
        recommendation = "DIRECT_BERTH"
        reason = "Vessel draft is within port limits. No lightering needed."
    
    return {
        "vessel": {
            "class": vessel["class"],
            "subtype": vessel["subtype"],
            "max_draft_m": vessel["max_draft_m"],
            "estimated_loaded_draft_m": round(estimated_draft, 2),
            "dwt": vessel["typical_dwt"],
        },
        "port": {
            "name": port["name"],
            "max_draft_m": port["max_draft_m"],
            "country": port["country"],
        },
        "cargo_quantity_tonnes": cargo_quantity_tonnes,
        "lightering_calculation": lighter_calc,
        "lightering_cost": lightering_cost_data,
        "direct_berthing_cost": round(direct_berthing_cost, 2),
        "weather_risk": weather_risk,
        "recommendation": recommendation,
        "reason": reason,
    }
