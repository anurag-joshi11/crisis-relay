def default_priority(operation_type: str) -> str:
    if operation_type == "WATER_DROP":
        return "CRITICAL"
    return "HIGH"


def blindspot_severity(operation: dict) -> str:
    if operation.get("need_still_active"):
        return "CRITICAL"
    return operation.get("priority") or "HIGH"
