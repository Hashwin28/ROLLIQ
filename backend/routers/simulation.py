"""
ROLLIQ Simulation Router.
Controls the 10-scenario IMU simulation engine, streaming through the real processing pipeline.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, async_session_factory
from models import MonitoringSession, User
from schemas import (
    SimulationStartRequest, SimulationStatusResponse,
    SimulationScenario, ScenarioChangeRequest, SensorBatch
)
from services.simulation_engine import SimulationEngine
from routers.sensor import ingest_sensor_data

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Singleton simulation engine instance
_sim_engine = SimulationEngine()


async def _handle_sim_batch(batch: SensorBatch):
    """Callback receiving simulated batch and pushing through the real ingestion router."""
    async with async_session_factory() as session:
        try:
            await ingest_sensor_data(batch, db=session)
        except Exception as e:
            # Avoid crashing simulation task on batch error
            pass


_sim_engine.callback = _handle_sim_batch


@router.get("/scenarios", response_model=List[SimulationScenario])
async def list_simulation_scenarios():
    """List all 10 predefined clinical and ergonomic simulation scenarios."""
    scenarios = _sim_engine.get_available_scenarios()
    return [
        SimulationScenario(
            name=s["key"],
            description=f"{s['name']} — {s['description']}",
            estimated_duration_s=60,
        )
        for s in scenarios
    ]


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status():
    """Get current simulation engine state."""
    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=state["is_running"],
        is_paused=state["is_paused"],
        scenario=state["current_scenario"],
        session_id=state["session_id"],
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )


@router.post("/start", response_model=SimulationStatusResponse)
async def start_simulation(payload: SimulationStartRequest, db: AsyncSession = Depends(get_db)):
    """
    Start simulation mode:
      1. Creates a real monitoring session flagged as `is_simulation=True`
      2. Starts the background 50 Hz IMU generator
      3. Streams data through the exact same processing, classification, and WS pipeline
    """
    # Ensure user exists or create default
    u_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        user = User(id=payload.user_id, display_name="Simulation Subject", age_group="adult")
        db.add(user)
        await db.flush()

    # Create session
    new_session = MonitoringSession(
        user_id=payload.user_id,
        device_id="SIM-ROLLIQ-NODE",
        is_simulation=True,
        simulation_scenario=payload.scenario,
        status="active",
        started_at=datetime.now(timezone.utc),
        notes=f"Simulated scenario: {payload.scenario}",
        total_movements=0,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Launch engine
    await _sim_engine.start(
        session_id=new_session.id,
        scenario=payload.scenario,
        speed=payload.speed,
    )

    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=state["is_running"],
        is_paused=state["is_paused"],
        scenario=state["current_scenario"],
        session_id=new_session.id,
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )


@router.post("/stop", response_model=SimulationStatusResponse)
async def stop_simulation():
    """Stop the running simulation."""
    await _sim_engine.stop()
    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=False,
        is_paused=False,
        scenario=state["current_scenario"],
        session_id=state["session_id"],
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )


@router.post("/pause", response_model=SimulationStatusResponse)
async def pause_simulation():
    """Pause the running simulation."""
    await _sim_engine.pause()
    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=state["is_running"],
        is_paused=True,
        scenario=state["current_scenario"],
        session_id=state["session_id"],
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )


@router.post("/resume", response_model=SimulationStatusResponse)
async def resume_simulation():
    """Resume a paused simulation."""
    await _sim_engine.resume()
    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=state["is_running"],
        is_paused=False,
        scenario=state["current_scenario"],
        session_id=state["session_id"],
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )


@router.post("/scenario", response_model=SimulationStatusResponse)
async def change_scenario(payload: ScenarioChangeRequest):
    """Change active simulation scenario on the fly."""
    ok = _sim_engine.set_scenario(payload.scenario)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid scenario key")
    state = _sim_engine.get_status()
    return SimulationStatusResponse(
        is_running=state["is_running"],
        is_paused=state["is_paused"],
        scenario=state["current_scenario"],
        session_id=state["session_id"],
        speed=state["speed"],
        samples_generated=state["packets_generated"],
    )
