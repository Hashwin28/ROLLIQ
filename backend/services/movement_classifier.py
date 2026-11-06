"""
Movement Classifier — detect, segment, and classify bed-mobility events
from a sliding window of processed sensor data.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from config import settings
from services.signal_processor import ProcessedSample
from services.posture_detector import Posture, PostureReading


EVENT_TYPES = [
    "left_roll",
    "right_roll",
    "supine_to_sitting",
    "sitting_to_supine",
    "posture_transition",
    "minor_adjustment",
    "unclassified",
]


@dataclass
class MovementEventData:
    """Intermediate structure returned by the classifier (not ORM)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "unclassified"
    start_time_ms: int = 0
    end_time_ms: int = 0
    duration_ms: int = 0
    start_posture: str = "unknown"
    end_posture: str = "unknown"
    peak_angular_velocity: float = 0.0
    avg_angular_velocity: float = 0.0
    movement_smoothness: float = 0.0
    stability_after: float = 0.0
    confidence: float = 0.0
    classification_details: Dict[str, Any] = field(default_factory=dict)
    sensor_data_start_idx: Optional[int] = None
    sensor_data_end_idx: Optional[int] = None


class MovementClassifier:
    """Stateful classifier that maintains a sliding window and detects movements."""

    def __init__(self):
        self._buffer: List[ProcessedSample] = []
        self._postures: List[PostureReading] = []
        self._in_movement: bool = False
        self._movement_start_idx: int = 0
        self._below_threshold_start: Optional[int] = None
        self._total_idx: int = 0  # running index across all batches
        self._pending_events: List[MovementEventData] = []

    def feed(
        self,
        samples: List[ProcessedSample],
        postures: List[PostureReading],
    ) -> List[MovementEventData]:
        """Feed new processed samples and posture readings.
        Returns any movement events completed in this batch.
        """
        events: List[MovementEventData] = []

        for i, (sample, posture) in enumerate(zip(samples, postures)):
            global_idx = self._total_idx
            self._total_idx += 1

            self._buffer.append(sample)
            self._postures.append(posture)

            # Keep buffer bounded (last 500 samples ≈ 10s at 50Hz)
            max_buf = 500
            if len(self._buffer) > max_buf:
                trim = len(self._buffer) - max_buf
                self._buffer = self._buffer[trim:]
                self._postures = self._postures[trim:]
                if self._in_movement:
                    self._movement_start_idx = max(0, self._movement_start_idx - trim)

            gyro_mag = sample.gyro_magnitude

            if not self._in_movement:
                # Detect movement onset
                if gyro_mag >= settings.MOVEMENT_ANGULAR_VELOCITY_THRESHOLD:
                    self._in_movement = True
                    self._movement_start_idx = len(self._buffer) - 1
                    self._below_threshold_start = None
            else:
                # Detect movement end
                if gyro_mag < settings.MOVEMENT_END_THRESHOLD:
                    if self._below_threshold_start is None:
                        self._below_threshold_start = sample.timestamp_ms
                    else:
                        quiet_dur = sample.timestamp_ms - self._below_threshold_start
                        if quiet_dur >= settings.MOVEMENT_END_SUSTAIN_MS:
                            # Movement ended
                            end_idx = len(self._buffer) - 1
                            ev = self._extract_event(
                                self._movement_start_idx, end_idx,
                            )
                            if ev is not None:
                                events.append(ev)
                            self._in_movement = False
                            self._below_threshold_start = None
                else:
                    self._below_threshold_start = None

                # Safety: if movement too long, force close
                if self._in_movement and len(self._buffer) > self._movement_start_idx:
                    dur = (
                        self._buffer[-1].timestamp_ms
                        - self._buffer[self._movement_start_idx].timestamp_ms
                    )
                    if dur > settings.MOVEMENT_MAX_DURATION_MS:
                        end_idx = len(self._buffer) - 1
                        ev = self._extract_event(self._movement_start_idx, end_idx)
                        if ev is not None:
                            events.append(ev)
                        self._in_movement = False
                        self._below_threshold_start = None

        return events

    def reset(self) -> None:
        self._buffer.clear()
        self._postures.clear()
        self._in_movement = False
        self._movement_start_idx = 0
        self._below_threshold_start = None
        self._total_idx = 0

    # ──────────────────────────────────────────────────────────────────────
    # Event extraction
    # ──────────────────────────────────────────────────────────────────────
    def _extract_event(
        self,
        start_idx: int,
        end_idx: int,
    ) -> Optional[MovementEventData]:
        """Extract features from the movement segment and classify."""
        if start_idx >= len(self._buffer) or end_idx >= len(self._buffer):
            return None

        segment = self._buffer[start_idx : end_idx + 1]
        posture_segment = self._postures[start_idx : end_idx + 1]

        if len(segment) < 2:
            return None

        duration_ms = segment[-1].timestamp_ms - segment[0].timestamp_ms
        if duration_ms < settings.MOVEMENT_MIN_DURATION_MS:
            return None

        # ── Feature extraction ────────────────────────────────────────────
        features = self._extract_features(segment)

        # ── Posture at start and end ─────────────────────────────────────
        start_posture = posture_segment[0].posture if posture_segment else Posture.UNKNOWN
        # For end posture, look at the buffer AFTER movement ended
        end_posture = posture_segment[-1].posture if posture_segment else Posture.UNKNOWN

        # Also check posture a bit further out if buffer allows
        post_end = min(end_idx + 10, len(self._postures) - 1)
        if post_end > end_idx and post_end < len(self._postures):
            end_posture = self._postures[post_end].posture

        # ── Classification ───────────────────────────────────────────────
        event_type, confidence, details = self._classify(
            start_posture, end_posture, features, segment,
        )

        # ── Post-movement stability ─────────────────────────────────────
        stability = self._compute_stability(end_idx)

        return MovementEventData(
            event_type=event_type,
            start_time_ms=segment[0].timestamp_ms,
            end_time_ms=segment[-1].timestamp_ms,
            duration_ms=duration_ms,
            start_posture=start_posture.value if isinstance(start_posture, Posture) else str(start_posture),
            end_posture=end_posture.value if isinstance(end_posture, Posture) else str(end_posture),
            peak_angular_velocity=features["peak_gyro"],
            avg_angular_velocity=features["avg_gyro"],
            movement_smoothness=features["jerk_metric"],
            stability_after=stability,
            confidence=confidence,
            classification_details=details,
            sensor_data_start_idx=self._total_idx - (end_idx - start_idx + 1),
            sensor_data_end_idx=self._total_idx - 1,
        )

    @staticmethod
    def _extract_features(segment: List[ProcessedSample]) -> Dict[str, Any]:
        """Extract kinematic features from a movement segment."""
        gyro_mags = [s.gyro_magnitude for s in segment]
        accel_mags = [s.accel_magnitude for s in segment]

        peak_gyro = max(gyro_mags) if gyro_mags else 0.0
        avg_gyro = float(np.mean(gyro_mags)) if gyro_mags else 0.0

        # Dominant gyro axis (which axis had the largest total rotation)
        gx_total = sum(abs(s.gx) for s in segment)
        gy_total = sum(abs(s.gy) for s in segment)
        gz_total = sum(abs(s.gz) for s in segment)
        axis_totals = {"gx": gx_total, "gy": gy_total, "gz": gz_total}
        dominant_axis = max(axis_totals, key=axis_totals.get)  # type: ignore[arg-type]

        # Roll/pitch changes
        roll_change = segment[-1].roll - segment[0].roll if len(segment) >= 2 else 0.0
        pitch_change = segment[-1].pitch - segment[0].pitch if len(segment) >= 2 else 0.0

        # Jerk metric (smoothness) — derivative of acceleration magnitude
        jerk_metric = 0.0
        if len(accel_mags) >= 3:
            accel_arr = np.array(accel_mags)
            dt_ms = max(1, (segment[-1].timestamp_ms - segment[0].timestamp_ms)) / len(segment)
            dt_s = dt_ms / 1000.0
            if dt_s > 0:
                jerk = np.diff(accel_arr) / dt_s
                jerk_metric = float(np.sqrt(np.mean(jerk ** 2)))

        return {
            "peak_gyro": peak_gyro,
            "avg_gyro": avg_gyro,
            "dominant_axis": dominant_axis,
            "gx_total": gx_total,
            "gy_total": gy_total,
            "gz_total": gz_total,
            "roll_change": roll_change,
            "pitch_change": pitch_change,
            "jerk_metric": jerk_metric,
        }

    @staticmethod
    def _classify(
        start_posture: Posture,
        end_posture: Posture,
        features: Dict[str, Any],
        segment: List[ProcessedSample],
    ) -> tuple[str, float, Dict[str, Any]]:
        """Rule-based movement classification.

        Returns (event_type, confidence, explanation_dict).
        """
        sp = start_posture
        ep = end_posture
        dom = features["dominant_axis"]
        roll_ch = features["roll_change"]
        pitch_ch = features["pitch_change"]
        details: Dict[str, Any] = {
            "start_posture": sp.value if isinstance(sp, Posture) else str(sp),
            "end_posture": ep.value if isinstance(ep, Posture) else str(ep),
            "dominant_axis": dom,
            "roll_change_deg": round(roll_ch, 1),
            "pitch_change_deg": round(pitch_ch, 1),
        }

        # Check if posture actually changed
        posture_changed = sp != ep and sp != Posture.UNKNOWN and ep != Posture.UNKNOWN

        if not posture_changed:
            # Minor adjustment — movement detected but no posture change
            details["reason"] = "No posture change detected"
            return "minor_adjustment", 0.6, details

        # Left roll
        if ep == Posture.LEFT_LATERAL and sp in (Posture.SUPINE, Posture.RIGHT_LATERAL):
            details["reason"] = f"Transition from {sp.value} to left_lateral, roll dominant"
            return "left_roll", 0.85, details

        # Right roll
        if ep == Posture.RIGHT_LATERAL and sp in (Posture.SUPINE, Posture.LEFT_LATERAL):
            details["reason"] = f"Transition from {sp.value} to right_lateral, roll dominant"
            return "right_roll", 0.85, details

        # Supine to sitting
        if sp == Posture.SUPINE and ep == Posture.SITTING:
            details["reason"] = "Supine to sitting, pitch change significant"
            return "supine_to_sitting", 0.80, details

        # Sitting to supine
        if sp == Posture.SITTING and ep == Posture.SUPINE:
            details["reason"] = "Sitting to supine, pitch change significant"
            return "sitting_to_supine", 0.80, details

        # Generic posture transition
        details["reason"] = f"Posture changed from {sp.value} to {ep.value}"
        return "posture_transition", 0.65, details

    def _compute_stability(self, end_idx: int) -> float:
        """Compute post-movement stability: variance of accel in 2s window after movement."""
        # 2s at 50Hz = 100 samples
        stability_window = min(100, settings.SAMPLING_RATE * 2)
        start = end_idx + 1
        end = min(start + stability_window, len(self._buffer))

        if end <= start:
            return 0.0

        mags = [s.accel_magnitude for s in self._buffer[start:end]]
        if len(mags) < 3:
            return 0.0

        return float(np.var(mags))
