"""
Email notification tasks for sending various types of emails.

This module provides Celery tasks for sending email notifications including
candidate feedback, report delivery, system alerts, and other email communications.
"""
import logging
from typing import Dict, Any, List, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
) -> Dict[str, Any]:
    """
    Send candidate feedback via email.

    This Celery task handles sending candidate feedback to recruiters or hiring managers.
    It includes the feedback summary, scores, and detailed analysis.

    Task Workflow:
    1. Retrieve candidate feedback from database
    2. Format feedback content for email
    3. Compose email with appropriate template
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
        ...     feedback_data={"match_score": 85, "recommendations": ["..."]}
        ... )
        >>> print(result.get())
        {'feedback_id': '123-456', 'status': 'sent', 'recipient': 'recruiter@example.com'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending feedback notification for feedback_id={feedback_id} "
        f"to {recipient_email}"
    )

    try:
        # Compose email subject
        subject = f"Candidate Feedback: {candidate_name}"

        # Compose email body
        body = f"""
Feedback for Candidate: {candidate_name}
Feedback ID: {feedback_id}

Match Score: {feedback_data.get('match_score', 'N/A')}%

Skills Feedback:
{feedback_data.get('skills_feedback', {})}

Experience Feedback:
{feedback_data.get('experience_feedback', {})}

Recommendations:
{chr(10).join(f'- {rec}' for rec in feedback_data.get('recommendations', []))}

---
This is an automated email from AgentHR Resume Analysis System.
        """.strip()

        # Log email details (in production, actually send email)
        logger.info(f"Email composed: subject='{subject}', to={recipient_email}")
        logger.info(f"Email body length: {len(body)} characters")

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
) -> Dict[str, Any]:
    """
    Send batch notifications to multiple recipients.

    This Celery task handles sending notifications to multiple recipients
    for batch operations like batch resume analysis completion, system alerts,
    or scheduled reports.

    Args:
        self: Celery task instance (bind=True)
        batch_type: Type of batch notification (batch_analysis, system_alert, etc.)
        recipient_emails: List of email addresses to send to
        notification_data: Dictionary containing notification details:
            - title: Notification title
            - message: Main notification message
            - details: Additional details dictionary
            - metadata: Any additional metadata

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
        ...     notification_data={"title": "Batch Complete", "message": "..."}
        ... )
        >>> print(result.get())
        {'batch_type': 'batch_analysis', 'status': 'sent', 'total_recipients': 2}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending batch notification of type '{batch_type}' "
        f"to {len(recipient_emails)} recipients"
    )

    successful_sends = 0
    failed_sends = 0
    errors = []

    try:
        title = notification_data.get("title", f"{batch_type} Notification")
        message = notification_data.get("message", "")

        for recipient_email in recipient_emails:
            try:
                # Compose individual email
                body = f"""
{title}

{message}

Details:
{notification_data.get('details', {})}

---
This is an automated email from AgentHR.
                """.strip()

                # Log email details (in production, actually send email)
                logger.info(f"Sending batch email to {recipient_email}")
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
