# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-purpose bot: post one discussion question to a Discord channel per day, sourced live from r/AskReddit with a local JSON fallback. There is no persistent process — a GitHub Actions cron job polls every 5 minutes, and `src/main.py` decides on each invocation whether it's actually time to post.

## Commands

- Install dependencies: `pip install -r requirements.txt`
- Local dry run (no-op unless it's past `TARGET_TIME` and not yet posted today): `python src/main.py`
- Force a run past the time gate for testing: `TARGET_TIME=00:00 python src/main.py` (requires `DISCORD_WEBHOOK_URL` set, or it will fail when it reaches the post step)
- Validate the JSON data files: `python -c "import json; json.load(open('questions.json')); json.load(open('state.json'))"`
- Trigger the workflow manually instead of waiting for the cron: `gh workflow run post_question.yml`

No test suite, linter, or build step exists in this repo.

## Architecture

See `README.md` for the full diagram and design notes (fallback chain, why it's a webhook and not a gateway bot, timezone handling). Key points for making changes:

- **Idempotency lives in `state.json`**, not in the workflow. `last_posted_date` is the single source of truth for "have we posted today"; the workflow commits this file back to the repo after a successful post specifically so the *next* cron tick (5 minutes later) sees the updated state and skips.
- **Time gating uses `Europe/Amsterdam` via `zoneinfo`** (stdlib, no dependency) rather than UTC, so DST transitions don't need manual handling. `TARGET_TIME` (env var, default `09:00`) is compared against wall-clock time in that zone.
- **Question sourcing is a fallback chain, not a single source**: `fetch_reddit_question()` hits Reddit's public JSON endpoint (no API key) and filters for a question-shaped, non-stickied, non-NSFW title; any failure (network error, HTTP error, no qualifying post) falls through to `fallback_question()`, which indexes into `questions.json` by day-of-year so it cycles without repeats until the list wraps.
- **The workflow only commits when `state.json` actually changed** (`git diff --quiet` check), so the 5-minute polling doesn't create empty commits — only the one run per day that actually posts produces a commit.
- Required secret: `DISCORD_WEBHOOK_URL`. Optional repo variable: `TARGET_TIME`.
