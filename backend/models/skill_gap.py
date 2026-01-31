"""
SkillGapReport model for storing skill gap analysis results
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SkillGapReport(Base, UUIDMixin, TimestampMixin):
    """
    SkillGapReport model for storing candidate-to-vacancy skill gap analysis

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy

        # Candidate skills data
        candidate_skills: JSON array of skills extracted from candidate's resume
        candidate_skill_levels: JSON object mapping skills to proficiency levels

        # Required skills data
        required_skills: JSON array of skills required by the vacancy
        required_skill_levels: JSON object mapping skills to required proficiency levels

        # Gap analysis
        missing_skills: JSON array of required skills not found in candidate's resume
        missing_skill_details: JSON object with details about each missing skill (gap severity, importance)
        matched_skills: JSON array of skills that match requirements
        partial_match_skills: JSON array of skills with insufficient proficiency

        # Overall assessment
        gap_severity: Overall severity of skill gaps (critical/moderate/minimal/none)
        gap_percentage: Percentage of required skills missing (0-100)
        bridgeability_score: Score indicating how easily gaps can be bridged (0-1)
        estimated_time_to_bridge: Estimated hours/weeks to bridge all gaps

        # Recommendations
        recommended_resources_count: Number of learning resources recommended
        priority_ordering: JSON array indicating order of priority for addressing gaps

        created_at: Timestamp when report was generated (inherited)
        updated_at: Timestamp when report was last updated (inherited)
    """

    __tablename__ = "skill_gap_reports"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Candidate skills data
    candidate_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    candidate_skill_levels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Required skills data
    required_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    required_skill_levels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Gap analysis
    missing_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_skill_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    matched_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    partial_match_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Overall assessment
    gap_severity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )
    gap_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True, default=None
    )
    bridgeability_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    estimated_time_to_bridge: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )  # in hours

    # Recommendations
    recommended_resources_count: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )
    priority_ordering: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SkillGapReport(id={self.id}, resume_id={self.resume_id}, "
            f"vacancy_id={self.vacancy_id}, gap_severity={self.gap_severity})>"
        )
