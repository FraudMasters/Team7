"""
JobSeekerProfile model for storing job seeker profile information
"""
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class JobSeekerProfile(Base, UUIDMixin, TimestampMixin):
    """
    JobSeekerProfile model for storing comprehensive job seeker profile information

    This model serves as the central profile for job seekers, linking users
    to their resumes and profile data. It enables job seekers to manage
    their professional identity and resume uploads.

    Attributes:
        id: UUID primary key
        user_id: User that owns this profile
        organization_id: Organization that this profile belongs to
        phone: Contact phone number
        location: City, state or country of residence
        bio: Professional summary or biography
        linkedin_url: LinkedIn profile URL
        portfolio_url: Portfolio or website URL
        years_of_experience: Total years of work experience
        current_title: Current or most recent job title
        current_company: Current or most recent company
        industry: Industry of expertise
        job_seeker_status: Current employment status (actively looking, open, etc.)
        preferred_locations: Preferred job locations (comma-separated)
        preferred_job_types: Preferred employment types (comma-separated)
        expected_salary: Expected salary range
        resume_id: Primary/default resume for this profile
        created_at: Timestamp when profile was created (inherited from TimestampMixin)
        updated_at: Timestamp when profile was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "job_seeker_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    years_of_experience: Mapped[Optional[float]] = mapped_column(nullable=True)
    current_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    job_seeker_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_locations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_job_types: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expected_salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resume_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<JobSeekerProfile(id={self.id}, user_id={self.user_id}, location={self.location})>"
