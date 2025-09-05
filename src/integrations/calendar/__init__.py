"""Google Calendar integration module."""

from .client import GoogleCalendarClient
from .operations import (
    get_calendar_client,
    list_user_calendars,
    get_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    get_upcoming_events,
    subscribe_calendar_to_discord,
    unsubscribe_calendar_from_discord
)
from .webhooks import (
    handle_calendar_webhook,
    setup_calendar_watch,
    stop_calendar_watch
)

__all__ = [
    # Client
    "GoogleCalendarClient",
    
    # Operations
    "get_calendar_client",
    "list_user_calendars",
    "get_calendar_events",
    "create_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
    "get_upcoming_events",
    "subscribe_calendar_to_discord",
    "unsubscribe_calendar_from_discord",
    
    # Webhooks
    "handle_calendar_webhook",
    "setup_calendar_watch",
    "stop_calendar_watch"
]
