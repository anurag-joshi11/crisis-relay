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


def test_draft_status_request_uses_live_blindspot_store():
    deps.runner = ScenarioRunner(store=InMemoryMongoService())
    deps.runner.reset()
    client = TestClient(app)

    blindspot_id = None
    for _ in range(30):
        status = client.post("/api/demo/next-event")
        assert status.status_code == 200
        blindspots = status.json()["blindspots"]
        if blindspots:
            blindspot_id = blindspots[0]["blindspot_id"]
            break

    assert blindspot_id is not None

    draft = client.post(f"/api/blindspots/{blindspot_id}/draft-status-request")
    assert draft.status_code == 200
    assert draft.json()["blindspot_id"] == blindspot_id
    assert draft.json()["approval_status"] == "PENDING"

    deps.runner = None
