"""
Tests for ROLLIQ Sensor Simulation Engine.
"""
import pytest
import asyncio
from services.simulation_engine import SimulationEngine


def test_simulation_scenario_catalog():
    engine = SimulationEngine()
    scenarios = engine.get_available_scenarios()
    assert len(scenarios) == 10
    keys = [s["key"] for s in scenarios]
    assert "normal_rolling" in keys
    assert "left_right_turning" in keys
    assert "supine_to_sitting" in keys
    assert "prolonged_immobility" in keys
    assert "sensor_disconnect" in keys
    assert "noisy_signals" in keys


@pytest.mark.asyncio
async def test_simulation_produces_valid_telemetry():
    received_batches = []

    async def mock_callback(batch):
        received_batches.append(batch)

    engine = SimulationEngine(callback=mock_callback)
    await engine.start(session_id="test-sim-session", scenario="normal_rolling", speed=3.0)

    # Let it generate a few batches
    await asyncio.sleep(0.4)
    await engine.stop()

    assert len(received_batches) > 0
    first_batch = received_batches[0]
    assert first_batch.session_id == "test-sim-session"
    assert len(first_batch.samples) > 0

    sample = first_batch.samples[0]
    assert -3.0 <= sample.ax <= 3.0
    assert -3.0 <= sample.ay <= 3.0
    assert -3.0 <= sample.az <= 3.0
    assert sample.timestamp_ms >= 0
