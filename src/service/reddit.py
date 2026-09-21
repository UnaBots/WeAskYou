"""Question sourcing: live r/AskReddit lookup with a local JSON fallback."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from util.date import TIMEZONE

QUESTIONS_PATH = Path(__file__).parent.parent.parent / "questions.json"
REDDIT_URL = "https://www.reddit.com/r/AskReddit/hot.json?limit=25"
USER_AGENT = "WeAskYou/1.0 (daily discussion question bot)"


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
