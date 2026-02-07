"""
Alerting service for health check notifications.

This module provides a comprehensive alerting framework for sending notifications
when system health checks detect issues. It supports multiple notification channels
including email, Slack, and PagerDuty with configurable alerting rules and cooldowns.

The alerting service supports:
- Multiple notification channels (email, Slack, PagerDuty)
- Alert severity levels (info, warning, critical)
- Configurable cooldown periods to prevent alert fatigue
- Channel-specific configuration and credentials
- Graceful failure handling for notification delivery
- Alert history tracking for debugging

Alert severity levels:
- info: Informational alerts (e.g., system recovered, scheduled maintenance)
- warning: Warning alerts (e.g., degraded performance, high resource usage)
- critical: Critical alerts (e.g., service down, data loss risk)
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any, Dict, List, Optional
from smtplib import SMTP, SMTPException
from urllib.parse import urljoin

import aiohttp

from config import get_settings

logger = logging.getLogger(__name__)

# Global alerting service instance
_alerting_service: Optional["AlertingService"] = None


@dataclass
class Alert:
    """
    Alert data class representing a system alert.

    Attributes:
        title: Short alert title
        message: Detailed alert message
        severity: Alert severity level (info, warning, critical)
        component: Component that generated the alert
        status: Health status that triggered the alert
        details: Additional alert details (metrics, error messages, etc.)
        timestamp: When the alert was generated
        alert_id: Unique identifier for this alert

    Example:
        >>> alert = Alert(
        ...     title="Database Degraded",
        ...     message="Database response time exceeds threshold",
        ...     severity="warning",
        ...     component="database",
        ...     status="degraded"
        ... )
    """

    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_CRITICAL = "critical"

    title: str
    message: str
    severity: str
    component: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    alert_id: Optional[str] = None

    def __post_init__(self):
        """Generate alert ID if not provided."""
        if self.alert_id is None:
            # Generate unique ID based on component, severity, and timestamp
            self.alert_id = f"{self.component}:{self.severity}:{int(self.timestamp.timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to dictionary representation.

        Returns:
            Dictionary with all alert fields
        """
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "component": self.component,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }

    def get_emoji(self) -> str:
        """
        Get emoji icon for alert severity.

        Returns:
            Emoji string representing severity
        """
        emoji_map = {
            self.SEVERITY_INFO: "ℹ️",
            self.SEVERITY_WARNING: "⚠️",
            self.SEVERITY_CRITICAL: "🚨",
        }
        return emoji_map.get(self.severity, "📋")

    def get_color(self) -> str:
        """
        Get color for alert severity (for Slack/HTML formatting).

        Returns:
            Hex color code
        """
        color_map = {
            self.SEVERITY_INFO: "#36a64f",  # green
            self.SEVERITY_WARNING: "#ff9900",  # orange
            self.SEVERITY_CRITICAL: "#ff0000",  # red
        }
        return color_map.get(self.severity, "#cccccc")


class BaseNotificationChannel(ABC):
    """
    Abstract base class for notification channels.

    All notification channels should inherit from this class and implement
    the send() method.

    Attributes:
        enabled: Whether this channel is enabled
        name: Human-readable channel name

    Example:
        >>> class CustomChannel(BaseNotificationChannel):
        ...     async def send(self, alert: Alert) -> bool:
        ...         # Implementation here
        ...         return True
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize the notification channel.

        Args:
            enabled: Whether this channel is enabled
        """
        self.enabled = enabled
        self.name = self.__class__.__name__.replace("Channel", "").replace("Alert", "")

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """
        Send alert notification through this channel.

        This method must be implemented by subclasses.

        Args:
            alert: Alert object containing notification details

        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass

    def is_enabled(self) -> bool:
        """
        Check if this channel is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled


