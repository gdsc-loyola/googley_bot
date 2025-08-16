"""Main Discord bot client implementation for GoogleyBot."""

import asyncio
import signal
import sys
import discord
from discord.ext import commands
from loguru import logger

from src.bot.events import GoogleyEventHandlers
from src.utils.config import settings
from src.utils.database import create_tables


class GoogleyBot(commands.Bot):
    """Main GoogleyBot client with enhanced functionality."""

    def __init__(self):
        """Initialize the bot with proper intents and configuration."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        intents.guild_reactions = True

        super().__init__(
            command_prefix=settings.discord_command_prefix,
            description=settings.discord_description,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True,
        )

        self.initial_extensions = [
            "src.commands.github",
            "src.commands.sheets",
            "src.commands.calendar",
            "src.commands.telegram",
            "src.commands.notion",
            "src.commands.standup",
            "src.commands.utils",
            "src.bot.events",
        ]

        self.db_ready = False
        self.shutdown_event = asyncio.Event()

        logger.info("🤖 Googley Bot initialized")

        @self.tree.command(name="test", description="Simple test command")
        async def test_command(interaction: discord.Interaction):
            await interaction.response.send_message("🎉 Test command works!")

    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting."""
        logger.info("⚙️ Running setup hook...")

        await self._setup_database()
        await self._load_extensions()

        # Sync commands
        if settings.development_mode:
            guild = discord.Object(id=int(settings.discord_guild_id))
            logger.info(f"🔍 Syncing commands to dev guild {settings.discord_guild_id}")
            try:
                self.tree.clear_commands(guild=guild)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"📋 Synced {len(synced)} commands to dev guild")
            except Exception as e:
                logger.error(f"❌ Failed to sync commands to dev guild: {e}")
        else:
            try:
                synced = await self.tree.sync()
                logger.info(f"🌍 Synced {len(synced)} commands globally")
            except Exception as e:
                logger.error(f"❌ Failed to sync commands globally: {e}")

        # Start Postgres listener
        handler = GoogleyEventHandlers(self)
        fixed_dsn = settings.database_url.replace("postgresql+asyncpg", "postgresql")
        await handler.start_postgres_listener(fixed_dsn)

    async def _setup_database(self) -> None:
        """Initialize database connection and tables."""
        try:
            logger.info("🗄️ Setting up database...")
            await create_tables()
            self.db_ready = True
            logger.success("✅ Database setup complete")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            self.db_ready = False
            raise

    async def _load_extensions(self) -> None:
        """Load all bot extensions (command modules)."""
        logger.info("📦 Loading extensions...")

        loaded, failed = 0, 0
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.debug(f"✅ Loaded extension: {ext}")
                loaded += 1
            except Exception as e:
                logger.error(f"❌ Failed to load {ext}: {e}")
                failed += 1

        logger.info(f"📦 Extensions loaded: {loaded} successful, {failed} failed")

    async def on_ready(self) -> None:
        """Called when bot is ready and connected."""
        logger.success(f"🚀 {self.user} is ready!")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        logger.info(f"👥 Serving {len(set(self.get_all_members()))} users")

        activity_type = getattr(
            discord.ActivityType,
            settings.discord_activity_type,
            discord.ActivityType.playing,
        )
        await self.change_presence(
            activity=discord.Activity(
                type=activity_type,
                name=settings.discord_activity_name,
            )
        )

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle command errors gracefully."""
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.DisabledCommand):
            await ctx.send("❌ This command is disabled.", ephemeral=True)
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Cannot use in DMs.", ephemeral=True)
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You lack permissions.", ephemeral=True)
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏰ Cooldown: retry in {error.retry_after:.2f} sec.", ephemeral=True
            )
            return

        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send("❌ Unexpected error. Please try later.", ephemeral=True)

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, self._signal_handler)
        else:
            signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        self.shutdown_event.set()

    async def start_bot(self) -> None:
        """Start the bot with proper error handling."""
        self.setup_signal_handlers()

        try:
            async with self:
                bot_task = asyncio.create_task(self.start(settings.discord_token))
                done, pending = await asyncio.wait(
                    [bot_task, asyncio.create_task(self.shutdown_event.wait())],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if self.shutdown_event.is_set():
                    logger.info("🛑 Shutdown signal received, closing bot...")
                    await self.close()
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        except discord.LoginFailure:
            logger.error("❌ Invalid Discord token")
            raise
        except discord.HTTPException as e:
            logger.error(f"❌ HTTP error: {e}")
            raise
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise
        finally:
            logger.info("🔄 Bot stopped")


def create_bot() -> GoogleyBot:
    """Factory function to create GoogleyBot instance."""
    return GoogleyBot()
