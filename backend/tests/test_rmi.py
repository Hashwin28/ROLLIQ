"""
Tests for ROLLIQ Mobility Index (RMI) Calculation.
"""
import pytest
from services.rmi_calculator import RMICalculator


def test_rmi_weights_sum_to_one():
    calc = RMICalculator()
    total_w = sum(calc.weights.values())
    assert pytest.approx(total_w, 0.001) == 1.0


def test_rmi_empty_movements():
    calc = RMICalculator()
    res = calc.calculate([])
    assert res["score"] == 0.0
    assert res["movement_count"] == 0
    assert res["completeness"] == 0.0


def test_rmi_healthy_movements():
    calc = RMICalculator()
    movements = [
        {
            "event_type": "left_roll",
            "duration_ms": 2300,
            "peak_angular_velocity": 75.0,
            "avg_angular_velocity": 45.0,
            "movement_smoothness": 1.5,
            "stability_after": 0.03,
            "confidence": 0.95,
        },
        {
            "event_type": "right_roll",
            "duration_ms": 2400,
            "peak_angular_velocity": 72.0,
            "avg_angular_velocity": 42.0,
            "movement_smoothness": 1.4,
            "stability_after": 0.02,
            "confidence": 0.94,
        },
        {
            "event_type": "supine_to_sitting",
            "duration_ms": 2800,
            "peak_angular_velocity": 65.0,
            "avg_angular_velocity": 38.0,
            "movement_smoothness": 1.8,
            "stability_after": 0.04,
            "confidence": 0.92,
        },
    ]
    res = calc.calculate(movements)
    assert 0.0 <= res["score"] <= 100.0
    # Healthy transitions should achieve high RMI score (> 75)
    assert res["score"] >= 75.0
    assert res["movement_count"] == 3
    assert all(k in res["components"] for k in ["duration", "smoothness", "velocity", "stability", "completion", "consistency"])


def test_rmi_handles_extreme_outliers():
    calc = RMICalculator()
    extreme_movements = [
        {
            "event_type": "unclassified",
            "duration_ms": 15000,
            "peak_angular_velocity": 350.0,
            "avg_angular_velocity": 210.0,
            "movement_smoothness": 45.0,
            "stability_after": 0.85,
            "confidence": 0.3,
        }
    ]
    res = calc.calculate(extreme_movements)
    assert 0.0 <= res["score"] <= 100.0
    # High jerk and excessive duration should produce lower score
    assert res["score"] < 45.0
