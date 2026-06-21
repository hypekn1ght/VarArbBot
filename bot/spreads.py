from decimal import Decimal
from typing import Optional

from bot.variational import Listing


def mark_spread(a: Listing, b: Listing) -> Decimal:
    """a.mark − b.mark. Used for alert triggering."""
    return a.mark - b.mark


def executable_spread_short_a_long_b(a: Listing, b: Listing) -> Optional[Decimal]:
    """
    Spread captured by shorting A (hitting bid) and longing B (lifting ask).
    Returns None if either side's quote is unavailable.
    """
    if a.bid_1k is None or b.ask_1k is None:
        return None
    return a.bid_1k - b.ask_1k
