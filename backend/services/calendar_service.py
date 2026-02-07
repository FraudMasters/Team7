"""
Base calendar service interface for external calendar integration.

This module provides an abstract base class for integrating with external calendar
providers (Google Calendar and Microsoft Outlook/Graph). It defines the common interface
that all calendar service implementations must follow, enabling seamless switching
between different calendar providers.

The calendar service supports:
- Creating and updating calendar events
- Checking availability for scheduling
- Listing and retrieving events
- Deleting events and handling cancellations
- Webhook notifications for real-time sync
- OAuth token management and refresh

Event data flow:
1. Interview scheduled in system → create_event() → Calendar API
2. Calendar webhook received → handle_webhook() → Update interview
3. Availability check → get_availability() → Return free slots
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CalendarEvent(BaseModel):
    """
    Standardized calendar event representation.

    This model provides a provider-agnostic representation of calendar events,
    allowing the rest of the application to work with events regardless of
    the underlying calendar provider.

    Attributes:
        event_id: Unique identifier from the calendar provider
        title: Event title/summary
        description: Detailed event description
        start_time: Event start time (UTC)
        end_time: Event end time (UTC)
        location: Optional physical location
        meeting_link: Optional virtual meeting link
        attendees: List of attendee email addresses
        organizer_email: Email of the event organizer
        status: Event status (confirmed, tentative, cancelled)
        provider: Calendar provider (google/outlook)
    """

    event_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: List[str] = []
    organizer_email: str
    status: str = "confirmed"
    provider: str = "unknown"


class AvailabilitySlot(BaseModel):
    """
    Time slot representing availability for scheduling.

    Attributes:
        start_time: Slot start time (UTC)
        end_time: Slot end time (UTC)
        available: Whether the slot is free (True) or busy (False)
        confidence: Confidence score for availability (0-1)
    """

    start_time: datetime
    end_time: datetime
    available: bool
    confidence: float = 1.0


class CalendarServiceError(Exception):
    """Base exception for calendar service errors."""

    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize calendar service error.

        Args:
            message: Error message
            provider: Calendar provider name
            details: Additional error details
        """
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(f"[{provider}] {message}")


class AuthenticationError(CalendarServiceError):
    """Raised when calendar authentication fails."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when OAuth token has expired and refresh failed."""

    pass


