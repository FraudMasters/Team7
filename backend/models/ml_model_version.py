"""
MLModelVersion model for storing machine learning model versioning information

Supports champion/challenger model management workflow for continuous improvement
of ML models with proper governance and A/B test integration.
"""
import enum
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ModelRole(str, enum.Enum):
    """Role of a model version in the champion/challenger workflow"""

    STANDARD = "standard"  # Regular model version, not in champion/challenger workflow
    CHAMPION = "champion"  # Current production model for this model_name
    CHALLENGER = "challenger"  # Candidate to replace the champion


class MLModelVersion(Base, UUIDMixin, TimestampMixin):
    """
    MLModelVersion model for storing ML model versioning and A/B testing info

    Supports champion/challenger workflow where a champion model serves production
    traffic while challengers are evaluated for potential promotion based on
    performance metrics and A/B test results.

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
        model_role: Role in champion/challenger workflow (standard, champion, challenger)
        challenger_traffic_percent: Percentage of traffic to route to challenger (0-100)
        promoted_at: Timestamp when this model was promoted to champion
        promoted_from_id: ID of previous champion when this was promoted
        ab_test_id: Optional A/B test ID if this model is part of an experiment
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

    # Champion/Challenger fields
    model_role: Mapped[ModelRole] = mapped_column(
        Enum(ModelRole), default=ModelRole.STANDARD, nullable=False, index=True
    )
    challenger_traffic_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    promoted_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    promoted_from_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ml_model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    ab_test_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ab_tests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        exp = " [experiment]" if self.is_experiment else ""
        role = f" [{self.model_role.value}]" if self.model_role != ModelRole.STANDARD else ""
        return f"<MLModelVersion(id={self.id}, name={self.model_name}, version={self.version}, status={status}{exp}{role})>"
