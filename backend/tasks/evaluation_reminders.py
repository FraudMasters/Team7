"""
Evaluation reminder tasks for sending scorecard completion notifications.

This module provides Celery tasks for sending reminders to evaluators
who have incomplete scorecards, ensuring timely completion of candidate
evaluations.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def format_scorecard_reminder_email(
    evaluator_name: str,
    candidate_name: str,
    template_name: str,
    scorecard_id: str,
    days_pending: int,
    criteria_count: int,
) -> Dict[str, Any]:
    """
    Format scorecard reminder email.

    This function formats an email notification to remind evaluators
    about incomplete scorecards that need their attention.

    Args:
        evaluator_name: Name of the evaluator
        candidate_name: Name of the candidate being evaluated
        template_name: Name of the evaluation template
        scorecard_id: UUID of the scorecard
        days_pending: Number of days the scorecard has been pending
        criteria_count: Number of criteria in the template

    Returns:
        Dictionary containing email details:
        {
            "subject": "Reminder: Complete your evaluation for John Doe",
            "body": "Email body with reminder details...",
            "priority": "normal"
        }

    Example:
        >>> email = format_scorecard_reminder_email(
        ...     "Jane Smith", "John Doe", "Technical Interview",
        ...     "scorecard-123", 3, 5
        ... )
        >>> print(email['subject'])
        'Reminder: Complete your evaluation for John Doe'
    """
    try:
        logger.info(
            f"Formatting scorecard reminder email for evaluator: {evaluator_name}, "
            f"candidate: {candidate_name}"
        )

        # Build email subject
        urgency_indicator = "⏰ " if days_pending > 5 else ""
        subject = f"{urgency_indicator}Reminder: Complete your evaluation for {candidate_name}"

        # Build email body
        body_lines = [
            f"Dear {evaluator_name},",
            f"",
            f"This is a friendly reminder to complete your evaluation scorecard for:",
            f"",
            f"Candidate: {candidate_name}",
            f"Evaluation Template: {template_name}",
            f"Scorecard ID: {scorecard_id}",
            f"",
        ]

        # Add urgency message based on days pending
        if days_pending == 0:
            body_lines.append("This evaluation was just assigned to you.")
        elif days_pending == 1:
            body_lines.append("This evaluation was assigned yesterday.")
        elif days_pending <= 3:
            body_lines.append(f"This evaluation has been pending for {days_pending} days.")
        elif days_pending <= 7:
            body_lines.append(
                f"⚠️ This evaluation has been pending for {days_pending} days. "
                f"Please complete it soon."
            )
        else:
            body_lines.append(
                f"⚠️ URGENT: This evaluation has been pending for {days_pending} days. "
                f"Your immediate attention is required."
            )

        body_lines.extend([
            f"",
            f"Evaluation Details:",
            f"  - Number of criteria to evaluate: {criteria_count}",
            f"  - Estimated completion time: {criteria_count * 2} minutes",
            f"",
            f"Please log in to the AgentHR system to complete this evaluation.",
            f"",
            f"---",
            f"This is an automated reminder from the AgentHR Evaluation System.",
            f"If you have already completed this evaluation, please disregard this message.",
        ])

        body = "\n".join(body_lines)

        # Determine priority based on urgency
        if days_pending > 5:
            priority = "high"
        elif days_pending > 3:
            priority = "normal"
        else:
            priority = "low"

        email_details = {
            "subject": subject,
            "body": body,
            "priority": priority,
        }

        logger.info(f"Scorecard reminder email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format scorecard reminder email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Reminder: Complete your evaluation for {candidate_name}",
            "body": f"Please complete your evaluation scorecard (ID: {scorecard_id}) for {candidate_name}.",
            "priority": "normal",
        }


def send_notification_via_email(
    recipients: List[str],
    email_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send notification via email to specified recipients.

    This function sends a notification email using the configured email service.
    In production, this would integrate with SMTP, SendGrid, AWS SES, or similar.

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
        >>> result = send_notification_via_email(["admin@example.com"], details)
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
        subject = email_details.get("subject", "Notification")
        body = email_details.get("body", "")
        priority = email_details.get("priority", "normal")

        logger.info(
            f"Sending notification email: subject='{subject}', "
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

        logger.info(f"Notification email sent successfully to {len(recipients)} recipients")

        return {
            "success": success,
            "recipients_count": len(recipients),
            "error": error,
        }

    except Exception as e:
        logger.error(f"Failed to send notification email: {e}", exc_info=True)
        return {
            "success": False,
            "recipients_count": len(recipients),
            "error": str(e),
        }


@shared_task(
    name="tasks.send_scorecard_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_scorecard_reminders(
    self,
    scorecard_ids: Optional[List[str]] = None,
    evaluator_ids: Optional[List[str]] = None,
    days_threshold: int = 3,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Send scorecard completion reminders to evaluators.

    This Celery task identifies incomplete scorecards and sends reminder
    emails to the assigned evaluators. It can filter by specific scorecards,
    evaluators, or a threshold of days pending.

    Task Workflow:
    1. Query database for incomplete scorecards
    2. Filter by days threshold and optional filters
    3. Format reminder emails for each evaluator
    4. Send reminder notifications
    5. Return delivery status summary

    Args:
        self: Celery task instance (bind=True)
        scorecard_ids: Optional list of specific scorecard IDs to remind
        evaluator_ids: Optional list of specific evaluator IDs to remind
        days_threshold: Only remind if pending >= this many days (default: 3)
        dry_run: If True, don't send emails, just report what would be sent

    Returns:
        Dictionary containing reminder results:
        - scorecards_reminded: Number of scorecards reminded
        - evaluators_notified: Number of evaluators notified
        - emails_sent: Number of emails sent
        - emails_failed: Number of emails that failed to send
        - dry_run: Whether this was a dry run
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed)
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or email sending errors

    Example:
        >>> from tasks.evaluation_reminders import send_scorecard_reminders
        >>> task = send_scorecard_reminders.delay(days_threshold=5)
        >>> result = task.get()
        >>> print(result['scorecards_reminded'])
        12
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting scorecard reminder task: days_threshold={days_threshold}, "
            f"dry_run={dry_run}"
        )

        # Note: In a real implementation, you would get db_session here
        # from database import get_db_session
        # db_session = get_db_session()

        # Placeholder: Simulate querying incomplete scorecards
        # In production, you would query:
        # SELECT s.*, r.candidate_name, et.name as template_name,
        #        r.email as evaluator_email, r.name as evaluator_name
        # FROM evaluation_scorecards s
        # JOIN resumes ON s.resume_id = resumes.id
        # JOIN evaluation_templates et ON s.template_id = et.id
        # LEFT JOIN recruiters r ON s.evaluator_id = r.id
        # WHERE s.status IN ('draft', 'in_progress')
        #   AND s.created_at < NOW() - INTERVAL '{days_threshold} days'
        #   (AND s.id IN scorecard_ids IF provided)
        #   (AND s.evaluator_id IN evaluator_ids IF provided)

        # Simulate database query results
        incomplete_scorecards = []

        if scorecard_ids:
            logger.info(f"Filtering by {len(scorecard_ids)} specific scorecard IDs")
            # In production: WHERE s.id IN (scorecard_ids)

        if evaluator_ids:
            logger.info(f"Filtering by {len(evaluator_ids)} specific evaluator IDs")
            # In production: WHERE s.evaluator_id IN (evaluator_ids)

        # Placeholder data - replace with actual database query results
        if not dry_run:
            # Simulate finding some incomplete scorecards
            incomplete_scorecards = [
                {
                    "scorecard_id": "scorecard-1",
                    "evaluator_id": "evaluator-1",
                    "evaluator_name": "Jane Smith",
                    "evaluator_email": "jane.smith@example.com",
                    "candidate_name": "John Doe",
                    "template_name": "Technical Interview",
                    "created_at": datetime.utcnow() - timedelta(days=5),
                    "status": "in_progress",
                    "criteria_count": 5,
                },
                {
                    "scorecard_id": "scorecard-2",
                    "evaluator_id": "evaluator-2",
                    "evaluator_name": "Bob Johnson",
                    "evaluator_email": "bob.johnson@example.com",
                    "candidate_name": "Alice Williams",
                    "template_name": "Cultural Fit Assessment",
                    "created_at": datetime.utcnow() - timedelta(days=7),
                    "status": "draft",
                    "criteria_count": 3,
                },
            ]

        logger.info(f"Found {len(incomplete_scorecards)} incomplete scorecards to remind")

        emails_sent = 0
        emails_failed = 0
        evaluators_notified = set()
        scorecards_reminded = 0

        # Process each incomplete scorecard
        for scorecard in incomplete_scorecards:
            try:
                scorecard_id = scorecard["scorecard_id"]
                evaluator_email = scorecard.get("evaluator_email")
                evaluator_name = scorecard.get("evaluator_name", "Evaluator")
                candidate_name = scorecard["candidate_name"]
                template_name = scorecard["template_name"]
                created_at = scorecard["created_at"]
                criteria_count = scorecard.get("criteria_count", 0)

                # Calculate days pending
                days_pending = (datetime.utcnow() - created_at).days

                logger.info(
                    f"Processing scorecard {scorecard_id}: "
                    f"candidate={candidate_name}, evaluator={evaluator_name}, "
                    f"days_pending={days_pending}"
                )

                # Format reminder email
                email_details = format_scorecard_reminder_email(
                    evaluator_name=evaluator_name,
                    candidate_name=candidate_name,
                    template_name=template_name,
                    scorecard_id=scorecard_id,
                    days_pending=days_pending,
                    criteria_count=criteria_count,
                )

                # Send email (or log if dry run)
                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would send reminder to {evaluator_email}: "
                        f"subject='{email_details['subject']}'"
                    )
                    emails_sent += 1
                elif evaluator_email:
                    delivery_result = send_notification_via_email(
                        [evaluator_email],
                        email_details,
                    )
                    if delivery_result.get("success"):
                        emails_sent += 1
                    else:
                        emails_failed += 1
                        logger.error(
                            f"Failed to send reminder to {evaluator_email}: "
                            f"{delivery_result.get('error')}"
                        )
                else:
                    logger.warning(f"No email address for evaluator {evaluator_name}")
                    emails_failed += 1

                # Track statistics
                evaluators_notified.add(scorecard["evaluator_id"])
                scorecards_reminded += 1

                # Update progress
                progress = {
                    "current": scorecards_reminded,
                    "total": len(incomplete_scorecards),
                    "percentage": int(scorecards_reminded / len(incomplete_scorecards) * 100)
                    if incomplete_scorecards else 100,
                    "status": "sending_reminders",
                    "emails_sent": emails_sent,
                    "emails_failed": emails_failed,
                }
                self.update_state(state="PROGRESS", meta=progress)

            except Exception as e:
                logger.error(
                    f"Error processing scorecard {scorecard.get('scorecard_id')}: {e}",
                    exc_info=True,
                )
                emails_failed += 1
                continue

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "scorecards_reminded": scorecards_reminded,
            "evaluators_notified": len(evaluators_notified),
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "dry_run": dry_run,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Scorecard reminder task completed: {scorecards_reminded} scorecards, "
            f"{len(evaluators_notified)} evaluators notified, "
            f"{emails_sent} emails sent, {emails_failed} failed, "
            f"time: {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "scorecards_reminded": scorecards_reminded,
            "evaluators_notified": len(evaluators_notified) if evaluators_notified else 0,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed + 1,
            "dry_run": dry_run,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": "Task exceeded maximum time limit",
        }

    except Exception as e:
        logger.error(f"Error in scorecard reminder task: {e}", exc_info=True)
        return {
            "scorecards_reminded": scorecards_reminded if scorecards_reminded else 0,
            "evaluators_notified": len(evaluators_notified) if evaluators_notified else 0,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "dry_run": dry_run,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }
