#!/usr/bin/env python3
"""Post one daily discussion question to a Discord channel via webhook.

Intended to run on a frequent cron (e.g. every 5 minutes) from GitHub
Actions. Each run checks whether it's actually time to post, based on
TARGET_TIME and state.json, so at most one post happens per day.
"""
import sys
from datetime import datetime

from service.discord import post_to_discord
from service.reddit import get_question
from state import load_state, save_state
from util.date import TIMEZONE, parse_target_time


def main() -> int:
    now = datetime.now(TIMEZONE)
    today = now.date().isoformat()

    state = load_state()
    if state.get("last_posted_date") == today:
        print(f"Already posted today ({today}). Skipping.")
        return 0

    if now.time() < parse_target_time():
        due_time = now.time().isoformat(timespec="minutes")
        print(f"Not due yet ({due_time}). Skipping.")
        return 0

    question = get_question()
    post_to_discord(question)
    print(f"Posted: {question!r}")

    save_state({"last_posted_date": today})
    return 0


if __name__ == "__main__":
    sys.exit(main())
