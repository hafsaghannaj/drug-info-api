from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    status: str


# Region Schemas
class RegionBase(BaseModel):
    name: str
    country: str
    lat: float
    lon: float
    population: int


class RegionCreate(RegionBase):
    pass


class RegionResponse(RegionBase):
    id: int
    current_risk_level: str
    current_risk_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Risk Prediction Schemas
class PredictionBase(BaseModel):
    region_id: int
    risk_score: float
    confidence: float
    factors: Optional[Dict[str, Any]] = None


class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    region_id: int
    severity: str
    disease_type: str
    description: str


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AlertResponse(AlertBase):
    id: int
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Data Source Schemas
class DataSourceBase(BaseModel):
    region_id: int
    source_type: str
    data_payload: Dict[str, Any]


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceResponse(DataSourceBase):
    id: int
    ingested_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas
class AnalyticsSummary(BaseModel):
    total_regions_monitored: int
    active_alerts: int
    high_risk_regions: int
    predictions_today: int
    avg_risk_score: float
    trend: str


class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class TrendData(BaseModel):
    date: str
    avg_risk_score: float
    prediction_count: int
