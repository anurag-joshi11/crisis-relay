from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.benchmark_extraction import (
    create_report,
    load_context,
    run_benchmark,
    run_case,
    score_case,
)
from backend.schemas.gemini_schema import ExtractionResult


def case(
    *,
    test_id: str = "TC-TEST",
    category: str = "EXPLICIT_STATE",
    raw_text: str = "Tanker two dispatched.",
    expected: dict | None = None,
) -> dict:
    return {
        "test_id": test_id,
        "category": category,
        "raw_text": raw_text,
        "expected": expected
        or {
            "entity_id": "TANKER_2",
            "state_transition": "DISPATCHED",
            "expected_behavior": "EXTRACT_STATE",
        },
    }


def result(**overrides) -> ExtractionResult:
    payload = {
        "incident_type": None,
        "severity": None,
        "location": None,
        "state_events": [],
        "assumptions": [],
        "claims": [],
        "blockers": [],
        "related_operation": None,
        "need_still_active": False,
        "transport_source": None,
    }
    payload.update(overrides)
    return ExtractionResult.model_validate(payload)


def event(entity_id="TANKER_2", new_state="DISPATCHED", operation_id="OP-WATER-001"):
    return {
        "operation_id": operation_id,
        "entity_id": entity_id,
        "previous_state": None,
        "new_state": new_state,
        "evidence": "fixture evidence",
        "confidence": 0.9,
    }


