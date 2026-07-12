from dataclasses import dataclass


@dataclass(frozen=True)
class StateEvent:
    operation_id: str
    entity_id: str | None
    previous_state: str | None
    new_state: str
    evidence: str
    confidence: float
    scenario_time: str
    report_id: str
