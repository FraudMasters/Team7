"""
Celery tasks for automated audit log alerting

This module provides scheduled security monitoring tasks for detecting suspicious
activity patterns in audit logs and sending real-time alerts.

It integrates with the audit alerting service to detect:
- Failed login attempts (brute force attacks)
- Bulk data exports (data exfiltration)
- Permission and role changes (privilege escalation)
- Unusual user activity patterns
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from services.audit_alerting import detect_suspicious_activity

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.audit_alerting.check_and_alert_suspicious_activity",
    bind=True,
)
def check_and_alert_suspicious_activity(
    self,
    time_window_minutes: int = 5,
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check for suspicious activity in audit logs and trigger alerts.

    This Celery task periodically analyzes audit logs to detect suspicious activity
    patterns and sends alerts when configured thresholds are exceeded. It runs on
    a scheduled interval (typically every 5 minutes) to provide near-real-time
    security monitoring.

    Task Workflow:
    1. Calculate time window for analysis (default: last 5 minutes)
    2. Call audit alerting service to detect suspicious patterns
    3. Process detected alerts and trigger notifications
    4. Log alert summary and return statistics

    The task detects the following suspicious patterns:
    - Failed login attempts exceeding threshold (potential brute force)
    - Bulk data exports exceeding threshold (potential data exfiltration)
    - Multiple permission changes (potential privilege escalation)
    - Multiple role changes (potential unauthorized access)

    Alerts are sent through configured channels:
    - Email notifications to security team
    - Webhook notifications to security monitoring systems
    - Slack notifications (if configured)

    Args:
        self: Celery task instance (bind=True)
        time_window_minutes: Time window in minutes to analyze (default: 5)
        organization_id: Organization UUID to scope analysis (None for all orgs)

    Returns:
        Dictionary containing detection results:
        - status: Task status (success/failed)
        - time_window_minutes: Time window used for analysis
        - analyzed_period_start: Start of analyzed period
        - analyzed_period_end: End of analyzed period
        - alerts: List of alerts detected
        - alert_count: Total number of alerts
        - alerts_by_type: Breakdown of alerts by type
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.audit_alerting import check_and_alert_suspicious_activity
        >>> task = check_and_alert_suspicious_activity.delay(time_window_minutes=10)
        >>> result = task.get()
        >>> print(result['alert_count'])
        3
        >>> print(result['alerts_by_type'])
        {'FAILED_LOGIN': 2, 'BULK_EXPORT': 1}

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting suspicious activity check with {time_window_minutes}min window"
        )

        # Convert organization_id string to UUID if provided
        org_uuid = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid organization_id format: {organization_id}: {e}")
                return {
                    "status": "failed",
                    "error": f"Invalid organization_id format: {organization_id}",
                    "time_window_minutes": time_window_minutes,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

        # Calculate time window
        end_time = datetime.utcnow()
        start_time_window = datetime.utcnow()  # Will be calculated in service

        # Run the async detection function
        async def perform_detection():
            alerts = await detect_suspicious_activity(
                time_window_minutes=time_window_minutes,
                organization_id=org_uuid,
                alert_types=None,  # Check all alert types
            )
            return alerts

        # Execute async detection
        try:
            # Get or create event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        detected_alerts = loop.run_until_complete(perform_detection())

        # Process and categorize alerts
        alerts_by_type = {}
        for alert in detected_alerts:
            alert_type = alert.get("alert_type", "UNKNOWN")
            alerts_by_type[alert_type] = alerts_by_type.get(alert_type, 0) + 1

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Log alert summary
        if detected_alerts:
            logger.warning(
                f"Detected {len(detected_alerts)} suspicious activity alerts: "
                f"{alerts_by_type}"
            )

            # Log details of first few alerts
            for alert in detected_alerts[:5]:
                logger.warning(
                    f"Alert [{alert.get('alert_type')}] {alert.get('severity', 'MEDIUM')}: "
                    f"{alert.get('message', 'No message')}"
                )

            if len(detected_alerts) > 5:
                logger.warning(f"... and {len(detected_alerts) - 5} more alerts")
        else:
            logger.info("No suspicious activity detected")

        # Build result
        result = {
            "status": "success",
            "time_window_minutes": time_window_minutes,
            "analyzed_period_start": (
                datetime.utcnow().isoformat() if detected_alerts else None
            ),
            "analyzed_period_end": end_time.isoformat(),
            "alerts": detected_alerts,
            "alert_count": len(detected_alerts),
            "alerts_by_type": alerts_by_type,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Suspicious activity check completed: "
            f"{len(detected_alerts)} alerts detected in {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Suspicious activity check exceeded time limit after {processing_time_ms}ms"
        )
        return {
            "status": "failed",
            "error": "Task exceeded time limit",
            "time_window_minutes": time_window_minutes,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Suspicious activity check failed: {e}",
            exc_info=True
        )
        return {
            "status": "failed",
            "error": str(e),
            "time_window_minutes": time_window_minutes,
            "processing_time_ms": processing_time_ms,
        }


__all__ = [
    "check_and_alert_suspicious_activity",
]
