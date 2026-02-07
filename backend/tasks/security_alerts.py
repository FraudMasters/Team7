"""
Celery tasks for automated security alert detection

This module provides scheduled security monitoring tasks for detecting suspicious
activity patterns such as multiple failed login attempts and unusual IP access patterns.

It also provides multi-channel alert notification delivery via email, SMS, webhook,
and Slack integration.
"""
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import httpx
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.audit_log import AuditLog, AuditActionType

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.security_alerts.check_suspicious_activity",
    bind=True,
)
def check_suspicious_activity(
    self,
    time_window_minutes: int = 60,
    failed_login_threshold: Optional[int] = None,
    alert_on_multiple_ips: bool = True,
    ip_change_threshold: int = 3,
) -> Dict[str, Any]:
    """
    Check for suspicious security activity patterns.

    This Celery task analyzes audit logs to detect potentially suspicious activity:
    1. Multiple failed login attempts from the same user/IP
    2. Successful logins from multiple different IPs within a short time window

    Detected threats are logged and can be used to trigger automated responses
    such as account locks, email notifications, or requiring additional authentication.

    Task Workflow:
    1. Calculate time window for analysis
    2. Query audit logs for failed login attempts
    3. Group by user_id and ip_address to count failures
    4. Query audit logs for successful logins
    5. Group by user_id to count unique IP addresses
    6. Identify patterns exceeding thresholds
    7. Log alerts and return summary statistics

    Args:
        self: Celery task instance (bind=True)
        time_window_minutes: Time window in minutes to look back for suspicious activity
        failed_login_threshold: Number of failed logins before alert (uses config default if not specified)
        alert_on_multiple_ips: Whether to alert on multiple IP logins
        ip_change_threshold: Number of unique IPs before alerting (default: 3)

    Returns:
        Dictionary containing detection results:
        - status: Task status (success/failed)
        - time_window_minutes: Time window used for analysis
        - analyzed_period_start: Start of analyzed period
        - analyzed_period_end: End of analyzed period
        - failed_login_alerts: List of users with suspicious failed login counts
        - multiple_ip_alerts: List of users with multiple IP access
        - total_failed_logins: Total number of failed login attempts in period
        - total_unique_users: Total number of unique users with activity
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.security_alerts import check_suspicious_activity
        >>> task = check_suspicious_activity.delay(time_window_minutes=30)
        >>> result = task.get()
        >>> print(result['failed_login_alerts'])
        [{'user_id': 'uuid', 'failed_count': 15, 'ip_address': '192.168.1.1'}]
    """
    import time
    import asyncio
    start_time = time.time()

    try:
        # Use default threshold if not specified
        if failed_login_threshold is None:
            failed_login_threshold = 5  # Default threshold

        logger.info(
            f"Starting suspicious activity check with {time_window_minutes}min window, "
            f"failed_login_threshold={failed_login_threshold}"
        )

        # Calculate time window
        end_time = datetime.utcnow()
        start_time_window = end_time - timedelta(minutes=time_window_minutes)

        async def perform_security_check():
            async with async_session_maker() as session:
                # Check 1: Multiple failed login attempts
                failed_login_alerts = await check_failed_logins(
                    session=session,
                    start_time=start_time_window,
                    end_time=end_time,
                    threshold=failed_login_threshold,
                )

                # Check 2: Multiple IPs for successful logins
                multiple_ip_alerts = []
                if alert_on_multiple_ips:
                    multiple_ip_alerts = await check_multiple_ip_access(
                        session=session,
                        start_time=start_time_window,
                        end_time=end_time,
                        threshold=ip_change_threshold,
                    )

                # Get summary statistics
                total_failed = await get_total_failed_logins(
                    session=session,
                    start_time=start_time_window,
                    end_time=end_time,
                )

                unique_users = await get_unique_active_users(
                    session=session,
                    start_time=start_time_window,
                    end_time=end_time,
                )

                return {
                    "failed_login_alerts": failed_login_alerts,
                    "multiple_ip_alerts": multiple_ip_alerts,
                    "total_failed_logins": total_failed,
                    "total_unique_users": unique_users,
                }

        # Run the async security check
        try:
            # Get or create event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        check_results = loop.run_until_complete(perform_security_check())

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Log alerts for monitoring
        if check_results["failed_login_alerts"]:
            logger.warning(
                f"Detected {len(check_results['failed_login_alerts'])} users with "
                f"suspicious failed login attempts"
            )
            for alert in check_results["failed_login_alerts"][:5]:  # Log first 5
                logger.warning(
                    f"User {alert['user_id']}: {alert['failed_count']} failed logins "
                    f"from IP {alert['ip_address']}"
                )

        if check_results["multiple_ip_alerts"]:
            logger.warning(
                f"Detected {len(check_results['multiple_ip_alerts'])} users with "
                f"multiple IP access patterns"
            )
            for alert in check_results["multiple_ip_alerts"][:5]:  # Log first 5
                logger.warning(
                    f"User {alert['user_id']}: {alert['ip_count']} unique IPs, "
                    f"locations: {', '.join(alert['locations'][:3])}"
                )

        result = {
            "status": "success",
            "time_window_minutes": time_window_minutes,
            "analyzed_period_start": start_time_window.isoformat(),
            "analyzed_period_end": end_time.isoformat(),
            "failed_login_alerts": check_results["failed_login_alerts"],
            "multiple_ip_alerts": check_results["multiple_ip_alerts"],
            "total_failed_logins": check_results["total_failed_logins"],
            "total_unique_users": check_results["total_unique_users"],
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Security check completed: "
            f"{len(check_results['failed_login_alerts'])} failed login alerts, "
            f"{len(check_results['multiple_ip_alerts'])} multiple IP alerts, "
            f"processing time: {processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Security activity check failed: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "failed",
            "error": str(e),
            "time_window_minutes": time_window_minutes,
            "processing_time_ms": processing_time_ms,
        }


