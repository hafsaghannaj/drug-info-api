from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_db
from app.models import Alert, AlertStatus
from app.schemas import AlertResponse, AlertCreate, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[str] = None,
    region_id: Optional[int] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get alerts, optionally filtered by status and region"""
    query = select(Alert).order_by(Alert.created_at.desc())

    if status:
        query = query.where(Alert.status == status)

    if region_id:
        query = query.where(Alert.region_id == region_id)

    query = query.limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert by ID"""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.post("", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert"""
    db_alert = Alert(**alert.model_dump())
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)

    return db_alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alert (e.g., mark as resolved)"""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields
    update_data = alert_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.commit()
    await db.refresh(alert)

    return alert
