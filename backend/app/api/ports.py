"""Ports API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.port import Port, PortConstraint, Country, PortType
from app.schemas.port import (
    PortResponse,
    PortDetailResponse,
    PortConstraintResponse,
    PortCreate,
    PortConstraintCreate
)

router = APIRouter()


@router.get("/", response_model=List[PortResponse])
async def get_ports(
    country: Optional[Country] = None,
    port_type: Optional[PortType] = None,
    region: Optional[str] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get list of ports with optional filters"""
    query = db.query(Port).filter(Port.is_active == is_active)
    
    if country:
        query = query.filter(Port.country == country)
    if port_type:
        query = query.filter(Port.port_type == port_type)
    if region:
        query = query.filter(Port.region.ilike(f"%{region}%"))
    
    ports = query.offset(skip).limit(limit).all()
    return ports


@router.get("/indian-east-coast", response_model=List[PortDetailResponse])
async def get_indian_east_coast_ports(db: Session = Depends(get_db)):
    """Get all Indian East Coast ports with their constraints"""
    ports = db.query(Port).filter(
        Port.country == Country.INDIA,
        Port.region == "East Coast",
        Port.is_active == True
    ).all()
    return ports


@router.get("/loading-ports", response_model=List[PortDetailResponse])
async def get_loading_ports(
    country: Optional[Country] = None,
    db: Session = Depends(get_db)
):
    """Get loading ports (origin ports for cargo)"""
    query = db.query(Port).filter(
        Port.port_type.in_([PortType.LOADING, PortType.BOTH]),
        Port.is_active == True
    )
    
    if country:
        query = query.filter(Port.country == country)
    
    ports = query.all()
    return ports


@router.get("/{port_id}", response_model=PortDetailResponse)
async def get_port(port_id: int, db: Session = Depends(get_db)):
    """Get detailed port information including constraints"""
    port = db.query(Port).filter(Port.id == port_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")
    return port


@router.get("/{port_id}/constraints", response_model=PortConstraintResponse)
async def get_port_constraints(port_id: int, db: Session = Depends(get_db)):
    """Get port infrastructure constraints"""
    constraint = db.query(PortConstraint).filter(
        PortConstraint.port_id == port_id
    ).first()
    
    if not constraint:
        raise HTTPException(status_code=404, detail="Port constraints not found")
    return constraint


@router.post("/", response_model=PortResponse)
async def create_port(port_data: PortCreate, db: Session = Depends(get_db)):
    """Create a new port"""
    port = Port(**port_data.model_dump())
    db.add(port)
    db.commit()
    db.refresh(port)
    return port


@router.post("/{port_id}/constraints", response_model=PortConstraintResponse)
async def create_port_constraints(
    port_id: int,
    constraint_data: PortConstraintCreate,
    db: Session = Depends(get_db)
):
    """Create or update port constraints"""
    # Check if port exists
    port = db.query(Port).filter(Port.id == port_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")
    
    # Check if constraints already exist
    existing = db.query(PortConstraint).filter(
        PortConstraint.port_id == port_id
    ).first()
    
    if existing:
        # Update existing constraints
        for key, value in constraint_data.model_dump().items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new constraints
        constraint = PortConstraint(port_id=port_id, **constraint_data.model_dump())
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint


@router.get("/{port_id}/vessel-compatibility")
async def check_vessel_compatibility(
    port_id: int,
    vessel_type: str,
    dwt: Optional[float] = None,
    draft: Optional[float] = None,
    loa: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Check if a vessel type/size is compatible with port constraints"""
    constraint = db.query(PortConstraint).filter(
        PortConstraint.port_id == port_id
    ).first()
    
    if not constraint:
        raise HTTPException(status_code=404, detail="Port constraints not found")
    
    issues = []
    compatible = True
    
    if constraint.max_dwt and dwt and dwt > constraint.max_dwt:
        issues.append(f"DWT {dwt} exceeds port maximum of {constraint.max_dwt}")
        compatible = False
    
    if constraint.max_draft and draft and draft > constraint.max_draft:
        issues.append(f"Draft {draft}m exceeds port maximum of {constraint.max_draft}m")
        compatible = False
    
    if constraint.max_loa and loa and loa > constraint.max_loa:
        issues.append(f"LOA {loa}m exceeds port maximum of {constraint.max_loa}m")
        compatible = False
    
    if constraint.max_vessel_size:
        vessel_hierarchy = ["handysize", "supramax", "panamax", "capesize"]
        if vessel_type.lower() in vessel_hierarchy:
            max_idx = vessel_hierarchy.index(constraint.max_vessel_size.lower()) if constraint.max_vessel_size.lower() in vessel_hierarchy else 3
            vessel_idx = vessel_hierarchy.index(vessel_type.lower())
            if vessel_idx > max_idx:
                issues.append(f"Vessel type {vessel_type} exceeds port maximum of {constraint.max_vessel_size}")
                compatible = False
    
    return {
        "port_id": port_id,
        "vessel_type": vessel_type,
        "compatible": compatible,
        "issues": issues,
        "port_constraints": {
            "max_dwt": constraint.max_dwt,
            "max_draft": constraint.max_draft,
            "max_loa": constraint.max_loa,
            "max_vessel_size": constraint.max_vessel_size
        }
    }
