"""Database Seeding Script"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.port import Port, PortConstraint, Country, PortType
from app.models.vessel import VesselType, Vessel, VesselStatus
from app.models.freight import FreightHistory, VesselCategory
from app.models.route import Route
from app.ml.synthetic_data import SyntheticDataGenerator


def seed_database():
    """Seed the database with initial data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    generator = SyntheticDataGenerator()
    
    try:
        print("Seeding database...")
        
        # Seed Ports
        print("Seeding ports...")
        seed_ports(db, generator)
        
        # Seed Port Constraints
        print("Seeding port constraints...")
        seed_port_constraints(db)
        
        # Seed Vessel Types
        print("Seeding vessel types...")
        seed_vessel_types(db, generator)
        
        # Seed Routes
        print("Seeding routes...")
        seed_routes(db)
        
        # Seed Historical Freight Data
        print("Seeding freight history (this may take a moment)...")
        seed_freight_history(db, generator)
        
        db.commit()
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_ports(db: Session, generator: SyntheticDataGenerator):
    """Seed port data"""
    # Check if ports already exist
    if db.query(Port).count() > 0:
        print("Ports already seeded, skipping...")
        return
    
    # Indian East Coast Ports
    indian_ports = [
        {"name": "Paradip", "code": "INPRT", "country": Country.INDIA, "region": "East Coast", 
         "latitude": 20.2644, "longitude": 86.6085, "port_type": PortType.DISCHARGE},
        {"name": "Vizag (Visakhapatnam)", "code": "INVTZ", "country": Country.INDIA, "region": "East Coast",
         "latitude": 17.6868, "longitude": 83.2185, "port_type": PortType.DISCHARGE},
        {"name": "Gangavaram", "code": "INGVP", "country": Country.INDIA, "region": "East Coast",
         "latitude": 17.6200, "longitude": 83.2300, "port_type": PortType.DISCHARGE},
        {"name": "Gopalpur", "code": "INGOP", "country": Country.INDIA, "region": "East Coast",
         "latitude": 19.2583, "longitude": 84.9167, "port_type": PortType.DISCHARGE},
        {"name": "Dhamra", "code": "INDHA", "country": Country.INDIA, "region": "East Coast",
         "latitude": 20.7833, "longitude": 86.9500, "port_type": PortType.DISCHARGE},
        {"name": "Haldia", "code": "INHAL", "country": Country.INDIA, "region": "East Coast",
         "latitude": 22.0667, "longitude": 88.0833, "port_type": PortType.DISCHARGE},
        {"name": "Sagar-Sandheads", "code": "INSAG", "country": Country.INDIA, "region": "East Coast",
         "latitude": 21.6500, "longitude": 88.0500, "port_type": PortType.DISCHARGE},
    ]
    
    # Origin Ports (Loading)
    origin_ports = [
        {"name": "Newcastle", "code": "AUNTL", "country": Country.AUSTRALIA, "region": "New South Wales",
         "latitude": -32.9283, "longitude": 151.7817, "port_type": PortType.LOADING},
        {"name": "Hay Point", "code": "AUHPT", "country": Country.AUSTRALIA, "region": "Queensland",
         "latitude": -21.2833, "longitude": 149.3000, "port_type": PortType.LOADING},
        {"name": "Gladstone", "code": "AUGLT", "country": Country.AUSTRALIA, "region": "Queensland",
         "latitude": -23.8500, "longitude": 151.2500, "port_type": PortType.LOADING},
        {"name": "Hampton Roads", "code": "USHRP", "country": Country.USA, "region": "Virginia",
         "latitude": 36.9500, "longitude": -76.3300, "port_type": PortType.LOADING},
        {"name": "Baltimore", "code": "USBAL", "country": Country.USA, "region": "Maryland",
         "latitude": 39.2667, "longitude": -76.5833, "port_type": PortType.LOADING},
        {"name": "Nacala", "code": "MZNAC", "country": Country.MOZAMBIQUE, "region": "Nampula",
         "latitude": -14.5500, "longitude": 40.6833, "port_type": PortType.LOADING},
        {"name": "Beira", "code": "MZBEW", "country": Country.MOZAMBIQUE, "region": "Sofala",
         "latitude": -19.8333, "longitude": 34.8500, "port_type": PortType.LOADING},
        {"name": "Samarinda", "code": "IDSRI", "country": Country.INDONESIA, "region": "East Kalimantan",
         "latitude": -0.5000, "longitude": 117.1500, "port_type": PortType.LOADING},
        {"name": "Banjarmasin", "code": "IDBDJ", "country": Country.INDONESIA, "region": "South Kalimantan",
         "latitude": -3.3167, "longitude": 114.5833, "port_type": PortType.LOADING},
        {"name": "Murmansk", "code": "RUMMK", "country": Country.RUSSIA, "region": "Murmansk Oblast",
         "latitude": 68.9667, "longitude": 33.0833, "port_type": PortType.LOADING},
    ]
    
    for port_data in indian_ports + origin_ports:
        port = Port(**port_data)
        db.add(port)
    
    db.flush()


