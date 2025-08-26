"""Notion integration Discord commands."""

from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from src.integrations.notion.client import get_notion_client
from src.models.notion import NotionTask, TaskPriority, TaskStatus
from src.utils.database import AsyncSessionLocal


class NotionCommands(commands.Cog):
    """Discord commands for Notion integration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    notion_group = app_commands.Group(
        name="notion", 
        description="Notion integration commands"
    )

    @notion_group.command(
        name="create", 
        description="Create a new task in Notion"
    )
    @app_commands.describe(
        task_name="The name/title of the task",
        description="Detailed description of the task",
        discord_user_id="Discord user ID (mention someone or use their ID)",
        priority="Task priority level"
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        task_name: str,
        description: str,
        discord_user_id: str,
        priority: str = "Medium"
    ):
        """Create a new task in Notion database."""
        await interaction.response.defer()
        
        # Add unique identifier to prevent duplicate processing
        command_id = f"{interaction.user.id}_{interaction.id}_{task_name[:50]}"
        logger.info(f"Processing task creation command: {command_id}")

        try:
            # Validate inputs
            if len(task_name.strip()) == 0:
                await interaction.followup.send(
                    "❌ Task name cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(task_name) > 500:
                await interaction.followup.send(
                    "❌ Task name is too long (max 500 characters)!", 
                    ephemeral=True
                )
                return

            if len(description.strip()) == 0:
                await interaction.followup.send(
                    "❌ Description cannot be empty!", 
                    ephemeral=True
                )
                return

            # Parse and validate Discord user ID
            target_discord_id = discord_user_id.strip()
            
            # Handle mentions (extract ID from <@!123456> or <@123456>)
            if target_discord_id.startswith('<@') and target_discord_id.endswith('>'):
                target_discord_id = target_discord_id.replace('<@!', '').replace('<@', '').replace('>', '')
            
            # Validate it's a valid Discord ID (numeric and reasonable length)
            if not target_discord_id.isdigit() or len(target_discord_id) < 17 or len(target_discord_id) > 20:
                await interaction.followup.send(
                    "❌ Invalid Discord user ID! Please provide a valid user ID or mention a user.",
                    ephemeral=True
                )
                return

            # Parse priority
            task_priority = TaskPriority.MEDIUM
            priority_lower = priority.lower()
            if priority_lower in ["low", "l"]:
                task_priority = TaskPriority.LOW
            elif priority_lower in ["medium", "med", "m"]:
                task_priority = TaskPriority.MEDIUM
            elif priority_lower in ["high", "h"]:
                task_priority = TaskPriority.HIGH
            elif priority_lower in ["urgent", "u"]:
                task_priority = TaskPriority.URGENT
            else:
                await interaction.followup.send(
                    "❌ Invalid priority! Valid options: Low, Medium, High, Urgent",
                    ephemeral=True
                )
                return

            # Check for recent duplicate tasks (within last 60 seconds)
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, func
                from datetime import timedelta
                
                recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
                
                duplicate_check = await session.execute(
                    select(NotionTask).where(
                        NotionTask.title == task_name.strip(),
                        NotionTask.discord_user_id == target_discord_id,
                        NotionTask.created_at > recent_cutoff
                    )
                )
                
                existing_task = duplicate_check.scalar_one_or_none()
                
                if existing_task:
                    logger.warning(f"Duplicate task detected for command {command_id}, skipping creation")
                    await interaction.followup.send(
                        f"⚠️ A task with the same name was just created! Task ID: {existing_task.id}",
                        ephemeral=True
                    )
                    return

            # Get Notion client
            notion_client = get_notion_client()
            
            # Log database schema for debugging (only first time)
            logger.debug("Getting ready to create Notion task")

            # Create task in Notion
            logger.info(f"Creating Notion task: '{task_name.strip()}' for user {target_discord_id}")
            notion_response = await notion_client.create_task(
                title=task_name.strip(),
                description=description.strip(),
                discord_user_id=target_discord_id,
                priority=task_priority,
                start_date=datetime.utcnow()
            )
            logger.info(f"Notion task created successfully with ID: {notion_response['id']}")

            # Save to local database
            async with AsyncSessionLocal() as session:
                task = NotionTask(
                    notion_page_id=notion_response["id"],
                    notion_database_id=notion_client.tasks_database_id,
                    title=task_name.strip(),
                    description=description.strip(),
                    priority=task_priority,
                    status=TaskStatus.NOT_STARTED,
                    discord_user_id=target_discord_id,
                    discord_message_id=str(interaction.message.id) if interaction.message else None,
                    discord_channel_id=str(interaction.channel_id),
                    start_date=datetime.utcnow(),
                    notion_url=notion_response.get("url"),
                    notion_properties=notion_response.get("properties", {}),
                    last_synced=datetime.utcnow(),
                    sync_status="completed"
                )

                session.add(task)
                logger.info(f"Saving task to local database: {task_name.strip()}")
                await session.commit()
                await session.refresh(task)
                logger.info(f"Task saved to database with ID: {task.id}")

            # Create simple embed matching the desired format
            embed = discord.Embed(
                title="📝 New task made!",
                description=f"### {task_name.strip()}\n{description.strip()}",
                color=0xFF8C00  # Orange color to match the sidebar
            )

            embed.add_field(
                name="👤 Assigned to:",
                value=f"<@{target_discord_id}>",
                inline=False
            )

            await interaction.followup.send(embed=embed)

            logger.info(f"Task created: {task_name} by {interaction.user.name} for user {target_discord_id}")

        except ValueError as e:
            await interaction.followup.send(
                f"❌ Configuration error: {str(e)}\nPlease contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Notion configuration error: {e}")

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to create task. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error creating Notion task: {e}")

    @create_task.autocomplete('priority')
    async def priority_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for priority parameter."""
        priorities = ["Low", "Medium", "High", "Urgent"]
        return [
            app_commands.Choice(name=priority, value=priority)
            for priority in priorities
            if current.lower() in priority.lower()
        ]


async def setup(bot: commands.Bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(NotionCommands(bot))