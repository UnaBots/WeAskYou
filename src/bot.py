#!/usr/bin/env python3
"""Discord bot: posts a daily discussion question and answers /ask.

A single always-on process (a real gateway bot), replacing the old
GitHub Actions cron + webhook setup. One connection both schedules the
daily post and handles the /ask slash command.
"""
import os
from datetime import datetime, time as dtime

import discord
from discord.ext import commands, tasks

from service.reddit import get_question
from state import load_state, save_state
from util.date import TIMEZONE, parse_target_time

CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
DAILY_POST_TIME = parse_target_time().replace(tzinfo=TIMEZONE)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def already_posted_today() -> bool:
    today = datetime.now(TIMEZONE).date().isoformat()
    return load_state().get("last_posted_date") == today


def mark_posted_today() -> None:
    today = datetime.now(TIMEZONE).date().isoformat()
    save_state({"last_posted_date": today})


@tasks.loop(time=DAILY_POST_TIME)
async def daily_post() -> None:
    if already_posted_today():
        return

    question = get_question()
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(question)
    mark_posted_today()
    print(f"Posted: {question!r}")


@daily_post.before_loop
async def before_daily_post() -> None:
    await bot.wait_until_ready()


@bot.tree.command(name="ask", description="Ask for a new discussion question right now")
async def ask(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    question = get_question(random_fallback=True)
    await interaction.followup.send(question)


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")

    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()

    if not daily_post.is_running():
        daily_post.start()


def main() -> None:
    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
