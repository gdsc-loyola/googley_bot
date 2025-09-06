"""Google Calendar integration models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CalendarEventStatus(str, Enum):
    """Google Calendar event status."""
    
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class CalendarEventVisibility(str, Enum):
    """Google Calendar event visibility."""
    
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"


class CalendarEventReminderMethod(str, Enum):
    """Google Calendar reminder methods."""
    
    EMAIL = "email"
    POPUP = "popup"


class GoogleCalendar(Base):
    """Google Calendar configuration."""

    __tablename__ = "google_calendars"

    # Calendar identification
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Calendar details
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    access_role: Mapped[str] = mapped_column(String(50), default="reader")  # owner, writer, reader
    
    # Discord integration
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    notification_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # OAuth configuration
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)  # Encrypted
    access_token: Mapped[Optional[str]] = mapped_column(Text)  # Encrypted
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Tracking settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    track_events: Mapped[bool] = mapped_column(Boolean, default=True)
    track_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    track_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Filter settings
    ignored_event_types: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of event types
    ignored_attendees: Mapped[Optional[str]] = mapped_column(Text)    # JSON array of email addresses
    
    # Statistics
    total_events: Mapped[int] = mapped_column(Integer, default=0)
    total_reminders: Mapped[int] = mapped_column(Integer, default=0)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<GoogleCalendar(calendar_id={self.calendar_id}, summary={self.summary})>"

    @property
    def calendar_url(self) -> str:
        """Get Google Calendar URL."""
        return f"https://calendar.google.com/calendar/embed?src={self.calendar_id}"


class CalendarEvent(Base):
    """Google Calendar event."""

    __tablename__ = "calendar_events"

    # Event identification
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Event details
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Event metadata
    status: Mapped[CalendarEventStatus] = mapped_column(String(20), default=CalendarEventStatus.CONFIRMED)
    visibility: Mapped[CalendarEventVisibility] = mapped_column(String(20), default=CalendarEventVisibility.DEFAULT)
    
    # Attendees
    attendees: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # List of attendee objects
    organizer_email: Mapped[Optional[str]] = mapped_column(String(255))
    organizer_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Recurrence
    recurrence: Mapped[Optional[str]] = mapped_column(Text)  # RRULE string
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Reminders
    reminders: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Reminder configuration
    
    # Raw event data
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Discord integration
    discord_message_id: Mapped[Optional[str]] = mapped_column(String(20))
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync tracking
    last_modified: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_version: Mapped[int] = mapped_column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<CalendarEvent(event_id={self.event_id}, summary={self.summary})>"

    @property
    def google_calendar_url(self) -> str:
        """Get Google Calendar event URL."""
        return f"https://calendar.google.com/calendar/event?eid={self.event_id}"

    @property
    def duration_minutes(self) -> int:
        """Get event duration in minutes."""
        if self.is_all_day:
            return 24 * 60  # All day events
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def mark_processed(self, discord_message_id: Optional[str] = None, discord_channel_id: Optional[str] = None) -> None:
        """Mark event as processed."""
        self.processed = True
        self.processed_at = datetime.now()
        if discord_message_id:
            self.discord_message_id = discord_message_id
        if discord_channel_id:
            self.discord_channel_id = discord_channel_id


class CalendarWebhookEvent(Base):
    """Google Calendar webhook event log."""

    __tablename__ = "calendar_webhook_events"

    # Event identification
    webhook_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Calendar information
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    calendar_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # sync, create, update, delete
    event_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Timing
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Raw webhook data
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    discord_message_id: Mapped[Optional[str]] = mapped_column(String(20))
    discord_channel_id: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<CalendarWebhookEvent(webhook_id={self.webhook_id}, type={self.event_type}, calendar={self.calendar_id})>"

    def mark_processed(self, discord_message_id: Optional[str] = None, discord_channel_id: Optional[str] = None) -> None:
        """Mark event as processed."""
        self.processed = True
        self.processed_at = datetime.now()
        if discord_message_id:
            self.discord_message_id = discord_message_id
        if discord_channel_id:
            self.discord_channel_id = discord_channel_id

    def mark_error(self, error_message: str) -> None:
        """Mark event as having an error."""
        self.error_message = error_message
        self.retry_count += 1
