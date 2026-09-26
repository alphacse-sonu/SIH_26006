# 🚢 Maritime Chartering Decision Platform

**SIH 2026 | PS SIH26006 | Team IIT ISM Dhanbad**

An AI-powered maritime chartering decision engine for SIH PS-26006 that connects freight rate forecasting, automatic vessel selection, port constraints, charter timing, idle-scenario planning, and risk assessment into one unified decision-support platform.

## 🎯 Problem Statement

SAIL (Steel Authority of India Limited) needs to shift from reactive, one-off spot chartering decisions toward proactive short and medium-term voyage planning. This platform provides data-driven recommendations by analyzing:

1. **When to charter** - Freight rate forecasting with confidence intervals
2. **What it truly costs** - Total delivered cost beyond just the freight quote
3. **How to handle constraints** - Automatic vessel selection using cargo material, parcel size, draft, LOA, beam and handling limits at both ports
4. **How to reduce idle time** - Low-demand windows and alternative-employment/positioning guidance
5. **What to decide** - Charter vs Spot recommendation with Monte Carlo simulation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Tailwind)                   │
│  Dashboard │ Vessel Optimizer │ Forecast Chart │ Cost Analysis │ Decision Panel  │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST API
┌─────────────────────────────┼───────────────────────────────┐
│                    BACKEND (FastAPI + Python)                     │
│                                                                  │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────┐          │
│  │  Forecasting  │  │ Cost Engine  │  │  Lightering    │          │
│  │  XGB+LGB+LSTM │  │ 9 Components │  │  TPC Curves    │          │
│  └───────┬───────┘  └──────┬───────┘  └───────┬───────┘          │
│          └────────────┼────────────┘                          │
│                ┌────┴───────────────┐                          │
│                │ Decision Engine  │                          │
│                │ NPV + Monte Carlo│                          │
│                └─────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- pip and npm

### Setup

**1. Clone the repository**
```bash
git clone https://gitlab.com/iitism-group1/sih-2026-iitism.git
cd sih-2026-iitism
```

**2. Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python data/generate_synthetic_data.py   # Generate training data (~30 sec)
uvicorn main:app --reload --port 8000    # Start API server
```

**3. Frontend Setup** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

**4. Open Dashboard**
```
http://localhost:5173
```

Enter cargo details → Click "Run Full Analysis" → View results across all tabs.

> **Note:** First analysis takes 30-60 seconds as ML models train on startup. Subsequent analyses are instant.

## 📊 Tech Stack

| Layer | Technology |
|-------|------------|
| ML/Forecasting | XGBoost, LightGBM, PyTorch (LSTM), scikit-learn |
| Feature Engineering | Pandas, NumPy, SciPy |
| Backend API | FastAPI, Pydantic, Uvicorn |
| Frontend | React 18, Vite, Tailwind CSS v4, Recharts |
| Data Generation | Ornstein-Uhlenbeck process, GARCH volatility, Fourier seasonality |

## 🧠 Mathematical Methodology

### 1. Freight Rate Forecasting
- **Ornstein-Uhlenbeck process** for mean-reverting rate dynamics
- **GARCH(1,1)** volatility clustering
- **Fourier series** seasonal decomposition (annual + semi-annual harmonics)
- **50+ engineered features**: lagged rates, rolling statistics, momentum, realized volatility, BDI/bunker correlation
- **Confidence intervals** via XGBoost quantile regression with sqrt(h) uncertainty scaling

### 2. Total Delivered Cost
```
TotalCost = Freight + PortCharges + WaitingCost + Demurrage
          + DisruptionCost + CanalFees + Insurance + BunkerCost
