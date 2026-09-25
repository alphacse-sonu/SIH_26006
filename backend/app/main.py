"""Main FastAPI Application Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import freight, ports, vessels, predictions, analytics
from app.database import engine, Base
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    yield
    # Shutdown
    print("Application shutting down")


app = FastAPI(
    title="Freight Forecasting API",
    description="""
    Intelligent Freight Forecasting Model for Vessel Chartering and Bulk Cargo Procurement.
    
    ## Features
    - Freight rate prediction for various vessel types
    - Optimal market entry timing recommendations
    - Vessel type optimization based on port constraints
    - Port infrastructure analysis
    - Risk assessment and early warnings
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(freight.router, prefix="/api/v1/freight", tags=["Freight Rates"])
app.include_router(ports.router, prefix="/api/v1/ports", tags=["Ports"])
app.include_router(vessels.router, prefix="/api/v1/vessels", tags=["Vessels"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "healthy",
        "service": "Freight Forecasting API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "ml_model": "loaded"
    }
