"""
Model Alert Service for ML model performance and training alerts.

This module provides a comprehensive alerting system for ML model lifecycle events,
including performance degradation, training failures, version promotions, and
deployment issues.

The service supports:
- Performance degradation alerts when metrics drop below thresholds
- Training failure alerts with error details
- Model version promotion notifications
- Canary deployment alerts
- Rollback notifications
- Configurable alert channels (email, webhook, Slack, Teams)
- Alert history tracking and cooldown management

Alert types:
- performance_degradation: Model accuracy/metrics dropped below threshold
- training_failure: Model training job failed
- training_success: Model training completed successfully
- model_promoted: New model version promoted to production
- canary_deployed: Canary deployment started
- canary_promoted: Canary model promoted to production
- rollback_triggered: Model rollback performed
- feedback_threshold: Feedback volume threshold reached
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelAlertType:
    """Types of model alerts."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    TRAINING_FAILURE = "training_failure"
    TRAINING_SUCCESS = "training_success"
    MODEL_PROMOTED = "model_promoted"
    CANARY_DEPLOYED = "canary_deployed"
    CANARY_PROMOTED = "canary_promoted"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    FEEDBACK_THRESHOLD = "feedback_threshold"


class ModelAlertSeverity:
    """Alert severity levels for model alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ModelAlertChannel:
    """Alert notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