```

### 3. Lightering Optimization
- **TPC curve integration**: cargo_to_lighter = ∫ TPC(d) dd from target_draft to vessel_draft
- Trapezoidal numerical integration with 1cm resolution
- Weather window risk assessment (Hs > 1.5m threshold per OCIMF guidelines)

### 4. Charter vs Spot Decision
- **NPV comparison**: NPV = Σ CF_t / (1+r)^t
- **Breakeven analysis**: R = Σ(E[S_t]/(1+r)^t) / Σ(1/(1+r)^t)
- **Monte Carlo simulation**: 1000 rate paths, VaR at 95%

## 📁 Project Structure

```
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── requirements.txt
│   ├── models/
│   │   ├── forecasting.py         # XGBoost + LightGBM + LSTM ensemble
│   │   ├── cost_calculator.py     # Total delivered cost engine
│   │   ├── lightering.py          # TPC curve & lightering optimizer
│   │   └── decision_engine.py     # Charter vs Spot (NPV + Monte Carlo)
│   └── data/
│       ├── generate_synthetic_data.py
│       ├── routes.json            # 35 PS-26006 origin→East Coast trade lanes
│       ├── vessels.json           # 7 vessel types with TPC curves
│       └── ports.json             # Origin + East Coast port constraints
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │       ├── Dashboard.jsx      # Main input form + layout
│   │       ├── ForecastChart.jsx  # Rate forecast with CI bands
│   │       ├── CostBreakdown.jsx  # Cost pie chart + vessel comparison
│   │       ├── LighteringAnalysis.jsx
│   │       ├── DecisionPanel.jsx  # Charter/Spot recommendation
│   │       └── RiskIndicators.jsx
│   ├── package.json
│   └── vite.config.js
├── run.sh                         # Linux/Mac start script
├── run.bat                        # Windows start script
└── README.md
```

## 🔄 PS-26006 Input Flow

The dashboard no longer asks the user to choose a vessel class. The user enters:

- Cargo quantity
- Cargo material (Coal / Steel)
- Origin region (Australia / US / Mozambique / Russia / Indonesia)
- East Coast Indian discharge port
- Contract period and loading month

The backend then:
1. Maps the origin + destination to one of the 35 modeled PS-26006 trade lanes.
2. Selects a feasible Handysize, Supramax, Panamax or Capesize option using parcel size and both-port draft/LOA/beam/handling constraints.
3. Uses the fixed, seeded synthetic historical series for that trade lane to generate the freight-rate forecast.
4. Calculates delivered cost, lightering implications, charter-vs-spot economics, market-entry timing, idle-management guidance and risk indicators.

The port constraints and historical freight series included in this student prototype are **synthetic/demo planning inputs**. They should be replaced with SAIL-approved/live operational data before real-world deployment.

## 📚 Data Sources & References

- **Baltic Exchange** - Freight rate indices (C5, C3, P1A, S10 route structures)
- **Clarksons Research** - Historical fixture data patterns
- **World Port Source / MarineTraffic** - Port draft limits and charges
- **NOAA GFS** - Marine weather forecast methodology
- **IMO / OCIMF** - STS operation guidelines

### Academic References
- Alizadeh & Nomikos (2009), *Shipping Derivatives and Risk Management*
- Kavussanos & Visvikis (2006), *Derivatives and Risk Management in Shipping*
- Stopford (2009), *Maritime Economics*, 3rd Edition
- Rawson & Tupper (2001), *Basic Ship Theory*, 5th Edition

## 🛡️ Key Differentiators

1. **Mathematical rigor** - Not fake predictions. Real Ornstein-Uhlenbeck + GARCH + Fourier models
2. **Proper feature engineering** - 50+ features with documented mathematical formulations
3. **Connected decision engine** - All modules feed into one recommendation, not separate tools
4. **Confidence intervals** - Quantile regression with proper uncertainty scaling
5. **Indian port focus** - Paradip (18.5m draft), Vizag, Haldia, Mundra, Dhamra included
6. **Full cost transparency** - 9 cost components, not just freight rate

---

**Team IIT ISM Dhanbad | Smart India Hackathon 2026**
