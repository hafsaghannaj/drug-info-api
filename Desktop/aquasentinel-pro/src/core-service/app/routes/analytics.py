from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db import get_db
from app.models import Region, Alert, RiskPrediction, RiskLevel, AlertStatus
from app.schemas import AnalyticsSummary, RiskDistribution

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary statistics"""

    # Total regions
    result = await db.execute(select(func.count(Region.id)))
    total_regions = result.scalar()

    # Active alerts
    result = await db.execute(
        select(func.count(Alert.id)).where(Alert.status == AlertStatus.ACTIVE)
    )
    active_alerts = result.scalar()

    # High risk regions (high or critical)
    result = await db.execute(
        select(func.count(Region.id)).where(
            Region.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        )
    )
    high_risk_regions = result.scalar()

    # Predictions today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(RiskPrediction.id)).where(
            RiskPrediction.timestamp >= today_start
        )
    )
    predictions_today = result.scalar()

    # Average risk score
    result = await db.execute(
        select(func.avg(Region.current_risk_score))
    )
    avg_risk_score = result.scalar() or 0.0

    # Determine trend (compare last 7 days vs previous 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)

    result = await db.execute(
        select(func.avg(RiskPrediction.risk_score)).where(
            RiskPrediction.timestamp >= seven_days_ago
        )
    )
    recent_avg = result.scalar() or 0.0

    result = await db.execute(
        select(func.avg(RiskPrediction.risk_score)).where(
            RiskPrediction.timestamp >= fourteen_days_ago,
            RiskPrediction.timestamp < seven_days_ago
        )
    )
    previous_avg = result.scalar() or 0.0

    trend = "stable"
    if recent_avg > previous_avg + 0.05:
        trend = "increasing"
    elif recent_avg < previous_avg - 0.05:
        trend = "decreasing"

    return {
        "total_regions_monitored": total_regions,
        "active_alerts": active_alerts,
        "high_risk_regions": high_risk_regions,
        "predictions_today": predictions_today,
        "avg_risk_score": float(avg_risk_score),
        "trend": trend
    }


@router.get("/risk-distribution", response_model=RiskDistribution)
async def get_risk_distribution(db: AsyncSession = Depends(get_db)):
    """Get distribution of regions by risk level"""

    result = await db.execute(
        select(func.count(Region.id)).where(Region.current_risk_level == RiskLevel.LOW)
    )
    low = result.scalar()

    result = await db.execute(
        select(func.count(Region.id)).where(Region.current_risk_level == RiskLevel.MEDIUM)
    )
    medium = result.scalar()

    result = await db.execute(
        select(func.count(Region.id)).where(Region.current_risk_level == RiskLevel.HIGH)
    )
    high = result.scalar()

    result = await db.execute(
        select(func.count(Region.id)).where(Region.current_risk_level == RiskLevel.CRITICAL)
    )
    critical = result.scalar()

    return {
        "low": low,
        "medium": medium,
        "high": high,
        "critical": critical
    }
