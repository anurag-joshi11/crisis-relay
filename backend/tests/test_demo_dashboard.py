import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import deps
from backend.demo.scenario_runner import ScenarioRunner
from backend.main import app
from backend.schemas.gemini_schema import DraftStatusResponse
from backend.services.mongodb_service import InMemoryMongoService


class DemoDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        deps.runner = ScenarioRunner(store=InMemoryMongoService())
        deps.runner.reset()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        deps.runner = None

    def advance_to(self, report_id: str) -> dict:
        while True:
            response = self.client.post("/api/demo/next-event")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["reports"] and payload["reports"][-1]["report_id"] == report_id:
                return payload

    def test_timeline_includes_uncertain_resource_signal(self) -> None:
        self.advance_to("RPT-017")

        response = self.client.get("/api/operations/OP-EVAC-001/timeline")
        self.assertEqual(response.status_code, 200)
        timeline = response.json()

        self.assertTrue(
            any(
                event["kind"] == "assumption"
                and event["scenario_time"] == "10:36"
                and event["title"] == "UNCERTAIN ARRIVED"
                for event in timeline["events"]
            )
        )
        self.assertEqual(timeline["events"][-1]["kind"], "missing_confirmation")

    def test_timeline_includes_repeated_active_need_signal(self) -> None:
        self.advance_to("RPT-020")

        response = self.client.get("/api/operations/OP-WATER-001/timeline")
        self.assertEqual(response.status_code, 200)
        timeline = response.json()

        self.assertTrue(
            any(
                event["kind"] == "active_need"
                and event["scenario_time"] == "10:44"
                and event["title"] == "ACTIVE NEED REPEATED"
                for event in timeline["events"]
            )
        )
        self.assertEqual(timeline["events"][-1]["kind"], "missing_confirmation")

    @patch("backend.api.dispatches.GeminiIntelligenceService._build_client", return_value=None)
    @patch("backend.api.dispatches.GeminiIntelligenceService.draft_status")
    def test_pending_draft_request_refreshes_with_latest_operation_context(self, mock_draft_status, _mock_build_client) -> None:
        def fake_draft(request):
            return DraftStatusResponse(
                draft=f"{request.resource_id}:{request.current_state}:{request.missing_confirmation}",
                draft_source="FALLBACK_TEMPLATE",
            )

        mock_draft_status.side_effect = fake_draft

        status = self.advance_to("RPT-020")
        blindspot = next(item for item in status["blindspots"] if item["operation_id"] == "OP-WATER-001")

        first = self.client.post(f"/api/blindspots/{blindspot['blindspot_id']}/draft-status-request")
        self.assertEqual(first.status_code, 200)
        first_payload = first.json()
        self.assertIn("TANKER_2:DISPATCHED:ARRIVAL_OR_FULFILMENT", first_payload["ai_draft"])

        self.advance_to("RPT-026")

        second = self.client.post(f"/api/blindspots/{blindspot['blindspot_id']}/draft-status-request")
        self.assertEqual(second.status_code, 200)
        second_payload = second.json()
        self.assertEqual(second_payload["dispatch_id"], first_payload["dispatch_id"])
        self.assertIn("TANKER_2:HOLDING:FULFILMENT", second_payload["ai_draft"])
        self.assertEqual(second_payload["audio_status"], "NOT_GENERATED")


if __name__ == "__main__":
    unittest.main()
