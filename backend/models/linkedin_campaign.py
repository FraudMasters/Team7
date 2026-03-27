"""
LinkedInCampaign model for tracking LinkedIn outreach campaigns
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LinkedInCampaignStatus(str, enum.Enum):
    """Status of LinkedIn outreach campaigns"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LinkedInCampaign(Base, UUIDMixin, TimestampMixin):
    """
    LinkedInCampaign model for tracking LinkedIn outreach campaigns

    This model manages LinkedIn outreach campaigns, enabling recruiters to organize
    and track their sourcing efforts for specific job vacancies. It records campaign
    metadata, target metrics, and performance statistics including message sends and
    response rates.

    Attributes:
        id: UUID primary key
        name: Campaign name/title
        recruiter_id: Foreign key to Recruiter who created the campaign
        vacancy_id: Optional foreign key to the job vacancy for this campaign
        status: Current status of the campaign
        target_count: Target number of candidates to reach out to
        sent_count: Number of outreach messages sent
        response_count: Number of responses received
        description: Optional campaign description/notes
        created_at: Timestamp when campaign was created (inherited)
        updated_at: Timestamp when campaign was last updated (inherited)
    """

    __tablename__ = "linkedin_campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[LinkedInCampaignStatus] = mapped_column(
        String(50), nullable=False, index=True, default=LinkedInCampaignStatus.DRAFT
    )
    target_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    sent_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    response_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<LinkedInCampaign(id={self.id}, name={self.name}, status={self.status})>"
