"""
MatchResult model for storing resume-vacancy matching results
"""
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MatchResult(Base, UUIDMixin, TimestampMixin):
    """
    MatchResult model for storing resume-to-vacancy matching results

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        match_percentage: Overall match score (0-100)
        matched_skills: JSON array of skills found in resume with metadata
        missing_skills: JSON array of required skills not found in resume
        additional_skills_matched: JSON array of additional skills matched
        experience_verified: Whether experience requirements were met
        experience_details: JSON object with experience breakdown by skill
        created_at: Timestamp when match was computed (inherited)
    """

    __tablename__ = "match_results"

    resume_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )
    matched_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    additional_skills_matched: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    experience_verified: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    experience_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<MatchResult(id={self.id}, resume_id={self.resume_id}, vacancy_id={self.vacancy_id}, match={self.match_percentage}%)>"
