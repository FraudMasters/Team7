"""
EvaluationCriteria model for template criteria definitions with weights and rating scales
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EvaluationCriteria(Base, UUIDMixin, TimestampMixin):
    """
    EvaluationCriteria model for template criteria definitions with weights and rating scales

    This model defines individual criteria within an evaluation template, such as
    "Technical Skills" or "Cultural Fit". Each criteria has a weight for aggregate
    scoring, a rating scale (e.g., 1-5), and optional description.

    Attributes:
        id: UUID primary key
        template_id: Foreign key to EvaluationTemplate
        name: Human-readable name for this criteria (e.g., "Technical Skills")
        description: Optional description of what this criteria measures
        criteria_type: Type of criteria (skills, experience, cultural_fit, etc.)
        weight: Weight for this criteria in aggregate scoring (0.0-1.0)
        min_score: Minimum score for this criteria's rating scale
        max_score: Maximum score for this criteria's rating scale
        rating_scale_description: Optional description of rating scale (e.g., "1-5, Poor to Excellent")
        display_order: Order to display this criteria in the template
        extra_metadata: JSON object with additional criteria configuration
        created_at: Timestamp when criteria was created (inherited)
        updated_at: Timestamp when criteria was last updated (inherited)
    """

    __tablename__ = "evaluation_criteria"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    weight: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    min_score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    rating_scale_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EvaluationCriteria(id={self.id}, template_id={self.template_id}, "
            f"name={self.name}, type={self.criteria_type}, weight={self.weight})>"
        )
