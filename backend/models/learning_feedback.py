"""
LearningFeedback model for storing aggregated correction feedback for parser improvement

This table stores aggregated patterns and insights derived from user corrections,
enabling:
- Identification of common parsing errors
- Pattern-based parser improvement
- Tracking of parser accuracy metrics over time
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LearningFeedback(Base, UUIDMixin, TimestampMixin):
    """
    LearningFeedback model for storing aggregated correction feedback

    This table stores aggregated patterns and insights derived from user
    corrections to parsed resume data. It enables the parser to learn from
    past mistakes and improve accuracy over time.

    Attributes:
        id: UUID primary key
        correction_id: Optional reference to the specific correction that triggered this feedback
        field_name: The field type this feedback applies to (e.g., "skills", "position", "education")
        error_pattern: Description of the error pattern observed
        suggestion: Suggested improvement for the parser
        pattern_type: Type of pattern (e.g., "extraction", "classification", "formatting")
        confidence_score: Confidence level of this learning (0.0-1.0)
        sample_count: Number of corrections that contributed to this pattern
        examples: Example corrections that demonstrate this pattern (JSON array)
        parser_version: Version of the parser when this feedback was generated
        is_applied: Whether this feedback has been applied to improve the parser
    """

    __tablename__ = "learning_feedbacks"

    # Optional reference to specific correction
    correction_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("parsing_corrections.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Field identification
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Pattern details
    error_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pattern_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Confidence and sample metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)

    # Examples of the pattern (JSON array of sample corrections)
    examples: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Parser metadata
    parser_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Application status
    is_applied: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<LearningFeedback(id={self.id}, field={self.field_name}, pattern_type={self.pattern_type})>"
