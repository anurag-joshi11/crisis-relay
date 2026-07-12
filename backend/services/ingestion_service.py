from backend.services.priority_engine import default_priority
from backend.services.state_engine import evaluate_unconfirmed, fulfilled_for_state, is_transition_allowed
from backend.services.time_utils import elapsed_minutes


class IngestionService:
    def __init__(self, store, extraction_provider):
        self.store = store
        self.extraction_provider = extraction_provider

    def seed_operations(self, metadata: dict) -> None:
        for item in metadata["operations"]:
            existing = self.store.get_operation(item["id"])
            operation = existing or {
                "operation_id": item["id"],
                "operation_type": item["type"],
                "location": item["location"],
                "resource_id": item["resource_id"],
                "current_state": None,
                "priority": default_priority(item["type"]),
                "fulfilled": False,
                "need_still_active": False,
                "last_state_change": None,
                "blockers": [],
            }
            self.store.upsert_operation(operation)

    def ingest_report(self, report: dict) -> dict:
        inserted = self.store.insert_report_once(report)
        if not inserted:
            return {"report_id": report["report_id"], "duplicate": True, "state_events": []}

        extraction = self.extraction_provider.extract(report)
        applied_events = []

        related_operation = extraction.get("related_operation")
        if related_operation and extraction.get("need_still_active"):
            operation = self.store.get_operation(related_operation)
            if operation:
                operation["need_still_active"] = True
                self.store.upsert_operation(operation)

        for proposed in extraction.get("state_events", []):
            operation = self._resolve_operation(proposed)
            if not operation:
                continue
            new_state = proposed.get("new_state")
            current_state = operation.get("current_state")
            if not is_transition_allowed(current_state, new_state):
                continue

            event = {
                "report_id": report["report_id"],
                "scenario_time": report["scenario_time"],
                "operation_id": operation["operation_id"],
                "entity_id": proposed.get("entity_id") or operation.get("resource_id"),
                "previous_state": current_state,
                "new_state": new_state,
                "evidence": proposed.get("evidence") or report["raw_text"],
                "confidence": proposed.get("confidence", 1.0),
            }
            if self.store.insert_state_event_once(event):
                operation["current_state"] = new_state
                operation["last_state_change"] = report["scenario_time"]
                operation["fulfilled"] = fulfilled_for_state(new_state, operation.get("fulfilled", False))
                if extraction.get("need_still_active"):
                    operation["need_still_active"] = True
                if extraction.get("severity") and operation["operation_type"] == "WATER_DROP":
                    operation["priority"] = extraction["severity"]
                if extraction.get("blockers"):
                    operation["blockers"] = extraction["blockers"]
                self.store.upsert_operation(operation)
                applied_events.append(event)

        for blocker in extraction.get("blockers", []):
            operation = self._resolve_operation(blocker)
            if operation:
                blockers = operation.get("blockers", [])
                blockers.append(blocker)
                operation["blockers"] = blockers
                self.store.upsert_operation(operation)

        self.refresh_blindspots(report["scenario_time"])
        return {"report_id": report["report_id"], "duplicate": False, "state_events": applied_events}

    def refresh_blindspots(self, scenario_time: str) -> None:
        for operation in self.store.list_operations():
            minutes = elapsed_minutes(operation.get("last_state_change"), scenario_time)
            if operation.get("current_state") in {"COMPLETED", "VERIFIED"} or operation.get("fulfilled"):
                open_blindspot = self.store.find_open_blindspot_for_operation(operation["operation_id"])
                if open_blindspot:
                    open_blindspot["status"] = "RESOLVED"
                    open_blindspot["resolved_at"] = scenario_time
                    self.store.upsert_blindspot(open_blindspot)
                continue

            evaluation = evaluate_unconfirmed(operation, minutes)
            if not evaluation["alert"]:
                continue

            blindspot = self.store.find_open_blindspot_for_operation(operation["operation_id"])
            if not blindspot:
                blindspot = {
                    "blindspot_id": f"BS-{len(self.store.list_blindspots()) + 1:03d}",
                    "operation_id": operation["operation_id"],
                    "resource_id": operation["resource_id"],
                    "type": "UNCONFIRMED",
                    "status": "OPEN",
                }
            blindspot.update(
                {
                    "severity": evaluation["severity"],
                    "minutes_in_state": minutes,
                    "reason": _blindspot_reason(operation),
                    "demo_heuristic": True,
                }
            )
            self.store.upsert_blindspot(blindspot)

    def _resolve_operation(self, proposed: dict) -> dict | None:
        operation_id = proposed.get("operation_id")
        if operation_id:
            return self.store.get_operation(operation_id)
        entity_id = proposed.get("entity_id")
        if entity_id:
            return self.store.get_operation_by_resource(entity_id)
        return None


def _blindspot_reason(operation: dict) -> str:
    state = operation.get("current_state") or "UNKNOWN"
    reason = (
        f"{operation['operation_type'].replace('_', '-').lower()} fulfilment is not verified. "
        f"{operation['resource_id']}'s latest confirmed state is {state}."
    )
    if operation.get("blockers"):
        reason += f" Blocker context: {operation['blockers'][-1].get('type')}."
    return reason
