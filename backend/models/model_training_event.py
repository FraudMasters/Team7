"""
ModelTrainingEvent model for tracking model training runs
"""
from typing import Optional

from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ModelTrainingEvent(Base, UUIDMixin, TimestampMixin):
    """
    ModelTrainingEvent model for tracking ML model training runs

    Attributes:
        id: UUID primary key
        model_name: Name of the model being trained (e.g., skill_matching, resume_parser)
        version: Version identifier for the trained model (e.g., v1.0.0, v2.1.3)
        training_status: Status of the training run (pending, in_progress, completed, failed)
        training_config: JSON object with training parameters (epochs, learning_rate, etc.)
        training_metrics: JSON object with metrics from the training run (loss, accuracy, etc.)
        error_message: Error message if training failed
        started_at: Timestamp when training started
        completed_at: Timestamp when training completed
        training_duration: Duration of the training run in seconds
        dataset_info: JSON object with dataset information (size, splits, etc.)
        ml_model_version_id: UUID reference to the created MLModelVersion (if successful)
        created_at: Timestamp when training event was created (inherited)
        updated_at: Timestamp when training event was last updated (inherited)
    """

    __tablename__ = "model_training_events"

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    training_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    training_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    training_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    training_duration: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    dataset_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ml_model_version_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<ModelTrainingEvent(id={self.id}, model={self.model_name}, version={self.version}, status={self.training_status})>"
