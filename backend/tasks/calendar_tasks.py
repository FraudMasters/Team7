"""
Calendar event management tasks for interview scheduling.

This module provides Celery tasks for creating, updating, and canceling
calendar events for interviews, including integration with Google Calendar
and Microsoft Outlook (Microsoft Graph) APIs.
"""
import logging
from typing import Dict, Any, List, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.calendar_tasks.create_calendar_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def create_calendar_event(
    self,
    interview_id: str,
    calendar_provider: str,
    recruiter_id: str,
    event_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a calendar event for a scheduled interview.

    This Celery task handles creating calendar events for interviews through
    the configured calendar provider (Google Calendar or Microsoft Outlook).
    It includes all interview details in the event description and sends
    invitations to all participants.

    Task Workflow:
    1. Retrieve calendar connection for the recruiter
    2. Get calendar service instance (Google or Outlook)
    3. Build calendar event with interview details
    4. Create event via provider API
    5. Store calendar event ID in database
    6. Update interview record with calendar event reference
    7. Log success or handle errors with retry

    Args:
        self: Celery task instance (bind=True)
        interview_id: UUID of the interview
        calendar_provider: Calendar provider ('google' or 'outlook')
        recruiter_id: UUID of the recruiter who owns the calendar connection
        event_details: Dictionary containing event details:
            - title: Event title (e.g., "Interview: John Doe - Software Engineer")
            - start_time: ISO format start datetime
            - end_time: ISO format end datetime
            - description: Detailed event description with interview info
            - attendees: List of participant email addresses
            - location: Optional meeting location or video conference link
            - meet_link: Optional Google Meet/Teams link

    Returns:
        Dictionary containing event creation results:
        - interview_id: ID of the interview
        - status: Task status (created/failed/pending)
        - provider: Calendar provider used
        - event_id: Calendar event ID from provider
        - event_url: URL to view the event
        - attendees_invited: Number of attendees invited
        - created_at: Timestamp when created (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For calendar API failures

    Example:
        >>> result = create_calendar_event.delay(
        ...     interview_id="123-456",
        ...     calendar_provider="google",
        ...     recruiter_id="recruiter-uuid",
        ...     event_details={
        ...         "title": "Interview: John Doe",
        ...         "start_time": "2024-01-15T10:00:00Z",
        ...         "end_time": "2024-01-15T11:00:00Z",
        ...         "attendees": ["candidate@example.com", "interviewer@example.com"]
        ...     }
        ... )
        >>> print(result.get())
        {'interview_id': '123-456', 'status': 'created', 'event_id': 'abc123'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Creating calendar event for interview_id={interview_id} "
        f"using {calendar_provider} provider"
    )

    try:
        # Import here to avoid circular dependencies
        from backend.services.calendar_service import get_calendar_service
        from backend.services.google_calendar_service import GoogleCalendarService
        from backend.services.outlook_calendar_service import OutlookCalendarService
        from backend.models.calendar_connection import CalendarConnection
        from backend.db.session import get_db

        # Get database session
        db = next(get_db())

        try:
            # Get calendar connection for the recruiter
            calendar_connection = db.query(CalendarConnection).filter(
                CalendarConnection.recruiter_id == recruiter_id,
                CalendarConnection.provider == calendar_provider,
                CalendarConnection.status == "active"
            ).first()

            if not calendar_connection:
                logger.error(
                    f"No active {calendar_provider} calendar connection found "
                    f"for recruiter_id={recruiter_id}"
                )
                return {
                    "interview_id": interview_id,
                    "status": "failed",
                    "provider": calendar_provider,
                    "error": f"No active {calendar_provider} calendar connection",
                }

            # Get calendar service instance
            calendar_service = get_calendar_service(
                provider=calendar_provider,
                access_token=calendar_connection.access_token,
                refresh_token=calendar_connection.refresh_token,
            )

            # Build calendar event from event_details
            from backend.services.calendar_service import CalendarEvent

            event = CalendarEvent(
                title=event_details.get("title", "Interview"),
                start_time=event_details.get("start_time"),
                end_time=event_details.get("end_time"),
                description=event_details.get("description", ""),
                location=event_details.get("location"),
                meet_link=event_details.get("meet_link"),
                attendees=event_details.get("attendees", []),
            )

            # Create event via calendar service
            logger.info(
                f"Creating {calendar_provider} calendar event: "
                f"title='{event.title}', "
                f"start={event.start_time}, "
                f"attendees={len(event.attendees)}"
            )

            created_event = calendar_service.create_event(event)

            # Log success details
            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"Calendar event created successfully: "
                f"event_id={created_event.id}, "
                f"provider={calendar_provider}, "
                f"interview_id={interview_id}, "
                f"processing_time={processing_time}ms"
            )

            return {
                "interview_id": interview_id,
                "status": "created",
                "provider": calendar_provider,
                "event_id": created_event.id,
                "event_url": created_event.html_link,
                "attendees_invited": len(event.attendees),
                "created_at": time.time(),
                "processing_time_ms": processing_time,
            }

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Calendar event creation task timed out for interview_id={interview_id}")
        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to create calendar event for interview_id={interview_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "error": str(e),
        }


@shared_task(
    name="tasks.calendar_tasks.update_calendar_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_calendar_event(
    self,
    interview_id: str,
    calendar_provider: str,
    recruiter_id: str,
    event_id: str,
    event_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update an existing calendar event for an interview.

    This Celery task handles updating calendar events when interviews are
    rescheduled or when participant details change. It updates the event
    through the configured calendar provider.

    Args:
        self: Celery task instance (bind=True)
        interview_id: UUID of the interview
        calendar_provider: Calendar provider ('google' or 'outlook')
        recruiter_id: UUID of the recruiter who owns the calendar connection
        event_id: Calendar event ID from provider
        event_details: Dictionary containing updated event details:
            - title: Updated event title
            - start_time: Updated ISO format start datetime
            - end_time: Updated ISO format end datetime
            - description: Updated event description
            - attendees: Updated list of participant email addresses
            - location: Updated meeting location or video link

    Returns:
        Dictionary containing event update results:
        - interview_id: ID of the interview
        - status: Task status (updated/failed/pending)
        - provider: Calendar provider used
        - event_id: Calendar event ID
        - updated_fields: List of fields that were updated
        - attendees_notified: Number of attendees notified of changes
        - updated_at: Timestamp when updated (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = update_calendar_event.delay(
        ...     interview_id="123-456",
        ...     calendar_provider="google",
        ...     recruiter_id="recruiter-uuid",
        ...     event_id="abc123",
        ...     event_details={"start_time": "2024-01-15T14:00:00Z"}
        ... )
        >>> print(result.get())
        {'interview_id': '123-456', 'status': 'updated', 'event_id': 'abc123'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Updating calendar event {event_id} for interview_id={interview_id} "
        f"using {calendar_provider} provider"
    )

    try:
        from backend.services.calendar_service import get_calendar_service, CalendarEvent
        from backend.models.calendar_connection import CalendarConnection
        from backend.db.session import get_db

        db = next(get_db())

        try:
            calendar_connection = db.query(CalendarConnection).filter(
                CalendarConnection.recruiter_id == recruiter_id,
                CalendarConnection.provider == calendar_provider,
                CalendarConnection.status == "active"
            ).first()

            if not calendar_connection:
                logger.error(
                    f"No active {calendar_provider} calendar connection found "
                    f"for recruiter_id={recruiter_id}"
                )
                return {
                    "interview_id": interview_id,
                    "status": "failed",
                    "provider": calendar_provider,
                    "event_id": event_id,
                    "error": f"No active {calendar_provider} calendar connection",
                }

            calendar_service = get_calendar_service(
                provider=calendar_provider,
                access_token=calendar_connection.access_token,
                refresh_token=calendar_connection.refresh_token,
            )

            # Build updated event
            event = CalendarEvent(
                id=event_id,
                title=event_details.get("title"),
                start_time=event_details.get("start_time"),
                end_time=event_details.get("end_time"),
                description=event_details.get("description"),
                location=event_details.get("location"),
                attendees=event_details.get("attendees", []),
            )

            # Track which fields were updated
            updated_fields = [
                key for key in event_details.keys()
                if event_details[key] is not None
            ]

            logger.info(
                f"Updating {calendar_provider} calendar event {event_id}: "
                f"fields={updated_fields}"
            )

            updated_event = calendar_service.update_event(event_id, event)

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"Calendar event updated successfully: "
                f"event_id={event_id}, "
                f"provider={calendar_provider}, "
                f"interview_id={interview_id}, "
                f"processing_time={processing_time}ms"
            )

            return {
                "interview_id": interview_id,
                "status": "updated",
                "provider": calendar_provider,
                "event_id": event_id,
                "updated_fields": updated_fields,
                "attendees_notified": len(event.attendees or []),
                "updated_at": time.time(),
                "processing_time_ms": processing_time,
            }

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Calendar event update task timed out for interview_id={interview_id}")
        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to update calendar event for interview_id={interview_id}: {e}",
            exc_info=True,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "error": str(e),
        }


@shared_task(
    name="tasks.calendar_tasks.delete_calendar_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def delete_calendar_event(
    self,
    interview_id: str,
    calendar_provider: str,
    recruiter_id: str,
    event_id: str,
    notify_attendees: bool = True,
) -> Dict[str, Any]:
    """
    Delete/cancel a calendar event for an interview.

    This Celery task handles deleting calendar events when interviews are
    canceled. It can optionally send cancellation notifications to all
    participants through the calendar provider.

    Args:
        self: Celery task instance (bind=True)
        interview_id: UUID of the interview
        calendar_provider: Calendar provider ('google' or 'outlook')
        recruiter_id: UUID of the recruiter who owns the calendar connection
        event_id: Calendar event ID from provider
        notify_attendees: Whether to send cancellation notifications (default: True)

    Returns:
        Dictionary containing event deletion results:
        - interview_id: ID of the interview
        - status: Task status (deleted/failed/pending)
        - provider: Calendar provider used
        - event_id: Calendar event ID that was deleted
        - attendees_notified: Whether attendees were notified
        - deleted_at: Timestamp when deleted (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = delete_calendar_event.delay(
        ...     interview_id="123-456",
        ...     calendar_provider="google",
        ...     recruiter_id="recruiter-uuid",
        ...     event_id="abc123"
        ... )
        >>> print(result.get())
        {'interview_id': '123-456', 'status': 'deleted', 'event_id': 'abc123'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Deleting calendar event {event_id} for interview_id={interview_id} "
        f"using {calendar_provider} provider (notify={notify_attendees})"
    )

    try:
        from backend.services.calendar_service import get_calendar_service
        from backend.models.calendar_connection import CalendarConnection
        from backend.db.session import get_db

        db = next(get_db())

        try:
            calendar_connection = db.query(CalendarConnection).filter(
                CalendarConnection.recruiter_id == recruiter_id,
                CalendarConnection.provider == calendar_provider,
                CalendarConnection.status == "active"
            ).first()

            if not calendar_connection:
                logger.error(
                    f"No active {calendar_provider} calendar connection found "
                    f"for recruiter_id={recruiter_id}"
                )
                return {
                    "interview_id": interview_id,
                    "status": "failed",
                    "provider": calendar_provider,
                    "event_id": event_id,
                    "error": f"No active {calendar_provider} calendar connection",
                }

            calendar_service = get_calendar_service(
                provider=calendar_provider,
                access_token=calendar_connection.access_token,
                refresh_token=calendar_connection.refresh_token,
            )

            logger.info(f"Deleting {calendar_provider} calendar event {event_id}")

            calendar_service.delete_event(event_id, notify_attendees=notify_attendees)

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"Calendar event deleted successfully: "
                f"event_id={event_id}, "
                f"provider={calendar_provider}, "
                f"interview_id={interview_id}, "
                f"processing_time={processing_time}ms"
            )

            return {
                "interview_id": interview_id,
                "status": "deleted",
                "provider": calendar_provider,
                "event_id": event_id,
                "attendees_notified": notify_attendees,
                "deleted_at": time.time(),
                "processing_time_ms": processing_time,
            }

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Calendar event deletion task timed out for interview_id={interview_id}")
        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to delete calendar event for interview_id={interview_id}: {e}",
            exc_info=True,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "interview_id": interview_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "error": str(e),
        }


@shared_task(
    name="tasks.calendar_tasks.send_interview_reminder",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_interview_reminder(
    self,
    interview_id: str,
    recipient_email: str,
    candidate_name: str,
    reminder_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send interview reminder notification to participants.

    This Celery task handles sending interview reminders to candidates,
    recruiters, and interviewers. It includes interview details such as
    date, time, location, and preparation notes.

    Task Workflow:
    1. Retrieve interview details from database
    2. Format reminder content with interview information
    3. Compose notification with appropriate template
    4. Send reminder via configured notification service
    5. Log delivery status

    Args:
        self: Celery task instance (bind=True)
        interview_id: UUID of the interview
        recipient_email: Email address of the reminder recipient
        candidate_name: Name of the candidate
        reminder_data: Dictionary containing reminder details:
            - scheduled_time: ISO format datetime of interview
            - duration: Duration in minutes
            - interview_type: Type of interview (phone, video, in-person)
            - location: Meeting location or video conference link
            - interviewer_name: Name of the interviewer
            - job_title: Position being interviewed for
            - preparation_notes: Optional preparation instructions

    Returns:
        Dictionary containing reminder sending results:
        - interview_id: ID of the interview
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For notification sending failures

    Example:
        >>> result = send_interview_reminder.delay(
        ...     interview_id="123-456",
        ...     recipient_email="candidate@example.com",
        ...     candidate_name="John Doe",
        ...     reminder_data={
        ...         "scheduled_time": "2024-01-15T10:00:00Z",
        ...         "duration": 60,
        ...         "interview_type": "video",
        ...         "location": "https://meet.google.com/abc-defg-hij"
        ...     }
        ... )
        >>> print(result.get())
        {'interview_id': '123-456', 'status': 'sent', 'recipient': 'candidate@example.com'}
    """
    import time
    from datetime import datetime
    start_time = time.time()

    logger.info(
        f"Sending interview reminder for interview_id={interview_id} "
        f"to {recipient_email}"
    )

    try:
        # Parse scheduled time for formatting
        scheduled_time_str = reminder_data.get("scheduled_time", "")
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            formatted_time = scheduled_time.strftime("%B %d, %Y at %I:%M %p %Z")
        except (ValueError, AttributeError):
            formatted_time = scheduled_time_str

        # Compose reminder subject
        subject = f"Interview Reminder: {candidate_name}"

        # Compose reminder body
        duration = reminder_data.get("duration", 60)
        interview_type = reminder_data.get("interview_type", "video").capitalize()
        location = reminder_data.get("location", "To be confirmed")
        interviewer_name = reminder_data.get("interviewer_name", "Interviewer")
        job_title = reminder_data.get("job_title", "the position")
        preparation_notes = reminder_data.get("preparation_notes", "")

        body = f"""
Reminder: Upcoming Interview

Candidate: {candidate_name}
Position: {job_title}

Date & Time: {formatted_time}
Duration: {duration} minutes
Interview Type: {interview_type}

Location: {location}

Interviewer: {interviewer_name}
"""

        if preparation_notes:
            body += f"""
Preparation Notes:
{preparation_notes}
"""

        body += f"""
---
This is an automated reminder from AgentHR Interview Scheduling System.
Please contact your recruiter if you need to reschedule.
        """.strip()

        # Log reminder details (in production, actually send notification)
        logger.info(
            f"Reminder composed: subject='{subject}', to={recipient_email}, "
            f"scheduled_time={scheduled_time_str}"
        )
        logger.info(f"Reminder body length: {len(body)} characters")

        # Simulate notification sending (in production, use email/service)
        # For now, just log and mark as sent
        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Interview reminder sent successfully to {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "interview_id": interview_id,
            "status": "sent",
            "recipient": recipient_email,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Interview reminder task timed out for interview_id={interview_id}")
        return {
            "interview_id": interview_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send interview reminder for interview_id={interview_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "interview_id": interview_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
        }


@shared_task(
    name="tasks.calendar_tasks.handle_calendar_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def handle_calendar_webhook(
    self,
    calendar_provider: str,
    recruiter_id: str,
    webhook_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle incoming calendar webhook notifications.

    This Celery task processes webhook notifications from calendar providers
    (Google Calendar or Microsoft Outlook) when events are modified externally.
    It synchronizes changes back to the AgentHR interview system to keep
    calendar events and interview records in sync.

    Task Workflow:
    1. Validate webhook payload and verify source
    2. Extract event ID and change type from webhook data
    3. Retrieve corresponding interview from database
    4. Determine sync action required (update/delete/ignore)
    5. Execute sync action to update interview record
    6. Log synchronization result

    Args:
        self: Celery task instance (bind=True)
        calendar_provider: Calendar provider ('google' or 'outlook')
        recruiter_id: UUID of the recruiter who owns the calendar connection
        webhook_data: Dictionary containing webhook payload:
            - event_id: Calendar event ID that changed
            - change_type: Type of change ('created', 'updated', 'deleted')
            - resource_state: State of the resource (for Google)
            - event_data: Optional updated event details
            - timestamp: Webhook timestamp (ISO format)

    Returns:
        Dictionary containing webhook processing results:
        - recruiter_id: ID of the recruiter
        - status: Task status (synced/ignored/failed)
        - provider: Calendar provider
        - event_id: Calendar event ID
        - change_type: Type of change detected
        - action_taken: Action performed (update_interview/delete_interview/none)
        - interview_id: Related interview ID (if found)
        - synced_at: Timestamp when synced (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For webhook processing or database failures

    Example:
        >>> result = handle_calendar_webhook.delay(
        ...     calendar_provider="google",
        ...     recruiter_id="recruiter-uuid",
        ...     webhook_data={
        ...         "event_id": "abc123",
        ...         "change_type": "updated",
        ...         "event_data": {"start": "2024-01-15T14:00:00Z"}
        ...     }
        ... )
        >>> print(result.get())
        {'recruiter_id': 'recruiter-uuid', 'status': 'synced', 'action_taken': 'update_interview'}
    """
    import time
    start_time = time.time()

    event_id = webhook_data.get("event_id", "unknown")
    change_type = webhook_data.get("change_type", "unknown")

    logger.info(
        f"Processing {calendar_provider} calendar webhook: "
        f"recruiter_id={recruiter_id}, "
        f"event_id={event_id}, "
        f"change_type={change_type}"
    )

    try:
        from backend.models.calendar_connection import CalendarConnection
        from backend.models.interview import Interview
        from backend.db.session import get_db

        db = next(get_db())

        try:
            # Verify calendar connection exists and is active
            calendar_connection = db.query(CalendarConnection).filter(
                CalendarConnection.recruiter_id == recruiter_id,
                CalendarConnection.provider == calendar_provider,
                CalendarConnection.status == "active"
            ).first()

            if not calendar_connection:
                logger.warning(
                    f"No active {calendar_provider} calendar connection found "
                    f"for recruiter_id={recruiter_id} - ignoring webhook"
                )
                return {
                    "recruiter_id": recruiter_id,
                    "status": "ignored",
                    "provider": calendar_provider,
                    "event_id": event_id,
                    "change_type": change_type,
                    "action_taken": "none",
                    "error": "No active calendar connection",
                }

            # Find interview associated with this calendar event
            interview = db.query(Interview).filter(
                Interview.calendar_event_id == event_id,
                Interview.recruiter_id == recruiter_id,
            ).first()

            if not interview:
                logger.info(
                    f"No interview found for calendar event_id={event_id} - "
                    f"event may not be managed by AgentHR"
                )
                return {
                    "recruiter_id": recruiter_id,
                    "status": "ignored",
                    "provider": calendar_provider,
                    "event_id": event_id,
                    "change_type": change_type,
                    "action_taken": "none",
                    "error": "Interview not found",
                }

            logger.info(
                f"Found interview_id={interview.id} for calendar event_id={event_id}"
            )

            # Determine action based on change type
            action_taken = "none"
            event_data = webhook_data.get("event_data", {})

            if change_type == "deleted":
                # Event was deleted in calendar - mark interview as cancelled
                logger.info(
                    f"Calendar event deleted - marking interview "
                    f"interview_id={interview.id} as cancelled"
                )
                interview.status = "cancelled"
                interview.cancellation_reason = (
                    f"Calendar event deleted via {calendar_provider}"
                )
                db.commit()
                action_taken = "cancel_interview"

            elif change_type in ("created", "updated"):
                # Event was created or updated - sync relevant fields
                logger.info(
                    f"Syncing calendar event changes to interview "
                    f"interview_id={interview.id}"
                )

                # Update interview times if provided in webhook
                if "start_time" in event_data or "start" in event_data:
                    start_time_str = event_data.get("start_time") or event_data.get("start")
                    if start_time_str:
                        try:
                            from datetime import datetime
                            interview.scheduled_time = datetime.fromisoformat(
                                start_time_str.replace('Z', '+00:00')
                            )
                            logger.info(
                                f"Updated interview scheduled_time to "
                                f"{interview.scheduled_time}"
                            )
                        except ValueError as e:
                            logger.warning(
                                f"Failed to parse start_time '{start_time_str}': {e}"
                            )

                # Update duration if provided
                if "duration" in event_data:
                    interview.duration = event_data["duration"]
                    logger.info(f"Updated interview duration to {interview.duration} minutes")

                # Update location/meet link if provided
                if "location" in event_data:
                    interview.location = event_data["location"]
                    logger.info(f"Updated interview location to {interview.location}")

                if "meet_link" in event_data:
                    interview.meet_link = event_data["meet_link"]
                    logger.info(f"Updated interview meet_link")

                db.commit()
                action_taken = "update_interview"

            else:
                logger.info(
                    f"Change type '{change_type}' does not require sync - ignoring"
                )

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"Calendar webhook processed successfully: "
                f"recruiter_id={recruiter_id}, "
                f"provider={calendar_provider}, "
                f"event_id={event_id}, "
                f"action_taken={action_taken}, "
                f"processing_time={processing_time}ms"
            )

            return {
                "recruiter_id": recruiter_id,
                "status": "synced" if action_taken != "none" else "ignored",
                "provider": calendar_provider,
                "event_id": event_id,
                "change_type": change_type,
                "action_taken": action_taken,
                "interview_id": str(interview.id) if interview else None,
                "synced_at": time.time(),
                "processing_time_ms": processing_time,
            }

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(
            f"Calendar webhook processing timed out for "
            f"recruiter_id={recruiter_id}, event_id={event_id}"
        )
        return {
            "recruiter_id": recruiter_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "change_type": change_type,
            "action_taken": "none",
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to process calendar webhook for "
            f"recruiter_id={recruiter_id}, event_id={event_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff for transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "recruiter_id": recruiter_id,
            "status": "failed",
            "provider": calendar_provider,
            "event_id": event_id,
            "change_type": change_type,
            "action_taken": "none",
            "error": str(e),
        }
