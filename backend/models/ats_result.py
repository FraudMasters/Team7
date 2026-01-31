"""
ATS Result model for storing ATS simulation results.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ATSResult(Base, UUIDMixin, TimestampMixin):
    """
    ATS (Applicant Tracking System) simulation result.

    Stores the results of LLM-based ATS evaluation of resumes
    against job postings.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        passed: Whether the resume passed the ATS threshold
        overall_score: Combined ATS score (0-1)
        keyword_score: Keyword matching score (0-1)
        experience_score: Experience relevance score (0-1)
        education_score: Education match score (0-1)
        fit_score: Overall fit assessment (0-1)
        looks_professional: Whether resume looks professionally formatted
        disqualified: Whether resume has disqualifying issues
        visual_issues: List of visual/formatting issues
        ats_issues: List of ATS-specific issues
        missing_keywords: List of missing keywords
        suggestions: List of improvement suggestions
        feedback: Detailed feedback from LLM
        provider: LLM provider used
        model: Model name used
        raw_response: Raw LLM response for debugging
    """

    __tablename__ = "ats_results"

    # Reference to resume and vacancy
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Pass/Fail status
    passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Individual scores
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    keyword_score: Mapped[float] = mapped_column(Float, nullable=True)
    experience_score: Mapped[float] = mapped_column(Float, nullable=True)
    education_score: Mapped[float] = mapped_column(Float, nullable=True)
    fit_score: Mapped[float] = mapped_column(Float, nullable=True)

    # Professional appearance and disqualification
    looks_professional: Mapped[bool] = mapped_column(Boolean, default=True)
    disqualified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Issues and feedback
    visual_issues: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ats_issues: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ATSResult(id={self.id}, resume_id={self.resume_id}, "
            f"vacancy_id={self.vacancy_id}, passed={self.passed}, "
            f"score={self.overall_score:.2f})>"
        )
