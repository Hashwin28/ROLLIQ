"""
ROLLIQ Personalized Baseline Engine.
Computes and maintains individual movement baselines across monitoring sessions.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import numpy as np


class BaselineEngine:
    """
    Manages user-specific mobility baselines.
    Never compares individuals against universal one-size-fits-all metrics.
    Requires at least MIN_SESSIONS (default 3) to establish a confident baseline.
    """

    MIN_SESSIONS = 3
    MIN_MOVEMENTS_PER_SESSION = 2

    @classmethod
    def can_establish_baseline(cls, session_metrics_list: List[Any]) -> bool:
        """Check if enough quality sessions exist to establish a baseline."""
        valid_sessions = [
            m for m in session_metrics_list
            if getattr(m, "total_movements", 0) >= cls.MIN_MOVEMENTS_PER_SESSION
        ]
        return len(valid_sessions) >= cls.MIN_SESSIONS

    @classmethod
    def compute_baseline(cls, session_metrics_list: List[Any]) -> Dict[str, Any]:
        """
        Aggregate session metrics to produce baseline statistical profile.
        """
        valid_sessions = [
            m for m in session_metrics_list
            if getattr(m, "total_movements", 0) >= cls.MIN_MOVEMENTS_PER_SESSION
        ]

        sessions_used = len(valid_sessions)
        is_ready = sessions_used >= cls.MIN_SESSIONS

        if not valid_sessions:
            return {
                "sessions_used": 0,
                "is_ready": False,
                "avg_transition_duration": 0.0,
                "std_transition_duration": 0.0,
                "avg_angular_velocity": 0.0,
                "std_angular_velocity": 0.0,
                "avg_smoothness": 0.0,
                "std_smoothness": 0.0,
                "avg_stability": 0.0,
                "std_stability": 0.0,
                "avg_rmi": 0.0,
                "std_rmi": 0.0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "baseline_data": {
                    "message": "No sessions recorded yet. Complete 3 sessions with movement to establish baseline.",
                    "progress": 0.0,
                },
            }

        durations = [m.avg_transition_duration_ms for m in valid_sessions if m.avg_transition_duration_ms > 0]
        velocities = [m.avg_angular_velocity for m in valid_sessions if m.avg_angular_velocity > 0]
        smoothnesses = [m.avg_smoothness for m in valid_sessions if m.avg_smoothness > 0]
        stabilities = [m.avg_stability for m in valid_sessions if m.avg_stability > 0]
        rmis = [m.rmi_score for m in valid_sessions if m.rmi_score > 0]

        def _stats(arr: List[float], default_mean: float = 0.0):
            if not arr:
                return default_mean, 0.0
            return float(np.mean(arr)), float(np.std(arr))

        avg_dur, std_dur = _stats(durations, 2500.0)
        avg_vel, std_vel = _stats(velocities, 60.0)
        avg_sm, std_sm = _stats(smoothnesses, 2.0)
        avg_stab, std_stab = _stats(stabilities, 0.05)
        avg_rmi, std_rmi = _stats(rmis, 70.0)

        progress = min(1.0, sessions_used / cls.MIN_SESSIONS)

        return {
            "sessions_used": sessions_used,
            "is_ready": is_ready,
            "avg_transition_duration": round(avg_dur, 1),
            "std_transition_duration": round(max(std_dur, 100.0), 1),
            "avg_angular_velocity": round(avg_vel, 1),
            "std_angular_velocity": round(max(std_vel, 5.0), 1),
            "avg_smoothness": round(avg_sm, 2),
            "std_smoothness": round(max(std_sm, 0.2), 2),
            "avg_stability": round(avg_stab, 3),
            "std_stability": round(max(std_stab, 0.01), 3),
            "avg_rmi": round(avg_rmi, 1),
            "std_rmi": round(max(std_rmi, 3.0), 1),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "baseline_data": {
                "progress": round(progress, 2),
                "sessions_needed": max(0, cls.MIN_SESSIONS - sessions_used),
                "message": (
                    "Baseline established."
                    if is_ready
                    else f"Calibrating baseline: {sessions_used}/{cls.MIN_SESSIONS} sessions completed."
                ),
            },
        }

    @classmethod
    def compare_to_baseline(
        cls, session_metric: Any, baseline: Any
    ) -> Dict[str, Any]:
        """
        Compare a single session's metrics against the user's personal baseline.
        Computes z-scores and flags meaningful deviations (|z| > 1.5).
        """
        if not baseline or not getattr(baseline, "is_ready", False):
            return {
                "is_baseline_ready": False,
                "message": "Personal baseline has not reached minimum data requirement (3+ sessions).",
                "deviations": [],
                "overall_status": "calibrating",
            }

        deviations = []
        metrics_to_check = [
            {
                "name": "Transition Duration",
                "key": "avg_transition_duration_ms",
                "b_mean": baseline.avg_transition_duration,
                "b_std": baseline.std_transition_duration,
                "unit": "ms",
                "lower_is_better": True,
            },
            {
                "name": "Angular Velocity",
                "key": "avg_angular_velocity",
                "b_mean": baseline.avg_angular_velocity,
                "b_std": baseline.std_angular_velocity,
                "unit": "°/s",
                "lower_is_better": False,
            },
            {
                "name": "Movement Smoothness (Jerk)",
                "key": "avg_smoothness",
                "b_mean": baseline.avg_smoothness,
                "b_std": baseline.std_smoothness,
                "unit": "jerk",
                "lower_is_better": True,
            },
            {
                "name": "Postural Stability",
                "key": "avg_stability",
                "b_mean": baseline.avg_stability,
                "b_std": baseline.std_stability,
                "unit": "var",
                "lower_is_better": True,
            },
            {
                "name": "ROLLIQ Mobility Index",
                "key": "rmi_score",
                "b_mean": baseline.avg_rmi,
                "b_std": baseline.std_rmi,
                "unit": "pts",
                "lower_is_better": False,
            },
        ]

        significant_count = 0
        declines = 0

        for item in metrics_to_check:
            current_val = getattr(session_metric, item["key"], None)
            if current_val is None or current_val == 0.0:
                continue

            mean = item["b_mean"]
            std = max(item["b_std"], 1e-4)
            z_score = (current_val - mean) / std

            is_significant = abs(z_score) >= 1.5
            if is_significant:
                significant_count += 1

            # Determine direction
            if abs(z_score) < 0.5:
                direction = "nominal"
            elif z_score > 0:
                direction = "higher"
            else:
                direction = "lower"

            # Determine if this direction represents an improvement or decline
            if item["lower_is_better"]:
                is_improved = z_score < -0.5
                is_declined = z_score > 1.5
            else:
                is_improved = z_score > 0.5
                is_declined = z_score < -1.5

            if is_declined:
                declines += 1

            pct_change = round(((current_val - mean) / (mean + 1e-5)) * 100.0, 1)

            deviations.append({
                "metric_name": item["name"],
                "current_value": round(float(current_val), 2),
                "baseline_mean": round(float(mean), 2),
                "baseline_std": round(float(std), 2),
                "unit": item["unit"],
                "z_score": round(float(z_score), 2),
                "pct_change": pct_change,
                "direction": direction,
                "is_significant": is_significant,
                "is_improved": is_improved,
                "is_declined": is_declined,
            })

        if declines >= 2:
            overall_status = "notable_change_attention"
        elif significant_count > 0:
            overall_status = "variation_detected"
        else:
            overall_status = "consistent_with_baseline"

        return {
            "is_baseline_ready": True,
            "sessions_in_baseline": baseline.sessions_used,
            "deviations": deviations,
            "significant_deviations_count": significant_count,
            "overall_status": overall_status,
            "summary": (
                f"{significant_count} metric(s) deviate notably from baseline."
                if significant_count > 0
                else "Session performance is consistent with personal baseline profile."
            ),
        }
