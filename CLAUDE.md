# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Discord bot: posts one discussion question per day, sourced live from the Parabol icebreaker API with a local JSON fallback, and answers `/ask` with a fresh question on demand. It's a real gateway bot (`discord.py`) — an always-on process, run on a VPS, not a stateless GitHub Actions cron.

## Commands

- Install dependencies: `pip install -r requirements.txt`
- Run the bot: `python src/bot.py` (requires `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` set; see README.md Setup)
- Validate the JSON data files: `python -c "import json; json.load(open('questions.json')); json.load(open('state.json'))"`
- Dry-run question sourcing without connecting to Discord: `python -c "import sys; sys.path.insert(0, 'src'); from icebreaker import get_question; print(get_question())"`

No test suite, linter, or build step exists in this repo.

## Architecture

See `README.md` for the full diagram and design notes (fallback chain, why it's a gateway bot and not a webhook, timezone handling). Key points for making changes:

- **`src/bot.py`** is the entrypoint: a single `discord.py` `commands.Bot` process. It schedules the daily post via `discord.ext.tasks.loop(time=...)` and handles the `/ask` slash command — both reuse `icebreaker.get_question()`.
- **Idempotency lives in `state.json`**, read/written by `src/state.py`. `last_posted_date` guards against a double post if the bot restarts on the same day; it's a local file on the host now, not something committed back to the repo (the old GitHub Actions cron needed that to survive between stateless runs — a persistent process doesn't).
- **Time gating uses `Europe/Amsterdam` via `zoneinfo`** (stdlib, no dependency), attached as `tzinfo` on the `time` object passed to `tasks.loop`, so `discord.py` fires at the right wall-clock time across DST transitions. `TARGET_TIME` (env var, default `09:00`) is parsed in `src/date.py`.
- **Question sourcing is a fallback chain, not a single source** (`src/icebreaker.py`): `fetch_icebreaker_question()` hits `icebreakers.parabol.co/api/icebreaker/random` (no API key). This replaced an earlier r/AskReddit source — Reddit's anti-bot system blocks anonymous requests from most cloud/hosting IP ranges (confirmed via a "blocked by network security" response), which is exactly the kind of IP a VPS has, and OAuth felt like unnecessary complexity once a simpler, no-auth API was available. Any failure (network error, HTTP error, malformed response) falls through to `fallback_question()`, which indexes into `questions.json` by day-of-year for the daily post (deterministic) or picks randomly for `/ask` (so repeated on-demand use doesn't return the same question all day), cycling without repeats until the list wraps.
- Required env vars: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`. Optional: `DISCORD_GUILD_ID` (fast slash-command sync while developing), `TARGET_TIME`.
