from __future__ import annotations

import json
from pathlib import Path

from backend.schemas.gemini_schema import ExtractRequest, ScenarioContext
from backend.services.gemini_service import GeminiIntelligenceService


ROOT = Path(__file__).resolve().parents[1]


def load_context() -> ScenarioContext:
    metadata = json.loads((ROOT / "dataset" / "scenario_metadata.json").read_text())
    return ScenarioContext.model_validate(
        {
            "operations": metadata["operations"],
            "resources": metadata["resources"],
            "state_machine": metadata["state_machine"],
        }
    )


def case_passed(expected: dict, result) -> bool:
    events = result.state_events
    if expected["expected_behavior"] == "EXTRACT_STATE":
        return any(
            event.entity_id == expected["entity_id"]
            and event.new_state == expected["state_transition"]
            for event in events
        )

    forbidden_entity = expected["must_not_transition_entity"]
    forbidden_state = expected["must_not_transition_to"]
    forbidden_transition = any(
        event.entity_id == forbidden_entity and event.new_state == forbidden_state
        for event in events
    )
    if forbidden_transition:
        return False
    if expected.get("assumption_expected") and not result.assumptions:
        return False
    if expected.get("unresolved_link_expected") and not result.claims:
        return False
    return True


def main() -> int:
    cases = json.loads((ROOT / "dataset" / "extraction_test_cases.json").read_text())
    context = load_context()
    service = GeminiIntelligenceService()
    failures: list[str] = []

    for case in cases:
        result = service.extract_report(
            ExtractRequest(raw_text=case["raw_text"], scenario_context=context)
        )
        if not case_passed(case["expected"], result):
            failures.append(case["test_id"])
            print(f"FAIL {case['test_id']}: {case['raw_text']}")
            print(result.model_dump_json(indent=2))
        else:
            print(f"PASS {case['test_id']}")

    print(f"\nPassed {len(cases) - len(failures)}/{len(cases)} cases")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
