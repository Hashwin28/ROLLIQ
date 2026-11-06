"""
ROLLIQ Session Management Router.
Handles full lifecycle of monitoring sessions, movement querying, and metric finalization.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from database import get_db
from models import (
    MonitoringSession, SessionMetrics, MovementEvent,
    SensorReading, User, PersonalBaseline
)
from schemas import (
    SessionCreate, SessionUpdate, SessionRead, SessionDetail,
    MovementEventRead, MovementDetailRead, SessionMetricsRead,
    SensorReadingRead
)
from services.rmi_calculator import RMICalculator
from services.baseline_engine import BaselineEngine

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
rmi_calculator = RMICalculator()


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new monitoring session."""
    # Ensure user exists or create default
    u_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        user = User(id=payload.user_id, display_name="Primary User", age_group="adult")
        db.add(user)
        await db.flush()

    new_session = MonitoringSession(
        user_id=payload.user_id,
        device_id=payload.device_id,
        is_simulation=payload.is_simulation,
        simulation_scenario=payload.simulation_scenario,
        notes=payload.notes,
        status="active",
        started_at=datetime.now(timezone.utc),
        total_movements=0,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.get("", response_model=List[SessionRead])
async def list_sessions(
    user_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List monitoring sessions with optional filtering."""
    query = select(MonitoringSession).order_by(desc(MonitoringSession.started_at))
    if user_id:
        query = query.where(MonitoringSession.user_id == user_id)
    if status_filter:
        query = query.where(MonitoringSession.status == status_filter)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get single session with associated metrics."""
    query = (
        select(MonitoringSession)
        .options(selectinload(MonitoringSession.metrics))
        .where(MonitoringSession.id == session_id)
    )
    res = await db.execute(query)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Monitoring session not found")

    detail = SessionDetail(
        id=session.id,
        user_id=session.user_id,
        device_id=session.device_id,
        is_simulation=session.is_simulation,
        simulation_scenario=session.simulation_scenario,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_movements=session.total_movements or 0,
        avg_transition_duration=session.avg_transition_duration,
        rmi_score=session.rmi_score,
        notes=session.notes,
        movement_count=session.total_movements or 0,
        metrics=session.metrics,
    )
    return detail


@router.patch("/{session_id}", response_model=SessionRead)
async def update_session(session_id: str, payload: SessionUpdate, db: AsyncSession = Depends(get_db)):
    """Update session status (pause, resume, complete) or notes."""
    res = await db.execute(select(MonitoringSession).where(MonitoringSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if payload.status:
        session.status = payload.status
        if payload.status == "completed" and not session.ended_at:
            session.ended_at = datetime.now(timezone.utc)
    if payload.notes is not None:
        session.notes = payload.notes

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a session and all its associated telemetry."""
    res = await db.execute(select(MonitoringSession).where(MonitoringSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


@router.get("/{session_id}/movements", response_model=List[MovementEventRead])
async def list_session_movements(session_id: str, db: AsyncSession = Depends(get_db)):
    """List all detected movement events for a session."""
    query = (
        select(MovementEvent)
        .where(MovementEvent.session_id == session_id)
        .order_by(MovementEvent.start_time_ms)
    )
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/{session_id}/movements/{movement_id}", response_model=MovementDetailRead)
async def get_movement_detail(
    session_id: str, movement_id: str, db: AsyncSession = Depends(get_db)
):
    """
    Get detailed movement analysis including surrounding raw sensor waveform window.
    Demonstrates deep engineering insight.
    """
    m_res = await db.execute(
        select(MovementEvent)
        .where(MovementEvent.session_id == session_id, MovementEvent.id == movement_id)
    )
    movement = m_res.scalar_one_or_none()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement event not found")

    # Fetch window of raw sensor readings around movement (1s padding before and after)
    t_start = max(0, movement.start_time_ms - 1000)
    t_end = movement.end_time_ms + 1000

    r_query = (
        select(SensorReading)
        .where(
            SensorReading.session_id == session_id,
            SensorReading.timestamp_ms >= t_start,
            SensorReading.timestamp_ms <= t_end,
        )
        .order_by(SensorReading.timestamp_ms)
    )
    readings_res = await db.execute(r_query)
    readings = list(readings_res.scalars().all())

    # Build response
    detail = MovementDetailRead(
        id=movement.id,
        session_id=movement.session_id,
        event_type=movement.event_type,
        start_time_ms=movement.start_time_ms,
        end_time_ms=movement.end_time_ms,
        duration_ms=movement.duration_ms,
        start_posture=movement.start_posture,
        end_posture=movement.end_posture,
        peak_angular_velocity=movement.peak_angular_velocity,
        avg_angular_velocity=movement.avg_angular_velocity,
        movement_smoothness=movement.movement_smoothness,
        stability_after=movement.stability_after,
        confidence=movement.confidence,
        classification_details=movement.classification_details,
        sensor_data_start_idx=movement.sensor_data_start_idx,
        sensor_data_end_idx=movement.sensor_data_end_idx,
        sensor_data=[SensorReadingRead.model_validate(r) for r in readings],
    )
    return detail


@router.get("/{session_id}/sensor-data", response_model=List[SensorReadingRead])
async def get_session_sensor_data(
    session_id: str,
    from_ms: Optional[int] = None,
    to_ms: Optional[int] = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve raw sensor data window for visualization."""
    query = select(SensorReading).where(SensorReading.session_id == session_id)
    if from_ms is not None:
        query = query.where(SensorReading.timestamp_ms >= from_ms)
    if to_ms is not None:
        query = query.where(SensorReading.timestamp_ms <= to_ms)
    query = query.order_by(SensorReading.timestamp_ms).limit(limit)

    res = await db.execute(query)
    return list(res.scalars().all())


@router.post("/{session_id}/complete", response_model=SessionDetail)
async def finalize_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Finalize a session:
      1. Calculate summary metrics (left/right rolls, sit transitions, durations)
      2. Calculate ROLLIQ Mobility Index (RMI)
      3. Save SessionMetrics record
      4. Update user's personal baseline
    """
    s_res = await db.execute(select(MonitoringSession).where(MonitoringSession.id == session_id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    if not session.ended_at:
        session.ended_at = datetime.now(timezone.utc)

    # Fetch all movements in this session
    m_res = await db.execute(
        select(MovementEvent)
        .where(MovementEvent.session_id == session_id)
        .order_by(MovementEvent.start_time_ms)
    )
    movements = list(m_res.scalars().all())

    # Calculate RMI
    rmi_result = rmi_calculator.calculate(movements)

    # Aggregate counts and metrics
    total_mov = len(movements)
    left_rolls = sum(1 for m in movements if m.event_type == "left_roll")
    right_rolls = sum(1 for m in movements if m.event_type == "right_roll")
    sit_trans = sum(1 for m in movements if m.event_type in ("supine_to_sitting", "sitting_to_supine"))

    durations = [m.duration_ms for m in movements if m.duration_ms > 0]
    avg_dur = float(np.mean(durations)) if durations else 0.0
    med_dur = float(np.median(durations)) if durations else 0.0

    velocities = [m.peak_angular_velocity for m in movements if m.peak_angular_velocity > 0]
    avg_vel = float(np.mean(velocities)) if velocities else 0.0

    smoothnesses = [m.movement_smoothness for m in movements if m.movement_smoothness > 0]
    avg_smooth = float(np.mean(smoothnesses)) if smoothnesses else 0.0

    stabilities = [m.stability_after for m in movements if m.stability_after > 0]
    avg_stab = float(np.mean(stabilities)) if stabilities else 0.0

    # Bilateral symmetry ratio
    if left_rolls + right_rolls > 0:
        sym_ratio = round(left_rolls / max(1, right_rolls), 2)
    else:
        sym_ratio = 1.0

    # Session duration
    first_r = await db.execute(
        select(SensorReading.timestamp_ms)
        .where(SensorReading.session_id == session_id)
        .order_by(SensorReading.timestamp_ms)
        .limit(1)
    )
    last_r = await db.execute(
        select(SensorReading.timestamp_ms)
        .where(SensorReading.session_id == session_id)
        .order_by(desc(SensorReading.timestamp_ms))
        .limit(1)
    )
    t0 = first_r.scalar_one_or_none() or 0
    t1 = last_r.scalar_one_or_none() or 0
    session_dur_ms = max(0, t1 - t0)

    session.total_movements = total_mov
    session.avg_transition_duration = avg_dur
    session.rmi_score = rmi_result["score"]

    # Check for existing SessionMetrics or create new
    sm_res = await db.execute(select(SessionMetrics).where(SessionMetrics.session_id == session_id))
    sm = sm_res.scalar_one_or_none()
    if not sm:
        sm = SessionMetrics(session_id=session_id)
        db.add(sm)

    sm.total_movements = total_mov
    sm.total_left_rolls = left_rolls
    sm.total_right_rolls = right_rolls
    sm.total_sit_transitions = sit_trans
    sm.avg_transition_duration_ms = avg_dur
    sm.median_transition_duration_ms = med_dur
    sm.avg_angular_velocity = avg_vel
    sm.avg_smoothness = avg_smooth
    sm.avg_stability = avg_stab
    sm.movement_symmetry = sym_ratio
    sm.rmi_score = rmi_result["score"]
    sm.rmi_components = rmi_result["components"]
    sm.data_completeness = rmi_result["completeness"]
    sm.session_duration_ms = session_dur_ms

    await db.flush()

    # Update personal baseline for user
    all_metrics_res = await db.execute(
        select(SessionMetrics)
        .join(MonitoringSession, SessionMetrics.session_id == MonitoringSession.id)
        .where(MonitoringSession.user_id == session.user_id)
    )
    all_user_metrics = list(all_metrics_res.scalars().all())

    new_baseline_dict = BaselineEngine.compute_baseline(all_user_metrics)

    b_res = await db.execute(select(PersonalBaseline).where(PersonalBaseline.user_id == session.user_id))
    pb = b_res.scalar_one_or_none()
    if not pb:
        pb = PersonalBaseline(user_id=session.user_id)
        db.add(pb)

    pb.sessions_used = new_baseline_dict["sessions_used"]
    pb.is_ready = new_baseline_dict["is_ready"]
    pb.avg_transition_duration = new_baseline_dict["avg_transition_duration"]
    pb.std_transition_duration = new_baseline_dict["std_transition_duration"]
    pb.avg_angular_velocity = new_baseline_dict["avg_angular_velocity"]
    pb.std_angular_velocity = new_baseline_dict["std_angular_velocity"]
    pb.avg_smoothness = new_baseline_dict["avg_smoothness"]
    pb.std_smoothness = new_baseline_dict["std_smoothness"]
    pb.avg_stability = new_baseline_dict["avg_stability"]
    pb.std_stability = new_baseline_dict["std_stability"]
    pb.avg_rmi = new_baseline_dict["avg_rmi"]
    pb.std_rmi = new_baseline_dict["std_rmi"]
    pb.baseline_data = new_baseline_dict["baseline_data"]
    pb.last_updated = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(session)

    return await get_session(session_id, db)
