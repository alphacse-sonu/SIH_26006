"""Vessels API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.vessel import Vessel, VesselType, VesselStatus
from app.schemas.vessel import (
    VesselResponse,
    VesselTypeResponse,
    VesselCreate,
    VesselTypeCreate,
    VesselOptimizationRequest,
    VesselOptimizationResponse
)

router = APIRouter()


@router.get("/types", response_model=List[VesselTypeResponse])
async def get_vessel_types(db: Session = Depends(get_db)):
    """Get all vessel type specifications"""
    types = db.query(VesselType).all()
    return types


@router.get("/types/{type_name}", response_model=VesselTypeResponse)
async def get_vessel_type(type_name: str, db: Session = Depends(get_db)):
    """Get specific vessel type specifications"""
    vessel_type = db.query(VesselType).filter(
        VesselType.name.ilike(type_name)
    ).first()
    
    if not vessel_type:
        raise HTTPException(status_code=404, detail="Vessel type not found")
    return vessel_type


@router.get("/", response_model=List[VesselResponse])
async def get_vessels(
    vessel_type: Optional[str] = None,
    status: Optional[VesselStatus] = None,
    min_dwt: Optional[float] = None,
    max_dwt: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get list of vessels with optional filters"""
    query = db.query(Vessel)
    
    if vessel_type:
        query = query.filter(Vessel.vessel_type.ilike(vessel_type))
    if status:
        query = query.filter(Vessel.status == status)
    if min_dwt:
        query = query.filter(Vessel.dwt >= min_dwt)
    if max_dwt:
        query = query.filter(Vessel.dwt <= max_dwt)
    
    vessels = query.offset(skip).limit(limit).all()
    return vessels


@router.get("/{vessel_id}", response_model=VesselResponse)
async def get_vessel(vessel_id: int, db: Session = Depends(get_db)):
    """Get specific vessel details"""
    vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return vessel


@router.post("/", response_model=VesselResponse)
async def create_vessel(vessel_data: VesselCreate, db: Session = Depends(get_db)):
    """Create a new vessel entry"""
    vessel = Vessel(**vessel_data.model_dump())
    db.add(vessel)
    db.commit()
    db.refresh(vessel)
    return vessel


@router.post("/types", response_model=VesselTypeResponse)
async def create_vessel_type(
    type_data: VesselTypeCreate,
    db: Session = Depends(get_db)
):
    """Create a new vessel type specification"""
    vessel_type = VesselType(**type_data.model_dump())
    db.add(vessel_type)
    db.commit()
    db.refresh(vessel_type)
    return vessel_type


@router.post("/optimize", response_model=VesselOptimizationResponse)
async def optimize_vessel_selection(
    request: VesselOptimizationRequest,
    db: Session = Depends(get_db)
):
    """Recommend optimal vessel type for given cargo and route"""
    from app.models.port import PortConstraint
    from app.models.route import Route
    
    # Get port constraints
    origin_constraint = db.query(PortConstraint).filter(
        PortConstraint.port_id == request.origin_port_id
    ).first()
    
    dest_constraint = db.query(PortConstraint).filter(
        PortConstraint.port_id == request.destination_port_id
    ).first()
    
    # Get all vessel types
    vessel_types = db.query(VesselType).all()
    
    recommendations = []
    
    for vt in vessel_types:
        score = 100
        issues = []
        
        # Check cargo capacity
        if vt.max_dwt < request.cargo_volume:
            score -= 50
            issues.append(f"Insufficient capacity: {vt.max_dwt} DWT vs {request.cargo_volume} tons required")
        elif vt.min_dwt > request.cargo_volume * 1.5:
            score -= 20
            issues.append(f"Vessel too large for cargo: minimum {vt.min_dwt} DWT")
        
        # Check origin port constraints
        if origin_constraint:
            if origin_constraint.max_dwt and vt.typical_dwt and vt.typical_dwt > origin_constraint.max_dwt:
                score -= 40
                issues.append(f"Exceeds origin port DWT limit")
            if origin_constraint.max_draft and vt.typical_draft and vt.typical_draft > origin_constraint.max_draft:
                score -= 40
                issues.append(f"Exceeds origin port draft limit")
        
        # Check destination port constraints
        if dest_constraint:
            if dest_constraint.max_dwt and vt.typical_dwt and vt.typical_dwt > dest_constraint.max_dwt:
                score -= 40
                issues.append(f"Exceeds destination port DWT limit")
            if dest_constraint.max_draft and vt.typical_draft and vt.typical_draft > dest_constraint.max_draft:
                score -= 40
                issues.append(f"Exceeds destination port draft limit")
        
        # Calculate efficiency score
        if vt.typical_dwt:
            utilization = min(request.cargo_volume / vt.typical_dwt, 1.0)
            efficiency_bonus = utilization * 20
            score += efficiency_bonus
        
        recommendations.append({
            "vessel_type": vt.name,
            "score": max(0, min(100, score)),
            "issues": issues,
            "estimated_cost": vt.daily_charter_rate_high * 30 if vt.daily_charter_rate_high else None,
            "capacity_utilization": utilization if vt.typical_dwt else None
        })
    
    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return VesselOptimizationResponse(
        cargo_volume=request.cargo_volume,
        origin_port_id=request.origin_port_id,
        destination_port_id=request.destination_port_id,
        recommendations=recommendations,
        best_choice=recommendations[0]["vessel_type"] if recommendations else None
    )
