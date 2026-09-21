#!/usr/bin/env python3
"""Post one daily discussion question to a Discord channel via webhook.

Intended to run on a frequent cron (e.g. every 5 minutes) from GitHub
Actions. Each run checks whether it's actually time to post, based on
TARGET_TIME and state.json, so at most one post happens per day.
"""
import json
import os
import sys
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import requests

TIMEZONE = ZoneInfo("Europe/Amsterdam")
STATE_PATH = Path(__file__).parent / "state.json"
QUESTIONS_PATH = Path(__file__).parent / "questions.json"
REDDIT_URL = "https://www.reddit.com/r/AskReddit/hot.json?limit=25"
USER_AGENT = "WeAskYou/1.0 (daily discussion question bot)"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_posted_date": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def parse_target_time() -> dtime:
    raw = os.environ.get("TARGET_TIME", "09:00")
    hour, minute = (int(part) for part in raw.split(":"))
    return dtime(hour=hour, minute=minute)


def fetch_reddit_question() -> Optional[str]:
    response = requests.get(
        REDDIT_URL, headers={"User-Agent": USER_AGENT}, timeout=10
    )
    response.raise_for_status()
    posts = response.json()["data"]["children"]
    for post in posts:
        data = post["data"]
        title = data.get("title", "").strip()
        if not title.endswith("?"):
            continue
        if data.get("stickied") or data.get("over_18"):
            continue
        return title
    return None


def fallback_question() -> str:
    questions = json.loads(QUESTIONS_PATH.read_text())
    day_of_year = datetime.now(TIMEZONE).timetuple().tm_yday
    return questions[day_of_year % len(questions)]


def get_question() -> str:
    try:
        question = fetch_reddit_question()
        if question:
            print("Using question from r/AskReddit.")
            return question
        print("No suitable r/AskReddit post found, using fallback.")
    except requests.RequestException as exc:
        print(f"r/AskReddit fetch failed ({exc}), using fallback.")
    return fallback_question()


def post_to_discord(question: str) -> None:
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    response = requests.post(
        webhook_url, json={"content": question}, timeout=10
    )
    response.raise_for_status()


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
