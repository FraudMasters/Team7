"""
Google Calendar service implementation for external calendar integration.

This module provides integration with Google Calendar API, enabling the
application to create, update, and manage calendar events directly on
users' Google Calendars.

Key features:
- OAuth 2.0 authentication with automatic token refresh
- Full CRUD operations for calendar events
- Availability checking and conflict detection
- Webhook notifications for real-time sync
- Google Meet meeting link generation

Google Calendar API Documentation:
https://developers.google.com/calendar/api/v3/reference
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config import settings
from backend.services.calendar_service import (
    AvailabilitySlot,
    AuthenticationError,
    CalendarEvent,
    CalendarService,
    CalendarServiceError,
    EventConflictError,
    RateLimitError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)


class GoogleCalendarService(CalendarService):
    """
    Google Calendar API service implementation.

    This service integrates with Google Calendar API v3 to manage events
    on user calendars. It handles authentication, event CRUD operations,
    availability checking, and webhook management.

    Authentication Flow:
    1. User authorizes via OAuth 2.0
    2. Access token and refresh token stored in database
    3. Access token used for API calls
    4. Token automatically refreshed when expired

    Event Management:
    - Events include title, description, times, attendees, location
    - Google Meet links can be auto-generated
    - Attendees receive email invitations
    - Event updates sync to all participants

    Webhooks:
    - Google uses "push notifications" via channel watches
    - Webhook payload contains event ID and change type
    - Full event details fetched separately

    Example:
        >>> service = GoogleCalendarService(
        ...     access_token="ya29.a0AfH6...",
        ...     refresh_token="1//0g...",
        ...     token_expires_at=datetime(2024, 1, 16, 12, 0),
        ...     calendar_email="user@example.com"
        ... )
        >>> event = service.create_event(
        ...     title="Technical Interview",
        ...     start_time=datetime(2024, 1, 15, 10, 0),
        ...     end_time=datetime(2024, 1, 15, 11, 0),
        ...     attendees=["candidate@example.com"]
        ... )
    """

    # Google Calendar API constants
    API_SERVICE_NAME = "calendar"
    API_VERSION = "v3"
    DEFAULT_CALENDAR_ID = "primary"

    # Google Calendar API scopes
    SCOPE_CALENDAR = "https://www.googleapis.com/auth/calendar"
    SCOPE_EVENTS = "https://www.googleapis.com/auth/calendar.events"

    # Event status mapping
    EVENT_STATUS_CONFIRMED = "confirmed"
    EVENT_STATUS_TENTATIVE = "tentative"
    EVENT_STATUS_CANCELLED = "cancelled"

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        calendar_email: str,
        calendar_id: Optional[str] = None,
    ) -> None:
        """
        Initialize Google Calendar service.

        Args:
            access_token: OAuth access token for API calls
            refresh_token: OAuth refresh token for token renewal
            token_expires_at: When the access token expires
            calendar_email: Email address of the connected calendar
            calendar_id: Optional Google Calendar ID (defaults to 'primary')
        """
        super().__init__(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
            calendar_id=calendar_id,
        )

        # Initialize Google API service (will be built when needed)
        self._service = None

    @property
    def provider_name(self) -> str:
        """Get the human-readable provider name."""
        return "Google Calendar"

    def _get_default_calendar_id(self) -> str:
        """Get the default calendar ID for Google."""
        return self.DEFAULT_CALENDAR_ID

    def _get_google_service(self):
        """
        Build and return the Google Calendar API service object.

        Creates a new service object if one doesn't exist or token was refreshed.
        Uses the current access token for authentication.

        Returns:
            Google Calendar API service object
        """
        if self._service is None:
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_calendar_client_id,
                client_secret=settings.google_calendar_client_secret,
                scopes=[self.SCOPE_CALENDAR, self.SCOPE_EVENTS],
            )

            self._service = build(
                self.API_SERVICE_NAME,
                self.API_VERSION,
                credentials=credentials,
                cache_discovery=False,
            )
            logger.debug("Google Calendar API service initialized")

        return self._service

    def _refresh_access_token(self) -> str:
        """
        Refresh the OAuth access token using the refresh token.

        Makes a request to Google's OAuth 2.0 endpoint to exchange the
        refresh token for a new access token.

        Returns:
            New access token

        Raises:
            TokenExpiredError: If token refresh fails
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_calendar_client_id,
                client_secret=settings.google_calendar_client_secret,
                scopes=[self.SCOPE_CALENDAR, self.SCOPE_EVENTS],
            )

            # Refresh the token
            credentials.refresh(requests.Request())
            new_token = credentials.token
            new_expiry = datetime.utcnow() + timedelta(
                seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp()
            )

            logger.info(f"Access token refreshed for {self.calendar_email}")

            # Update service object with new credentials
            self._service = None  # Force rebuild on next use

            return new_token

        except Exception as e:
            logger.error(f"Failed to refresh Google Calendar token: {e}")
            raise TokenExpiredError(
                f"Failed to refresh access token: {e}",
                provider=self.provider_name,
            )

    def _parse_google_event(self, google_event: Dict[str, Any]) -> CalendarEvent:
        """
        Parse a Google Calendar event into our standardized CalendarEvent model.

        Args:
            google_event: Raw event data from Google Calendar API

        Returns:
            Standardized CalendarEvent object
        """
        # Parse start and end times
        start_data = google_event.get("start", {})
        end_data = google_event.get("end", {})

        # Handle both date and dateTime formats
        start_time_str = start_data.get("dateTime") or start_data.get("date")
        end_time_str = end_data.get("dateTime") or end_data.get("date")

        # Parse ISO 8601 format
        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))

        # Convert to UTC if timezone aware
        if start_time.tzinfo is not None:
            start_time = start_time.utctimetuple()
            start_time = datetime(*start_time[:6])
        if end_time.tzinfo is not None:
            end_time = end_time.utctimetuple()
            end_time = datetime(*end_time[:6])

        # Extract attendees
        attendees = []
        for attendee in google_event.get("attendees", []):
            email = attendee.get("email")
            if email:
                attendees.append(email)

        # Extract meeting link (Google Meet)
        meeting_link = google_event.get("hangoutLink") or google_event.get(
            "conferenceData", {}
        ).get("entryPoints", [{}])[0].get("uri")

        # Map status
        status = google_event.get("status", "confirmed").lower()
        if status == "cancelled":
            status = self.STATUS_CANCELLED
        elif status == "tentative":
            status = self.STATUS_TENTATIVE
        else:
            status = self.STATUS_CONFIRMED

        return CalendarEvent(
            event_id=google_event["id"],
            title=google_event.get("summary", "No Title"),
            description=google_event.get("description"),
            start_time=start_time,
            end_time=end_time,
            location=google_event.get("location"),
            meeting_link=meeting_link,
            attendees=attendees,
            organizer_email=google_event.get("organizer", {}).get("email", ""),
            status=status,
            provider=self.PROVIDER_GOOGLE,
        )

    def _build_google_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        meeting_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a Google Calendar event dictionary from parameters.

        Args:
            title: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Optional event description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            meeting_link: Optional virtual meeting link

        Returns:
            Google Calendar API event dictionary
        """
        event = {
            "summary": title,
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
        }

        # Add optional fields
        if description:
            event["description"] = description

        if location:
            event["location"] = location

        if meeting_link:
            event["conferenceData"] = {
                "createRequest": {
                    "requestId": f"{start_time.timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        return event

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        meeting_link: Optional[str] = None,
    ) -> CalendarEvent:
        """
        Create a new Google Calendar event.

        Creates an event on the user's Google Calendar and sends email
        invitations to all attendees.

        Args:
            title: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Optional event description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            meeting_link: Optional virtual meeting link (if None, may auto-generate Google Meet)

        Returns:
            Created CalendarEvent with Google-assigned event_id

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded
            EventConflictError: If event conflicts with existing events

        Example:
            >>> event = service.create_event(
            ...     title="Technical Interview",
            ...     start_time=datetime(2024, 1, 15, 14, 0),
            ...     end_time=datetime(2024, 1, 15, 15, 0),
            ...     attendees=["candidate@example.com"],
            ...     description="Discuss Python experience and system design"
            ... )
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            google_event = self._build_google_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees,
                meeting_link=meeting_link,
            )

            # Create conference data if meeting_link requested
            if meeting_link or not location:
                google_event["conferenceDataVersion"] = 1

            logger.info(
                f"Creating Google Calendar event: {title} at {start_time} "
                f"for {len(attendees or [])} attendees"
            )

            # Insert event
            created_event = (
                service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=google_event,
                    sendUpdates="all",  # Send notifications to attendees
                )
                .execute()
            )

            parsed_event = self._parse_google_event(created_event)

            logger.info(
                f"Google Calendar event created: {parsed_event.event_id} "
                f"(Google Meet: {parsed_event.meeting_link})"
            )

            return parsed_event

        except HttpError as e:
            error_details = e.error_details if hasattr(e, "error_details") else []

            # Handle rate limiting
            if e.resp.status == 429:
                retry_after = None
                for detail in error_details:
                    if detail.get("type") == "rateLimitExceeded":
                        retry_after = detail.get("retryAfter")
                        break

                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=retry_after,
                    details={"error": str(e)},
                )

            # Handle authentication errors
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            # Handle conflict errors
            if e.resp.status == 409:
                raise EventConflictError(
                    "Event conflicts with existing event",
                    provider=self.provider_name,
                    conflicting_events=[],
                    details={"error": str(e)},
                )

            # Generic error
            raise CalendarServiceError(
                f"Failed to create event: {e}",
                provider=self.provider_name,
                details={"error": str(e), "status": e.resp.status},
            )

        except Exception as e:
            logger.error(f"Unexpected error creating Google Calendar event: {e}")
            raise CalendarServiceError(
                f"Unexpected error creating event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        meeting_link: Optional[str] = None,
    ) -> CalendarEvent:
        """
        Update an existing Google Calendar event.

        Args:
            event_id: Google event ID
            title: New event title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            location: New location (optional)
            attendees: New attendee list (optional)
            meeting_link: New meeting link (optional)

        Returns:
            Updated CalendarEvent

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded
            CalendarServiceError: If event not found or update fails

        Example:
            >>> updated = service.update_event(
            ...     event_id="abc123xyz",
            ...     start_time=datetime(2024, 1, 15, 15, 0),
            ...     end_time=datetime(2024, 1, 15, 16, 0)
            ... )
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            # Get existing event first
            existing_event = (
                service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            )

            # Build update with only provided fields
            update_data = {}

            if title is not None:
                update_data["summary"] = title

            if start_time is not None:
                update_data["start"] = {
                    "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC",
                }

            if end_time is not None:
                update_data["end"] = {
                    "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC",
                }

            if description is not None:
                update_data["description"] = description

            if location is not None:
                update_data["location"] = location

            if attendees is not None:
                update_data["attendees"] = [{"email": email} for email in attendees]

            if meeting_link is not None:
                update_data["conferenceData"] = {
                    "createRequest": {
                        "requestId": f"{start_time or datetime.utcnow().timestamp()}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                }

            logger.info(f"Updating Google Calendar event: {event_id}")

            # Update event
            updated_event = (
                service.events()
                .patch(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=update_data,
                    sendUpdates="all",  # Send notifications to attendees
                )
                .execute()
            )

            parsed_event = self._parse_google_event(updated_event)

            logger.info(f"Google Calendar event updated: {event_id}")

            return parsed_event

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 404:
                raise CalendarServiceError(
                    f"Event not found: {event_id}",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to update event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error updating Google Calendar event: {e}")
            raise CalendarServiceError(
                f"Unexpected error updating event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a Google Calendar event.

        Args:
            event_id: Google event ID

        Returns:
            True if deletion was successful

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded
            CalendarServiceError: If event not found or deletion fails

        Example:
            >>> success = service.delete_event("abc123xyz")
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            logger.info(f"Deleting Google Calendar event: {event_id}")

            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates="all",  # Send notifications to attendees
            ).execute()

            logger.info(f"Google Calendar event deleted: {event_id}")

            return True

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 404:
                # Event already deleted or doesn't exist
                logger.warning(f"Event not found for deletion: {event_id}")
                return True

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to delete event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error deleting Google Calendar event: {e}")
            raise CalendarServiceError(
                f"Unexpected error deleting event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Retrieve a specific Google Calendar event.

        Args:
            event_id: Google event ID

        Returns:
            CalendarEvent if found, None otherwise

        Raises:
            AuthenticationError: If authentication fails
            CalendarServiceError: If retrieval fails

        Example:
            >>> event = service.get_event("abc123xyz")
            >>> if event:
            ...     print(f"Event: {event.title}")
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            google_event = service.events().get(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()

            return self._parse_google_event(google_event)

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 404:
                logger.warning(f"Event not found: {event_id}")
                return None

            raise CalendarServiceError(
                f"Failed to get event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error getting Google Calendar event: {e}")
            raise CalendarServiceError(
                f"Unexpected error getting event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def list_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """
        List Google Calendar events within a time range.

        Args:
            start_time: Start of time range (defaults to now)
            end_time: End of time range (defaults to 30 days from now)
            limit: Maximum number of events to return

        Returns:
            List of CalendarEvents

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded

        Example:
            >>> events = service.list_events(
            ...     start_time=datetime(2024, 1, 1),
            ...     end_time=datetime(2024, 1, 31),
            ...     limit=50
            ... )
        """
        self._ensure_valid_token()

        if start_time is None:
            start_time = datetime.utcnow()
        if end_time is None:
            end_time = datetime.utcnow() + timedelta(days=30)

        try:
            service = self._get_google_service()

            # List events
            events_result = (
                service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    timeMax=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    maxResults=limit,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            google_events = events_result.get("items", [])

            parsed_events = [self._parse_google_event(e) for e in google_events]

            logger.info(
                f"Listed {len(parsed_events)} Google Calendar events between "
                f"{start_time} and {end_time}"
            )

            return parsed_events

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to list events: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error listing Google Calendar events: {e}")
            raise CalendarServiceError(
                f"Unexpected error listing events: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def get_availability(
        self,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
    ) -> List[AvailabilitySlot]:
        """
        Check availability for scheduling within a time range.

        Queries Google Calendar's free/busy API to find time slots that
        are available for booking events of the specified duration.

        Args:
            start_time: Start of search window (UTC)
            end_time: End of search window (UTC)
            duration_minutes: Required duration for booking

        Returns:
            List of AvailabilitySlots indicating free/busy times

        Example:
            >>> slots = service.get_availability(
            ...     start_time=datetime(2024, 1, 15, 9, 0),
            ...     end_time=datetime(2024, 1, 15, 17, 0),
            ...     duration_minutes=60
            ... )
            >>> free_slots = [s for s in slots if s.available]
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            # Use free/busy query
            body = {
                "timeMin": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "timeMax": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "items": [{"id": self.calendar_id}],
            }

            freebusy_result = service.freebusy().query(body=body).execute()

            # Get busy periods
            calendars = freebusy_result.get("calendars", {})
            calendar_data = calendars.get(self.calendar_id, {})
            busy_periods = calendar_data.get("busy", [])

            # Build availability slots
            slots = []
            current_time = start_time
            duration_delta = timedelta(minutes=duration_minutes)

            # Sort busy periods by start time
            busy_periods.sort(key=lambda x: x.get("start", ""))

            for busy in busy_periods:
                busy_start = datetime.fromisoformat(
                    busy["start"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                busy_end = datetime.fromisoformat(
                    busy["end"].replace("Z", "+00:00")
                ).replace(tzinfo=None)

                # Add free slot before this busy period
                if current_time < busy_start:
                    # Check if slot is long enough
                    if (busy_start - current_time) >= duration_delta:
                        slots.append(
                            AvailabilitySlot(
                                start_time=current_time,
                                end_time=busy_start,
                                available=True,
                                confidence=1.0,
                            )
                        )
                    else:
                        # Slot too short, mark as busy
                        slots.append(
                            AvailabilitySlot(
                                start_time=current_time,
                                end_time=busy_start,
                                available=False,
                                confidence=1.0,
                            )
                        )

                # Add busy slot
                slots.append(
                    AvailabilitySlot(
                        start_time=busy_start,
                        end_time=busy_end,
                        available=False,
                        confidence=1.0,
                    )
                )

                current_time = max(current_time, busy_end)

            # Add final free slot if any
            if current_time < end_time:
                if (end_time - current_time) >= duration_delta:
                    slots.append(
                        AvailabilitySlot(
                            start_time=current_time,
                            end_time=end_time,
                            available=True,
                            confidence=1.0,
                        )
                    )
                else:
                    slots.append(
                        AvailabilitySlot(
                            start_time=current_time,
                            end_time=end_time,
                            available=False,
                            confidence=1.0,
                        )
                    )

            logger.info(
                f"Generated {len(slots)} availability slots, "
                f"{sum(1 for s in slots if s.available)} free"
            )

            return slots

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to get availability: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error getting Google Calendar availability: {e}")
            raise CalendarServiceError(
                f"Unexpected error getting availability: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def check_conflict(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[str] = None,
    ) -> Tuple[bool, List[CalendarEvent]]:
        """
        Check if a time slot conflicts with existing Google Calendar events.

        Args:
            start_time: Proposed start time (UTC)
            end_time: Proposed end time (UTC)
            exclude_event_id: Optional event ID to exclude from conflict check

        Returns:
            Tuple of (has_conflict, conflicting_events)

        Example:
            >>> has_conflict, conflicts = service.check_conflict(
            ...     start_time=datetime(2024, 1, 15, 10, 0),
            ...     end_time=datetime(2024, 1, 15, 11, 0)
            ... )
            >>> if has_conflict:
            ...     print(f"Conflicts with {len(conflicts)} events")
        """
        self._ensure_valid_token()

        try:
            # List events in the time range
            events = self.list_events(start_time=start_time, end_time=end_time, limit=100)

            # Filter for conflicts
            conflicting_events = []
            for event in events:
                # Exclude specified event
                if exclude_event_id and event.event_id == exclude_event_id:
                    continue

                # Check for time overlap
                if not (event.end_time <= start_time or event.start_time >= end_time):
                    # Events overlap
                    conflicting_events.append(event)

            has_conflict = len(conflicting_events) > 0

            logger.info(
                f"Conflict check for {start_time} - {end_time}: "
                f"{'conflict found' if has_conflict else 'no conflict'} "
                f"({len(conflicting_events)} conflicting events)"
            )

            return has_conflict, conflicting_events

        except Exception as e:
            logger.error(f"Error checking Google Calendar conflicts: {e}")
            # On error, assume conflict to be safe
            return True, []

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook notification from Google Calendar.

        Google Calendar webhooks (push notifications) include:
        - Channel ID and expiration
        - Event ID and resource state
        - Full event details fetched separately

        Args:
            payload: Webhook payload from Google

        Returns:
            Dictionary with action, event_id, event, and raw payload

        Example:
            >>> result = service.handle_webhook(webhook_data)
            >>> if result['action'] == 'deleted':
            ...     cancel_interview(result['event_id'])
        """
        try:
            # Extract notification data
            headers = payload.get("headers", {})
            body = payload.get("body", {})

            # Google sends notification in headers
            resource_id = headers.get("X-Goog-Resource-ID")
            resource_state = headers.get("X-Goog-Resource-State")
            resource_uri = headers.get("X-Goog-Resource-URI")

            if not resource_id:
                raise CalendarServiceError(
                    "Invalid webhook payload: missing resource ID",
                    provider=self.provider_name,
                    details={"payload": payload},
                )

            # Extract event ID from resource URI
            event_id = None
            if resource_uri:
                # URI format: .../events/{eventId}
                parts = resource_uri.split("/events/")
                if len(parts) > 1:
                    event_id = parts[1].split("?")[0]

            # Determine action
            action = "unknown"
            if resource_state == "exists":
                action = "updated"
            elif resource_state == "sync":
                action = "sync"
            elif resource_state == "not_exists":
                action = "deleted"

            # Fetch full event details if not deleted
            event = None
            if event_id and action != "deleted":
                try:
                    event = self.get_event(event_id)
                except Exception as e:
                    logger.warning(f"Could not fetch event details for {event_id}: {e}")

            result = {
                "event_id": event_id,
                "action": action,
                "event": event,
                "raw": payload,
            }

            logger.info(
                f"Processed Google Calendar webhook: {action} for event {event_id} "
                f"(resource: {resource_id})"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing Google Calendar webhook: {e}")
            raise CalendarServiceError(
                f"Failed to process webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e), "payload": payload},
            )

    def create_webhook_subscription(
        self, webhook_url: str
    ) -> Tuple[str, Optional[datetime]]:
        """
        Create a webhook subscription for Google Calendar notifications.

        Google uses "channel watches" to push notifications when events change.

        Args:
            webhook_url: URL to receive webhook notifications

        Returns:
            Tuple of (subscription_id, expiration_time)

        Example:
            >>> sub_id, expires = service.create_webhook_subscription(
            ...     "https://example.com/api/calendar/webhook"
            ... )
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            # Generate unique channel ID
            import uuid

            channel_id = f"agenthr-{self.calendar_email}-{uuid.uuid4()}"

            # Watch for changes
            body = {
                "id": channel_id,
                "type": "web_hook",
                "address": webhook_url,
            }

            # Watch the calendar
            watch_response = (
                service.events()
                .watch(
                    calendarId=self.calendar_id,
                    body=body,
                )
                .execute()
            )

            resource_id = watch_response.get("resourceId")
            expiration = watch_response.get("expiration")

            # Convert expiration timestamp to datetime
            expiration_time = None
            if expiration:
                expiration_time = datetime.utcfromtimestamp(int(expiration) / 1000)

            logger.info(
                f"Created Google Calendar webhook subscription: "
                f"{resource_id} (expires: {expiration_time})"
            )

            return resource_id, expiration_time

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to create webhook subscription: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error creating Google Calendar webhook: {e}")
            raise CalendarServiceError(
                f"Unexpected error creating webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """
        Delete a Google Calendar webhook subscription.

        Args:
            subscription_id: Resource ID from create_webhook_subscription

        Returns:
            True if deletion was successful

        Example:
            >>> success = service.delete_webhook_subscription("resource_id_123")
        """
        self._ensure_valid_token()

        try:
            service = self._get_google_service()

            # Stop watching the calendar
            service.channels().stop(body={"id": subscription_id, "resourceId": subscription_id}).execute()

            logger.info(f"Deleted Google Calendar webhook subscription: {subscription_id}")

            return True

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(
                    "Authentication failed", provider=self.provider_name, details={"error": str(e)}
                )

            if e.resp.status == 404:
                # Subscription already deleted
                logger.warning(f"Webhook subscription not found: {subscription_id}")
                return True

            if e.resp.status == 429:
                raise RateLimitError(
                    "Google Calendar API rate limit exceeded",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to delete webhook subscription: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error deleting Google Calendar webhook: {e}")
            raise CalendarServiceError(
                f"Unexpected error deleting webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )
