"""
Vessel Type Optimization
========================
Selects a feasible bulk-carrier class from Handysize, Supramax,
Panamax and Capesize using:
- cargo material and parcel size
- origin + destination port draft/LOA/beam constraints
- vessel cargo capacity
- port cargo-handling capability
- expected waiting/turnaround exposure

The port figures in this student prototype are synthetic/demo planning inputs.
They are not live nautical operating limits.
"""

import json
import os
import math
from typing import Dict, List, Optional


def _load_json(filename: str):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def _find(items, key, value):
    value = str(value).lower()
    for item in items:
        if str(item.get(key, "")).lower() == value:
            return item
    return None


def get_route(route_code: str) -> Dict:
    route = _find(_load_json("routes.json"), "route_code", route_code)
    if not route:
        raise ValueError(f"Route not found: {route_code}")
    return route


def _estimate_loaded_draft(vessel: Dict, cargo_tonnes: float) -> float:
    load_factor = min(1.0, max(0.0, cargo_tonnes / vessel["typical_dwt"]))
    min_draft = vessel["tpc_curve"]["draft_m"][0]
    return min_draft + (vessel["max_draft_m"] - min_draft) * load_factor


def _material_fit(material: str, vessel_class: str) -> float:
    material = material.lower()
    # Preference, not a hard exclusion: the port/capacity checks decide feasibility.
    if material == "coal":
        return {
            "Handysize": 0.65,
            "Supramax": 0.90,
            "Panamax": 1.00,
            "Capesize": 0.95,
        }.get(vessel_class, 0.70)
    if material == "steel":
        return {
            "Handysize": 1.00,
            "Supramax": 0.95,
            "Panamax": 0.82,
            "Capesize": 0.65,
        }.get(vessel_class, 0.70)
    return 0.80


def _class_order(vessel_class: str) -> int:
    return {"Handysize": 1, "Supramax": 2, "Panamax": 3, "Capesize": 4}.get(vessel_class, 0)


