from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError

from backend.schemas.gemini_schema import (
    DraftStatusRequest,
    ExtractRequest,
    ExtractionResult,
    ScenarioContext,
)
from backend.services.gemini_service import GeminiIntelligenceService, GeminiResponseValidationError


ROOT = Path(__file__).resolve().parents[2]


class FakeModels:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text=json.dumps(self.payloads.pop(0)), parsed=None)


class FakeGeminiClient:
    def __init__(self, *payloads: dict) -> None:
        self.models = FakeModels(list(payloads))


def extraction_payload(
    *,
    state_events=None,
    assumptions=None,
    claims=None,
    blockers=None,
    related_operation=None,
    need_still_active=False,
):
    return {
        "incident_type": "WILDFIRE",
        "severity": "CRITICAL",
        "location": "SECTOR_4",
        "state_events": state_events or [],
        "assumptions": assumptions or [],
        "claims": claims or [],
        "blockers": blockers or [],
        "related_operation": related_operation,
        "need_still_active": need_still_active,
        "transport_source": None,
    }


def state_event(entity_id: str, new_state: str, evidence: str, operation_id: str | None = None):
    return {
        "operation_id": operation_id,
        "entity_id": entity_id,
        "previous_state": None,
        "new_state": new_state,
        "evidence": evidence,
        "confidence": 0.99,
    }


def default_context() -> ScenarioContext:
    metadata = json.loads((ROOT / "dataset" / "scenario_metadata.json").read_text())
    return ScenarioContext.model_validate(
        {
            "operations": metadata["operations"],
            "resources": metadata["resources"],
            "state_machine": metadata["state_machine"],
        }
    )


class GeminiSchemaTests(unittest.TestCase):
    def test_contract_sample_validates_against_pydantic(self) -> None:
        sample = json.loads((ROOT / "contracts" / "extraction_result.json").read_text())
        result = ExtractionResult.model_validate(sample)
        self.assertEqual(result.state_events[0].entity_id, "TANKER_2")

    def test_unknown_contract_fields_are_rejected(self) -> None:
        sample = json.loads((ROOT / "contracts" / "extraction_result.json").read_text())
        sample["ground_truth"] = {"should_not": "appear"}
        with self.assertRaises(ValidationError):
            ExtractionResult.model_validate(sample)


