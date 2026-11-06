"""
Tests for ROLLIQ Personalized Baseline Engine.
"""
from types import SimpleNamespace
import pytest
from services.baseline_engine import BaselineEngine


def create_mock_metrics(dur: float, vel: float, smooth: float, stab: float, rmi: float):
    return SimpleNamespace(
        total_movements=5,
        avg_transition_duration_ms=dur,
        avg_angular_velocity=vel,
        avg_smoothness=smooth,
        avg_stability=stab,
        rmi_score=rmi,
    )


def test_baseline_requires_minimum_sessions():
    # Only 2 sessions
    two_sessions = [
        create_mock_metrics(2400, 65, 1.8, 0.04, 82),
        create_mock_metrics(2500, 62, 1.9, 0.05, 80),
    ]
    b = BaselineEngine.compute_baseline(two_sessions)
    assert b["is_ready"] is False
    assert b["sessions_used"] == 2
    assert b["baseline_data"]["sessions_needed"] == 1


def test_baseline_ready_with_three_sessions():
    three_sessions = [
        create_mock_metrics(2400, 65, 1.8, 0.04, 82),
        create_mock_metrics(2500, 62, 1.9, 0.05, 80),
        create_mock_metrics(2450, 64, 1.7, 0.03, 83),
    ]
    b = BaselineEngine.compute_baseline(three_sessions)
    assert b["is_ready"] is True
    assert b["sessions_used"] == 3
    assert 2400 <= b["avg_transition_duration"] <= 2500


def test_baseline_deviation_detection():
    baseline_obj = SimpleNamespace(
        is_ready=True,
        sessions_used=5,
        avg_transition_duration=2200.0,
        std_transition_duration=200.0,
        avg_angular_velocity=70.0,
        std_angular_velocity=8.0,
        avg_smoothness=1.5,
        std_smoothness=0.3,
        avg_stability=0.03,
        std_stability=0.01,
        avg_rmi=84.0,
        std_rmi=4.0,
    )

    # Session with prolonged duration (4000ms vs 2200ms) and poor smoothness
    divergent_session = SimpleNamespace(
        avg_transition_duration_ms=4200.0,
        avg_angular_velocity=35.0,
        avg_smoothness=4.2,
        avg_stability=0.12,
        rmi_score=52.0,
    )

    comparison = BaselineEngine.compare_to_baseline(divergent_session, baseline_obj)
    assert comparison["is_baseline_ready"] is True
    assert comparison["significant_deviations_count"] >= 2
    assert comparison["overall_status"] == "notable_change_attention"
