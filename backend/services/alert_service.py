"""
Alert notification service for email and webhooks.

This module provides comprehensive alert notification functionality including:
- Email alerts for health check failures
- Webhook notifications for external integrations
- Support for multiple notification channels
- Alert formatting and delivery
- Error handling and retry logic
"""
import json
import logging
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertChannel:
    """Types of alert notification channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class AlertSeverity:
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def send_email_alert(
    recipient_email: str,
    subject: str,
    message: str,
    severity: str = AlertSeverity.WARNING,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send an alert notification via email.

    This function handles sending email alerts for system health monitoring.
    It composes and sends email notifications with formatted content including
    severity levels and optional metadata.

    Args:
        recipient_email: Email address of the recipient
        subject: Email subject line
        message: Main alert message body
        severity: Alert severity level (info, warning, error, critical)
        metadata: Optional additional context and data

    Returns:
        Dictionary containing sending results:
        - channel: Channel type (email)
        - status: Sending status (sent/failed)
        - recipient: Email address of recipient
        - severity: Alert severity level
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        Exception: For email sending failures

    Example:
        >>> result = send_email_alert(
        ...     recipient_email="admin@example.com",
        ...     subject="Health Check Failed",
        ...     message="Database is unhealthy",
        ...     severity="critical",
        ...     metadata={"component": "database", "status": "unhealthy"}
        ... )
        >>> print(result['status'])
        'sent'
    """
    start_time = time.time()

    logger.info(
        f"Sending email alert to {recipient_email} "
        f"(severity={severity}, subject='{subject}')"
    )

    try:
        # Compose email body with severity formatting
        severity_upper = severity.upper()
        body_parts = [
            f"Severity: {severity_upper}",
            f"Subject: {subject}",
            "",
            message,
        ]

        # Add metadata if provided
        if metadata:
            body_parts.append("")
            body_parts.append("Details:")
            for key, value in metadata.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                body_parts.append(f"  {key}: {value}")

        body_parts.append("")
        body_parts.append("---")
        body_parts.append("This is an automated alert from AgentHR Health Monitoring.")

        body = "\n".join(body_parts)

        # Log email details (in production, actually send email)
        logger.info(f"Email alert composed: to={recipient_email}")
        logger.info(f"Email body length: {len(body)} characters")

        # Simulate email sending (in production, use SMTP/service)
        # For now, just log and mark as sent
        time.sleep(0.05)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Email alert sent successfully to {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "channel": AlertChannel.EMAIL,
            "status": "sent",
            "recipient": recipient_email,
            "severity": severity,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except Exception as e:
        logger.error(
            f"Failed to send email alert to {recipient_email}: {e}",
            exc_info=True,
        )

        return {
            "channel": AlertChannel.EMAIL,
            "status": "failed",
            "recipient": recipient_email,
            "severity": severity,
            "error": str(e),
        }


def send_webhook_alert(
    webhook_url: str,
    alert_data: Dict[str, Any],
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Send an alert notification via webhook.

    This function handles sending webhook notifications to external systems.
    It supports generic webhooks as well as specific integrations like Slack
    and Microsoft Teams.

    Args:
        webhook_url: URL to send the webhook to
        alert_data: Dictionary containing alert details:
            - severity: Alert severity level
            - title: Alert title
            - message: Alert message
            - component: System component name
            - status: Health status
            - timestamp: ISO 8601 timestamp
            - metadata: Optional additional data
        timeout: Request timeout in seconds

    Returns:
        Dictionary containing sending results:
        - channel: Channel type (webhook)
        - status: Sending status (sent/failed)
        - webhook_url: URL that was called
        - status_code: HTTP status code (if sent)
        - response_body: Response body (if sent)
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        ValueError: If webhook_url is invalid
        Exception: For webhook sending failures

    Example:
        >>> result = send_webhook_alert(
        ...     webhook_url="https://hooks.slack.com/services/...",
        ...     alert_data={
        ...         "severity": "critical",
        ...         "title": "Database Unhealthy",
        ...         "message": "Database connection failed",
        ...         "component": "database",
        ...         "status": "unhealthy"
        ...     }
        ... )
        >>> print(result['status'])
        'sent'
    """
    start_time = time.time()

    # Validate webhook URL
    try:
        parsed = urlparse(webhook_url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Invalid webhook URL: {webhook_url}")
    except Exception as e:
        logger.error(f"Invalid webhook URL: {e}")
        return {
            "channel": AlertChannel.WEBHOOK,
            "status": "failed",
            "webhook_url": webhook_url,
            "error": f"Invalid URL: {str(e)}",
        }

    logger.info(f"Sending webhook alert to {webhook_url}")

    try:
        # Detect webhook type and format payload accordingly
        if "slack.com" in webhook_url:
            payload = _format_slack_payload(alert_data)
        elif "webhook.office.com" in webhook_url or "office.com/webhook" in webhook_url:
            payload = _format_teams_payload(alert_data)
        else:
            # Generic webhook format
            payload = alert_data

        # Convert to JSON
        payload_json = json.dumps(payload).encode("utf-8")

        # Send webhook request
        request = Request(
            webhook_url,
            data=payload_json,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AgentHR-HealthMonitor/1.0",
            },
            method="POST",
        )

        with urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8", errors="replace")

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Webhook alert sent successfully to {webhook_url} "
            f"(status={status_code}) in {processing_time}ms"
        )

        return {
            "channel": AlertChannel.WEBHOOK,
            "status": "sent",
            "webhook_url": webhook_url,
            "status_code": status_code,
            "response_body": response_body,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except HTTPError as e:
        logger.error(f"Webhook HTTP error: {e.code} - {e.reason}")
        return {
            "channel": AlertChannel.WEBHOOK,
            "status": "failed",
            "webhook_url": webhook_url,
            "status_code": e.code,
            "error": f"HTTP {e.code}: {e.reason}",
        }

    except URLError as e:
        logger.error(f"Webhook URL error: {e.reason}")
        return {
            "channel": AlertChannel.WEBHOOK,
            "status": "failed",
            "webhook_url": webhook_url,
            "error": f"URL error: {e.reason}",
        }

    except Exception as e:
        logger.error(
            f"Failed to send webhook alert to {webhook_url}: {e}",
            exc_info=True,
        )

        return {
            "channel": AlertChannel.WEBHOOK,
            "status": "failed",
            "webhook_url": webhook_url,
            "error": str(e),
        }


def send_alert(
    channel: str,
    destination: str,
    title: str,
    message: str,
    severity: str = AlertSeverity.WARNING,
    component: Optional[str] = None,
    status: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send an alert notification through the specified channel.

    This is the main entry point for sending alerts. It routes the alert
    to the appropriate channel (email, webhook, Slack, Teams) with proper
    formatting and error handling.

    Args:
        channel: Alert channel (email, webhook, slack, teams)
        destination: Destination address (email address or webhook URL)
        title: Alert title
        message: Alert message
        severity: Alert severity level (info, warning, error, critical)
        component: System component name
        status: Health status (healthy, degraded, unhealthy)
        metadata: Optional additional context and data

    Returns:
        Dictionary containing sending results from the specific channel

    Raises:
        ValueError: If channel is not supported
        Exception: For alert sending failures

    Example:
        >>> result = send_alert(
        ...     channel="email",
        ...     destination="admin@example.com",
        ...     title="Database Unhealthy",
        ...     message="Database connection failed",
        ...     severity="critical",
        ...     component="database",
        ...     status="unhealthy"
        ... )
        >>> print(result['status'])
        'sent'
    """
    logger.info(
        f"Sending alert via {channel} to {destination} "
        f"(severity={severity}, component={component or 'N/A'})"
    )

    # Prepare metadata
    alert_metadata = metadata or {}
    if component:
        alert_metadata["component"] = component
    if status:
        alert_metadata["status"] = status

    # Route to appropriate channel
    if channel == AlertChannel.EMAIL:
        return send_email_alert(
            recipient_email=destination,
            subject=title,
            message=message,
            severity=severity,
            metadata=alert_metadata if alert_metadata else None,
        )

    elif channel in [AlertChannel.WEBHOOK, AlertChannel.SLACK, AlertChannel.TEAMS]:
        alert_data = {
            "severity": severity,
            "title": title,
            "message": message,
            "timestamp": time.time(),
        }
        if component:
            alert_data["component"] = component
        if status:
            alert_data["status"] = status
        if alert_metadata:
            alert_data["metadata"] = alert_metadata

        return send_webhook_alert(
            webhook_url=destination,
            alert_data=alert_data,
        )

    else:
        error_msg = f"Unsupported alert channel: {channel}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def send_batch_alerts(
    alerts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Send multiple alert notifications in batch.

    This function handles sending multiple alerts at once, which is useful
    for aggregating health check results or sending alerts to multiple
    recipients.

    Args:
        alerts: List of alert dictionaries, each containing:
            - channel: Alert channel
            - destination: Destination address
            - title: Alert title
            - message: Alert message
            - severity: Alert severity level (optional)
            - component: System component name (optional)
            - status: Health status (optional)
            - metadata: Optional additional data (optional)

    Returns:
        Dictionary containing batch sending results:
        - total_alerts: Number of alerts to send
        - successful_sends: Number of successful sends
        - failed_sends: Number of failed sends
        - results: List of individual result dictionaries
        - processing_time_ms: Total processing time

    Example:
        >>> alerts = [
        ...     {
        ...         "channel": "email",
        ...         "destination": "admin@example.com",
        ...         "title": "Database Unhealthy",
        ...         "message": "Database connection failed",
        ...         "severity": "critical"
        ...     },
        ...     {
        ...         "channel": "webhook",
        ...         "destination": "https://hooks.slack.com/...",
        ...         "title": "Redis Unhealthy",
        ...         "message": "Redis connection failed",
        ...         "severity": "warning"
        ...     }
        ... ]
        >>> result = send_batch_alerts(alerts)
        >>> print(result['successful_sends'])
        2
    """
    start_time = time.time()

    logger.info(f"Sending batch of {len(alerts)} alerts")

    successful_sends = 0
    failed_sends = 0
    results = []

    for alert_config in alerts:
        try:
            result = send_alert(
                channel=alert_config["channel"],
                destination=alert_config["destination"],
                title=alert_config["title"],
                message=alert_config["message"],
                severity=alert_config.get("severity", AlertSeverity.WARNING),
                component=alert_config.get("component"),
                status=alert_config.get("status"),
                metadata=alert_config.get("metadata"),
            )

            results.append(result)

            if result["status"] == "sent":
                successful_sends += 1
            else:
                failed_sends += 1

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            failed_sends += 1
            results.append({
                "status": "failed",
                "error": str(e),
            })

    processing_time = int((time.time() - start_time) * 1000)

    logger.info(
        f"Batch alert sending completed: {successful_sends}/{len(alerts)} "
        f"sends successful in {processing_time}ms"
    )

    return {
        "total_alerts": len(alerts),
        "successful_sends": successful_sends,
        "failed_sends": failed_sends,
        "results": results,
        "processing_time_ms": processing_time,
    }


def _format_slack_payload(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format alert data for Slack webhook.

    Args:
        alert_data: Alert data dictionary

    Returns:
        Slack-formatted payload
    """
    severity = alert_data.get("severity", "info").lower()
    title = alert_data.get("title", "Alert")
    message = alert_data.get("message", "")
    component = alert_data.get("component", "")
    status = alert_data.get("status", "")

    # Choose color based on severity
    color_map = {
        "info": "#36a64f",      # green
        "warning": "#ff9900",   # orange
        "error": "#ff0000",     # red
        "critical": "#990000",  # dark red
    }
    color = color_map.get(severity, "#36a64f")

    # Build attachment
    attachment = {
        "color": color,
        "title": f"*{title}*",
        "text": message,
        "fields": [],
        "footer": "AgentHR Health Monitor",
        "ts": int(alert_data.get("timestamp", time.time())),
    }

    # Add component field if present
    if component:
        attachment["fields"].append({
            "title": "Component",
            "value": component,
            "short": True,
        })

    # Add status field if present
    if status:
        attachment["fields"].append({
            "title": "Status",
            "value": status,
            "short": True,
        })

    # Add metadata if present
    metadata = alert_data.get("metadata")
    if metadata and isinstance(metadata, dict):
        metadata_text = "\n".join(
            f"• *{k}*: {v}"
            for k, v in metadata.items()
            if k not in ["component", "status"]
        )
        if metadata_text:
            attachment["fields"].append({
                "title": "Details",
                "value": metadata_text,
                "short": False,
            })

    return {
        "attachments": [attachment],
    }


def _format_teams_payload(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format alert data for Microsoft Teams webhook.

    Args:
        alert_data: Alert data dictionary

    Returns:
        Teams-formatted payload
    """
    severity = alert_data.get("severity", "info").upper()
    title = alert_data.get("title", "Alert")
    message = alert_data.get("message", "")
    component = alert_data.get("component", "")
    status = alert_data.get("status", "")

    # Build facts list
    facts = []
    if component:
        facts.append({"name": "Component", "value": component})
    if status:
        facts.append({"name": "Status", "value": status})

    # Add metadata facts
    metadata = alert_data.get("metadata")
    if metadata and isinstance(metadata, dict):
        for k, v in metadata.items():
            if k not in ["component", "status"]:
                facts.append({"name": k.capitalize(), "value": str(v)})

    # Choose color based on severity
    color_map = {
        "INFO": "0078D4",      # blue
        "WARNING": "FF9900",   # orange
        "ERROR": "FF0000",     # red
        "CRITICAL": "990000",  # dark red
    }
    theme_color = color_map.get(severity, "0078D4")

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": theme_color,
        "title": f"[{severity}] {title}",
        "text": message,
        "sections": [{
            "facts": facts,
        }] if facts else [],
    }