class GeminiExtractionTests(unittest.TestCase):
    def extract_with_payload(self, raw_text: str, payload: dict) -> ExtractionResult:
        service = GeminiIntelligenceService(client=FakeGeminiClient(payload), model="test-model")
        return service.extract_report(
            ExtractRequest(raw_text=raw_text, scenario_context=default_context())
        )

    def test_assumption_does_not_advance_bus_to_arrived(self) -> None:
        result = self.extract_with_payload(
            "Bus seven should be at Alpha by now.",
            extraction_payload(
                assumptions=[
                    {
                        "text": "Bus seven should be at Alpha by now.",
                        "entity_id": "BUS_7",
                        "blocked_transition": "ARRIVED",
                        "reason": "Should language is an assumption, not arrival evidence.",
                    }
                ]
            ),
        )
        self.assertEqual(result.state_events, [])
        self.assertEqual(result.assumptions[0].entity_id, "BUS_7")
        self.assertEqual(result.assumptions[0].blocked_transition, "ARRIVED")

    def test_unlinked_residents_arriving_does_not_transition_bus(self) -> None:
        result = self.extract_with_payload(
            "Sector Four residents arriving at Alpha.",
            extraction_payload(
                claims=[
                    {
                        "text": "Sector Four residents arriving at Alpha.",
                        "entity_id": None,
                        "operation_id": "OP-EVAC-001",
                        "unresolved": True,
                        "reason": "Evacuees arriving does not prove Bus 7 arrived.",
                    }
                ]
            ),
        )
        self.assertEqual(result.state_events, [])
        self.assertTrue(result.claims[0].unresolved)

    def test_explicit_bus_arrival_extracts_arrived(self) -> None:
        result = self.extract_with_payload(
            "Bus seven just pulled into Alpha.",
            extraction_payload(
                state_events=[
                    state_event(
                        "BUS_7",
                        "ARRIVED",
                        "Bus seven just pulled into Alpha.",
                        "OP-EVAC-001",
                    )
                ]
            ),
        )
        self.assertEqual(result.state_events[0].entity_id, "BUS_7")
        self.assertEqual(result.state_events[0].new_state, "ARRIVED")

    def test_tanker_holding_extracts_blocker(self) -> None:
        result = self.extract_with_payload(
            "Tanker two holding south. Unable to enter due to visibility.",
            extraction_payload(
                state_events=[
                    state_event(
                        "TANKER_2",
                        "HOLDING",
                        "Tanker two holding south.",
                        "OP-WATER-001",
                    )
                ],
                blockers=[
                    {
                        "entity_id": "TANKER_2",
                        "operation_id": "OP-WATER-001",
                        "type": "VISIBILITY",
                        "evidence": "Unable to enter due to visibility.",
                        "confidence": 0.99,
                    }
                ],
            ),
        )
        self.assertEqual(result.state_events[0].new_state, "HOLDING")
        self.assertEqual(result.blockers[0].type, "VISIBILITY")

    def test_active_water_need_does_not_infer_failure_or_completion(self) -> None:
        result = self.extract_with_payload(
            "Water drop urgently required for Sector Four.",
            extraction_payload(
                related_operation="OP-WATER-001",
                need_still_active=True,
            ),
        )
        self.assertEqual(result.state_events, [])
        self.assertEqual(result.related_operation, "OP-WATER-001")
        self.assertTrue(result.need_still_active)

    def test_prompt_excludes_dataset_ground_truth(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(raw_text="Bus 7 assigned.", scenario_context=default_context())
        )
        prompt = client.models.calls[0]["contents"]
        self.assertNotIn("ground_truth", prompt)
        self.assertIn("Never infer ARRIVED", prompt)

    def test_invalid_gemini_json_fails_contract_validation(self) -> None:
        service = GeminiIntelligenceService(
            client=FakeGeminiClient({"state_events": "not-an-array"}),
            model="test-model",
        )
        with self.assertRaises(GeminiResponseValidationError):
            service.extract_report(ExtractRequest(raw_text="Bus 7 assigned."))


class DraftStatusTests(unittest.TestCase):
    def test_fallback_draft_is_under_25_words_and_labeled(self) -> None:
        service = GeminiIntelligenceService(client=None, model="test-model")
        result = service.draft_status(
            DraftStatusRequest(
                resource_id="TANKER_2",
                operation_id="OP-WATER-001",
                current_state="DISPATCHED",
                missing_confirmation="ARRIVED",
                active_need="water drop",
                location="SECTOR_4",
            )
        )
        self.assertLessEqual(len(result.draft.split()), 25)
        self.assertEqual(result.draft_source, "FALLBACK_TEMPLATE")
        self.assertNotIn("dispatch", result.draft.lower())

    def test_gemini_draft_is_labeled_gemini(self) -> None:
        service = GeminiIntelligenceService(
            client=FakeGeminiClient({"draft": "Tanker Two, confirm status near Sector Four."}),
            model="test-model",
        )
        result = service.draft_status(
            DraftStatusRequest(
                resource_id="TANKER_2",
                current_state="DISPATCHED",
                missing_confirmation="ARRIVED",
                location="SECTOR_4",
            )
        )
        self.assertEqual(result.draft_source, "GEMINI")
        self.assertLessEqual(len(result.draft.split()), 25)

    def test_status_draft_rejects_new_deployment_order(self) -> None:
        service = GeminiIntelligenceService(
            client=FakeGeminiClient({"draft": "Tanker Two, deploy to Sector Four now."}),
            model="test-model",
        )
        with self.assertRaises(GeminiResponseValidationError):
            service.draft_status(
                DraftStatusRequest(
                    resource_id="TANKER_2",
                    current_state="DISPATCHED",
                    missing_confirmation="ARRIVED",
                )
            )


if __name__ == "__main__":
    unittest.main()
