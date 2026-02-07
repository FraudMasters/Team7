"""
Email notification tasks for asynchronous email sending.

This module provides Celery tasks for sending various types of email notifications
including search alerts, backup notifications, candidate feedback, and system alerts.
It handles email composition, delivery, retries, and status tracking.

Tasks in this module use the EmailService for actual SMTP operations and support
HTML templates, plain text fallbacks, and bulk email operations.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from services.email_service import get_email_service, EmailService

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.email_tasks.send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email_task(
    self,
    to: str,
    subject: str,
    body: str,
    email_type: str = "general",
    html: bool = False,
    reply_to: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send an email asynchronously via Celery task.

    This is the primary email sending task that can be used for any type of email.
    It supports both HTML and plain text emails, CC/BCC recipients, and custom
    reply-to addresses.

    Task Workflow:
    1. Retrieve email service instance
    2. Compose email with provided parameters
    3. Send email via configured SMTP service
    4. Return delivery status with timing information

    Args:
        self: Celery task instance (bind=True)
        to: Primary recipient email address
        subject: Email subject line
        body: Email body content (HTML or plain text based on html parameter)
        email_type: Type of email for logging/tracking (e.g., "notification", "alert")
        html: Whether body is HTML (True) or plain text (False)
        reply_to: Optional reply-to email address
        cc: Optional list of CC recipient email addresses
        bcc: Optional list of BCC recipient email addresses

    Returns:
        Dictionary containing sending results:
        - email_type: Type of email sent
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For SMTP or email service errors

    Example:
        >>> result = send_email_task.delay(
        ...     to="user@example.com",
        ...     subject="Welcome to AgentHR",
        ...     body="<h1>Welcome!</h1><p>Thanks for joining.</p>",
        ...     email_type="welcome",
        ...     html=True
        ... )
        >>> print(result.get())
        {'email_type': 'welcome', 'status': 'sent', 'recipient': 'user@example.com'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending {email_type} email to {to} with subject '{subject}'"
    )

    try:
        # Get email service instance
        email_service = get_email_service()

        # Check if email sending is enabled
        if not email_service.enabled:
            logger.warning(f"Email sending disabled, skipping email to {to}")
            return {
                "email_type": email_type,
                "status": "skipped",
                "recipient": to,
                "error": "Email sending is disabled",
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Send email
        success = email_service.send_email(
            to=to,
            subject=subject,
            body=body,
            html=html,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
        )

        processing_time = int((time.time() - start_time) * 1000)

        if success:
            logger.info(
                f"Email sent successfully to {to} in {processing_time}ms"
            )
            return {
                "email_type": email_type,
                "status": "sent",
                "recipient": to,
                "sent_at": time.time(),
                "processing_time_ms": processing_time,
            }
        else:
            logger.error(f"Failed to send email to {to}")
            return {
                "email_type": email_type,
                "status": "failed",
                "recipient": to,
                "error": "Email service returned failure",
                "processing_time_ms": processing_time,
            }

    except SoftTimeLimitExceeded:
        logger.error(f"Email sending task timed out for {to}")
        return {
            "email_type": email_type,
            "status": "failed",
            "recipient": to,
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to send email to {to}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "email_type": email_type,
            "status": "failed",
            "recipient": to,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


@shared_task(
    name="tasks.email_tasks.send_template_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_template_email_task(
    self,
    to: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    email_type: str = "template",
    reply_to: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send a template-based email asynchronously.

    This Celery task handles sending emails using predefined HTML templates.
    Templates are rendered with the provided context dictionary and sent
    via the configured SMTP service.

    Task Workflow:
    1. Retrieve email service instance
    2. Render email template with context variables
    3. Send HTML email via configured SMTP service
    4. Return delivery status with timing information

    Args:
        self: Celery task instance (bind=True)
        to: Primary recipient email address
        subject: Email subject line
        template_name: Name of the template (without .html extension)
        context: Dictionary of variables for template rendering
        email_type: Type of email for logging/tracking
        reply_to: Optional reply-to email address
        cc: Optional list of CC recipient email addresses
        bcc: Optional list of BCC recipient email addresses

    Returns:
        Dictionary containing sending results:
        - email_type: Type of email sent
        - template_name: Template used
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_template_email_task.delay(
        ...     to="user@example.com",
        ...     subject="New Match Alert",
        ...     template_name="search_alert",
        ...     context={"candidate_name": "John Doe", "match_score": 85}
        ... )
        >>> print(result.get())
        {'email_type': 'template', 'template_name': 'search_alert', 'status': 'sent'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending template email '{template_name}' to {to}"
    )

    try:
        # Get email service instance
        email_service = get_email_service()

        # Check if email sending is enabled
        if not email_service.enabled:
            logger.warning(f"Email sending disabled, skipping template email to {to}")
            return {
                "email_type": email_type,
                "template_name": template_name,
                "status": "skipped",
                "recipient": to,
                "error": "Email sending is disabled",
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Send template email
        success = email_service.send_template_email(
            to=to,
            subject=subject,
            template_name=template_name,
            context=context,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
        )

        processing_time = int((time.time() - start_time) * 1000)

        if success:
            logger.info(
                f"Template email '{template_name}' sent successfully to {to} in {processing_time}ms"
            )
            return {
                "email_type": email_type,
                "template_name": template_name,
                "status": "sent",
                "recipient": to,
                "sent_at": time.time(),
                "processing_time_ms": processing_time,
            }
        else:
            logger.error(f"Failed to send template email '{template_name}' to {to}")
            return {
                "email_type": email_type,
                "template_name": template_name,
                "status": "failed",
                "recipient": to,
                "error": "Email service returned failure",
                "processing_time_ms": processing_time,
            }

    except SoftTimeLimitExceeded:
        logger.error(f"Template email task timed out for {to}")
        return {
            "email_type": email_type,
            "template_name": template_name,
            "status": "failed",
            "recipient": to,
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to send template email '{template_name}' to {to}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "email_type": email_type,
            "template_name": template_name,
            "status": "failed",
            "recipient": to,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


@shared_task(
    name="tasks.email_tasks.send_bulk_email_task",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def send_bulk_email_task(
    self,
    recipients: List[Dict[str, Any]],
    subject: str,
    template_name: str,
    email_type: str = "bulk",
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send personalized bulk emails to multiple recipients.

    This Celery task handles sending personalized emails to multiple recipients
    using a template. Each recipient receives an email with their own context
    variables rendered into the template.

    Task Workflow:
    1. Validate recipients list
    2. Retrieve email service instance
    3. Send personalized emails to each recipient
    4. Aggregate results and return summary

    Args:
        self: Celery task instance (bind=True)
        recipients: List of dictionaries, each containing:
            - email: Recipient email address
            - context: Dictionary of variables for template rendering
        subject: Email subject line
        template_name: Name of the template (without .html extension)
        email_type: Type of email for logging/tracking
        reply_to: Optional reply-to email address

    Returns:
        Dictionary containing bulk sending results:
        - email_type: Type of email sent
        - template_name: Template used
        - status: Overall task status (sent/failed/partial)
        - total_recipients: Number of recipients
        - successful_sends: Number of successful sends
        - failed_sends: Number of failed sends
        - errors: List of error messages (if any)
        - processing_time_ms: Total processing time

    Example:
        >>> recipients = [
        ...     {"email": "user1@example.com", "context": {"name": "John"}},
        ...     {"email": "user2@example.com", "context": {"name": "Jane"}},
        ... ]
        >>> result = send_bulk_email_task.delay(
        ...     recipients=recipients,
        ...     subject="Weekly Update",
        ...     template_name="notification"
        ... )
        >>> print(result.get())
        {'email_type': 'bulk', 'status': 'sent', 'total_recipients': 2, 'successful_sends': 2}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(
        f"Sending bulk email '{template_name}' to {len(recipients)} recipients"
    )

    try:
        # Get email service instance
        email_service = get_email_service()

        # Check if email sending is enabled
        if not email_service.enabled:
            logger.warning("Email sending disabled, skipping bulk email")
            return {
                "email_type": email_type,
                "template_name": template_name,
                "status": "skipped",
                "total_recipients": len(recipients),
                "successful_sends": 0,
                "failed_sends": len(recipients),
                "error": "Email sending is disabled",
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Prepare recipients list for email service
        recipient_list = [
            (r["email"], r.get("context", {}))
            for r in recipients
        ]

        # Send bulk emails
        result = email_service.send_bulk_emails(
            recipients=recipient_list,
            subject=subject,
            template_name=template_name,
            reply_to=reply_to,
        )

        processing_time = int((time.time() - start_time) * 1000)

        # Determine overall status
        if result["failed"] == 0:
            status = "sent"
        elif result["success"] == 0:
            status = "failed"
        else:
            status = "partial"

        logger.info(
            f"Bulk email completed: {result['success']}/{result['total']} sent, "
            f"{result['failed']} failed in {processing_time}ms"
        )

        return {
            "email_type": email_type,
            "template_name": template_name,
            "status": status,
            "total_recipients": result["total"],
            "successful_sends": result["success"],
            "failed_sends": result["failed"],
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Bulk email task timed out for template '{template_name}'")
        return {
            "email_type": email_type,
            "template_name": template_name,
            "status": "failed",
            "total_recipients": len(recipients),
            "successful_sends": 0,
            "failed_sends": len(recipients),
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to send bulk email '{template_name}': {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))

        return {
            "email_type": email_type,
            "template_name": template_name,
            "status": "failed",
            "total_recipients": len(recipients),
            "successful_sends": 0,
            "failed_sends": len(recipients),
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


@shared_task(
    name="tasks.email_tasks.send_search_alert_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_search_alert_email_task(
    self,
    alert_id: str,
    saved_search_id: str,
    resume_id: str,
    recipient_email: str,
    candidate_name: str,
    match_score: int,
    matched_skills: List[str],
    saved_search_name: str,
) -> Dict[str, Any]:
    """
    Send search alert notification email.

    This Celery task handles sending search alert emails when a new resume
    matches a user's saved search criteria. It uses the search_alert template
    to render a formatted email with match details.

    Task Workflow:
    1. Retrieve email service instance
    2. Render search alert template with match details
    3. Send HTML email to recipient
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        alert_id: UUID of the search alert
        saved_search_id: UUID of the saved search that matched
        resume_id: UUID of the matching resume
        recipient_email: Email address to send notification to
        candidate_name: Name of the candidate
        match_score: Match score percentage (0-100)
        matched_skills: List of skills that matched
        saved_search_name: Name of the saved search

    Returns:
        Dictionary containing sending results:
        - alert_id: ID of the alert
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_search_alert_email_task.delay(
        ...     alert_id="alert-123",
        ...     saved_search_id="search-456",
        ...     resume_id="resume-789",
        ...     recipient_email="user@example.com",
        ...     candidate_name="John Doe",
        ...     match_score=85,
        ...     matched_skills=["Python", "FastAPI"],
        ...     saved_search_name="Senior Python Developer"
        ... )
        >>> print(result.get())
        {'alert_id': 'alert-123', 'status': 'sent'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending search alert email for alert_id={alert_id} to {recipient_email}"
    )

    try:
        # Get email service instance
        email_service = get_email_service()

        # Check if email sending is enabled
        if not email_service.enabled:
            logger.warning(f"Email sending disabled, skipping search alert to {recipient_email}")
            return {
                "alert_id": alert_id,
                "status": "skipped",
                "recipient": recipient_email,
                "error": "Email sending is disabled",
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Prepare template context
        context = {
            "candidate_name": candidate_name,
            "match_score": match_score,
            "matched_skills": matched_skills,
            "saved_search_name": saved_search_name,
            "alert_id": alert_id,
            "resume_id": resume_id,
        }

        # Compose subject
        subject = f"New Match: {candidate_name} matches your saved search '{saved_search_name}'"

        # Send template email
        success = email_service.send_template_email(
            to=recipient_email,
            subject=subject,
            template_name=EmailService.TEMPLATE_MATCH_ALERT,
            context=context,
        )

        processing_time = int((time.time() - start_time) * 1000)

        if success:
            logger.info(
                f"Search alert email sent successfully to {recipient_email} in {processing_time}ms"
            )
            return {
                "alert_id": alert_id,
                "status": "sent",
                "recipient": recipient_email,
                "sent_at": time.time(),
                "processing_time_ms": processing_time,
            }
        else:
            logger.error(f"Failed to send search alert email to {recipient_email}")
            return {
                "alert_id": alert_id,
                "status": "failed",
                "recipient": recipient_email,
                "error": "Email service returned failure",
                "processing_time_ms": processing_time,
            }

    except SoftTimeLimitExceeded:
        logger.error(f"Search alert email task timed out for alert_id={alert_id}")
        return {
            "alert_id": alert_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to send search alert email for alert_id={alert_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "alert_id": alert_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


@shared_task(
    name="tasks.email_tasks.send_backup_notification_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_backup_notification_email_task(
    self,
    backup_id: str,
    operation_type: str,
    status: str,
    recipient_email: str,
    details: Dict[str, Any],
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send backup notification email.

    This Celery task handles sending backup notification emails for backup
    operations (success/failure). It uses the backup_notification template
    to render a formatted email with operation details.

    Task Workflow:
    1. Retrieve email service instance
    2. Render backup notification template with operation details
    3. Send HTML email to recipient
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        backup_id: UUID of the backup operation
        operation_type: Type of backup operation (backup, restore)
        status: Operation status (success, failure, warning)
        recipient_email: Email address to send notification to
        details: Dictionary containing operation details:
            - started_at: Operation start timestamp
            - completed_at: Operation completion timestamp
            - duration_seconds: Operation duration
            - file_count: Number of files processed
            - total_size_bytes: Total size processed
        error_message: Optional error message for failed operations

    Returns:
        Dictionary containing sending results:
        - backup_id: ID of the backup
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_backup_notification_email_task.delay(
        ...     backup_id="backup-123",
        ...     operation_type="backup",
        ...     status="success",
        ...     recipient_email="admin@example.com",
        ...     details={"duration_seconds": 45, "file_count": 152}
        ... )
        >>> print(result.get())
        {'backup_id': 'backup-123', 'status': 'sent'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending backup notification email for backup_id={backup_id} to {recipient_email}"
    )

    try:
        # Get email service instance
        email_service = get_email_service()

        # Check if email sending is enabled
        if not email_service.enabled:
            logger.warning(f"Email sending disabled, skipping backup notification to {recipient_email}")
            return {
                "backup_id": backup_id,
                "status": "skipped",
                "recipient": recipient_email,
                "error": "Email sending is disabled",
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Prepare template context
        context = {
            "backup_id": backup_id,
            "operation_type": operation_type,
            "status": status,
            "details": details,
            "error_message": error_message,
        }

        # Determine subject and template based on status
        if status == "success":
            template_name = EmailService.TEMPLATE_BACKUP_SUCCESS
            subject = f"Backup {operation_type.title()} Completed Successfully"
        else:
            template_name = EmailService.TEMPLATE_BACKUP_FAILURE
            severity = "Failed" if status == "failure" else "Warning"
            subject = f"Backup {operation_type.title()} {severity}"

        # Send template email
        success = email_service.send_template_email(
            to=recipient_email,
            subject=subject,
            template_name=template_name,
            context=context,
        )

        processing_time = int((time.time() - start_time) * 1000)

        if success:
            logger.info(
                f"Backup notification email sent successfully to {recipient_email} in {processing_time}ms"
            )
            return {
                "backup_id": backup_id,
                "status": "sent",
                "recipient": recipient_email,
                "sent_at": time.time(),
                "processing_time_ms": processing_time,
            }
        else:
            logger.error(f"Failed to send backup notification email to {recipient_email}")
            return {
                "backup_id": backup_id,
                "status": "failed",
                "recipient": recipient_email,
                "error": "Email service returned failure",
                "processing_time_ms": processing_time,
            }

    except SoftTimeLimitExceeded:
        logger.error(f"Backup notification email task timed out for backup_id={backup_id}")
        return {
            "backup_id": backup_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to send backup notification email for backup_id={backup_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "backup_id": backup_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }
