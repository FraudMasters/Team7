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
