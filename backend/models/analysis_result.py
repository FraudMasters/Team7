"""
AnalysisResult model for storing resume analysis results
"""
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AnalysisResult(Base, UUIDMixin, TimestampMixin):
    """
    AnalysisResult model for storing NLP/ML analysis results

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        errors: JSON array of detected errors (grammar, spelling, missing elements)
        skills: JSON array of extracted skills
        experience_summary: JSON object with total experience and breakdown by skill
        recommendations: JSON array of improvement recommendations
        keywords: JSON array of extracted keywords with scores
        entities: JSON object with named entities (organizations, dates, education)
        created_at: Timestamp when analysis was created (inherited)
    """

    __tablename__ = "analysis_results"

    resume_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    experience_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, resume_id={self.resume_id})>"
