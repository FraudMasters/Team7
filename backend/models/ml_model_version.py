"""
MLModelVersion model for storing machine learning model versioning information
"""
from typing import Optional

from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MLModelVersion(Base, UUIDMixin, TimestampMixin):
    """
    MLModelVersion model for storing ML model versioning and A/B testing info

    Attributes:
        id: UUID primary key
        model_name: Name of the model (e.g., skill_matching, resume_parser)
        version: Version identifier (e.g., v1.0.0, v2.1.3)
        is_active: Whether this model version is currently active
        is_experiment: Whether this is an experimental model for A/B testing
        experiment_config: JSON object with A/B testing configuration (traffic_percentage, etc.)
        model_metadata: JSON object with model training metadata (algorithm, training_date, etc.)
        accuracy_metrics: JSON object with accuracy metrics (precision, recall, f1_score, etc.)
        file_path: Path to the model file in storage
        performance_score: Overall performance score (0-100)
        created_at: Timestamp when model version was created (inherited)
        updated_at: Timestamp when model version was last updated (inherited)
    """

    __tablename__ = "ml_model_versions"

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_experiment: Mapped[bool] = mapped_column(nullable=False, default=False)
    experiment_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    accuracy_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    performance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        exp = " [experiment]" if self.is_experiment else ""
        return f"<MLModelVersion(id={self.id}, name={self.model_name}, version={self.version}, status={status}{exp})>"
