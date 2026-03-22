"""
AuditAlertConfig model for configuring alert rules for suspicious audit log patterns
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AlertType(str, enum.Enum):
    """Types of audit alerts that can be configured"""

    # Authentication alerts
    FAILED_LOGINS = "failed_logins"
    MULTIPLE_LOGIN_LOCATIONS = "multiple_login_locations"
    SUSPICIOUS_LOGIN = "suspicious_login"

    # Data access alerts
    BULK_DATA_EXPORT = "bulk_data_export"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    EXCESSIVE_DATA_QUERIES = "excessive_data_queries"

    # Permission and access alerts
    PERMISSION_CHANGES = "permission_changes"
    ROLE_CHANGES = "role_changes"
    USER_DELETED = "user_deleted"
    USER_CREATED = "user_created"

    # System alerts
    CONFIGURATION_CHANGES = "configuration_changes"
    BACKUP_OPERATIONS = "backup_operations"
    SYSTEM_SETTINGS_CHANGED = "system_settings_changed"

    # Security alerts
    IP_BLOCKED = "ip_blocked"
    SESSION_HIJACKING = "session_hijacking"
    UNUSUAL_ACTIVITY_PATTERN = "unusual_activity_pattern"


class AlertSeverity(str, enum.Enum):
    """Severity levels for audit alerts"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditAlertConfig(Base, UUIDMixin, TimestampMixin):
    """
    AuditAlertConfig model for configuring alert rules for suspicious audit log patterns

    This model defines rules for detecting suspicious patterns in audit logs and triggering
    alerts when thresholds are exceeded. Alert rules can be scoped to specific organizations
    or applied globally. Each rule defines what to monitor, the threshold for triggering,
    and who should be notified.

    Attributes:
        id: UUID primary key
        name: Human-readable name for the alert rule
        alert_type: Type of alert to monitor (failed_logins, bulk_export, etc.)
        description: Detailed description of what this alert monitors
        enabled: Whether this alert rule is currently active
        severity: Severity level of the alert (info, warning, error, critical)
        organization_id: Organization this rule applies to (null for global rules)
        threshold: Numeric threshold that triggers the alert
        time_window_minutes: Time window in minutes for threshold evaluation
        action_types: JSON list of AuditActionType values to monitor (null for all)
        recipients: JSON object with notification recipients (emails, webhooks, slack)
        alert_config: JSON object with additional alert-specific configuration
        cooldown_minutes: Minutes to wait before sending another alert of the same type
        last_triggered_at: ISO timestamp when this alert was last triggered
        trigger_count: Number of times this alert has been triggered
        created_by: UUID of user who created this alert rule
        updated_by: UUID of user who last updated this alert rule
        created_at: Timestamp when the rule was created (inherited)
        updated_at: Timestamp when the rule was last updated (inherited)
    """

    __tablename__ = "audit_alert_configs"

    # Core alert configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alert_type: Mapped[AlertType] = mapped_column(
        String(50), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        String(20), nullable=False, default=AlertSeverity.WARNING, index=True
    )

    # Organization scope
    organization_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)

    # Threshold and time window configuration
    threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5,
        comment="Numeric threshold that triggers the alert"
    )
    time_window_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10,
        comment="Time window in minutes for threshold evaluation"
    )

    # Action filtering
    action_types: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True,
        comment="List of AuditActionType values to monitor (null for all)"
    )

    # Notification configuration
    recipients: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Notification recipients: {emails: [], webhooks: [], slack_channels: []}"
    )
    alert_config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Additional alert-specific configuration and metadata"
    )

    # Alert throttling and tracking
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60,
        comment="Minutes to wait before sending another alert of the same type"
    )
    last_triggered_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trigger_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of times this alert has been triggered"
    )

    # Audit trail for the configuration itself
    created_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        org_id = f"org={self.organization_id}" if self.organization_id else "global"
        return f"<AuditAlertConfig(id={self.id}, name={self.name}, type={self.alert_type}, {status}, {org_id})>"
