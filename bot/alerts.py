from dataclasses import dataclass
from decimal import Decimal

from bot import config


@dataclass
class Condition:
    key: str                  # unique ID, used in state.py and log messages
    pair: tuple[str, str]     # ("PAXG", "XAUT") — logical names, not raw tickers
    direction: str            # "above" | "below"
    threshold: Decimal
    reset_buffer: Decimal
    short_leg: str            # label for the Short button
    long_leg: str             # label for the Long button
    alert_emoji: str          # leading emoji for the Telegram message


CONDITIONS = [
    Condition(
        key="PAXG_XAUT_HIGH", pair=("PAXG", "XAUT"), direction="above",
        threshold=config.PAXG_XAUT_HIGH, reset_buffer=config.RESET_BUFFER,
        short_leg="PAXG", long_leg="XAUT", alert_emoji="🔴",
    ),
    Condition(
        key="PAXG_XAUT_LOW", pair=("PAXG", "XAUT"), direction="below",
        threshold=config.PAXG_XAUT_LOW, reset_buffer=config.RESET_BUFFER,
        short_leg="XAUT", long_leg="PAXG", alert_emoji="🟢",
    ),
    Condition(
        key="XAU_XAUT_HIGH", pair=("XAU", "XAUT"), direction="above",
        threshold=config.XAU_XAUT_HIGH, reset_buffer=config.RESET_BUFFER,
        short_leg="XAU", long_leg="XAUT", alert_emoji="🔴",
    ),
    Condition(
        key="XAU_XAUT_LOW", pair=("XAU", "XAUT"), direction="below",
        threshold=config.XAU_XAUT_LOW, reset_buffer=config.RESET_BUFFER,
        short_leg="XAUT", long_leg="XAU", alert_emoji="🟢",
    ),
]


def evaluate(cond: Condition, value: Decimal, armed: bool) -> tuple[bool, bool]:
    """
    Returns (should_fire, new_armed).
    Fires once when the condition is met and state is armed, then disarms.
    Re-arms silently when spread retreats past threshold ± reset_buffer.
    """
    if cond.direction == "above":
        triggered  = value > cond.threshold
        rearm_zone = value < (cond.threshold - cond.reset_buffer)
    else:
        triggered  = value < cond.threshold
        rearm_zone = value > (cond.threshold + cond.reset_buffer)

    if triggered and armed:
        return True, False      # fire + disarm
    if rearm_zone and not armed:
        return False, True      # silently re-arm
    return False, armed         # no change
