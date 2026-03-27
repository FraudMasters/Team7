"""
ApplicationSource model for tracking where job applications originate
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class SourceType(str, enum.Enum):
    """Types of application sources"""

    JOB_BOARD = "JOB_BOARD"          # External job boards (Indeed, LinkedIn Jobs, etc.)
    REFERRAL = "REFERRAL"            # Employee referral
    CAREER_PAGE = "CAREER_PAGE"      # Company career page/website
    SOCIAL_MEDIA = "SOCIAL_MEDIA"    # Social media posts
    RECRUITER = "RECRUITER"          # Direct recruiter outreach
    EVENT = "EVENT"                  # Career fair, conference, etc.
    AGENCY = "AGENCY"                # Recruitment agency
    INTERNAL = "INTERNAL"            # Internal job posting
    DIRECT = "DIRECT"                # Direct application/walk-in
    OTHER = "OTHER"                  # Other sources


class ApplicationSource(Base, UUIDMixin, TimestampMixin):
    """
    ApplicationSource model for tracking where job applications originate

    This model enables source effectiveness analytics by recording the origin
    of each application. Tracks metrics like application volume, quality scores,
    conversion rates, and time-to-hire by source to optimize recruiting spend.

    Attributes:
        id: UUID primary key
        application_id: Foreign key to JobApplication
        source_type: Category of application source (job board, referral, etc.)
        source_name: Specific name/identifier of the source (e.g., "Indeed", "LinkedIn")
        source_url: Optional URL where the application originated
        campaign_id: Optional marketing/recruiting campaign identifier
        referrer_id: Optional foreign key to User who referred (for REFERRAL type)
        cost_per_application: Optional cost in dollars for this application source
        quality_score: Optional quality score (0-100) for source effectiveness
        notes: Optional notes about the source
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "application_sources"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType), nullable=False, index=True
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    referrer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cost_per_application: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Cost in cents
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    application: Mapped["JobApplication"] = relationship(
        "JobApplication",
        back_populates="source"
    )
    referrer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="referred_applications",
        foreign_keys=[referrer_id]
    )

    def __repr__(self) -> str:
        return f"<ApplicationSource(id={self.id}, type={self.source_type.value}, name={self.source_name})>"
