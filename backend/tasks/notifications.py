"""
Notification tasks for model retraining and performance monitoring events.

This module provides Celery tasks for sending email notifications about
model retraining events, performance degradation alerts, and training
completion notifications.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def format_retraining_notification_email(
    model_name: str,
    training_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format model retraining notification email.

    This function formats an email notification for model retraining events,
    including training results, performance metrics, and deployment status.

    Args:
        model_name: Name of the model that was retrained
        training_result: Training result dictionary containing:
            - status: Training status (success/failed)
            - new_version_id: ID of the new model version
            - previous_version_id: ID of the previous model version
            - metrics: Performance metrics (accuracy, precision, recall, f1_score)
            - training_samples: Number of samples used for training
            - training_duration_ms: Training duration in milliseconds
            - activated: Whether the new model was activated
            - error: Error message (if training failed)

    Returns:
        Dictionary containing email details:
        {
            "subject": "Model Retraining Completed: ranking",
            "body": "Email body with training results...",
            "recipients": ["admin@example.com"],
            "priority": "high"
        }

    Example:
        >>> result = {"status": "success", "metrics": {"accuracy": 0.92}}
        >>> email = format_retraining_notification_email("ranking", result)
        >>> print(email['subject'])
        'Model Retraining Completed: ranking'
    """
    try:
        logger.info(f"Formatting retraining notification email for model: {model_name}")

        status = training_result.get("status", "unknown")
        new_version_id = training_result.get("new_version_id")
        previous_version_id = training_result.get("previous_version_id")
        metrics = training_result.get("metrics", {})
        activated = training_result.get("activated", False)

        # Determine email subject based on status
        if status == "success":
            subject = f"Model Retraining Completed: {model_name}"
            status_emoji = "✅"
        elif status == "failed":
            subject = f"Model Retraining Failed: {model_name}"
            status_emoji = "❌"
        else:
            subject = f"Model Retraining Update: {model_name}"
            status_emoji = "ℹ️"

        # Build email body
        body_lines = [
            f"Model Retraining Notification",
            f"",
            f"Model: {model_name}",
            f"Status: {status_emoji} {status.upper()}",
            f"Timestamp: {datetime.utcnow().isoformat()}",
        ]

        if status == "success":
            body_lines.extend([
                f"",
                f"New Version ID: {new_version_id}",
                f"Previous Version ID: {previous_version_id}",
            ])

            if metrics:
                body_lines.extend([
                    f"",
                    f"Performance Metrics:",
                ])
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, float):
                        body_lines.append(f"  - {metric_name}: {metric_value:.4f}")
                    else:
                        body_lines.append(f"  - {metric_name}: {metric_value}")

            training_samples = training_result.get("training_samples")
            if training_samples:
                body_lines.append(f"Training Samples: {training_samples:,}")

            training_duration = training_result.get("training_duration_ms")
            if training_duration:
                duration_seconds = training_duration / 1000
                body_lines.append(f"Training Duration: {duration_seconds:.2f} seconds")

            activation_status = "Activated" if activated else "Not Activated (requires manual approval)"
            body_lines.extend([
                f"",
                f"Deployment Status: {activation_status}",
            ])

        elif status == "failed":
            error = training_result.get("error", "Unknown error")
            body_lines.extend([
                f"",
                f"Error Details:",
                f"  {error}",
            ])

        body_lines.extend([
            f"",
            f"---",
            f"This is an automated notification from AgentHR Model Training System.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "high" if status == "failed" else "normal",
        }

        logger.info(f"Retraining notification email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format retraining notification email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Model Retraining Notification: {model_name}",
            "body": f"An error occurred while formatting the notification. Status: {training_result.get('status')}",
            "priority": "normal",
        }


def format_performance_degradation_email(
    model_name: str,
    degradation_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format performance degradation alert email.

    This function formats an email notification for performance degradation
    alerts, including current vs baseline metrics and degradation percentage.

    Args:
        model_name: Name of the model with performance degradation
        degradation_details: Degradation details dictionary containing:
            - current_metrics: Current performance metrics
            - baseline_metrics: Baseline performance metrics
            - degradation_percentage: Percentage of degradation
            - threshold: Threshold that was exceeded
            - detected_at: Timestamp when degradation was detected

    Returns:
        Dictionary containing email details:
        {
            "subject": "Performance Degradation Alert: ranking",
            "body": "Email body with degradation details...",
            "priority": "high"
        }

    Example:
        >>> details = {"degradation_percentage": 0.08, "threshold": 0.05}
        >>> email = format_performance_degradation_email("ranking", details)
        >>> print(email['subject'])
        'Performance Degradation Alert: ranking'
    """
    try:
        logger.info(f"Formatting performance degradation alert email for model: {model_name}")

        current_metrics = degradation_details.get("current_metrics", {})
        baseline_metrics = degradation_details.get("baseline_metrics", {})
        degradation_percentage = degradation_details.get("degradation_percentage", 0)
        threshold = degradation_details.get("threshold", 0)
        detected_at = degradation_details.get("detected_at", datetime.utcnow().isoformat())

        # Build email subject
        degradation_pct_str = f"{degradation_percentage * 100:.1f}%"
        subject = f"⚠️ Performance Degradation Alert: {model_name} ({degradation_pct_str} drop)"

        # Build email body
        body_lines = [
            f"Performance Degradation Alert",
            f"",
            f"Model: {model_name}",
            f"Detected At: {detected_at}",
            f"",
            f"Degradation Summary:",
            f"  Degradation: {degradation_pct_str}",
            f"  Threshold Exceeded: {threshold * 100:.1f}%",
        ]

        if baseline_metrics and current_metrics:
            body_lines.extend([
                f"",
                f"Metrics Comparison:",
            ])

            # Compare key metrics
            for metric_name in ["accuracy", "precision", "recall", "f1_score"]:
                if metric_name in baseline_metrics and metric_name in current_metrics:
                    baseline_value = baseline_metrics[metric_name]
                    current_value = current_metrics[metric_name]
                    delta = baseline_value - current_value
                    delta_pct = (delta / baseline_value * 100) if baseline_value > 0 else 0

                    delta_str = f"({delta_pct:+.1f}%)"
                    indicator = "⬇️" if delta > 0 else "➡️"
                    body_lines.append(
                        f"  {indicator} {metric_name}: {current_value:.4f} vs {baseline_value:.4f} {delta_str}"
                    )

        body_lines.extend([
            f"",
            f"Recommendation:",
            f"  Consider triggering model retraining to address performance degradation.",
            f"",
            f"---",
            f"This is an automated alert from AgentHR Performance Monitoring System.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "high",
        }

        logger.info(f"Performance degradation alert email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format performance degradation email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Performance Alert: {model_name}",
            "body": f"Performance degradation detected. Threshold exceeded by {degradation_details.get('degradation_percentage', 0) * 100:.1f}%",
            "priority": "high",
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
    name="tasks.notifications.send_model_retraining_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_model_retraining_notification(
    self,
    model_name: str,
    training_result: Dict[str, Any],
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send notification about model retraining completion.

    This Celery task handles sending email notifications when model retraining
    completes, whether successful or failed. It formats the notification with
    training results, performance metrics, and deployment status.

    Task Workflow:
    1. Format notification email with training results
    2. Determine recipients (default: admin emails from settings)
    3. Send notification via email
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model that was retrained
        training_result: Training result dictionary from retraining task
        recipients: Optional list of email recipients (defaults to admin emails)

    Returns:
        Dictionary containing notification results:
        - model_name: Name of the model
        - notification_type: Type of notification (retraining_completion)
        - status: Task status (sent/failed)
        - recipients_count: Number of recipients notified
        - delivery_successful: Whether delivery was successful
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For email sending errors

    Example:
        >>> from tasks.notifications import send_model_retraining_notification
        >>> result = {"status": "success", "metrics": {"accuracy": 0.92}}
        >>> task = send_model_retraining_notification.delay("ranking", result)
        >>> notification_result = task.get()
        >>> print(notification_result['status'])
        'sent'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Sending model retraining notification for: {model_name}, "
            f"training status: {training_result.get('status')}"
        )

        # Step 1: Format notification email
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_notification",
            "message": "Formatting notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Formatting notification email")

        email_details = format_retraining_notification_email(model_name, training_result)

        # Step 2: Determine recipients
        if not recipients:
            # Default to admin emails from settings
            recipients = getattr(settings, 'admin_email_addresses', ['admin@agenthr.com'])
        elif isinstance(recipients, str):
            recipients = [recipients]

        logger.info(f"Recipients: {len(recipients)} email addresses")

        # Step 3: Send notification
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_notification",
            "message": "Sending notification email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending notification email")

        delivery_result = send_notification_via_email(recipients, email_details)
        delivery_successful = delivery_result.get("success", False)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "model_name": model_name,
            "notification_type": "retraining_completion",
            "status": "sent" if delivery_successful else "failed",
            "recipients_count": len(recipients),
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "processing_time_ms": processing_time_ms,
        }

        if delivery_successful:
            logger.info(
                f"Model retraining notification sent successfully: {model_name}, "
                f"delivered to {len(recipients)} recipients, "
                f"time: {processing_time_ms}ms"
            )
        else:
            logger.warning(
                f"Model retraining notification delivery failed: {model_name}, "
                f"error: {delivery_result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "model_name": model_name,
            "notification_type": "retraining_completion",
            "status": "failed",
            "error": "Notification sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in model retraining notification: {e}", exc_info=True)
        return {
            "model_name": model_name,
            "notification_type": "retraining_completion",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.notifications.send_performance_degradation_alert",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_performance_degradation_alert(
    self,
    model_name: str,
    degradation_details: Dict[str, Any],
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send alert about performance degradation.

    This Celery task handles sending email alerts when model performance
    degradation is detected. It formats the alert with current vs baseline
    metrics and the degradation percentage.

    Task Workflow:
    1. Format alert email with degradation details
    2. Determine recipients (default: admin emails from settings)
    3. Send alert via email
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model with performance degradation
        degradation_details: Degradation details dictionary containing metrics
        recipients: Optional list of email recipients (defaults to admin emails)

    Returns:
        Dictionary containing alert results:
        - model_name: Name of the model
        - notification_type: Type of notification (performance_degradation)
        - status: Task status (sent/failed)
        - recipients_count: Number of recipients notified
        - delivery_successful: Whether delivery was successful
        - degradation_percentage: Percentage of degradation
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For email sending errors

    Example:
        >>> from tasks.notifications import send_performance_degradation_alert
        >>> details = {"degradation_percentage": 0.08, "threshold": 0.05}
        >>> task = send_performance_degradation_alert.delay("ranking", details)
        >>> alert_result = task.get()
        >>> print(alert_result['status'])
        'sent'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Sending performance degradation alert for: {model_name}, "
            f"degradation: {degradation_details.get('degradation_percentage', 0) * 100:.1f}%"
        )

        # Step 1: Format alert email
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_alert",
            "message": "Formatting alert email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Formatting alert email")

        email_details = format_performance_degradation_email(model_name, degradation_details)

        # Step 2: Determine recipients
        if not recipients:
            # Default to admin emails from settings
            recipients = getattr(settings, 'admin_email_addresses', ['admin@agenthr.com'])
        elif isinstance(recipients, str):
            recipients = [recipients]

        logger.info(f"Recipients: {len(recipients)} email addresses")

        # Step 3: Send alert
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_alert",
            "message": "Sending alert email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending alert email")

        delivery_result = send_notification_via_email(recipients, email_details)
        delivery_successful = delivery_result.get("success", False)

        degradation_percentage = degradation_details.get("degradation_percentage", 0)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "model_name": model_name,
            "notification_type": "performance_degradation",
            "status": "sent" if delivery_successful else "failed",
            "recipients_count": len(recipients),
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "degradation_percentage": degradation_percentage,
            "processing_time_ms": processing_time_ms,
        }

        if delivery_successful:
            logger.info(
                f"Performance degradation alert sent successfully: {model_name}, "
                f"degradation: {degradation_percentage * 100:.1f}%, "
                f"delivered to {len(recipients)} recipients, "
                f"time: {processing_time_ms}ms"
            )
        else:
            logger.warning(
                f"Performance degradation alert delivery failed: {model_name}, "
                f"error: {delivery_result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "model_name": model_name,
            "notification_type": "performance_degradation",
            "status": "failed",
            "error": "Alert sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in performance degradation alert: {e}", exc_info=True)
        return {
            "model_name": model_name,
            "notification_type": "performance_degradation",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.notifications.send_follow_up_reminders",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_follow_up_reminders(
    self,
    look_ahead_hours: int = 24,
) -> Dict[str, Any]:
    """
    Send follow-up reminder notifications to recruiters.

    This Celery task queries for upcoming follow-ups scheduled within the
    specified time window and sends reminder notifications to the assigned
    recruiters. It helps ensure timely follow-up actions with candidates.

    Task Workflow:
    1. Query communications with upcoming follow-ups within look_ahead_hours
    2. Group follow-ups by recruiter
    3. Format reminder email for each recruiter with their follow-up list
    4. Send reminder notifications via email
    5. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        look_ahead_hours: Number of hours to look ahead for follow-ups (default: 24)

    Returns:
        Dictionary containing reminder results:
        - notification_type: Type of notification (follow_up_reminders)
        - status: Task status (sent/failed/partial)
        - recruiters_notified: Number of recruiters notified
        - total_followups: Total number of upcoming follow-ups found
        - recipients_count: Total number of email recipients
        - delivery_successful: Whether all deliveries were successful
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or email sending errors

    Example:
        >>> from tasks.notifications import send_follow_up_reminders
        >>> task = send_follow_up_reminders.delay(look_ahead_hours=24)
        >>> result = task.get()
        >>> print(result['total_followups'])
        15
    """
    import asyncio
    from datetime import timedelta

    start_time = time.time()

    try:
        logger.info(
            f"Sending follow-up reminders: looking ahead {look_ahead_hours} hours"
        )

        # Step 1: Query upcoming follow-ups
        progress = {
            "current": 1,
            "total": 3,
            "percentage": 33,
            "status": "querying_followups",
            "message": "Querying upcoming follow-ups...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Querying upcoming follow-ups")

        # Note: This is a placeholder for database query
        # In a real implementation, you would:
        # 1. Query Communications table with status='pending' or status='sent'
        # 2. Filter by metadata.followup_date within the look_ahead_hours window
        # 3. Group by recruiter_id
        # 4. Include candidate_name, vacancy_title, communication_type, followup_date

        # Placeholder data - replace with actual database queries
        upcoming_followups_by_recruiter = {
            "recruiter1@example.com": [
                {
                    "communication_id": "uuid-1",
                    "candidate_name": "John Doe",
                    "candidate_id": "candidate-uuid-1",
                    "vacancy_title": "Senior Software Engineer",
                    "communication_type": "email",
                    "subject": "Interview follow-up",
                    "followup_date": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                    "priority": "high",
                },
                {
                    "communication_id": "uuid-2",
                    "candidate_name": "Jane Smith",
                    "candidate_id": "candidate-uuid-2",
                    "vacancy_title": "Product Manager",
                    "communication_type": "phone_call",
                    "subject": "Technical discussion follow-up",
                    "followup_date": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                    "priority": "medium",
                },
            ],
            "recruiter2@example.com": [
                {
                    "communication_id": "uuid-3",
                    "candidate_name": "Bob Johnson",
                    "candidate_id": "candidate-uuid-3",
                    "vacancy_title": "Data Analyst",
                    "communication_type": "email",
                    "subject": "Salary negotiation follow-up",
                    "followup_date": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                    "priority": "high",
                },
            ],
        }

        total_followups = sum(
            len(followups)
            for followups in upcoming_followups_by_recruiter.values()
        )
        recruiters_to_notify = len(upcoming_followups_by_recruiter)

        logger.info(
            f"Found {total_followups} upcoming follow-ups for {recruiters_to_notify} recruiters"
        )

        # Step 2: Send reminders to each recruiter
        progress = {
            "current": 2,
            "total": 3,
            "percentage": 66,
            "status": "sending_reminders",
            "message": f"Sending reminders to {recruiters_to_notify} recruiters...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending reminder emails")

        successful_deliveries = 0
        failed_deliveries = 0

        for recruiter_email, followups in upcoming_followups_by_recruiter.items():
            try:
                # Format reminder email for this recruiter
                email_details = format_follow_up_reminder_email(recruiter_email, followups, look_ahead_hours)

                # Send reminder email
                delivery_result = send_notification_via_email([recruiter_email], email_details)
                delivery_successful = delivery_result.get("success", False)

                if delivery_successful:
                    successful_deliveries += 1
                    logger.info(
                        f"Follow-up reminder sent successfully to {recruiter_email} "
                        f"({len(followups)} follow-ups)"
                    )
                else:
                    failed_deliveries += 1
                    logger.warning(
                        f"Failed to send follow-up reminder to {recruiter_email}: "
                        f"{delivery_result.get('error')}"
                    )

            except Exception as e:
                failed_deliveries += 1
                logger.error(
                    f"Error sending follow-up reminder to {recruiter_email}: {e}",
                    exc_info=True
                )

        # Step 3: Return results
        progress = {
            "current": 3,
            "total": 3,
            "percentage": 100,
            "status": "completed",
            "message": "Follow-up reminders processed",
        }
        self.update_state(state="PROGRESS", meta=progress)

        delivery_successful = failed_deliveries == 0
        status = "sent" if delivery_successful else ("partial" if successful_deliveries > 0 else "failed")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "notification_type": "follow_up_reminders",
            "status": status,
            "recruiters_notified": successful_deliveries,
            "recruiters_failed": failed_deliveries,
            "total_followups": total_followups,
            "recipients_count": recruiters_to_notify,
            "delivery_successful": delivery_successful,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Follow-up reminder notifications completed: "
            f"{successful_deliveries} sent, {failed_deliveries} failed, "
            f"{total_followups} follow-ups, time: {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "notification_type": "follow_up_reminders",
            "status": "failed",
            "error": "Follow-up reminder sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in follow-up reminder notifications: {e}", exc_info=True)
        return {
            "notification_type": "follow_up_reminders",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def format_follow_up_reminder_email(
    recruiter_email: str,
    followups: List[Dict[str, Any]],
    look_ahead_hours: int,
) -> Dict[str, Any]:
    """
    Format follow-up reminder email for a recruiter.

    This function formats an email notification for upcoming follow-ups,
    including candidate details, communication type, and follow-up dates.

    Args:
        recruiter_email: Email address of the recruiter
        followups: List of follow-up dictionaries containing:
            - candidate_name: Name of the candidate
            - vacancy_title: Position/title
            - communication_type: Type of communication (email, phone_call, sms)
            - subject: Communication subject
            - followup_date: When the follow-up is scheduled (ISO format)
            - priority: Priority level (high, medium, low)
        look_ahead_hours: Number of hours ahead being checked

    Returns:
        Dictionary containing email details:
        {
            "subject": "Follow-up Reminders: 3 upcoming actions",
            "body": "Email body with follow-up list...",
            "priority": "high"
        }

    Example:
        >>> followups = [{"candidate_name": "John Doe", "vacancy_title": "Engineer", ...}]
        >>> email = format_follow_up_reminder_email("recruiter@example.com", followups, 24)
        >>> print(email['subject'])
        'Follow-up Reminders: 1 upcoming action'
    """
    try:
        logger.info(
            f"Formatting follow-up reminder email for {recruiter_email}: "
            f"{len(followups)} follow-ups"
        )

        # Sort follow-ups by date and priority
        sorted_followups = sorted(
            followups,
            key=lambda f: (
                f.get("followup_date", ""),
                {"high": 0, "medium": 1, "low": 2}.get(f.get("priority", "low"), 2)
            )
        )

        # Determine email priority based on highest priority follow-up
        priority_map = {"high": "high", "medium": "normal", "low": "normal"}
        highest_priority = max(
            [f.get("priority", "low") for f in followups],
            key=lambda p: {"high": 2, "medium": 1, "low": 0}.get(p, 0)
        )
        email_priority = priority_map.get(highest_priority, "normal")

        # Build email subject
        subject = f"Follow-up Reminders: {len(followups)} upcoming action"
        if len(followups) > 1:
            subject += "s"
        if highest_priority == "high":
            subject += " 🔴"

        # Build email body
        body_lines = [
            f"Upcoming Follow-up Reminders",
            f"",
            f"You have {len(followups)} follow-up action"
            f"{'s' if len(followups) > 1 else ''} scheduled within the next {look_ahead_hours} hours.",
            f"",
            f"---",
        ]

        for idx, followup in enumerate(sorted_followups, start=1):
            candidate_name = followup.get("candidate_name", "Unknown Candidate")
            vacancy_title = followup.get("vacancy_title", "Unknown Position")
            comm_type = followup.get("communication_type", "communication").replace("_", " ").title()
            subject_line = followup.get("subject", "No subject")
            followup_date = followup.get("followup_date", "")
            priority = followup.get("priority", "low").upper()

            # Parse and format date
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(followup_date.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                date_str = followup_date

            # Priority indicator
            priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")

            body_lines.extend([
                f"",
                f"{idx}. {candidate_name} - {vacancy_title}",
                f"   Type: {comm_type}",
                f"   Subject: {subject_line}",
                f"   Follow-up: {date_str}",
                f"   Priority: {priority_emoji} {priority}",
            ])

        body_lines.extend([
            f"",
            f"---",
            f"Please ensure to complete these follow-ups on time to maintain candidate engagement.",
            f"",
            f"View all follow-ups in the Communications page.",
            f"",
            f"This is an automated reminder from AgentHR Communication System.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": email_priority,
        }

        logger.info(f"Follow-up reminder email formatted successfully for {recruiter_email}")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format follow-up reminder email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Follow-up Reminders: {len(followups)} upcoming",
            "body": f"You have {len(followups)} follow-up(s) scheduled. Check the Communications page for details.",
            "priority": "normal",
        }
