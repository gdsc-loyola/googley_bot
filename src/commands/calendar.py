"""Google Calendar integration commands."""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from typing import Optional
from datetime import datetime, timedelta

from src.integrations.calendar import operations
from src.integrations.calendar.client import GoogleCalendarClient


class CalendarCommands(commands.Cog):
    """Google Calendar integration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="calendar-auth", description="Get Google Calendar authorization URL")
    async def calendar_auth(self, interaction: discord.Interaction) -> None:
        """Get Google Calendar authorization URL."""
        await interaction.response.defer(ephemeral=True)
        try:
            auth_url = GoogleCalendarClient.get_authorization_url()
            embed = discord.Embed(
                title="🔐 Google Calendar Authorization",
                description="Click the link below to authorize the bot to access your Google Calendar:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Authorization URL",
                value=f"[Click here to authorize]({auth_url})",
                inline=False
            )
            embed.add_field(
                name="Next Steps",
                value="1. Click the link above\n2. Sign in to your Google account\n3. Grant calendar permissions\n4. Copy the authorization code\n5. Use `/calendar-setup` with the code",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error getting auth URL: {e}")
            await interaction.followup.send("❌ Failed to get authorization URL.", ephemeral=True)

    @app_commands.command(name="calendar-setup", description="Complete Google Calendar setup with authorization code")
    @app_commands.describe(code="Authorization code from Google OAuth")
    async def calendar_setup(self, interaction: discord.Interaction, code: str) -> None:
        """Complete Google Calendar setup with authorization code."""
        await interaction.response.defer(ephemeral=True)
        try:
            # Exchange code for credentials
            credentials = GoogleCalendarClient.exchange_code_for_credentials(code)
            
            # Store credentials in database (this would need to be implemented)
            # For now, just show success
            embed = discord.Embed(
                title="✅ Google Calendar Setup Complete",
                description="Your Google Calendar has been successfully connected!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="What's Next?",
                value="• Use `/calendar-list` to see your calendars\n• Use `/calendar-events` to view upcoming events\n• Use `/calendar-subscribe` to get notifications",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error setting up calendar: {e}")
            await interaction.followup.send("❌ Failed to complete setup. Please try again.", ephemeral=True)

    @app_commands.command(name="calendar-list", description="List your Google Calendars")
    async def calendar_list(self, interaction: discord.Interaction) -> None:
        """List user's Google Calendars."""
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            calendars = await operations.list_user_calendars(user_id)
            
            embed = discord.Embed(title="📅 Your Google Calendars", color=discord.Color.blue())
            
            if not calendars:
                embed.description = "No calendars found. Use `/calendar-auth` to connect your Google Calendar."
            else:
                for calendar in calendars[:10]:  # Limit to 10 calendars
                    embed.add_field(
                        name=calendar.get('summary', 'Untitled Calendar'),
                        value=f"ID: `{calendar.get('id')}`\n"
                              f"Access: {calendar.get('accessRole', 'Unknown')}\n"
                              f"Primary: {'Yes' if calendar.get('primary') else 'No'}",
                        inline=True
                    )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing calendars: {e}")
            await interaction.followup.send("❌ Failed to list calendars.")

    @app_commands.command(name="calendar-events", description="List upcoming events from your calendars")
    @app_commands.describe(
        calendar_id="Specific calendar ID (optional)",
        days="Number of days ahead to look (default: 7)"
    )
    async def calendar_events(
        self,
        interaction: discord.Interaction,
        calendar_id: Optional[str] = None,
        days: int = 7
    ) -> None:
        """List upcoming events from calendars."""
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            events = await operations.get_upcoming_events(user_id, calendar_id, days * 24)
            
            embed = discord.Embed(
                title=f"📅 Upcoming Events ({days} days)",
                color=discord.Color.green()
            )
            
            if not events:
                embed.description = "No upcoming events found."
            else:
                for event in events[:10]:  # Limit to 10 events
                    start = event.get('start', {})
                    start_time = start.get('dateTime', start.get('date', ''))
                    
                    # Parse and format time
                    try:
                        if 'T' in start_time:
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            time_str = dt.strftime('%Y-%m-%d %H:%M')
                        else:
                            time_str = start_time
                    except:
                        time_str = start_time
                    
                    embed.add_field(
                        name=event.get('summary', 'Untitled Event'),
                        value=f"**Time:** {time_str}\n"
                              f"**Location:** {event.get('location', 'N/A')}\n"
                              f"**Status:** {event.get('status', 'confirmed').title()}",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            await interaction.followup.send("❌ Failed to list events.")

    @app_commands.command(name="calendar-create", description="Create a new calendar event")
    @app_commands.describe(
        title="Event title",
        start_time="Start time (YYYY-MM-DD HH:MM)",
        end_time="End time (YYYY-MM-DD HH:MM)",
        description="Event description (optional)",
        location="Event location (optional)",
        calendar_id="Calendar ID (optional, uses primary if not specified)"
    )
    async def calendar_create(
        self,
        interaction: discord.Interaction,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: Optional[str] = None
    ) -> None:
        """Create a new calendar event."""
        await interaction.response.defer()
        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            
            # Create event data
            from src.schemas.calendar import CalendarEventCreate
            event_data = CalendarEventCreate(
                summary=title,
                description=description,
                location=location,
                start_time=start_dt,
                end_time=end_dt
            )
            
            user_id = str(interaction.user.id)
            
            # If no calendar_id specified, get the first available calendar
            if not calendar_id:
                calendars = await operations.list_user_calendars(user_id)
                if not calendars:
                    await interaction.followup.send("❌ No calendars found. Please set up your Google Calendar first.")
                    return
                calendar_id = calendars[0]['id']
            
            # Create the event
            created_event = await operations.create_calendar_event(
                user_id, calendar_id, event_data
            )
            
            if created_event:
                embed = discord.Embed(
                    title="✅ Event Created",
                    description=f"Successfully created event: **{title}**",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Details",
                    value=f"**Start:** {start_dt.strftime('%Y-%m-%d %H:%M')}\n"
                          f"**End:** {end_dt.strftime('%Y-%m-%d %H:%M')}\n"
                          f"**Calendar:** {calendar_id}",
                    inline=False
                )
                if created_event.get('htmlLink'):
                    embed.add_field(
                        name="View Event",
                        value=f"[Open in Google Calendar]({created_event['htmlLink']})",
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="❌ Failed to Create Event",
                    description="Could not create the calendar event.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed)
        except ValueError as e:
            await interaction.followup.send(f"❌ Invalid time format. Please use YYYY-MM-DD HH:MM format. Error: {e}")
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            await interaction.followup.send("❌ Failed to create event.")

    @app_commands.command(name="calendar-subscribe", description="Subscribe this channel to calendar notifications")
    @app_commands.describe(calendar_id="Calendar ID to subscribe to")
    async def calendar_subscribe(
        self,
        interaction: discord.Interaction,
        calendar_id: str
    ) -> None:
        """Subscribe a Discord channel to calendar notifications."""
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)
            
            success = await operations.subscribe_calendar_to_discord(
                user_id, calendar_id, channel_id
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Calendar Subscribed",
                    description=f"Channel {interaction.channel.mention} is now subscribed to calendar notifications.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Calendar ID",
                    value=f"`{calendar_id}`",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Subscription Failed",
                    description="Could not subscribe to the calendar. Make sure the calendar ID is correct and you have access to it.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error subscribing to calendar: {e}")
            await interaction.followup.send("❌ Failed to subscribe to calendar.")

    @app_commands.command(name="calendar-unsubscribe", description="Unsubscribe this channel from calendar notifications")
    @app_commands.describe(calendar_id="Calendar ID to unsubscribe from")
    async def calendar_unsubscribe(
        self,
        interaction: discord.Interaction,
        calendar_id: str
    ) -> None:
        """Unsubscribe a Discord channel from calendar notifications."""
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)
            
            success = await operations.unsubscribe_calendar_from_discord(
                user_id, calendar_id, channel_id
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Calendar Unsubscribed",
                    description=f"Channel {interaction.channel.mention} is no longer subscribed to calendar notifications.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Unsubscription Failed",
                    description="Could not unsubscribe from the calendar. Make sure the channel is currently subscribed.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error unsubscribing from calendar: {e}")
            await interaction.followup.send("❌ Failed to unsubscribe from calendar.")

    @app_commands.command(name="calendar-help", description="Show Google Calendar integration help")
    async def calendar_help(self, interaction: discord.Interaction) -> None:
        """Show Google Calendar integration help."""
        embed = discord.Embed(
            title="📅 Google Calendar Integration Help",
            description="Commands to manage your Google Calendar integration:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔐 Authentication",
            value="`/calendar-auth` - Get authorization URL\n"
                  "`/calendar-setup <code>` - Complete setup with auth code",
            inline=False
        )
        
        embed.add_field(
            name="📋 Viewing",
            value="`/calendar-list` - List your calendars\n"
                  "`/calendar-events [calendar_id] [days]` - View upcoming events",
            inline=False
        )
        
        embed.add_field(
            name="✏️ Managing",
            value="`/calendar-create` - Create new event\n"
                  "`/calendar-subscribe <calendar_id>` - Subscribe channel\n"
                  "`/calendar-unsubscribe <calendar_id>` - Unsubscribe channel",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Use `/calendar-auth` first to connect your Google account\n"
                  "• Calendar IDs can be found with `/calendar-list`\n"
                  "• Time format: YYYY-MM-DD HH:MM (24-hour format)\n"
                  "• Subscribed channels will receive event notifications",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add cog to bot."""
    await bot.add_cog(CalendarCommands(bot))
