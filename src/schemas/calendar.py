"""Pydantic schemas for Google Calendar integration."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CalendarEventStatus(str, Enum):
    """Google Calendar event status."""
    confirmed = "confirmed"
    tentative = "tentative"
    cancelled = "cancelled"


class CalendarEventVisibility(str, Enum):
    """Google Calendar event visibility."""
    default = "default"
    public = "public"
    private = "private"


class CalendarEventReminderMethod(str, Enum):
    """Google Calendar reminder methods."""
    email = "email"
    popup = "popup"


class CalendarEventAttendee(BaseModel):
    """Calendar event attendee."""
    email: str
    display_name: Optional[str] = None
    response_status: Optional[str] = None  # accepted, declined, tentative, needsAction
    optional: bool = False
    resource: bool = False


class CalendarEventReminder(BaseModel):
    """Calendar event reminder."""
    method: CalendarEventReminderMethod
    minutes: int = Field(..., ge=0, le=40320)  # Max 4 weeks in minutes


class GoogleCalendarSchema(BaseModel):
    """Google Calendar configuration schema."""
    id: int
    calendar_id: str
    summary: str
    description: Optional[str] = None
    timezone: str = "UTC"
    is_primary: bool = False
    is_public: bool = False
    access_role: str = "reader"
    discord_channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    user_id: str
    is_active: bool = True
    track_events: bool = True
    track_reminders: bool = True
    track_updates: bool = True
    ignored_event_types: Optional[str] = None
    ignored_attendees: Optional[str] = None
    total_events: int = 0
    total_reminders: int = 0
    last_sync: Optional[datetime] = None

    class Config:
        orm_mode = True


class CalendarEventSchema(BaseModel):
    """Google Calendar event schema."""
    id: int
    event_id: str
    calendar_id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    timezone: str = "UTC"
    status: CalendarEventStatus = CalendarEventStatus.confirmed
    visibility: CalendarEventVisibility = CalendarEventVisibility.default
    attendees: Optional[List[CalendarEventAttendee]] = None
    organizer_email: Optional[str] = None
    organizer_name: Optional[str] = None
    recurrence: Optional[str] = None
    is_recurring: bool = False
    reminders: Optional[List[CalendarEventReminder]] = None
    raw_data: Dict[str, Any]
    discord_message_id: Optional[str] = None
    discord_channel_id: Optional[str] = None
    processed: bool = False
    processed_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    sync_version: int = 1

    class Config:
        orm_mode = True


class CalendarWebhookEventSchema(BaseModel):
    """Google Calendar webhook event schema."""
    id: int
    webhook_id: str
    channel_id: str
    resource_id: str
    calendar_id: str
    calendar_summary: str
    event_type: str
    event_id: Optional[str] = None
    event_time: datetime
    raw_payload: Dict[str, Any]
    processed: bool = False
    processed_at: Optional[datetime] = None
    discord_message_id: Optional[str] = None
    discord_channel_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    class Config:
        orm_mode = True


class CalendarEventCreate(BaseModel):
    """Schema for creating a new calendar event."""
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    attendees: Optional[List[CalendarEventAttendee]] = None
    reminders: Optional[List[CalendarEventReminder]] = None
    visibility: CalendarEventVisibility = CalendarEventVisibility.default


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event."""
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    attendees: Optional[List[CalendarEventAttendee]] = None
    reminders: Optional[List[CalendarEventReminder]] = None
    visibility: Optional[CalendarEventVisibility] = None


class CalendarListResponse(BaseModel):
    """Response schema for calendar list."""
    calendars: List[GoogleCalendarSchema]
    total: int


class CalendarEventListResponse(BaseModel):
    """Response schema for event list."""
    events: List[CalendarEventSchema]
    total: int
    next_page_token: Optional[str] = None


class CalendarSyncRequest(BaseModel):
    """Schema for calendar sync request."""
    calendar_id: str
    sync_token: Optional[str] = None
    max_results: int = Field(default=100, ge=1, le=2500)


class CalendarWebhookSubscription(BaseModel):
    """Schema for webhook subscription."""
    calendar_id: str
    webhook_url: str
    channel_id: str
    resource_id: str
    expiration: datetime
    is_active: bool = True
