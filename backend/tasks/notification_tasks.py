"""
Email notification tasks for sending general notifications with delivery tracking.

This module provides Celery tasks for sending email notifications with
built-in retry logic, delivery tracking, and comprehensive error handling.
Includes support for application status change notifications.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.notification_tasks.send_email_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email_notification(
    self,
    notification_id: str,
    recipient_email: str,
    subject: str,
    message: str,
    notification_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send email notification with retry logic and delivery tracking.

    This Celery task handles sending email notifications with automatic retry
    on failure, exponential backoff, and comprehensive delivery tracking.
    It supports various notification types and includes metadata for tracking
    and analytics purposes.

    Task Workflow:
    1. Validate input parameters
    2. Compose email with subject and message
    3. Send email via configured SMTP/service
    4. Track delivery status and metrics
    5. Update notification record with delivery status
    6. Handle failures with exponential backoff retry

    Args:
        self: Celery task instance (bind=True)
        notification_id: Unique identifier for the notification
        recipient_email: Email address of the recipient
        subject: Email subject line
        message: Email body content (plain text or HTML)
        notification_type: Type of notification (general, alert, reminder, etc.)
        metadata: Optional dictionary containing additional tracking data:
            - priority: Email priority (high, normal, low)
            - template_name: Name of email template used
            - user_id: ID of the recipient user
            - category: Notification category
            - attachments: List of attachment metadata
            - send_at: Scheduled send time

    Returns:
        Dictionary containing notification delivery results:
        - notification_id: ID of the notification
        - status: Delivery status (sent/failed/pending)
        - recipient: Email address of recipient
        - notification_type: Type of notification sent
        - sent_at: Timestamp when sent (Unix timestamp)
        - delivered_at: Timestamp when delivery confirmed (Unix timestamp)
        - retry_count: Number of retry attempts made
        - processing_time_ms: Total processing time in milliseconds
        - delivery_provider: Email service provider used
        - message_id: Unique message ID from provider (if available)
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For email sending failures after max retries

    Example:
        >>> result = send_email_notification.delay(
        ...     notification_id="notif-123",
        ...     recipient_email="user@example.com",
        ...     subject="Welcome to AgentHR",
        ...     message="Thank you for signing up!",
        ...     notification_type="welcome",
        ...     metadata={"user_id": "user-456", "priority": "high"}
        ... )
        >>> print(result.get())
        {'notification_id': 'notif-123', 'status': 'sent', 'recipient': 'user@example.com'}
    """
    start_time = time.time()
    retry_count = self.request.retries

    logger.info(
        f"Sending email notification: notification_id={notification_id}, "
        f"type={notification_type}, to={recipient_email}, "
        f"retry_count={retry_count}/{self.max_retries}"
    )

    try:
        # Validate input parameters
        if not recipient_email:
            raise ValueError("recipient_email is required")
        if not subject:
            raise ValueError("subject is required")
        if not message:
            raise ValueError("message is required")

        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}

        priority = metadata.get("priority", "normal").lower()
        template_name = metadata.get("template_name", "default")
        user_id = metadata.get("user_id")
        category = metadata.get("category", "general")

        # Compose email
        logger.info(
            f"Composing email: notification_id={notification_id}, "
            f"template={template_name}, priority={priority}"
        )

        # Build email headers
        email_headers = {
            "X-Notification-ID": notification_id,
            "X-Notification-Type": notification_type,
            "X-Priority": "1" if priority == "high" else "3",
        }

        if user_id:
            email_headers["X-User-ID"] = user_id

        # Prepare email content
        email_body = message
        if metadata.get("include_footer", True):
            footer = "\n\n---\nThis is an automated email from AgentHR."
            email_body = message + footer

        # Log email composition
        logger.info(
            f"Email composed: notification_id={notification_id}, "
            f"subject='{subject}', to={recipient_email}, "
            f"body_length={len(email_body)}, priority={priority}"
        )

        # Simulate email sending (in production, use actual SMTP/service)
        # This is where you would integrate with:
        # - Python's smtplib
        # - SendGrid API
        # - AWS SES
        # - Mailgun
        # - Or an internal email service

        sent_timestamp = time.time()

        # Placeholder: Simulate email sending with small delay
        time.sleep(0.05)

        # In production, you would get a message_id from the email provider
        # message_id = smtp_service.send_email(
        #     to=recipient_email,
        #     subject=subject,
        #     body=email_body,
        #     headers=email_headers
        # )

        message_id = f"msg-{notification_id}-{int(sent_timestamp)}"

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Email notification sent successfully: notification_id={notification_id}, "
            f"to={recipient_email}, type={notification_type}, "
            f"message_id={message_id}, time={processing_time}ms"
        )

        return {
            "notification_id": notification_id,
            "status": "sent",
            "recipient": recipient_email,
            "notification_type": notification_type,
            "sent_at": sent_timestamp,
            "delivered_at": sent_timestamp,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "delivery_provider": "smtp-placeholder",  # Update with actual provider
            "message_id": message_id,
            "category": category,
        }

    except SoftTimeLimitExceeded:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Email notification task timed out: notification_id={notification_id}, "
            f"to={recipient_email}, time={processing_time}ms"
        )

        # Don't retry on timeout - it's likely a persistent issue
        return {
            "notification_id": notification_id,
            "status": "failed",
            "recipient": recipient_email,
            "notification_type": notification_type,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": "Task timed out",
        }

    except ValueError as e:
        # Validation errors - don't retry, will keep failing
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Validation error for email notification: notification_id={notification_id}, "
            f"error={str(e)}"
        )

        return {
            "notification_id": notification_id,
            "status": "failed",
            "recipient": recipient_email,
            "notification_type": notification_type,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": f"Validation error: {str(e)}",
        }

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed to send email notification: notification_id={notification_id}, "
            f"to={recipient_email}, error={str(e)}",
            exc_info=True,
        )

        # Retry with exponential backoff for transient errors
        if retry_count < self.max_retries:
            # Calculate exponential backoff: 60s, 120s, 240s
            backoff_delay = 60 * (2 ** retry_count)

            logger.warning(
                f"Retrying email notification: notification_id={notification_id}, "
                f"attempt={retry_count + 1}/{self.max_retries}, "
                f"backoff={backoff_delay}s"
            )

            raise self.retry(exc=e, countdown=backoff_delay)

        # Max retries exceeded - mark as permanently failed
        logger.error(
            f"Email notification failed after {self.max_retries} retries: "
            f"notification_id={notification_id}, to={recipient_email}"
        )

        return {
            "notification_id": notification_id,
            "status": "failed",
            "recipient": recipient_email,
            "notification_type": notification_type,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": f"Failed after {self.max_retries} retries: {str(e)}",
        }


