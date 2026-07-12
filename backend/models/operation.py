from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    operation_id: str
    operation_type: str
    location: str
    resource_id: str
    current_state: str | None = None
    priority: str = "HIGH"
    fulfilled: bool = False
    need_still_active: bool = False
    last_state_change: str | None = None
