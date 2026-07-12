from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    report_id: str
    scenario_id: str
    scenario_time: str
    source: str
    channel: str
    raw_text: str
    ground_truth: dict | None = None
