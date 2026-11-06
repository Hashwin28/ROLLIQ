"""
ROLLIQ Alerts Router.
Manages system and posture alert records, read acknowledgments, and caregiver views.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import Alert
from schemas import AlertRead

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertRead])
async def list_alerts(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve system alerts with optional filters."""
    query = select(Alert).order_by(desc(Alert.created_at))
    if user_id:
        query = query.where(Alert.user_id == user_id)
    if session_id:
        query = query.where(Alert.session_id == session_id)
    if unread_only:
        query = query.where(Alert.is_read.is_(False))

    query = query.limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.patch("/{alert_id}/read", response_model=AlertRead)
async def mark_alert_read(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Acknowledge and mark an alert as read."""
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an alert record."""
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()
