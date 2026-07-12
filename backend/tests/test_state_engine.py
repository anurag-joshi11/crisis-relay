from backend.services.state_engine import evaluate_unconfirmed, is_transition_allowed


def test_required_transitions():
    assert is_transition_allowed("REQUESTED", "ASSIGNED")
    assert is_transition_allowed("ASSIGNED", "DISPATCHED")
    assert is_transition_allowed("DISPATCHED", "ARRIVED")
    assert is_transition_allowed("DISPATCHED", "HOLDING")
    assert is_transition_allowed("HOLDING", "ARRIVED")


def test_rejected_transitions():
    assert not is_transition_allowed("DISPATCHED", "COMPLETED")
    assert not is_transition_allowed("VERIFIED", "ARRIVED")


def test_unconfirmed_demo_thresholds_and_active_need():
    operation = {"current_state": "DISPATCHED", "fulfilled": False, "priority": "HIGH", "need_still_active": True}
    result = evaluate_unconfirmed(operation, 31)
    assert result["alert"] is True
    assert result["type"] == "UNCONFIRMED"
    assert result["severity"] == "CRITICAL"


def test_terminal_state_has_no_alert():
    operation = {"current_state": "VERIFIED", "fulfilled": True}
    assert evaluate_unconfirmed(operation, 90)["alert"] is False


def test_assumptions_do_not_advance_state():
    assert not is_transition_allowed("DISPATCHED", None)
