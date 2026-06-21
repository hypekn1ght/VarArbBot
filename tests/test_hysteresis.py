from decimal import Decimal

import pytest

from bot.alerts import Condition, evaluate


COND_HIGH = Condition(
    key="PAXG_XAUT_HIGH",
    pair=("PAXG", "XAUT"),
    direction="above",
    threshold=Decimal("20"),
    reset_buffer=Decimal("2"),
    short_leg="PAXG",
    long_leg="XAUT",
    alert_emoji="🔴",
)

COND_LOW = Condition(
    key="PAXG_XAUT_LOW",
    pair=("PAXG", "XAUT"),
    direction="below",
    threshold=Decimal("10"),
    reset_buffer=Decimal("2"),
    short_leg="XAUT",
    long_leg="PAXG",
    alert_emoji="🟢",
)


def test_hysteresis_sequence_above():
    """
    Fires once on threshold crossing, stays silent above, re-arms
    below rearm zone (threshold - buffer = 18), fires again.
    """
    sequence = [
        # (spread, expected_should_fire, armed_after)
        (Decimal("15"), False, True),   # below threshold, still armed
        (Decimal("21"), True,  False),  # crosses > 20, FIRE, disarm
        (Decimal("22"), False, False),  # still above, disarmed → silent
        (Decimal("19"), False, False),  # below 20 but not past rearm zone (18)
        (Decimal("17"), False, True),   # crosses < 18 → re-arms silently
        (Decimal("21"), True,  False),  # crosses > 20 again, FIRE
    ]

    armed = True
    for spread, expected_fire, expected_armed_after in sequence:
        should_fire, armed = evaluate(COND_HIGH, spread, armed)
        assert should_fire == expected_fire, \
            f"spread={spread}: expected fire={expected_fire}, got {should_fire}"
        assert armed == expected_armed_after, \
            f"spread={spread}: expected armed={expected_armed_after}, got {armed}"


def test_hysteresis_no_double_fire():
    """Once fired, must not fire again until re-armed."""
    armed = True
    _, armed = evaluate(COND_HIGH, Decimal("21"), armed)  # fire + disarm
    assert not armed

    for _ in range(5):
        should_fire, armed = evaluate(COND_HIGH, Decimal("25"), armed)
        assert not should_fire
        assert not armed


def test_hysteresis_rearm_then_fire():
    """Confirm re-arm zone boundary: threshold - buffer = 18."""
    armed = True
    _, armed = evaluate(COND_HIGH, Decimal("21"), armed)  # fire
    assert not armed

    # value at exactly threshold-buffer (18) — NOT in rearm zone (must be strictly less)
    _, armed = evaluate(COND_HIGH, Decimal("18"), armed)
    assert not armed

    # value below rearm zone
    _, armed = evaluate(COND_HIGH, Decimal("17.99"), armed)
    assert armed  # re-armed

    should_fire, armed = evaluate(COND_HIGH, Decimal("21"), armed)
    assert should_fire
    assert not armed


def test_hysteresis_sequence_below():
    """Mirror test for 'below' direction."""
    sequence = [
        (Decimal("15"), False, True),   # above threshold, still armed
        (Decimal("9"),  True,  False),  # crosses < 10, FIRE, disarm
        (Decimal("8"),  False, False),  # still below, disarmed
        (Decimal("11"), False, False),  # above 10 but not past rearm zone (12)
        (Decimal("13"), False, True),   # crosses > 12 → re-arms silently
        (Decimal("9"),  True,  False),  # crosses < 10, FIRE again
    ]

    armed = True
    for spread, expected_fire, expected_armed_after in sequence:
        should_fire, armed = evaluate(COND_LOW, spread, armed)
        assert should_fire == expected_fire, \
            f"spread={spread}: expected fire={expected_fire}, got {should_fire}"
        assert armed == expected_armed_after, \
            f"spread={spread}: expected armed={expected_armed_after}, got {armed}"


def test_evaluate_returns_tuple():
    result = evaluate(COND_HIGH, Decimal("25"), True)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], bool)
