#!/usr/bin/env python3
"""Main entry point for Googley Bot."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bot.client import GoogleyBot
from src.utils.logger import logger
from src.utils.config import settings


async def main() -> None:
    """Main async function to run the bot."""
    logger.info("🚀 Starting Googley Bot...")
    logger.info(f"🐍 Python {sys.version}")
    logger.info(f"🏠 Project root: {project_root}")
    logger.info(f"🔧 Development mode: {settings.development_mode}")

    # Create and start bot
    bot = GoogleyBot()

    try:
        await bot.start_bot()
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⌨️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
