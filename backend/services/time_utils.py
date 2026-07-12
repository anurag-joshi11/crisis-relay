def minutes_since_midnight(value: str) -> int:
    hours, minutes = value.split(":", 1)
    return int(hours) * 60 + int(minutes)


def elapsed_minutes(start: str | None, end: str) -> int:
    if not start:
        return 0
    return max(0, minutes_since_midnight(end) - minutes_since_midnight(start))
