"""
ModelPerformanceSnapshot model for storing point-in-time aggregated performance metrics
"""
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ModelPerformanceSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    ModelPerformanceSnapshot model for storing point-in-time aggregated performance metrics

    This model stores periodic snapshots of model performance, providing a summarized view
    for dashboards, trend analysis, and alerting. Unlike ModelPerformanceHistory which
    records individual evaluation events, snapshots aggregate metrics over time windows.

    Attributes:
        id: UUID primary key
        model_version_id: Foreign key to MLModelVersion
        snapshot_type: Type of snapshot (hourly, daily, weekly, manual)
        time_window_hours: Number of hours of data included in this snapshot
        accuracy: Aggregated accuracy metric (0-1)
        precision: Aggregated precision metric (0-1)
        recall: Aggregated recall metric (0-1)
        f1_score: Aggregated F1 score metric (0-1)
        auc_score: Aggregated AUC-ROC score (0-1)
        ndcg_score: Normalized Discounted Cumulative Gain score (0-1)
        mrr_score: Mean Reciprocal Rank score (0-1)
        sample_count: Total number of samples used in this snapshot
        evaluation_count: Number of individual evaluations aggregated
        health_score: Overall model health score (0-100)
        performance_trend: Trend indicator (improving, declining, stable)
        alert_status: Current alert status (none, warning, critical)
        custom_metrics: JSON object for additional model-specific metrics
        snapshot_metadata: JSON object with snapshot details (data_sources, aggregation_method, etc.)
        created_at: Timestamp when snapshot was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "model_performance_snapshots"

    model_version_id: Mapped[str] = mapped_column(
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    snapshot_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    time_window_hours: Mapped[int] = mapped_column(nullable=False, default=24)
    accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    auc_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    ndcg_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    mrr_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    sample_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    evaluation_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    performance_trend: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    alert_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )
    custom_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    snapshot_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ModelPerformanceSnapshot("
            f"id={self.id}, "
            f"model_version_id={self.model_version_id}, "
            f"snapshot_type={self.snapshot_type}, "
            f"health_score={self.health_score}, "
            f"alert_status={self.alert_status})>"
        )
