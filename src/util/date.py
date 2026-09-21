"""Timezone and time-gating helpers, all in Europe/Amsterdam wall-clock time."""
import os
from datetime import time as dtime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Amsterdam")


def parse_target_time() -> dtime:
    raw = os.environ.get("TARGET_TIME", "09:00")
    hour, minute = (int(part) for part in raw.split(":"))
    return dtime(hour=hour, minute=minute)