def recommend_vessel(
    cargo_material: str,
    cargo_quantity_tonnes: float,
    route_code: str,
) -> Dict:
    routes = _load_json("routes.json")
    vessels = _load_json("vessels.json")
    ports = _load_json("ports.json")

    route = _find(routes, "route_code", route_code)
    if not route:
        raise ValueError(f"Route not found: {route_code}")

    origin = _find(ports, "name", route["origin"])
    destination = _find(ports, "name", route["destination"])
    if not origin or not destination:
        raise ValueError("Port constraint data missing for selected route")

    candidates: List[Dict] = []
    rejected: List[Dict] = []

    for vessel in vessels:
        vessel_name = f"{vessel['class']} ({vessel['subtype']})"
        reasons = []

        # A small operational margin prevents recommending a vessel at 100% DWT.
        usable_capacity = vessel["typical_dwt"] * 0.95
        if cargo_quantity_tonnes > usable_capacity:
            reasons.append(f"parcel exceeds 95% usable capacity ({usable_capacity:,.0f} t)")

        loaded_draft = _estimate_loaded_draft(vessel, cargo_quantity_tonnes)
        draft_limit = min(origin["max_draft_m"], destination["max_draft_m"])
        if loaded_draft > draft_limit:
            reasons.append(f"loaded draft {loaded_draft:.1f} m exceeds route limit {draft_limit:.1f} m")

        loa_limit = min(origin.get("max_loa_m", 999), destination.get("max_loa_m", 999))
        beam_limit = min(origin.get("max_beam_m", 999), destination.get("max_beam_m", 999))
        if vessel["loa_m"] > loa_limit:
            reasons.append(f"LOA {vessel['loa_m']:.0f} m exceeds route limit {loa_limit:.0f} m")
        if vessel["beam_m"] > beam_limit:
            reasons.append(f"beam {vessel['beam_m']:.1f} m exceeds route limit {beam_limit:.1f} m")

        if reasons:
            rejected.append({"vessel": vessel_name, "reasons": reasons})
            continue

        # Higher score is better. Cost/turnaround is used as a tie-breaker.
        utilization = cargo_quantity_tonnes / vessel["typical_dwt"]
        utilization_score = max(0.0, 1.0 - abs(0.72 - utilization))
        material_score = _material_fit(cargo_material, vessel["class"])

        origin_handling = origin.get("cargo_handling_rate_tpd", 50000)
        destination_handling = destination.get("cargo_handling_rate_tpd", 50000)
        handling_days = cargo_quantity_tonnes / max(1, min(origin_handling, destination_handling))
        waiting_days = (
            origin.get("avg_waiting_days", 3.0) / max(origin.get("berth_availability", 0.7), 0.1)
            + destination.get("avg_waiting_days", 3.0) / max(destination.get("berth_availability", 0.7), 0.1)
        )
        turnaround_score = max(0.0, 1.0 - min(1.0, (handling_days + waiting_days) / 25.0))
        score = 100 * (
            0.40 * material_score
            + 0.30 * utilization_score
            + 0.20 * turnaround_score
            + 0.10 * (1.0 if loaded_draft <= draft_limit else 0.0)
        )

        candidates.append({
            "vessel": vessel_name,
            "class": vessel["class"],
            "subtype": vessel["subtype"],
            "dwt": vessel["typical_dwt"],
            "usable_capacity_tonnes": round(usable_capacity, 0),
            "estimated_loaded_draft_m": round(loaded_draft, 2),
            "route_draft_limit_m": round(draft_limit, 2),
            "loa_m": vessel["loa_m"],
            "beam_m": vessel["beam_m"],
            "handling_days_est": round(handling_days, 1),
            "expected_waiting_days": round(waiting_days, 1),
            "cargo_utilization_pct": round(utilization * 100, 1),
            "material_fit_score": round(material_score * 100, 1),
            "feasibility_score": round(score, 1),
        })

    # Prefer feasible candidates with the highest suitability score; use vessel
    # class size as a deterministic tie-breaker.
    candidates.sort(
        key=lambda x: (x["feasibility_score"], -_class_order(x["class"])),
        reverse=True,
    )

    recommendation = candidates[0] if candidates else None

    # If the full parcel is too large for one vessel, optimize a multiple-voyage
    # plan. This directly supports PS-26006's multiple-voyage contract objective.
    if not recommendation:
        split_candidates = []
        route_draft_limit = min(origin["max_draft_m"], destination["max_draft_m"])
        for vessel in vessels:
            usable_capacity = vessel["typical_dwt"] * 0.95
            # Maximum parcel that satisfies the route draft, using the vessel's
            # simplified draft-load curve.
            min_draft = vessel["tpc_curve"]["draft_m"][0]
            if route_draft_limit <= min_draft:
                continue
            draft_fraction = min(
                1.0,
                (route_draft_limit - min_draft) /
                max(0.01, vessel["max_draft_m"] - min_draft)
            )
            draft_limited_capacity = vessel["typical_dwt"] * draft_fraction
            voyage_capacity = min(usable_capacity, draft_limited_capacity)
            voyages = max(1, int(math.ceil(cargo_quantity_tonnes / voyage_capacity)))
            per_voyage = cargo_quantity_tonnes / voyages
            loaded_draft = _estimate_loaded_draft(vessel, per_voyage)
            loa_limit = min(origin.get("max_loa_m", 999), destination.get("max_loa_m", 999))
            beam_limit = min(origin.get("max_beam_m", 999), destination.get("max_beam_m", 999))
            if loaded_draft > route_draft_limit or vessel["loa_m"] > loa_limit or vessel["beam_m"] > beam_limit:
                continue

            utilization = per_voyage / vessel["typical_dwt"]
            material_score = _material_fit(cargo_material, vessel["class"])
            handling_days = per_voyage / max(1, min(
                origin.get("cargo_handling_rate_tpd", 50000),
                destination.get("cargo_handling_rate_tpd", 50000)
            ))
            waiting_days = (
                origin.get("avg_waiting_days", 3.0) / max(origin.get("berth_availability", 0.7), 0.1)
                + destination.get("avg_waiting_days", 3.0) / max(destination.get("berth_availability", 0.7), 0.1)
            )
            # Fewer voyages are preferred, then material fit and utilization.
            score = 100 * (
                0.45 * (1.0 / voyages)
                + 0.30 * material_score
                + 0.15 * max(0.0, 1.0 - abs(0.72 - utilization))
                + 0.10 * max(0.0, 1.0 - min(1.0, (handling_days + waiting_days) / 25.0))
            )
            split_candidates.append({
                "vessel": f"{vessel['class']} ({vessel['subtype']})",
                "class": vessel["class"],
                "subtype": vessel["subtype"],
                "dwt": vessel["typical_dwt"],
                "usable_capacity_tonnes": round(usable_capacity, 0),
                "split_voyages": voyages,
                "per_voyage_cargo_tonnes": round(per_voyage, 0),
                "estimated_loaded_draft_m": round(loaded_draft, 2),
                "route_draft_limit_m": round(route_draft_limit, 2),
                "loa_m": vessel["loa_m"],
                "beam_m": vessel["beam_m"],
                "handling_days_est": round(handling_days, 1),
                "expected_waiting_days": round(waiting_days, 1),
                "cargo_utilization_pct": round(utilization * 100, 1),
                "material_fit_score": round(material_score * 100, 1),
                "feasibility_score": round(score, 1),
            })

        split_candidates.sort(key=lambda x: (x["split_voyages"], -x["feasibility_score"]))
        if split_candidates:
            recommendation = split_candidates[0]
            return {
                "status": "FEASIBLE_SPLIT",
                "cargo_material": cargo_material,
                "cargo_quantity_tonnes": cargo_quantity_tonnes,
                "route": {
                    "route_code": route_code,
                    "name": route["name"],
                    "origin": route["origin"],
                    "destination": route["destination"],
                },
                "port_constraints": {
                    "origin": {
                        "name": origin["name"], "max_draft_m": origin["max_draft_m"],
                        "max_loa_m": origin.get("max_loa_m"), "max_beam_m": origin.get("max_beam_m"),
                        "cargo_handling_rate_tpd": origin.get("cargo_handling_rate_tpd"),
                    },
                    "destination": {
                        "name": destination["name"], "max_draft_m": destination["max_draft_m"],
                        "max_loa_m": destination.get("max_loa_m"), "max_beam_m": destination.get("max_beam_m"),
                        "cargo_handling_rate_tpd": destination.get("cargo_handling_rate_tpd"),
                    },
                },
                "recommended": recommendation,
                "alternatives": split_candidates[1:5],
                "rejected": rejected,
                "explanation": (
                    f"The {cargo_quantity_tonnes:,.0f}-tonne parcel is too large for one feasible "
                    f"voyage. The model proposes {recommendation['split_voyages']} "
                    f"{recommendation['class']} voyages of about "
                    f"{recommendation['per_voyage_cargo_tonnes']:,.0f} tonnes each, while checking "
                    f"draft, LOA and beam at both ports."
                ),
            }

        return {
            "status": "NO_FEASIBLE_VESSEL",
            "cargo_material": cargo_material,
            "cargo_quantity_tonnes": cargo_quantity_tonnes,
            "route": {
                "route_code": route_code, "name": route["name"],
                "origin": route["origin"], "destination": route["destination"],
            },
            "port_constraints": {
                "origin": {
                    "name": origin["name"], "max_draft_m": origin["max_draft_m"],
                    "max_loa_m": origin.get("max_loa_m"), "max_beam_m": origin.get("max_beam_m"),
                    "cargo_handling_rate_tpd": origin.get("cargo_handling_rate_tpd"),
                },
                "destination": {
                    "name": destination["name"], "max_draft_m": destination["max_draft_m"],
                    "max_loa_m": destination.get("max_loa_m"), "max_beam_m": destination.get("max_beam_m"),
                    "cargo_handling_rate_tpd": destination.get("cargo_handling_rate_tpd"),
                },
            },
            "recommended": None, "alternatives": [], "rejected": rejected,
            "message": "No vessel in the modeled fleet satisfies the parcel and port constraints, even after splitting the parcel.",
        }

    return {
        "status": "FEASIBLE",
        "cargo_material": cargo_material,
        "cargo_quantity_tonnes": cargo_quantity_tonnes,
        "route": {
            "route_code": route_code,
            "name": route["name"],
            "origin": route["origin"],
            "destination": route["destination"],
        },
        "port_constraints": {
            "origin": {
                "name": origin["name"],
                "max_draft_m": origin["max_draft_m"],
                "max_loa_m": origin.get("max_loa_m"),
                "max_beam_m": origin.get("max_beam_m"),
                "cargo_handling_rate_tpd": origin.get("cargo_handling_rate_tpd"),
            },
            "destination": {
                "name": destination["name"],
                "max_draft_m": destination["max_draft_m"],
                "max_loa_m": destination.get("max_loa_m"),
                "max_beam_m": destination.get("max_beam_m"),
                "cargo_handling_rate_tpd": destination.get("cargo_handling_rate_tpd"),
            },
        },
        "recommended": recommendation,
        "alternatives": candidates[1:5],
        "rejected": rejected,
        "explanation": (
            f"{recommendation['class']} ({recommendation['subtype']}) is the selected "
            f"feasible option after checking cargo quantity, {cargo_material.lower()} "
            f"parcel suitability, draft, LOA, beam and expected port turnaround."
        ),
    }
