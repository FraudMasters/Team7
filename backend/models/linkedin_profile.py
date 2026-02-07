"""
LinkedIn Profile model for storing imported LinkedIn profile data
"""
import enum
from typing import Optional

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LinkedInProfileStatus(str, enum.Enum):
    """Status of LinkedIn profile processing and synchronization"""

    # Processing statuses
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    # Sync statuses
    SYNCED = "SYNCED"
    OUTDATED = "OUTDATED"
    ARCHIVED = "ARCHIVED"


class LinkedInProfile(Base, UUIDMixin, TimestampMixin):
    """
    LinkedIn Profile model for storing imported LinkedIn profile data

    Attributes:
        id: UUID primary key
        linkedin_id: LinkedIn member ID (unique identifier from LinkedIn)
        linkedin_url: Public LinkedIn profile URL
        first_name: Candidate's first name
        last_name: Candidate's last name
        headline: LinkedIn headline (job title, company, etc.)
        location: Candidate's location (city, country)
        email: Email address from LinkedIn profile
        phone: Phone number from LinkedIn profile
        profile_picture_url: URL to profile picture
        skills: List of skills from LinkedIn profile
        experience: Work experience data (JSON)
        education: Education data (JSON)
        raw_profile_data: Complete raw profile data from LinkedIn API (JSON)
        status: Current processing/sync status
        last_synced_at: Timestamp when profile was last synced with LinkedIn
        error_message: Error message if import/sync failed
    """

    __tablename__ = "linkedin_profiles"

    linkedin_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    linkedin_url: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    skills: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    experience: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    education: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_profile_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[LinkedInProfileStatus] = mapped_column(
        Enum(LinkedInProfileStatus), default=LinkedInProfileStatus.PENDING, nullable=False, index=True
    )
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<LinkedInProfile(id={self.id}, linkedin_id={self.linkedin_id}, status={self.status.value})>"