def seed_port_constraints(db: Session):
    """Seed port constraint data"""
    if db.query(PortConstraint).count() > 0:
        print("Port constraints already seeded, skipping...")
        return
    
    # Get all ports
    ports = db.query(Port).all()
    
    # Constraints for Indian East Coast ports
    indian_constraints = {
        "INPRT": {"max_loa": 300, "max_beam": 48, "max_draft": 14.5, "max_dwt": 150000,
                  "max_vessel_size": "capesize", "loading_rate": 40000, "unloading_rate": 35000,
                  "berth_count": 12, "avg_turnaround_days": 3.5},
        "INVTZ": {"max_loa": 330, "max_beam": 52, "max_draft": 17.1, "max_dwt": 180000,
                  "max_vessel_size": "capesize", "loading_rate": 45000, "unloading_rate": 40000,
                  "berth_count": 24, "avg_turnaround_days": 3.0},
        "INGVP": {"max_loa": 350, "max_beam": 55, "max_draft": 21.0, "max_dwt": 200000,
                  "max_vessel_size": "capesize", "loading_rate": 50000, "unloading_rate": 45000,
                  "berth_count": 6, "avg_turnaround_days": 2.5},
        "INGOP": {"max_loa": 230, "max_beam": 35, "max_draft": 14.0, "max_dwt": 80000,
                  "max_vessel_size": "panamax", "loading_rate": 25000, "unloading_rate": 20000,
                  "berth_count": 4, "avg_turnaround_days": 4.0},
        "INDHA": {"max_loa": 320, "max_beam": 50, "max_draft": 18.0, "max_dwt": 180000,
                  "max_vessel_size": "capesize", "loading_rate": 45000, "unloading_rate": 40000,
                  "berth_count": 8, "avg_turnaround_days": 3.0},
        "INHAL": {"max_loa": 200, "max_beam": 30, "max_draft": 8.5, "max_dwt": 60000,
                  "max_vessel_size": "supramax", "loading_rate": 15000, "unloading_rate": 12000,
                  "berth_count": 14, "avg_turnaround_days": 5.0, "tidal_restriction": True},
        "INSAG": {"max_loa": 250, "max_beam": 38, "max_draft": 12.5, "max_dwt": 100000,
                  "max_vessel_size": "panamax", "loading_rate": 30000, "unloading_rate": 25000,
                  "berth_count": 6, "avg_turnaround_days": 4.0},
    }
    
    # Constraints for origin ports
    origin_constraints = {
        "AUNTL": {"max_loa": 300, "max_beam": 50, "max_draft": 15.2, "max_dwt": 185000,
                  "max_vessel_size": "capesize", "loading_rate": 80000, "berth_count": 4},
        "AUHPT": {"max_loa": 320, "max_beam": 52, "max_draft": 18.5, "max_dwt": 220000,
                  "max_vessel_size": "capesize", "loading_rate": 100000, "berth_count": 3},
        "AUGLT": {"max_loa": 300, "max_beam": 50, "max_draft": 16.5, "max_dwt": 200000,
                  "max_vessel_size": "capesize", "loading_rate": 85000, "berth_count": 6},
        "USHRP": {"max_loa": 320, "max_beam": 50, "max_draft": 15.0, "max_dwt": 180000,
                  "max_vessel_size": "capesize", "loading_rate": 70000, "berth_count": 8},
        "USBAL": {"max_loa": 290, "max_beam": 45, "max_draft": 14.0, "max_dwt": 150000,
                  "max_vessel_size": "capesize", "loading_rate": 60000, "berth_count": 6},
        "MZNAC": {"max_loa": 280, "max_beam": 45, "max_draft": 14.5, "max_dwt": 120000,
                  "max_vessel_size": "panamax", "loading_rate": 40000, "berth_count": 3},
        "MZBEW": {"max_loa": 230, "max_beam": 35, "max_draft": 11.0, "max_dwt": 80000,
                  "max_vessel_size": "panamax", "loading_rate": 30000, "berth_count": 4},
        "IDSRI": {"max_loa": 250, "max_beam": 40, "max_draft": 12.0, "max_dwt": 90000,
                  "max_vessel_size": "panamax", "loading_rate": 35000, "berth_count": 5},
        "IDBDJ": {"max_loa": 230, "max_beam": 35, "max_draft": 10.5, "max_dwt": 75000,
                  "max_vessel_size": "supramax", "loading_rate": 30000, "berth_count": 4},
        "RUMMK": {"max_loa": 300, "max_beam": 48, "max_draft": 15.5, "max_dwt": 170000,
                  "max_vessel_size": "capesize", "loading_rate": 50000, "berth_count": 6},
    }
    
    all_constraints = {**indian_constraints, **origin_constraints}
    
    for port in ports:
        if port.code in all_constraints:
            constraint_data = all_constraints[port.code]
            constraint = PortConstraint(
                port_id=port.id,
                current_congestion_level=0.3 + (hash(port.code) % 50) / 100,
                vessels_at_anchorage=(hash(port.code) % 10) + 2,
                avg_waiting_time_hours=12 + (hash(port.code) % 36),
                cargo_types="coal,iron ore,grain",
                **constraint_data
            )
            db.add(constraint)
    
    db.flush()


