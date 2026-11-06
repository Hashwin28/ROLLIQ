"""
ROLLIQ Mobility Index (RMI) Calculator.
Experimental composite mobility metric (0-100) reflecting bed-mobility performance.
"""
from typing import Dict, List, Optional, Any
import numpy as np


class RMICalculator:
    """
    Computes the ROLLIQ Mobility Index (RMI) for a session's movements.
    Transparent, configurable scoring engine combining 6 interpretable components:
      1. Duration Score (20%): Transition duration vs physiologically typical bed mobility window (1.5s - 4.0s).
      2. Smoothness Score (20%): Quantified movement jerk; smoother deceleration/acceleration profiles score higher.
      3. Velocity Score (15%): Adequacy of angular velocity without excessive flailing or extreme slowness.
      4. Stability Score (15%): Posture stillness in the 2s post-transition window.
      5. Completion Score (15%): Ratio of completed purposeful movements to aborted/incomplete attempts.
      6. Consistency Score (15%): Repeatability/low coefficient of variation across movements of the same class.
    """

    DEFAULT_WEIGHTS = {
        "duration": 0.20,
        "smoothness": 0.20,
        "velocity": 0.15,
        "stability": 0.15,
        "completion": 0.15,
        "consistency": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        # Normalize weights to sum to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def calculate(self, movements: List[Any]) -> Dict[str, Any]:
        """
        Calculate RMI from a list of MovementEvent objects or dicts.
        Returns a dict with:
          - score: float (0.0 to 100.0)
          - components: dict of component scores (0-100)
          - weights: dict of component weights
          - completeness: float (0.0 to 1.0)
          - movement_count: int
          - explanation: str
        """
        if not movements:
            return {
                "score": 0.0,
                "components": {k: 0.0 for k in self.weights},
                "weights": self.weights,
                "completeness": 0.0,
                "movement_count": 0,
                "explanation": "No movement events recorded in this session. Score cannot be established.",
            }

        valid_movements = []
        for m in movements:
            if hasattr(m, "event_type"):
                valid_movements.append(m)
            elif isinstance(m, dict) and "event_type" in m:
                # Mock object-like access for dict
                class DictWrapper:
                    def __init__(self, d):
                        for k, v in d.items():
                            setattr(self, k, v)
                valid_movements.append(DictWrapper(m))

        count = len(valid_movements)
        if count == 0:
            return {
                "score": 0.0,
                "components": {k: 0.0 for k in self.weights},
                "weights": self.weights,
                "completeness": 0.0,
                "movement_count": 0,
                "explanation": "No valid movements detected.",
            }

        # 1. Duration Score: Target 1500ms to 4000ms for purposeful roll/transition
        durations = [getattr(m, "duration_ms", 2500) for m in valid_movements]
        median_dur = float(np.median(durations))
        if median_dur < 800:
            # Too abrupt / jerky adjustment
            dur_score = max(20.0, 100.0 - (800 - median_dur) * 0.1)
        elif median_dur <= 3500:
            # Optimal zone
            dur_score = 95.0 - (abs(median_dur - 2200) / 1300.0) * 15.0
        elif median_dur <= 8000:
            # Sluggish / struggling transition
            dur_score = max(30.0, 80.0 - ((median_dur - 3500) / 4500.0) * 50.0)
        else:
            dur_score = 25.0

        # 2. Smoothness Score: Jerk metric (typical values 0.5 - 15.0, lower is better)
        smoothnesses = [getattr(m, "movement_smoothness", 2.0) for m in valid_movements]
        avg_smoothness = float(np.mean(smoothnesses))
        # Map smoothness: 0.5 -> 98, 2.0 -> 85, 5.0 -> 60, 10.0+ -> 30
        smooth_score = max(10.0, min(100.0, 100.0 - avg_smoothness * 6.5))

        # 3. Velocity Score: Peak and average angular velocity (healthy roll ~45-120 deg/s)
        velocities = [getattr(m, "peak_angular_velocity", 60.0) for m in valid_movements]
        avg_vel = float(np.mean(velocities))
        if avg_vel < 15.0:
            vel_score = 35.0
        elif 30.0 <= avg_vel <= 140.0:
            vel_score = 90.0 - abs(avg_vel - 75.0) * 0.25
        elif avg_vel <= 200.0:
            vel_score = max(40.0, 75.0 - (avg_vel - 140.0) * 0.5)
        else:
            vel_score = 30.0

        # 4. Stability Score: Post-transition stillness in 2s window (lower variance is better)
        stabilities = [getattr(m, "stability_after", 0.05) for m in valid_movements]
        avg_stability = float(np.mean(stabilities))
        # avg_stability variance typically 0.005 to 0.5 g^2
        stab_score = max(15.0, min(100.0, 100.0 - avg_stability * 180.0))

        # 5. Completion Score: purposeful classified transitions vs incomplete/unclassified
        purposeful_types = {"left_roll", "right_roll", "supine_to_sitting", "sitting_to_supine", "posture_transition"}
        completed_count = sum(1 for m in valid_movements if getattr(m, "event_type", "") in purposeful_types)
        completion_ratio = completed_count / count
        comp_score = max(20.0, min(100.0, completion_ratio * 100.0))

        # 6. Consistency Score: variance across transitions
        if count >= 3:
            dur_cv = float(np.std(durations) / (np.mean(durations) + 1e-5))
            # Coefficient of variation typically 0.1 (very consistent) to 0.8+ (erratic)
            cons_score = max(20.0, min(100.0, 100.0 - (dur_cv * 90.0)))
        else:
            cons_score = 65.0  # neutral placeholder when too few samples to evaluate repeatability

        components = {
            "duration": round(float(dur_score), 1),
            "smoothness": round(float(smooth_score), 1),
            "velocity": round(float(vel_score), 1),
            "stability": round(float(stab_score), 1),
            "completion": round(float(comp_score), 1),
            "consistency": round(float(cons_score), 1),
        }

        # Final weighted sum
        final_score = sum(components[k] * self.weights[k] for k in self.weights)
        final_score = round(max(0.0, min(100.0, final_score)), 1)

        # Data completeness metric: Need at least 5 movements for high confidence
        completeness = round(min(1.0, count / 5.0), 2)

        explanation = (
            f"RMI {final_score}/100 computed across {count} movement(s). "
            f"Median duration: {median_dur:.0f}ms, Smoothness: {avg_smoothness:.2f}, "
            f"Peak velocity: {avg_vel:.1f}°/s. "
            f"Data completeness is {int(completeness * 100)}%."
        )

        return {
            "score": final_score,
            "components": components,
            "weights": self.weights,
            "completeness": completeness,
            "movement_count": count,
            "explanation": explanation,
        }
