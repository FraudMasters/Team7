"""
ResumeFeedback model for storing optimization suggestions

This table stores AI-powered optimization feedback including:
- Keyword analysis and missing keywords
- Formatting recommendations
- Content improvement suggestions
- Overall optimization score
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResumeFeedback(Base, UUIDMixin, TimestampMixin):
    """
    ResumeFeedback model for storing optimization suggestions

    This table stores the results of AI-powered resume optimization analysis,
    avoiding the need to regenerate feedback on every request.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        target_job_description: Job description used for keyword matching (optional)

        # Optimization results
        suggestions: List of optimization suggestions with type, priority, category, etc.
        total_suggestions: Total number of suggestions generated
        high_priority_count: Number of high-priority suggestions
        medium_priority_count: Number of medium-priority suggestions
        low_priority_count: Number of low-priority suggestions

        # Keyword analysis
        keywords_found: List of keywords found in resume
        missing_keywords: List of recommended missing keywords

        # Score
        score: Overall optimization score (0-100)

        # Enhanced optimization scores
        completeness_score: Resume completeness score (0-100)
        ats_score: ATS compatibility score (0-100)
        ranking_prediction: Before/after ranking prediction (JSON)

        # Processing metadata
        analyzer_version: Version of the optimizer used
    """

    __tablename__ = "resume_feedbacks"

    # Reference to resume
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Target job description (optional)
    target_job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optimization results (JSON fields for flexibility)
    suggestions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    total_suggestions: Mapped[Optional[int]] = mapped_column(nullable=True)
    high_priority_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    medium_priority_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    low_priority_count: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Keyword analysis
    keywords_found: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Score
    score: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Enhanced optimization scores
    completeness_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    ats_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    ranking_prediction: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Processing metadata
    analyzer_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ResumeFeedback(id={self.id}, resume_id={self.resume_id}, score={self.score})>"
