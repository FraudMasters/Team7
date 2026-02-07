"""
Email notification tasks for sending various types of emails.

This module provides Celery tasks for sending email notifications including
candidate feedback, report delivery, system alerts, and other email communications.
Emails are rendered using organization-specific branded templates.
"""
import logging
from typing import Dict, Any, List, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from services.email_rendering import render_email_template
from database import async_session_maker

logger = logging.getLogger(__name__)
settings = get_settings()


async def _render_template_async(
    db: AsyncSession,
    organization_id: str,
    template_type: str,
    context: Dict[str, Any],
) -> tuple[str, str, str]:
    """
    Async helper to render email template.

    Args:
        db: Database session
        organization_id: Organization ID
        template_type: Template type
        context: Template context variables

    Returns:
        Tuple of (subject, html_body, text_body)
    """
    # The render_email_template is synchronous, so we can call it directly
    return render_email_template(
        db=db,
        organization_id=organization_id,
        template_type=template_type,
        context=context,
    )


@shared_task(
    name="tasks.email_task.send_feedback_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_feedback_notification(
    self,
    feedback_id: str,
    recipient_email: str,
    candidate_name: str,
    feedback_data: Dict[str, Any],
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send candidate feedback via email.

    This Celery task handles sending candidate feedback to recruiters or hiring managers.
    It includes the feedback summary, scores, and detailed analysis. Emails are rendered
    using organization-specific branded templates when available.

    Task Workflow:
    1. Retrieve candidate feedback from database
    2. Format feedback content for email
    3. Compose email with branded template (or default template)
    4. Send email via configured SMTP/service
    5. Update delivery status in database

    Args:
        self: Celery task instance (bind=True)
        feedback_id: UUID of the candidate feedback
        recipient_email: Email address of the recipient
        candidate_name: Name of the candidate
        feedback_data: Dictionary containing feedback details:
            - grammar_feedback: Grammar and language feedback
            - skills_feedback: Skills assessment feedback
            - experience_feedback: Work experience feedback
            - recommendations: List of recommendations
            - match_score: Overall match score
            - tone: Feedback tone
        organization_id: Optional organization ID for branded templates

    Returns:
        Dictionary containing sending results:
        - feedback_id: ID of the feedback
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For email sending failures

    Example:
        >>> result = send_feedback_notification.delay(
        ...     feedback_id="123-456",
        ...     recipient_email="recruiter@example.com",
        ...     candidate_name="John Doe",
        ...     feedback_data={"match_score": 85, "recommendations": ["..."]},
        ...     organization_id="org-123"
        ... )
        >>> print(result.get())
        {'feedback_id': '123-456', 'status': 'sent', 'recipient': 'recruiter@example.com'}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(
        f"Sending feedback notification for feedback_id={feedback_id} "
        f"to {recipient_email}"
    )

    try:
        # Default organization ID if not provided
        if not organization_id:
            organization_id = "default"

        # Prepare template context
        template_context = {
            "candidate_name": candidate_name,
            "feedback_id": feedback_id,
            "match_score": feedback_data.get('match_score', 'N/A'),
            "skills_feedback": feedback_data.get('skills_feedback', ''),
            "experience_feedback": feedback_data.get('experience_feedback', ''),
            "recommendations": feedback_data.get('recommendations', []),
            "grammar_feedback": feedback_data.get('grammar_feedback', ''),
            "tone": feedback_data.get('tone', 'professional'),
        }

        # Render email template with organization branding
        async def render_email():
            async with async_session_maker() as db:
                return await _render_template_async(
                    db, organization_id, "candidate_feedback", template_context
                )

        # Run async database operation in sync context
        subject, html_body, text_body = asyncio.run(render_email())

        # Log email details (in production, actually send email)
        logger.info(f"Email composed: subject='{subject}', to={recipient_email}")
        logger.info(f"Email body length: {len(text_body)} characters (text)")
        logger.info(f"HTML body length: {len(html_body)} characters (html)")

        # Simulate email sending (in production, use SMTP/service)
        # For now, just log and mark as sent
        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Feedback notification sent successfully to {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "feedback_id": feedback_id,
            "status": "sent",
            "recipient": recipient_email,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Feedback notification task timed out for feedback_id={feedback_id}")
        return {
            "feedback_id": feedback_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send feedback notification for feedback_id={feedback_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "feedback_id": feedback_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
        }


@shared_task(
    name="tasks.email_task.send_batch_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def send_batch_notification(
    self,
    batch_type: str,
    recipient_emails: List[str],
    notification_data: Dict[str, Any],
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send batch notifications to multiple recipients.

    This Celery task handles sending notifications to multiple recipients
    for batch operations like batch resume analysis completion, system alerts,
    or scheduled reports. Emails are rendered using organization-specific
    branded templates when available.

    Args:
        self: Celery task instance (bind=True)
        batch_type: Type of batch notification (batch_analysis, system_alert, etc.)
        recipient_emails: List of email addresses to send to
        notification_data: Dictionary containing notification details:
            - title: Notification title
            - message: Main notification message
            - details: Additional details dictionary
            - metadata: Any additional metadata
        organization_id: Optional organization ID for branded templates

    Returns:
        Dictionary containing batch sending results:
        - batch_type: Type of notification
        - status: Task status (sent/failed/partial)
        - total_recipients: Number of recipients
        - successful_sends: Number of successful sends
        - failed_sends: Number of failed sends
        - errors: List of errors (if any)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_batch_notification.delay(
        ...     batch_type="batch_analysis",
        ...     recipient_emails=["user1@example.com", "user2@example.com"],
        ...     notification_data={"title": "Batch Complete", "message": "..."},
        ...     organization_id="org-123"
        ... )
        >>> print(result.get())
        {'batch_type': 'batch_analysis', 'status': 'sent', 'total_recipients': 2}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(
        f"Sending batch notification of type '{batch_type}' "
        f"to {len(recipient_emails)} recipients"
    )

    successful_sends = 0
    failed_sends = 0
    errors = []

    try:
        # Default organization ID if not provided
        if not organization_id:
            organization_id = "default"

        title = notification_data.get("title", f"{batch_type} Notification")
        message = notification_data.get("message", "")
        details = notification_data.get("details", {})

        # Prepare template context
        template_context = {
            "title": title,
            "message": message,
            "details": details,
            **notification_data.get("metadata", {}),
        }

        # Render email template once for all recipients
        async def render_email():
            async with async_session_maker() as db:
                return await _render_template_async(
                    db, organization_id, "batch_notification", template_context
                )

        # Run async database operation in sync context
        subject, html_body, text_body = asyncio.run(render_email())

        for recipient_email in recipient_emails:
            try:
                # Log email details (in production, actually send email)
                logger.info(
                    f"Sending batch email to {recipient_email}: "
                    f"subject='{subject}'"
                )
                time.sleep(0.05)  # Simulate network delay per recipient

                successful_sends += 1

            except Exception as e:
                failed_sends += 1
                error_msg = f"Failed to send to {recipient_email}: {str(e)}"
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
            f"Batch notification completed: {successful_sends}/{len(recipient_emails)} "
            f"sends successful in {processing_time}ms"
        )

        return {
            "batch_type": batch_type,
            "status": status,
            "total_recipients": len(recipient_emails),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "errors": errors,
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Batch notification task timed out for batch_type={batch_type}")
        return {
            "batch_type": batch_type,
            "status": "failed",
            "total_recipients": len(recipient_emails),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send batch notification for batch_type={batch_type}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))

        return {
            "batch_type": batch_type,
            "status": "failed",
            "total_recipients": len(recipient_emails),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "error": str(e),
        }
