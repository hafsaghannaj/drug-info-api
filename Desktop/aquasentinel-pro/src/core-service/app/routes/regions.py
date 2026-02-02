from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db import get_db
from app.models import Region, RiskPrediction
from app.schemas import RegionResponse, PredictionResponse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=List[RegionResponse])
async def get_regions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all regions with current risk levels"""
    result = await db.execute(
        select(Region).offset(skip).limit(limit)
    )
    regions = result.scalars().all()
    return regions


@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(
    region_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific region by ID"""
    result = await db.execute(
        select(Region).where(Region.id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    return region


@router.get("/{region_id}/predictions", response_model=List[PredictionResponse])
async def get_region_predictions(
    region_id: int,
    limit: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get historical predictions for a specific region"""
    # Verify region exists
    result = await db.execute(
        select(Region).where(Region.id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # Get predictions
    result = await db.execute(
        select(RiskPrediction)
        .where(RiskPrediction.region_id == region_id)
        .order_by(RiskPrediction.timestamp.desc())
        .limit(limit)
    )
    predictions = result.scalars().all()

    return predictions
