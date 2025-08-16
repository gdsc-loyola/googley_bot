# src/bot/events.py
"""Custom event handlers for the GoogleyBot."""

import asyncio
import asyncpg
import discord
import json
from discord.ext import commands
from loguru import logger


class GoogleyEventHandlers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._listening = False
        self._listener_conn: asyncpg.Connection | None = None

    async def on_task_update(self, payload: str):
        """Handle task update notifications from Postgres."""
        try:
            data = json.loads(payload)
            discord_id = int(data["discord_id"])
            message = data.get("message", {})

            user = await self.bot.fetch_user(discord_id)

            embed = discord.Embed(
                title="🔔 Task Updated",
                description="There was an update to one of your tasks.",
                color=0x3498db,
            )
            embed.add_field(name="Task", value=message.get("title", "N/A"), inline=True)
            embed.add_field(name="Description", value=message.get("description", "N/A"), inline=True)
            embed.add_field(name="Status", value=message.get("status", "unknown").title().replace("_", " "), inline=True)
            embed.add_field(name="Due Date", value=message.get("due_date", "N/A"), inline=True)

            if user:
                await user.send(embed=embed)
                logger.info(f"📩 Task update DM sent to {discord_id}")
            else:
                logger.warning(f"⚠️ User with ID {discord_id} not found.")
        except Exception as e:
            logger.error(f"❌ Notification payload error: {e} | Payload: {payload}")

    async def on_task_completed(self, payload: str):
        """Handle task completed notifications from Postgres."""
        try:
            data = json.loads(payload)
            discord_id = int(data["discord_id"])
            task = data.get("message", {})

            user = await self.bot.fetch_user(discord_id)

            embed = discord.Embed(
                title="✅ Task Completed!",
                description=f"🎉 You just completed **{task.get('title', 'a task')}**!",
                color=0x2ecc71,
            )

            if user:
                await user.send(embed=embed)
                logger.info(f"📩 Task completed DM sent to {discord_id}")
            else:
                logger.warning(f"⚠️ User with ID {discord_id} not found.")
        except Exception as e:
            logger.error(f"❌ Completion payload error: {e} | Payload: {payload}")

    async def on_task_assigned(self, payload: str):
        """Handle task assigned notifications from Postgres."""
        try:
            data = json.loads(payload)
            discord_id = int(data["discord_id"])
            task = data.get("message", {})

            user = await self.bot.fetch_user(discord_id)

            embed = discord.Embed(
                title="📌 New Task Assigned!",
                description=f"You've been assigned a new task: **{task.get('title', 'Untitled Task')}**",
                color=0xf1c40f,
            )
            embed.add_field(name="Description", value=task.get("description", "N/A"), inline=False)
            embed.add_field(name="Due Date", value=task.get("due_date", "N/A"), inline=True)
            embed.add_field(name="Status", value=task.get("status", "unknown").title(), inline=True)

            if user:
                await user.send(embed=embed)
                logger.info(f"📩 Task assignment DM sent to {discord_id}")
            else:
                logger.warning(f"⚠️ User with ID {discord_id} not found.")
        except Exception as e:
            logger.error(f"❌ Assignment payload error: {e} | Payload: {payload}")

    async def start_postgres_listener(self, dsn: str):
        """Start listening for Postgres NOTIFY events."""
        if self._listening:
            logger.warning("⚠️ Already listening for PG notifications.")
            return

        try:
            self._listener_conn = await asyncpg.connect(dsn=dsn)
            logger.info("🔌 Connected to PostgreSQL. Listening for task updates...")

            def update_callback(conn, pid, channel, payload):
                asyncio.create_task(self.on_task_update(payload))

            def completed_callback(conn, pid, channel, payload):
                asyncio.create_task(self.on_task_completed(payload))

            def assigned_callback(conn, pid, channel, payload):
                asyncio.create_task(self.on_task_assigned(payload))

            await self._listener_conn.add_listener("task_update", update_callback)
            await self._listener_conn.add_listener("task_completed", completed_callback)
            await self._listener_conn.add_listener("task_assigned", assigned_callback)

            self._listening = True
            asyncio.create_task(self._keep_pg_alive())
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL or listen: {e}")

    async def _keep_pg_alive(self):
        """Keeps the connection alive to avoid GC and disconnection."""
        try:
            while True:
                await asyncio.sleep(60)
                await self._listener_conn.execute("SELECT 1")
        except Exception as e:
            logger.error(f"⚠️ Lost connection to PostgreSQL: {e}")
            self._listening = False


# Cog setup
async def setup(bot: commands.Bot):
    await bot.add_cog(GoogleyEventHandlers(bot))
