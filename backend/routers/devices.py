"""
ROLLIQ Device Management Router.
Tracks ESP32 hardware registration, MPU6050 calibration records, and live connection status.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import Device, CalibrationRecord
from schemas import (
    DeviceCreate, DeviceUpdate, DeviceRead, DeviceStatus,
    CalibrationCreate, CalibrationRead
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def register_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    """Register a new ESP32 + MPU6050 hardware node."""
    res = await db.execute(select(Device).where(Device.id == payload.id))
    existing = res.scalar_one_or_none()
    if existing:
        existing.name = payload.name
        existing.firmware_version = payload.firmware_version
        existing.last_seen = datetime.now(timezone.utc)
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return existing

    device = Device(
        id=payload.id,
        name=payload.name,
        firmware_version=payload.firmware_version,
        is_active=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("", response_model=List[DeviceRead])
async def list_devices(db: AsyncSession = Depends(get_db)):
    """List all registered devices."""
    res = await db.execute(select(Device).order_by(desc(Device.last_seen)))
    return list(res.scalars().all())


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """Get single device details."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device(device_id: str, payload: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    """Update device metadata."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if payload.name is not None:
        device.name = payload.name
    if payload.firmware_version is not None:
        device.firmware_version = payload.firmware_version
    if payload.is_active is not None:
        device.is_active = payload.is_active
    if payload.calibration_data is not None:
        device.calibration_data = payload.calibration_data

    await db.commit()
    await db.refresh(device)
    return device


@router.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(device_id: str, db: AsyncSession = Depends(get_db)):
    """Check device connectivity and time since last transmission."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = datetime.now(timezone.utc)
    # Ensure timezone awareness for subtraction
    last = device.last_seen
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    delta = max(0.0, (now - last).total_seconds())

    return DeviceStatus(
        id=device.id,
        name=device.name,
        is_active=device.is_active and delta < 30.0,
        last_seen=device.last_seen,
        seconds_since_last_seen=round(delta, 1),
    )


@router.post("/{device_id}/calibrate", response_model=CalibrationRead)
async def record_calibration(
    device_id: str, payload: CalibrationCreate, db: AsyncSession = Depends(get_db)
):
    """Store sensor calibration biases (accel & gyro offsets) from ESP32."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    cal = CalibrationRecord(
        device_id=device_id,
        accel_offsets=payload.accel_offsets,
        gyro_offsets=payload.gyro_offsets,
        is_valid=True,
        calibrated_at=datetime.now(timezone.utc),
    )
    db.add(cal)

    device.calibration_data = {
        "accel_offsets": payload.accel_offsets,
        "gyro_offsets": payload.gyro_offsets,
        "last_calibrated": datetime.now(timezone.utc).isoformat(),
    }
    await db.commit()
    await db.refresh(cal)
    return cal
