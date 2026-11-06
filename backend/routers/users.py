"""
ROLLIQ User Profiles Router.
Manages isolated user records, personal baseline retrieval, and aggregate statistics.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import User, PersonalBaseline, MonitoringSession, SessionMetrics
from schemas import UserCreate, UserUpdate, UserRead, BaselineRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user profile."""
    new_user = User(
        display_name=payload.display_name,
        age_group=payload.age_group,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("", response_model=List[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all user profiles."""
    res = await db.execute(select(User).order_by(desc(User.created_at)))
    return list(res.scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve single user profile."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update user profile attributes."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.age_group is not None:
        user.age_group = payload.age_group

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Delete user and all associated monitoring sessions."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()


@router.get("/{user_id}/baseline", response_model=Optional[BaselineRead])
async def get_user_baseline(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve user's personal mobility baseline."""
    res = await db.execute(select(PersonalBaseline).where(PersonalBaseline.user_id == user_id))
    baseline = res.scalar_one_or_none()
    if not baseline:
        return None
    return baseline


@router.get("/{user_id}/summary")
async def get_user_summary(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve aggregate summary metrics for a user."""
    # Sessions
    s_res = await db.execute(
        select(MonitoringSession)
        .where(MonitoringSession.user_id == user_id)
        .order_by(desc(MonitoringSession.started_at))
    )
    sessions = list(s_res.scalars().all())

    # Baseline
    b_res = await db.execute(select(PersonalBaseline).where(PersonalBaseline.user_id == user_id))
    baseline = b_res.scalar_one_or_none()

    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.status == "completed")
    latest_rmi = sessions[0].rmi_score if sessions and sessions[0].rmi_score else None

    return {
        "user_id": user_id,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "latest_rmi": latest_rmi,
        "baseline_ready": baseline.is_ready if baseline else False,
        "baseline_sessions_used": baseline.sessions_used if baseline else 0,
    }
