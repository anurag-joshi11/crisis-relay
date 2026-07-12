from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from backend.schemas.gemini_schema import ExtractRequest, ExtractionResult, ScenarioContext
from backend.services.gemini_service import GeminiIntelligenceService


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_VERSION = "2026-07-11.student1.v2"
RESULTS_DIR = ROOT / "benchmark_results"


def load_context() -> ScenarioContext:
    metadata = json.loads((ROOT / "dataset" / "scenario_metadata.json").read_text())
    return ScenarioContext.model_validate(
        {
            "operations": metadata["operations"],
            "resources": metadata["resources"],
            "state_machine": metadata["state_machine"],
        }
    )


def load_cases() -> list[dict[str, Any]]:
    return json.loads((ROOT / "dataset" / "extraction_test_cases.json").read_text())


def operation_for_entity(context: ScenarioContext, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    for operation in context.operations:
        if operation.resource_id == entity_id:
            return operation.id
    return None


def enrich_case_expectations(case: dict[str, Any], context: ScenarioContext) -> dict[str, Any]:
    expected = dict(case["expected"])
    behavior = expected["expected_behavior"]
    enriched: dict[str, Any] = {
        "expected_behavior": behavior,
        "scored_fields": [],
        "fields_without_ground_truth": [
            "incident_type",
            "severity",
            "location",
            "transport_source",
        ],
    }

    if behavior == "EXTRACT_STATE":
        operation_id = operation_for_entity(context, expected["entity_id"])
        expected_event: dict[str, Any] = {
            "entity_id": expected["entity_id"],
            "new_state": expected["state_transition"],
            "previous_state": None,
        }
        if operation_id:
            expected_event["operation_id"] = operation_id
            enriched["expected_related_operation"] = operation_id
        enriched["expected_state_events"] = [expected_event]
        enriched["scored_fields"].extend(["state_events.entity_id", "state_events.new_state", "state_events.previous_state"])
        if operation_id:
            enriched["scored_fields"].extend(["state_events.operation_id", "related_operation"])

        if case["category"] == "BLOCKER_FAILURE":
            blocker = expected_blocker(case, expected["entity_id"], operation_id)
            if blocker:
                enriched["expected_blockers"] = [blocker]
                enriched["scored_fields"].extend(["blockers.entity_id", "blockers.type", "blockers.confidence"])
                if operation_id:
                    enriched["scored_fields"].append("blockers.operation_id")

        return enriched

    forbidden = {
        "entity_id": expected["must_not_transition_entity"],
        "new_state": expected["must_not_transition_to"],
    }
    enriched["forbidden_state_events"] = [forbidden]
    enriched["scored_fields"].extend(["forbidden_state_events.entity_id", "forbidden_state_events.new_state"])

    if expected.get("assumption_expected"):
        enriched["expected_assumptions"] = [
            {
                "entity_id": expected["must_not_transition_entity"],
                "blocked_transition": expected["must_not_transition_to"],
            }
        ]
        enriched["scored_fields"].extend(["assumptions.entity_id", "assumptions.blocked_transition"])

    if expected.get("unresolved_link_expected"):
        claim: dict[str, Any] = {"unresolved": True}
        enriched["expected_claims"] = [claim]
        enriched["scored_fields"].append("claims.unresolved")

    return enriched


def expected_blocker(case: dict[str, Any], entity_id: str, operation_id: str | None) -> dict[str, Any] | None:
    text = case["raw_text"].lower()
    blocker_type_by_keyword = {
        "smoke": "VISIBILITY",
        "visibility": "VISIBILITY",
        "debris": "DEBRIS",
        "bridge": "CLOSED_BRIDGE",
        "chemical": "CHEMICAL_EXPOSURE",
        "police": "POLICE_CLEARANCE",
        "collapsed": "ROAD_COLLAPSE",
        "floodwater": "FLOODWATER",
        "structural instability": "STRUCTURAL_INSTABILITY",
        "propulsion": "MECHANICAL_FAILURE",
    }
    for keyword, blocker_type in blocker_type_by_keyword.items():
        if keyword in text:
            blocker: dict[str, Any] = {"entity_id": entity_id, "type": blocker_type}
            if operation_id:
                blocker["operation_id"] = operation_id
            return blocker
    return None


def score_case(case: dict[str, Any], result: ExtractionResult, context: ScenarioContext) -> dict[str, Any]:
    expectations = enrich_case_expectations(case, context)
    details: list[dict[str, Any]] = []

    for expected_event in expectations.get("expected_state_events", []):
        matched = find_matching_state_event(result, expected_event)
        details.append(detail("expected_state_event", matched is not None, expected_event, event_dump(matched)))

    expected_events = expectations.get("expected_state_events", [])
    extra_events = find_unexpected_state_events(result, expected_events)
    if expected_events:
        details.append(detail("unexpected_extra_events", not extra_events, [], [event_dump(event) for event in extra_events]))
    else:
        details.append(detail("unscored_extra_events", True, [], [event_dump(event) for event in extra_events]))

    for forbidden_event in expectations.get("forbidden_state_events", []):
        matched = find_forbidden_state_event(result, forbidden_event)
        details.append(detail("forbidden_state_event", matched is None, forbidden_event, event_dump(matched)))

    for expected_assumption in expectations.get("expected_assumptions", []):
        matched = find_matching_assumption(result, expected_assumption)
        details.append(detail("expected_assumption", matched is not None, expected_assumption, assumption_dump(matched)))

    for expected_claim in expectations.get("expected_claims", []):
        matched = find_matching_claim(result, expected_claim)
        details.append(detail("expected_claim", matched is not None, expected_claim, claim_dump(matched)))

    for expected_blocker in expectations.get("expected_blockers", []):
        matched = find_matching_blocker(result, expected_blocker)
        details.append(detail("expected_blocker", matched is not None, expected_blocker, blocker_dump(matched)))

    if "expected_related_operation" in expectations:
        expected = expectations["expected_related_operation"]
        details.append(detail("related_operation", result.related_operation == expected, expected, result.related_operation))

    if "expected_need_still_active" in expectations:
        expected = expectations["expected_need_still_active"]
        details.append(detail("need_still_active", result.need_still_active == expected, expected, result.need_still_active))

    passed = all(item["passed"] for item in details)
    return {
        "case_id": case["test_id"],
        "category": case["category"],
        "passed": passed,
        "expectations": expectations,
        "field_details": details,
        "actual": result.model_dump(),
    }


def find_matching_state_event(result: ExtractionResult, expected: dict[str, Any]):
    for event in result.state_events:
        if "operation_id" in expected and event.operation_id != expected["operation_id"]:
            continue
        if event.entity_id != expected["entity_id"]:
            continue
        if event.previous_state != expected["previous_state"]:
            continue
        if event.new_state != expected["new_state"]:
            continue
        if not 0 <= event.confidence <= 1:
            continue
        return event
    return None


def find_unexpected_state_events(result: ExtractionResult, expected_events: list[dict[str, Any]]):
    unexpected = []
    for event in result.state_events:
        if not any(find_event_matches_expected(event, expected) for expected in expected_events):
            unexpected.append(event)
    return unexpected


def find_event_matches_expected(event, expected: dict[str, Any]) -> bool:
    if "operation_id" in expected and event.operation_id != expected["operation_id"]:
        return False
    return (
        event.entity_id == expected["entity_id"]
        and event.previous_state == expected["previous_state"]
        and event.new_state == expected["new_state"]
        and 0 <= event.confidence <= 1
    )


def find_forbidden_state_event(result: ExtractionResult, forbidden: dict[str, Any]):
    for event in result.state_events:
        if event.entity_id == forbidden["entity_id"] and event.new_state == forbidden["new_state"]:
            return event
    return None


def find_matching_assumption(result: ExtractionResult, expected: dict[str, Any]):
    for assumption in result.assumptions:
        if "entity_id" in expected and assumption.entity_id != expected["entity_id"]:
            continue
        if "blocked_transition" in expected and assumption.blocked_transition != expected["blocked_transition"]:
            continue
        return assumption
    return None


def find_matching_claim(result: ExtractionResult, expected: dict[str, Any]):
    for claim in result.claims:
        if "entity_id" in expected and claim.entity_id != expected["entity_id"]:
            continue
        if "operation_id" in expected and claim.operation_id != expected["operation_id"]:
            continue
        if "unresolved" in expected and claim.unresolved != expected["unresolved"]:
            continue
        return claim
    return None


def find_matching_blocker(result: ExtractionResult, expected: dict[str, Any]):
    for blocker in result.blockers:
        if "entity_id" in expected and blocker.entity_id != expected["entity_id"]:
            continue
        if "operation_id" in expected and blocker.operation_id != expected["operation_id"]:
            continue
        if "type" in expected and blocker.type != expected["type"]:
            continue
        if not 0 <= blocker.confidence <= 1:
            continue
        return blocker
    return None


def detail(field: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {"field": field, "passed": passed, "expected": expected, "actual": actual}


def event_dump(event) -> dict[str, Any] | None:
    return event.model_dump() if event else None


def assumption_dump(assumption) -> dict[str, Any] | None:
    return assumption.model_dump() if assumption else None


def claim_dump(claim) -> dict[str, Any] | None:
    return claim.model_dump() if claim else None


def blocker_dump(blocker) -> dict[str, Any] | None:
    return blocker.model_dump() if blocker else None


def create_report(
    cases: list[dict[str, Any]],
    model: str,
    delay_seconds: float = 5.0,
    max_rate_limit_retries: int = 3,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    selected_ids = [case["test_id"] for case in cases]
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "created_at_utc": now,
        "updated_at_utc": now,
        "model": model,
        "delay_seconds": delay_seconds,
        "max_rate_limit_retries": max_rate_limit_retries,
        "total_cases": len(cases),
        "selected_case_ids": selected_ids,
        "summary": empty_summary(len(cases)),
        "cases": [],
    }


def empty_summary(total_cases: int) -> dict[str, Any]:
    return {
        "attempted_cases": 0,
        "passed_cases": 0,
        "failed_cases": 0,
        "api_error_cases": 0,
        "overall_accuracy": 0.0,
        "per_category_accuracy": {},
        "per_field_totals": {},
        "total_cases": total_cases,
    }


def run_benchmark(
    *,
    cases: list[dict[str, Any]],
    context: ScenarioContext,
    service: GeminiIntelligenceService,
    report: dict[str, Any],
    report_path: Path,
    delay_seconds: float = 5.0,
    max_rate_limit_retries: int = 3,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    report.setdefault("delay_seconds", delay_seconds)
    report.setdefault("max_rate_limit_retries", max_rate_limit_retries)
    completed = {
        case_result["case_id"]
        for case_result in report["cases"]
        if "error" not in case_result
    }
    attempted_api_call = False
    for case in cases:
        if case["test_id"] in completed:
            continue
        case_result = run_case(
            case,
            context,
            service,
            delay_before_first_call=attempted_api_call,
            delay_seconds=delay_seconds,
            max_rate_limit_retries=max_rate_limit_retries,
            sleeper=sleeper,
        )
        attempted_api_call = attempted_api_call or case_result.get("api_attempt_count", 0) > 0
        replace_case_result(report, case_result)
        update_summary(report)
        save_report(report, report_path)
        status = "PASS" if case_result["passed"] else "FAIL"
        print(f"{status} {case['test_id']}")
    return report


def run_case(
    case: dict[str, Any],
    context: ScenarioContext,
    service: GeminiIntelligenceService,
    delay_before_first_call: bool = False,
    delay_seconds: float = 5.0,
    max_rate_limit_retries: int = 3,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    api_attempt_count = 0
    retry_details: list[dict[str, Any]] = []
    while True:
        if api_attempt_count == 0 and delay_before_first_call:
            sleeper(delay_seconds)
        api_attempt_count += 1
        try:
            result = service.extract_report(
                ExtractRequest(raw_text=case["raw_text"], scenario_context=context)
            )
            scored = score_case(case, result, context)
            scored["api_attempt_count"] = api_attempt_count
            if retry_details:
                scored["retry_details"] = retry_details
            return scored
        except Exception as exc:
            if is_rate_limit_error(exc) and api_attempt_count <= max_rate_limit_retries:
                retry_delay = retry_delay_seconds(exc, api_attempt_count, delay_seconds)
                retry_details.append(
                    {
                        "attempt": api_attempt_count,
                        "next_delay_seconds": retry_delay,
                        "error": {
                            "type": type(exc).__name__,
                            "message": sanitize_error(str(exc)),
                        },
                    }
                )
                sleeper(retry_delay)
                continue
            case_result = {
                "case_id": case["test_id"],
                "category": case["category"],
                "passed": False,
                "api_attempt_count": api_attempt_count,
                "error": {
                    "type": type(exc).__name__,
                    "message": sanitize_error(str(exc)),
                },
                "field_details": [
                    detail("service_exception", False, "successful ExtractionResult", type(exc).__name__)
                ],
            }
            if retry_details:
                case_result["retry_details"] = retry_details
            return case_result


def replace_case_result(report: dict[str, Any], case_result: dict[str, Any]) -> None:
    for index, existing in enumerate(report["cases"]):
        if existing["case_id"] == case_result["case_id"]:
            report["cases"][index] = case_result
            return
    report["cases"].append(case_result)


def is_rate_limit_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "429" in text or "resource_exhausted" in text or "rate limit" in text or "quota" in text


def retry_delay_seconds(exc: Exception, attempt: int, delay_seconds: float) -> float:
    provider_delay = provider_retry_delay_seconds(str(exc))
    if provider_delay is not None:
        return provider_delay + 1.0
    return max(delay_seconds, 1.0) * (2 ** (attempt - 1)) + 1.0


def provider_retry_delay_seconds(message: str) -> float | None:
    patterns = [
        r"retry[_ -]?delay['\"]?\s*[:=]\s*['\"]?([0-9]+(?:\.[0-9]+)?)s?",
        r"retry[_ -]?delay\s*\{\s*seconds:\s*([0-9]+(?:\.[0-9]+)?)",
        r"retry after\s*([0-9]+(?:\.[0-9]+)?)\s*seconds?",
        r"retry in\s*([0-9]+(?:\.[0-9]+)?)s?",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def sanitize_error(message: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message


def update_summary(report: dict[str, Any]) -> None:
    cases = report["cases"]
    attempted = len(cases)
    passed = sum(1 for case in cases if case["passed"])
    failed = attempted - passed
    api_errors = sum(1 for case in cases if "error" in case)
    report["updated_at_utc"] = datetime.now(UTC).isoformat()
    report["summary"] = {
        "total_cases": report["total_cases"],
        "attempted_cases": attempted,
        "passed_cases": passed,
        "failed_cases": failed,
        "api_error_cases": api_errors,
        "overall_accuracy": passed / attempted if attempted else 0.0,
        "per_category_accuracy": per_category_accuracy(cases),
        "per_field_totals": per_field_totals(cases),
    }


def per_category_accuracy(cases: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, dict[str, int]] = {}
    for case in cases:
        category = case["category"]
        totals.setdefault(category, {"attempted": 0, "passed": 0})
        totals[category]["attempted"] += 1
        totals[category]["passed"] += 1 if case["passed"] else 0
    return {
        category: {
            **values,
            "accuracy": values["passed"] / values["attempted"] if values["attempted"] else 0.0,
        }
        for category, values in sorted(totals.items())
    }


def per_field_totals(cases: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, dict[str, int]] = {}
    for case in cases:
        for item in case.get("field_details", []):
            field = item["field"]
            totals.setdefault(field, {"attempted": 0, "passed": 0})
            totals[field]["attempted"] += 1
            totals[field]["passed"] += 1 if item["passed"] else 0
    return {
        field: {
            **values,
            "accuracy": values["passed"] / values["attempted"] if values["attempted"] else 0.0,
        }
        for field, values in sorted(totals.items())
    }


def save_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    tmp_path.replace(path)


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def select_cases(cases: list[dict[str, Any]], case_id: str | None, limit: int | None) -> list[dict[str, Any]]:
    selected = cases
    if case_id:
        selected = [case for case in selected if case["test_id"] == case_id]
    if limit is not None:
        selected = selected[:limit]
    return selected


def report_path_for_new_run() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return RESULTS_DIR / f"extraction_benchmark_{stamp}.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CrisisRelay Gemini extraction benchmark.")
    parser.add_argument("--resume", type=Path, help="Resume an existing benchmark report JSON file.")
    parser.add_argument("--case-id", help="Run a single benchmark case ID.")
    parser.add_argument("--limit", type=int, help="Run only the first N selected cases.")
    parser.add_argument("--delay-seconds", type=float, default=5.0, help="Seconds to wait between Gemini API calls.")
    parser.add_argument(
        "--max-rate-limit-retries",
        type=int,
        default=3,
        help="Maximum retries for transient Gemini 429/RESOURCE_EXHAUSTED failures.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, service: GeminiIntelligenceService | None = None) -> int:
    args = parse_args(argv)
    all_cases = load_cases()
    context = load_context()

    if args.resume:
        report_path = args.resume
        report = load_report(report_path)
        cases = [case for case in all_cases if case["test_id"] in set(report["selected_case_ids"])]
        report.setdefault("delay_seconds", args.delay_seconds)
        report.setdefault("max_rate_limit_retries", args.max_rate_limit_retries)
    else:
        cases = select_cases(all_cases, args.case_id, args.limit)
        service = service or GeminiIntelligenceService()
        report = create_report(
            cases,
            service.model,
            delay_seconds=args.delay_seconds,
            max_rate_limit_retries=args.max_rate_limit_retries,
        )
        report_path = report_path_for_new_run()

    service = service or GeminiIntelligenceService()
    run_benchmark(
        cases=cases,
        context=context,
        service=service,
        report=report,
        report_path=report_path,
        delay_seconds=report["delay_seconds"],
        max_rate_limit_retries=report["max_rate_limit_retries"],
    )
    summary = report["summary"]
    print(f"\nPassed {summary['passed_cases']}/{summary['attempted_cases']} attempted cases")
    print(f"Report: {report_path}")
    return 0 if summary["failed_cases"] == 0 and summary["attempted_cases"] == summary["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
