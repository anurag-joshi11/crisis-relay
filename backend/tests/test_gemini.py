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


def schema_contains_key(value, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(schema_contains_key(item, key_name) for item in value.values())
    if isinstance(value, list):
        return any(schema_contains_key(item, key_name) for item in value)
    return False


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

    def test_prompt_requires_blocked_transition_for_uncertain_operational_transition(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(raw_text="Bus 7 may have arrived.", scenario_context=default_context())
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("Set blocked_transition to the canonical state", prompt)
        self.assertIn("Do not leave blocked_transition null", prompt)
        self.assertIn("scenario_context.state_machine", prompt)

    def test_tc021_style_assumption_blocked_transition_survives_validation(self) -> None:
        result = self.extract_with_payload(
            "Bus seven should be there by now.",
            extraction_payload(
                assumptions=[
                    {
                        "text": "Bus seven should be there by now.",
                        "entity_id": "BUS_7",
                        "blocked_transition": "ARRIVED",
                        "reason": "Should language describes an unconfirmed arrival.",
                    }
                ]
            ),
        )

        self.assertEqual(result.state_events, [])
        self.assertEqual(result.assumptions[0].entity_id, "BUS_7")
        self.assertEqual(result.assumptions[0].blocked_transition, "ARRIVED")

    def test_prompt_requires_blocker_type_to_capture_cause_not_state(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Tanker two holding south. Can't enter because of smoke.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("blocker.type must describe the cause category", prompt)
        self.assertIn("Do not use BLOCKED as blocker.type", prompt)
        self.assertIn("Use VISIBILITY for smoke", prompt)

    def test_prompt_prefers_resource_entity_for_operation_completion(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Water drop complete. Tanker two returning.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("use the resource_id as state_event.entity_id", prompt)
        self.assertIn("put the operation id in state_event.operation_id", prompt)
        self.assertIn("Do not use an operation id as state_event.entity_id", prompt)
        self.assertIn("responsible resource is explicitly named in the same report", prompt)

    def test_prompt_canonicalizes_report_entities_not_in_context(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Engine 6 holding south of the ridge.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("still extract the event when the text itself identifies an operational entity", prompt)
        self.assertIn('"Engine 6" -> ENGINE_6', prompt)
        self.assertIn('"Rescue Four" -> RESCUE_TEAM_4', prompt)

    def test_prompt_links_known_resource_events_to_operation_id(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Bus seven rolling out now.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("matches a scenario_context operation.resource_id", prompt)
        self.assertIn("fill operation_id with that operation id", prompt)

    def test_prompt_prefers_task_entity_when_no_resource_named(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="The water drop is done; we're heading home.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn('"water drop" -> WATER_DROP', prompt)
        self.assertIn("no responsible resource is named in the same report", prompt)
        self.assertIn("use the canonical task/outcome entity_id", prompt)
        self.assertIn("Explicit task/outcome completion or verification is enough", prompt)
        self.assertIn("do not downgrade it to an assumption or unresolved claim", prompt)
        self.assertIn("Do not treat scenario_context operation mapping alone", prompt)
        self.assertIn('"supply delivery" or "delivery inventory" -> SUPPLY_DELIVERY', prompt)

    def test_prompt_emits_state_event_for_named_blocked_entity(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Generator truck stopped; bridge is closed.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("blocker.entity_id must use that subject's canonical entity_id", prompt)
        self.assertIn("emit the blocked/failed state_event as well as the blocker", prompt)

    def test_prompt_maps_request_and_assignment_language(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="We received the request and are working it.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn('"received the request" -> ACKNOWLEDGED for RESOURCE_REQUEST', prompt)
        self.assertIn('"taken the evacuation", "taken the assignment", or "has taken"', prompt)

    def test_prompt_uses_final_verified_state_when_confirmed(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Command confirms Bus 12 arrived and unloaded all passengers.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn('"up and stable", or "unloaded all passengers" -> VERIFIED', prompt)
        self.assertIn("emit only the final VERIFIED state_event", prompt)

    def test_prompt_preserves_unlinked_outcomes_as_unresolved_claims(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="Power is back at Shelter Alpha.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn("emit a claim with unresolved=true instead of a state_event", prompt)
        self.assertIn("A claim must remain unresolved=true", prompt)
        self.assertIn('Facility/environment outcomes such as "power is back"', prompt)

    def test_prompt_maps_uncertain_got_generator_to_arrived(self) -> None:
        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(
                raw_text="They probably got the generator.",
                scenario_context=default_context(),
            )
        )

        prompt = client.models.calls[0]["contents"]
        self.assertIn('"probably got the generator"', prompt)
        self.assertIn("uncertain ARRIVED, not COMPLETED", prompt)

    def test_generate_content_uses_response_json_schema_with_strict_schema(self) -> None:
        schema = ExtractionResult.model_json_schema()
        self.assertTrue(schema_contains_key(schema, "additionalProperties"))

        client = FakeGeminiClient(extraction_payload())
        service = GeminiIntelligenceService(client=client, model="test-model")
        service.extract_report(
            ExtractRequest(raw_text="Tanker two dispatched.", scenario_context=default_context())
        )

        config = client.models.calls[0]["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIsNone(config.response_schema)
        self.assertEqual(config.response_json_schema, schema)
        self.assertTrue(schema_contains_key(config.response_json_schema, "additionalProperties"))

    def test_invalid_gemini_json_fails_contract_validation(self) -> None:
        service = GeminiIntelligenceService(
            client=FakeGeminiClient({"state_events": "not-an-array"}),
            model="test-model",
        )
        with self.assertRaises(GeminiResponseValidationError):
            service.extract_report(ExtractRequest(raw_text="Bus 7 assigned."))


class DraftStatusTests(unittest.TestCase):
    def test_fallback_draft_is_under_25_words_and_labeled(self) -> None:
        service = GeminiIntelligenceService(client=None, model="test-model", load_env=False)
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
