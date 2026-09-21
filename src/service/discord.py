"""Posting to Discord via an incoming webhook."""
import os

import requests


def post_to_discord(question: str) -> None:
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    response = requests.post(
        webhook_url, json={"content": question}, timeout=10
    )
    response.raise_for_status()
