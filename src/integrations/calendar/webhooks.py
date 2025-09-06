"""Google Calendar webhook handlers."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from sqlalchemy import select, and_

from src.utils.database import get_db_session
from src.models.calendar import GoogleCalendar, CalendarWebhookEvent, CalendarEvent
from src.integrations.calendar import operations

logger = logging.getLogger(__name__)


async def handle_calendar_webhook(request: Request) -> Dict[str, str]:
    """Handle Google Calendar webhook notifications."""
    try:
        # Get the raw body
        body = await request.body()
        
        # Parse the webhook data
        webhook_data = json.loads(body)
        
        # Extract webhook information
        webhook_id = webhook_data.get('id')
        channel_id = webhook_data.get('channelId')
        resource_id = webhook_data.get('resourceId')
        event_type = webhook_data.get('type', 'sync')
        
        logger.info(f"Received calendar webhook: {webhook_id}, type: {event_type}")
        
        # Store webhook event in database
        await store_webhook_event(
            webhook_id=webhook_id,
            channel_id=channel_id,
            resource_id=resource_id,
            event_type=event_type,
            raw_payload=webhook_data
        )
        
        # Process the webhook based on type
        if event_type == 'sync':
            await process_sync_webhook(webhook_data)
        elif event_type in ['create', 'update', 'delete']:
            await process_event_webhook(webhook_data)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
        
        return {"status": "success"}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing calendar webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def store_webhook_event(
    webhook_id: str,
    channel_id: str,
    resource_id: str,
    event_type: str,
    raw_payload: Dict[str, Any]
) -> None:
    """Store webhook event in database."""
    async_session = get_db_session()
    async with async_session() as db:
        try:
            # Get calendar information
            calendar_id = raw_payload.get('calendarId', '')
            calendar_summary = raw_payload.get('calendarSummary', 'Unknown Calendar')
            
            # Create webhook event record
            webhook_event = CalendarWebhookEvent(
                webhook_id=webhook_id,
                channel_id=channel_id,
                resource_id=resource_id,
                calendar_id=calendar_id,
                calendar_summary=calendar_summary,
                event_type=event_type,
                event_id=raw_payload.get('eventId'),
                event_time=datetime.utcnow(),
                raw_payload=raw_payload
            )
            
            db.add(webhook_event)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error storing webhook event: {e}")
            await db.rollback()


async def process_sync_webhook(webhook_data: Dict[str, Any]) -> None:
    """Process sync webhook to get updated events."""
    try:
        calendar_id = webhook_data.get('calendarId')
        if not calendar_id:
            logger.warning("No calendar ID in sync webhook")
            return
        
        # Get the sync token for incremental updates
        sync_token = webhook_data.get('syncToken')
        
        # Find the calendar in our database
        async_session = get_db_session()
        async with async_session() as db:
            result = await db.execute(
                select(GoogleCalendar).where(GoogleCalendar.calendar_id == calendar_id)
            )
            calendar = result.scalar_one_or_none()
            
            if not calendar:
                logger.warning(f"Calendar {calendar_id} not found in database")
                return
            
            # Get the user's calendar client
            client = await operations.get_calendar_client(calendar.user_id)
            if not client:
                logger.warning(f"No client found for user {calendar.user_id}")
                return
            
            # Sync events
            events_result = client.sync_events(
                calendar_id=calendar_id,
                sync_token=sync_token,
                max_results=100
            )
            
            # Process the events
            events = events_result.get('items', [])
            for event_data in events:
                await operations.store_calendar_event(
                    calendar.user_id, calendar_id, event_data
                )
            
            # Update calendar sync info
            calendar.last_sync = datetime.utcnow()
            await db.commit()
            
            # Send Discord notifications if configured
            if calendar.discord_channel_id:
                await send_calendar_notification(
                    calendar, events, "sync"
                )
            
    except Exception as e:
        logger.error(f"Error processing sync webhook: {e}")


async def process_event_webhook(webhook_data: Dict[str, Any]) -> None:
    """Process individual event webhook (create, update, delete)."""
    try:
        calendar_id = webhook_data.get('calendarId')
        event_id = webhook_data.get('eventId')
        event_type = webhook_data.get('type')
        
        if not calendar_id or not event_id:
            logger.warning("Missing calendar ID or event ID in event webhook")
            return
        
        # Find the calendar in our database
        async_session = get_db_session()
        async with async_session() as db:
            result = await db.execute(
                select(GoogleCalendar).where(GoogleCalendar.calendar_id == calendar_id)
            )
            calendar = result.scalar_one_or_none()
            
            if not calendar:
                logger.warning(f"Calendar {calendar_id} not found in database")
                return
            
            # Get the user's calendar client
            client = await operations.get_calendar_client(calendar.user_id)
            if not client:
                logger.warning(f"No client found for user {calendar.user_id}")
                return
            
            if event_type == 'delete':
                # Handle event deletion
                await operations.delete_calendar_event_from_db(calendar_id, event_id)
                await send_event_notification(calendar, event_id, "deleted")
            else:
                # Handle event creation or update
                try:
                    event_data = client.get_event(calendar_id, event_id)
                    await operations.store_calendar_event(
                        calendar.user_id, calendar_id, event_data
                    )
                    await send_event_notification(calendar, event_id, event_type)
                except Exception as e:
                    logger.error(f"Error fetching event {event_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error processing event webhook: {e}")


async def send_calendar_notification(
    calendar: GoogleCalendar,
    events: list,
    notification_type: str
) -> None:
    """Send Discord notification for calendar events."""
    try:
        # This would need access to the Discord bot instance
        # For now, we'll just log the notification
        logger.info(f"Would send {notification_type} notification for calendar {calendar.calendar_id} with {len(events)} events")
        
        # TODO: Implement actual Discord notification sending
        # This would involve:
        # 1. Getting the Discord bot instance
        # 2. Finding the channel by ID
        # 3. Creating an embed with event details
        # 4. Sending the message
        
    except Exception as e:
        logger.error(f"Error sending calendar notification: {e}")


async def send_event_notification(
    calendar: GoogleCalendar,
    event_id: str,
    event_type: str
) -> None:
    """Send Discord notification for a specific event."""
    try:
        # This would need access to the Discord bot instance
        logger.info(f"Would send {event_type} notification for event {event_id} in calendar {calendar.calendar_id}")
        
        # TODO: Implement actual Discord notification sending
        # This would involve:
        # 1. Getting the Discord bot instance
        # 2. Finding the channel by ID
        # 3. Creating an embed with event details
        # 4. Sending the message
        
    except Exception as e:
        logger.error(f"Error sending event notification: {e}")


async def setup_calendar_watch(
    user_id: str,
    calendar_id: str,
    webhook_url: str,
    expiration_hours: int = 24
) -> Optional[Dict[str, Any]]:
    """Set up calendar watching for webhooks."""
    try:
        client = await operations.get_calendar_client(user_id)
        if not client:
            logger.error(f"No client found for user {user_id}")
            return None
        
        expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        watch_result = client.watch_events(
            calendar_id=calendar_id,
            webhook_url=webhook_url,
            expiration=expiration
        )
        
        # Store watch information in database
        async_session = get_db_session()
        async with async_session() as db:
            result = await db.execute(
                select(GoogleCalendar).where(
                    and_(
                        GoogleCalendar.user_id == user_id,
                        GoogleCalendar.calendar_id == calendar_id
                    )
                )
            )
            calendar = result.scalar_one()
            
            # Store watch details (you might want to add these fields to the model)
            # calendar.watch_resource_id = watch_result.get('resourceId')
            # calendar.watch_channel_id = watch_result.get('id')
            # calendar.watch_expiration = expiration
            
            await db.commit()
        
        return watch_result
        
    except Exception as e:
        logger.error(f"Error setting up calendar watch: {e}")
        return None


async def stop_calendar_watch(
    user_id: str,
    calendar_id: str,
    resource_id: str
) -> bool:
    """Stop calendar watching."""
    try:
        client = await operations.get_calendar_client(user_id)
        if not client:
            logger.error(f"No client found for user {user_id}")
            return False
        
        success = client.stop_watching(resource_id, resource_id)
        
        if success:
            # Clear watch information from database
            async_session = get_db_session()
            async with async_session() as db:
                result = await db.execute(
                    select(GoogleCalendar).where(
                        and_(
                            GoogleCalendar.user_id == user_id,
                            GoogleCalendar.calendar_id == calendar_id
                        )
                    )
                )
                calendar = result.scalar_one()
                
                # Clear watch details
                # calendar.watch_resource_id = None
                # calendar.watch_channel_id = None
                # calendar.watch_expiration = None
                
                await db.commit()
        
        return success
        
    except Exception as e:
        logger.error(f"Error stopping calendar watch: {e}")
        return False
