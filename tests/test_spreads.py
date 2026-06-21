from decimal import Decimal
from datetime import datetime, timezone

import pytest

from bot.variational import Listing
from bot.spreads import mark_spread, executable_spread_short_a_long_b


def make_listing(mark, bid=None, ask=None):
    return Listing(
        ticker="TEST",
        mark=Decimal(str(mark)),
        bid_1k=Decimal(str(bid)) if bid is not None else None,
        ask_1k=Decimal(str(ask)) if ask is not None else None,
        updated_at=datetime.now(timezone.utc),
    )


def test_mark_spread_positive():
    a = make_listing("3342.50")
    b = make_listing("3319.80")
    result = mark_spread(a, b)
    assert result == Decimal("22.70")
    assert type(result) is Decimal


def test_mark_spread_negative():
    a = make_listing("3300.00")
    b = make_listing("3319.80")
    result = mark_spread(a, b)
    assert result == Decimal("-19.80")
    assert type(result) is Decimal


def test_mark_spread_zero():
    a = make_listing("3319.80")
    b = make_listing("3319.80")
    assert mark_spread(a, b) == Decimal("0")


def test_executable_spread_with_quotes():
    a = make_listing("3342.50", bid="3341.00", ask="3344.00")
    b = make_listing("3319.80", bid="3318.50", ask="3321.10")
    # short A (hit bid 3341.00), long B (lift ask 3321.10)
    result = executable_spread_short_a_long_b(a, b)
    assert result == Decimal("3341.00") - Decimal("3321.10")
    assert type(result) is Decimal


def test_executable_spread_missing_bid():
    a = make_listing("3342.50", bid=None, ask="3344.00")
    b = make_listing("3319.80", bid="3318.50", ask="3321.10")
    assert executable_spread_short_a_long_b(a, b) is None


def test_executable_spread_missing_ask():
    a = make_listing("3342.50", bid="3341.00", ask="3344.00")
    b = make_listing("3319.80", bid="3318.50", ask=None)
    assert executable_spread_short_a_long_b(a, b) is None


def test_executable_spread_both_missing():
    a = make_listing("3342.50")
    b = make_listing("3319.80")
    assert executable_spread_short_a_long_b(a, b) is None


def test_no_float_in_spreads():
    a = make_listing("3342.50", bid="3341.00", ask="3344.00")
    b = make_listing("3319.80", bid="3318.50", ask="3321.10")
    ms = mark_spread(a, b)
    es = executable_spread_short_a_long_b(a, b)
    assert type(ms) is Decimal
    assert type(es) is Decimal
    # Confirm no float leakage in inputs
    assert type(a.mark) is Decimal
    assert type(b.mark) is Decimal
    assert type(a.bid_1k) is Decimal
    assert type(b.ask_1k) is Decimal
