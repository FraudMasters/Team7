"""
BiasAlertConfig model for storing customizable bias alert thresholds and configuration
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class BiasAlertConfig(Base, UUIDMixin, TimestampMixin):
    """
    BiasAlertConfig model for storing customizable bias alert thresholds and configuration

    This model stores configurable alert thresholds for different types of bias metrics,
    allowing administrators to customize when alerts are triggered and how they are
    handled. Supports organization-level and system-wide configurations.

    Attributes:
        id: UUID primary key
        organization_id: Optional foreign key to organization (for multi-tenant support)
        alert_type: Type of bias metric (disparate_impact, statistical_parity, sample_size)
        metric_name: Human-readable name of the metric being monitored
        threshold_value: Threshold value that triggers an alert
        comparison_operator: Operator for threshold comparison (less_than, greater_than, equals)
        severity_level: Severity assigned when threshold is exceeded (low, medium, high, critical)
        is_enabled: Whether this alert configuration is active
        notification_enabled: Whether to send notifications when alert is triggered
        notification_recipients: JSON array of email addresses or user IDs to notify
        demographic_groups: JSON array of demographic groups this config applies to
        description: Human-readable description of this alert configuration
        applies_to_vacancies: JSON array of vacancy IDs this applies to (null = all vacancies)
        alert_frequency: How often to trigger alerts (immediate, daily, weekly)
        cooldown_period_hours: Hours to wait before re-triggering same alert
        auto_acknowledge: Whether to automatically acknowledge alerts after cooldown
        mitigation_recommendations: Suggested actions when alert is triggered
        custom_message_template: Custom message template for notifications
        metadata: JSON object with additional configuration options
    """

    __tablename__ = "bias_alert_configs"

    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Alert identification
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # disparate_impact, statistical_parity, sample_size
    metric_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Human-readable metric name

    # Threshold configuration
    threshold_value: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False
    )
    comparison_operator: Mapped[str] = mapped_column(
        String(20), nullable=False, default="less_than"
    )  # less_than, greater_than, equals, not_equals

    # Alert severity and status
    severity_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Notification settings
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    notification_recipients: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # ["email@example.com", "user_id_123"]

    # Scope and applicability
    demographic_groups: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # ["gender", "age_group", "ethnicity"] or null for all
    applies_to_vacancies: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # ["vacancy_id_1", "vacancy_id_2"] or null for all vacancies

    # Alert behavior
    alert_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="immediate"
    )  # immediate, daily, weekly
    cooldown_period_hours: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=24
    )  # Hours before same alert can re-trigger
    auto_acknowledge: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Guidance and documentation
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    mitigation_recommendations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    custom_message_template: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BiasAlertConfig("
            f"id={self.id}, "
            f"alert_type={self.alert_type}, "
            f"threshold_value={self.threshold_value}, "
            f"severity_level={self.severity_level}, "
            f"is_enabled={self.is_enabled})>"
        )