@shared_task(
    name="tasks.notification_tasks.send_bulk_email_notifications",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def send_bulk_email_notifications(
    self,
    bulk_notification_id: str,
    recipient_emails: List[str],
    subject: str,
    message: str,
    notification_type: str = "bulk",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send bulk email notifications to multiple recipients with delivery tracking.

    This Celery task handles sending email notifications to multiple recipients
    with individual delivery tracking, partial failure handling, and comprehensive
    reporting of delivery statistics.

    Task Workflow:
    1. Validate recipient list and parameters
    2. Process each recipient individually
    3. Track successful and failed deliveries
    4. Aggregate delivery statistics
    5. Return comprehensive delivery report

    Args:
        self: Celery task instance (bind=True)
        bulk_notification_id: Unique identifier for the bulk notification batch
        recipient_emails: List of email addresses to send to
        subject: Email subject line
        message: Email body content
        notification_type: Type of notification (bulk, broadcast, etc.)
        metadata: Optional dictionary containing additional tracking data

    Returns:
        Dictionary containing bulk notification results:
        - bulk_notification_id: ID of the bulk notification
        - status: Overall status (sent/failed/partial)
        - notification_type: Type of notification
        - total_recipients: Total number of recipients
        - successful_deliveries: Number of successful deliveries
        - failed_deliveries: Number of failed deliveries
        - delivery_rate: Percentage of successful deliveries
        - processing_time_ms: Total processing time
        - errors: List of delivery errors (if any)
        - recipient_results: Detailed results per recipient

    Example:
        >>> result = send_bulk_email_notifications.delay(
        ...     bulk_notification_id="bulk-123",
        ...     recipient_emails=["user1@example.com", "user2@example.com"],
        ...     subject="System Update",
        ...     message="System will be updated tonight.",
        ...     notification_type="announcement"
        ... )
        >>> print(result.get())
        {'bulk_notification_id': 'bulk-123', 'status': 'sent', 'total_recipients': 2}
    """
    start_time = time.time()

    logger.info(
        f"Sending bulk email notification: bulk_notification_id={bulk_notification_id}, "
        f"recipients={len(recipient_emails)}, type={notification_type}"
    )

    successful_deliveries = 0
    failed_deliveries = 0
    errors = []
    recipient_results = []

    try:
        # Validate inputs
        if not recipient_emails:
            raise ValueError("recipient_emails cannot be empty")

        # Remove duplicates while preserving order
        unique_emails = list(dict.fromkeys(recipient_emails))
        if len(unique_emails) < len(recipient_emails):
            logger.warning(
                f"Removed {len(recipient_emails) - len(unique_emails)} duplicate email addresses"
            )

        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}

        # Process each recipient
        for idx, recipient_email in enumerate(unique_emails, 1):
            try:
                logger.info(
                    f"Processing recipient {idx}/{len(unique_emails)}: {recipient_email}"
                )

                # Generate individual notification ID
                notification_id = f"{bulk_notification_id}-{idx}"

                # Create individual notification result
                result = {
                    "notification_id": notification_id,
                    "recipient": recipient_email,
                    "status": "sent",
                    "sent_at": time.time(),
                }

                # Simulate sending (in production, actually send email)
                time.sleep(0.02)  # Simulate small delay per recipient

                successful_deliveries += 1
                recipient_results.append(result)

                logger.debug(
                    f"Successfully sent to {recipient_email} "
                    f"({successful_deliveries}/{len(unique_emails)})"
                )

            except Exception as e:
                failed_deliveries += 1
                error_msg = f"Failed to send to {recipient_email}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

                recipient_results.append({
                    "notification_id": f"{bulk_notification_id}-{idx}",
                    "recipient": recipient_email,
                    "status": "failed",
                    "error": str(e),
                })

        processing_time = int((time.time() - start_time) * 1000)

        # Calculate delivery rate
        delivery_rate = (successful_deliveries / len(unique_emails) * 100) if unique_emails else 0

        # Determine overall status
        if failed_deliveries == 0:
            status = "sent"
        elif successful_deliveries == 0:
            status = "failed"
        else:
            status = "partial"

        logger.info(
            f"Bulk email notification completed: bulk_notification_id={bulk_notification_id}, "
            f"status={status}, successful={successful_deliveries}, "
            f"failed={failed_deliveries}, rate={delivery_rate:.1f}%, "
            f"time={processing_time}ms"
        )

        return {
            "bulk_notification_id": bulk_notification_id,
            "status": status,
            "notification_type": notification_type,
            "total_recipients": len(unique_emails),
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "delivery_rate": round(delivery_rate, 2),
            "processing_time_ms": processing_time,
            "errors": errors,
            "recipient_results": recipient_results,
        }

    except SoftTimeLimitExceeded:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Bulk email notification task timed out: bulk_notification_id={bulk_notification_id}"
        )

        return {
            "bulk_notification_id": bulk_notification_id,
            "status": "partial",
            "notification_type": notification_type,
            "total_recipients": len(recipient_emails),
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": len(recipient_emails) - successful_deliveries,
            "processing_time_ms": processing_time,
            "error": "Task timed out",
        }

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed to send bulk email notification: "
            f"bulk_notification_id={bulk_notification_id}, error={str(e)}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            backoff_delay = 120 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=backoff_delay)

        return {
            "bulk_notification_id": bulk_notification_id,
            "status": "failed",
            "notification_type": notification_type,
            "total_recipients": len(recipient_emails),
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "processing_time_ms": processing_time,
            "error": str(e),
        }


def format_application_status_email(
    application_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format application status change notification email.

    This function formats an email notification for job application status changes,
    including application details, new status, and next steps for the candidate.

    Args:
        application_details: Application details dictionary containing:
            - application_id: UUID of the job application
            - user_email: Email address of the candidate
            - user_name: Full name of the candidate
            - vacancy_title: Title of the job vacancy
            - vacancy_id: UUID of the job vacancy
            - old_status: Previous application status
            - new_status: New application status
            - status_changed_at: Timestamp when status changed
            - additional_notes: Optional notes about the status change

    Returns:
        Dictionary containing email details:
        {
            "subject": "Application Status Update: [Job Title]",
            "body": "Email body with status update details...",
            "priority": "high" or "normal"
        }

    Example:
        >>> details = {
        ...     "user_name": "Jane Doe",
        ...     "vacancy_title": "Senior Developer",
        ...     "new_status": "UNDER_REVIEW"
        ... }
        >>> email = format_application_status_email(details)
        >>> print(email['subject'])
        'Application Status Update: Senior Developer'
    """
    try:
        logger.info("Formatting application status notification email")

        application_id = application_details.get("application_id")
        user_name = application_details.get("user_name", "Candidate")
        vacancy_title = application_details.get("vacancy_title", "Position")
        old_status = application_details.get("old_status", "")
        new_status = application_details.get("new_status", "SUBMITTED")
        status_changed_at = application_details.get(
            "status_changed_at", datetime.utcnow().isoformat()
        )
        additional_notes = application_details.get("additional_notes", "")

        # Map status to user-friendly messages
        status_messages = {
            "PENDING": {
                "emoji": "📝",
                "title": "Draft Application",
                "message": "Your application is being prepared.",
                "next_steps": "Complete and submit your application to proceed.",
                "priority": "normal",
            },
            "SUBMITTED": {
                "emoji": "✅",
                "title": "Application Submitted",
                "message": "Your application has been successfully submitted!",
                "next_steps": "Our team will review your application shortly. You'll receive an update once we've completed our initial review.",
                "priority": "normal",
            },
            "UNDER_REVIEW": {
                "emoji": "🔍",
                "title": "Application Under Review",
                "message": "Great news! Your application is currently being reviewed by our hiring team.",
                "next_steps": "We're carefully reviewing your qualifications. We'll contact you soon with next steps.",
                "priority": "high",
            },
            "REJECTED": {
                "emoji": "❌",
                "title": "Application Update",
                "message": "Thank you for your interest in this position.",
                "next_steps": "While we've decided to move forward with other candidates for this role, we appreciate the time you invested in your application. We encourage you to apply for other positions that match your skills.",
                "priority": "normal",
            },
            "ACCEPTED": {
                "emoji": "🎉",
                "title": "Congratulations!",
                "message": "We're excited to inform you that your application has been accepted!",
                "next_steps": "Our team will contact you shortly to discuss the next steps in the hiring process. Please watch your email for further instructions.",
                "priority": "high",
            },
        }

        status_info = status_messages.get(
            new_status,
            {
                "emoji": "📬",
                "title": "Application Status Update",
                "message": f"Your application status has been updated to: {new_status}",
                "next_steps": "We'll keep you informed of any changes.",
                "priority": "normal",
            },
        )

        # Build email subject
        subject = f"{status_info['emoji']} {status_info['title']}: {vacancy_title}"

        # Build email body
        body_lines = [
            f"Hello {user_name},",
            f"",
            f"{status_info['message']}",
            f"",
            f"Position: {vacancy_title}",
            f"Application ID: {application_id}",
            f"Status: {new_status.replace('_', ' ').title()}",
            f"Updated: {status_changed_at}",
            f"",
        ]

        # Add status transition information if available
        if old_status and old_status != new_status:
            body_lines.extend([
                f"Previous Status: {old_status.replace('_', ' ').title()}",
                f"",
            ])

        # Add additional notes if provided
        if additional_notes:
            body_lines.extend([
                f"Additional Information:",
                f"{additional_notes}",
                f"",
            ])

        # Add next steps
        body_lines.extend([
            f"What's Next:",
            f"{status_info['next_steps']}",
            f"",
            f"---",
            f"This is an automated notification from AgentHR.",
            f"You can track your application status at any time through your candidate portal.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": status_info["priority"],
        }

        logger.info(
            f"Application status notification email formatted successfully: "
            f"application_id={application_id}, status={new_status}"
        )
        return email_details

    except Exception as e:
        logger.error(
            f"Failed to format application status email: {e}", exc_info=True
        )
        # Return a basic email format on error
        return {
            "subject": f"Application Status Update: {application_details.get('vacancy_title', 'Your Application')}",
            "body": f"Hello {application_details.get('user_name', 'Candidate')},\n\n"
                   f"Your application status has been updated.\n\n"
                   f"Application ID: {application_details.get('application_id')}\n"
                   f"New Status: {application_details.get('new_status', 'Updated')}",
            "priority": "normal",
        }


@shared_task(
    name="tasks.notification_tasks.send_application_status_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_application_status_notification(
    self,
    application_id: str,
    user_id: str,
    user_email: str,
    user_name: str,
    vacancy_id: str,
    vacancy_title: str,
    old_status: str,
    new_status: str,
    additional_notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send notification when a job application status changes.

    This Celery task handles sending email notifications to candidates when their
    job application status changes. It formats user-friendly messages for each
    status transition and includes relevant next steps for the candidate.

    Task Workflow:
    1. Validate application and user details
    2. Format status-specific email content
    3. Send notification via email
    4. Track delivery status
    5. Handle failures with retry logic

    Args:
        self: Celery task instance (bind=True)
        application_id: UUID of the job application
        user_id: UUID of the candidate user
        user_email: Email address of the candidate
        user_name: Full name of the candidate
        vacancy_id: UUID of the job vacancy
        vacancy_title: Title of the job position
        old_status: Previous application status (PENDING, SUBMITTED, etc.)
        new_status: New application status
        additional_notes: Optional notes to include in the notification
        metadata: Optional dictionary containing additional tracking data

    Returns:
        Dictionary containing notification delivery results:
        - application_id: ID of the application
        - user_id: ID of the candidate
        - status: Delivery status (sent/failed)
        - old_status: Previous application status
        - new_status: New application status
        - notification_sent_at: Timestamp when sent
        - processing_time_ms: Processing time
        - message_id: Email message ID
        - error: Error message (if failed)

    Raises:
        ValueError: If required parameters are missing
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For email sending failures after max retries

    Example:
        >>> result = send_application_status_notification.delay(
        ...     application_id="app-123",
        ...     user_id="user-456",
        ...     user_email="jane@example.com",
        ...     user_name="Jane Doe",
        ...     vacancy_id="vac-789",
        ...     vacancy_title="Senior Developer",
        ...     old_status="SUBMITTED",
        ...     new_status="UNDER_REVIEW"
        ... )
        >>> print(result.get())
        {'application_id': 'app-123', 'status': 'sent', 'new_status': 'UNDER_REVIEW'}
    """
    start_time = time.time()
    retry_count = self.request.retries

    logger.info(
        f"Sending application status notification: application_id={application_id}, "
        f"user_id={user_id}, old_status={old_status}, new_status={new_status}, "
        f"retry_count={retry_count}/{self.max_retries}"
    )

    try:
        # Validate input parameters
        if not application_id:
            raise ValueError("application_id is required")
        if not user_id:
            raise ValueError("user_id is required")
        if not user_email:
            raise ValueError("user_email is required")
        if not vacancy_id:
            raise ValueError("vacancy_id is required")
        if not new_status:
            raise ValueError("new_status is required")

        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}

        # Prepare application details for email formatting
        status_changed_at = datetime.utcnow().isoformat()
        application_details = {
            "application_id": application_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name or "Candidate",
            "vacancy_id": vacancy_id,
            "vacancy_title": vacancy_title or "Position",
            "old_status": old_status,
            "new_status": new_status,
            "status_changed_at": status_changed_at,
            "additional_notes": additional_notes,
        }

        # Format email content based on status change
        email_details = format_application_status_email(application_details)

        logger.info(
            f"Email formatted for application {application_id}: "
            f"subject='{email_details['subject']}', priority={email_details['priority']}"
        )

        # Build notification metadata
        notification_metadata = {
            "application_id": application_id,
            "user_id": user_id,
            "vacancy_id": vacancy_id,
            "old_status": old_status,
            "new_status": new_status,
            "priority": email_details["priority"],
            "category": "application_status",
            "notification_type": "application_status_change",
        }
        notification_metadata.update(metadata)

        # Simulate email sending (in production, use actual SMTP/service)
        # This is where you would integrate with your email service
        sent_timestamp = time.time()
        time.sleep(0.05)  # Simulate small delay

        # Generate message ID
        message_id = f"app-status-{application_id}-{new_status}-{int(sent_timestamp)}"

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Application status notification sent successfully: "
            f"application_id={application_id}, user_email={user_email}, "
            f"status_change={old_status}->{new_status}, "
            f"message_id={message_id}, time={processing_time}ms"
        )

        return {
            "application_id": application_id,
            "user_id": user_id,
            "status": "sent",
            "recipient": user_email,
            "old_status": old_status,
            "new_status": new_status,
            "notification_sent_at": sent_timestamp,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "message_id": message_id,
            "subject": email_details["subject"],
        }

    except SoftTimeLimitExceeded:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Application status notification task timed out: "
            f"application_id={application_id}, time={processing_time}ms"
        )

        return {
            "application_id": application_id,
            "user_id": user_id,
            "status": "failed",
            "recipient": user_email,
            "old_status": old_status,
            "new_status": new_status,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": "Task timed out",
        }

    except ValueError as e:
        # Validation errors - don't retry, will keep failing
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Validation error for application status notification: "
            f"application_id={application_id}, error={str(e)}"
        )

        return {
            "application_id": application_id,
            "user_id": user_id,
            "status": "failed",
            "recipient": user_email,
            "old_status": old_status,
            "new_status": new_status,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": f"Validation error: {str(e)}",
        }

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed to send application status notification: "
            f"application_id={application_id}, error={str(e)}",
            exc_info=True,
        )

        # Retry with exponential backoff for transient errors
        if retry_count < self.max_retries:
            # Calculate exponential backoff: 60s, 120s, 240s
            backoff_delay = 60 * (2 ** retry_count)

            logger.warning(
                f"Retrying application status notification: "
                f"application_id={application_id}, "
                f"attempt={retry_count + 1}/{self.max_retries}, "
                f"backoff={backoff_delay}s"
            )

            raise self.retry(exc=e, countdown=backoff_delay)

        # Max retries exceeded - mark as permanently failed
        logger.error(
            f"Application status notification failed after {self.max_retries} retries: "
            f"application_id={application_id}, user_email={user_email}"
        )

        return {
            "application_id": application_id,
            "user_id": user_id,
            "status": "failed",
            "recipient": user_email,
            "old_status": old_status,
            "new_status": new_status,
            "retry_count": retry_count,
            "processing_time_ms": processing_time,
            "error": f"Failed after {self.max_retries} retries: {str(e)}",
        }
