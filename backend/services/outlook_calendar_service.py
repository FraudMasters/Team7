"""
Microsoft Graph (Outlook) service implementation for external calendar integration.

This module provides integration with Microsoft Graph API for Outlook calendars,
enabling the application to create, update, and manage calendar events directly
on users' Outlook calendars.

Key features:
- OAuth 2.0 authentication with automatic token refresh
- Full CRUD operations for calendar events
- Availability checking and conflict detection
- Webhook notifications for real-time sync
- Microsoft Teams meeting link generation

Microsoft Graph API Documentation:
https://docs.microsoft.com/graph/api/resources/event
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

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


class OutlookCalendarService(CalendarService):
    """
    Microsoft Graph API service implementation for Outlook calendars.

    This service integrates with Microsoft Graph API to manage events
    on user Outlook calendars. It handles authentication, event CRUD operations,
    availability checking, and webhook management.

    Authentication Flow:
    1. User authorizes via OAuth 2.0
    2. Access token and refresh token stored in database
    3. Access token used for API calls
    4. Token automatically refreshed when expired

    Event Management:
    - Events include title, description, times, attendees, location
    - Microsoft Teams links can be auto-generated
    - Attendees receive email invitations
    - Event updates sync to all participants

    Webhooks:
    - Microsoft Graph uses change notifications
    - Webhook payload contains event ID and change type
    - Full event details fetched separately

    Example:
        >>> service = OutlookCalendarService(
        ...     access_token="eyJ0eXAi...",
        ...     refresh_token="0.ARoA6Wg...",
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

    # Microsoft Graph API constants
    API_BASE_URL = "https://graph.microsoft.com/v1.0"
    DEFAULT_CALENDAR_ID = ""  # Empty string for default calendar

    # Microsoft Graph API scopes
    SCOPE_CALENDAR = "Calendars.ReadWrite"
    SCOPE_EVENTS = "Calendars.ReadWrite"

    # Event status mapping
    EVENT_STATUS_CONFIRMED = "accepted"
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
        Initialize Outlook Calendar service.

        Args:
            access_token: OAuth access token for API calls
            refresh_token: OAuth refresh token for token renewal
            token_expires_at: When the access token expires
            calendar_email: Email address of the connected calendar
            calendar_id: Optional Outlook calendar ID (defaults to primary calendar)
        """
        super().__init__(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
            calendar_id=calendar_id,
        )

    @property
    def provider_name(self) -> str:
        """Get the human-readable provider name."""
        return "Microsoft Outlook"

    def _get_default_calendar_id(self) -> str:
        """Get the default calendar ID for Outlook."""
        return self.DEFAULT_CALENDAR_ID

    def _get_calendar_endpoint(self) -> str:
        """
        Get the calendar endpoint URL.

        Returns:
            Calendar API endpoint URL
        """
        if self.calendar_id:
            return f"{self.API_BASE_URL}/me/calendars/{self.calendar_id}/events"
        return f"{self.API_BASE_URL}/me/events"

    def _get_event_endpoint(self, event_id: str) -> str:
        """
        Get the event endpoint URL.

        Args:
            event_id: Event ID

        Returns:
            Event API endpoint URL
        """
        if self.calendar_id:
            return f"{self.API_BASE_URL}/me/calendars/{self.calendar_id}/events/{event_id}"
        return f"{self.API_BASE_URL}/me/events/{event_id}"

    def _refresh_access_token(self) -> str:
        """
        Refresh the OAuth access token using the refresh token.

        Makes a request to Microsoft's OAuth 2.0 endpoint to exchange the
        refresh token for a new access token.

        Returns:
            New access token

        Raises:
            TokenExpiredError: If token refresh fails
        """
        try:
            token_url = f"https://login.microsoftonline.com/{settings.microsoft_graph_tenant_id}/oauth2/v2.0/token"

            data = {
                "client_id": settings.microsoft_graph_client_id,
                "client_secret": settings.microsoft_graph_client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }

            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            new_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info(f"Access token refreshed for {self.calendar_email}")

            return new_token

        except requests.RequestException as e:
            logger.error(f"Failed to refresh Outlook token: {e}")
            raise TokenExpiredError(
                f"Failed to refresh access token: {e}",
                provider=self.provider_name,
            )
        except Exception as e:
            logger.error(f"Failed to refresh Outlook token: {e}")
            raise TokenExpiredError(
                f"Failed to refresh access token: {e}",
                provider=self.provider_name,
            )

    def _parse_outlook_event(self, outlook_event: Dict[str, Any]) -> CalendarEvent:
        """
        Parse a Microsoft Graph event into our standardized CalendarEvent model.

        Args:
            outlook_event: Raw event data from Microsoft Graph API

        Returns:
            Standardized CalendarEvent object
        """
        # Parse start and end times
        start_data = outlook_event.get("start", {})
        end_data = outlook_event.get("end", {})

        # Parse ISO 8601 format with timezone
        start_time_str = start_data.get("dateTime")
        end_time_str = end_data.get("dateTime")

        # Parse and convert to UTC
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            if start_time.tzinfo is not None:
                start_time = start_time.utctimetuple()
                start_time = datetime(*start_time[:6])

        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            if end_time.tzinfo is not None:
                end_time = end_time.utctimetuple()
                end_time = datetime(*end_time[:6])

        # Extract attendees
        attendees = []
        for attendee in outlook_event.get("attendees", []):
            email_data = attendee.get("emailAddress", {})
            email = email_data.get("address")
            if email:
                attendees.append(email)

        # Extract meeting link (Microsoft Teams or online meeting)
        meeting_link = None
        online_meeting = outlook_event.get("onlineMeeting")
        if online_meeting:
            meeting_link = online_meeting.get("joinUrl")

        # Map status
        response_status = outlook_event.get("responseStatus", {})
        response = response_status.get("response", "accepted").lower()

        status = self.STATUS_CONFIRMED
        if response == "declined":
            status = self.STATUS_CANCELLED
        elif response == "tentativelyAccepted":
            status = self.STATUS_TENTATIVE

        # Check if event is cancelled
        if outlook_event.get("isCancelled", False):
            status = self.STATUS_CANCELLED

        return CalendarEvent(
            event_id=outlook_event["id"],
            title=outlook_event.get("subject", "No Title"),
            description=outlook_event.get("body", {}).get("content"),
            start_time=start_time,
            end_time=end_time,
            location=outlook_event.get("location", {}).get("displayName"),
            meeting_link=meeting_link,
            attendees=attendees,
            organizer_email=outlook_event.get("organizer", {})
            .get("emailAddress", {})
            .get("address", ""),
            status=status,
            provider=self.PROVIDER_OUTLOOK,
        )

    def _build_outlook_event(
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
        Build a Microsoft Graph event dictionary from parameters.

        Args:
            title: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Optional event description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            meeting_link: Optional virtual meeting link

        Returns:
            Microsoft Graph API event dictionary
        """
        event = {
            "subject": title,
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
        }

        # Add description
        if description:
            event["body"] = {
                "contentType": "HTML",
                "content": description,
            }

        # Add location
        if location:
            event["location"] = {
                "displayName": location,
            }

        # Add online meeting (Microsoft Teams)
        if meeting_link or not location:
            event["isOnlineMeeting"] = True
            event["onlineMeetingProvider"] = "teamsForBusiness"

        # Add attendees
        if attendees:
            event["attendees"] = [
                {
                    "emailAddress": {
                        "address": email,
                        "name": email.split("@")[0],
                    },
                    "type": "required",
                }
                for email in attendees
            ]

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
        Create a new Outlook calendar event.

        Creates an event on the user's Outlook calendar and sends email
        invitations to all attendees.

        Args:
            title: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Optional event description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            meeting_link: Optional virtual meeting link (if None, may auto-generate Teams link)

        Returns:
            Created CalendarEvent with Outlook-assigned event_id

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
            outlook_event = self._build_outlook_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees,
                meeting_link=meeting_link,
            )

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            logger.info(
                f"Creating Outlook event: {title} at {start_time} "
                f"for {len(attendees or [])} attendees"
            )

            response = requests.post(
                self._get_calendar_endpoint(),
                json=outlook_event,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            created_event = response.json()
            parsed_event = self._parse_outlook_event(created_event)

            logger.info(
                f"Outlook event created: {parsed_event.event_id} "
                f"(Teams: {parsed_event.meeting_link})"
            )

            return parsed_event

        except requests.HTTPError as e:
            # Handle rate limiting (429)
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                retry_after_int = int(retry_after) if retry_after else None

                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=retry_after_int,
                    details={"error": str(e)},
                )

            # Handle authentication errors (401)
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            # Handle conflict errors (409)
            if e.response.status_code == 409:
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
                details={"error": str(e), "status": e.response.status_code},
            )

        except Exception as e:
            logger.error(f"Unexpected error creating Outlook event: {e}")
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
        Update an existing Outlook calendar event.

        Args:
            event_id: Outlook event ID
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
            ...     event_id="ABC123XYZ",
            ...     start_time=datetime(2024, 1, 15, 15, 0),
            ...     end_time=datetime(2024, 1, 15, 16, 0)
            ... )
        """
        self._ensure_valid_token()

        try:
            # Build update with only provided fields
            update_data = {}

            if title is not None:
                update_data["subject"] = title

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
                update_data["body"] = {
                    "contentType": "HTML",
                    "content": description,
                }

            if location is not None:
                update_data["location"] = {
                    "displayName": location,
                }

            if attendees is not None:
                update_data["attendees"] = [
                    {
                        "emailAddress": {
                            "address": email,
                            "name": email.split("@")[0],
                        },
                        "type": "required",
                    }
                    for email in attendees
                ]

            if meeting_link is not None:
                update_data["isOnlineMeeting"] = True
                update_data["onlineMeetingProvider"] = "teamsForBusiness"

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            logger.info(f"Updating Outlook event: {event_id}")

            response = requests.patch(
                self._get_event_endpoint(event_id),
                json=update_data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            updated_event = response.json()
            parsed_event = self._parse_outlook_event(updated_event)

            logger.info(f"Outlook event updated: {event_id}")

            return parsed_event

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 404:
                raise CalendarServiceError(
                    f"Event not found: {event_id}",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to update event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error updating Outlook event: {e}")
            raise CalendarServiceError(
                f"Unexpected error updating event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def delete_event(self, event_id: str) -> bool:
        """
        Delete an Outlook calendar event.

        Args:
            event_id: Outlook event ID

        Returns:
            True if deletion was successful

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded
            CalendarServiceError: If event not found or deletion fails

        Example:
            >>> success = service.delete_event("ABC123XYZ")
        """
        self._ensure_valid_token()

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            logger.info(f"Deleting Outlook event: {event_id}")

            response = requests.delete(
                self._get_event_endpoint(event_id),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            logger.info(f"Outlook event deleted: {event_id}")

            return True

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 404:
                # Event already deleted or doesn't exist
                logger.warning(f"Event not found for deletion: {event_id}")
                return True

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to delete event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error deleting Outlook event: {e}")
            raise CalendarServiceError(
                f"Unexpected error deleting event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Retrieve a specific Outlook calendar event.

        Args:
            event_id: Outlook event ID

        Returns:
            CalendarEvent if found, None otherwise

        Raises:
            AuthenticationError: If authentication fails
            CalendarServiceError: If retrieval fails

        Example:
            >>> event = service.get_event("ABC123XYZ")
            >>> if event:
            ...     print(f"Event: {event.title}")
        """
        self._ensure_valid_token()

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            response = requests.get(
                self._get_event_endpoint(event_id),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            outlook_event = response.json()
            return self._parse_outlook_event(outlook_event)

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 404:
                logger.warning(f"Event not found: {event_id}")
                return None

            raise CalendarServiceError(
                f"Failed to get event: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error getting Outlook event: {e}")
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
        List Outlook calendar events within a time range.

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
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            # Build OData filter for date range
            filter_str = (
                f"start/dateTime ge '{start_time.strftime('%Y-%m-%dT%H:%M:%S')}' "
                f"and end/dateTime le '{end_time.strftime('%Y-%m-%dT%H:%M:%S')}'"
            )

            params = {
                "$filter": filter_str,
                "$top": limit,
                "$orderby": "start/dateTime",
            }

            response = requests.get(
                self._get_calendar_endpoint(),
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            outlook_events = data.get("value", [])

            parsed_events = [self._parse_outlook_event(e) for e in outlook_events]

            logger.info(
                f"Listed {len(parsed_events)} Outlook events between "
                f"{start_time} and {end_time}"
            )

            return parsed_events

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to list events: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error listing Outlook events: {e}")
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

        Queries Microsoft Graph's getSchedule API to find time slots that
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
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # Use getSchedule API
            body = {
                "schedules": [self.calendar_email],
                "startTime": {
                    "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC",
                },
                "endTime": {
                    "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC",
                },
                "availabilityViewInterval": duration_minutes,
            }

            response = requests.post(
                f"{self.API_BASE_URL}/me/calendar/getSchedule",
                json=body,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            schedule_info = data.get("value", [{}])[0]
            availability_view = schedule_info.get("availabilityView", "")

            # Build availability slots from availability view
            # availability_view is a string like "02200" where:
            # 0 = free, 1 = tentative, 2 = busy, 3 = out of office, 4 = working elsewhere
            slots = []
            current_time = start_time
            duration_delta = timedelta(minutes=duration_minutes)

            for i, char in enumerate(availability_view):
                slot_start = current_time + (i * duration_delta)
                slot_end = slot_start + duration_delta

                if slot_end > end_time:
                    break

                # 0 = free, 1 = tentative (considered busy for interviews)
                available = char == "0"

                slots.append(
                    AvailabilitySlot(
                        start_time=slot_start,
                        end_time=slot_end,
                        available=available,
                        confidence=1.0,
                    )
                )

            logger.info(
                f"Generated {len(slots)} availability slots, "
                f"{sum(1 for s in slots if s.available)} free"
            )

            return slots

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to get availability: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error getting Outlook availability: {e}")
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
        Check if a time slot conflicts with existing Outlook calendar events.

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
            logger.error(f"Error checking Outlook calendar conflicts: {e}")
            # On error, assume conflict to be safe
            return True, []

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook notification from Microsoft Graph.

        Microsoft Graph webhooks (change notifications) include:
        - Subscription ID and expiration
        - Event ID and change type
        - Full event details fetched separately

        Args:
            payload: Webhook payload from Microsoft Graph

        Returns:
            Dictionary with action, event_id, event, and raw payload

        Example:
            >>> result = service.handle_webhook(webhook_data)
            >>> if result['action'] == 'deleted':
            ...     cancel_interview(result['event_id'])
        """
        try:
            # Extract notification data
            validation_token = payload.get("validationToken")
            if validation_token:
                # This is a validation request from Microsoft Graph
                # Return the token to confirm subscription
                return {
                    "validation_token": validation_token,
                    "action": "validate",
                    "event_id": None,
                    "event": None,
                    "raw": payload,
                }

            # Process actual notification
            value = payload.get("value", [])
            if not value:
                raise CalendarServiceError(
                    "Invalid webhook payload: missing notifications",
                    provider=self.provider_name,
                    details={"payload": payload},
                )

            # Process first notification (typically one per payload)
            notification = value[0]

            subscription_id = notification.get("subscriptionId")
            client_state = notification.get("clientState")

            # Extract event ID from resource
            resource = notification.get("resource", "")
            event_id = None
            if "/events/" in resource:
                parts = resource.split("/events/")
                if len(parts) > 1:
                    event_id = parts[1].split("?")[0]

            # Determine action
            action = "unknown"
            change_type = notification.get("changeType", "").lower()

            if change_type == "created":
                action = "created"
            elif change_type == "updated":
                action = "updated"
            elif change_type == "deleted":
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
                "subscription_id": subscription_id,
                "client_state": client_state,
                "raw": payload,
            }

            logger.info(
                f"Processed Outlook webhook: {action} for event {event_id} "
                f"(subscription: {subscription_id})"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing Outlook webhook: {e}")
            raise CalendarServiceError(
                f"Failed to process webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e), "payload": payload},
            )

    def create_webhook_subscription(
        self, webhook_url: str
    ) -> Tuple[str, Optional[datetime]]:
        """
        Create a webhook subscription for Microsoft Graph notifications.

        Microsoft Graph uses change notifications to push updates when
        calendar events change.

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
            import uuid

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # Create subscription
            subscription = {
                "changeType": "created,updated,deleted",
                "notificationUrl": webhook_url,
                "resource": f"me/calendars/{self.calendar_id}/events" if self.calendar_id else "me/events",
                "expirationDateTime": (datetime.utcnow() + timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "clientState": f"agenthr-{uuid.uuid4()}",
            }

            logger.info(f"Creating Outlook webhook subscription for {webhook_url}")

            response = requests.post(
                f"{self.API_BASE_URL}/subscriptions",
                json=subscription,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            subscription_id = data.get("id")
            expiration_str = data.get("expirationDateTime")

            # Convert expiration to datetime
            expiration_time = None
            if expiration_str:
                expiration_time = datetime.fromisoformat(expiration_str.replace("Z", "+00:00"))

            logger.info(
                f"Created Outlook webhook subscription: {subscription_id} "
                f"(expires: {expiration_time})"
            )

            return subscription_id, expiration_time

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to create webhook subscription: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error creating Outlook webhook: {e}")
            raise CalendarServiceError(
                f"Unexpected error creating webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """
        Delete a Microsoft Graph webhook subscription.

        Args:
            subscription_id: Subscription ID from create_webhook_subscription

        Returns:
            True if deletion was successful

        Example:
            >>> success = service.delete_webhook_subscription("subscription_id_123")
        """
        self._ensure_valid_token()

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            logger.info(f"Deleting Outlook webhook subscription: {subscription_id}")

            response = requests.delete(
                f"{self.API_BASE_URL}/subscriptions/{subscription_id}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            logger.info(f"Deleted Outlook webhook subscription: {subscription_id}")

            return True

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    provider=self.provider_name,
                    details={"error": str(e)},
                )

            if e.response.status_code == 404:
                # Subscription already deleted
                logger.warning(f"Webhook subscription not found: {subscription_id}")
                return True

            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Microsoft Graph API rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                    details={"error": str(e)},
                )

            raise CalendarServiceError(
                f"Failed to delete webhook subscription: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error deleting Outlook webhook: {e}")
            raise CalendarServiceError(
                f"Unexpected error deleting webhook: {e}",
                provider=self.provider_name,
                details={"error": str(e)},
            )
