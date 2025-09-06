"""Google Calendar operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import NoResultFound

from src.integrations.calendar.client import GoogleCalendarClient
from src.utils.database import get_db_session
from src.models.calendar import GoogleCalendar, CalendarEvent, CalendarWebhookEvent
from src.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventAttendee,
    CalendarEventReminder,
    CalendarEventReminderMethod
)

logger = logging.getLogger(__name__)


async def get_calendar_client(user_id: str) -> Optional[GoogleCalendarClient]:
    """Get Google Calendar client for a user."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(GoogleCalendar).where(
                    and_(
                        GoogleCalendar.user_id == user_id,
                        GoogleCalendar.is_active == True
                    )
                )
            )
            calendar = result.scalar_one()
            
            if not calendar.access_token:
                logger.warning(f"No access token for user {user_id}")
                return None
            
            # Create credentials from stored tokens
            credentials_dict = {
                'token': calendar.access_token,
                'refresh_token': calendar.refresh_token,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': calendar.user_id,  # This should be the actual client ID
                'client_secret': '',  # Not stored for security
                'scopes': ['https://www.googleapis.com/auth/calendar']
            }
            
            return GoogleCalendarClient.from_credentials_dict(credentials_dict)
        except NoResultFound:
            logger.warning(f"No active calendar found for user {user_id}")
            return None


async def list_user_calendars(user_id: str) -> List[Dict[str, Any]]:
    """List all calendars for a user."""
    client = await get_calendar_client(user_id)
    if not client:
        return []
    
    try:
        calendars = client.list_calendars()
        return calendars
    except Exception as e:
        logger.error(f"Error listing calendars for user {user_id}: {e}")
        return []


async def get_calendar_events(
    user_id: str,
    calendar_id: str,
    days_ahead: int = 7,
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """Get events from a specific calendar."""
    client = await get_calendar_client(user_id)
    if not client:
        return []
    
    try:
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        
        events_result = client.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results
        )
        
        return events_result.get('items', [])
    except Exception as e:
        logger.error(f"Error getting events for calendar {calendar_id}: {e}")
        return []


async def create_calendar_event(
    user_id: str,
    calendar_id: str,
    event_data: CalendarEventCreate
) -> Optional[Dict[str, Any]]:
    """Create a new calendar event."""
    client = await get_calendar_client(user_id)
    if not client:
        return None
    
    try:
        # Convert Pydantic model to Google Calendar API format
        google_event = {
            'summary': event_data.summary,
            'description': event_data.description,
            'location': event_data.location,
            'start': {
                'dateTime': event_data.start_time.isoformat() + 'Z',
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data.end_time.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
        }
        
        if event_data.is_all_day:
            google_event['start'] = {'date': event_data.start_time.date().isoformat()}
            google_event['end'] = {'date': event_data.end_time.date().isoformat()}
        
        if event_data.attendees:
            google_event['attendees'] = [
                {
                    'email': attendee.email,
                    'displayName': attendee.display_name,
                    'responseStatus': attendee.response_status,
                    'optional': attendee.optional,
                    'resource': attendee.resource
                }
                for attendee in event_data.attendees
            ]
        
        if event_data.reminders:
            google_event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {
                        'method': reminder.method.value,
                        'minutes': reminder.minutes
                    }
                    for reminder in event_data.reminders
                ]
            }
        
        google_event['visibility'] = event_data.visibility.value
        
        created_event = client.create_event(calendar_id, google_event)
        
        # Store event in database
        await store_calendar_event(user_id, calendar_id, created_event)
        
        return created_event
    except Exception as e:
        logger.error(f"Error creating event in calendar {calendar_id}: {e}")
        return None


async def update_calendar_event(
    user_id: str,
    calendar_id: str,
    event_id: str,
    event_data: CalendarEventUpdate
) -> Optional[Dict[str, Any]]:
    """Update an existing calendar event."""
    client = await get_calendar_client(user_id)
    if not client:
        return None
    
    try:
        # Get existing event
        existing_event = client.get_event(calendar_id, event_id)
        
        # Update fields that are provided
        if event_data.summary is not None:
            existing_event['summary'] = event_data.summary
        if event_data.description is not None:
            existing_event['description'] = event_data.description
        if event_data.location is not None:
            existing_event['location'] = event_data.location
        if event_data.start_time is not None:
            existing_event['start'] = {
                'dateTime': event_data.start_time.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
        if event_data.end_time is not None:
            existing_event['end'] = {
                'dateTime': event_data.end_time.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
        if event_data.is_all_day is not None:
            if event_data.is_all_day:
                existing_event['start'] = {'date': event_data.start_time.date().isoformat()}
                existing_event['end'] = {'date': event_data.end_time.date().isoformat()}
        
        if event_data.attendees is not None:
            existing_event['attendees'] = [
                {
                    'email': attendee.email,
                    'displayName': attendee.display_name,
                    'responseStatus': attendee.response_status,
                    'optional': attendee.optional,
                    'resource': attendee.resource
                }
                for attendee in event_data.attendees
            ]
        
        if event_data.reminders is not None:
            existing_event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {
                        'method': reminder.method.value,
                        'minutes': reminder.minutes
                    }
                    for reminder in event_data.reminders
                ]
            }
        
        if event_data.visibility is not None:
            existing_event['visibility'] = event_data.visibility.value
        
        updated_event = client.update_event(calendar_id, event_id, existing_event)
        
        # Update event in database
        await update_calendar_event_in_db(user_id, calendar_id, updated_event)
        
        return updated_event
    except Exception as e:
        logger.error(f"Error updating event {event_id} in calendar {calendar_id}: {e}")
        return None


async def delete_calendar_event(
    user_id: str,
    calendar_id: str,
    event_id: str
) -> bool:
    """Delete a calendar event."""
    client = await get_calendar_client(user_id)
    if not client:
        return False
    
    try:
        success = client.delete_event(calendar_id, event_id)
        if success:
            # Remove event from database
            await delete_calendar_event_from_db(calendar_id, event_id)
        return success
    except Exception as e:
        logger.error(f"Error deleting event {event_id} from calendar {calendar_id}: {e}")
        return False


async def store_calendar_event(
    user_id: str,
    calendar_id: str,
    event_data: Dict[str, Any]
) -> None:
    """Store calendar event in database."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            # Parse event data
            start_time = datetime.fromisoformat(
                event_data.get('start', {}).get('dateTime', '').replace('Z', '+00:00')
            )
            end_time = datetime.fromisoformat(
                event_data.get('end', {}).get('dateTime', '').replace('Z', '+00:00')
            )
            
            # Check if event already exists
            result = await db.execute(
                select(CalendarEvent).where(
                    and_(
                        CalendarEvent.event_id == event_data['id'],
                        CalendarEvent.calendar_id == calendar_id
                    )
                )
            )
            existing_event = result.scalar_one_or_none()
            
            if existing_event:
                # Update existing event
                existing_event.summary = event_data.get('summary', '')
                existing_event.description = event_data.get('description')
                existing_event.location = event_data.get('location')
                existing_event.start_time = start_time
                existing_event.end_time = end_time
                existing_event.is_all_day = 'date' in event_data.get('start', {})
                existing_event.status = event_data.get('status', 'confirmed')
                existing_event.visibility = event_data.get('visibility', 'default')
                existing_event.attendees = event_data.get('attendees')
                existing_event.organizer_email = event_data.get('organizer', {}).get('email')
                existing_event.organizer_name = event_data.get('organizer', {}).get('displayName')
                existing_event.reminders = event_data.get('reminders')
                existing_event.raw_data = event_data
                existing_event.last_modified = datetime.utcnow()
                existing_event.sync_version += 1
            else:
                # Create new event
                new_event = CalendarEvent(
                    event_id=event_data['id'],
                    calendar_id=calendar_id,
                    summary=event_data.get('summary', ''),
                    description=event_data.get('description'),
                    location=event_data.get('location'),
                    start_time=start_time,
                    end_time=end_time,
                    is_all_day='date' in event_data.get('start', {}),
                    status=event_data.get('status', 'confirmed'),
                    visibility=event_data.get('visibility', 'default'),
                    attendees=event_data.get('attendees'),
                    organizer_email=event_data.get('organizer', {}).get('email'),
                    organizer_name=event_data.get('organizer', {}).get('displayName'),
                    reminders=event_data.get('reminders'),
                    raw_data=event_data
                )
                db.add(new_event)
            
            await db.commit()
        except Exception as e:
            logger.error(f"Error storing calendar event: {e}")
            await db.rollback()


async def update_calendar_event_in_db(
    user_id: str,
    calendar_id: str,
    event_data: Dict[str, Any]
) -> None:
    """Update calendar event in database."""
    await store_calendar_event(user_id, calendar_id, event_data)


async def delete_calendar_event_from_db(
    calendar_id: str,
    event_id: str
) -> None:
    """Delete calendar event from database."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(CalendarEvent).where(
                    and_(
                        CalendarEvent.event_id == event_id,
                        CalendarEvent.calendar_id == calendar_id
                    )
                )
            )
            event = result.scalar_one_or_none()
            
            if event:
                await db.delete(event)
                await db.commit()
        except Exception as e:
            logger.error(f"Error deleting calendar event from database: {e}")
            await db.rollback()


async def get_upcoming_events(
    user_id: str,
    calendar_id: Optional[str] = None,
    hours_ahead: int = 24
) -> List[Dict[str, Any]]:
    """Get upcoming events for a user."""
    if calendar_id:
        calendars = [{'id': calendar_id}]
    else:
        calendars = await list_user_calendars(user_id)
    
    all_events = []
    for calendar in calendars:
        events = await get_calendar_events(
            user_id,
            calendar['id'],
            days_ahead=hours_ahead // 24 + 1
        )
        all_events.extend(events)
    
    # Sort by start time
    all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', ''))
    
    return all_events


async def subscribe_calendar_to_discord(
    user_id: str,
    calendar_id: str,
    discord_channel_id: str
) -> bool:
    """Subscribe a Discord channel to calendar events."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(GoogleCalendar).where(
                    and_(
                        GoogleCalendar.user_id == user_id,
                        GoogleCalendar.calendar_id == calendar_id
                    )
                )
            )
            calendar = result.scalar_one()
            calendar.discord_channel_id = discord_channel_id
            calendar.is_active = True
            await db.commit()
            return True
        except NoResultFound:
            logger.warning(f"Calendar {calendar_id} not found for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error subscribing calendar to Discord: {e}")
            await db.rollback()
            return False


async def unsubscribe_calendar_from_discord(
    user_id: str,
    calendar_id: str,
    discord_channel_id: str
) -> bool:
    """Unsubscribe a Discord channel from calendar events."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            result = await db.execute(
                select(GoogleCalendar).where(
                    and_(
                        GoogleCalendar.user_id == user_id,
                        GoogleCalendar.calendar_id == calendar_id,
                        GoogleCalendar.discord_channel_id == discord_channel_id
                    )
                )
            )
            calendar = result.scalar_one()
            calendar.discord_channel_id = None
            await db.commit()
            return True
        except NoResultFound:
            logger.warning(f"Calendar subscription not found")
            return False
        except Exception as e:
            logger.error(f"Error unsubscribing calendar from Discord: {e}")
            await db.rollback()
            return False
