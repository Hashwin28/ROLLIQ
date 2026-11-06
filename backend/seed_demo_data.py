"""
ROLLIQ Demonstration Data Seeder.
Populates an initial user profile with 4 completed monitoring sessions,
establishing an individual movement baseline and realistic mobility analytics.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from database import async_session_factory, init_db
from models import User, Device, MonitoringSession, MovementEvent, SessionMetrics, PersonalBaseline, Alert
from services.baseline_engine import BaselineEngine
from services.rmi_calculator import RMICalculator


async def seed():
    await init_db()
    async with async_session_factory() as db:
        # Check if already seeded
        from sqlalchemy import select
        res = await db.execute(select(User).where(User.display_name == "Eleanor Vance (Demo)"))
        if res.scalar_one_or_none():
            print("Demo data already present.")
            return

        print("Seeding ROLLIQ demo dataset...")

        # 1. Primary demo user
        user = User(
            id="demo-user-eleanor",
            display_name="Eleanor Vance (Demo)",
            age_group="elderly",
            created_at=datetime.now(timezone.utc) - timedelta(days=14),
        )
        db.add(user)

        # 2. ESP32 Hardware device
        device = Device(
            id="ESP32-TORSO-NODE-01",
            name="ESP32 NodeMCU (30-pin) + MPU6050",
            firmware_version="v1.0.4-firmware",
            is_active=True,
            calibration_data={
                "accel_offsets": {"x": 0.012, "y": -0.008, "z": 0.045},
                "gyro_offsets": {"x": -0.42, "y": 0.18, "z": 0.05},
                "last_calibrated": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            },
            last_seen=datetime.now(timezone.utc),
        )
        db.add(device)

        # 3. Four historical sessions over the past two weeks showing recovery progression
        session_configs = [
            {
                "day_offset": 12,
                "durations": [3800, 4100, 4200, 3900],
                "velocities": [38.0, 35.0, 36.0, 39.0],
                "smoothnesses": [4.2, 4.8, 4.5, 4.1],
                "stabilities": [0.08, 0.09, 0.085, 0.078],
                "left": 2, "right": 1, "sit": 1,
            },
            {
                "day_offset": 8,
                "durations": [3400, 3600, 3300, 3500],
                "velocities": [44.0, 42.0, 46.0, 43.0],
                "smoothnesses": [3.6, 3.8, 3.4, 3.5],
                "stabilities": [0.065, 0.07, 0.06, 0.062],
                "left": 2, "right": 2, "sit": 1,
            },
            {
                "day_offset": 4,
                "durations": [2900, 3100, 2800, 3000, 2950],
                "velocities": [52.0, 50.0, 55.0, 51.0, 53.0],
                "smoothnesses": [2.6, 2.8, 2.5, 2.7, 2.6],
                "stabilities": [0.045, 0.05, 0.042, 0.048, 0.044],
                "left": 3, "right": 2, "sit": 1,
            },
            {
                "day_offset": 1,
                "durations": [2500, 2600, 2400, 2550, 2450],
                "velocities": [62.0, 58.0, 64.0, 60.0, 61.0],
                "smoothnesses": [1.8, 2.0, 1.7, 1.9, 1.8],
                "stabilities": [0.032, 0.035, 0.03, 0.033, 0.031],
                "left": 3, "right": 3, "sit": 2,
            },
        ]

        rmi_calc = RMICalculator()
        all_metrics = []

        for i, sc in enumerate(session_configs):
            s_time = datetime.now(timezone.utc) - timedelta(days=sc["day_offset"], hours=4)
            e_time = s_time + timedelta(minutes=45)

            session = MonitoringSession(
                id=f"demo-session-{i+1}",
                user_id=user.id,
                device_id=device.id,
                is_simulation=False,
                status="completed",
                started_at=s_time,
                ended_at=e_time,
                notes=f"Recovery Phase session #{i+1}",
                total_movements=len(sc["durations"]),
            )
            db.add(session)

            # Generate mock movement events for this session
            movements = []
            for m_idx, (dur, vel, sm, stab) in enumerate(
                zip(sc["durations"], sc["velocities"], sc["smoothnesses"], sc["stabilities"])
            ):
                event_type = "left_roll" if m_idx % 2 == 0 else "right_roll"
                me = MovementEvent(
                    id=f"demo-mov-{i+1}-{m_idx+1}",
                    session_id=session.id,
                    event_type=event_type,
                    start_time_ms=m_idx * 15000 + 2000,
                    end_time_ms=m_idx * 15000 + 2000 + dur,
                    duration_ms=dur,
                    start_posture="supine" if event_type == "left_roll" else "left_lateral",
                    end_posture="left_lateral" if event_type == "left_roll" else "supine",
                    peak_angular_velocity=vel,
                    avg_angular_velocity=vel * 0.6,
                    movement_smoothness=sm,
                    stability_after=stab,
                    confidence=0.94,
                    classification_details={
                        "primary_axis": "roll (X/Y)",
                        "peak_velocity": f"{vel}°/s",
                        "jerk_score": sm,
                    },
                )
                db.add(me)
                movements.append(me)

            # Calculate RMI
            rmi_res = rmi_calc.calculate(movements)
            session.rmi_score = rmi_res["score"]
            session.avg_transition_duration = sum(sc["durations"]) / len(sc["durations"])

            # Session metrics record
            import numpy as np
            sm_rec = SessionMetrics(
                session_id=session.id,
                total_movements=len(movements),
                total_left_rolls=sc["left"],
                total_right_rolls=sc["right"],
                total_sit_transitions=sc["sit"],
                avg_transition_duration_ms=float(np.mean(sc["durations"])),
                median_transition_duration_ms=float(np.median(sc["durations"])),
                avg_angular_velocity=float(np.mean(sc["velocities"])),
                avg_smoothness=float(np.mean(sc["smoothnesses"])),
                avg_stability=float(np.mean(sc["stabilities"])),
                movement_symmetry=round(sc["left"] / max(1, sc["right"]), 2),
                rmi_score=rmi_res["score"],
                rmi_components=rmi_res["components"],
                data_completeness=1.0,
                session_duration_ms=45 * 60 * 1000,
            )
            db.add(sm_rec)
            all_metrics.append(sm_rec)

        # 4. Generate user's Personal Baseline from the 4 sessions
        base_dict = BaselineEngine.compute_baseline(all_metrics)
        baseline = PersonalBaseline(
            user_id=user.id,
            sessions_used=base_dict["sessions_used"],
            is_ready=base_dict["is_ready"],
            avg_transition_duration=base_dict["avg_transition_duration"],
            std_transition_duration=base_dict["std_transition_duration"],
            avg_angular_velocity=base_dict["avg_angular_velocity"],
            std_angular_velocity=base_dict["std_angular_velocity"],
            avg_smoothness=base_dict["avg_smoothness"],
            std_smoothness=base_dict["std_smoothness"],
            avg_stability=base_dict["avg_stability"],
            std_stability=base_dict["std_stability"],
            avg_rmi=base_dict["avg_rmi"],
            std_rmi=base_dict["std_rmi"],
            baseline_data=base_dict["baseline_data"],
            last_updated=datetime.now(timezone.utc),
        )
        db.add(baseline)

        # 5. Sample alert for demonstration
        demo_alert = Alert(
            user_id=user.id,
            session_id="demo-session-4",
            alert_type="prolonged_posture",
            severity="attention",
            title="Prolonged Right Lateral Posture",
            message="Subject remained in right lateral posture for 28 consecutive minutes during rest interval.",
            measurement_value=28.0,
            threshold_value=25.0,
            is_read=False,
            created_at=datetime.now(timezone.utc) - timedelta(hours=3),
        )
        db.add(demo_alert)

        await db.commit()
        print("Demo seed complete! User 'Eleanor Vance (Demo)' initialized with 4 historical sessions and established baseline.")


if __name__ == "__main__":
    asyncio.run(seed())
