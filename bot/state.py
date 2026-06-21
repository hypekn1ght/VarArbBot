import json
import os
from datetime import datetime, timezone

from bot.alerts import CONDITIONS

STATE_FILE = "state.json"


def load() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    # Default: all conditions start armed (ready to fire)
    return {c.key: {"armed": True, "last_fired": None} for c in CONDITIONS}


def save(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_cooled_down(state: dict, key: str, cooldown_s: int) -> bool:
    last = state[key].get("last_fired")
    if last is None:
        return True
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
    return elapsed >= cooldown_s
