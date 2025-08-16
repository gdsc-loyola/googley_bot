"""
Script to load and register all application commands (slash commands)
across the bot. This script is executed during startup.
"""

import asyncio
import logging

from discord.ext import commands
from src.bot.client import bot

# List of command cogs to load
COMMAND_MODULES = [
    "src.commands.github",
    "src.commands.notion",
    "src.commands.sheets",
]


async def setup_commands():
    logging.info("Setting up command modules...")
    for module in COMMAND_MODULES:
        try:
            await bot.load_extension(module)
            logging.info(f"Loaded module: {module}")
        except Exception as e:
            logging.error(f"Failed to load {module}: {e}")

    # Sync commands globally or to a test guild
    try:
        await bot.tree.sync()
        logging.info("✅ Slash commands synced globally")
    except Exception as e:
        logging.error(f"❌ Failed to sync commands: {e}")


if __name__ == "__main__":
    asyncio.run(setup_commands())
