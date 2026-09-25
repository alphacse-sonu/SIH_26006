"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/freight_forecast"
    )
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # ML Model Configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./ml_models")
    
    # Prediction Configuration
    FORECAST_HORIZON_DAYS: int = 90
    CONFIDENCE_INTERVAL: float = 0.95
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