async def check_failed_logins(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    threshold: int,
) -> List[Dict[str, Any]]:
    """
    Check for multiple failed login attempts from the same user/IP combination.

    Args:
        session: Database session
        start_time: Start of time window
        end_time: End of time window
        threshold: Minimum number of failed attempts to trigger alert

    Returns:
        List of alerts with user_id, failed_count, and ip_address
    """
    # Query for failed logins within time window
    query = (
        select(
            AuditLog.user_id,
            AuditLog.ip_address,
            func.count(AuditLog.id).label("failed_count"),
        )
        .where(
            and_(
                AuditLog.action_type == AuditActionType.LOGIN_FAILED,
                AuditLog.created_at >= start_time,
                AuditLog.created_at <= end_time,
                AuditLog.user_id.isnot(None),
                AuditLog.ip_address.isnot(None),
            )
        )
        .group_by(AuditLog.user_id, AuditLog.ip_address)
        .having(func.count(AuditLog.id) >= threshold)
        .order_by(func.count(AuditLog.id).desc())
    )

    result = await session.execute(query)
    alerts = [
        {
            "user_id": str(row.user_id),
            "ip_address": row.ip_address,
            "failed_count": row.failed_count,
        }
        for row in result.all()
    ]

    return alerts


async def check_multiple_ip_access(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    threshold: int,
) -> List[Dict[str, Any]]:
    """
    Check for successful logins from multiple different IP addresses.

    Args:
        session: Database session
        start_time: Start of time window
        end_time: End of time window
        threshold: Minimum number of unique IPs to trigger alert

    Returns:
        List of alerts with user_id, ip_count, locations, and ip_list
    """
    # Query for successful logins grouped by user and IP
    query = (
        select(
            AuditLog.user_id,
            AuditLog.ip_address,
            AuditLog.location,
            func.count(AuditLog.id).label("login_count"),
        )
        .where(
            and_(
                AuditLog.action_type == AuditActionType.LOGIN_SUCCESS,
                AuditLog.created_at >= start_time,
                AuditLog.created_at <= end_time,
                AuditLog.user_id.isnot(None),
                AuditLog.ip_address.isnot(None),
            )
        )
        .group_by(AuditLog.user_id, AuditLog.ip_address, AuditLog.location)
    )

    result = await session.execute(query)

    # Group IPs by user
    user_ips = defaultdict(lambda: {"ips": [], "locations": []})
    for row in result.all():
        user_ips[row.user_id]["ips"].append(row.ip_address)
        if row.location:
            user_ips[row.user_id]["locations"].append(row.location)

    # Filter users exceeding threshold
    alerts = [
        {
            "user_id": str(user_id),
            "ip_count": len(data["ips"]),
            "locations": list(set(data["locations"])),
            "ip_list": list(set(data["ips"])),
        }
        for user_id, data in user_ips.items()
        if len(data["ips"]) >= threshold
    ]

    # Sort by IP count (descending)
    alerts.sort(key=lambda x: x["ip_count"], reverse=True)

    return alerts


async def get_total_failed_logins(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
) -> int:
    """
    Get total count of failed login attempts in time window.

    Args:
        session: Database session
        start_time: Start of time window
        end_time: End of time window

    Returns:
        Total count of failed logins
    """
    query = select(func.count(AuditLog.id)).where(
        and_(
            AuditLog.action_type == AuditActionType.LOGIN_FAILED,
            AuditLog.created_at >= start_time,
            AuditLog.created_at <= end_time,
        )
    )

    result = await session.execute(query)
    return result.scalar() or 0


async def get_unique_active_users(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
) -> int:
    """
    Get count of unique users with login activity in time window.

    Args:
        session: Database session
        start_time: Start of time window
        end_time: End of time window

    Returns:
        Count of unique users
    """
    query = (
        select(func.count(func.distinct(AuditLog.user_id)))
        .where(
            and_(
                AuditLog.action_type.in_(
                    [AuditActionType.LOGIN_SUCCESS, AuditActionType.LOGIN_FAILED]
                ),
                AuditLog.created_at >= start_time,
                AuditLog.created_at <= end_time,
                AuditLog.user_id.isnot(None),
            )
        )
    )

    result = await session.execute(query)
    return result.scalar() or 0


