from backend.services.priority_engine import blindspot_severity

TERMINAL_STATES = {"COMPLETED", "VERIFIED"}
THRESHOLDS_MINUTES = {
    "REQUESTED": 10,
    "ACKNOWLEDGED": 15,
    "ASSIGNED": 20,
    "DISPATCHED": 25,
    "ARRIVED": 30,
    "HOLDING": 10,
}

ALLOWED_TRANSITIONS = {
    None: {"REQUESTED"},
    "REQUESTED": {"ACKNOWLEDGED", "ASSIGNED"},
    "ACKNOWLEDGED": {"ASSIGNED"},
    "ASSIGNED": {"DISPATCHED"},
    "DISPATCHED": {"ARRIVED", "HOLDING"},
    "HOLDING": {"DISPATCHED", "ARRIVED"},
    "ARRIVED": {"COMPLETED"},
    "COMPLETED": {"VERIFIED"},
    "VERIFIED": set(),
}


def is_transition_allowed(current_state: str | None, new_state: str | None) -> bool:
    if not new_state:
        return False
    if current_state == new_state:
        return current_state != "VERIFIED"
    return new_state in ALLOWED_TRANSITIONS.get(current_state, set())


def fulfilled_for_state(state: str | None, current: bool = False) -> bool:
    if state in TERMINAL_STATES:
        return True
    return current


def evaluate_unconfirmed(operation: dict, minutes_in_state: int) -> dict:
    state = operation.get("current_state")
    if state in TERMINAL_STATES or operation.get("fulfilled"):
        return {"alert": False}

    blocker_active = bool(operation.get("blockers"))
    threshold = THRESHOLDS_MINUTES.get(state)
    overdue = threshold is not None and minutes_in_state >= threshold
    if not overdue and not blocker_active:
        return {"alert": False}

    return {
        "alert": True,
        "type": "UNCONFIRMED",
        "severity": blindspot_severity(operation),
        "demo_heuristic": True,
    }
