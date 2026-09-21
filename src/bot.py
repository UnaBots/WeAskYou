#!/usr/bin/env python3
"""Discord bot: posts a daily discussion question and answers /ask.

A single always-on process (a real gateway bot), replacing the old
GitHub Actions cron + webhook setup. One connection both schedules the
daily post and handles the /ask slash command.
"""
from __future__ import annotations

import os

import discord
from discord.ext import commands, tasks

from date import TIMEZONE, parse_target_time
from icebreaker import get_question
from state import already_posted_today, get_channel_id, mark_posted_today, set_channel_id

GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
DAILY_POST_TIME = parse_target_time().replace(tzinfo=TIMEZONE)
DEFAULT_CHANNEL_NAME = "general"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def resolve_channel() -> discord.abc.Messageable | None:
    """The configured channel, falling back to one named "general"."""
    channel_id = get_channel_id()
    if channel_id is not None:
        channel = bot.get_channel(channel_id)
        if channel is not None:
            return channel

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=DEFAULT_CHANNEL_NAME)
        if channel is not None:
            return channel

    return None


@tasks.loop(time=DAILY_POST_TIME)
async def daily_post() -> None:
    if already_posted_today():
        return

    channel = resolve_channel()
    if channel is None:
        print("No target channel configured or found; skipping daily post.")
        return

    question = get_question()
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


@bot.tree.command(name="setchannel", description="Set the channel for the daily discussion question")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.describe(channel="The channel to post the daily question in")
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
    set_channel_id(channel.id)
    await interaction.response.send_message(f"Daily question channel set to {channel.mention}.")


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
