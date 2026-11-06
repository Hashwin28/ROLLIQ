"""
ROLLIQ Configuration — all settings configurable via environment variables.
"""
import os
from typing import List


class Settings:
    """Central configuration for the ROLLIQ backend."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./rolliq.db")

    # ── Sensor ────────────────────────────────────────────────────────────
    SAMPLING_RATE: int = int(os.getenv("SAMPLING_RATE", "50"))  # Hz
    SENSOR_BUFFER_SIZE: int = int(os.getenv("SENSOR_BUFFER_SIZE", "50"))

    # ── Movement Detection ────────────────────────────────────────────────
    MOVEMENT_ANGULAR_VELOCITY_THRESHOLD: float = float(
        os.getenv("MOVEMENT_ANGULAR_VELOCITY_THRESHOLD", "15.0")
    )  # deg/s
    MOVEMENT_END_THRESHOLD: float = float(
        os.getenv("MOVEMENT_END_THRESHOLD", "5.0")
    )  # deg/s
    MOVEMENT_END_SUSTAIN_MS: int = int(
        os.getenv("MOVEMENT_END_SUSTAIN_MS", "500")
    )  # ms below threshold
    MOVEMENT_MIN_DURATION_MS: int = int(
        os.getenv("MOVEMENT_MIN_DURATION_MS", "200")
    )
    MOVEMENT_MAX_DURATION_MS: int = int(
        os.getenv("MOVEMENT_MAX_DURATION_MS", "15000")
    )

    # ── Posture Detection ─────────────────────────────────────────────────
    POSTURE_SUPINE_AZ_MIN: float = float(os.getenv("POSTURE_SUPINE_AZ_MIN", "0.7"))
    POSTURE_PRONE_AZ_MAX: float = float(os.getenv("POSTURE_PRONE_AZ_MAX", "-0.7"))
    POSTURE_LEFT_AY_MIN: float = float(os.getenv("POSTURE_LEFT_AY_MIN", "0.7"))
    POSTURE_RIGHT_AY_MAX: float = float(os.getenv("POSTURE_RIGHT_AY_MAX", "-0.7"))
    POSTURE_SITTING_AX_MIN: float = float(os.getenv("POSTURE_SITTING_AX_MIN", "0.5"))
    POSTURE_SITTING_AZ_MAX: float = float(os.getenv("POSTURE_SITTING_AZ_MAX", "0.6"))
    POSTURE_HYSTERESIS_MS: int = int(os.getenv("POSTURE_HYSTERESIS_MS", "500"))

    # ── RMI Weights (must sum to 1.0) ────────────────────────────────────
    RMI_WEIGHT_DURATION: float = float(os.getenv("RMI_WEIGHT_DURATION", "0.20"))
    RMI_WEIGHT_SMOOTHNESS: float = float(os.getenv("RMI_WEIGHT_SMOOTHNESS", "0.20"))
    RMI_WEIGHT_VELOCITY: float = float(os.getenv("RMI_WEIGHT_VELOCITY", "0.15"))
    RMI_WEIGHT_STABILITY: float = float(os.getenv("RMI_WEIGHT_STABILITY", "0.15"))
    RMI_WEIGHT_COMPLETION: float = float(os.getenv("RMI_WEIGHT_COMPLETION", "0.15"))
    RMI_WEIGHT_CONSISTENCY: float = float(os.getenv("RMI_WEIGHT_CONSISTENCY", "0.15"))

    # Optimal ranges for RMI scoring
    RMI_OPTIMAL_DURATION_MIN_MS: float = float(
        os.getenv("RMI_OPTIMAL_DURATION_MIN_MS", "1000")
    )
    RMI_OPTIMAL_DURATION_MAX_MS: float = float(
        os.getenv("RMI_OPTIMAL_DURATION_MAX_MS", "5000")
    )
    RMI_OPTIMAL_VELOCITY_MIN: float = float(
        os.getenv("RMI_OPTIMAL_VELOCITY_MIN", "20.0")
    )
    RMI_OPTIMAL_VELOCITY_MAX: float = float(
        os.getenv("RMI_OPTIMAL_VELOCITY_MAX", "80.0")
    )

    # ── Baseline ──────────────────────────────────────────────────────────
    BASELINE_MIN_SESSIONS: int = int(os.getenv("BASELINE_MIN_SESSIONS", "3"))
    BASELINE_MIN_MOVEMENTS: int = int(os.getenv("BASELINE_MIN_MOVEMENTS", "5"))
    BASELINE_ROLLING_WINDOW: int = int(os.getenv("BASELINE_ROLLING_WINDOW", "10"))
    BASELINE_DEVIATION_THRESHOLD: float = float(
        os.getenv("BASELINE_DEVIATION_THRESHOLD", "1.5")
    )

    # ── Alert Thresholds ──────────────────────────────────────────────────
    ALERT_PROLONGED_POSTURE_MIN: int = int(
        os.getenv("ALERT_PROLONGED_POSTURE_MIN", "1800000")
    )  # 30 min in ms
    ALERT_UNUSUAL_MOVEMENT_STD: float = float(
        os.getenv("ALERT_UNUSUAL_MOVEMENT_STD", "2.0")
    )
    ALERT_SENSOR_DISCONNECT_MS: int = int(
        os.getenv("ALERT_SENSOR_DISCONNECT_MS", "10000")
    )  # 10s
    ALERT_INCOMPLETE_SESSION_MIN_DURATION_MS: int = int(
        os.getenv("ALERT_INCOMPLETE_SESSION_MIN_DURATION_MS", "600000")
    )  # 10 min
    ALERT_INCOMPLETE_SESSION_MIN_MOVEMENTS: int = int(
        os.getenv("ALERT_INCOMPLETE_SESSION_MIN_MOVEMENTS", "3")
    )
    ALERT_COOLDOWN_MS: int = int(
        os.getenv("ALERT_COOLDOWN_MS", "300000")
    )  # 5 min between duplicate alerts

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "*"
    ).split(",")

    # ── Signal Processing ─────────────────────────────────────────────────
    LOWPASS_CUTOFF_HZ: float = float(os.getenv("LOWPASS_CUTOFF_HZ", "5.0"))
    LOWPASS_ORDER: int = int(os.getenv("LOWPASS_ORDER", "4"))
    SPIKE_THRESHOLD_G: float = float(os.getenv("SPIKE_THRESHOLD_G", "4.0"))
    NOISE_WINDOW_SIZE: int = int(os.getenv("NOISE_WINDOW_SIZE", "10"))

    # ── Simulation ────────────────────────────────────────────────────────
    SIMULATION_DEFAULT_SPEED: float = float(
        os.getenv("SIMULATION_DEFAULT_SPEED", "1.0")
    )
    SIMULATION_NOISE_STD_ACCEL: float = float(
        os.getenv("SIMULATION_NOISE_STD_ACCEL", "0.02")
    )
    SIMULATION_NOISE_STD_GYRO: float = float(
        os.getenv("SIMULATION_NOISE_STD_GYRO", "0.5")
    )


settings = Settings()
