from fastapi.testclient import TestClient

from backend.api import deps
from backend.demo.scenario_runner import ScenarioRunner
from backend.main import app
from backend.services.mongodb_service import InMemoryMongoService


def test_demo_and_core_routes():
    deps.runner = ScenarioRunner(store=InMemoryMongoService())
    client = TestClient(app)

    reset = client.post("/api/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["demo"]["event_index"] == 0

    next_event = client.post("/api/demo/next-event")
    assert next_event.status_code == 200
    assert next_event.json()["demo"]["event_index"] == 1

    operations = client.get("/api/operations")
    assert operations.status_code == 200
    assert len(operations.json()) == 3

    timeline = client.get("/api/operations/OP-WATER-001/timeline")
    assert timeline.status_code == 200
    assert timeline.json()["operation_id"] == "OP-WATER-001"

    status = client.get("/api/demo/status")
    assert status.status_code == 200
    assert set(status.json()) == {"scenario", "reports", "operations", "blindspots", "selected_timeline", "demo"}

    deps.runner = None
