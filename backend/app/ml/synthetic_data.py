"""Synthetic Data Generator for Training ML Models"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


class SyntheticDataGenerator:
    """Generate realistic synthetic freight data for model training"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Base rates by vessel type (USD per metric ton)
        self.base_rates = {
            'handysize': {'mean': 12.5, 'std': 2.5},
            'supramax': {'mean': 15.8, 'std': 3.2},
            'panamax': {'mean': 18.2, 'std': 4.0},
            'capesize': {'mean': 22.5, 'std': 5.5}
        }
        
        # Port data for Indian East Coast
        self.indian_ports = [
            {'id': 1, 'name': 'Paradip', 'code': 'INPRT', 'max_draft': 14.5, 'max_dwt': 150000},
            {'id': 2, 'name': 'Vizag', 'code': 'INVTZ', 'max_draft': 17.1, 'max_dwt': 180000},
            {'id': 3, 'name': 'Gangavaram', 'code': 'INGVP', 'max_draft': 21.0, 'max_dwt': 200000},
            {'id': 4, 'name': 'Gopalpur', 'code': 'INGOP', 'max_draft': 14.0, 'max_dwt': 80000},
            {'id': 5, 'name': 'Dhamra', 'code': 'INDHA', 'max_draft': 18.0, 'max_dwt': 180000},
            {'id': 6, 'name': 'Haldia', 'code': 'INHAL', 'max_draft': 8.5, 'max_dwt': 60000},
            {'id': 7, 'name': 'Sagar-Sandheads', 'code': 'INSAG', 'max_draft': 12.5, 'max_dwt': 100000}
        ]
        
        # Origin ports (loading ports)
        self.origin_ports = [
            {'id': 101, 'name': 'Newcastle', 'country': 'australia', 'code': 'AUNTL'},
            {'id': 102, 'name': 'Hay Point', 'country': 'australia', 'code': 'AUHPT'},
            {'id': 103, 'name': 'Gladstone', 'country': 'australia', 'code': 'AUGLT'},
            {'id': 104, 'name': 'Hampton Roads', 'country': 'usa', 'code': 'USHRP'},
            {'id': 105, 'name': 'Baltimore', 'country': 'usa', 'code': 'USBAL'},
            {'id': 106, 'name': 'Nacala', 'country': 'mozambique', 'code': 'MZNAC'},
            {'id': 107, 'name': 'Beira', 'country': 'mozambique', 'code': 'MZBEW'},
            {'id': 108, 'name': 'Samarinda', 'country': 'indonesia', 'code': 'IDSRI'},
            {'id': 109, 'name': 'Banjarmasin', 'country': 'indonesia', 'code': 'IDBDJ'},
            {'id': 110, 'name': 'Murmansk', 'country': 'russia', 'code': 'RUMMK'}
        ]
        
        # Route distances (nautical miles)
        self.route_distances = {
            (101, 1): 5800,  # Newcastle to Paradip
            (101, 2): 5700,  # Newcastle to Vizag
            (101, 3): 5650,  # Newcastle to Gangavaram
            (102, 1): 5900,  # Hay Point to Paradip
            (103, 2): 5750,  # Gladstone to Vizag
            (104, 1): 9500,  # Hampton Roads to Paradip
            (104, 2): 9400,  # Hampton Roads to Vizag
            (106, 1): 3200,  # Nacala to Paradip
            (106, 2): 3100,  # Nacala to Vizag
            (108, 1): 2800,  # Samarinda to Paradip
            (108, 2): 2700,  # Samarinda to Vizag
            (110, 1): 7500,  # Murmansk to Paradip
        }
    
    def generate_freight_history(
        self,
        vessel_type: str,
        num_records: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Generate synthetic historical freight rate data"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365*3)  # 3 years of data
        if end_date is None:
            end_date = datetime.now()
        
        records = []
        base_rate_info = self.base_rates.get(vessel_type.lower(), self.base_rates['supramax'])
        
        # Generate date range
        date_range = (end_date - start_date).days
        
        for _ in range(num_records):
            # Random date within range
            random_days = random.randint(0, date_range)
            record_date = start_date + timedelta(days=random_days)
            
            # Random origin and destination
            origin = random.choice(self.origin_ports)
            destination = random.choice(self.indian_ports)
            
            # Calculate base rate with various factors
            rate = self._calculate_rate(
                base_rate_info,
                origin,
                destination,
                record_date,
                vessel_type
            )
            
            # Generate related features
            record = {
                'vessel_type': vessel_type,
                'origin_port_id': origin['id'],
                'origin_port_name': origin['name'],
                'origin_country': origin['country'],
                'destination_port_id': destination['id'],
                'destination_port_name': destination['name'],
                'rate_per_ton': round(rate, 2),
                'record_date': record_date,
                'cargo_volume': self._generate_cargo_volume(vessel_type),
                'voyage_duration_days': self._calculate_voyage_duration(origin['id'], destination['id'], vessel_type),
                'fuel_price': self._generate_fuel_price(record_date),
                'bunker_consumption': self._get_bunker_consumption(vessel_type),
                'market_index': self._generate_market_index(record_date),
                'coal_price': self._generate_coal_price(record_date),
                'season': self._get_season(record_date),
                'congestion_level': round(random.uniform(0.1, 0.9), 2),
                'month': record_date.month,
                'day_of_week': record_date.weekday(),
                'year': record_date.year
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        return df.sort_values('record_date').reset_index(drop=True)
    
    def _calculate_rate(
        self,
        base_rate_info: Dict,
        origin: Dict,
        destination: Dict,
        date: datetime,
        vessel_type: str
    ) -> float:
        """Calculate freight rate with multiple factors"""
        # Base rate with random variation
        rate = np.random.normal(base_rate_info['mean'], base_rate_info['std'])
        
        # Distance factor
        route_key = (origin['id'], destination['id'])
        distance = self.route_distances.get(route_key, 5000)
        distance_factor = 1 + (distance - 5000) / 50000  # Normalize around 5000nm
        rate *= distance_factor
        
        # Seasonal factor
        month = date.month
        seasonal_factors = {
            1: 1.08, 2: 1.05, 3: 1.02, 4: 0.98,
            5: 0.95, 6: 0.92, 7: 0.90, 8: 0.92,
            9: 0.96, 10: 1.02, 11: 1.10, 12: 1.12
        }
        rate *= seasonal_factors.get(month, 1.0)
        
        # Year-over-year trend (slight increase)
        years_from_base = (date.year - 2021)
        rate *= (1 + years_from_base * 0.03)
        
        # Random market volatility
        volatility = np.random.normal(0, 0.05)
        rate *= (1 + volatility)
        
        # Country-specific factors
        country_factors = {
            'australia': 1.0,
            'usa': 1.15,  # Longer distance
            'mozambique': 0.95,
            'indonesia': 0.90,  # Shorter distance
            'russia': 1.10
        }
        rate *= country_factors.get(origin['country'], 1.0)
        
        return max(rate, 5.0)  # Minimum rate floor
    
    def _generate_cargo_volume(self, vessel_type: str) -> float:
        """Generate realistic cargo volume based on vessel type"""
        volumes = {
            'handysize': (25000, 35000),
            'supramax': (45000, 60000),
            'panamax': (65000, 80000),
            'capesize': (150000, 180000)
        }
        min_vol, max_vol = volumes.get(vessel_type.lower(), (40000, 60000))
        return round(random.uniform(min_vol, max_vol), 0)
    
    def _calculate_voyage_duration(self, origin_id: int, dest_id: int, vessel_type: str) -> int:
        """Calculate voyage duration based on distance and vessel speed"""
        distance = self.route_distances.get((origin_id, dest_id), 5000)
        
        speeds = {
            'handysize': 12,
            'supramax': 13,
            'panamax': 14,
            'capesize': 14.5
        }
        speed = speeds.get(vessel_type.lower(), 13)
        
        # Calculate days at sea
        sea_days = distance / (speed * 24)
        
        # Add port time (loading + unloading)
        port_days = random.randint(3, 7)
        
        return int(sea_days + port_days)
    
    def _generate_fuel_price(self, date: datetime) -> float:
        """Generate realistic fuel price based on date"""
        # Base price around $500/ton with variation
        base_price = 500
        
        # Year trend
        year_factor = 1 + (date.year - 2021) * 0.08
        
        # Seasonal variation
        month_factor = 1 + 0.05 * np.sin(2 * np.pi * date.month / 12)
        
        # Random variation
        random_factor = np.random.normal(1, 0.1)
        
        return round(base_price * year_factor * month_factor * random_factor, 2)
    
    def _get_bunker_consumption(self, vessel_type: str) -> float:
        """Get daily bunker consumption by vessel type"""
        consumption = {
            'handysize': 25,
            'supramax': 32,
            'panamax': 38,
            'capesize': 55
        }
        base = consumption.get(vessel_type.lower(), 35)
        return round(base * random.uniform(0.9, 1.1), 1)
    
    def _generate_market_index(self, date: datetime) -> float:
        """Generate Baltic Dry Index-like market index"""
        # Base index around 1500
        base_index = 1500
        
        # Year trend
        year_factor = 1 + (date.year - 2021) * 0.1
        
        # Seasonal pattern
        month_factor = 1 + 0.15 * np.sin(2 * np.pi * (date.month - 3) / 12)
        
        # Random variation
        random_factor = np.random.normal(1, 0.15)
        
        return round(base_index * year_factor * month_factor * random_factor, 0)
    
    def _generate_coal_price(self, date: datetime) -> float:
        """Generate coal price (USD per ton)"""
        # Base price around $150/ton
        base_price = 150
        
        # Year trend (coal prices have been volatile)
        year_factor = 1 + (date.year - 2021) * 0.15
        
        # Seasonal (higher in winter)
        month = date.month
        if month in [11, 12, 1, 2]:
            seasonal_factor = 1.15
        elif month in [6, 7, 8]:
            seasonal_factor = 0.90
        else:
            seasonal_factor = 1.0
        
        # Random variation
        random_factor = np.random.normal(1, 0.12)
        
        return round(base_price * year_factor * seasonal_factor * random_factor, 2)
    
    def _get_season(self, date: datetime) -> str:
        """Determine season based on date (Indian context)"""
        month = date.month
        if month in [6, 7, 8, 9]:
            return 'monsoon'
        elif month in [11, 12, 1, 2]:
            return 'winter'
        else:
            return 'summer'
    
    def generate_port_data(self) -> List[Dict]:
        """Generate complete port data for database seeding"""
        all_ports = []
        
        # Indian East Coast ports
        for port in self.indian_ports:
            all_ports.append({
                **port,
                'country': 'india',
                'region': 'East Coast',
                'port_type': 'discharge',
                'latitude': 20.0 + random.uniform(-2, 2),
                'longitude': 86.0 + random.uniform(-2, 2)
            })
        
        # Origin ports
        for port in self.origin_ports:
            all_ports.append({
                **port,
                'region': self._get_region(port['country']),
                'port_type': 'loading',
                'latitude': self._get_latitude(port['country']),
                'longitude': self._get_longitude(port['country'])
            })
        
        return all_ports
    
    def _get_region(self, country: str) -> str:
        """Get region based on country"""
        regions = {
            'australia': 'Queensland',
            'usa': 'East Coast',
            'mozambique': 'East Africa',
            'indonesia': 'Kalimantan',
            'russia': 'Arctic'
        }
        return regions.get(country, 'Unknown')
    
    def _get_latitude(self, country: str) -> float:
        """Get approximate latitude for country"""
        latitudes = {
            'australia': -27.0,
            'usa': 37.0,
            'mozambique': -15.0,
            'indonesia': -3.0,
            'russia': 69.0
        }
        return latitudes.get(country, 0.0) + random.uniform(-2, 2)
    
    def _get_longitude(self, country: str) -> float:
        """Get approximate longitude for country"""
        longitudes = {
            'australia': 153.0,
            'usa': -76.0,
            'mozambique': 40.0,
            'indonesia': 117.0,
            'russia': 33.0
        }
        return longitudes.get(country, 0.0) + random.uniform(-2, 2)
    
    def generate_vessel_types(self) -> List[Dict]:
        """Generate vessel type specifications"""
        return [
            {
                'name': 'handysize',
                'min_dwt': 15000,
                'max_dwt': 35000,
                'typical_dwt': 28000,
                'typical_loa': 170,
                'typical_beam': 27,
                'typical_draft': 10,
                'speed_knots': 12,
                'fuel_consumption_per_day': 25,
                'daily_charter_rate_low': 8000,
                'daily_charter_rate_high': 15000,
                'operating_cost_per_day': 5500
            },
            {
                'name': 'supramax',
                'min_dwt': 50000,
                'max_dwt': 60000,
                'typical_dwt': 55000,
                'typical_loa': 190,
                'typical_beam': 32,
                'typical_draft': 12.8,
                'speed_knots': 13,
                'fuel_consumption_per_day': 32,
                'daily_charter_rate_low': 10000,
                'daily_charter_rate_high': 22000,
                'operating_cost_per_day': 6500
            },
            {
                'name': 'panamax',
                'min_dwt': 65000,
                'max_dwt': 80000,
                'typical_dwt': 75000,
                'typical_loa': 229,
                'typical_beam': 32.3,
                'typical_draft': 13.5,
                'speed_knots': 14,
                'fuel_consumption_per_day': 38,
                'daily_charter_rate_low': 12000,
                'daily_charter_rate_high': 28000,
                'operating_cost_per_day': 7000
            },
            {
                'name': 'capesize',
                'min_dwt': 100000,
                'max_dwt': 200000,
                'typical_dwt': 180000,
                'typical_loa': 300,
                'typical_beam': 50,
                'typical_draft': 18.5,
                'speed_knots': 14.5,
                'fuel_consumption_per_day': 55,
                'daily_charter_rate_low': 15000,
                'daily_charter_rate_high': 45000,
                'operating_cost_per_day': 8500
            }
        ]
