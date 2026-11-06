"""
Tests for ROLLIQ Posture Detection & Movement Classification.
"""
import pytest
from services.posture_detector import PostureDetector, Posture
from services.movement_classifier import MovementClassifier
from services.signal_processor import ProcessedSample


def create_sample(ts: int, ax: float, ay: float, az: float, gx: float = 0.0, gy: float = 0.0, gz: float = 0.0):
    return ProcessedSample(
        timestamp_ms=ts,
        ax=ax, ay=ay, az=az,
        gx=gx, gy=gy, gz=gz,
        roll=0.0, pitch=0.0,
        accel_magnitude=1.0,
        gyro_magnitude=0.0,
        signal_quality=1.0,
        packet_sequence=0,
    )


def test_posture_detection_supine():
    detector = PostureDetector()
    # Feed supine samples over > 500ms hysteresis window
    for t in range(0, 700, 20):
        reading = detector.detect(create_sample(t, ax=0.02, ay=0.01, az=0.98))
    assert detector.current_posture == Posture.SUPINE
    assert reading.confirmed is True


def test_posture_detection_lateral():
    detector = PostureDetector()
    # Left lateral: ay > 0.7
    for t in range(0, 700, 20):
        detector.detect(create_sample(t, ax=0.02, ay=0.95, az=0.05))
    assert detector.current_posture == Posture.LEFT_LATERAL

    # Right lateral: ay < -0.7
    for t in range(700, 1400, 20):
        detector.detect(create_sample(t, ax=0.01, ay=-0.95, az=0.04))
    assert detector.current_posture == Posture.RIGHT_LATERAL


def test_posture_detection_sitting():
    detector = PostureDetector()
    for t in range(0, 700, 20):
        detector.detect(create_sample(t, ax=0.88, ay=0.02, az=0.35))
    assert detector.current_posture == Posture.SITTING


def test_posture_hysteresis_prevents_rapid_switching():
    detector = PostureDetector()
    # Establish supine first
    for t in range(0, 600, 20):
        detector.detect(create_sample(t, ax=0.0, ay=0.0, az=1.0))
    assert detector.current_posture == Posture.SUPINE

    # Short 100ms glitch towards left lateral should NOT flip confirmed posture
    for t in range(620, 700, 20):
        detector.detect(create_sample(t, ax=0.0, ay=0.9, az=0.1))
    assert detector.current_posture == Posture.SUPINE


def test_classifier_does_not_trigger_on_rest():
    classifier = MovementClassifier()
    detector = PostureDetector()
    samples = [create_sample(t, ax=0.0, ay=0.0, az=1.0, gx=0.2, gy=-0.1, gz=0.05) for t in range(0, 1000, 20)]
    postures = [detector.detect(s) for s in samples]

    events = classifier.feed(samples, postures)
    assert len(events) == 0
