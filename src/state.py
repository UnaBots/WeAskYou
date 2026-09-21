"""Read/write state.json, the source of truth for "posted today"."""
import json
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "state.json"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_posted_date": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")
