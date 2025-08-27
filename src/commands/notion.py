"""Notion integration Discord commands."""

from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from dateutil import parser as date_parser

from src.integrations.notion.client import get_notion_client
from src.models.notion import NotionTask, TaskPriority, TaskStatus, NotionTeam, TeamStatus, NotionResource
from src.utils.database import AsyncSessionLocal


class NotionCommands(commands.Cog):
    """Discord commands for Notion integration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    notion_group = app_commands.Group(
        name="notion", 
        description="Notion integration commands"
    )
    
    task_group = app_commands.Group(
        name="task",
        description="Task management commands",
        parent=notion_group
    )
    
    team_group = app_commands.Group(
        name="team",
        description="Team management commands",
        parent=notion_group
    )
    
    resource_group = app_commands.Group(
        name="resource",
        description="Resource management commands",
        parent=notion_group
    )
    
    # Future database type groups can be added here:
    # project_group = app_commands.Group(
    #     name="project",
    #     description="Project management commands",
    #     parent=notion_group
    # )

    @task_group.command(
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
                title="📝 New task created!",
                description=f"### {task_name.strip()}\n{description.strip()}",
                color=0xFF8C00  # Orange color to match the sidebar
            )
            
            embed.add_field(
                name="📋 Task ID",
                value=f"`{task.notion_page_id}`",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Priority",
                value=task_priority.value,
                inline=True
            )

            embed.add_field(
                name="👤 Assigned to",
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

    @task_group.command(
        name="update", 
        description="Update the status of an existing task"
    )
    @app_commands.describe(
        task_id="Task ID from Notion URL",
        status="New status: Not started, On hold, In progress, Cancelled, or Done"
    )
    async def update_task(
        self,
        interaction: discord.Interaction,
        task_id: str,
        status: str
    ):
        """Update the status of an existing task."""
        await interaction.response.defer()

        try:
            # Clean the task_id
            notion_task_id = task_id.strip()
            
            # Validate status
            valid_statuses = {
                "not started": TaskStatus.NOT_STARTED,
                "on hold": TaskStatus.ON_HOLD,
                "in progress": TaskStatus.IN_PROGRESS,
                "cancelled": TaskStatus.CANCELLED,
                "done": TaskStatus.COMPLETED
            }
            
            status_lower = status.lower()
            if status_lower not in valid_statuses:
                await interaction.followup.send(
                    "❌ Invalid status! Valid options: Not started, On hold, In progress, Cancelled, Done",
                    ephemeral=True
                )
                return
            
            new_status = valid_statuses[status_lower]

            # Get task from database - handle both formats (with/without dashes)
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                # Try with the provided format first
                result = await session.execute(
                    select(NotionTask).where(NotionTask.notion_page_id == notion_task_id)
                )
                task = result.scalar_one_or_none()
                
                # If not found and no dashes provided, try adding dashes in UUID format
                if not task and '-' not in notion_task_id and len(notion_task_id) == 32:
                    # Convert 25b389c4434b8146bee3dde5835db2a5 to 25b389c4-434b-8146-bee3-dde5835db2a5
                    formatted_id = f"{notion_task_id[:8]}-{notion_task_id[8:12]}-{notion_task_id[12:16]}-{notion_task_id[16:20]}-{notion_task_id[20:]}"
                    result = await session.execute(
                        select(NotionTask).where(NotionTask.notion_page_id == formatted_id)
                    )
                    task = result.scalar_one_or_none()
                
                # If still not found and dashes provided, try removing dashes
                elif not task and '-' in notion_task_id:
                    no_dash_id = notion_task_id.replace('-', '')
                    result = await session.execute(
                        select(NotionTask).where(NotionTask.notion_page_id == no_dash_id)
                    )
                    task = result.scalar_one_or_none()
                
                if not task:
                    await interaction.followup.send(
                        f"❌ Task with ID {notion_task_id} not found!\nMake sure you're using the correct Notion page ID.",
                        ephemeral=True
                    )
                    return

                old_status = task.status
                
                # Update local database
                task.status = new_status
                if new_status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated task {task.id} status from {old_status} to {new_status.value}")

                # Try to update Notion (if possible)
                try:
                    notion_client = get_notion_client()
                    
                    # Get database schema to find status field
                    db_info = notion_client.client.databases.retrieve(database_id=notion_client.tasks_database_id)
                    properties = db_info.get("properties", {})
                    
                    status_field_name = None
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "unknown")
                        
                        if prop_type == "status":
                            status_field_name = prop_name
                            break
                        elif prop_type == "select" and any(keyword in prop_name.lower() for keyword in ["status", "state", "progress"]):
                            status_field_name = prop_name
                            break
                    
                    if status_field_name:
                        field_info = properties[status_field_name]
                        field_type = field_info.get("type")
                        
                        if field_type == "status":
                            properties_update = {
                                status_field_name: {
                                    "status": {
                                        "name": new_status.value
                                    }
                                }
                            }
                        else:
                            properties_update = {
                                status_field_name: {
                                    "select": {
                                        "name": new_status.value
                                    }
                                }
                            }
                        
                        notion_client.client.pages.update(
                            page_id=task.notion_page_id,
                            properties=properties_update
                        )
                    else:
                        raise Exception("No status field found in Notion database")
                    
                    task.last_synced = datetime.utcnow()
                    task.sync_status = "completed"
                    await session.commit()
                    logger.info(f"Successfully synced status update to Notion for task {task.id}")
                    
                except Exception as notion_error:
                    logger.error(f"Failed to update Notion status: {notion_error}")
                    logger.error(f"Notion page ID: {task.notion_page_id}")
                    logger.error(f"New status: {new_status.value}")
                    task.sync_status = "failed"
                    task.error_message = str(notion_error)
                    await session.commit()

                # Create simple embed matching the desired format
                embed = discord.Embed(
                    title="📝 Task updated!",
                    description=f"**Status changed from {old_status.value} to {new_status.value}**\nCheck the Tasks database in Notion to edit more properties.",
                    color=0xFF8C00  # Orange color to match the sidebar
                )
                
                embed.add_field(
                    name="📋 Task",
                    value=task.title,
                    inline=True
                )
                
                embed.add_field(
                    name="📊 New Status",
                    value=new_status.value,
                    inline=True
                )
                
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to update task. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error updating task: {e}")

    @task_group.command(
        name="list", 
        description="List tasks assigned to you"
    )
    async def list_user_tasks(
        self,
        interaction: discord.Interaction
    ):
        """List tasks assigned to the user."""
        await interaction.response.defer()

        try:
            user_id = str(interaction.user.id)
            
            # Get tasks from database assigned to this user
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(NotionTask).where(
                        NotionTask.discord_user_id == user_id
                    ).order_by(
                        NotionTask.created_at.desc()
                    )  # Show all tasks assigned to user
                )
                tasks = result.scalars().all()

            if not tasks:
                embed = discord.Embed(
                    title="📋 No tasks found",
                    description="You don't have any tasks assigned to you.",
                    color=0x95a5a6
                )
                await interaction.followup.send(embed=embed)
                return

            # Group tasks by status
            from collections import defaultdict
            grouped_tasks = defaultdict(list)
            
            for task in tasks:
                grouped_tasks[task.status].append(task)

            # Status order for display
            status_order = ["In progress", "Not started", "On hold", "Completed", "Cancelled"]
            
            # Status emojis
            status_emojis = {
                "Not started": "⚪",  # Grey/white
                "On hold": "🟠",     # Orange
                "In progress": "🔵", # Blue
                "Completed": "🟢",   # Green
                "Cancelled": "🔴"    # Red
            }

            # Create tasks list embed
            embed = discord.Embed(
                title=f"📋 Your tasks ({len(tasks)})",
                description="All tasks assigned to you across all projects",
                color=0x3498db
            )

            # Add tasks grouped by status
            for status in status_order:
                if status in grouped_tasks and grouped_tasks[status]:
                    status_tasks = grouped_tasks[status]
                    status_emoji = status_emojis.get(status, "⚪")
                    
                    task_list = []
                    for task in status_tasks:
                        # Get priority
                        priority = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                        
                        # Task info with just priority since status is already grouped
                        task_info = f"**{task.title}**\n{priority}"
                        
                        if task.description:
                            desc_preview = task.description[:80] + "..." if len(task.description) > 80 else task.description
                            task_info += f"\n*{desc_preview}*"
                        
                        task_list.append(task_info)
                    
                    embed.add_field(
                        name=f"{status_emoji} {status} ({len(status_tasks)})",
                        value="\n\n".join(task_list),
                        inline=False
                    )

            embed.set_footer(text=f"Showing all {len(tasks)} of your tasks")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to retrieve your tasks. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error listing user tasks: {e}")

    @task_group.command(
        name="summary", 
        description="List tasks with start dates in the current week"
    )
    async def weekly_summary(
        self,
        interaction: discord.Interaction
    ):
        """List tasks assigned to the user with start dates in the current week."""
        await interaction.response.defer()

        try:
            user_id = str(interaction.user.id)
            
            # Get current week boundaries (Monday to Sunday)
            from datetime import timedelta
            now = datetime.utcnow()
            
            # Find Monday of current week
            days_since_monday = now.weekday()
            week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            # Get tasks from database with start dates in current week
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, and_
                
                result = await session.execute(
                    select(NotionTask).where(
                        and_(
                            NotionTask.discord_user_id == user_id,
                            NotionTask.start_date >= week_start,
                            NotionTask.start_date <= week_end
                        )
                    ).order_by(
                        NotionTask.start_date.asc()
                    )
                )
                tasks = result.scalars().all()

            if not tasks:
                embed = discord.Embed(
                    title="📅 No tasks this week",
                    description=f"You don't have any tasks with start dates between {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}.",
                    color=0x95a5a6
                )
                await interaction.followup.send(embed=embed)
                return

            # Group tasks by status
            from collections import defaultdict
            grouped_tasks = defaultdict(list)
            
            for task in tasks:
                grouped_tasks[task.status].append(task)

            # Status order for display
            status_order = ["In progress", "Not started", "On hold", "Completed", "Cancelled"]
            
            # Status emojis
            status_emojis = {
                "Not started": "⚪",  # Grey/white
                "On hold": "🟠",     # Orange
                "In progress": "🔵", # Blue
                "Completed": "🟢",   # Green
                "Cancelled": "🔴"    # Red
            }

            # Create tasks summary embed
            embed = discord.Embed(
                title=f"📅 This week's task summary ({len(tasks)})",
                description=f"Tasks with start dates between {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}",
                color=0x3498db
            )

            # Add tasks grouped by status
            for status in status_order:
                if status in grouped_tasks and grouped_tasks[status]:
                    status_tasks = grouped_tasks[status]
                    status_emoji = status_emojis.get(status, "⚪")
                    
                    task_list = []
                    for task in status_tasks:
                        # Get priority
                        priority = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                        
                        # Task info with priority and start date
                        start_date_str = task.start_date.strftime('%b %d') if task.start_date else "No date"
                        task_info = f"**{task.title}**\n{priority} • Start: {start_date_str}"
                        
                        if task.description:
                            desc_preview = task.description[:70] + "..." if len(task.description) > 70 else task.description
                            task_info += f"\n*{desc_preview}*"
                        
                        task_list.append(task_info)
                    
                    embed.add_field(
                        name=f"{status_emoji} {status} ({len(status_tasks)})",
                        value="\n\n".join(task_list),
                        inline=False
                    )

            embed.set_footer(text=f"Showing {len(tasks)} tasks for this week")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to retrieve your weekly summary. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error retrieving weekly summary: {e}")

    @update_task.autocomplete('status')
    async def update_status_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for status parameter - excludes current status."""
        try:
            task_id = interaction.namespace.task_id
            if not task_id:
                # If no task ID provided yet, show all options
                all_statuses = ["Not started", "On hold", "In progress", "Cancelled", "Done"]
                return [app_commands.Choice(name=status, value=status) for status in all_statuses]
            
            # Try to find the task to get current status
            current_status = None
            try:
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import select
                    
                    # Handle both ID formats
                    notion_task_id = task_id.strip()
                    
                    # Try with provided format first
                    result = await session.execute(
                        select(NotionTask).where(NotionTask.notion_page_id == notion_task_id)
                    )
                    task = result.scalar_one_or_none()
                    
                    # If not found and no dashes, try adding dashes
                    if not task and '-' not in notion_task_id and len(notion_task_id) == 32:
                        formatted_id = f"{notion_task_id[:8]}-{notion_task_id[8:12]}-{notion_task_id[12:16]}-{notion_task_id[16:20]}-{notion_task_id[20:]}"
                        result = await session.execute(
                            select(NotionTask).where(NotionTask.notion_page_id == formatted_id)
                        )
                        task = result.scalar_one_or_none()
                    
                    if task:
                        current_status = task.status
                        
            except Exception:
                pass  # Ignore errors, just show all options
            
            # All possible statuses
            all_statuses = ["Not started", "On hold", "In progress", "Cancelled", "Done"]
            
            # Remove current status from options if found
            if current_status:
                available_statuses = [s for s in all_statuses if s != current_status]
            else:
                available_statuses = all_statuses
            
            # Filter based on current input
            if current:
                available_statuses = [s for s in available_statuses if current.lower() in s.lower()]
            
            return [app_commands.Choice(name=status, value=status) for status in available_statuses[:25]]  # Discord limit
            
        except Exception as e:
            logger.error(f"Status autocomplete error: {e}")
            # Fallback to basic options
            return [
                app_commands.Choice(name="Not started", value="Not started"),
                app_commands.Choice(name="In progress", value="In progress"),
                app_commands.Choice(name="Done", value="Done")
            ]

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

    @create_task.autocomplete('discord_user_id')
    async def discord_user_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for discord_user_id parameter - search by username."""
        try:
            if not current or len(current) < 2:
                return []
            
            # Search through guild members
            guild = interaction.guild
            if not guild:
                return []
            
            matches = []
            current_lower = current.lower()
            
            # Search by display name and username
            for member in guild.members:
                # Skip bots
                if member.bot:
                    continue
                    
                # Check display name
                if current_lower in member.display_name.lower():
                    matches.append(app_commands.Choice(
                        name=f"{member.display_name} ({member.name})",
                        value=str(member.id)
                    ))
                # Check username if different from display name
                elif current_lower in member.name.lower() and member.name != member.display_name:
                    matches.append(app_commands.Choice(
                        name=f"{member.name} (username)",
                        value=str(member.id)
                    ))
                
                # Limit to 25 results (Discord limit)
                if len(matches) >= 25:
                    break
            
            return matches
            
        except Exception as e:
            logger.error(f"Discord user autocomplete error: {e}")
            return []


    @team_group.command(
        name="create", 
        description="Create a new team member in Notion"
    )
    @app_commands.describe(
        name="Full name of the team member",
        position="Job title or position", 
        email="Email address",
        phone_number="Phone number",
        birthday="Birthday (e.g., 01-15-1990 or January 15, 1990)"
    )
    async def create_team_member(
        self,
        interaction: discord.Interaction,
        name: str,
        position: str,
        email: str,
        phone_number: str,
        birthday: str
    ):
        """Create a new team member in Notion database."""
        await interaction.response.defer()
        
        command_id = f"{interaction.user.id}_{interaction.id}_{name[:50]}"
        logger.info(f"Processing team member creation command: {command_id}")

        try:
            # Validate all required inputs
            if len(name.strip()) == 0:
                await interaction.followup.send(
                    "❌ Name cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(position.strip()) == 0:
                await interaction.followup.send(
                    "❌ Position cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(email.strip()) == 0:
                await interaction.followup.send(
                    "❌ Email cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(phone_number.strip()) == 0:
                await interaction.followup.send(
                    "❌ Phone number cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(birthday.strip()) == 0:
                await interaction.followup.send(
                    "❌ Birthday cannot be empty!", 
                    ephemeral=True
                )
                return

            # Validate birthday date format
            try:
                birthday_date = date_parser.parse(birthday.strip())
            except (ValueError, TypeError):
                await interaction.followup.send(
                    "❌ Invalid birthday format! Please use formats like 'MM-DD-YYYY' or 'January 15, 1990'.",
                    ephemeral=True
                )
                return

            # Validate field lengths
            if len(name) > 200:
                await interaction.followup.send(
                    "❌ Name is too long (max 200 characters)!", 
                    ephemeral=True
                )
                return

            if len(position) > 200:
                await interaction.followup.send(
                    "❌ Position is too long (max 200 characters)!", 
                    ephemeral=True
                )
                return

            if len(email) > 200:
                await interaction.followup.send(
                    "❌ Email is too long (max 200 characters)!", 
                    ephemeral=True
                )
                return

            # Validate email format
            if '@' not in email or '.' not in email:
                await interaction.followup.send(
                    "❌ Please provide a valid email address!",
                    ephemeral=True
                )
                return

            # Check for recent duplicate team members (within last 60 seconds)
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, func
                from datetime import timedelta
                
                recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
                
                duplicate_check = await session.execute(
                    select(NotionTeam).where(
                        NotionTeam.name == name.strip(),
                        NotionTeam.created_at > recent_cutoff
                    )
                )
                
                existing_member = duplicate_check.scalar_one_or_none()
                
                if existing_member:
                    logger.warning(f"Duplicate team member detected for command {command_id}, skipping creation")
                    await interaction.followup.send(
                        f"⚠️ A team member with the same name was just created! Member ID: {existing_member.id}",
                        ephemeral=True
                    )
                    return

            # Get Notion client
            notion_client = get_notion_client()
            
            # Create team member in Notion
            logger.info(f"Creating Notion team member: '{name.strip()}'")
            notion_response = await notion_client.create_team_member(
                name=name.strip(),
                position=position.strip(),
                email=email.strip(),
                phone_number=phone_number.strip(),
                birthday=birthday.strip(),
                discord_user_id=str(interaction.user.id)
            )
            logger.info(f"Notion team member created successfully with ID: {notion_response['id']}")

            # Save to local database
            async with AsyncSessionLocal() as session:
                team_member = NotionTeam(
                    notion_page_id=notion_response["id"],
                    notion_database_id=notion_client.teams_database_id,
                    name=name.strip(),
                    position=position.strip(),
                    email=email.strip(),
                    phone_number=phone_number.strip(),
                    birthday=birthday_date,  # Store as datetime object
                    status=TeamStatus.ACTIVE,  # Default status
                    discord_user_id=str(interaction.user.id),
                    discord_message_id=str(interaction.message.id) if interaction.message else None,
                    discord_channel_id=str(interaction.channel_id),
                    notion_url=notion_response.get("url"),
                    notion_properties=notion_response.get("properties", {}),
                    last_synced=datetime.utcnow(),
                    sync_status="completed"
                )

                session.add(team_member)
                logger.info(f"Saving team member to local database: {name.strip()}")
                await session.commit()
                await session.refresh(team_member)
                logger.info(f"Team member saved to database with ID: {team_member.id}")

            # Create embed for response
            embed = discord.Embed(
                title="👥 New team member added!",
                description=f"### {name.strip()}",
                color=0x00D084  # Green color for team
            )
            
            embed.add_field(
                name="💼 Position",
                value=position.strip(),
                inline=False
            )
            
            embed.add_field(
                name="📊 Status",
                value=TeamStatus.ACTIVE.value,
                inline=False
            )
            
            # Add contact info
            contact_info = [
                f"📧 {email.strip()}",
                f"📞 {phone_number.strip()}",
                f"🎂 {birthday_date.strftime('%B %d, %Y')}"
            ]
            
            embed.add_field(
                name="📞 Contact Information",
                value="\n".join(contact_info),
                inline=False
            )

            await interaction.followup.send(embed=embed)

            logger.info(f"Team member created: {name} by {interaction.user.name}")

        except ValueError as e:
            await interaction.followup.send(
                f"❌ Configuration error: {str(e)}\nPlease contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Notion configuration error: {e}")

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to create team member. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error creating Notion team member: {e}")

    @team_group.command(
        name="update", 
        description="Update an existing team member in Notion"
    )
    @app_commands.describe(
        name="Name of the team member to update (required)",
        status="New status for the team member (required)",
        position="Updated job title or position (optional)", 
        email="Updated email address (optional)",
        phone_number="Updated phone number (optional)",
        birthday="Updated birthday (optional, e.g., 01-15-1990)"
    )
    async def update_team_member(
        self,
        interaction: discord.Interaction,
        name: str,
        status: str,
        position: str = None,
        email: str = None,
        phone_number: str = None,
        birthday: str = None
    ):
        """Update an existing team member in Notion database."""
        await interaction.response.defer()
        
        command_id = f"{interaction.user.id}_{interaction.id}_{name[:50]}"
        logger.info(f"Processing team member update command: {command_id}")

        try:
            # Validate required inputs
            if len(name.strip()) == 0:
                await interaction.followup.send(
                    "❌ Name cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(status.strip()) == 0:
                await interaction.followup.send(
                    "❌ Status cannot be empty!", 
                    ephemeral=True
                )
                return

            # Validate status
            valid_statuses = {
                "active": TeamStatus.ACTIVE,
                "inactive": TeamStatus.INACTIVE
            }
            
            status_lower = status.lower()
            if status_lower not in valid_statuses:
                await interaction.followup.send(
                    "❌ Invalid status! Valid options: Active, Inactive",
                    ephemeral=True
                )
                return
            
            new_status = valid_statuses[status_lower]

            # Find team member by name
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(NotionTeam).where(
                        NotionTeam.name.ilike(f"%{name.strip()}%")  # Case insensitive search
                    )
                )
                team_members = result.scalars().all()
                
                if not team_members:
                    await interaction.followup.send(
                        f"❌ No team member found with name '{name.strip()}'!",
                        ephemeral=True
                    )
                    return
                
                if len(team_members) > 1:
                    member_names = [member.name for member in team_members]
                    await interaction.followup.send(
                        f"❌ Multiple team members found with similar names: {', '.join(member_names)}\nPlease use the exact name.",
                        ephemeral=True
                    )
                    return
                
                team_member = team_members[0]
                # Convert string status to enum for comparison
                if isinstance(team_member.status, str):
                    try:
                        old_status = TeamStatus(team_member.status)
                    except ValueError:
                        old_status = TeamStatus.ACTIVE  # Default fallback
                else:
                    old_status = team_member.status

                # Validate optional fields if provided
                if email and '@' not in email:
                    await interaction.followup.send(
                        "❌ Please provide a valid email address!",
                        ephemeral=True
                    )
                    return

                # Validate birthday format if provided
                birthday_date = None
                if birthday:
                    try:
                        birthday_date = date_parser.parse(birthday.strip())
                    except (ValueError, TypeError):
                        await interaction.followup.send(
                            "❌ Invalid birthday format! Please use formats like 'MM-DD-YYYY' or 'January 15, 1990'.",
                            ephemeral=True
                        )
                        return

                # Get Notion client and update
                notion_client = get_notion_client()
                
                # Update team member in Notion
                logger.info(f"Updating Notion team member: '{team_member.name}' (ID: {team_member.notion_page_id})")
                notion_response = await notion_client.update_team_member(
                    page_id=team_member.notion_page_id,
                    name=name.strip() if name else None,
                    position=position.strip() if position else None,
                    email=email.strip() if email else None,
                    phone_number=phone_number.strip() if phone_number else None,
                    birthday=birthday.strip() if birthday else None,
                    status=new_status
                )
                logger.info(f"Notion team member updated successfully")

                # Update local database
                if name: team_member.name = name.strip()
                if position: team_member.position = position.strip()
                if email: team_member.email = email.strip()
                if phone_number: team_member.phone_number = phone_number.strip()
                if birthday_date: team_member.birthday = birthday_date
                team_member.status = new_status
                team_member.last_synced = datetime.utcnow()
                team_member.sync_status = "completed"

                await session.commit()
                await session.refresh(team_member)
                logger.info(f"Team member updated in local database: {team_member.name}")

                # Create embed for response
                embed = discord.Embed(
                    title="👥 Team member updated!",
                    description=f"### {team_member.name}",
                    color=0x00D084  # Green color for team
                )
                
                embed.add_field(
                    name="📊 Status Change",
                    value=f"{old_status.value if hasattr(old_status, 'value') else old_status} → {new_status.value}",
                    inline=False
                )
                
                if position:
                    embed.add_field(
                        name="💼 Position",
                        value=position.strip(),
                        inline=False
                    )
                
                # Add updated contact info if provided
                contact_updates = []
                if email:
                    contact_updates.append(f"📧 {email.strip()}")
                if phone_number:
                    contact_updates.append(f"📞 {phone_number.strip()}")
                if birthday_date:
                    contact_updates.append(f"🎂 {birthday_date.strftime('%B %d, %Y')}")
                
                if contact_updates:
                    embed.add_field(
                        name="📝 Updated Contact Info",
                        value="\n".join(contact_updates),
                        inline=False
                    )

                await interaction.followup.send(embed=embed)
                logger.info(f"Team member updated: {team_member.name} by {interaction.user.name}")

        except ValueError as e:
            await interaction.followup.send(
                f"❌ Configuration error: {str(e)}\nPlease contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Notion configuration error: {e}")

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to update team member. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error updating Notion team member: {e}")

    @update_team_member.autocomplete('status')
    async def team_status_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for team member status."""
        statuses = ["Active", "Inactive"]
        return [
            app_commands.Choice(name=status, value=status)
            for status in statuses
            if current.lower() in status.lower()
        ][:25]  # Discord limit

    @update_team_member.autocomplete('name')
    async def team_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for team member names."""
        try:
            if not current or len(current) < 2:
                return []
            
            # Search team members by name
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(NotionTeam).where(
                        NotionTeam.name.ilike(f"%{current}%")
                    ).limit(25)
                )
                team_members = result.scalars().all()
                
                return [
                    app_commands.Choice(name=member.name, value=member.name)
                    for member in team_members
                ]
            
        except Exception as e:
            logger.error(f"Team name autocomplete error: {e}")
            return []

    @resource_group.command(
        name="create", 
        description="Create a new resource in Notion"
    )
    @app_commands.describe(
        title="Title of the resource (required)",
        url="URL of the resource (required, must start with http:// or https://)",
        description="Description of the resource (optional)"
    )
    async def create_resource(
        self,
        interaction: discord.Interaction,
        title: str,
        url: str,
        description: str = None
    ):
        """Create a new resource in Notion database."""
        await interaction.response.defer()
        
        command_id = f"{interaction.user.id}_{interaction.id}_{title[:50]}"
        logger.info(f"Processing resource creation command: {command_id}")

        try:
            # Validate required inputs
            if len(title.strip()) == 0:
                await interaction.followup.send(
                    "❌ Title cannot be empty!", 
                    ephemeral=True
                )
                return

            if len(url.strip()) == 0:
                await interaction.followup.send(
                    "❌ URL cannot be empty!", 
                    ephemeral=True
                )
                return

            # Validate field lengths
            if len(title) > 500:
                await interaction.followup.send(
                    "❌ Title is too long (max 500 characters)!", 
                    ephemeral=True
                )
                return

            if len(url) > 1000:
                await interaction.followup.send(
                    "❌ URL is too long (max 1000 characters)!", 
                    ephemeral=True
                )
                return

            # Validate URL format
            if not url.strip().startswith(('http://', 'https://')):
                await interaction.followup.send(
                    "❌ URL must start with http:// or https://!",
                    ephemeral=True
                )
                return

            # Check for recent duplicate resources (within last 60 seconds)
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                from datetime import timedelta
                
                recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
                
                duplicate_check = await session.execute(
                    select(NotionResource).where(
                        NotionResource.title == title.strip(),
                        NotionResource.created_at > recent_cutoff
                    )
                )
                
                existing_resource = duplicate_check.scalar_one_or_none()
                
                if existing_resource:
                    logger.warning(f"Duplicate resource detected for command {command_id}, skipping creation")
                    await interaction.followup.send(
                        f"⚠️ A resource with the same title was just created! Resource ID: {existing_resource.id}",
                        ephemeral=True
                    )
                    return

            # Get Notion client
            notion_client = get_notion_client()
            
            # Create resource in Notion
            logger.info(f"Creating Notion resource: '{title.strip()}'")
            notion_response = await notion_client.create_resource(
                title=title.strip(),
                url=url.strip(),
                description=description.strip() if description else None,
                discord_user_id=str(interaction.user.id)
            )
            logger.info(f"Notion resource created successfully with ID: {notion_response['id']}")

            # Save to local database
            async with AsyncSessionLocal() as session:
                resource = NotionResource(
                    notion_page_id=notion_response["id"],
                    notion_database_id=notion_client.resources_database_id,
                    title=title.strip(),
                    description=description.strip() if description else None,
                    url=url.strip(),
                    discord_user_id=str(interaction.user.id),
                    discord_message_id=str(interaction.message.id) if interaction.message else None,
                    discord_channel_id=str(interaction.channel_id),
                    notion_url=notion_response.get("url"),
                    notion_properties=notion_response.get("properties", {}),
                    last_synced=datetime.utcnow(),
                    sync_status="completed"
                )

                session.add(resource)
                logger.info(f"Saving resource to local database: {title.strip()}")
                await session.commit()
                await session.refresh(resource)
                logger.info(f"Resource saved to database with ID: {resource.id}")

            # Create embed for response
            embed = discord.Embed(
                title="📚 New resource created!",
                description=f"### {title.strip()}",
                color=0x9B59B6  # Purple color for resources
            )
            
            embed.add_field(
                name="🔗 URL",
                value=f"[{url.strip()}]({url.strip()})",
                inline=False
            )
            
            if description:
                # Truncate description if too long for embed
                desc_display = description.strip()
                if len(desc_display) > 300:
                    desc_display = desc_display[:300] + "..."
                    
                embed.add_field(
                    name="📝 Description",
                    value=desc_display,
                    inline=False
                )

            embed.add_field(
                name="👤 Added by",
                value=f"{interaction.user.display_name}",
                inline=True
            )

            await interaction.followup.send(embed=embed)

            logger.info(f"Resource created: {title} by {interaction.user.name}")

        except ValueError as e:
            await interaction.followup.send(
                f"❌ Configuration error: {str(e)}\nPlease contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Notion configuration error: {e}")

        except Exception as e:
            await interaction.followup.send(
                "❌ Failed to create resource. Please try again later.",
                ephemeral=True
            )
            logger.error(f"Error creating Notion resource: {e}")


async def setup(bot: commands.Bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(NotionCommands(bot))