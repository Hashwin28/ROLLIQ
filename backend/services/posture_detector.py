"""
Posture Detector — determine the subject's posture from processed sensor data.
Uses gravity-vector decomposition with hysteresis.
"""
from __future__ import annotations

import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

from config import settings
from services.signal_processor import ProcessedSample


class Posture(str, Enum):
    SUPINE = "supine"
    PRONE = "prone"
    LEFT_LATERAL = "left_lateral"
    RIGHT_LATERAL = "right_lateral"
    SITTING = "sitting"
    UNKNOWN = "unknown"


@dataclass
class PostureReading:
    """Result of posture detection for one instant."""
    posture: Posture
    confidence: float  # 0-1
    timestamp_ms: int
    confirmed: bool  # True if stable long enough (hysteresis)


class PostureDetector:
    """Stateful posture detector with hysteresis."""

    def __init__(self):
        self._current_posture: Posture = Posture.UNKNOWN
        self._confirmed_posture: Posture = Posture.UNKNOWN
        self._candidate_posture: Posture = Posture.UNKNOWN
        self._candidate_start_ms: int = 0
        self._hysteresis_ms: int = settings.POSTURE_HYSTERESIS_MS

    @property
    def current_posture(self) -> Posture:
        return self._confirmed_posture

    def detect(self, sample: ProcessedSample) -> PostureReading:
        """Detect posture from a single processed sample."""
        raw_posture, confidence = self._classify_instant(
            sample.ax, sample.ay, sample.az,
        )

        confirmed = False

        if raw_posture == self._candidate_posture:
            # Same candidate — check if held long enough
            elapsed = sample.timestamp_ms - self._candidate_start_ms
            if elapsed >= self._hysteresis_ms:
                self._confirmed_posture = raw_posture
                confirmed = True
        else:
            # New candidate
            self._candidate_posture = raw_posture
            self._candidate_start_ms = sample.timestamp_ms

        # If we already had a confirmed posture and raw still matches it
        if raw_posture == self._confirmed_posture:
            confirmed = True

        return PostureReading(
            posture=self._confirmed_posture if confirmed else self._confirmed_posture,
            confidence=confidence,
            timestamp_ms=sample.timestamp_ms,
            confirmed=confirmed,
        )

    def detect_batch(self, samples: List[ProcessedSample]) -> List[PostureReading]:
        """Detect posture for a batch of samples."""
        return [self.detect(s) for s in samples]

    def reset(self) -> None:
        self._current_posture = Posture.UNKNOWN
        self._confirmed_posture = Posture.UNKNOWN
        self._candidate_posture = Posture.UNKNOWN
        self._candidate_start_ms = 0

    # ──────────────────────────────────────────────────────────────────────
    # Internal classification
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _classify_instant(ax: float, ay: float, az: float) -> tuple[Posture, float]:
        """Classify posture from a single accelerometer reading.

        Returns (posture, confidence).
        Gravity is ~1g; the dominant axis indicates orientation.
        """
        mag = math.sqrt(ax ** 2 + ay ** 2 + az ** 2)
        if mag < 0.01:
            return Posture.UNKNOWN, 0.0

        # Normalise to unit gravity
        nax = ax / mag
        nay = ay / mag
        naz = az / mag

        candidates: list[tuple[Posture, float]] = []

        # Supine — back down → az positive and dominant
        if naz > settings.POSTURE_SUPINE_AZ_MIN:
            conf = min(1.0, (naz - settings.POSTURE_SUPINE_AZ_MIN) / 0.3 + 0.5)
            candidates.append((Posture.SUPINE, conf))

        # Prone — face down → az strongly negative
        if naz < settings.POSTURE_PRONE_AZ_MAX:
            conf = min(1.0, (abs(naz) - abs(settings.POSTURE_PRONE_AZ_MAX)) / 0.3 + 0.5)
            candidates.append((Posture.PRONE, conf))

        # Left lateral — left side down → ay positive
        if nay > settings.POSTURE_LEFT_AY_MIN:
            conf = min(1.0, (nay - settings.POSTURE_LEFT_AY_MIN) / 0.3 + 0.5)
            candidates.append((Posture.LEFT_LATERAL, conf))

        # Right lateral — right side down → ay negative
        if nay < settings.POSTURE_RIGHT_AY_MAX:
            conf = min(1.0, (abs(nay) - abs(settings.POSTURE_RIGHT_AY_MAX)) / 0.3 + 0.5)
            candidates.append((Posture.RIGHT_LATERAL, conf))

        # Sitting — upright → ax dominant positive, az moderate
        if nax > settings.POSTURE_SITTING_AX_MIN and abs(naz) < settings.POSTURE_SITTING_AZ_MAX:
            conf = min(1.0, (nax - settings.POSTURE_SITTING_AX_MIN) / 0.3 + 0.4)
            candidates.append((Posture.SITTING, conf))

        if not candidates:
            return Posture.UNKNOWN, 0.3

        # Pick highest confidence
        candidates.sort(key=lambda c: c[1], reverse=True)
        return candidates[0]
