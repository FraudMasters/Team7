"""
ModelPerformanceHistory model for tracking ML model performance metrics over time
"""
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ModelPerformanceHistory(Base, UUIDMixin, TimestampMixin):
    """
    ModelPerformanceHistory model for tracking ML model performance metrics over time

    This model stores historical performance data for ML models, enabling tracking of
    model degradation, improvement from retraining, and A/B testing comparison.

    Attributes:
        id: UUID primary key
        model_version_id: Foreign key to MLModelVersion
        dataset_type: Type of dataset used for evaluation (training, validation, test, production)
        accuracy: Overall accuracy metric (0-1)
        precision: Precision metric (0-1)
        recall: Recall metric (0-1)
        f1_score: F1 score metric (0-1)
        auc_score: AUC-ROC score (0-1)
        sample_size: Number of samples used for evaluation
        confusion_matrix: JSON object containing confusion matrix data
        custom_metrics: JSON object for additional model-specific metrics
        performance_delta: Change in performance score compared to previous measurement
        evaluation_metadata: JSON object with evaluation details (evaluator_version, data_source, etc.)
        recorded_at: Timestamp when performance was recorded (uses created_at from TimestampMixin)
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "model_performance_history"

    model_version_id: Mapped[str] = mapped_column(
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dataset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    auc_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    confusion_matrix: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    performance_delta: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    evaluation_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ModelPerformanceHistory("
            f"id={self.id}, "
            f"model_version_id={self.model_version_id}, "
            f"dataset_type={self.dataset_type}, "
            f"f1_score={self.f1_score})>"
        )
