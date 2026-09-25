# Freight Forecasting System - SIH 2026 (Problem ID: 26006)

## Intelligent Freight Forecasting Model for Vessel Chartering and Bulk Cargo Procurement

A comprehensive software solution for predicting freight rates, optimizing vessel selection, and improving chartering decisions for bulk cargo procurement to India's East Coast ports.

![Dashboard Preview](docs/images/dashboard-preview.png)

## Problem Statement

The current approach to vessel chartering for bulk cargo procurement to India's East Coast ports involves daily market exploration, leading to reactive decision-making and missed opportunities for cost savings. This system addresses:

- Lack of predictive insight into future freight rates
- Inability to identify optimal market entry timing
- Challenges in minimizing vessel idle time
- Port-specific infrastructure constraints

## Features

### 1. Freight Rate Forecasting
- ML-powered predictions for 7-180 days ahead
- Support for all vessel types (Handysize, Supramax, Panamax, Capesize)
- Confidence intervals for risk assessment
- Trend analysis and recommendations

### 2. Optimal Market Entry Timing
- Identify ideal windows for charter contracts
- Short-term and mid-term contract analysis
- Market sentiment indicators
- Cost savings potential calculation

### 3. Vessel Type Optimization
- Cargo volume-based recommendations
- Port constraint compatibility checking
- Capacity utilization optimization
- Cost-per-ton analysis

### 4. Port Infrastructure Analysis
- Indian East Coast ports (Paradip, Vizag, Gangavaram, Gopalpur, Dhamra, Haldia, Sagar-Sandheads)
- Origin ports (Australia, USA, Mozambique, Indonesia, Russia)
- Real-time congestion monitoring
- Draft, LOA, and DWT constraints

### 5. Risk Assessment
- Weather risk evaluation (monsoon season impact)
- Port congestion risk
- Market volatility assessment
- Mitigation recommendations

### 6. Analytics Dashboard
- Market overview and trends
- Seasonal pattern analysis
- Route comparison
- Historical data visualization

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **ML Libraries**: scikit-learn, XGBoost, pandas, numpy
- **ORM**: SQLAlchemy with Alembic migrations

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Routing**: React Router v6

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Project Structure

```
freight-forecasting/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── freight.py    # Freight rates endpoints
│   │   │   ├── ports.py      # Ports endpoints
│   │   │   ├── vessels.py    # Vessels endpoints
│   │   │   ├── predictions.py # ML predictions endpoints
│   │   │   └── analytics.py  # Analytics endpoints
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── ml/               # Machine learning module
│   │   │   ├── predictor.py  # Main prediction engine
│   │   │   ├── synthetic_data.py # Training data generator
│   │   │   └── feature_engineering.py
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration settings
│   │   ├── database.py       # Database connection
│   │   └── seed_data.py      # Database seeding script
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── FreightForecast.jsx
│   │   │   ├── MarketEntry.jsx
│   │   │   ├── VesselOptimization.jsx
│   │   │   ├── PortAnalysis.jsx
│   │   │   ├── RiskAssessment.jsx
│   │   │   └── Analytics.jsx
│   │   ├── services/         # API service layer
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL 15 (or use Docker)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://gitlab.com/iitism-group1/sih-2026-2nd-version.git
   cd sih-2026-2nd-version
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Setup database**
   ```bash
   # Create PostgreSQL database
   createdb freight_forecast
   
   # Run migrations and seed data
   python -m app.seed_data
   ```

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if backend is not on localhost:8000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Key Endpoints

#### Freight Rates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/freight/rates` | Get current freight rates |
| GET | `/freight/history` | Get historical freight data |
| GET | `/freight/trends` | Get rate trends for a route |

#### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/freight-forecast` | Generate freight rate forecast |
| POST | `/predictions/market-entry` | Analyze optimal market entry |
| POST | `/predictions/risk-assessment` | Assess voyage risks |

#### Ports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ports/` | List all ports |
| GET | `/ports/indian-east-coast` | Get Indian East Coast ports |
| GET | `/ports/{id}/constraints` | Get port constraints |
| GET | `/ports/{id}/vessel-compatibility` | Check vessel compatibility |

#### Vessels
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vessels/types` | Get vessel type specifications |
| POST | `/vessels/optimize` | Get vessel optimization recommendations |

#### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/dashboard` | Get dashboard summary |
| GET | `/analytics/market-overview` | Get market overview |
| GET | `/analytics/congestion` | Get port congestion report |
| GET | `/analytics/seasonal` | Get seasonal analysis |

### Example API Calls

#### Generate Freight Forecast
```bash
curl -X POST "http://localhost:8000/api/v1/predictions/freight-forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_type": "supramax",
    "origin_port_id": 8,
    "destination_port_id": 1,
    "forecast_days": 30
  }'
```

#### Get Vessel Optimization
```bash
curl -X POST "http://localhost:8000/api/v1/vessels/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "cargo_volume": 55000,
    "origin_port_id": 8,
    "destination_port_id": 2
  }'
```

## Machine Learning Model

### Features Used
- **Temporal**: Month, day of week, year, season
- **Market**: Fuel price, Baltic Dry Index, coal price
- **Route**: Distance, origin/destination ports
- **Operational**: Cargo volume, voyage duration, congestion level

### Model Architecture
- **Algorithm**: Gradient Boosting Regressor (ensemble method)
- **Training Data**: 3 years of synthetic historical data
- **Prediction Horizon**: 7-180 days
- **Confidence Intervals**: 95% confidence bands

### Synthetic Data Generation
Since actual historical data is not available, the system generates realistic synthetic data based on:
- Known freight rate patterns and seasonality
- Route distance factors
- Port-specific characteristics
- Market volatility patterns
- Commodity price correlations

## Database Schema

### Core Tables
- `ports` - Port information and locations
- `port_constraints` - Infrastructure limitations
- `vessel_types` - Vessel specifications
- `vessels` - Individual vessel data
- `freight_rates` - Current freight rates
- `freight_history` - Historical rate data
- `routes` - Shipping route information
- `predictions` - Prediction requests and results

## Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)

### Freight Forecast
![Forecast](docs/images/forecast.png)

### Vessel Optimization
![Optimization](docs/images/optimization.png)

### Port Analysis
![Ports](docs/images/ports.png)

## Future Enhancements

1. **Real-time Data Integration**
   - Baltic Exchange API integration
   - AIS vessel tracking data
   - Weather API integration

2. **Advanced ML Models**
   - LSTM for time series forecasting
   - Ensemble methods for improved accuracy
   - Anomaly detection for market disruptions

3. **Additional Features**
   - Multi-voyage contract optimization
   - Fleet management module
   - Automated alerts and notifications
   - Mobile application

## Team

**IITISM Group 1** - Smart India Hackathon 2026

## License

This project is developed for the Smart India Hackathon 2026 (Problem ID: 26006).

## Acknowledgments

- Ministry of Ports, Shipping and Waterways, Government of India
- Smart India Hackathon organizing committee
- IIT (ISM) Dhanbad
