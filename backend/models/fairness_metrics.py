"""
FairnessMetrics model for storing AI bias analysis and fairness monitoring results
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class FairnessMetrics(Base, UUIDMixin, TimestampMixin):
    """
    FairnessMetrics model for storing AI bias analysis and fairness monitoring results

    This model stores fairness metrics calculated from ranking outcomes to detect
    demographic bias across groups (gender, age, ethnicity indicators inferred from
    resume patterns). Enables compliance monitoring and bias alerting.

    Attributes:
        id: UUID primary key
        vacancy_id: Foreign key to JobVacancy
        model_version_id: Foreign key to MLModelVersion
        analysis_date: Date of the fairness analysis
        demographic_group: Demographic attribute analyzed (gender, age_group, ethnicity)
        disparate_impact_ratio: Ratio of selection rates between groups (1.0 = fair, <0.8 = potential bias)
        statistical_parity_difference: Difference in selection rates between groups
        group_selection_rate: Selection rate for the demographic group
        overall_selection_rate: Overall selection rate across all candidates
        group_sample_size: Number of candidates in the demographic group
        total_sample_size: Total number of candidates analyzed
        alert_threshold: Threshold that triggers bias alerts
        alert_triggered: Whether bias threshold was exceeded
        alert_severity: Severity of bias alert (low, medium, high, critical)
        group_metrics: JSON object with detailed metrics per demographic subgroup
        mitigation_suggested: Recommended actions to reduce bias
        is_fairness_aware: Whether fairness-aware ranking was enabled
        analysis_metadata: JSON object with analysis details (methodology, confidence, etc.)
    """

    __tablename__ = "fairness_metrics"

    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    model_version_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("ml_model_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Analysis metadata
    analysis_date: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    demographic_group: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # gender, age_group, ethnicity

    # Core fairness metrics
    disparate_impact_ratio: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )  # Ratio of selection rates (1.0 = fair)
    statistical_parity_difference: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )  # Difference in selection rates
    group_selection_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    overall_selection_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # Sample sizes
    group_sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    total_sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Alert configuration
    alert_threshold: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.8
    )  # Default 80% threshold
    alert_triggered: Mapped[bool] = mapped_column(nullable=False, default=False)
    alert_severity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )  # low, medium, high, critical

    # Detailed metrics and recommendations
    group_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mitigation_suggested: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    is_fairness_aware: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Additional metadata
    analysis_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<FairnessMetrics("
            f"id={self.id}, "
            f"vacancy_id={self.vacancy_id}, "
            f"demographic_group={self.demographic_group}, "
            f"disparate_impact_ratio={self.disparate_impact_ratio}, "
            f"alert_triggered={self.alert_triggered})>"
        )


class FairnessAlert(Base, UUIDMixin, TimestampMixin):
    """
    FairnessAlert model for storing bias detection alerts

    This model captures alerts triggered when fairness metrics exceed
    acceptable thresholds, enabling compliance tracking and remediation.

    Attributes:
        id: UUID primary key
        fairness_metric_id: Foreign key to FairnessMetrics
        vacancy_id: Foreign key to JobVacancy
        alert_type: Type of alert (disparate_impact, statistical_parity, sample_size)
        severity: Alert severity level (low, medium, high, critical)
        status: Alert status (active, acknowledged, resolved, false_positive)
        message: Human-readable alert message
        threshold_value: The threshold that was exceeded
        actual_value: The actual metric value that triggered the alert
        acknowledged_by: Optional user who acknowledged the alert
        acknowledged_at: Timestamp when alert was acknowledged
        resolution_notes: Notes on how the alert was resolved
        resolved_at: Timestamp when alert was resolved
        notification_sent: Whether email/notification was sent
        alert_metadata: JSON object with additional alert details
    """

    __tablename__ = "fairness_alerts"

    fairness_metric_id: Mapped[UUID] = mapped_column(
        ForeignKey("fairness_metrics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Alert details
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # disparate_impact, statistical_parity, sample_size
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, acknowledged, resolved, false_positive

    message: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_value: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    actual_value: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # Acknowledgment and resolution
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, default=None
    )
    acknowledged_at: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    resolved_at: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )

    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Additional metadata
    alert_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<FairnessAlert("
            f"id={self.id}, "
            f"fairness_metric_id={self.fairness_metric_id}, "
            f"alert_type={self.alert_type}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )
