from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.db import get_db
from app.models import RiskPrediction
from app.schemas import PredictionResponse, PredictionCreate, TrendData

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("", response_model=List[PredictionResponse])
async def get_predictions(
    region_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get predictions, optionally filtered by region and date range"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = select(RiskPrediction).where(RiskPrediction.timestamp >= cutoff_date)

    if region_id:
        query = query.where(RiskPrediction.region_id == region_id)

    query = query.order_by(RiskPrediction.timestamp.desc()).limit(100)

    result = await db.execute(query)
    predictions = result.scalars().all()

    return predictions


@router.post("", response_model=PredictionResponse)
async def create_prediction(
    prediction: PredictionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prediction"""
    db_prediction = RiskPrediction(**prediction.model_dump())
    db.add(db_prediction)
    await db.commit()
    await db.refresh(db_prediction)

    return db_prediction


@router.get("/trends", response_model=List[TrendData])
async def get_prediction_trends(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated trend data over time"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Group predictions by date and calculate averages
    result = await db.execute(
        select(
            func.date(RiskPrediction.timestamp).label("date"),
            func.avg(RiskPrediction.risk_score).label("avg_risk_score"),
            func.count(RiskPrediction.id).label("prediction_count")
        )
        .where(RiskPrediction.timestamp >= cutoff_date)
        .group_by(func.date(RiskPrediction.timestamp))
        .order_by(func.date(RiskPrediction.timestamp))
    )

    trends = []
    for row in result:
        trends.append({
            "date": str(row.date),
            "avg_risk_score": float(row.avg_risk_score),
            "prediction_count": int(row.prediction_count)
        })

    return trends