class RateLimitError(CalendarServiceError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            provider: Calendar provider name
            retry_after: Seconds to wait before retry (if provided by API)
            details: Additional error details
        """
        super().__init__(message, provider, details)
        self.retry_after = retry_after


class EventConflictError(CalendarServiceError):
    """Raised when attempting to create an event that conflicts with existing events."""

    def __init__(
        self,
        message: str,
        provider: str,
        conflicting_events: List[CalendarEvent],
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize event conflict error.

        Args:
            message: Error message
            provider: Calendar provider name
            conflicting_events: List of events that conflict
            details: Additional error details
        """
        super().__init__(message, provider, details)
        self.conflicting_events = conflicting_events


class CalendarService(ABC):
    """
    Abstract base class for calendar service implementations.

    This class defines the interface that all calendar service implementations
    (GoogleCalendarService, OutlookCalendarService) must follow. It provides
    a unified API for calendar operations regardless of the underlying provider.

    Implementations must handle:
    - OAuth token management and refresh
    - API rate limiting and retries
    - Error handling and logging
    - Event serialization/deserialization
    - Webhook processing

    Attributes:
        provider_name: Human-readable provider name
        access_token: Current OAuth access token
        refresh_token: OAuth refresh token for token renewal
        token_expires_at: When the access token expires
        calendar_id: Provider-specific calendar identifier
        calendar_email: Email address of connected calendar

    Example:
        >>> service = GoogleCalendarService(access_token="...")
        >>> event = service.create_event(
        ...     title="Interview with John Doe",
        ...     start_time=datetime(2024, 1, 15, 10, 0),
        ...     end_time=datetime(2024, 1, 15, 11, 0),
        ...     attendees=["john@example.com", "interviewer@example.com"]
        ... )
        >>> print(event.event_id)
    """

    # Provider constants
    PROVIDER_GOOGLE = "google"
    PROVIDER_OUTLOOK = "outlook"

    # Event status constants
    STATUS_CONFIRMED = "confirmed"
    STATUS_TENTATIVE = "tentative"
    STATUS_CANCELLED = "cancelled"

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        calendar_email: str,
        calendar_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the calendar service.

        Args:
            access_token: OAuth access token for API calls
            refresh_token: OAuth refresh token for obtaining new access tokens
            token_expires_at: When the access token expires
            calendar_email: Email address of the connected calendar
            calendar_id: Optional provider-specific calendar identifier
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.calendar_email = calendar_email
        self.calendar_id = calendar_id or self._get_default_calendar_id()

        logger.info(
            f"{self.__class__.__name__} initialized for {self.calendar_email} "
            f"(token expires: {self.token_expires_at})"
        )

    @abstractmethod
    def _get_default_calendar_id(self) -> str:
        """
        Get the default calendar ID for the provider.

        Returns:
            Default calendar identifier

        Example:
            Google: 'primary'
            Outlook: Calendar ID from API
        """
        pass

    @abstractmethod
    def _refresh_access_token(self) -> str:
        """
        Refresh the OAuth access token using the refresh token.

        Returns:
            New access token

        Raises:
            TokenExpiredError: If token refresh fails
        """
        pass

    def _ensure_valid_token(self) -> None:
        """
        Ensure the current access token is valid, refresh if needed.

        Checks if the access token is expired or about to expire and
        refreshes it if necessary. Called automatically before API requests.
        """
        # Add 5-minute buffer to refresh before actual expiration
        refresh_threshold = datetime.utcnow() + timedelta(minutes=5)

        if self.token_expires_at <= refresh_threshold:
            logger.info(f"Access token expiring soon, refreshing for {self.calendar_email}")
            try:
                new_token = self._refresh_access_token()
                self.access_token = new_token
                logger.info("Access token refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh access token: {e}")
                raise TokenExpiredError(
                    f"Failed to refresh access token: {e}",
                    provider=self.provider_name,
                )

    @abstractmethod
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
        Create a new calendar event.

        Args:
            title: Event title
            start_time: Event start time (UTC)
            end_time: Event end time (UTC)
            description: Optional event description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            meeting_link: Optional virtual meeting link

        Returns:
            Created CalendarEvent with provider-assigned event_id

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
        pass

    @abstractmethod
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
        Update an existing calendar event.

        Args:
            event_id: Provider-specific event identifier
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
            ...     event_id="abc123",
            ...     start_time=datetime(2024, 1, 15, 15, 0),
            ...     end_time=datetime(2024, 1, 15, 16, 0)
            ... )
        """
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Provider-specific event identifier

        Returns:
            True if deletion was successful

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded
            CalendarServiceError: If event not found or deletion fails

        Example:
            >>> success = service.delete_event("abc123")
        """
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Retrieve a specific calendar event.

        Args:
            event_id: Provider-specific event identifier

        Returns:
            CalendarEvent if found, None otherwise

        Raises:
            AuthenticationError: If authentication fails
            CalendarServiceError: If retrieval fails

        Example:
            >>> event = service.get_event("abc123")
            >>> if event:
            ...     print(f"Event: {event.title}")
        """
        pass

    @abstractmethod
    def list_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """
        List events in the calendar within a time range.

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
        pass

    @abstractmethod
    def get_availability(
        self,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
    ) -> List[AvailabilitySlot]:
        """
        Check availability for scheduling within a time range.

        Returns time slots that are free for scheduling events of a
        specified duration.

        Args:
            start_time: Start of search window (UTC)
            end_time: End of search window (UTC)
            duration_minutes: Required duration for booking

        Returns:
            List of AvailabilitySlots indicating free/busy times

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If API rate limit is exceeded

        Example:
            >>> slots = service.get_availability(
            ...     start_time=datetime(2024, 1, 15, 9, 0),
            ...     end_time=datetime(2024, 1, 15, 17, 0),
            ...     duration_minutes=60
            ... )
            >>> free_slots = [s for s in slots if s.available]
        """
        pass

    @abstractmethod
    def check_conflict(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[str] = None,
    ) -> Tuple[bool, List[CalendarEvent]]:
        """
        Check if a time slot conflicts with existing events.

        Args:
            start_time: Proposed start time (UTC)
            end_time: Proposed end time (UTC)
            exclude_event_id: Optional event ID to exclude from conflict check
                (useful when updating an existing event)

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
        pass

    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook notification from the calendar provider.

        Handles real-time notifications about event changes, cancellations,
        and updates. Returns a standardized response with action to take.

        Args:
            payload: Webhook payload from provider

        Returns:
            Dictionary with:
                - event_id: ID of the affected event
                - action: Action to take (created, updated, deleted)
                - event: Full CalendarEvent if available
                - raw: Raw payload for debugging

        Raises:
            CalendarServiceError: If webhook processing fails

        Example:
            >>> result = service.handle_webhook(webhook_data)
            >>> if result['action'] == 'deleted':
            ...     # Cancel interview in system
            ...     cancel_interview(result['event_id'])
        """
        pass

    @abstractmethod
    def create_webhook_subscription(
        self, webhook_url: str
    ) -> Tuple[str, Optional[datetime]]:
        """
        Create a webhook subscription for real-time event notifications.

        Args:
            webhook_url: URL to receive webhook notifications

        Returns:
            Tuple of (subscription_id, expiration_time)

        Raises:
            AuthenticationError: If authentication fails
            CalendarServiceError: If subscription creation fails

        Example:
            >>> sub_id, expires = service.create_webhook_subscription(
            ...     "https://example.com/api/calendar/webhook"
            ... )
        """
        pass

    @abstractmethod
    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """
        Delete a webhook subscription.

        Args:
            subscription_id: Subscription identifier from create_webhook_subscription

        Returns:
            True if deletion was successful

        Example:
            >>> success = service.delete_webhook_subscription("sub_abc123")
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the calendar service connection.

        Verifies that the access token is valid and the calendar is accessible.

        Returns:
            Dictionary with health status:
                - status: 'healthy', 'unhealthy', or 'degraded'
                - provider: Provider name
                - calendar_email: Connected calendar email
                - token_valid: Whether access token is valid
                - error: Optional error message

        Example:
            >>> health = service.health_check()
            >>> if health['status'] == 'healthy':
            ...     print("Calendar service is ready")
        """
        result = {
            "status": "unhealthy",
            "provider": self.provider_name,
            "calendar_email": self.calendar_email,
            "token_valid": False,
            "error": None,
        }

        try:
            # Check token expiration
            if datetime.utcnow() >= self.token_expires_at:
                result["error"] = "Access token expired"
                return result

            # Try to fetch a single event to verify API access
            events = self.list_events(
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=1),
                limit=1,
            )

            result["token_valid"] = True
            result["status"] = "healthy"
            logger.debug(f"Health check passed for {self.provider_name}")

        except AuthenticationError as e:
            result["error"] = f"Authentication failed: {e.message}"
        except RateLimitError as e:
            result["status"] = "degraded"
            result["error"] = f"Rate limited: {e.message}"
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Health check failed for {self.provider_name}: {e}")

        return result

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the human-readable provider name.

        Returns:
            Provider name (e.g., 'Google Calendar', 'Microsoft Outlook')
        """
        pass


def get_calendar_service(
    provider: str,
    access_token: str,
    refresh_token: str,
    token_expires_at: datetime,
    calendar_email: str,
    calendar_id: Optional[str] = None,
) -> CalendarService:
    """
    Factory function to get the appropriate calendar service implementation.

    Args:
        provider: Calendar provider ('google' or 'outlook')
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        token_expires_at: Token expiration time
        calendar_email: Connected calendar email
        calendar_id: Optional provider-specific calendar ID

    Returns:
        Instantiated calendar service

    Raises:
        ValueError: If provider is not supported

    Example:
        >>> service = get_calendar_service(
        ...     provider="google",
        ...     access_token="ya29...",
        ...     refresh_token="1//0g...",
        ...     token_expires_at=datetime(2024, 1, 16, 12, 0),
        ...     calendar_email="user@example.com"
        ... )
        >>> event = service.create_event(...)
    """
    if provider == CalendarService.PROVIDER_GOOGLE:
        from backend.services.google_calendar_service import GoogleCalendarService

        return GoogleCalendarService(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
            calendar_id=calendar_id,
        )

    elif provider == CalendarService.PROVIDER_OUTLOOK:
        from backend.services.outlook_calendar_service import OutlookCalendarService

        return OutlookCalendarService(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
            calendar_id=calendar_id,
        )

    else:
        raise ValueError(
            f"Unsupported calendar provider: {provider}. "
            f"Supported providers: {CalendarService.PROVIDER_GOOGLE}, {CalendarService.PROVIDER_OUTLOOK}"
        )
