"""
ROLLIQ Analytics Router.
Generates recovery trends, bilateral symmetry comparisons, and baseline deviation evaluations.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import MonitoringSession, SessionMetrics, MovementEvent, PersonalBaseline
from schemas import (
    RMIHistoryPoint, MovementDistribution, DurationTrend,
    SymmetryData, SmoothnessTrend, SessionMetricsRead,
    BaselineComparisonResult, BaselineComparison
)
from services.baseline_engine import BaselineEngine

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/rmi-history/{user_id}", response_model=List[RMIHistoryPoint])
async def get_rmi_history(user_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve RMI score progression across chronological sessions."""
    query = (
        select(MonitoringSession)
        .where(MonitoringSession.user_id == user_id, MonitoringSession.rmi_score.isnot(None))
        .order_by(MonitoringSession.started_at)
        .limit(limit)
    )
    res = await db.execute(query)
    sessions = list(res.scalars().all())

    return [
        RMIHistoryPoint(
            session_id=s.id,
            date=s.started_at,
            rmi_score=s.rmi_score or 0.0,
            total_movements=s.total_movements or 0,
        )
        for s in sessions
    ]


@router.get("/movement-distribution/{user_id}", response_model=List[MovementDistribution])
async def get_movement_distribution(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve frequency breakdown of movement types."""
    query = (
        select(MovementEvent.event_type)
        .join(MonitoringSession, MovementEvent.session_id == MonitoringSession.id)
        .where(MonitoringSession.user_id == user_id)
    )
    res = await db.execute(query)
    event_types = list(res.scalars().all())

    total = len(event_types)
    if total == 0:
        return []

    counts: Dict[str, int] = {}
    for et in event_types:
        counts[et] = counts.get(et, 0) + 1

    return [
        MovementDistribution(
            event_type=k,
            count=v,
            percentage=round((v / total) * 100.0, 1),
        )
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/duration-trends/{user_id}", response_model=List[DurationTrend])
async def get_duration_trends(user_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve average and median transition duration trend across sessions."""
    query = (
        select(SessionMetrics, MonitoringSession.started_at)
        .join(MonitoringSession, SessionMetrics.session_id == MonitoringSession.id)
        .where(MonitoringSession.user_id == user_id)
        .order_by(MonitoringSession.started_at)
        .limit(limit)
    )
    res = await db.execute(query)
    rows = list(res.all())

    return [
        DurationTrend(
            session_id=m.session_id,
            date=started_at,
            avg_duration_ms=m.avg_transition_duration_ms,
            median_duration_ms=m.median_transition_duration_ms,
        )
        for m, started_at in rows
    ]


@router.get("/symmetry/{user_id}", response_model=List[SymmetryData])
async def get_symmetry_trends(user_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve bilateral movement counts and symmetry ratio trends."""
    query = (
        select(SessionMetrics, MonitoringSession.started_at)
        .join(MonitoringSession, SessionMetrics.session_id == MonitoringSession.id)
        .where(MonitoringSession.user_id == user_id)
        .order_by(MonitoringSession.started_at)
        .limit(limit)
    )
    res = await db.execute(query)
    rows = list(res.all())

    return [
        SymmetryData(
            session_id=m.session_id,
            date=started_at,
            left_rolls=m.total_left_rolls,
            right_rolls=m.total_right_rolls,
            symmetry_ratio=m.movement_symmetry,
        )
        for m, started_at in rows
    ]


@router.get("/smoothness-trends/{user_id}", response_model=List[SmoothnessTrend])
async def get_smoothness_trends(user_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve movement jerk / smoothness metric trends over time."""
    query = (
        select(SessionMetrics, MonitoringSession.started_at)
        .join(MonitoringSession, SessionMetrics.session_id == MonitoringSession.id)
        .where(MonitoringSession.user_id == user_id)
        .order_by(MonitoringSession.started_at)
        .limit(limit)
    )
    res = await db.execute(query)
    rows = list(res.all())

    return [
        SmoothnessTrend(
            session_id=m.session_id,
            date=started_at,
            avg_smoothness=m.avg_smoothness,
        )
        for m, started_at in rows
    ]


@router.get("/baseline-comparison/{session_id}", response_model=BaselineComparisonResult)
async def get_baseline_comparison(session_id: str, db: AsyncSession = Depends(get_db)):
    """Compare a session's metrics with the user's personal baseline profile."""
    s_res = await db.execute(select(MonitoringSession).where(MonitoringSession.id == session_id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    m_res = await db.execute(select(SessionMetrics).where(SessionMetrics.session_id == session_id))
    metric = m_res.scalar_one_or_none()

    b_res = await db.execute(select(PersonalBaseline).where(PersonalBaseline.user_id == session.user_id))
    baseline = b_res.scalar_one_or_none()

    if not metric or not baseline or not baseline.is_ready:
        return BaselineComparisonResult(
            user_id=session.user_id,
            session_id=session_id,
            baseline_ready=False,
            comparisons=[],
            overall_deviation="Baseline not ready (minimum 3 sessions required).",
        )

    result = BaselineEngine.compare_to_baseline(metric, baseline)

    comparisons = [
        BaselineComparison(
            metric_name=d["metric_name"],
            current_value=d["current_value"],
            baseline_mean=d["baseline_mean"],
            baseline_std=d["baseline_std"],
            z_score=d["z_score"],
            deviation_direction=d["direction"],
            is_significant=d["is_significant"],
        )
        for d in result["deviations"]
    ]

    return BaselineComparisonResult(
        user_id=session.user_id,
        session_id=session_id,
        baseline_ready=True,
        comparisons=comparisons,
        overall_deviation=result["summary"],
    )


@router.get("/session-comparison")
async def compare_sessions(
    session_a_id: str = Query(...),
    session_b_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Compare metrics between two distinct sessions."""
    res_a = await db.execute(select(SessionMetrics).where(SessionMetrics.session_id == session_a_id))
    res_b = await db.execute(select(SessionMetrics).where(SessionMetrics.session_id == session_b_id))
    ma = res_a.scalar_one_or_none()
    mb = res_b.scalar_one_or_none()

    if not ma or not mb:
        raise HTTPException(status_code=404, detail="One or both sessions lack computed metrics")

    differences = {
        "rmi_diff": round(mb.rmi_score - ma.rmi_score, 1),
        "duration_diff_ms": round(mb.avg_transition_duration_ms - ma.avg_transition_duration_ms, 1),
        "smoothness_diff": round(mb.avg_smoothness - ma.avg_smoothness, 2),
        "velocity_diff": round(mb.avg_angular_velocity - ma.avg_angular_velocity, 1),
        "movements_diff": mb.total_movements - ma.total_movements,
    }

    return {
        "session_a": SessionMetricsRead.model_validate(ma),
        "session_b": SessionMetricsRead.model_validate(mb),
        "differences": differences,
    }