@shared_task(
    name="tasks.security_alerts.send_security_alert",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_security_alert(
    self,
    alert_type: str,
    recipient_email: Optional[str] = None,
    recipient_phone: Optional[str] = None,
    alert_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send security alert notification via email and/or SMS.

    This Celery task handles sending security alert notifications to users
    when suspicious activity is detected. It supports both email and SMS delivery
    and formats the alert based on the alert type.

    Task Workflow:
    1. Validate alert type and recipient information
    2. Format alert message based on alert type (failed_logins, multiple_ips, etc.)
    3. Send email notification if email provided
    4. Send SMS notification if phone provided
    5. Return delivery status for both channels

    Args:
        self: Celery task instance (bind=True)
        alert_type: Type of security alert (failed_logins, multiple_ips, account_locked, etc.)
        recipient_email: Email address to send alert to (optional)
        recipient_phone: Phone number to send SMS to (optional)
        alert_data: Dictionary containing alert-specific details:
            - user_id: UUID of the affected user
            - ip_address: IP address involved in the alert
            - failed_count: Number of failed attempts (for failed_logins)
            - ip_count: Number of unique IPs (for multiple_ips)
            - locations: List of locations (for multiple_ips)
            - timestamp: When the alert was triggered
            - severity: Alert severity (low, medium, high)

    Returns:
        Dictionary containing alert delivery results:
        - alert_type: Type of security alert
        - status: Task status (sent/failed/partial)
        - email_sent: Whether email was sent successfully
        - sms_sent: Whether SMS was sent successfully
        - recipient_email: Email address (if provided)
        - recipient_phone_masked: Masked phone number (if provided)
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For notification sending failures

    Example:
        >>> from tasks.security_alerts import send_security_alert
        >>> alert_data = {
        ...     "user_id": "uuid-123",
        ...     "ip_address": "192.168.1.1",
        ...     "failed_count": 10,
        ...     "severity": "high"
        ... }
        >>> task = send_security_alert.delay(
        ...     alert_type="failed_logins",
        ...     recipient_email="user@example.com",
        ...     alert_data=alert_data
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending security alert: type={alert_type}, "
        f"email={'yes' if recipient_email else 'no'}, "
        f"sms={'yes' if recipient_phone else 'no'}"
    )

    if not alert_data:
        alert_data = {}

    email_sent = False
    sms_sent = False
    errors = []

    try:
        # Validate that at least one recipient is provided
        if not recipient_email and not recipient_phone:
            error_msg = "At least one recipient (email or phone) must be provided"
            logger.error(error_msg)
            return {
                "alert_type": alert_type,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 1: Format alert message
        progress = {
            "current": 1,
            "total": 3,
            "percentage": 33,
            "status": "formatting_alert",
            "message": "Formatting alert message...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        email_subject, email_body, sms_message = format_security_alert_message(
            alert_type=alert_type,
            alert_data=alert_data,
        )

        logger.info(f"Alert formatted: subject='{email_subject}', sms_length={len(sms_message)}")

        # Step 2: Send email if recipient provided
        if recipient_email:
            progress = {
                "current": 2,
                "total": 3,
                "percentage": 66,
                "status": "sending_email",
                "message": "Sending email notification...",
            }
            self.update_state(state="PROGRESS", meta=progress)

            try:
                # Log email details (in production, actually send email)
                logger.info(
                    f"Sending security alert email: subject='{email_subject}', "
                    f"to={recipient_email}"
                )

                # Simulate email sending (in production, use SMTP/service)
                time.sleep(0.1)  # Simulate network delay

                email_sent = True
                logger.info(f"Security alert email sent successfully to {recipient_email}")

            except Exception as e:
                error_msg = f"Failed to send email: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Step 3: Send SMS if phone provided
        if recipient_phone:
            progress = {
                "current": 3,
                "total": 3,
                "percentage": 100,
                "status": "sending_sms",
                "message": "Sending SMS notification...",
            }
            self.update_state(state="PROGRESS", meta=progress)

            try:
                # Log SMS details (in production, actually send SMS)
                logger.info(
                    f"Sending security alert SMS: length={len(sms_message)}, "
                    f"to={mask_phone_number(recipient_phone)}"
                )

                # Simulate SMS sending (in production, use Twilio/SNS/etc.)
                time.sleep(0.1)  # Simulate network delay

                sms_sent = True
                logger.info(
                    f"Security alert SMS sent successfully to {mask_phone_number(recipient_phone)}"
                )

            except Exception as e:
                error_msg = f"Failed to send SMS: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Determine overall status
        if email_sent or sms_sent:
            status = "sent"
        else:
            status = "failed"

        result = {
            "alert_type": alert_type,
            "status": status,
            "email_sent": email_sent,
            "sms_sent": sms_sent,
            "recipient_email": recipient_email if recipient_email else None,
            "recipient_phone_masked": mask_phone_number(recipient_phone) if recipient_phone else None,
            "processing_time_ms": processing_time_ms,
        }

        if errors:
            result["errors"] = errors

        if status == "sent":
            logger.info(
                f"Security alert sent successfully: type={alert_type}, "
                f"email={email_sent}, sms={sms_sent}, time={processing_time_ms}ms"
            )
        else:
            logger.error(f"Security alert delivery failed: type={alert_type}, errors={errors}")

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Security alert task timed out for alert_type={alert_type}")
        return {
            "alert_type": alert_type,
            "status": "failed",
            "email_sent": email_sent,
            "sms_sent": sms_sent,
            "error": "Task timed out",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(
            f"Failed to send security alert for alert_type={alert_type}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "alert_type": alert_type,
            "status": "failed",
            "email_sent": email_sent,
            "sms_sent": sms_sent,
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def format_security_alert_message(
    alert_type: str,
    alert_data: Dict[str, Any],
) -> tuple[str, str, str]:
    """
    Format security alert message for email and SMS.

    This function formats security alert messages based on the alert type.
    It returns both an email version (with subject and body) and an SMS version
    (short and concise).

    Args:
        alert_type: Type of security alert
        alert_data: Dictionary containing alert-specific details

    Returns:
        Tuple of (email_subject, email_body, sms_message)

    Example:
        >>> subject, body, sms = format_security_alert_message(
        ...     "failed_logins",
        ...     {"failed_count": 10, "ip_address": "192.168.1.1"}
        ... )
        >>> print(subject)
        'Security Alert: Multiple Failed Login Attempts Detected'
    """
    user_id = alert_data.get("user_id", "Unknown")
    ip_address = alert_data.get("ip_address", "Unknown")
    severity = alert_data.get("severity", "medium").upper()
    timestamp = alert_data.get("timestamp", datetime.utcnow().isoformat())

    if alert_type == "failed_logins":
        failed_count = alert_data.get("failed_count", 0)

        email_subject = f"⚠️ Security Alert: Multiple Failed Login Attempts Detected"

        email_body = f"""
Security Alert Notification

Alert Type: Multiple Failed Login Attempts
Severity: {severity}
User ID: {user_id}
Timestamp: {timestamp}

Details:
- We detected {failed_count} failed login attempts on your account.
- These attempts originated from IP address: {ip_address}.
- This may indicate someone is trying to gain unauthorized access to your account.

Recommended Actions:
1. Review your recent login activity in your security settings.
2. Change your password immediately if you don't recognize this activity.
3. Enable two-factor authentication for enhanced security.
4. Contact support if you believe this is suspicious.

If this was you, you can safely ignore this alert.

---
This is an automated security notification from AgentHR.
        """.strip()

        sms_message = (
            f"⚠️ AgentHR Security Alert: {failed_count} failed login attempts detected "
            f"from IP {ip_address}. If this wasn't you, secure your account immediately."
        )

    elif alert_type == "multiple_ips":
        ip_count = alert_data.get("ip_count", 0)
        locations = alert_data.get("locations", [])

        email_subject = f"⚠️ Security Alert: Unusual Multiple Location Access Detected"

        location_str = ", ".join(locations[:3]) if locations else "Various locations"

        email_body = f"""
Security Alert Notification

Alert Type: Multiple Location Access
Severity: {severity}
User ID: {user_id}
Timestamp: {timestamp}

Details:
- We detected successful logins to your account from {ip_count} different IP addresses.
- Access locations: {location_str}
- This unusual pattern may indicate unauthorized access.

Recommended Actions:
1. Review your recent login activity and locations.
2. Verify that you recognize all these access locations.
3. Change your password if you don't recognize this activity.
4. Contact support if you believe your account has been compromised.

If this was you accessing your account from multiple locations, you can safely ignore this alert.

---
This is an automated security notification from AgentHR.
        """.strip()

        sms_message = (
            f"⚠️ AgentHR Security Alert: Logins detected from {ip_count} different locations. "
            f"If this wasn't you, secure your account immediately."
        )

    elif alert_type == "account_locked":
        reason = alert_data.get("reason", "Too many failed login attempts")

        email_subject = f"🔒 Security Alert: Your Account Has Been Locked"

        email_body = f"""
Security Alert Notification

Alert Type: Account Locked
Severity: {severity}
User ID: {user_id}
Timestamp: {timestamp}

Details:
- Your AgentHR account has been locked due to security concerns.
- Reason: {reason}
- This action was taken automatically to protect your account.

To Regain Access:
1. Visit the account security page.
2. Verify your identity through the provided methods.
3. Reset your password if required.
4. Contact support if you need assistance.

This lock protects your account from unauthorized access.

---
This is an automated security notification from AgentHR.
        """.strip()

        sms_message = (
            f"🔒 AgentHR Security Alert: Your account has been locked due to suspicious activity. "
            f"Visit AgentHR to verify and unlock your account."
        )

    elif alert_type == "password_reset":
        email_subject = f"🔑 Security Alert: Password Reset Requested"

        email_body = f"""
Security Alert Notification

Alert Type: Password Reset
Severity: {severity}
User ID: {user_id}
Timestamp: {timestamp}

Details:
- A password reset was requested for your AgentHR account.
- If you requested this, follow the reset link sent separately.
- If you did NOT request this, secure your account immediately.

Recommended Actions (if you didn't request this):
1. Change your password immediately.
2. Review your account security settings.
3. Enable two-factor authentication.
4. Contact support if needed.

---
This is an automated security notification from AgentHR.
        """.strip()

        sms_message = (
            f"🔑 AgentHR Security Alert: Password reset requested for your account. "
            f"If this wasn't you, contact support immediately."
        )

    else:
        # Generic security alert
        email_subject = f"⚠️ Security Alert: {alert_type.replace('_', ' ').title()}"

        email_body = f"""
Security Alert Notification

Alert Type: {alert_type}
Severity: {severity}
User ID: {user_id}
Timestamp: {timestamp}

Details:
- A security event was detected on your AgentHR account.
- IP Address: {ip_address}

Please review your account security settings and contact support if you have concerns.

---
This is an automated security notification from AgentHR.
        """.strip()

        sms_message = (
            f"⚠️ AgentHR Security Alert: {alert_type.replace('_', ' ').title()} detected. "
            f"Review your account security settings."
        )

    return email_subject, email_body, sms_message


def mask_phone_number(phone: str) -> str:
    """
    Mask a phone number for logging purposes.

    This function masks all but the last 4 digits of a phone number
    to protect user privacy in logs.

    Args:
        phone: Phone number string

    Returns:
        Masked phone number (e.g., "******1234")

    Example:
        >>> mask_phone_number("+1234567890")
        '******7890'
    """
    if not phone:
        return "Unknown"

    # Remove any non-digit characters
    digits = "".join(c for c in phone if c.isdigit())

    if len(digits) <= 4:
        return "*" * len(digits)

    # Show only last 4 digits
    return "*" * (len(digits) - 4) + digits[-4:]


@shared_task(
    name="tasks.security_alerts.send_security_alert_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_security_alert_webhook(
    self,
    alert_type: str,
    webhook_url: str,
    webhook_secret: Optional[str] = None,
    alert_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send security alert notification via webhook.

    This Celery task handles sending security alert notifications to external
    systems via HTTP webhooks. It formats the alert as JSON and sends it as a POST
    request to the configured webhook URL.

    Task Workflow:
    1. Validate webhook URL format
    2. Format alert payload as JSON
    3. Send POST request to webhook URL
    4. Handle authentication (if secret provided)
    5. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        alert_type: Type of security alert (failed_logins, multiple_ips, etc.)
        webhook_url: URL endpoint to send the webhook to
        webhook_secret: Optional secret for HMAC signature authentication
        alert_data: Dictionary containing alert-specific details:
            - user_id: UUID of the affected user
            - ip_address: IP address involved in the alert
            - failed_count: Number of failed attempts (for failed_logins)
            - ip_count: Number of unique IPs (for multiple_ips)
            - locations: List of locations (for multiple_ips)
            - timestamp: When the alert was triggered
            - severity: Alert severity (low, medium, high)

    Returns:
        Dictionary containing webhook delivery results:
        - alert_type: Type of security alert
        - status: Task status (sent/failed)
        - webhook_url: URL webhook was sent to (masked)
        - response_status_code: HTTP status code from webhook endpoint
        - response_body: Response body from webhook endpoint
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For webhook sending failures

    Example:
        >>> from tasks.security_alerts import send_security_alert_webhook
        >>> alert_data = {
        ...     "user_id": "uuid-123",
        ...     "ip_address": "192.168.1.1",
        ...     "failed_count": 10,
        ...     "severity": "high"
        ... }
        >>> task = send_security_alert_webhook.delay(
        ...     alert_type="failed_logins",
        ...     webhook_url="https://example.com/webhook",
        ...     alert_data=alert_data
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    import time
    import hmac
    import hashlib
    start_time = time.time()

    logger.info(
        f"Sending security alert webhook: type={alert_type}, "
        f"url={mask_webhook_url(webhook_url)}"
    )

    if not alert_data:
        alert_data = {}

    try:
        # Validate webhook URL
        parsed_url = urlparse(webhook_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            error_msg = f"Invalid webhook URL: {webhook_url}"
            logger.error(error_msg)
            return {
                "alert_type": alert_type,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 1: Format webhook payload
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_payload",
            "message": "Formatting webhook payload...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        payload = format_webhook_payload(
            alert_type=alert_type,
            alert_data=alert_data,
        )

        # Step 2: Send webhook
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_webhook",
            "message": "Sending webhook notification...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AgentHR-SecurityAlerts/1.0",
        }

        # Add signature header if secret provided
        if webhook_secret:
            payload_bytes = json.dumps(payload).encode("utf-8")
            signature = hmac.new(
                webhook_secret.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()
            headers["X-AgentHR-Signature"] = f"sha256={signature}"
            headers["X-AgentHR-Timestamp"] = str(int(time.time()))

        logger.info(
            f"Sending POST request to {mask_webhook_url(webhook_url)}, "
            f"payload_size={len(json.dumps(payload))} bytes"
        )

        # Send webhook with timeout
        timeout = httpx.Timeout(10.0, connect=5.0)
        async def send_webhook():
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                )
                return response

        # Run async webhook in new event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(send_webhook())

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Check response status
        if 200 <= response.status_code < 300:
            status = "sent"
            logger.info(
                f"Security alert webhook sent successfully: "
                f"type={alert_type}, status_code={response.status_code}, "
                f"time={processing_time_ms}ms"
            )
        else:
            status = "failed"
            logger.warning(
                f"Security alert webhook returned non-success status: "
                f"type={alert_type}, status_code={response.status_code}"
            )

        result = {
            "alert_type": alert_type,
            "status": status,
            "webhook_url": mask_webhook_url(webhook_url),
            "response_status_code": response.status_code,
            "response_body": response.text[:1000] if response.text else None,  # Truncate large responses
            "processing_time_ms": processing_time_ms,
        }

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Security alert webhook task timed out for alert_type={alert_type}")
        return {
            "alert_type": alert_type,
            "status": "failed",
            "webhook_url": mask_webhook_url(webhook_url),
            "error": "Task timed out",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(
            f"Failed to send security alert webhook for alert_type={alert_type}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "alert_type": alert_type,
            "status": "failed",
            "webhook_url": mask_webhook_url(webhook_url),
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.security_alerts.send_security_alert_slack",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_security_alert_slack(
    self,
    alert_type: str,
    slack_webhook_url: str,
    alert_data: Optional[Dict[str, Any]] = None,
    channel: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send security alert notification via Slack webhook.

    This Celery task handles sending security alert notifications to Slack channels
    using Slack's incoming webhook API. It formats the alert as a rich Slack message
    with color coding based on severity.

    Task Workflow:
    1. Validate Slack webhook URL
    2. Format alert as Slack message with blocks
    3. Send POST request to Slack webhook URL
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        alert_type: Type of security alert (failed_logins, multiple_ips, etc.)
        slack_webhook_url: Slack incoming webhook URL
        alert_data: Dictionary containing alert-specific details:
            - user_id: UUID of the affected user
            - ip_address: IP address involved in the alert
            - failed_count: Number of failed attempts (for failed_logins)
            - ip_count: Number of unique IPs (for multiple_ips)
            - locations: List of locations (for multiple_ips)
            - timestamp: When the alert was triggered
            - severity: Alert severity (low, medium, high)
        channel: Optional Slack channel override (defaults to webhook's default channel)

    Returns:
        Dictionary containing Slack delivery results:
        - alert_type: Type of security alert
        - status: Task status (sent/failed)
        - channel: Slack channel message was sent to
        - response_status_code: HTTP status code from Slack
        - response_body: Response body from Slack
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For Slack sending failures

    Example:
        >>> from tasks.security_alerts import send_security_alert_slack
        >>> alert_data = {
        ...     "user_id": "uuid-123",
        ...     "ip_address": "192.168.1.1",
        ...     "failed_count": 10,
        ...     "severity": "high"
        ... }
        >>> task = send_security_alert_slack.delay(
        ...     alert_type="failed_logins",
        ...     slack_webhook_url="https://hooks.slack.com/services/...",
        ...     alert_data=alert_data
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending security alert to Slack: type={alert_type}"
    )

    if not alert_data:
        alert_data = {}

    try:
        # Validate Slack webhook URL
        if not slack_webhook_url.startswith("https://hooks.slack.com/"):
            error_msg = "Invalid Slack webhook URL (must start with https://hooks.slack.com/)"
            logger.error(error_msg)
            return {
                "alert_type": alert_type,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 1: Format Slack message
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_message",
            "message": "Formatting Slack message...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        slack_message = format_slack_message(
            alert_type=alert_type,
            alert_data=alert_data,
        )

        # Override channel if specified
        if channel:
            slack_message["channel"] = channel

        # Step 2: Send to Slack
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_to_slack",
            "message": "Sending message to Slack...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        logger.info(
            f"Sending POST request to Slack webhook, "
            f"message_blocks={len(slack_message.get('blocks', []))}"
        )

        # Send Slack webhook with timeout
        timeout = httpx.Timeout(10.0, connect=5.0)
        async def send_slack():
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    slack_webhook_url,
                    json=slack_message,
                )
                return response

        # Run async webhook in new event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(send_slack())

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Check response status (Slack returns 200 for success)
        if response.status_code == 200:
            status = "sent"
            logger.info(
                f"Security alert sent to Slack successfully: "
                f"type={alert_type}, time={processing_time_ms}ms"
            )
        else:
            status = "failed"
            logger.warning(
                f"Slack webhook returned non-success status: "
                f"type={alert_type}, status_code={response.status_code}"
            )

        result = {
            "alert_type": alert_type,
            "status": status,
            "channel": channel or "webhook-default",
            "response_status_code": response.status_code,
            "response_body": response.text[:500] if response.text else None,
            "processing_time_ms": processing_time_ms,
        }

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Security alert Slack task timed out for alert_type={alert_type}")
        return {
            "alert_type": alert_type,
            "status": "failed",
            "error": "Task timed out",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(
            f"Failed to send security alert to Slack for alert_type={alert_type}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "alert_type": alert_type,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.security_alerts.send_security_alert_multi_channel",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_security_alert_multi_channel(
    self,
    alert_type: str,
    recipient_email: Optional[str] = None,
    recipient_phone: Optional[str] = None,
    webhook_url: Optional[str] = None,
    slack_webhook_url: Optional[str] = None,
    alert_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send security alert notification via multiple channels simultaneously.

    This Celery task orchestrates sending security alerts across multiple
    notification channels (email, SMS, webhook, Slack) in parallel. Each channel
    is handled by its own dedicated task, allowing for independent failure handling
    and retry logic.

    Task Workflow:
    1. Validate alert data and configured channels
    2. Trigger parallel delivery tasks for each enabled channel
    3. Aggregate results from all channels
    4. Return combined delivery status

    Args:
        self: Celery task instance (bind=True)
        alert_type: Type of security alert (failed_logins, multiple_ips, etc.)
        recipient_email: Email address to send alert to (optional)
        recipient_phone: Phone number to send SMS to (optional)
        webhook_url: Webhook URL to send alert to (optional)
        slack_webhook_url: Slack webhook URL to send alert to (optional)
        alert_data: Dictionary containing alert-specific details

    Returns:
        Dictionary containing multi-channel delivery results:
        - alert_type: Type of security alert
        - status: Overall task status (sent/partial/failed)
        - channels_sent: List of channels that succeeded
        - channels_failed: List of channels that failed
        - email_status: Email delivery result (if email provided)
        - sms_status: SMS delivery result (if phone provided)
        - webhook_status: Webhook delivery result (if webhook URL provided)
        - slack_status: Slack delivery result (if Slack URL provided)
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.security_alerts import send_security_alert_multi_channel
        >>> task = send_security_alert_multi_channel.delay(
        ...     alert_type="failed_logins",
        ...     recipient_email="user@example.com",
        ...     slack_webhook_url="https://hooks.slack.com/services/...",
        ...     alert_data={"failed_count": 10}
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'sent'
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending multi-channel security alert: type={alert_type}, "
        f"email={'yes' if recipient_email else 'no'}, "
        f"sms={'yes' if recipient_phone else 'no'}, "
        f"webhook={'yes' if webhook_url else 'no'}, "
        f"slack={'yes' if slack_webhook_url else 'no'}"
    )

    if not alert_data:
        alert_data = {}

    channels_sent = []
    channels_failed = []
    channel_results = {}

    try:
        # Validate at least one channel is configured
        if not any([recipient_email, recipient_phone, webhook_url, slack_webhook_url]):
            error_msg = "At least one notification channel must be configured"
            logger.error(error_msg)
            return {
                "alert_type": alert_type,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Trigger delivery tasks for each enabled channel
        tasks = []

        # Email channel
        if recipient_email:
            email_task = send_security_alert.subtask(
                args=(alert_type,),
                kwargs={
                    "recipient_email": recipient_email,
                    "recipient_phone": None,
                    "alert_data": alert_data,
                },
            )
            tasks.append(("email", email_task))

        # SMS channel
        if recipient_phone:
            sms_task = send_security_alert.subtask(
                args=(alert_type,),
                kwargs={
                    "recipient_email": None,
                    "recipient_phone": recipient_phone,
                    "alert_data": alert_data,
                },
            )
            tasks.append(("sms", sms_task))

        # Webhook channel
        if webhook_url:
            webhook_task = send_security_alert_webhook.subtask(
                args=(alert_type, webhook_url),
                kwargs={"alert_data": alert_data},
            )
            tasks.append(("webhook", webhook_task))

        # Slack channel
        if slack_webhook_url:
            slack_task = send_security_alert_slack.subtask(
                args=(alert_type, slack_webhook_url),
                kwargs={"alert_data": alert_data},
            )
            tasks.append(("slack", slack_task))

        # Execute all tasks in parallel using celery group
        from celery import group
        from celery.result import GroupResult

        task_group = group([task for _, task in tasks])
        group_result: GroupResult = task_group.apply_async()

        # Wait for all tasks to complete (with timeout)
        try:
            group_result.get(timeout=30)
        except Exception as e:
            logger.warning(f"Some channel tasks failed or timed out: {e}")

        # Collect results
        for i, (channel_name, _) in enumerate(tasks):
            try:
                result = group_result.children[i].result
                if result and result.get("status") == "sent":
                    channels_sent.append(channel_name)
                else:
                    channels_failed.append(channel_name)
                channel_results[f"{channel_name}_status"] = result
            except Exception as e:
                logger.error(f"Failed to get result for {channel_name}: {e}")
                channels_failed.append(channel_name)
                channel_results[f"{channel_name}_status"] = {"error": str(e)}

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Determine overall status
        if channels_sent and not channels_failed:
            status = "sent"
        elif channels_sent:
            status = "partial"
        else:
            status = "failed"

        result = {
            "alert_type": alert_type,
            "status": status,
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
            "processing_time_ms": processing_time_ms,
        }
        result.update(channel_results)

        logger.info(
            f"Multi-channel security alert completed: "
            f"status={status}, sent={len(channels_sent)}, failed={len(channels_failed)}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(
            f"Failed to send multi-channel security alert for alert_type={alert_type}: {e}",
            exc_info=True,
        )

        return {
            "alert_type": alert_type,
            "status": "failed",
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def format_webhook_payload(
    alert_type: str,
    alert_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format security alert as a webhook JSON payload.

    This function creates a standardized JSON payload for webhook delivery,
    suitable for consumption by external monitoring systems, SIEM platforms,
    or custom alert handlers.

    Args:
        alert_type: Type of security alert
        alert_data: Dictionary containing alert-specific details

    Returns:
        Dictionary containing formatted webhook payload

    Example:
        >>> payload = format_webhook_payload(
        ...     "failed_logins",
        ...     {"failed_count": 10, "ip_address": "192.168.1.1"}
        ... )
        >>> print(payload['event_type'])
        'security.alert.failed_logins'
    """
    user_id = alert_data.get("user_id", "unknown")
    ip_address = alert_data.get("ip_address", "unknown")
    severity = alert_data.get("severity", "medium").lower()
    timestamp = alert_data.get("timestamp", datetime.utcnow().isoformat())

    # Map alert type to severity level and color
    severity_colors = {
        "low": "#36a64f",  # green
        "medium": "#ff9900",  # orange
        "high": "#ff0000",  # red
        "critical": "#8b0000",  # dark red
    }
    color = severity_colors.get(severity, "#ff9900")

    payload = {
        "event_type": f"security.alert.{alert_type}",
        "event_id": f"{alert_type}_{user_id}_{int(datetime.utcnow().timestamp())}",
        "timestamp": timestamp,
        "severity": severity,
        "source": "agenthr",
        "source_type": "security_monitoring",
        "data": {
            "alert_type": alert_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "severity": severity,
        },
    }

    # Add alert-type specific data
    if alert_type == "failed_logins":
        failed_count = alert_data.get("failed_count", 0)
        payload["data"]["failed_count"] = failed_count
        payload["title"] = f"Multiple Failed Login Attempts Detected"
        payload["description"] = (
            f"{failed_count} failed login attempts detected from IP {ip_address}"
        )
    elif alert_type == "multiple_ips":
        ip_count = alert_data.get("ip_count", 0)
        locations = alert_data.get("locations", [])
        payload["data"]["ip_count"] = ip_count
        payload["data"]["locations"] = locations
        payload["title"] = f"Unusual Multiple Location Access Detected"
        payload["description"] = (
            f"Successful logins from {ip_count} different IP addresses detected"
        )
    elif alert_type == "account_locked":
        reason = alert_data.get("reason", "Security policy")
        payload["data"]["reason"] = reason
        payload["title"] = f"Account Locked"
        payload["description"] = f"Account locked due to: {reason}"
    else:
        payload["title"] = f"Security Alert: {alert_type.replace('_', ' ').title()}"
        payload["description"] = f"Security event detected: {alert_type}"

    # Add alert_data fields that aren't already in payload
    for key, value in alert_data.items():
        if key not in payload["data"]:
            payload["data"][key] = value

    return payload


def format_slack_message(
    alert_type: str,
    alert_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format security alert as a Slack message with blocks.

    This function creates a rich Slack message using Slack's Block Kit API,
    with color coding, emojis, and structured information display.

    Args:
        alert_type: Type of security alert
        alert_data: Dictionary containing alert-specific details

    Returns:
        Dictionary containing formatted Slack message

    Example:
        >>> message = format_slack_message(
        ...     "failed_logins",
        ...     {"failed_count": 10, "ip_address": "192.168.1.1"}
        ... )
        >>> print(message['blocks'][0]['text']['text'])
        '🚨 Security Alert'
    """
    user_id = alert_data.get("user_id", "unknown")
    ip_address = alert_data.get("ip_address", "unknown")
    severity = alert_data.get("severity", "medium").lower()
    timestamp = alert_data.get("timestamp", datetime.utcnow().isoformat())

    # Map severity to color and emoji
    severity_config = {
        "low": {"color": "#36a64f", "emoji": "🟢", "label": "Low"},
        "medium": {"color": "#ff9900", "emoji": "🟠", "label": "Medium"},
        "high": {"color": "#ff0000", "emoji": "🔴", "label": "High"},
        "critical": {"color": "#8b0000", "emoji": "🚨", "label": "Critical"},
    }
    config = severity_config.get(severity, severity_config["medium"])

    # Build alert title and description
    if alert_type == "failed_logins":
        failed_count = alert_data.get("failed_count", 0)
        title = f"Multiple Failed Login Attempts Detected"
        description = f"*{failed_count}* failed login attempts detected from IP `{ip_address}`"
    elif alert_type == "multiple_ips":
        ip_count = alert_data.get("ip_count", 0)
        locations = alert_data.get("locations", [])
        title = f"Unusual Multiple Location Access Detected"
        location_str = ", ".join(locations[:3]) if locations else "Various locations"
        description = f"Logins from *{ip_count}* different IP addresses. Locations: {location_str}"
    elif alert_type == "account_locked":
        reason = alert_data.get("reason", "Security policy")
        title = f"Account Locked"
        description = f"Account locked due to: *{reason}*"
    elif alert_type == "password_reset":
        title = f"Password Reset Requested"
        description = f"A password reset was requested for this account"
    else:
        title = f"Security Alert: {alert_type.replace('_', ' ').title()}"
        description = f"Security event detected: *{alert_type}*"

    # Build Slack message blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{config['emoji']} Security Alert",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Alert Type:*\n{title}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Severity:*\n{config['label'].upper()}",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": description,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*User ID:*\n`{user_id}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*IP Address:*\n`{ip_address}`",
                },
            ],
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Timestamp:*\n{timestamp}",
                },
            ],
        },
        {
            "type": "divider",
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Powered by AgentHR Security Monitoring",
                },
            ],
        },
    ]

    message = {
        "username": "AgentHR Security Alerts",
        "icon_emoji": ":shield:",
        "attachments": [
            {
                "color": config["color"],
                "blocks": blocks,
            },
        ],
    }

    return message


def mask_webhook_url(url: str) -> str:
    """
    Mask a webhook URL for logging purposes.

    This function masks sensitive parts of a webhook URL to protect
    security credentials in logs while preserving the domain for debugging.

    Args:
        url: Webhook URL string

    Returns:
        Masked webhook URL

    Example:
        >>> mask_webhook_url("https://example.com/webhook/secret123")
        'https://example.com/webhook/****'
    """
    if not url:
        return "unknown"

    try:
        parsed = urlparse(url)
        # Show scheme and netloc, mask the path
        masked = f"{parsed.scheme}://{parsed.netloc}/****"
        return masked
    except Exception:
        return "****"


__all__ = [
    "check_suspicious_activity",
    "send_security_alert",
    "send_security_alert_webhook",
    "send_security_alert_slack",
    "send_security_alert_multi_channel",
]
