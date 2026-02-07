"""
Comment notification tasks for @mentions and comment replies.

This module provides Celery tasks for sending email notifications about
@mentions in team comments, comment replies, and comment thread updates.
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


def format_comment_mention_email(
    comment_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format comment mention notification email.

    This function formats an email notification for @mentions in team comments,
    including comment content, author information, and candidate context.

    Args:
        comment_details: Comment details dictionary containing:
            - comment_id: UUID of the comment
            - content: Comment content text
            - author_name: Name of the comment author
            - author_email: Email of the comment author
            - resume_id: UUID of the candidate resume being discussed
            - candidate_name: Name of the candidate being discussed
            - parent_comment_id: Optional UUID of parent comment (if reply)
            - created_at: Timestamp when comment was created

    Returns:
        Dictionary containing email details:
        {
            "subject": "You were mentioned in a comment",
            "body": "Email body with comment details...",
            "priority": "normal"
        }

    Example:
        >>> details = {"author_name": "John", "content": "What do you think?"}
        >>> email = format_comment_mention_email(details)
        >>> print(email['subject'])
        'You were mentioned in a comment'
    """
    try:
        logger.info("Formatting comment mention notification email")

        comment_id = comment_details.get("comment_id")
        content = comment_details.get("content", "")
        author_name = comment_details.get("author_name", "Unknown")
        author_email = comment_details.get("author_email", "")
        candidate_name = comment_details.get("candidate_name", "Unknown candidate")
        parent_comment_id = comment_details.get("parent_comment_id")
        created_at = comment_details.get("created_at", datetime.utcnow().isoformat())

        # Determine if this is a reply
        is_reply = parent_comment_id is not None
        comment_type = "reply to a comment" if is_reply else "comment"
        comment_type_emoji = "💬" if is_reply else "💭"

        # Build email subject
        subject = f"{comment_type_emoji} You were mentioned in a {comment_type} about {candidate_name}"

        # Build email body
        body_lines = [
            f"You were mentioned in a team comment",
            f"",
            f"Candidate: {candidate_name}",
            f"Author: {author_name} ({author_email})",
            f"Time: {created_at}",
            f"",
            f"Comment:",
            f"  {content}",
        ]

        if is_reply:
            body_lines.extend([
                f"",
                f"This is a reply to a comment thread.",
            ])

        body_lines.extend([
            f"",
            f"---",
            f"This is an automated notification from AgentHR Team Collaboration.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "normal",
        }

        logger.info("Comment mention notification email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format comment mention email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": "You were mentioned in a comment",
            "body": f"You were mentioned in a comment. Comment ID: {comment_details.get('comment_id')}",
            "priority": "normal",
        }


def format_comment_reply_email(
    comment_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format comment reply notification email.

    This function formats an email notification for replies to comments,
    including reply content and thread context.

    Args:
        comment_details: Comment reply details dictionary containing:
            - comment_id: UUID of the reply comment
            - parent_comment_id: UUID of the parent comment being replied to
            - content: Reply content text
            - author_name: Name of the reply author
            - author_email: Email of the reply author
            - resume_id: UUID of the candidate resume being discussed
            - candidate_name: Name of the candidate being discussed
            - original_author_name: Name of the original comment author
            - created_at: Timestamp when reply was created

    Returns:
        Dictionary containing email details:
        {
            "subject": "Someone replied to your comment",
            "body": "Email body with reply details...",
            "priority": "normal"
        }

    Example:
        >>> details = {"author_name": "Jane", "content": "I agree!"}
        >>> email = format_comment_reply_email(details)
        >>> print(email['subject'])
        'Someone replied to your comment'
    """
    try:
        logger.info("Formatting comment reply notification email")

        content = comment_details.get("content", "")
        author_name = comment_details.get("author_name", "Unknown")
        author_email = comment_details.get("author_email", "")
        candidate_name = comment_details.get("candidate_name", "Unknown candidate")
        created_at = comment_details.get("created_at", datetime.utcnow().isoformat())

        # Build email subject
        subject = f"💬 Reply to your comment about {candidate_name}"

        # Build email body
        body_lines = [
            f"Someone replied to your comment",
            f"",
            f"Candidate: {candidate_name}",
            f"Reply from: {author_name} ({author_email})",
            f"Time: {created_at}",
            f"",
            f"Reply:",
            f"  {content}",
            f"",
            f"---",
            f"This is an automated notification from AgentHR Team Collaboration.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "normal",
        }

        logger.info("Comment reply notification email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format comment reply email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": "Reply to your comment",
            "body": f"Someone replied to your comment about {comment_details.get('candidate_name', 'a candidate')}",
            "priority": "normal",
        }


def send_comment_notification_via_email(
    recipients: List[str],
    email_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send comment notification via email to specified recipients.

    This function sends a comment notification email using the configured
    email service. In production, this would integrate with SMTP, SendGrid,
    AWS SES, or similar.

    Args:
        recipients: List of email addresses to send the notification to
        email_details: Email details dictionary containing:
            - subject: Email subject line
            - body: Email body content
            - priority: Email priority (high/normal)
            - attachments: Optional list of attachments

    Returns:
        Dictionary containing email sending results:
        - success: Whether email was sent successfully
        - recipients_count: Number of recipients
        - error: Error message (if failed)

    Example:
        >>> details = {"subject": "Test", "body": "Body", "priority": "normal"}
        >>> result = send_comment_notification_via_email(["user@example.com"], details)
        >>> result['success']
        True
    """
    # Note: This is a placeholder for email sending
    # In a real implementation, you would use:
    # - Python's smtplib with email.mime modules
    # - SendGrid API
    # - AWS SES
    # - Mailgun
    # Or an internal email service

    try:
        subject = email_details.get("subject", "Comment Notification")
        body = email_details.get("body", "")
        priority = email_details.get("priority", "normal")

        logger.info(
            f"Sending comment notification email: subject='{subject}', "
            f"to={len(recipients)} recipients, priority={priority}"
        )

        # Placeholder: Log email details
        # In production, this would actually send the email
        email_message = {
            "subject": subject,
            "from": settings.smtp_default_from if hasattr(settings, 'smtp_default_from') else "noreply@agenthr.com",
            "to": recipients,
            "body": body,
            "priority": priority,
        }

        logger.info(
            f"Email prepared: from={email_message['from']}, "
            f"subject='{subject}', to={len(recipients)} recipients"
        )

        # Simulate successful email sending
        # In production: smtp.send_message(email_message)
        success = True
        error = None

        logger.info(f"Comment notification email sent successfully to {len(recipients)} recipients")

        return {
            "success": success,
            "recipients_count": len(recipients),
            "error": error,
        }

    except Exception as e:
        logger.error(f"Failed to send comment notification email: {e}", exc_info=True)
        return {
            "success": False,
            "recipients_count": len(recipients),
            "error": str(e),
        }


@shared_task(
    name="tasks.comment_notifications.send_comment_mention_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_comment_mention_notification(
    self,
    comment_id: UUID,
    mentioned_user_id: UUID,
    mentioned_user_email: str,
    comment_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send notification when a user is @mentioned in a comment.

    This Celery task handles sending email notifications when a user is
    @mentioned in a team comment. It formats the notification with comment
    content, author information, and candidate context.

    Task Workflow:
    1. Format notification email with comment details
    2. Send notification to the mentioned user
    3. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        comment_id: UUID of the comment where mention occurred
        mentioned_user_id: UUID of the user who was mentioned
        mentioned_user_email: Email address of the mentioned user
        comment_details: Dictionary containing comment information:
            - content: Comment content text
            - author_name: Name of the comment author
            - author_email: Email of the comment author
            - resume_id: UUID of the candidate resume
            - candidate_name: Name of the candidate being discussed
            - parent_comment_id: Optional parent comment UUID (if reply)
            - created_at: Timestamp when comment was created

    Returns:
        Dictionary containing notification results:
        - comment_id: UUID of the comment
        - mentioned_user_id: UUID of the mentioned user
        - notification_type: Type of notification (comment_mention)
        - status: Task status (sent/failed)
        - delivery_successful: Whether delivery was successful
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For email sending errors

    Example:
        >>> from tasks.comment_notifications import send_comment_mention_notification
        >>> from uuid import uuid4
        >>> details = {"content": "What do you think?", "author_name": "John"}
        >>> task = send_comment_mention_notification.delay(
        ...     uuid4(), uuid4(), "user@example.com", details
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Sending comment mention notification for comment: {comment_id}, "
            f"mentioned user: {mentioned_user_id}"
        )

        # Step 1: Format notification email
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_notification",
            "message": "Formatting mention notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Formatting mention notification email")

        email_details = format_comment_mention_email(comment_details)

        # Step 2: Send notification to mentioned user
        recipients = [mentioned_user_email]

        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_notification",
            "message": "Sending mention notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending mention notification email")

        delivery_result = send_comment_notification_via_email(recipients, email_details)
        delivery_successful = delivery_result.get("success", False)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "comment_id": str(comment_id),
            "mentioned_user_id": str(mentioned_user_id),
            "notification_type": "comment_mention",
            "status": "sent" if delivery_successful else "failed",
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "processing_time_ms": processing_time_ms,
        }

        if delivery_successful:
            logger.info(
                f"Comment mention notification sent successfully: comment_id={comment_id}, "
                f"mentioned_user={mentioned_user_id}, "
                f"time: {processing_time_ms}ms"
            )
        else:
            logger.warning(
                f"Comment mention notification delivery failed: comment_id={comment_id}, "
                f"error: {delivery_result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "comment_id": str(comment_id),
            "mentioned_user_id": str(mentioned_user_id),
            "notification_type": "comment_mention",
            "status": "failed",
            "error": "Notification sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in comment mention notification: {e}", exc_info=True)
        return {
            "comment_id": str(comment_id),
            "mentioned_user_id": str(mentioned_user_id),
            "notification_type": "comment_mention",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.comment_notifications.send_comment_reply_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_comment_reply_notification(
    self,
    comment_id: UUID,
    parent_comment_id: UUID,
    parent_author_id: UUID,
    parent_author_email: str,
    comment_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send notification when someone replies to a user's comment.

    This Celery task handles sending email notifications when someone replies
    to a user's comment. It formats the notification with reply content and
    thread context.

    Task Workflow:
    1. Format notification email with reply details
    2. Send notification to the original comment author
    3. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        comment_id: UUID of the reply comment
        parent_comment_id: UUID of the parent comment being replied to
        parent_author_id: UUID of the original comment author
        parent_author_email: Email address of the original comment author
        comment_details: Dictionary containing reply information:
            - content: Reply content text
            - author_name: Name of the reply author
            - author_email: Email of the reply author
            - resume_id: UUID of the candidate resume
            - candidate_name: Name of the candidate being discussed
            - created_at: Timestamp when reply was created

    Returns:
        Dictionary containing notification results:
        - comment_id: UUID of the reply comment
        - parent_comment_id: UUID of the parent comment
        - parent_author_id: UUID of the original author
        - notification_type: Type of notification (comment_reply)
        - status: Task status (sent/failed)
        - delivery_successful: Whether delivery was successful
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For email sending errors

    Example:
        >>> from tasks.comment_notifications import send_comment_reply_notification
        >>> from uuid import uuid4
        >>> details = {"content": "I agree!", "author_name": "Jane"}
        >>> task = send_comment_reply_notification.delay(
        ...     uuid4(), uuid4(), uuid4(), "user@example.com", details
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Sending comment reply notification for comment: {comment_id}, "
            f"parent comment: {parent_comment_id}"
        )

        # Step 1: Format notification email
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_notification",
            "message": "Formatting reply notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Formatting reply notification email")

        email_details = format_comment_reply_email(comment_details)

        # Step 2: Send notification to original comment author
        recipients = [parent_author_email]

        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_notification",
            "message": "Sending reply notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending reply notification email")

        delivery_result = send_comment_notification_via_email(recipients, email_details)
        delivery_successful = delivery_result.get("success", False)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "comment_id": str(comment_id),
            "parent_comment_id": str(parent_comment_id),
            "parent_author_id": str(parent_author_id),
            "notification_type": "comment_reply",
            "status": "sent" if delivery_successful else "failed",
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "processing_time_ms": processing_time_ms,
        }

        if delivery_successful:
            logger.info(
                f"Comment reply notification sent successfully: comment_id={comment_id}, "
                f"parent_author={parent_author_id}, "
                f"time: {processing_time_ms}ms"
            )
        else:
            logger.warning(
                f"Comment reply notification delivery failed: comment_id={comment_id}, "
                f"error: {delivery_result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "comment_id": str(comment_id),
            "parent_comment_id": str(parent_comment_id),
            "parent_author_id": str(parent_author_id),
            "notification_type": "comment_reply",
            "status": "failed",
            "error": "Notification sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in comment reply notification: {e}", exc_info=True)
        return {
            "comment_id": str(comment_id),
            "parent_comment_id": str(parent_comment_id),
            "parent_author_id": str(parent_author_id),
            "notification_type": "comment_reply",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }
