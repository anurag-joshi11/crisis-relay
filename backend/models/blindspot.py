from dataclasses import dataclass


@dataclass(frozen=True)
class Blindspot:
    blindspot_id: str
    operation_id: str
    resource_id: str
    type: str
    severity: str
    status: str
    minutes_in_state: int
    reason: str
