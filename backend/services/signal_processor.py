"""
Signal Processor — low-pass filtering, orientation estimation,
quality assessment, spike detection.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from scipy.signal import butter, sosfilt

from config import settings


@dataclass
class ProcessedSample:
    """A single processed sensor sample."""
    timestamp_ms: int
    # filtered accelerometer (g)
    ax: float
    ay: float
    az: float
    # filtered gyroscope (deg/s)
    gx: float
    gy: float
    gz: float
    # orientation (degrees)
    roll: float
    pitch: float
    # derived
    accel_magnitude: float
    gyro_magnitude: float
    signal_quality: float
    packet_sequence: int = 0


class SignalProcessor:
    """Stateful processor that filters and enhances raw sensor streams."""

    def __init__(
        self,
        sampling_rate: int = settings.SAMPLING_RATE,
        cutoff_hz: float = settings.LOWPASS_CUTOFF_HZ,
        order: int = settings.LOWPASS_ORDER,
    ):
        self.sampling_rate = sampling_rate
        self.cutoff_hz = cutoff_hz
        self.order = order

        # Pre-compute Butterworth coefficients (second-order sections)
        nyquist = sampling_rate / 2.0
        normalised_cutoff = min(cutoff_hz / nyquist, 0.99)
        self._sos = butter(order, normalised_cutoff, btype="low", output="sos")

        # Running buffers for filter state
        self._accel_buf: List[Tuple[float, float, float]] = []
        self._gyro_buf: List[Tuple[float, float, float]] = []
        self._timestamps: List[int] = []

        # For quality tracking
        self._prev_timestamp: Optional[int] = None
        self._interval_history: List[float] = []

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────
    def process_batch(
        self,
        samples: List[dict],
    ) -> List[ProcessedSample]:
        """Process a batch of raw samples and return processed results.

        Each sample dict must contain: timestamp_ms, ax, ay, az, gx, gy, gz.
        """
        if not samples:
            return []

        # Sanitise inputs (replace NaN/Inf with 0)
        clean = [self._sanitise(s) for s in samples]

        # Separate channels
        ax_raw = np.array([s["ax"] for s in clean], dtype=np.float64)
        ay_raw = np.array([s["ay"] for s in clean], dtype=np.float64)
        az_raw = np.array([s["az"] for s in clean], dtype=np.float64)
        gx_raw = np.array([s["gx"] for s in clean], dtype=np.float64)
        gy_raw = np.array([s["gy"] for s in clean], dtype=np.float64)
        gz_raw = np.array([s["gz"] for s in clean], dtype=np.float64)

        # Apply low-pass filter (only when enough samples)
        if len(clean) >= self.order * 2 + 1:
            ax_f = sosfilt(self._sos, ax_raw)
            ay_f = sosfilt(self._sos, ay_raw)
            az_f = sosfilt(self._sos, az_raw)
            gx_f = sosfilt(self._sos, gx_raw)
            gy_f = sosfilt(self._sos, gy_raw)
            gz_f = sosfilt(self._sos, gz_raw)
        else:
            ax_f, ay_f, az_f = ax_raw, ay_raw, az_raw
            gx_f, gy_f, gz_f = gx_raw, gy_raw, gz_raw

        results: List[ProcessedSample] = []
        for i, s in enumerate(clean):
            ts = s["timestamp_ms"]

            ax_v = float(ax_f[i])
            ay_v = float(ay_f[i])
            az_v = float(az_f[i])
            gx_v = float(gx_f[i])
            gy_v = float(gy_f[i])
            gz_v = float(gz_f[i])

            roll, pitch = self._compute_orientation(ax_v, ay_v, az_v)
            accel_mag = math.sqrt(ax_v ** 2 + ay_v ** 2 + az_v ** 2)
            gyro_mag = math.sqrt(gx_v ** 2 + gy_v ** 2 + gz_v ** 2)
            quality = self._assess_quality(s, ax_raw, i, ts)

            results.append(ProcessedSample(
                timestamp_ms=ts,
                ax=ax_v, ay=ay_v, az=az_v,
                gx=gx_v, gy=gy_v, gz=gz_v,
                roll=roll, pitch=pitch,
                accel_magnitude=accel_mag,
                gyro_magnitude=gyro_mag,
                signal_quality=quality,
                packet_sequence=s.get("packet_sequence", 0),
            ))

        return results

    def detect_spikes(self, samples: List[ProcessedSample]) -> List[int]:
        """Return indices of samples with acceleration spikes."""
        indices: List[int] = []
        threshold = settings.SPIKE_THRESHOLD_G
        for i, s in enumerate(samples):
            if s.accel_magnitude > threshold:
                indices.append(i)
        return indices

    # ──────────────────────────────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _sanitise(s: dict) -> dict:
        """Replace NaN/Inf with 0."""
        out = dict(s)
        for key in ("ax", "ay", "az", "gx", "gy", "gz"):
            v = out.get(key, 0.0)
            if not math.isfinite(v):
                out[key] = 0.0
        return out

    @staticmethod
    def _compute_orientation(ax: float, ay: float, az: float) -> Tuple[float, float]:
        """Estimate roll and pitch from accelerometer (gravity decomposition).

        Roll  = atan2(ay, az)   — rotation about X axis
        Pitch = atan2(-ax, sqrt(ay² + az²))  — rotation about Y axis
        Returns degrees.
        """
        roll = math.degrees(math.atan2(ay, az))
        denom = math.sqrt(ay ** 2 + az ** 2)
        if denom < 1e-9:
            pitch = 90.0 if ax < 0 else -90.0
        else:
            pitch = math.degrees(math.atan2(-ax, denom))
        return roll, pitch

    def _assess_quality(
        self,
        raw_sample: dict,
        ax_raw: np.ndarray,
        idx: int,
        timestamp_ms: int,
    ) -> float:
        """Return signal quality 0-1 based on noise and timing."""
        quality = 1.0

        # Check timing consistency
        if self._prev_timestamp is not None:
            expected_interval = 1000.0 / self.sampling_rate
            actual_interval = timestamp_ms - self._prev_timestamp
            if actual_interval > 0:
                ratio = actual_interval / expected_interval
                if ratio > 2.0 or ratio < 0.5:
                    quality -= 0.3
                elif ratio > 1.5 or ratio < 0.7:
                    quality -= 0.1

        self._prev_timestamp = timestamp_ms

        # Check local noise (std-dev in small window)
        win = settings.NOISE_WINDOW_SIZE
        start = max(0, idx - win // 2)
        end = min(len(ax_raw), idx + win // 2 + 1)
        if end - start >= 3:
            local_std = float(np.std(ax_raw[start:end]))
            if local_std > 0.5:
                quality -= 0.2
            elif local_std > 0.3:
                quality -= 0.1

        return max(0.0, min(1.0, quality))
