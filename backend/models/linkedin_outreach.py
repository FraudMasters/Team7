"""
LinkedInOutreach model for tracking individual LinkedIn outreach messages
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LinkedInOutreachResponseStatus(str, enum.Enum):
    """Response status for LinkedIn outreach messages"""

    NO_RESPONSE = "no_response"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    REPLIED = "replied"
    BOUNCED = "bounced"
    OPENED = "opened"


class LinkedInOutreach(Base, UUIDMixin, TimestampMixin):
    """
    LinkedInOutreach model for tracking individual LinkedIn outreach messages

    This model tracks individual outreach messages sent to LinkedIn candidates as part
    of recruitment campaigns. It enables recruiters to monitor message delivery, response
    rates, and candidate engagement for optimization of sourcing strategies.

    Attributes:
        id: UUID primary key
        campaign_id: Foreign key to the LinkedInCampaign this outreach belongs to
        linkedin_profile_id: Foreign key to the LinkedInProfile being contacted
        recruiter_id: Foreign key to Recruiter who sent the outreach
        message_subject: Subject line of the message (for InMail)
        message_body: Content of the outreach message
        message_sent_at: Timestamp when the message was sent
        response_received_at: Optional timestamp when response was received
        response_status: Current response status
        response_text: Optional text of the candidate's response
        created_at: Timestamp when outreach record was created (inherited)
        updated_at: Timestamp when outreach record was last updated (inherited)
    """

    __tablename__ = "linkedin_outreach"

    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("linkedin_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    linkedin_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("linkedin_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    message_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_status: Mapped[LinkedInOutreachResponseStatus] = mapped_column(
        String(50), nullable=False, index=True, default=LinkedInOutreachResponseStatus.NO_RESPONSE
    )
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<LinkedInOutreach(id={self.id}, campaign={self.campaign_id}, status={self.response_status})>"
