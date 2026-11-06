"""
ROLLIQ ORM Models — SQLAlchemy 2.0 async models for all database tables.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, JSON, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# User
# ═══════════════════════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    display_name = Column(String, nullable=False)
    age_group = Column(String, nullable=True)  # child | adult | elderly
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    sessions = relationship("MonitoringSession", back_populates="user", cascade="all, delete-orphan")
    baselines = relationship("PersonalBaseline", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════════════════
# Device
# ═══════════════════════════════════════════════════════════════════════════
class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)  # hardware ID
    name = Column(String, nullable=False)
    last_seen = Column(DateTime, default=_utcnow)
    firmware_version = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    calibration_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    sessions = relationship("MonitoringSession", back_populates="device")
    calibrations = relationship("CalibrationRecord", back_populates="device", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════════════════
# Monitoring Session
# ═══════════════════════════════════════════════════════════════════════════
class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)
    is_simulation = Column(Boolean, default=False)
    simulation_scenario = Column(String, nullable=True)
    status = Column(String, default="active")  # active | paused | completed | incomplete
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_movements = Column(Integer, default=0)
    avg_transition_duration = Column(Float, nullable=True)
    rmi_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    readings = relationship("SensorReading", back_populates="session", cascade="all, delete-orphan")
    movements = relationship("MovementEvent", back_populates="session", cascade="all, delete-orphan")
    metrics = relationship("SessionMetrics", back_populates="session", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="session", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════════════════
# Sensor Reading
# ═══════════════════════════════════════════════════════════════════════════
class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("monitoring_sessions.id"), nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    ax = Column(Float, nullable=False)
    ay = Column(Float, nullable=False)
    az = Column(Float, nullable=False)
    gx = Column(Float, nullable=False)
    gy = Column(Float, nullable=False)
    gz = Column(Float, nullable=False)
    roll = Column(Float, nullable=False, default=0.0)
    pitch = Column(Float, nullable=False, default=0.0)
    signal_quality = Column(Float, default=1.0)
    packet_sequence = Column(Integer, default=0)

    session = relationship("MonitoringSession", back_populates="readings")


# ═══════════════════════════════════════════════════════════════════════════
# Movement Event
# ═══════════════════════════════════════════════════════════════════════════
class MovementEvent(Base):
    __tablename__ = "movement_events"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("monitoring_sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    start_time_ms = Column(Integer, nullable=False)
    end_time_ms = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    start_posture = Column(String, nullable=True)
    end_posture = Column(String, nullable=True)
    peak_angular_velocity = Column(Float, default=0.0)
    avg_angular_velocity = Column(Float, default=0.0)
    movement_smoothness = Column(Float, default=0.0)
    stability_after = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    classification_details = Column(JSON, nullable=True)
    sensor_data_start_idx = Column(Integer, nullable=True)
    sensor_data_end_idx = Column(Integer, nullable=True)

    session = relationship("MonitoringSession", back_populates="movements")


# ═══════════════════════════════════════════════════════════════════════════
# Session Metrics
# ═══════════════════════════════════════════════════════════════════════════
class SessionMetrics(Base):
    __tablename__ = "session_metrics"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("monitoring_sessions.id"), unique=True, nullable=False)
    total_movements = Column(Integer, default=0)
    total_left_rolls = Column(Integer, default=0)
    total_right_rolls = Column(Integer, default=0)
    total_sit_transitions = Column(Integer, default=0)
    avg_transition_duration_ms = Column(Float, default=0.0)
    median_transition_duration_ms = Column(Float, default=0.0)
    avg_angular_velocity = Column(Float, default=0.0)
    avg_smoothness = Column(Float, default=0.0)
    avg_stability = Column(Float, default=0.0)
    movement_symmetry = Column(Float, default=1.0)
    rmi_score = Column(Float, default=0.0)
    rmi_components = Column(JSON, nullable=True)
    data_completeness = Column(Float, default=1.0)
    session_duration_ms = Column(Integer, default=0)

    session = relationship("MonitoringSession", back_populates="metrics")


# ═══════════════════════════════════════════════════════════════════════════
# Personal Baseline
# ═══════════════════════════════════════════════════════════════════════════
class PersonalBaseline(Base):
    __tablename__ = "personal_baselines"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    sessions_used = Column(Integer, default=0)
    avg_transition_duration = Column(Float, default=0.0)
    std_transition_duration = Column(Float, default=0.0)
    avg_angular_velocity = Column(Float, default=0.0)
    std_angular_velocity = Column(Float, default=0.0)
    avg_smoothness = Column(Float, default=0.0)
    std_smoothness = Column(Float, default=0.0)
    avg_stability = Column(Float, default=0.0)
    std_stability = Column(Float, default=0.0)
    avg_rmi = Column(Float, default=0.0)
    std_rmi = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=_utcnow)
    is_ready = Column(Boolean, default=False)
    baseline_data = Column(JSON, nullable=True)

    user = relationship("User", back_populates="baselines")


# ═══════════════════════════════════════════════════════════════════════════
# Alert
# ═══════════════════════════════════════════════════════════════════════════
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("monitoring_sessions.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String, default="info")  # info | warning | attention
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    measurement_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("MonitoringSession", back_populates="alerts")
    user = relationship("User", back_populates="alerts")


# ═══════════════════════════════════════════════════════════════════════════
# Calibration Record
# ═══════════════════════════════════════════════════════════════════════════
class CalibrationRecord(Base):
    __tablename__ = "calibration_records"

    id = Column(String, primary_key=True, default=_uuid)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    calibrated_at = Column(DateTime, default=_utcnow)
    accel_offsets = Column(JSON, nullable=True)
    gyro_offsets = Column(JSON, nullable=True)
    is_valid = Column(Boolean, default=True)

    device = relationship("Device", back_populates="calibrations")
