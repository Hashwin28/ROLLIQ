"""
ROLLIQ Pydantic Schemas — request / response models for the API layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── helpers ───────────────────────────────────────────────────────────────
def _uuid_str() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# User
# ═══════════════════════════════════════════════════════════════════════════
class UserCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    age_group: Optional[str] = Field(None, pattern="^(child|adult|elderly)$")


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    age_group: Optional[str] = Field(None, pattern="^(child|adult|elderly)$")


class UserRead(BaseModel):
    id: str
    display_name: str
    age_group: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Device
# ═══════════════════════════════════════════════════════════════════════════
class DeviceCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    firmware_version: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    firmware_version: Optional[str] = None
    is_active: Optional[bool] = None
    calibration_data: Optional[Dict[str, Any]] = None


class DeviceRead(BaseModel):
    id: str
    name: str
    last_seen: datetime
    firmware_version: Optional[str] = None
    is_active: bool
    calibration_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceStatus(BaseModel):
    id: str
    name: str
    is_active: bool
    last_seen: datetime
    seconds_since_last_seen: float


class CalibrationCreate(BaseModel):
    accel_offsets: Dict[str, float] = Field(default_factory=dict)
    gyro_offsets: Dict[str, float] = Field(default_factory=dict)


class CalibrationRead(BaseModel):
    id: str
    device_id: str
    calibrated_at: datetime
    accel_offsets: Optional[Dict[str, float]] = None
    gyro_offsets: Optional[Dict[str, float]] = None
    is_valid: bool

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Monitoring Session
# ═══════════════════════════════════════════════════════════════════════════
class SessionCreate(BaseModel):
    user_id: str
    device_id: Optional[str] = None
    is_simulation: bool = False
    simulation_scenario: Optional[str] = None
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(active|paused|completed|incomplete)$")
    notes: Optional[str] = None


class SessionRead(BaseModel):
    id: str
    user_id: str
    device_id: Optional[str] = None
    is_simulation: bool
    simulation_scenario: Optional[str] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_movements: int
    avg_transition_duration: Optional[float] = None
    rmi_score: Optional[float] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionDetail(SessionRead):
    metrics: Optional[SessionMetricsRead] = None
    movement_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# Sensor Data
# ═══════════════════════════════════════════════════════════════════════════
class SensorSample(BaseModel):
    timestamp_ms: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    packet_sequence: int = 0

    @field_validator("ax", "ay", "az")
    @classmethod
    def accel_finite(cls, v: float) -> float:
        import math
        if not math.isfinite(v):
            raise ValueError("Accelerometer value must be finite")
        return v

    @field_validator("gx", "gy", "gz")
    @classmethod
    def gyro_finite(cls, v: float) -> float:
        import math
        if not math.isfinite(v):
            raise ValueError("Gyroscope value must be finite")
        return v


class SensorBatch(BaseModel):
    session_id: str
    device_id: Optional[str] = None
    samples: List[SensorSample] = Field(..., min_length=1)


class SensorBatchAck(BaseModel):
    received: int
    processed: int
    commands: List[str] = Field(default_factory=list)


class SensorReadingRead(BaseModel):
    id: int
    session_id: str
    timestamp_ms: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    roll: float
    pitch: float
    signal_quality: float
    packet_sequence: int

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Movement Event
# ═══════════════════════════════════════════════════════════════════════════
class MovementEventRead(BaseModel):
    id: str
    session_id: str
    event_type: str
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    start_posture: Optional[str] = None
    end_posture: Optional[str] = None
    peak_angular_velocity: float
    avg_angular_velocity: float
    movement_smoothness: float
    stability_after: float
    confidence: float
    classification_details: Optional[Dict[str, Any]] = None
    sensor_data_start_idx: Optional[int] = None
    sensor_data_end_idx: Optional[int] = None

    model_config = {"from_attributes": True}


class MovementDetailRead(MovementEventRead):
    sensor_data: List[SensorReadingRead] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Session Metrics
# ═══════════════════════════════════════════════════════════════════════════
class SessionMetricsRead(BaseModel):
    id: str
    session_id: str
    total_movements: int
    total_left_rolls: int
    total_right_rolls: int
    total_sit_transitions: int
    avg_transition_duration_ms: float
    median_transition_duration_ms: float
    avg_angular_velocity: float
    avg_smoothness: float
    avg_stability: float
    movement_symmetry: float
    rmi_score: float
    rmi_components: Optional[Dict[str, Any]] = None
    data_completeness: float
    session_duration_ms: int

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Personal Baseline
# ═══════════════════════════════════════════════════════════════════════════
class BaselineRead(BaseModel):
    id: str
    user_id: str
    sessions_used: int
    avg_transition_duration: float
    std_transition_duration: float
    avg_angular_velocity: float
    std_angular_velocity: float
    avg_smoothness: float
    std_smoothness: float
    avg_stability: float
    std_stability: float
    avg_rmi: float
    std_rmi: float
    last_updated: datetime
    is_ready: bool
    baseline_data: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class BaselineComparison(BaseModel):
    metric_name: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    deviation_direction: str  # "above" | "below" | "within"
    is_significant: bool


class BaselineComparisonResult(BaseModel):
    user_id: str
    session_id: str
    baseline_ready: bool
    comparisons: List[BaselineComparison] = Field(default_factory=list)
    overall_deviation: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Alert
# ═══════════════════════════════════════════════════════════════════════════
class AlertRead(BaseModel):
    id: str
    session_id: Optional[str] = None
    user_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    measurement_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════
class RMIHistoryPoint(BaseModel):
    session_id: str
    date: datetime
    rmi_score: float
    total_movements: int


class MovementDistribution(BaseModel):
    event_type: str
    count: int
    percentage: float


class DurationTrend(BaseModel):
    session_id: str
    date: datetime
    avg_duration_ms: float
    median_duration_ms: float


class SymmetryData(BaseModel):
    session_id: str
    date: datetime
    left_rolls: int
    right_rolls: int
    symmetry_ratio: float


class SmoothnessTrend(BaseModel):
    session_id: str
    date: datetime
    avg_smoothness: float


class SessionComparisonResult(BaseModel):
    session_a: SessionMetricsRead
    session_b: SessionMetricsRead
    differences: Dict[str, float]


# ═══════════════════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════════════════
class SimulationStartRequest(BaseModel):
    user_id: str
    scenario: str = "normal_rolling"
    speed: float = Field(1.0, ge=0.5, le=5.0)


class SimulationStatusResponse(BaseModel):
    is_running: bool
    is_paused: bool
    scenario: Optional[str] = None
    session_id: Optional[str] = None
    speed: float = 1.0
    elapsed_ms: int = 0
    samples_generated: int = 0


class SimulationScenario(BaseModel):
    name: str
    description: str
    estimated_duration_s: int


class ScenarioChangeRequest(BaseModel):
    scenario: str


# ── Forward-ref resolution ───────────────────────────────────────────────
SessionDetail.model_rebuild()
