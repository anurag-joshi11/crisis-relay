from typing import Protocol


class ExtractionProvider(Protocol):
    def extract(self, report: dict) -> dict:
        ...


class GroundTruthMockExtractionProvider:
    def extract(self, report: dict) -> dict:
        ground_truth = report.get("ground_truth") or {}
        state_events = []

        for operation_id, state in ground_truth.get("requests", []):
            state_events.append(_event(report, operation_id=operation_id, state=state))

        if ground_truth.get("state"):
            state_events.append(
                _event(
                    report,
                    operation_id=ground_truth.get("operation_id"),
                    entity_id=ground_truth.get("entity_id"),
                    state=ground_truth["state"],
                )
            )

        blockers = []
        if ground_truth.get("blocker"):
            blockers.append(
                {
                    "operation_id": ground_truth.get("operation_id"),
                    "entity_id": ground_truth.get("entity_id"),
                    "type": ground_truth["blocker"],
                    "evidence": report["raw_text"],
                }
            )

        assumptions = []
        if ground_truth.get("assumption"):
            assumptions.append(ground_truth["assumption"])

        claims = []
        if ground_truth.get("claim"):
            claims.append(ground_truth["claim"])

        return {
            "incident_type": ground_truth.get("incident_type"),
            "severity": ground_truth.get("severity"),
            "location": ground_truth.get("location"),
            "state_events": state_events,
            "assumptions": assumptions,
            "claims": claims,
            "blockers": blockers,
            "related_operation": ground_truth.get("related_operation"),
            "need_still_active": ground_truth.get("need_still_active", False),
            "transport_source": ground_truth.get("transport_source"),
        }


def _event(report: dict, operation_id: str | None, state: str, entity_id: str | None = None) -> dict:
    return {
        "operation_id": operation_id,
        "entity_id": entity_id,
        "previous_state": None,
        "new_state": state,
        "evidence": report["raw_text"],
        "confidence": 1.0,
    }
