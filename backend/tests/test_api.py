"""
Integration tests for ROLLIQ REST API Endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_user_and_session_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create user
        user_res = await client.post("/api/users", json={"display_name": "Dr. Sarah Lin", "age_group": "adult"})
        assert user_res.status_code == 201
        user_data = user_res.json()
        user_id = user_data["id"]
        assert user_data["display_name"] == "Dr. Sarah Lin"

        # 2. Create session
        session_res = await client.post("/api/sessions", json={
            "user_id": user_id,
            "is_simulation": True,
            "simulation_scenario": "normal_rolling",
            "notes": "Validation test run"
        })
        assert session_res.status_code == 201
        session_data = session_res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "active"

        # 3. Ingest sensor batch
        batch_payload = {
            "session_id": session_id,
            "samples": [
                {
                    "timestamp_ms": 100,
                    "ax": 0.02, "ay": 0.01, "az": 0.98,
                    "gx": 0.5, "gy": -0.2, "gz": 0.1,
                    "packet_sequence": 1
                },
                {
                    "timestamp_ms": 120,
                    "ax": 0.03, "ay": 0.02, "az": 0.97,
                    "gx": 0.6, "gy": -0.1, "gz": 0.0,
                    "packet_sequence": 2
                }
            ]
        }
        ingest_res = await client.post("/api/sensor/data", json=batch_payload)
        assert ingest_res.status_code == 200
        ack = ingest_res.json()
        assert ack["received"] == 2

        # 4. Complete session
        complete_res = await client.post(f"/api/sessions/{session_id}/complete")
        assert complete_res.status_code == 200
        final_data = complete_res.json()
        assert final_data["status"] == "completed"

        # 5. Check user baseline endpoint
        baseline_res = await client.get(f"/api/users/{user_id}/baseline")
        assert baseline_res.status_code == 200
