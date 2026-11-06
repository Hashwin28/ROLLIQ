"""
ROLLIQ Realistic Sensor Simulation Engine.
Generates physically plausible 6-axis IMU data across 10 clinical/ergonomic scenarios.
Passes through the exact same processing and classification pipeline as physical hardware.
"""
import asyncio
import math
import random
import time
from typing import Dict, List, Optional, Callable, Awaitable, Any

from schemas import SensorBatch, SensorSample


class SimulationEngine:
    """
    Simulates ESP32 + MPU6050 output at 50 Hz.
    Generates realistic gravity vectors, rotational velocity bell curves,
    sensor noise, and anatomical movement kinematics.
    """

    SCENARIOS = {
        "normal_rolling": {
            "name": "Normal Rolling",
            "description": "Natural, periodic left and right turning with normal transition duration (2-3s) and rest periods.",
            "postures": ["supine", "left_lateral", "supine", "right_lateral"],
            "transition_time_s": 2.5,
            "dwell_time_s": 8.0,
        },
        "left_right_turning": {
            "name": "Left-to-Right Turning",
            "description": "Continuous alternating side-to-side turns evaluating bilateral symmetry and turning smoothness.",
            "postures": ["left_lateral", "right_lateral", "left_lateral", "right_lateral"],
            "transition_time_s": 3.0,
            "dwell_time_s": 6.0,
        },
        "supine_to_sitting": {
            "name": "Supine-to-Sitting Transition",
            "description": "Rise from lying down to upright sitting posture with abdominal flexion and trunk elevation.",
            "postures": ["supine", "sitting", "supine", "sitting"],
            "transition_time_s": 3.2,
            "dwell_time_s": 10.0,
        },
        "sitting_to_supine": {
            "name": "Sitting-to-Supine Transition",
            "description": "Controlled descent from upright sitting back to flat supine bed rest.",
            "postures": ["sitting", "supine", "sitting", "supine"],
            "transition_time_s": 2.8,
            "dwell_time_s": 9.0,
        },
        "minor_movements": {
            "name": "Repeated Minor Movements",
            "description": "Restless micro-adjustments, fidgeting, and limb shifting without full postural orientation changes.",
            "postures": ["supine", "supine", "supine"],
            "transition_time_s": 1.0,
            "dwell_time_s": 4.0,
            "is_minor": True,
        },
        "prolonged_immobility": {
            "name": "Prolonged Immobility",
            "description": "Extended static posture with minimal physiological micro-vibration, testing static posture alerting.",
            "postures": ["supine"],
            "transition_time_s": 0.0,
            "dwell_time_s": 60.0,
        },
        "irregular_movement": {
            "name": "Irregular Movement",
            "description": "Variable transition durations, erratic angular velocity peaks, and variable recovery times.",
            "postures": ["supine", "left_lateral", "sitting", "right_lateral", "supine"],
            "transition_time_s": 4.5,
            "dwell_time_s": 5.0,
            "is_irregular": True,
        },
        "sensor_disconnect": {
            "name": "Sensor Disconnection",
            "description": "Simulates intermittent Wi-Fi or hardware dropouts with telemetry packet stalls.",
            "postures": ["supine", "left_lateral"],
            "transition_time_s": 2.5,
            "dwell_time_s": 5.0,
            "disconnect_at_s": 12.0,
            "reconnect_at_s": 22.0,
        },
        "noisy_signals": {
            "name": "Noisy Sensor Signals",
            "description": "Elevated accelerometer and gyroscope noise (low SNR), testing filter robustness and quality metrics.",
            "postures": ["supine", "right_lateral", "supine"],
            "transition_time_s": 2.5,
            "dwell_time_s": 7.0,
            "noise_factor": 4.5,
        },
        "incomplete_transition": {
            "name": "Incomplete Movement Transition",
            "description": "An attempted roll that stalls midway due to weakness or fatigue, returning back to origin posture.",
            "postures": ["supine", "incomplete_roll", "supine"],
            "transition_time_s": 3.0,
            "dwell_time_s": 6.0,
        },
    }

    # Reference orientation vectors (ax, ay, az in g) for torso placement
    POSTURE_VECTORS = {
        "supine": (0.02, 0.01, 0.98),         # Torso flat, gravity along +Z
        "prone": (0.01, -0.02, -0.98),        # Lying front, gravity along -Z
        "left_lateral": (0.02, 0.97, 0.08),   # Left shoulder down, gravity along +Y
        "right_lateral": (-0.01, -0.97, 0.07),# Right shoulder down, gravity along -Y
        "sitting": (0.88, 0.02, 0.38),        # Torso inclined forward/upright, gravity along +X
        "incomplete_roll": (0.05, 0.52, 0.75),# Stalled at ~35 degrees roll
    }

    def __init__(self, callback: Optional[Callable[[SensorBatch], Awaitable[None]]] = None):
        self.callback = callback
        self.is_running = False
        self.is_paused = False
        self.current_scenario_key = "normal_rolling"
        self.current_session_id: Optional[str] = None
        self.speed = 1.0
        self._task: Optional[asyncio.Task] = None
        self._seq = 0
        self.sample_rate = 50.0  # Hz

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": k,
                "name": v["name"],
                "description": v["description"],
            }
            for k, v in self.SCENARIOS.items()
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_scenario": self.current_scenario_key,
            "scenario_name": self.SCENARIOS.get(self.current_scenario_key, {}).get("name", "Unknown"),
            "session_id": self.current_session_id,
            "speed": self.speed,
            "packets_generated": self._seq,
        }

    async def start(self, session_id: str, scenario: str = "normal_rolling", speed: float = 1.0) -> None:
        """Start the simulation loop."""
        if self.is_running:
            await self.stop()

        if scenario not in self.SCENARIOS:
            scenario = "normal_rolling"

        self.current_session_id = session_id
        self.current_scenario_key = scenario
        self.speed = max(0.2, min(5.0, speed))
        self.is_running = True
        self.is_paused = False
        self._seq = 0

        self._task = asyncio.create_task(self._simulation_loop())

    async def pause(self) -> None:
        self.is_paused = True

    async def resume(self) -> None:
        self.is_paused = False

    async def stop(self) -> None:
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.2, min(5.0, speed))

    def set_scenario(self, scenario: str) -> bool:
        if scenario in self.SCENARIOS:
            self.current_scenario_key = scenario
            return True
        return False

    async def _simulation_loop(self) -> None:
        """Core asynchronous generator producing 50 Hz data in batches."""
        cfg = self.SCENARIOS[self.current_scenario_key]
        postures = cfg["postures"]
        posture_idx = 0
        in_transition = False
        transition_progress = 0.0
        dwell_timer = 0.0

        current_vec = list(self.POSTURE_VECTORS[postures[0]])
        target_vec = list(self.POSTURE_VECTORS[postures[0]])

        batch_size = 5  # Emit batches every 100ms (5 samples at 50Hz)
        dt = 1.0 / self.sample_rate
        sim_time_sec = 0.0

        try:
            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(0.1)
                    continue

                batch_points: List[SensorSample] = []

                for _ in range(batch_size):
                    step_dt = dt * self.speed
                    sim_time_sec += step_dt
                    cfg = self.SCENARIOS[self.current_scenario_key]
                    is_noise_scenario = "noise_factor" in cfg
                    noise_factor = cfg.get("noise_factor", 1.0)

                    # Check for sensor disconnect scenario
                    if "disconnect_at_s" in cfg:
                        if cfg["disconnect_at_s"] <= sim_time_sec <= cfg["reconnect_at_s"]:
                            # Sensor disconnected: simulate dropout / no packets
                            continue

                    # State machine for posture dwell vs transition
                    if not in_transition:
                        dwell_timer += step_dt
                        if dwell_timer >= cfg.get("dwell_time_s", 6.0):
                            # Start transition to next posture
                            in_transition = True
                            transition_progress = 0.0
                            dwell_timer = 0.0
                            next_idx = (posture_idx + 1) % len(postures)
                            target_vec = list(self.POSTURE_VECTORS[postures[next_idx]])
                            posture_idx = next_idx

                        # In dwell: minimal movement, baseline sensor drift and noise
                        ax = current_vec[0] + random.gauss(0, 0.015 * noise_factor)
                        ay = current_vec[1] + random.gauss(0, 0.015 * noise_factor)
                        az = current_vec[2] + random.gauss(0, 0.015 * noise_factor)
                        gx = random.gauss(0, 0.6 * noise_factor)
                        gy = random.gauss(0, 0.6 * noise_factor)
                        gz = random.gauss(0, 0.6 * noise_factor)

                        if cfg.get("is_minor", False) and random.random() < 0.08:
                            # Restless micro-adjustment
                            ay += random.choice([-0.12, 0.12])
                            gy += random.choice([-15.0, 15.0])
                    else:
                        # In active transition
                        trans_dur = cfg.get("transition_time_s", 2.5)
                        transition_progress += step_dt / max(0.5, trans_dur)

                        if transition_progress >= 1.0:
                            # Transition finished
                            in_transition = False
                            current_vec = target_vec.copy()
                            transition_progress = 1.0

                        # Smooth sigmoidal interpolation of gravity vector
                        s = 0.5 - 0.5 * math.cos(math.pi * min(1.0, transition_progress))
                        ax_interp = current_vec[0] + (target_vec[0] - current_vec[0]) * s
                        ay_interp = current_vec[1] + (target_vec[1] - current_vec[1]) * s
                        az_interp = current_vec[2] + (target_vec[2] - current_vec[2]) * s

                        # Bell-curve angular velocity profile during movement
                        # Peak velocity proportional to posture angular difference
                        bell = math.sin(math.pi * min(1.0, transition_progress))
                        peak_vel = 70.0 + random.uniform(-10.0, 15.0)
                        if cfg.get("is_irregular", False):
                            peak_vel *= random.uniform(0.6, 1.8)

                        # Determine primary axis of rotation
                        diff_y = target_vec[1] - current_vec[1]
                        diff_x = target_vec[0] - current_vec[0]

                        # Roll rotation shows up mainly on X/Z gyro axes depending on mount
                        gx = bell * peak_vel * (1.0 if diff_y > 0 else -1.0) + random.gauss(0, 2.0 * noise_factor)
                        gy = bell * peak_vel * 0.7 * (1.0 if diff_x > 0 else -0.3) + random.gauss(0, 2.0 * noise_factor)
                        gz = bell * (peak_vel * 0.4) + random.gauss(0, 1.5 * noise_factor)

                        ax = ax_interp + random.gauss(0, 0.03 * noise_factor)
                        ay = ay_interp + random.gauss(0, 0.03 * noise_factor)
                        az = az_interp + random.gauss(0, 0.03 * noise_factor)

                    # Compute estimated roll & pitch in degrees
                    norm_g = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
                    roll_deg = math.degrees(math.atan2(ay, az))
                    pitch_deg = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

                    # Assess signal quality (lower if excessive noise)
                    sig_q = max(0.1, min(1.0, 1.0 - (noise_factor - 1.0) * 0.2))

                    self._seq += 1
                    batch_points.append(
                        SensorSample(
                            timestamp_ms=int(sim_time_sec * 1000),
                            ax=round(ax, 4),
                            ay=round(ay, 4),
                            az=round(az, 4),
                            gx=round(gx, 2),
                            gy=round(gy, 2),
                            gz=round(gz, 2),
                            packet_sequence=self._seq,
                        )
                    )

                if batch_points and self.callback:
                    batch = SensorBatch(
                        device_id="SIM-ROLLIQ-NODE",
                        session_id=self.current_session_id or "sim-session",
                        samples=batch_points,
                    )
                    try:
                        await self.callback(batch)
                    except Exception:
                        pass

                # Sleep to maintain ~50 Hz real-time output (batch_size / 50 = 0.1s)
                sleep_sec = (batch_size / self.sample_rate) / self.speed
                await asyncio.sleep(max(0.01, sleep_sec))

        except asyncio.CancelledError:
            pass
        finally:
            self.is_running = False
