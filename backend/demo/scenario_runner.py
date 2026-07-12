import json
from pathlib import Path

from backend.services.extraction_provider import GroundTruthMockExtractionProvider
from backend.services.ingestion_service import IngestionService
from backend.services.mongodb_service import MongoDBService

ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "dataset"


class ScenarioRunner:
    def __init__(self, store=None, provider=None):
        self.store = store or MongoDBService()
        self.provider = provider or GroundTruthMockExtractionProvider()
        self.ingestion = IngestionService(self.store, self.provider)
        self.metadata = _load_json(DATASET_DIR / "scenario_metadata.json")
        self.reports = _load_json(DATASET_DIR / "wildfire_scenario.json")
        self.ingestion.seed_operations(self.metadata)

    def reset(self) -> dict:
        self.store.reset()
        self.ingestion.seed_operations(self.metadata)
        self.store.set_app_state("demo", {"event_index": 0, "total_events": len(self.reports), "complete": False})
        return self.status()

    def next_event(self) -> dict:
        state = self.store.get_app_state("demo") or {"event_index": 0, "total_events": len(self.reports), "complete": False}
        index = state["event_index"]
        if index >= len(self.reports):
            state["complete"] = True
            self.store.set_app_state("demo", state)
            return self.status()
        self.ingestion.ingest_report(self.reports[index])
        state["event_index"] = index + 1
        state["complete"] = state["event_index"] >= len(self.reports)
        self.store.set_app_state("demo", state)
        return self.status()

    def status(self) -> dict:
        state = self.store.get_app_state("demo") or {"event_index": 0, "total_events": len(self.reports), "complete": False}
        reports = self.store.list_reports()
        current_time = reports[-1]["scenario_time"] if reports else self.reports[0]["scenario_time"]
        selected = _select_operation(self.store)
        return {
            "scenario": {"id": self.metadata["scenario_id"], "name": self.metadata["name"], "current_time": current_time},
            "reports": [_public_report(reports[-1])] if reports else [],
            "operations": [_public_operation(operation) for operation in self.store.list_operations()],
            "blindspots": [_public_blindspot(blindspot) for blindspot in self.store.list_blindspots("OPEN")],
            "selected_timeline": _selected_timeline(self.store, selected),
            "demo": state,
        }


def _select_operation(store) -> str | None:
    blindspots = store.list_blindspots("OPEN")
    critical = [item for item in blindspots if item.get("severity") == "CRITICAL"]
    if critical:
        return critical[0]["operation_id"]
    if blindspots:
        return blindspots[0]["operation_id"]
    operations = store.list_operations()
    return operations[0]["operation_id"] if operations else None


def _selected_timeline(store, operation_id: str | None) -> dict:
    if not operation_id:
        return {"operation_id": None, "events": [], "missing_confirmation": None, "related_active_need": None}
    operation = store.get_operation(operation_id)
    events = [
        {"scenario_time": event["scenario_time"], "new_state": event["new_state"], "evidence": event["evidence"]}
        for event in store.list_state_events(operation_id)
    ]
    return {
        "operation_id": operation_id,
        "events": events,
        "missing_confirmation": _missing_confirmation(operation),
        "related_active_need": _related_active_need(store, operation_id),
    }


def _missing_confirmation(operation: dict | None) -> str | None:
    if not operation or operation.get("fulfilled"):
        return None
    state = operation.get("current_state")
    if state == "DISPATCHED":
        return "ARRIVAL_OR_FULFILMENT"
    if state in {"ARRIVED", "HOLDING"}:
        return "FULFILMENT"
    return "STATE_PROGRESS"


def _related_active_need(store, operation_id: str) -> dict | None:
    for report in reversed(store.list_reports()):
        gt = report.get("ground_truth") or {}
        if gt.get("related_operation") == operation_id and gt.get("need_still_active"):
            return {"scenario_time": report["scenario_time"], "evidence": report["raw_text"]}
    return None


def _public_report(report: dict) -> dict:
    return {
        "report_id": report["report_id"],
        "scenario_time": report["scenario_time"],
        "source": report["source"],
        "channel": report["channel"],
        "raw_text": report["raw_text"],
    }


def _public_operation(operation: dict) -> dict:
    return {
        "operation_id": operation["operation_id"],
        "operation_type": operation["operation_type"],
        "location": operation["location"],
        "resource_id": operation["resource_id"],
        "current_state": operation["current_state"],
        "priority": operation["priority"],
        "fulfilled": operation["fulfilled"],
        "need_still_active": operation["need_still_active"],
        "last_state_change": operation["last_state_change"],
    }


def _public_blindspot(blindspot: dict) -> dict:
    return {
        "blindspot_id": blindspot["blindspot_id"],
        "operation_id": blindspot["operation_id"],
        "resource_id": blindspot["resource_id"],
        "type": blindspot["type"],
        "severity": blindspot["severity"],
        "status": blindspot["status"],
        "minutes_in_state": blindspot["minutes_in_state"],
        "reason": blindspot["reason"],
    }


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