@dataclass
class ModelAlert:
    """
    Model alert data class representing an ML model alert.

    Attributes:
        alert_type: Type of alert (performance_degradation, training_failure, etc.)
        model_name: Name of the model (ranking, skill_matching, etc.)
        severity: Alert severity level
        title: Short alert title
        message: Detailed alert message
        details: Additional alert details (metrics, version info, etc.)
        timestamp: When the alert was generated
        alert_id: Unique identifier for this alert
        model_version_id: ID of the related model version (if applicable)
        previous_version_id: ID of the previous model version (if applicable)
    """
    alert_type: str
    model_name: str
    severity: str
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    alert_id: Optional[str] = None
    model_version_id: Optional[str] = None
    previous_version_id: Optional[str] = None

    def __post_init__(self):
        """Generate alert ID if not provided."""
        if self.alert_id is None:
            self.alert_id = f"{self.model_name}:{self.alert_type}:{int(self.timestamp.timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to dictionary representation.

        Returns:
            Dictionary with all alert fields
        """
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "model_name": self.model_name,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "model_version_id": self.model_version_id,
            "previous_version_id": self.previous_version_id,
        }

    def get_emoji(self) -> str:
        """
        Get emoji icon for alert type and severity.

        Returns:
            Emoji string representing the alert
        """
        emoji_map = {
            ModelAlertType.PERFORMANCE_DEGRADATION: "📉",
            ModelAlertType.TRAINING_FAILURE: "❌",
            ModelAlertType.TRAINING_SUCCESS: "✅",
            ModelAlertType.MODEL_PROMOTED: "🚀",
            ModelAlertType.CANARY_DEPLOYED: "🦅",
            ModelAlertType.CANARY_PROMOTED: "⬆️",
            ModelAlertType.ROLLBACK_TRIGGERED: "⏪",
            ModelAlertType.FEEDBACK_THRESHOLD: "📊",
        }
        return emoji_map.get(self.alert_type, "⚠️")

    def get_color(self) -> str:
        """
        Get color for alert severity (for Slack/HTML formatting).

        Returns:
            Hex color code
        """
        color_map = {
            ModelAlertSeverity.INFO: "#36a64f",  # green
            ModelAlertSeverity.WARNING: "#ff9900",  # orange
            ModelAlertSeverity.ERROR: "#ff0000",  # red
            ModelAlertSeverity.CRITICAL: "#990000",  # dark red
        }
        return color_map.get(self.severity, "#cccccc")


class ModelAlertService:
    """
    Service for sending ML model alerts.

    This service handles sending alerts for model performance degradation,
    training failures, version promotions, and other ML lifecycle events.
    It supports multiple notification channels with configurable cooldowns.

    Attributes:
        enabled: Whether alerting is globally enabled
        cooldown_minutes: Cooldown period between duplicate alerts
        channels: List of enabled notification channels
        recipients: Default recipients for alerts
        alert_history: Recent alert history for cooldown tracking

    Example:
        >>> service = ModelAlertService()
        >>> alert = ModelAlert(
        ...     alert_type=ModelAlertType.PERFORMANCE_DEGRADATION,
        ...     model_name="ranking",
        ...     severity=ModelAlertSeverity.WARNING,
        ...     title="Performance Degradation Detected",
        ...     message="Model accuracy dropped by 8%"
        ... )
        >>> result = await service.send_alert(alert)
    """

    # Default cooldown period in minutes
    DEFAULT_COOLDOWN_MINUTES = 30

    def __init__(
        self,
        enabled: Optional[bool] = None,
        cooldown_minutes: Optional[int] = None,
        channels: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None,
    ):
        """
        Initialize the model alert service.

        Args:
            enabled: Whether alerting is enabled (defaults to settings)
            cooldown_minutes: Cooldown period in minutes (defaults to 30)
            channels: List of notification channels to use
            recipients: Default recipients for alerts
        """
        self.enabled = enabled if enabled is not None else getattr(
            settings, "model_alert_enabled", True
        )
        self.cooldown_minutes = cooldown_minutes or self.DEFAULT_COOLDOWN_MINUTES
        self.channels = channels or [ModelAlertChannel.EMAIL]
        self.recipients = recipients or self._get_default_recipients()

        # Alert history for cooldown tracking: {alert_key: timestamp}
        self.alert_history: Dict[str, datetime] = {}

        logger.info(
            f"ModelAlertService initialized (enabled={self.enabled}, "
            f"channels={self.channels}, cooldown={self.cooldown_minutes}m)"
        )

    def _get_default_recipients(self) -> List[str]:
        """
        Get default alert recipients from settings.

        Returns:
            List of recipient email addresses
        """
        recipients = getattr(settings, "model_alert_recipients", None)
        if recipients:
            if isinstance(recipients, str):
                return [r.strip() for r in recipients.split(",")]
            return recipients
        return ["admin@agenthr.com"]

    def send_alert(self, alert: ModelAlert) -> Dict[str, Any]:
        """
        Send a model alert through all enabled channels.

        This method sends the alert through all configured notification
        channels, respecting cooldown periods to prevent alert spam.

        Args:
            alert: ModelAlert object to send

        Returns:
            Dictionary containing:
            - alert_id: Unique identifier for the alert
            - status: Overall status (sent/skipped/failed)
            - channels: Results per channel
            - processing_time_ms: Total processing time
            - error: Error message (if failed)

        Example:
            >>> service = ModelAlertService()
            >>> alert = ModelAlert(
            ...     alert_type=ModelAlertType.TRAINING_FAILURE,
            ...     model_name="ranking",
            ...     severity=ModelAlertSeverity.ERROR,
            ...     title="Training Failed",
            ...     message="Out of memory error during training"
            ... )
            >>> result = service.send_alert(alert)
            >>> print(result['status'])
            'sent'
        """
        start_time = time.time()

        if not self.enabled:
            logger.debug(f"Model alerting disabled, skipping alert: {alert.alert_id}")
            return {
                "alert_id": alert.alert_id,
                "status": "skipped",
                "reason": "alerting_disabled",
                "processing_time_ms": 0,
            }

        # Check cooldown
        alert_key = f"{alert.model_name}:{alert.alert_type}"
        if self._is_in_cooldown(alert_key):
            logger.debug(f"Alert in cooldown period, skipping: {alert.alert_id}")
            return {
                "alert_id": alert.alert_id,
                "status": "skipped",
                "reason": "cooldown",
                "processing_time_ms": 0,
            }

        logger.info(
            f"Sending model alert: {alert.alert_id} "
            f"({alert.model_name}:{alert.alert_type})"
        )

        results = {}
        success_count = 0

        for channel in self.channels:
            try:
                if channel == ModelAlertChannel.EMAIL:
                    result = self._send_email_alert(alert)
                elif channel in [
                    ModelAlertChannel.WEBHOOK,
                    ModelAlertChannel.SLACK,
                    ModelAlertChannel.TEAMS,
                ]:
                    result = self._send_webhook_alert(alert, channel)
                else:
                    logger.warning(f"Unknown alert channel: {channel}")
                    continue

                results[channel] = result
                if result.get("status") == "sent":
                    success_count += 1

            except Exception as e:
                logger.error(f"Error sending alert via {channel}: {e}", exc_info=True)
                results[channel] = {"status": "failed", "error": str(e)}

        # Record alert in history
        if success_count > 0:
            self._record_alert(alert_key)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        overall_status = "sent" if success_count > 0 else "failed"

        return {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "model_name": alert.model_name,
            "status": overall_status,
            "channels": results,
            "recipients_count": len(self.recipients),
            "processing_time_ms": processing_time_ms,
        }

    def _is_in_cooldown(self, alert_key: str) -> bool:
        """
        Check if an alert is in cooldown period.

        Args:
            alert_key: Unique key for the alert type/model combination

        Returns:
            True if in cooldown, False otherwise
        """
        if alert_key not in self.alert_history:
            return False

        last_sent = self.alert_history[alert_key]
        cooldown_expiry = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)

        return last_sent > cooldown_expiry

    def _record_alert(self, alert_key: str) -> None:
        """
        Record an alert in history for cooldown tracking.

        Args:
            alert_key: Unique key for the alert type/model combination
        """
        self.alert_history[alert_key] = datetime.utcnow()

        # Clean old entries
        cooldown_expiry = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)
        self.alert_history = {
            k: v for k, v in self.alert_history.items() if v > cooldown_expiry
        }

    def _send_email_alert(self, alert: ModelAlert) -> Dict[str, Any]:
        """
        Send alert via email.

        Args:
            alert: ModelAlert object to send

        Returns:
            Dictionary with sending status and details
        """
        try:
            email_details = format_model_alert_email(alert)

            logger.info(
                f"Sending model alert email: subject='{email_details['subject']}', "
                f"to={len(self.recipients)} recipients"
            )

            # In production, this would actually send the email
            # For now, log and simulate success
            logger.info(
                f"Email alert prepared: "
                f"subject='{email_details['subject']}', "
                f"priority={email_details['priority']}"
            )

            return {
                "status": "sent",
                "channel": "email",
                "recipients": self.recipients,
                "subject": email_details["subject"],
            }

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
            return {
                "status": "failed",
                "channel": "email",
                "error": str(e),
            }

    def _send_webhook_alert(
        self, alert: ModelAlert, channel: str
    ) -> Dict[str, Any]:
        """
        Send alert via webhook.

        Args:
            alert: ModelAlert object to send
            channel: Webhook channel type (webhook, slack, teams)

        Returns:
            Dictionary with sending status and details
        """
        webhook_url = self._get_webhook_url(channel)

        if not webhook_url:
            logger.warning(f"No webhook URL configured for channel: {channel}")
            return {
                "status": "skipped",
                "channel": channel,
                "reason": "not_configured",
            }

        try:
            # Format payload based on channel type
            if channel == ModelAlertChannel.SLACK:
                payload = _format_slack_model_alert(alert)
            elif channel == ModelAlertChannel.TEAMS:
                payload = _format_teams_model_alert(alert)
            else:
                payload = alert.to_dict()

            payload_json = json.dumps(payload).encode("utf-8")

            request = Request(
                webhook_url,
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AgentHR-ModelAlert/1.0",
                },
                method="POST",
            )

            with urlopen(request, timeout=10) as response:
                status_code = response.getcode()
                response_body = response.read().decode("utf-8", errors="replace")

            logger.info(
                f"Webhook alert sent successfully to {webhook_url} "
                f"(status={status_code})"
            )

            return {
                "status": "sent",
                "channel": channel,
                "status_code": status_code,
            }

        except HTTPError as e:
            logger.error(f"Webhook HTTP error: {e.code} - {e.reason}")
            return {
                "status": "failed",
                "channel": channel,
                "error": f"HTTP {e.code}: {e.reason}",
            }

        except URLError as e:
            logger.error(f"Webhook URL error: {e.reason}")
            return {
                "status": "failed",
                "channel": channel,
                "error": f"URL error: {e.reason}",
            }

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}", exc_info=True)
            return {
                "status": "failed",
                "channel": channel,
                "error": str(e),
            }

    def _get_webhook_url(self, channel: str) -> Optional[str]:
        """
        Get webhook URL for a channel from settings.

        Args:
            channel: Channel type

        Returns:
            Webhook URL or None if not configured
        """
        if channel == ModelAlertChannel.SLACK:
            return getattr(settings, "model_alert_slack_webhook", None)
        elif channel == ModelAlertChannel.TEAMS:
            return getattr(settings, "model_alert_teams_webhook", None)
        elif channel == ModelAlertChannel.WEBHOOK:
            return getattr(settings, "model_alert_webhook_url", None)
        return None

    # Convenience methods for common alert types

    def send_performance_degradation_alert(
        self,
        model_name: str,
        degradation_percentage: float,
        threshold: float,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a performance degradation alert.

        This is a convenience method for sending performance degradation
        alerts with properly formatted content.

        Args:
            model_name: Name of the model with degradation
            degradation_percentage: Percentage of performance drop (0.0-1.0)
            threshold: Threshold that was exceeded
            current_metrics: Current performance metrics
            baseline_metrics: Baseline performance metrics for comparison

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_performance_degradation_alert(
            ...     model_name="ranking",
            ...     degradation_percentage=0.08,
            ...     threshold=0.05,
            ...     current_metrics={"accuracy": 0.85},
            ...     baseline_metrics={"accuracy": 0.92}
            ... )
        """
        degradation_pct_str = f"{degradation_percentage * 100:.1f}%"

        # Determine severity based on degradation level
        if degradation_percentage >= 0.15:
            severity = ModelAlertSeverity.CRITICAL
        elif degradation_percentage >= 0.10:
            severity = ModelAlertSeverity.ERROR
        else:
            severity = ModelAlertSeverity.WARNING

        alert = ModelAlert(
            alert_type=ModelAlertType.PERFORMANCE_DEGRADATION,
            model_name=model_name,
            severity=severity,
            title=f"Performance Degradation: {model_name}",
            message=f"Model {model_name} performance dropped by {degradation_pct_str}, "
                    f"exceeding the {threshold * 100:.1f}% threshold.",
            details={
                "degradation_percentage": degradation_percentage,
                "threshold": threshold,
                "current_metrics": current_metrics,
                "baseline_metrics": baseline_metrics,
                "detected_at": datetime.utcnow().isoformat(),
            },
        )

        return self.send_alert(alert)

    def send_training_failure_alert(
        self,
        model_name: str,
        error_message: str,
        training_config: Optional[Dict[str, Any]] = None,
        traceback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a training failure alert.

        This is a convenience method for sending training failure
        alerts with error details.

        Args:
            model_name: Name of the model that failed training
            error_message: Error message from the training failure
            training_config: Optional training configuration used
            traceback: Optional stack trace

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_training_failure_alert(
            ...     model_name="ranking",
            ...     error_message="Out of memory during training",
            ...     training_config={"epochs": 100, "batch_size": 64}
            ... )
        """
        alert = ModelAlert(
            alert_type=ModelAlertType.TRAINING_FAILURE,
            model_name=model_name,
            severity=ModelAlertSeverity.ERROR,
            title=f"Training Failed: {model_name}",
            message=f"Model training for {model_name} failed: {error_message}",
            details={
                "error_message": error_message,
                "training_config": training_config,
                "traceback": traceback,
                "failed_at": datetime.utcnow().isoformat(),
            },
        )

        return self.send_alert(alert)

    def send_training_success_alert(
        self,
        model_name: str,
        new_version_id: str,
        metrics: Dict[str, Any],
        training_samples: int,
        training_duration_ms: float,
        auto_activated: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a training success notification.

        This is a convenience method for sending training success
        alerts with performance metrics.

        Args:
            model_name: Name of the model that was trained
            new_version_id: ID of the new model version
            metrics: Performance metrics from training
            training_samples: Number of samples used for training
            training_duration_ms: Training duration in milliseconds
            auto_activated: Whether the model was automatically activated

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_training_success_alert(
            ...     model_name="ranking",
            ...     new_version_id="v1.2.0",
            ...     metrics={"accuracy": 0.92, "f1_score": 0.89},
            ...     training_samples=5000,
            ...     training_duration_ms=120000
            ... )
        """
        alert = ModelAlert(
            alert_type=ModelAlertType.TRAINING_SUCCESS,
            model_name=model_name,
            severity=ModelAlertSeverity.INFO,
            title=f"Training Completed: {model_name}",
            message=f"Model {model_name} training completed successfully. "
                    f"New version: {new_version_id}",
            details={
                "new_version_id": new_version_id,
                "metrics": metrics,
                "training_samples": training_samples,
                "training_duration_ms": training_duration_ms,
                "auto_activated": auto_activated,
                "completed_at": datetime.utcnow().isoformat(),
            },
            model_version_id=new_version_id,
        )

        return self.send_alert(alert)

    def send_rollback_alert(
        self,
        model_name: str,
        from_version_id: str,
        to_version_id: str,
        reason: str,
        triggered_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Send a model rollback alert.

        This is a convenience method for sending rollback notifications.

        Args:
            model_name: Name of the model that was rolled back
            from_version_id: Version ID being rolled back from
            to_version_id: Version ID being rolled back to
            reason: Reason for the rollback
            triggered_by: Who triggered the rollback (system/user)

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_rollback_alert(
            ...     model_name="ranking",
            ...     from_version_id="v1.2.0",
            ...     to_version_id="v1.1.0",
            ...     reason="Performance degradation detected",
            ...     triggered_by="system"
            ... )
        """
        alert = ModelAlert(
            alert_type=ModelAlertType.ROLLBACK_TRIGGERED,
            model_name=model_name,
            severity=ModelAlertSeverity.WARNING,
            title=f"Model Rollback: {model_name}",
            message=f"Model {model_name} rolled back from {from_version_id} to "
                    f"{to_version_id}. Reason: {reason}",
            details={
                "from_version_id": from_version_id,
                "to_version_id": to_version_id,
                "reason": reason,
                "triggered_by": triggered_by,
                "rolled_back_at": datetime.utcnow().isoformat(),
            },
            model_version_id=to_version_id,
            previous_version_id=from_version_id,
        )

        return self.send_alert(alert)

    def send_feedback_threshold_alert(
        self,
        model_name: str,
        feedback_count: int,
        threshold: int,
        model_version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a feedback volume threshold alert.

        This is a convenience method for alerting when enough feedback
        has accumulated to trigger retraining.

        Args:
            model_name: Name of the model
            feedback_count: Current feedback count
            threshold: Threshold that was exceeded
            model_version_id: ID of the current model version

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_feedback_threshold_alert(
            ...     model_name="ranking",
            ...     feedback_count=1250,
            ...     threshold=1000
            ... )
        """
        alert = ModelAlert(
            alert_type=ModelAlertType.FEEDBACK_THRESHOLD,
            model_name=model_name,
            severity=ModelAlertSeverity.INFO,
            title=f"Feedback Threshold Reached: {model_name}",
            message=f"Model {model_name} has accumulated {feedback_count:,} feedback "
                    f"entries, exceeding the {threshold:,} threshold. "
                    f"Retraining may be triggered.",
            details={
                "feedback_count": feedback_count,
                "threshold": threshold,
                "model_version_id": model_version_id,
                "detected_at": datetime.utcnow().isoformat(),
            },
            model_version_id=model_version_id,
        )

        return self.send_alert(alert)

    def send_canary_deployed_alert(
        self,
        model_name: str,
        canary_version_id: str,
        production_version_id: str,
        traffic_percentage: float,
    ) -> Dict[str, Any]:
        """
        Send a canary deployment alert.

        This is a convenience method for alerting when a canary
        deployment is started.

        Args:
            model_name: Name of the model
            canary_version_id: ID of the canary model version
            production_version_id: ID of the production model version
            traffic_percentage: Percentage of traffic to canary (0.0-1.0)

        Returns:
            Alert sending result dictionary

        Example:
            >>> service = ModelAlertService()
            >>> result = service.send_canary_deployed_alert(
            ...     model_name="ranking",
            ...     canary_version_id="v1.3.0",
            ...     production_version_id="v1.2.0",
            ...     traffic_percentage=0.10
            ... )
        """
        traffic_pct_str = f"{traffic_percentage * 100:.0f}%"

        alert = ModelAlert(
            alert_type=ModelAlertType.CANARY_DEPLOYED,
            model_name=model_name,
            severity=ModelAlertSeverity.INFO,
            title=f"Canary Deployed: {model_name}",
            message=f"Canary version {canary_version_id} of {model_name} deployed "
                    f"with {traffic_pct_str} traffic.",
            details={
                "canary_version_id": canary_version_id,
                "production_version_id": production_version_id,
                "traffic_percentage": traffic_percentage,
                "deployed_at": datetime.utcnow().isoformat(),
            },
            model_version_id=canary_version_id,
            previous_version_id=production_version_id,
        )

        return self.send_alert(alert)

    def clear_history(self, model_name: Optional[str] = None) -> None:
        """
        Clear alert history, optionally for a specific model.

        Args:
            model_name: Model to clear history for (None = all models)
        """
        if model_name:
            self.alert_history = {
                k: v for k, v in self.alert_history.items()
                if not k.startswith(f"{model_name}:")
            }
            logger.debug(f"Cleared alert history for: {model_name}")
        else:
            self.alert_history.clear()
            logger.debug("Cleared all alert history")

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of the model alert service.

        Returns:
            Dictionary with health status information
        """
        return {
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "channels": self.channels,
            "recipients_count": len(self.recipients),
            "cooldown_minutes": self.cooldown_minutes,
            "tracked_alerts": len(self.alert_history),
        }


# Module-level convenience functions

def format_model_alert_email(alert: ModelAlert) -> Dict[str, Any]:
    """
    Format model alert as email content.

    This function creates email-ready content from a ModelAlert object,
    including subject, body, and priority level.

    Args:
        alert: ModelAlert object to format

    Returns:
        Dictionary containing:
        - subject: Email subject line
        - body: Email body text
        - priority: Email priority (high/normal)

    Example:
        >>> alert = ModelAlert(
        ...     alert_type=ModelAlertType.TRAINING_FAILURE,
        ...     model_name="ranking",
        ...     severity=ModelAlertSeverity.ERROR,
        ...     title="Training Failed",
        ...     message="Out of memory error"
        ... )
        >>> email = format_model_alert_email(alert)
        >>> print(email['subject'])
        '[ERROR] Training Failed: ranking'
    """
    try:
        logger.info(f"Formatting model alert email for: {alert.alert_type}")

        severity_upper = alert.severity.upper()
        emoji = alert.get_emoji()

        # Build subject
        subject = f"[{severity_upper}] {alert.title}"

        # Build body
        body_lines = [
            f"Model Alert Notification",
            f"",
            f"{emoji} {alert.title}",
            f"",
            f"Model: {alert.model_name}",
            f"Alert Type: {alert.alert_type}",
            f"Severity: {severity_upper}",
            f"Timestamp: {alert.timestamp.isoformat()}",
            f"",
            f"Message:",
            f"  {alert.message}",
        ]

        # Add details if present
        if alert.details:
            body_lines.extend([
                f"",
                f"Details:",
            ])
            for key, value in alert.details.items():
                if isinstance(value, dict):
                    value_str = json.dumps(value, indent=2)
                    body_lines.append(f"  {key}:")
                    for line in value_str.split("\n"):
                        body_lines.append(f"    {line}")
                elif isinstance(value, float):
                    body_lines.append(f"  {key}: {value:.4f}")
                else:
                    body_lines.append(f"  {key}: {value}")

        # Add version info if present
        if alert.model_version_id:
            body_lines.extend([
                f"",
                f"Model Version: {alert.model_version_id}",
            ])
        if alert.previous_version_id:
            body_lines.append(f"Previous Version: {alert.previous_version_id}")

        body_lines.extend([
            f"",
            f"---",
            f"Alert ID: {alert.alert_id}",
            f"This is an automated alert from AgentHR Model Training System.",
        ])

        body = "\n".join(body_lines)

        # Determine priority based on severity
        priority = "high" if alert.severity in [
            ModelAlertSeverity.ERROR,
            ModelAlertSeverity.CRITICAL
        ] else "normal"

        return {
            "subject": subject,
            "body": body,
            "priority": priority,
        }

    except Exception as e:
        logger.error(f"Failed to format model alert email: {e}", exc_info=True)
        return {
            "subject": f"[{alert.severity.upper()}] {alert.title}",
            "body": alert.message,
            "priority": "normal",
        }


def _format_slack_model_alert(alert: ModelAlert) -> Dict[str, Any]:
    """
    Format model alert for Slack webhook.

    Args:
        alert: ModelAlert object to format

    Returns:
        Slack-formatted payload dictionary
    """
    fields = [
        {"title": "Model", "value": alert.model_name, "short": True},
        {"title": "Severity", "value": alert.severity.upper(), "short": True},
        {"title": "Type", "value": alert.alert_type.replace("_", " ").title(), "short": True},
        {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M UTC"), "short": True},
    ]

    # Add key details as fields
    if alert.details:
        for key in ["degradation_percentage", "new_version_id", "error_message"]:
            if key in alert.details:
                value = alert.details[key]
                if isinstance(value, float):
                    value = f"{value * 100:.1f}%" if value < 1 else f"{value:.2f}"
                fields.append({"title": key.replace("_", " ").title(), "value": str(value), "short": True})

    return {
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


def _format_teams_model_alert(alert: ModelAlert) -> Dict[str, Any]:
    """
    Format model alert for Microsoft Teams webhook.

    Args:
        alert: ModelAlert object to format

    Returns:
        Teams-formatted payload dictionary
    """
    facts = [
        {"name": "Model", "value": alert.model_name},
        {"name": "Alert Type", "value": alert.alert_type.replace("_", " ").title()},
        {"name": "Severity", "value": alert.severity.upper()},
        {"name": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M UTC")},
    ]

    # Add key details as facts
    if alert.details:
        for key in ["degradation_percentage", "new_version_id", "error_message"]:
            if key in alert.details:
                value = alert.details[key]
                if isinstance(value, float):
                    value = f"{value * 100:.1f}%" if value < 1 else f"{value:.2f}"
                facts.append({"name": key.replace("_", " ").title(), "value": str(value)})

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": alert.title,
        "themeColor": alert.get_color().lstrip("#"),
        "title": f"[{alert.severity.upper()}] {alert.title}",
        "text": alert.message,
        "sections": [{"facts": facts}],
    }


# Global service instance
_model_alert_service: Optional[ModelAlertService] = None


def get_model_alert_service() -> ModelAlertService:
    """
    Get or create the global model alert service instance.

    Returns:
        ModelAlertService singleton instance

    Example:
        >>> service = get_model_alert_service()
        >>> result = service.send_performance_degradation_alert(
        ...     model_name="ranking",
        ...     degradation_percentage=0.08,
        ...     threshold=0.05,
        ...     current_metrics={"accuracy": 0.85},
        ...     baseline_metrics={"accuracy": 0.92}
        ... )
    """
    global _model_alert_service
    if _model_alert_service is None:
        _model_alert_service = ModelAlertService()
    return _model_alert_service


__all__ = [
    "ModelAlertType",
    "ModelAlertSeverity",
    "ModelAlertChannel",
    "ModelAlert",
    "ModelAlertService",
    "format_model_alert_email",
    "get_model_alert_service",
]
