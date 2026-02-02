from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app.db import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    population = Column(Integer, nullable=False)
    current_risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    current_risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions = relationship("RiskPrediction", back_populates="region", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="region", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="region", cascade="all, delete-orphan")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    factors = Column(JSON, nullable=True)  # Store contributing factors as JSON
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    region = relationship("Region", back_populates="predictions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    disease_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    region = relationship("Region", back_populates="alerts")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String, nullable=False, index=True)  # 'WHO', 'NASA', 'NOAA'
    data_payload = Column(JSON, nullable=False)  # Raw data from source
    ingested_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    region = relationship("Region", back_populates="data_sources")
