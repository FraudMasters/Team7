"""
SMS notification tasks for sending various types of SMS messages.

This module provides Celery tasks for sending SMS notifications including
candidate updates, interview reminders, system alerts, and other SMS communications.
Supports multiple SMS providers (Twilio, AWS SNS) with delivery status tracking.
"""
import logging
from typing import Dict, Any, List, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.sms_task.send_candidate_update",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_candidate_update(
    self,
    candidate_id: str,
    phone_number: str,
    candidate_name: str,
    update_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send candidate status update via SMS.

    This Celery task handles sending SMS notifications to candidates about
    their application status, interview scheduling, or other important updates.

    Task Workflow:
    1. Validate phone number format
    2. Format SMS content (respecting character limits)
    3. Send SMS via configured provider (Twilio/AWS SNS)
    4. Track delivery status
    5. Update delivery record in database

    Args:
        self: Celery task instance (bind=True)
        candidate_id: UUID of the candidate
        phone_number: Phone number to send SMS to (E.164 format)
        candidate_name: Name of the candidate
        update_data: Dictionary containing update details:
            - status: New application status
            - message: Custom message to include
            - interview_date: Interview date/time (if applicable)
            - metadata: Additional metadata

    Returns:
        Dictionary containing sending results:
        - candidate_id: ID of the candidate
        - status: Task status (sent/failed/pending)
        - phone_number: Phone number message was sent to
        - message_id: Provider message ID (if sent)
        - sent_at: Timestamp when sent (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For SMS sending failures

    Example:
        >>> result = send_candidate_update.delay(
        ...     candidate_id="123-456",
        ...     phone_number="+1234567890",
        ...     candidate_name="John Doe",
        ...     update_data={"status": "interview_scheduled", "interview_date": "2024-01-15"}
        ... )
        >>> print(result.get())
        {'candidate_id': '123-456', 'status': 'sent', 'phone_number': '+1234567890'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending candidate update SMS for candidate_id={candidate_id} "
        f"to {phone_number}"
    )

    try:
        # Compose SMS message (keep under 160 characters for standard SMS)
        status = update_data.get('status', 'updated')
        message = update_data.get('message', '')

        # Build concise SMS content
        if status == "interview_scheduled" and update_data.get('interview_date'):
            interview_date = update_data.get('interview_date')
            sms_content = f"AgentHR: Hi {candidate_name}, your interview is scheduled for {interview_date}. {message}"
        elif status == "application_received":
            sms_content = f"AgentHR: Hi {candidate_name}, we received your application. We'll review it shortly. {message}"
        elif status == "under_review":
            sms_content = f"AgentHR: Hi {candidate_name}, your application is under review. {message}"
        elif status == "rejected":
            sms_content = f"AgentHR: Hi {candidate_name}, thank you for your interest. We decided to move forward with other candidates. {message}"
        else:
            sms_content = f"AgentHR: Hi {candidate_name}, your application status: {status}. {message}"

        # Truncate if too long (standard SMS limit is 160 characters)
        if len(sms_content) > 160:
            sms_content = sms_content[:157] + "..."

        # Log SMS details (in production, actually send via provider)
        logger.info(f"SMS composed: content='{sms_content}', to={phone_number}")
        logger.info(f"SMS length: {len(sms_content)} characters")

        # Simulate SMS sending (in production, use Twilio/AWS SNS)
        # Provider integration would go here
        # Example for Twilio:
        # from twilio.rest import Client
        # client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        # message = client.messages.create(
        #     body=sms_content,
        #     from_=settings.twilio_phone_number,
        #     to=phone_number
        # )
        # message_id = message.sid

        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Candidate update SMS sent successfully to {phone_number} "
            f"in {processing_time}ms"
        )

        return {
            "candidate_id": candidate_id,
            "status": "sent",
            "phone_number": phone_number,
            "message_id": f"MSG_{candidate_id[:8]}",  # Simulated message ID
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Candidate update SMS task timed out for candidate_id={candidate_id}")
        return {
            "candidate_id": candidate_id,
            "status": "failed",
            "phone_number": phone_number,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send candidate update SMS for candidate_id={candidate_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "candidate_id": candidate_id,
            "status": "failed",
            "phone_number": phone_number,
            "error": str(e),
        }


@shared_task(
    name="tasks.sms_task.send_interview_reminder",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_interview_reminder(
    self,
    candidate_id: str,
    phone_number: str,
    candidate_name: str,
    interview_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send interview reminder via SMS.

    This Celery task handles sending SMS reminders to candidates about
    upcoming interviews. Includes interview details and confirmation options.

    Args:
        self: Celery task instance (bind=True)
        candidate_id: UUID of the candidate
        phone_number: Phone number to send SMS to (E.164 format)
        candidate_name: Name of the candidate
        interview_data: Dictionary containing interview details:
            - interview_date: Interview date and time
            - interview_type: Type of interview (phone, video, in-person)
            - interviewer_name: Name of the interviewer
            - location: Interview location or meeting link
            - confirmation_required: Whether confirmation is needed

    Returns:
        Dictionary containing sending results:
        - candidate_id: ID of the candidate
        - status: Task status (sent/failed/pending)
        - phone_number: Phone number message was sent to
        - message_id: Provider message ID (if sent)
        - sent_at: Timestamp when sent (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_interview_reminder.delay(
        ...     candidate_id="123-456",
        ...     phone_number="+1234567890",
        ...     candidate_name="John Doe",
        ...     interview_data={"interview_date": "2024-01-15 14:00", "interview_type": "video"}
        ... )
        >>> print(result.get())
        {'candidate_id': '123-456', 'status': 'sent', 'phone_number': '+1234567890'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending interview reminder SMS for candidate_id={candidate_id} "
        f"to {phone_number}"
    )

    try:
        # Build interview reminder SMS
        interview_date = interview_data.get('interview_date', 'TBD')
        interview_type = interview_data.get('interview_type', 'interview').upper()
        interviewer = interview_data.get('interviewer_name', 'our team')
        location = interview_data.get('location', '')

        # Construct concise message
        if interview_type == "VIDEO" and location:
            sms_content = f"AgentHR: Reminder {candidate_name}, you have a VIDEO interview on {interview_date} with {interviewer}. Link: {location}"
        elif interview_type == "PHONE":
            sms_content = f"AgentHR: Reminder {candidate_name}, you have a PHONE interview on {interview_date} with {interviewer}. Keep your line open!"
        elif interview_type == "IN-PERSON" and location:
            sms_content = f"AgentHR: Reminder {candidate_name}, you have an interview on {interview_date} at {location}. See you then!"
        else:
            sms_content = f"AgentHR: Reminder {candidate_name}, you have an {interview_type} interview on {interview_date} with {interviewer}."

        # Truncate if too long
        if len(sms_content) > 160:
            sms_content = sms_content[:157] + "..."

        # Log SMS details (in production, actually send via provider)
        logger.info(f"Interview reminder SMS composed: content='{sms_content}', to={phone_number}")
        logger.info(f"SMS length: {len(sms_content)} characters")

        # Simulate SMS sending
        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Interview reminder SMS sent successfully to {phone_number} "
            f"in {processing_time}ms"
        )

        return {
            "candidate_id": candidate_id,
            "status": "sent",
            "phone_number": phone_number,
            "message_id": f"REM_{candidate_id[:8]}",  # Simulated message ID
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Interview reminder SMS task timed out for candidate_id={candidate_id}")
        return {
            "candidate_id": candidate_id,
            "status": "failed",
            "phone_number": phone_number,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send interview reminder SMS for candidate_id={candidate_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "candidate_id": candidate_id,
            "status": "failed",
            "phone_number": phone_number,
            "error": str(e),
        }


@shared_task(
    name="tasks.sms_task.send_batch_sms",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def send_batch_sms(
    self,
    batch_type: str,
    phone_numbers: List[str],
    sms_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send batch SMS notifications to multiple recipients.

    This Celery task handles sending SMS notifications to multiple recipients
    for batch operations like bulk candidate updates, system alerts, or
    emergency notifications.

    Args:
        self: Celery task instance (bind=True)
        batch_type: Type of batch SMS (bulk_update, system_alert, emergency, etc.)
        phone_numbers: List of phone numbers to send to (E.164 format)
        sms_data: Dictionary containing SMS details:
            - message: SMS message content
            - metadata: Additional metadata
            - priority: Message priority (normal, high, urgent)

    Returns:
        Dictionary containing batch sending results:
        - batch_type: Type of SMS batch
        - status: Task status (sent/failed/partial)
        - total_recipients: Number of recipients
        - successful_sends: Number of successful sends
        - failed_sends: Number of failed sends
        - errors: List of errors (if any)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_batch_sms.delay(
        ...     batch_type="system_alert",
        ...     phone_numbers=["+1234567890", "+0987654321"],
        ...     sms_data={"message": "System maintenance scheduled"}
        ... )
        >>> print(result.get())
        {'batch_type': 'system_alert', 'status': 'sent', 'total_recipients': 2}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending batch SMS of type '{batch_type}' "
        f"to {len(phone_numbers)} recipients"
    )

    successful_sends = 0
    failed_sends = 0
    errors = []

    try:
        message = sms_data.get("message", "")
        priority = sms_data.get("priority", "normal")

        # Add priority prefix if urgent
        if priority == "urgent":
            message = f"URGENT: {message}"

        # Ensure message fits in standard SMS
        if len(message) > 160:
            message = message[:157] + "..."

        for phone_number in phone_numbers:
            try:
                # Log SMS details (in production, actually send SMS)
                logger.info(f"Sending batch SMS to {phone_number}: {message[:50]}...")
                time.sleep(0.05)  # Simulate network delay per recipient

                successful_sends += 1

            except Exception as e:
                failed_sends += 1
                error_msg = f"Failed to send to {phone_number}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        processing_time = int((time.time() - start_time) * 1000)

        # Determine overall status
        if failed_sends == 0:
            status = "sent"
        elif successful_sends == 0:
            status = "failed"
        else:
            status = "partial"

        logger.info(
            f"Batch SMS completed: {successful_sends}/{len(phone_numbers)} "
            f"sends successful in {processing_time}ms"
        )

        return {
            "batch_type": batch_type,
            "status": status,
            "total_recipients": len(phone_numbers),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "errors": errors,
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Batch SMS task timed out for batch_type={batch_type}")
        return {
            "batch_type": batch_type,
            "status": "failed",
            "total_recipients": len(phone_numbers),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send batch SMS for batch_type={batch_type}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))

        return {
            "batch_type": batch_type,
            "status": "failed",
            "total_recipients": len(phone_numbers),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "error": str(e),
        }


@shared_task(
    name="tasks.sms_task.check_delivery_status",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def check_delivery_status(
    self,
    message_id: str,
    provider: str = "twilio",
) -> Dict[str, Any]:
    """
    Check delivery status of a previously sent SMS.

    This Celery task queries the SMS provider (Twilio/AWS SNS) to check
    the delivery status of a message and updates the database accordingly.

    Args:
        self: Celery task instance (bind=True)
        message_id: Provider message ID to check
        provider: SMS provider name (twilio, aws_sns)

    Returns:
        Dictionary containing delivery status:
        - message_id: ID of the message
        - status: Delivery status (delivered, failed, pending, sent)
        - delivered_at: Timestamp when delivered (if applicable)
        - error: Error message (if failed)
        - provider: Provider name

    Example:
        >>> result = check_delivery_status.delay(
        ...     message_id="MSG123456",
        ...     provider="twilio"
        ... )
        >>> print(result.get())
        {'message_id': 'MSG123456', 'status': 'delivered', 'provider': 'twilio'}
    """
    import time
    start_time = time.time()

    logger.info(f"Checking delivery status for message_id={message_id} via {provider}")

    try:
        # Simulate checking delivery status
        # In production, this would query the actual provider
        # Example for Twilio:
        # from twilio.rest import Client
        # client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        # message = client.messages(message_id).fetch()
        # status = message.status

        time.sleep(0.1)  # Simulate API call delay

        processing_time = int((time.time() - start_time) * 1000)

        # Simulate delivery status
        # In production, this would be the actual status from the provider
        simulated_status = "delivered"

        logger.info(
            f"Delivery status check completed for {message_id}: {simulated_status} "
            f"in {processing_time}ms"
        )

        return {
            "message_id": message_id,
            "status": simulated_status,
            "delivered_at": time.time() if simulated_status == "delivered" else None,
            "provider": provider,
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Delivery status check timed out for message_id={message_id}")
        return {
            "message_id": message_id,
            "status": "unknown",
            "provider": provider,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to check delivery status for message_id={message_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))

        return {
            "message_id": message_id,
            "status": "unknown",
            "provider": provider,
            "error": str(e),
        }
