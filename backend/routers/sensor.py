"""
ROLLIQ Sensor Ingestion Router.
Receives telemetry packets, executes signal processing pipeline, broadcasts real-time events.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db, async_session_factory
from models import MonitoringSession, SensorReading, MovementEvent, Alert
from schemas import SensorBatch, SensorBatchAck, SensorReadingRead
from services.signal_processor import SignalProcessor, ProcessedSample
from services.posture_detector import PostureDetector
from services.movement_classifier import MovementClassifier
from services.alert_service import AlertService
from websocket.manager import ws_manager

router = APIRouter(prefix="/api/sensor", tags=["sensor"])

# In-memory per-session pipeline instances
_pipelines: Dict[str, Dict[str, Any]] = {}
alert_service = AlertService()


def get_pipeline(session_id: str) -> Dict[str, Any]:
    if session_id not in _pipelines:
        _pipelines[session_id] = {
            "processor": SignalProcessor(),
            "detector": PostureDetector(),
            "classifier": MovementClassifier(),
            "last_posture": "unknown",
            "last_packet_time": 0,
            "posture_start_ms": 0,
        }
    return _pipelines[session_id]


@router.post("/data", response_model=SensorBatchAck)
async def ingest_sensor_data(batch: SensorBatch, db: AsyncSession = Depends(get_db)):
    """
    Ingest a batch of raw 6-axis IMU samples from ESP32 or Simulator.
    Applies filtering, posture detection, movement classification, and broadcast.
    """
    if not batch.samples:
        return SensorBatchAck(received=0, processed=0)

    # Verify session exists
    session_res = await db.execute(select(MonitoringSession).where(MonitoringSession.id == batch.session_id))
    session = session_res.scalar_one_or_none()
    if not session:
        # Create session on the fly if needed (e.g. simulation or direct ESP32 boot)
        session = MonitoringSession(
            id=batch.session_id,
            user_id="default-user",
            device_id=batch.device_id,
            status="active",
        )
        db.add(session)
        await db.flush()

    pipeline = get_pipeline(batch.session_id)
    processor: SignalProcessor = pipeline["processor"]
    detector: PostureDetector = pipeline["detector"]
    classifier: MovementClassifier = pipeline["classifier"]

    # Convert samples to dictionary format expected by SignalProcessor
    sample_dicts = [
        {
            "timestamp_ms": s.timestamp_ms,
            "ax": s.ax,
            "ay": s.ay,
            "az": s.az,
            "gx": s.gx,
            "gy": s.gy,
            "gz": s.gz,
            "packet_sequence": s.packet_sequence,
        }
        for s in batch.samples
    ]

    # Process signals (Butterworth/LPF, roll, pitch, signal quality)
    processed_samples = processor.process_batch(sample_dicts)

    # Detect postures
    posture_readings = [detector.detect(ps) for ps in processed_samples]

    # Feed classifier
    new_movements = classifier.feed(processed_samples, posture_readings)

    # Prepare DB readings
    db_readings = []
    ws_readings = []
    for ps in processed_samples:
        db_readings.append(
            SensorReading(
                session_id=batch.session_id,
                timestamp_ms=ps.timestamp_ms,
                ax=ps.ax,
                ay=ps.ay,
                az=ps.az,
                gx=ps.gx,
                gy=ps.gy,
                gz=ps.gz,
                roll=ps.roll,
                pitch=ps.pitch,
                signal_quality=ps.signal_quality,
                packet_sequence=ps.packet_sequence,
            )
        )
        ws_readings.append({
            "timestamp_ms": ps.timestamp_ms,
            "ax": round(ps.ax, 3),
            "ay": round(ps.ay, 3),
            "az": round(ps.az, 3),
            "gx": round(ps.gx, 2),
            "gy": round(ps.gy, 2),
            "gz": round(ps.gz, 2),
            "roll": round(ps.roll, 2),
            "pitch": round(ps.pitch, 2),
            "signal_quality": round(ps.signal_quality, 2),
            "packet_sequence": ps.packet_sequence,
        })

    # Add readings to DB in batch
    db.add_all(db_readings)

    # Record any completed movement events
    for me in new_movements:
        session.total_movements = (session.total_movements or 0) + 1
        db_me = MovementEvent(
            id=me.id,
            session_id=batch.session_id,
            event_type=me.event_type,
            start_time_ms=me.start_time_ms,
            end_time_ms=me.end_time_ms,
            duration_ms=me.duration_ms,
            start_posture=me.start_posture,
            end_posture=me.end_posture,
            peak_angular_velocity=me.peak_angular_velocity,
            avg_angular_velocity=me.avg_angular_velocity,
            movement_smoothness=me.movement_smoothness,
            stability_after=me.stability_after,
            confidence=me.confidence,
            classification_details=me.classification_details,
            sensor_data_start_idx=me.sensor_data_start_idx,
            sensor_data_end_idx=me.sensor_data_end_idx,
        )
        db.add(db_me)

        # Check for unusual movement alert
        al = alert_service.check_unusual_movement(batch.session_id, session.user_id, me)
        if al:
            db_al = Alert(**al)
            db.add(db_al)
            await ws_manager.broadcast_alert(batch.session_id, al)

        # Broadcast movement to clients
        await ws_manager.broadcast_movement(batch.session_id, {
            "id": me.id,
            "event_type": me.event_type,
            "start_time_ms": me.start_time_ms,
            "end_time_ms": me.end_time_ms,
            "duration_ms": me.duration_ms,
            "start_posture": me.start_posture,
            "end_posture": me.end_posture,
            "peak_angular_velocity": me.peak_angular_velocity,
            "avg_angular_velocity": me.avg_angular_velocity,
            "movement_smoothness": me.movement_smoothness,
            "stability_after": me.stability_after,
            "confidence": me.confidence,
            "classification_details": me.classification_details,
        })

    # Check posture change & prolonged posture
    if posture_readings:
        latest_pr = posture_readings[-1]
        current_posture_str = str(latest_pr.posture.value)
        if current_posture_str != pipeline["last_posture"]:
            pipeline["last_posture"] = current_posture_str
            pipeline["posture_start_ms"] = latest_pr.timestamp_ms
            await ws_manager.broadcast_posture(
                batch.session_id, current_posture_str, latest_pr.confidence
            )
        else:
            # Check prolonged posture
            dwell_sec = (latest_pr.timestamp_ms - pipeline["posture_start_ms"]) / 1000.0
            pal = alert_service.check_prolonged_posture(
                batch.session_id, session.user_id, current_posture_str, dwell_sec, threshold_sec=1200.0
            )
            if pal:
                db_pal = Alert(**pal)
                db.add(db_pal)
                await ws_manager.broadcast_alert(batch.session_id, pal)

    # Broadcast sensor readings batch over WebSocket
    await ws_manager.broadcast_sensor_data(batch.session_id, ws_readings)

    await db.commit()

    return SensorBatchAck(
        received=len(batch.samples),
        processed=len(processed_samples),
        commands=[],
    )


@router.get("/latest/{session_id}", response_model=List[SensorReadingRead])
async def get_latest_readings(
    session_id: str, limit: int = 200, db: AsyncSession = Depends(get_db)
):
    """Retrieve the most recent sensor readings for a session."""
    query = (
        select(SensorReading)
        .where(SensorReading.session_id == session_id)
        .order_by(desc(SensorReading.timestamp_ms))
        .limit(limit)
    )
    result = await db.execute(query)
    readings = list(result.scalars().all())
    readings.reverse()  # Return in chronological order
    return readings


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Live streaming WebSocket connection for session monitoring."""
    await ws_manager.connect(websocket, session_id)
    try:
        while True:
            # Keep alive and listen for client ping or instructions
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)
    except Exception:
        ws_manager.disconnect(websocket, session_id)
