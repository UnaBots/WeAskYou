"""Read/write state.json, the source of truth for "posted today"."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from date import TIMEZONE

STATE_PATH = Path(__file__).parent.parent / "state.json"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_posted_date": None, "channel_id": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def already_posted_today() -> bool:
    today = datetime.now(TIMEZONE).date().isoformat()
    return load_state().get("last_posted_date") == today


def mark_posted_today() -> None:
    today = datetime.now(TIMEZONE).date().isoformat()
    state = load_state()
    state["last_posted_date"] = today
    save_state(state)


def get_channel_id() -> int | None:
    return load_state().get("channel_id")


def set_channel_id(channel_id: int) -> None:
    state = load_state()
    state["channel_id"] = channel_id
    save_state(state)
