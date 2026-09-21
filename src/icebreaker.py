"""Question sourcing: live Parabol icebreaker API with a local JSON fallback."""
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from date import TIMEZONE

QUESTIONS_PATH = Path(__file__).parent.parent / "questions.json"
ICEBREAKER_URL = "https://icebreakers.parabol.co/api/icebreaker/random"
USER_AGENT = "WeAskYou/1.0 (daily discussion question bot)"


def fetch_icebreaker_question() -> Optional[str]:
    response = requests.get(
        ICEBREAKER_URL, headers={"User-Agent": USER_AGENT}, timeout=10
    )
    response.raise_for_status()
    return response.json().get("icebreaker", {}).get("question")


def fallback_question(random_pick: bool = False) -> str:
    questions = json.loads(QUESTIONS_PATH.read_text())
    if random_pick:
        return random.choice(questions)
    day_of_year = datetime.now(TIMEZONE).timetuple().tm_yday
    return questions[day_of_year % len(questions)]


def get_question(random_fallback: bool = False) -> str:
    try:
        question = fetch_icebreaker_question()
        if question:
            print("Using question from the icebreaker API.")
            return question
        print("Icebreaker API returned nothing usable, using fallback.")
    except requests.RequestException as exc:
        print(f"Icebreaker API fetch failed ({exc}), using fallback.")
    return fallback_question(random_pick=random_fallback)
