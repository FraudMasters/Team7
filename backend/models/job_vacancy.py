"""
JobVacancy model for storing job vacancy descriptions
"""
from typing import Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class JobVacancy(Base, UUIDMixin, TimestampMixin):
    """
    JobVacancy model for storing job postings to match against resumes

    Attributes:
        id: UUID primary key
        title: Job title
        description: Full job description
        required_skills: JSON array of required skills
        min_experience_months: Minimum required experience in months
        additional_requirements: JSON array of additional (preferred) skills
        industry: Industry sector
        work_format: Work format (remote, office, hybrid)
        location: Required location (if any)
        external_id: External system ID (e.g., from job board API)
        source: Source of the vacancy (manual, api, scrape)
        created_at: Timestamp when vacancy was created (inherited)
    """

    __tablename__ = "job_vacancies"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    min_experience_months: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )
    additional_requirements: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )
    salary_max: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )
    english_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    weight_profiles: Mapped[list["MatchingWeightProfile"]] = relationship(
        "MatchingWeightProfile",
        back_populates="vacancy",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<JobVacancy(id={self.id}, title={self.title})>"
