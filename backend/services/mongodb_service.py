import copy
import os
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

COLLECTIONS = ("reports", "operations", "state_events", "blindspots", "dispatches", "app_state")


class MongoDBService:
    def __init__(self, uri: str | None = None, database: str | None = None):
        try:
            from pymongo import ASCENDING, MongoClient
        except ImportError as exc:
            raise RuntimeError("pymongo is required for MongoDBService") from exc

        self._ascending = ASCENDING
        self.client = MongoClient(uri or os.environ["MONGODB_URI"])
        self.db = self.client[database or os.getenv("MONGODB_DATABASE", "crisis_relay")]
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        self.db.reports.create_index([("report_id", self._ascending)], unique=True)
        self.db.operations.create_index([("operation_id", self._ascending)], unique=True)
        self.db.operations.create_index([("resource_id", self._ascending)])
        self.db.state_events.create_index(
            [("report_id", self._ascending), ("operation_id", self._ascending), ("new_state", self._ascending)],
            unique=True,
        )
        self.db.blindspots.create_index([("blindspot_id", self._ascending)], unique=True)
        self.db.blindspots.create_index([("operation_id", self._ascending), ("status", self._ascending)])
        self.db.dispatches.create_index([("dispatch_id", self._ascending)], unique=True)

    def reset(self) -> None:
        for name in COLLECTIONS:
            self.db[name].delete_many({})

    def insert_report_once(self, report: dict) -> bool:
        try:
            self.db.reports.insert_one(copy.deepcopy(report))
            return True
        except Exception as exc:
            if exc.__class__.__name__ == "DuplicateKeyError":
                return False
            raise

    def upsert_operation(self, operation: dict) -> None:
        self.db.operations.replace_one({"operation_id": operation["operation_id"]}, copy.deepcopy(operation), upsert=True)

    def get_operation(self, operation_id: str) -> dict | None:
        return _clean(self.db.operations.find_one({"operation_id": operation_id}))

    def get_operation_by_resource(self, resource_id: str) -> dict | None:
        return _clean(self.db.operations.find_one({"resource_id": resource_id}))

    def list_operations(self) -> list[dict]:
        return [_clean(item) for item in self.db.operations.find({}, {"_id": 0}).sort("operation_id", self._ascending)]

    def insert_state_event_once(self, event: dict) -> bool:
        try:
            self.db.state_events.insert_one(copy.deepcopy(event))
            return True
        except Exception as exc:
            if exc.__class__.__name__ == "DuplicateKeyError":
                return False
            raise

    def list_state_events(self, operation_id: str | None = None) -> list[dict]:
        query = {"operation_id": operation_id} if operation_id else {}
        return [_clean(item) for item in self.db.state_events.find(query, {"_id": 0}).sort("scenario_time", self._ascending)]

    def list_reports(self) -> list[dict]:
        return [_clean(item) for item in self.db.reports.find({}, {"_id": 0}).sort("scenario_time", self._ascending)]

    def upsert_blindspot(self, blindspot: dict) -> None:
        self.db.blindspots.replace_one({"blindspot_id": blindspot["blindspot_id"]}, copy.deepcopy(blindspot), upsert=True)

    def get_blindspot(self, blindspot_id: str) -> dict | None:
        return _clean(self.db.blindspots.find_one({"blindspot_id": blindspot_id}, {"_id": 0}))

    def find_open_blindspot_for_operation(self, operation_id: str) -> dict | None:
        return _clean(self.db.blindspots.find_one({"operation_id": operation_id, "status": "OPEN"}, {"_id": 0}))

    def list_blindspots(self, status: str | None = None) -> list[dict]:
        query = {"status": status} if status else {}
        return [_clean(item) for item in self.db.blindspots.find(query, {"_id": 0}).sort("blindspot_id", self._ascending)]

    def set_app_state(self, key: str, value: dict) -> None:
        self.db.app_state.replace_one({"key": key}, {"key": key, "value": copy.deepcopy(value)}, upsert=True)

    def get_app_state(self, key: str) -> dict | None:
        row = self.db.app_state.find_one({"key": key}, {"_id": 0})
        return copy.deepcopy(row["value"]) if row else None


class InMemoryMongoService:
    def __init__(self):
        self.reset()

    def ensure_indexes(self) -> None:
        return None

    def reset(self) -> None:
        self.reports = {}
        self.operations = {}
        self.state_events = {}
        self.blindspots = {}
        self.dispatches = {}
        self.app_state = {}

    def insert_report_once(self, report: dict) -> bool:
        key = report["report_id"]
        if key in self.reports:
            return False
        self.reports[key] = copy.deepcopy(report)
        return True

    def upsert_operation(self, operation: dict) -> None:
        self.operations[operation["operation_id"]] = copy.deepcopy(operation)

    def get_operation(self, operation_id: str) -> dict | None:
        return copy.deepcopy(self.operations.get(operation_id))

    def get_operation_by_resource(self, resource_id: str) -> dict | None:
        matches = [op for op in self.operations.values() if op.get("resource_id") == resource_id]
        return copy.deepcopy(matches[0]) if len(matches) == 1 else None

    def list_operations(self) -> list[dict]:
        return [copy.deepcopy(self.operations[k]) for k in sorted(self.operations)]

    def insert_state_event_once(self, event: dict) -> bool:
        key = (event["report_id"], event["operation_id"], event["new_state"])
        if key in self.state_events:
            return False
        self.state_events[key] = copy.deepcopy(event)
        return True

    def list_state_events(self, operation_id: str | None = None) -> list[dict]:
        events = list(self.state_events.values())
        if operation_id:
            events = [event for event in events if event["operation_id"] == operation_id]
        return sorted(copy.deepcopy(events), key=lambda event: event["scenario_time"])

    def list_reports(self) -> list[dict]:
        return sorted(copy.deepcopy(list(self.reports.values())), key=lambda report: report["scenario_time"])

    def upsert_blindspot(self, blindspot: dict) -> None:
        self.blindspots[blindspot["blindspot_id"]] = copy.deepcopy(blindspot)

    def get_blindspot(self, blindspot_id: str) -> dict | None:
        return copy.deepcopy(self.blindspots.get(blindspot_id))

    def find_open_blindspot_for_operation(self, operation_id: str) -> dict | None:
        for blindspot in self.blindspots.values():
            if blindspot["operation_id"] == operation_id and blindspot["status"] == "OPEN":
                return copy.deepcopy(blindspot)
        return None

    def list_blindspots(self, status: str | None = None) -> list[dict]:
        rows = list(self.blindspots.values())
        if status:
            rows = [row for row in rows if row["status"] == status]
        return sorted(copy.deepcopy(rows), key=lambda row: row["blindspot_id"])

    def set_app_state(self, key: str, value: dict) -> None:
        self.app_state[key] = copy.deepcopy(value)

    def get_app_state(self, key: str) -> dict | None:
        return copy.deepcopy(self.app_state.get(key))


def _clean(row: dict | None) -> dict | None:
    if not row:
        return None
    row = dict(row)
    row.pop("_id", None)
    return row