def seed_vessel_types(db: Session, generator: SyntheticDataGenerator):
    """Seed vessel type data"""
    if db.query(VesselType).count() > 0:
        print("Vessel types already seeded, skipping...")
        return
    
    vessel_types = generator.generate_vessel_types()
    
    for vt_data in vessel_types:
        vt = VesselType(**vt_data)
        db.add(vt)
    
    db.flush()


def seed_routes(db: Session):
    """Seed route data"""
    if db.query(Route).count() > 0:
        print("Routes already seeded, skipping...")
        return
    
    # Get ports
    indian_ports = db.query(Port).filter(Port.country == Country.INDIA).all()
    origin_ports = db.query(Port).filter(Port.country != Country.INDIA).all()
    
    # Route distances (nautical miles) - approximate
    route_data = {
        ("AUNTL", "INPRT"): {"distance": 5800, "name": "Newcastle-Paradip", "duration": 18},
        ("AUNTL", "INVTZ"): {"distance": 5700, "name": "Newcastle-Vizag", "duration": 17},
        ("AUNTL", "INGVP"): {"distance": 5650, "name": "Newcastle-Gangavaram", "duration": 17},
        ("AUHPT", "INPRT"): {"distance": 5900, "name": "Hay Point-Paradip", "duration": 18},
        ("AUHPT", "INVTZ"): {"distance": 5800, "name": "Hay Point-Vizag", "duration": 18},
        ("AUGLT", "INVTZ"): {"distance": 5750, "name": "Gladstone-Vizag", "duration": 17},
        ("USHRP", "INPRT"): {"distance": 9500, "name": "Hampton Roads-Paradip", "duration": 32},
        ("USHRP", "INVTZ"): {"distance": 9400, "name": "Hampton Roads-Vizag", "duration": 31},
        ("USBAL", "INPRT"): {"distance": 9600, "name": "Baltimore-Paradip", "duration": 33},
        ("MZNAC", "INPRT"): {"distance": 3200, "name": "Nacala-Paradip", "duration": 10},
        ("MZNAC", "INVTZ"): {"distance": 3100, "name": "Nacala-Vizag", "duration": 10},
        ("MZBEW", "INPRT"): {"distance": 3400, "name": "Beira-Paradip", "duration": 11},
        ("IDSRI", "INPRT"): {"distance": 2800, "name": "Samarinda-Paradip", "duration": 9},
        ("IDSRI", "INVTZ"): {"distance": 2700, "name": "Samarinda-Vizag", "duration": 8},
        ("IDBDJ", "INPRT"): {"distance": 2900, "name": "Banjarmasin-Paradip", "duration": 9},
        ("RUMMK", "INPRT"): {"distance": 7500, "name": "Murmansk-Paradip", "duration": 25},
    }
    
    port_map = {p.code: p.id for p in indian_ports + origin_ports}
    
    for (origin_code, dest_code), data in route_data.items():
        if origin_code in port_map and dest_code in port_map:
            route = Route(
                origin_port_id=port_map[origin_code],
                destination_port_id=port_map[dest_code],
                distance_nm=data["distance"],
                route_name=data["name"],
                typical_duration_days=data["duration"],
                monsoon_impact=2.0,
                winter_impact=1.0,
                piracy_risk_level=0.1,
                weather_risk_level=0.3
            )
            db.add(route)
    
    db.flush()


def seed_freight_history(db: Session, generator: SyntheticDataGenerator):
    """Seed historical freight data"""
    if db.query(FreightHistory).count() > 0:
        print("Freight history already seeded, skipping...")
        return
    
    # Get ports
    indian_ports = db.query(Port).filter(Port.country == Country.INDIA).all()
    origin_ports = db.query(Port).filter(Port.country != Country.INDIA).all()
    
    # Generate data for each vessel type
    for vessel_type in ['handysize', 'supramax', 'panamax', 'capesize']:
        print(f"  Generating {vessel_type} data...")
        df = generator.generate_freight_history(
            vessel_type=vessel_type,
            num_records=500  # 500 records per vessel type
        )
        
        # Map port names to IDs
        origin_map = {p.name: p.id for p in origin_ports}
        dest_map = {p.name: p.id for p in indian_ports}
        
        for _, row in df.iterrows():
            # Find matching ports
            origin_id = origin_map.get(row['origin_port_name'])
            dest_id = dest_map.get(row['destination_port_name'])
            
            if origin_id and dest_id:
                history = FreightHistory(
                    vessel_type=VesselCategory(vessel_type),
                    origin_port_id=origin_id,
                    destination_port_id=dest_id,
                    rate_per_ton=row['rate_per_ton'],
                    cargo_volume=row['cargo_volume'],
                    voyage_duration_days=row['voyage_duration_days'],
                    fuel_price=row['fuel_price'],
                    bunker_consumption=row['bunker_consumption'],
                    market_index=row['market_index'],
                    coal_price=row['coal_price'],
                    season=row['season'],
                    congestion_level=row['congestion_level'],
                    record_date=row['record_date']
                )
                db.add(history)
    
    db.flush()


if __name__ == "__main__":
    seed_database()