class EmailAlertChannel(BaseNotificationChannel):
    """
    Email notification channel using SMTP.

    Sends alert notifications via email using configured SMTP server.

    Attributes:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_username: SMTP authentication username
        smtp_password: SMTP authentication password
        smtp_use_tls: Whether to use TLS encryption
        from_email: Sender email address
        to_emails: List of recipient email addresses
    """

    def __init__(
        self,
        enabled: bool = True,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_use_tls: Optional[bool] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the email notification channel.

        Args:
            enabled: Whether email alerts are enabled
            smtp_host: SMTP server hostname (defaults to settings)
            smtp_port: SMTP server port (defaults to settings)
            smtp_username: SMTP authentication username (defaults to settings)
            smtp_password: SMTP authentication password (defaults to settings)
            smtp_use_tls: Whether to use TLS (defaults to settings)
            from_email: Sender email address (defaults to settings)
            to_emails: List of recipient email addresses (defaults to settings)
        """
        super().__init__(enabled)

        settings = get_settings()

        # Get SMTP configuration from settings or parameters
        self.smtp_host = smtp_host or getattr(settings, "alert_smtp_host", "localhost")
        self.smtp_port = smtp_port or getattr(settings, "alert_smtp_port", 587)
        self.smtp_username = smtp_username or getattr(settings, "alert_smtp_username", None)
        self.smtp_password = smtp_password or getattr(settings, "alert_smtp_password", None)
        self.smtp_use_tls = smtp_use_tls if smtp_use_tls is not None else getattr(settings, "alert_smtp_use_tls", True)
        self.from_email = from_email or getattr(settings, "alert_email_from", "alerts@agenthr.local")

        # Get recipient emails
        if to_emails:
            self.to_emails = to_emails
        else:
            # Try to get from settings (could be a single email or comma-separated list)
            alert_email = getattr(settings, "health_check_alert_email", None)
            if alert_email:
                self.to_emails = [e.strip() for e in alert_email.split(",")]
            else:
                self.to_emails = ["admin@localhost"]

        # Disable if no recipients configured
        if not self.to_emails or self.to_emails == ["admin@localhost"]:
            logger.warning("No valid email recipients configured, disabling email alerts")
            self.enabled = False

    async def send(self, alert: Alert) -> bool:
        """
        Send alert notification via email.

        Args:
            alert: Alert object containing notification details

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email alerts are disabled, skipping notification")
            return False

        if not self.to_emails:
            logger.warning("No email recipients configured, skipping notification")
            return False

        try:
            # Create email message
            msg = EmailMessage()
            msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            # Build email body
            body = self._build_email_body(alert)
            msg.set_content(body, subtype="html")

            # Send email using SMTP
            with SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email alert sent: {alert.alert_id} to {len(self.to_emails)} recipients")
            return True

        except SMTPException as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email alert: {e}", exc_info=True)
            return False

    def _build_email_body(self, alert: Alert) -> str:
        """
        Build HTML email body from alert details.

        Args:
            alert: Alert object

        Returns:
            HTML email body
        """
        severity_colors = {
            Alert.SEVERITY_INFO: "#36a64f",
            Alert.SEVERITY_WARNING: "#ff9900",
            Alert.SEVERITY_CRITICAL: "#ff0000",
        }
        color = severity_colors.get(alert.severity, "#666666")

        # Build details section
        details_html = ""
        if alert.details:
            details_html = "<h3>Details:</h3><ul>"
            for key, value in alert.details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"

        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">{alert.get_emoji()} {alert.title}</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">Severity: {alert.severity.upper()}</p>
                </div>

                <div style="padding: 20px; background-color: #f9f9f9;">
                    <h2>Alert Details</h2>
                    <p><strong>Component:</strong> {alert.component}</p>
                    <p><strong>Status:</strong> {alert.status}</p>
                    <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><strong>Message:</strong> {alert.message}</p>

                    {details_html}
                </div>

                <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
                    <p>Alert ID: {alert.alert_id}</p>
                    <p>This is an automated message from AgentHR Health Check System</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_body


class SlackAlertChannel(BaseNotificationChannel):
    """
    Slack notification channel using webhook.

    Sends alert notifications to Slack using incoming webhooks.

    Attributes:
        webhook_url: Slack webhook URL
        channel: Slack channel to post to (overrides webhook default)
        username: Bot username for messages
        icon_emoji: Bot icon emoji
    """

    def __init__(
        self,
        enabled: bool = True,
        webhook_url: Optional[str] = None,
        channel: Optional[str] = None,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
    ) -> None:
        """
        Initialize the Slack notification channel.

        Args:
            enabled: Whether Slack alerts are enabled
            webhook_url: Slack webhook URL (defaults to settings)
            channel: Slack channel to post to (overrides webhook default)
            username: Bot username (defaults to settings)
            icon_emoji: Bot icon emoji (defaults to settings)
        """
        super().__init__(enabled)

        settings = get_settings()

        self.webhook_url = webhook_url or getattr(settings, "alert_slack_webhook_url", None)
        self.channel = channel or getattr(settings, "alert_slack_channel", None)
        self.username = username or getattr(settings, "alert_slack_username", "HealthCheck Bot")
        self.icon_emoji = icon_emoji or getattr(settings, "alert_slack_icon_emoji", ":warning:")

        # Disable if no webhook URL configured
        if not self.webhook_url:
            logger.info("No Slack webhook URL configured, disabling Slack alerts")
            self.enabled = False

    async def send(self, alert: Alert) -> bool:
        """
        Send alert notification to Slack.

        Args:
            alert: Alert object containing notification details

        Returns:
            True if message was posted successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack alerts are disabled, skipping notification")
            return False

        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured, skipping notification")
            return False

        try:
            # Build Slack message payload
            payload = self._build_slack_payload(alert)

            # Send to Slack webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.alert_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack webhook returned error {response.status}: {error_text}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack alert: {e}", exc_info=True)
            return False

    def _build_slack_payload(self, alert: Alert) -> Dict[str, Any]:
        """
        Build Slack webhook payload from alert details.

        Args:
            alert: Alert object

        Returns:
            Slack webhook payload dictionary
        """
        # Build fields list
        fields = [
            {"title": "Component", "value": alert.component, "short": True},
            {"title": "Status", "value": alert.status, "short": True},
            {"title": "Severity", "value": alert.severity.upper(), "short": True},
            {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"), "short": True},
        ]

        # Add details as fields if present
        if alert.details:
            for key, value in alert.details.items():
                # Convert value to string and truncate if too long
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                fields.append({"title": key, "value": value_str, "short": True})

        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [
                {
                    "color": alert.get_color(),
                    "title": f"{alert.get_emoji()} {alert.title}",
                    "text": alert.message,
                    "fields": fields,
                    "footer": f"Alert ID: {alert.alert_id}",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ],
        }

        # Override channel if specified
        if self.channel:
            payload["channel"] = self.channel

        return payload


class PagerDutyAlertChannel(BaseNotificationChannel):
    """
    PagerDuty notification channel using Events API v2.

    Sends alert notifications to PagerDuty using the Events API.

    Attributes:
        integration_key: PagerDuty integration key (routing key)
        api_endpoint: PagerDuty Events API endpoint
        dedup_key: Custom deduplication key (auto-generated if not provided)
    """

    # PagerDuty severity levels
    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_ERROR = "error"
    SEVERITY_CRITICAL = "critical"

    # PagerDuty event actions
    ACTION_TRIGGER = "trigger"
    ACTION_ACKNOWLEDGE = "acknowledge"
    ACTION_RESOLVE = "resolve"

    def __init__(
        self,
        enabled: bool = True,
        integration_key: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> None:
        """
        Initialize the PagerDuty notification channel.

        Args:
            enabled: Whether PagerDuty alerts are enabled
            integration_key: PagerDuty integration key (defaults to settings)
            api_endpoint: PagerDuty Events API endpoint (defaults to production)
        """
        super().__init__(enabled)

        settings = get_settings()

        self.integration_key = integration_key or getattr(settings, "alert_pagerduty_integration_key", None)
        self.api_endpoint = api_endpoint or getattr(
            settings,
            "alert_pagerduty_api_endpoint",
            "https://events.pagerduty.com/v2/enqueue",
        )

        # Disable if no integration key configured
        if not self.integration_key:
            logger.info("No PagerDuty integration key configured, disabling PagerDuty alerts")
            self.enabled = False

    async def send(self, alert: Alert) -> bool:
        """
        Send alert notification to PagerDuty.

        Args:
            alert: Alert object containing notification details

        Returns:
            True if event was created successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("PagerDuty alerts are disabled, skipping notification")
            return False

        if not self.integration_key:
            logger.warning("No PagerDuty integration key configured, skipping notification")
            return False

        try:
            # Build PagerDuty event payload
            payload = self._build_event_payload(alert)

            # Send to PagerDuty Events API
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 202:  # 202 = Event accepted
                        logger.info(f"PagerDuty alert sent: {alert.alert_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"PagerDuty API returned error {response.status}: {error_text}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending PagerDuty alert: {e}", exc_info=True)
            return False

    def _build_event_payload(self, alert: Alert) -> Dict[str, Any]:
        """
        Build PagerDuty Events API payload from alert details.

        Args:
            alert: Alert object

        Returns:
            PagerDuty event payload dictionary
        """
        # Map alert severity to PagerDuty severity
        severity_map = {
            Alert.SEVERITY_INFO: self.SEVERITY_INFO,
            Alert.SEVERITY_WARNING: self.SEVERITY_WARNING,
            Alert.SEVERITY_CRITICAL: self.SEVERITY_CRITICAL,
        }
        pd_severity = severity_map.get(alert.severity, self.SEVERITY_ERROR)

        # Build custom details
        custom_details = {
            "component": alert.component,
            "status": alert.status,
            "alert_id": alert.alert_id,
            **alert.details,
        }

        payload = {
            "routing_key": self.integration_key,
            "event_action": self.ACTION_TRIGGER,
            "payload": {
                "summary": f"{alert.component}: {alert.title}",
                "severity": pd_severity,
                "source": "AgentHR Health Check",
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": custom_details,
            },
            "dedup_key": alert.alert_id,  # Use alert_id as dedup key
            "client": "AgentHR",
            "client_url": "https://agenthr.local",
        }

        return payload


class AlertingService:
    """
    Main alerting service that manages notification channels.

    This class provides a unified interface for sending alerts through
    multiple notification channels with configurable cooldown periods.

    Attributes:
        channels: Dictionary of registered notification channels
        enabled: Whether alerting is globally enabled
        cooldown_minutes: Cooldown period between alerts for same component
        alert_on_warning: Send alerts for warning severity
        alert_on_critical: Send alerts for critical severity
        alert_history: Recent alert history for cooldown tracking

    Example:
        >>> service = AlertingService()
        >>> await service.send_alert(alert)
        >>> # Alert sent through all enabled channels
    """

    # Channel names
    CHANNEL_EMAIL = "email"
    CHANNEL_SLACK = "slack"
    CHANNEL_PAGERDUTY = "pagerduty"

    def __init__(
        self,
        enabled: Optional[bool] = None,
        cooldown_minutes: Optional[int] = None,
        alert_on_warning: Optional[bool] = None,
        alert_on_critical: Optional[bool] = None,
        channels: Optional[Dict[str, BaseNotificationChannel]] = None,
    ) -> None:
        """
        Initialize the alerting service.

        Args:
            enabled: Whether alerting is enabled (defaults to settings)
            cooldown_minutes: Cooldown period in minutes (defaults to settings)
            alert_on_warning: Alert on warning severity (defaults to settings)
            alert_on_critical: Alert on critical severity (defaults to settings)
            channels: Custom notification channels (defaults to all built-in channels)
        """
        settings = get_settings()

        self.enabled = enabled if enabled is not None else getattr(settings, "health_check_alert_enabled", True)
        self.cooldown_minutes = cooldown_minutes or getattr(settings, "health_check_alert_cooldown_minutes", 30)
        self.alert_on_warning = alert_on_warning if alert_on_warning is not None else getattr(settings, "health_check_alert_on_warning", True)
        self.alert_on_critical = alert_on_critical if alert_on_critical is not None else getattr(settings, "health_check_alert_on_critical", True)

        # Initialize notification channels
        if channels is None:
            self.channels = {
                self.CHANNEL_EMAIL: EmailAlertChannel(enabled=True),
                self.CHANNEL_SLACK: SlackAlertChannel(enabled=True),
                self.CHANNEL_PAGERDUTY: PagerDutyAlertChannel(enabled=True),
            }
        else:
            self.channels = channels

        # Alert history for cooldown tracking: {component: [(severity, timestamp)]}
        self.alert_history: Dict[str, List[tuple]] = {}

        # Count of enabled channels
        enabled_count = sum(1 for ch in self.channels.values() if ch.enabled)
        logger.info(
            f"AlertingService initialized (enabled={self.enabled}, "
            f"channels={enabled_count}, cooldown={self.cooldown_minutes}m)"
        )

    async def send_alert(self, alert: Alert) -> Dict[str, bool]:
        """
        Send alert through all enabled notification channels.

        Respects cooldown period and severity settings.

        Args:
            alert: Alert object to send

        Returns:
            Dictionary mapping channel names to success status

        Example:
            >>> service = AlertingService()
            >>> alert = Alert(
            ...     title="Database Degraded",
            ...     message="Database slow",
            ...     severity="warning",
            ...     component="database",
            ...     status="degraded"
            ... )
            >>> results = await service.send_alert(alert)
            >>> print(results['email'])
            True
        """
        if not self.enabled:
            logger.debug(f"Alerting is disabled, skipping alert: {alert.alert_id}")
            return {}

        # Check if we should alert based on severity
        if not self._should_alert(alert):
            logger.debug(f"Alert severity '{alert.severity}' not configured for sending: {alert.alert_id}")
            return {}

        # Check cooldown
        if self._is_in_cooldown(alert):
            logger.debug(f"Alert in cooldown period, skipping: {alert.alert_id}")
            return {}

        logger.info(f"Sending alert: {alert.alert_id} ({alert.component}:{alert.severity})")

        # Send alert through all enabled channels
        results = {}
        for channel_name, channel in self.channels.items():
            if channel.enabled:
                try:
                    success = await channel.send(alert)
                    results[channel_name] = success

                    if success:
                        logger.debug(f"Alert sent via {channel_name}: {alert.alert_id}")
                    else:
                        logger.warning(f"Failed to send alert via {channel_name}: {alert.alert_id}")

                except Exception as e:
                    logger.error(f"Error sending alert via {channel_name}: {e}", exc_info=True)
                    results[channel_name] = False
            else:
                logger.debug(f"Channel {channel_name} is disabled, skipping")

        # Record alert in history
        if results:
            self._record_alert(alert)

        return results

    def _should_alert(self, alert: Alert) -> bool:
        """
        Check if alert should be sent based on severity settings.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent, False otherwise
        """
        if alert.severity == Alert.SEVERITY_INFO:
            # Always send info alerts (e.g., recovery notifications)
            return True
        elif alert.severity == Alert.SEVERITY_WARNING:
            return self.alert_on_warning
        elif alert.severity == Alert.SEVERITY_CRITICAL:
            return self.alert_on_critical
        return False

    def _is_in_cooldown(self, alert: Alert) -> bool:
        """
        Check if alert is in cooldown period for this component.

        Args:
            alert: Alert to check

        Returns:
            True if in cooldown, False otherwise
        """
        if alert.component not in self.alert_history:
            return False

        cooldown_expiry = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)

        # Filter out old alerts
        self.alert_history[alert.component] = [
            (severity, timestamp)
            for severity, timestamp in self.alert_history[alert.component]
            if timestamp > cooldown_expiry
        ]

        # Check if there was a recent alert for this component
        return len(self.alert_history[alert.component]) > 0

    def _record_alert(self, alert: Alert) -> None:
        """
        Record alert in history for cooldown tracking.

        Args:
            alert: Alert to record
        """
        if alert.component not in self.alert_history:
            self.alert_history[alert.component] = []

        self.alert_history[alert.component].append((alert.severity, alert.timestamp))

        # Clean old alerts
        cooldown_expiry = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)
        self.alert_history[alert.component] = [
            (severity, timestamp)
            for severity, timestamp in self.alert_history[alert.component]
            if timestamp > cooldown_expiry
        ]

    def register_channel(self, name: str, channel: BaseNotificationChannel) -> None:
        """
        Register a custom notification channel.

        Args:
            name: Name for the channel
            channel: Channel instance

        Example:
            >>> service = AlertingService()
            >>> service.register_channel("custom", CustomChannel())
        """
        self.channels[name] = channel
        logger.info(f"Registered notification channel: {name}")

    def unregister_channel(self, name: str) -> None:
        """
        Unregister a notification channel.

        Args:
            name: Name of the channel to unregister

        Example:
            >>> service = AlertingService()
            >>> service.unregister_channel("slack")
        """
        if name in self.channels:
            del self.channels[name]
            logger.info(f"Unregistered notification channel: {name}")

    def clear_history(self, component: Optional[str] = None) -> None:
        """
        Clear alert history, optionally for a specific component.

        Args:
            component: Component to clear history for (None = all components)

        Example:
            >>> service = AlertingService()
            >>> service.clear_history("database")
        """
        if component:
            if component in self.alert_history:
                del self.alert_history[component]
                logger.debug(f"Cleared alert history for: {component}")
        else:
            self.alert_history.clear()
            logger.debug("Cleared all alert history")

    def get_enabled_channels(self) -> List[str]:
        """
        Get list of enabled channel names.

        Returns:
            List of enabled channel names

        Example:
            >>> service = AlertingService()
            >>> channels = service.get_enabled_channels()
            >>> print(channels)
            ['email', 'slack']
        """
        return [name for name, channel in self.channels.items() if channel.enabled]

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of alerting service.

        Returns:
            Dictionary with health status information

        Example:
            >>> service = AlertingService()
            >>> health = service.health_check()
            >>> print(health['status'])
            'healthy'
        """
        enabled_channels = self.get_enabled_channels()

        return {
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "channels_enabled": len(enabled_channels),
            "channels_total": len(self.channels),
            "channel_names": enabled_channels,
            "cooldown_minutes": self.cooldown_minutes,
            "alert_on_warning": self.alert_on_warning,
            "alert_on_critical": self.alert_on_critical,
            "tracked_components": len(self.alert_history),
        }


def get_alerting_service() -> AlertingService:
    """
    Get or create global alerting service instance.

    Returns:
        Global AlertingService instance

    Example:
        >>> service = get_alerting_service()
        >>> await service.send_alert(alert)
    """
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service


async def send_health_alert(
    component: str,
    status: str,
    severity: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Convenience function to send a health check alert.

    Args:
        component: Component that generated the alert
        status: Health status (healthy, degraded, unhealthy)
        severity: Alert severity (info, warning, critical)
        message: Alert message (auto-generated if not provided)
        details: Additional alert details

    Returns:
        Dictionary mapping channel names to success status

    Example:
        >>> await send_health_alert(
        ...     component="database",
        ...     status="degraded",
        ...     severity="warning",
        ...     message="Database response time high"
        ... )
    """
    # Generate alert title and message if not provided
    if message is None:
        status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(status, "📋")
        message = f"{status_emoji} Component {component} is {status}"

    title = f"{component.title()} Status: {status.title()}"

    # Create alert
    alert = Alert(
        title=title,
        message=message,
        severity=severity,
        component=component,
        status=status,
        details=details or {},
    )

    # Get alerting service and send alert
    service = get_alerting_service()
    return await service.send_alert(alert)


__all__ = [
    "Alert",
    "BaseNotificationChannel",
    "EmailAlertChannel",
    "SlackAlertChannel",
    "PagerDutyAlertChannel",
    "AlertingService",
    "get_alerting_service",
    "send_health_alert",
]