class FakeService:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.model = "fake-model"

    def extract_report(self, request):
        self.calls.append(request.raw_text)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class BenchmarkScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = load_context()

    def assert_case_passes(self, benchmark_case: dict, extraction: ExtractionResult) -> None:
        scored = score_case(benchmark_case, extraction, self.context)
        self.assertTrue(scored["passed"], scored["field_details"])

    def assert_case_fails(self, benchmark_case: dict, extraction: ExtractionResult) -> None:
        scored = score_case(benchmark_case, extraction, self.context)
        self.assertFalse(scored["passed"], scored["field_details"])

    def test_correct_expected_state_event_passes(self) -> None:
        self.assert_case_passes(
            case(),
            result(
                state_events=[event()],
                related_operation="OP-WATER-001",
                need_still_active=True,
            ),
        )

    def test_wrong_entity_id_fails(self) -> None:
        self.assert_case_fails(case(), result(state_events=[event(entity_id="BUS_7")]))

    def test_wrong_operation_id_fails_when_ground_truth_exists(self) -> None:
        self.assert_case_fails(case(), result(state_events=[event(operation_id="OP-EVAC-001")]))

    def test_wrong_new_state_fails(self) -> None:
        self.assert_case_fails(case(), result(state_events=[event(new_state="ARRIVED")]))

    def test_forbidden_transition_fails(self) -> None:
        benchmark_case = case(
            category="ASSUMPTION",
            raw_text="Bus seven should be there by now.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "BUS_7",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": True,
                "unresolved_link_expected": False,
            },
        )
        self.assert_case_fails(
            benchmark_case,
            result(
                state_events=[event(entity_id="BUS_7", new_state="ARRIVED", operation_id="OP-EVAC-001")],
                assumptions=[
                    {
                        "text": "should be there",
                        "entity_id": "BUS_7",
                        "blocked_transition": "ARRIVED",
                        "reason": "assumption",
                    }
                ],
            ),
        )

    def test_correct_structured_assumption_passes(self) -> None:
        benchmark_case = case(
            category="ASSUMPTION",
            raw_text="Bus seven should be there by now.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "BUS_7",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": True,
                "unresolved_link_expected": False,
            },
        )
        self.assert_case_passes(
            benchmark_case,
            result(
                assumptions=[
                    {
                        "text": "should be there",
                        "entity_id": "BUS_7",
                        "blocked_transition": "ARRIVED",
                        "reason": "assumption",
                    }
                ]
            ),
        )

    def test_unrelated_non_empty_assumption_fails(self) -> None:
        benchmark_case = case(
            category="ASSUMPTION",
            raw_text="Bus seven should be there by now.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "BUS_7",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": True,
                "unresolved_link_expected": False,
            },
        )
        self.assert_case_fails(
            benchmark_case,
            result(
                assumptions=[
                    {
                        "text": "probably completed",
                        "entity_id": "TANKER_2",
                        "blocked_transition": "COMPLETED",
                        "reason": "assumption",
                    }
                ]
            ),
        )

    def test_correct_unresolved_claim_passes(self) -> None:
        benchmark_case = case(
            category="UNLINKED_EVENT",
            raw_text="Sector Four residents arriving at Alpha.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "BUS_7",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": False,
                "unresolved_link_expected": True,
            },
        )
        self.assert_case_passes(
            benchmark_case,
            result(
                claims=[
                    {
                        "text": "residents arriving",
                        "entity_id": None,
                        "operation_id": "OP-EVAC-001",
                        "unresolved": True,
                        "reason": "unlinked",
                    }
                ]
            ),
        )

    def test_unrelated_non_empty_claim_fails(self) -> None:
        benchmark_case = case(
            category="UNLINKED_EVENT",
            raw_text="Sector Four residents arriving at Alpha.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "BUS_7",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": False,
                "unresolved_link_expected": True,
            },
        )
        self.assert_case_fails(
            benchmark_case,
            result(
                claims=[
                    {
                        "text": "water visible",
                        "entity_id": None,
                        "operation_id": "OP-WATER-001",
                        "unresolved": True,
                        "reason": "unlinked",
                    }
                ]
            ),
        )

    def test_expected_blocker_passes(self) -> None:
        benchmark_case = case(
            category="BLOCKER_FAILURE",
            raw_text="Tanker two holding south. Can't enter because of smoke.",
            expected={
                "entity_id": "TANKER_2",
                "state_transition": "HOLDING",
                "expected_behavior": "EXTRACT_STATE",
            },
        )
        self.assert_case_passes(
            benchmark_case,
            result(
                state_events=[event(new_state="HOLDING")],
                blockers=[
                    {
                        "entity_id": "TANKER_2",
                        "operation_id": "OP-WATER-001",
                        "type": "VISIBILITY",
                        "evidence": "smoke",
                        "confidence": 0.9,
                    }
                ],
                related_operation="OP-WATER-001",
                need_still_active=True,
            ),
        )

    def test_missing_expected_blocker_fails(self) -> None:
        benchmark_case = case(
            category="BLOCKER_FAILURE",
            raw_text="Tanker two holding south. Can't enter because of smoke.",
            expected={
                "entity_id": "TANKER_2",
                "state_transition": "HOLDING",
                "expected_behavior": "EXTRACT_STATE",
            },
        )
        self.assert_case_fails(
            benchmark_case,
            result(
                state_events=[event(new_state="HOLDING")],
                related_operation="OP-WATER-001",
                need_still_active=True,
            ),
        )

    def test_wrong_blocker_type_fails(self) -> None:
        benchmark_case = case(
            category="BLOCKER_FAILURE",
            raw_text="Tanker two holding south. Can't enter because of smoke.",
            expected={
                "entity_id": "TANKER_2",
                "state_transition": "HOLDING",
                "expected_behavior": "EXTRACT_STATE",
            },
        )
        self.assert_case_fails(
            benchmark_case,
            result(
                state_events=[event(new_state="HOLDING")],
                blockers=[
                    {
                        "entity_id": "TANKER_2",
                        "operation_id": "OP-WATER-001",
                        "type": "DEBRIS",
                        "evidence": "smoke",
                        "confidence": 0.9,
                    }
                ],
                related_operation="OP-WATER-001",
                need_still_active=True,
            ),
        )

    def test_related_operation_mismatch_fails(self) -> None:
        self.assert_case_fails(
            case(),
            result(
                state_events=[event()],
                related_operation="OP-EVAC-001",
                need_still_active=True,
            ),
        )

    def test_terminal_state_does_not_create_need_still_active_ground_truth(self) -> None:
        scored = score_case(
            case(
                category="COMPLETION",
                raw_text="Water drop complete. Tanker two returning.",
                expected={
                    "entity_id": "TANKER_2",
                    "state_transition": "COMPLETED",
                    "expected_behavior": "EXTRACT_STATE",
                },
            ),
            result(
                state_events=[event(new_state="COMPLETED")],
                related_operation="OP-WATER-001",
                need_still_active=False,
            ),
            self.context,
        )
        self.assertNotIn("expected_need_still_active", scored["expectations"])
        self.assertFalse(any(item["field"] == "need_still_active" for item in scored["field_details"]))

    def test_unrelated_state_event_in_uncertainty_case_is_unscored_not_failure(self) -> None:
        benchmark_case = case(
            category="ASSUMPTION",
            raw_text="Tanker two should be there by now.",
            expected={
                "state_transition": None,
                "must_not_transition_entity": "TANKER_2",
                "must_not_transition_to": "ARRIVED",
                "expected_behavior": "PRESERVE_UNCERTAINTY",
                "assumption_expected": False,
                "unresolved_link_expected": False,
            },
        )
        scored = score_case(
            benchmark_case,
            result(
                state_events=[event(entity_id="CREW_7", new_state="ARRIVED", operation_id=None)],
            ),
            self.context,
        )
        self.assertTrue(scored["passed"], scored["field_details"])
        unscored = [item for item in scored["field_details"] if item["field"] == "unscored_extra_events"]
        self.assertEqual(len(unscored), 1)
        self.assertEqual(unscored[0]["actual"][0]["entity_id"], "CREW_7")
        self.assertFalse(any(item["field"] == "unexpected_extra_events" for item in scored["field_details"]))

    def test_service_exception_is_failure_and_benchmark_continues(self) -> None:
        first = case(test_id="TC-ERR")
        second = case(test_id="TC-OK")
        service = FakeService(
            [
                RuntimeError("rate limit for secret-key"),
                result(
                    state_events=[event()],
                    related_operation="OP-WATER-001",
                    need_still_active=True,
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            report = create_report([first, second], service.model)
            run_benchmark(
                cases=[first, second],
                context=self.context,
                service=service,
                report=report,
                report_path=report_path,
            )

        self.assertEqual(report["summary"]["attempted_cases"], 2)
        self.assertEqual(report["summary"]["failed_cases"], 1)
        self.assertEqual(report["summary"]["api_error_cases"], 1)
        self.assertEqual(service.calls, [first["raw_text"], second["raw_text"]])

    def test_completed_cases_are_skipped_during_resume(self) -> None:
        first = case(test_id="TC-DONE")
        second = case(test_id="TC-LEFT")
        service = FakeService(
            [
                result(
                    state_events=[event()],
                    related_operation="OP-WATER-001",
                    need_still_active=True,
                )
            ]
        )
        report = create_report([first, second], service.model)
        report["cases"].append(
            {
                "case_id": "TC-DONE",
                "category": "EXPLICIT_STATE",
                "passed": True,
                "field_details": [],
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            run_benchmark(
                cases=[first, second],
                context=self.context,
                service=service,
                report=report,
                report_path=report_path,
            )

        self.assertEqual(service.calls, [second["raw_text"]])
        self.assertEqual(len(report["cases"]), 2)


if __name__ == "__main__":
    unittest.main()
