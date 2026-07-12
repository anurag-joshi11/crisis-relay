import json
from pathlib import Path

from backend.demo.scenario_runner import ScenarioRunner
from backend.services.mongodb_service import InMemoryMongoService

ROOT = Path(__file__).resolve().parents[2]


def build_runner():
    return ScenarioRunner(store=InMemoryMongoService())


def advance_to(runner, report_id):
    while True:
        status = runner.next_event()
        if status["reports"] and status["reports"][-1]["report_id"] == report_id:
            return status


def test_duplicate_report_processing_does_not_duplicate_events():
    runner = build_runner()
    runner.reset()
    report = _reports()[0]
    first = runner.ingestion.ingest_report(report)
    second = runner.ingestion.ingest_report(report)
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert len(runner.store.list_state_events()) == 2


def test_runner_seeds_operations_on_startup_without_reset():
    runner = build_runner()
    operations = runner.store.list_operations()
    assert {operation["operation_id"] for operation in operations} == {
        "OP-EVAC-001",
        "OP-WATER-001",
        "OP-POWER-001",
    }


def test_bus_7_not_updated_by_outcomes_or_assumptions_through_rpt_024():
    runner = build_runner()
    runner.reset()
    advance_to(runner, "RPT-024")
    bus = runner.store.get_operation("OP-EVAC-001")
    assert bus["current_state"] == "DISPATCHED"
    assert bus["fulfilled"] is False


def test_tanker_critical_unconfirmed_at_1044():
    runner = build_runner()
    runner.reset()
    status = advance_to(runner, "RPT-020")
    tanker = runner.store.get_operation("OP-WATER-001")
    assert tanker["current_state"] == "DISPATCHED"
    blindspots = [b for b in status["blindspots"] if b["operation_id"] == "OP-WATER-001"]
    assert blindspots
    assert blindspots[0]["severity"] == "CRITICAL"
    assert blindspots[0]["minutes_in_state"] == 31


def test_rpt_026_holding_records_blocker_and_unfulfilled():
    runner = build_runner()
    runner.reset()
    advance_to(runner, "RPT-026")
    tanker = runner.store.get_operation("OP-WATER-001")
    assert tanker["current_state"] == "HOLDING"
    assert tanker["fulfilled"] is False
    assert tanker["blockers"][-1]["type"] == "VISIBILITY"


def test_generator_ends_verified_and_fulfilled():
    runner = build_runner()
    runner.reset()
    advance_to(runner, "RPT-030")
    generator = runner.store.get_operation("OP-POWER-001")
    assert generator["current_state"] == "VERIFIED"
    assert generator["fulfilled"] is True


def test_demo_reset_repeatable_and_status_contract_shape():
    runner = build_runner()
    status = runner.reset()
    status = runner.next_event()
    status = runner.reset()
    assert status["demo"]["event_index"] == 0
    assert set(status) == {"scenario", "reports", "operations", "blindspots", "selected_timeline", "demo"}


def test_dashboard_nested_shapes_match_contract():
    runner = build_runner()
    runner.reset()
    status = advance_to(runner, "RPT-020")

    assert set(status["reports"][0]) == {"report_id", "scenario_time", "source", "channel", "raw_text"}
    assert set(status["operations"][0]) == {
        "operation_id",
        "operation_type",
        "location",
        "resource_id",
        "current_state",
        "priority",
        "fulfilled",
        "need_still_active",
        "last_state_change",
    }
    assert set(status["blindspots"][0]) == {
        "blindspot_id",
        "operation_id",
        "resource_id",
        "type",
        "severity",
        "status",
        "minutes_in_state",
        "reason",
    }


def _reports():
    with (ROOT / "dataset" / "wildfire_scenario.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)
