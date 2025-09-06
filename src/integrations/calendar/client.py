"""Google Calendar API client."""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API configuration
GOOGLE_CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/callback")


class GoogleCalendarClient:
    """Google Calendar API client."""

    def __init__(self, credentials: Optional[Credentials] = None):
        """Initialize the Google Calendar client."""
        self.credentials = credentials
        self.service = None
        self._build_service()

    def _build_service(self) -> None:
        """Build the Google Calendar service."""
        if self.credentials:
            try:
                self.service = build('calendar', 'v3', credentials=self.credentials)
            except Exception as e:
                logger.error(f"Failed to build Google Calendar service: {e}")
                self.service = None

    def refresh_credentials(self) -> bool:
        """Refresh expired credentials."""
        if not self.credentials:
            return False
        
        try:
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._build_service()
                return True
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
        
        return False

    @classmethod
    def create_flow(cls) -> Flow:
        """Create OAuth2 flow for authentication."""
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GOOGLE_CALENDAR_SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        return flow

    @classmethod
    def from_credentials_dict(cls, credentials_dict: Dict[str, Any]) -> 'GoogleCalendarClient':
        """Create client from credentials dictionary."""
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        return cls(credentials)

    def get_authorization_url(self) -> str:
        """Get authorization URL for OAuth flow."""
        flow = self.create_flow()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url

    def exchange_code_for_credentials(self, code: str) -> Credentials:
        """Exchange authorization code for credentials."""
        flow = self.create_flow()
        flow.fetch_token(code=code)
        return flow.credentials

    # Calendar operations
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List user's calendars."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except HttpError as e:
            logger.error(f"Error listing calendars: {e}")
            raise

    def get_calendar(self, calendar_id: str) -> Dict[str, Any]:
        """Get specific calendar details."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            return self.service.calendars().get(calendarId=calendar_id).execute()
        except HttpError as e:
            logger.error(f"Error getting calendar {calendar_id}: {e}")
            raise

    # Event operations
    def list_events(
        self,
        calendar_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        single_events: bool = True,
        order_by: str = 'startTime',
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List events from a calendar."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            # Set default time range if not provided
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = time_min + timedelta(days=30)
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=single_events,
                orderBy=order_by,
                pageToken=page_token
            ).execute()
            
            return events_result
        except HttpError as e:
            logger.error(f"Error listing events for calendar {calendar_id}: {e}")
            raise

    def get_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """Get specific event details."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            return self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
        except HttpError as e:
            logger.error(f"Error getting event {event_id} from calendar {calendar_id}: {e}")
            raise

    def create_event(self, calendar_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            return self.service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
        except HttpError as e:
            logger.error(f"Error creating event in calendar {calendar_id}: {e}")
            raise

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing event."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            return self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
        except HttpError as e:
            logger.error(f"Error updating event {event_id} in calendar {calendar_id}: {e}")
            raise

    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error deleting event {event_id} from calendar {calendar_id}: {e}")
            raise

    def watch_events(
        self,
        calendar_id: str,
        webhook_url: str,
        expiration: datetime
    ) -> Dict[str, Any]:
        """Set up event watching for webhooks."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            watch_request = {
                'id': f"calendar-{calendar_id}-{int(datetime.utcnow().timestamp())}",
                'type': 'web_hook',
                'address': webhook_url,
                'expiration': int(expiration.timestamp() * 1000)  # Convert to milliseconds
            }
            
            return self.service.events().watch(
                calendarId=calendar_id,
                body=watch_request
            ).execute()
        except HttpError as e:
            logger.error(f"Error setting up watch for calendar {calendar_id}: {e}")
            raise

    def stop_watching(self, resource_id: str, channel_id: str) -> bool:
        """Stop watching events."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            self.service.channels().stop(
                body={
                    'id': resource_id,
                    'resourceId': resource_id
                }
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error stopping watch {resource_id}: {e}")
            raise

    def sync_events(
        self,
        calendar_id: str,
        sync_token: Optional[str] = None,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """Sync events using sync token for incremental updates."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            params = {
                'calendarId': calendar_id,
                'maxResults': max_results
            }
            
            if sync_token:
                params['syncToken'] = sync_token
            else:
                # First sync - get all events from now
                params['timeMin'] = datetime.utcnow().isoformat() + 'Z'
            
            return self.service.events().list(**params).execute()
        except HttpError as e:
            logger.error(f"Error syncing events for calendar {calendar_id}: {e}")
            raise

    def get_free_busy(
        self,
        calendar_ids: List[str],
        time_min: datetime,
        time_max: datetime
    ) -> Dict[str, Any]:
        """Get free/busy information for calendars."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        try:
            body = {
                'timeMin': time_min.isoformat() + 'Z',
                'timeMax': time_max.isoformat() + 'Z',
                'items': [{'id': cal_id} for cal_id in calendar_ids]
            }
            
            return self.service.freebusy().query(body=body).execute()
        except HttpError as e:
            logger.error(f"Error getting free/busy info: {e}")
            raise
