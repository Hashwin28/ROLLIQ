"""
ROLLIQ Alert Service.
Evaluates monitoring state and sensor signals to raise informative, non-alarmist notifications.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import time
import uuid


class AlertService:
    """
    Evaluates session conditions against engineering and mobility thresholds.
    Adheres strictly to the principle:
    'Do not present an experimental mobility deviation as a medical emergency.'
    """

    COOLDOWN_SECONDS = 30  # Cooldown between duplicate alerts

    def __init__(self):
        # Track last alert timestamps: key -> epoch_time
        self._last_alert_times: Dict[str, float] = {}

    def _can_fire(self, alert_key: str) -> bool:
        now = time.time()
        last = self._last_alert_times.get(alert_key, 0.0)
        if now - last >= self.COOLDOWN_SECONDS:
            self._last_alert_times[alert_key] = now
            return True
        return False

    def check_prolonged_posture(
        self,
        session_id: str,
        user_id: str,
        current_posture: str,
        posture_duration_sec: float,
        threshold_sec: float = 1800.0,  # 30 mins default, or lower for testing
    ) -> Optional[Dict[str, Any]]:
        """Triggered when a user stays in an unchanging posture for extended periods."""
        if current_posture.lower() in ("unknown", "transitional"):
            return None

        if posture_duration_sec >= threshold_sec:
            key = f"{session_id}:prolonged:{current_posture}"
            if self._can_fire(key):
                mins = int(posture_duration_sec // 60)
                return {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": user_id,
                    "alert_type": "prolonged_posture",
                    "severity": "attention",
                    "title": f"Prolonged {current_posture.replace('_', ' ').title()} Posture",
                    "message": (
                        f"The user has remained in the {current_posture.replace('_', ' ')} posture "
                        f"for {mins} minutes continuously. Consider encouraging a positional adjustment."
                    ),
                    "measurement_value": round(posture_duration_sec, 1),
                    "threshold_value": round(threshold_sec, 1),
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc),
                }
        return None

    def check_sensor_disconnect(
        self,
        session_id: str,
        user_id: str,
        last_packet_age_sec: float,
        threshold_sec: float = 10.0,
    ) -> Optional[Dict[str, Any]]:
        """Triggered when incoming telemetry packets stall during an active session."""
        if last_packet_age_sec >= threshold_sec:
            key = f"{session_id}:disconnect"
            if self._can_fire(key):
                return {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": user_id,
                    "alert_type": "sensor_disconnect",
                    "severity": "warning",
                    "title": "Sensor Stream Interrupted",
                    "message": (
                        f"No telemetry packets received for {int(last_packet_age_sec)} seconds. "
                        "Verify ESP32 power, MPU6050 wiring, and Wi-Fi connection."
                    ),
                    "measurement_value": round(last_packet_age_sec, 1),
                    "threshold_value": round(threshold_sec, 1),
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc),
                }
        return None

    def check_baseline_deviation(
        self,
        session_id: str,
        user_id: str,
        deviation_result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Triggered when multiple mobility metrics notably deviate from established baseline."""
        if not deviation_result.get("is_baseline_ready", False):
            return None

        significant_count = deviation_result.get("significant_deviations_count", 0)
        overall_status = deviation_result.get("overall_status", "")

        if significant_count >= 2 or overall_status == "notable_change_attention":
            key = f"{session_id}:baseline_dev"
            if self._can_fire(key):
                return {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": user_id,
                    "alert_type": "baseline_deviation",
                    "severity": "attention",
                    "title": "Baseline Mobility Shift Detected",
                    "message": (
                        f"{significant_count} movement metrics diverge significantly from the individual's "
                        "established mobility baseline. Review transition duration and movement smoothness."
                    ),
                    "measurement_value": float(significant_count),
                    "threshold_value": 2.0,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc),
                }
        return None

    def check_unusual_movement(
        self,
        session_id: str,
        user_id: str,
        movement_event: Any,
    ) -> Optional[Dict[str, Any]]:
        """Triggered when an individual movement event exhibits high jerk or sudden anomaly."""
        smoothness = getattr(movement_event, "movement_smoothness", 0.0)
        dur = getattr(movement_event, "duration_ms", 0)

        # Extreme jerk > 25 or extremely prolonged transition > 9s
        if smoothness > 25.0 or dur > 9000:
            key = f"{session_id}:unusual_mov:{getattr(movement_event, 'id', str(uuid.uuid4()))}"
            if self._can_fire(key):
                return {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": user_id,
                    "alert_type": "unusual_movement",
                    "severity": "info",
                    "title": "Atypical Transition Characteristics",
                    "message": (
                        f"Detected {getattr(movement_event, 'event_type', 'movement')} with "
                        f"duration {dur}ms and elevated jerk index ({smoothness:.1f})."
                    ),
                    "measurement_value": round(float(smoothness), 1),
                    "threshold_value": 25.0,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc),
                }
        return None
