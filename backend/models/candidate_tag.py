"""
CandidateTag model for custom candidate tags (e.g., High Priority, Urgent, Remote, Referral)
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateTag(Base, UUIDMixin, TimestampMixin):
    """
    CandidateTag model for custom candidate tags

    This model enables organizations to create custom tags for categorizing
    and prioritizing candidates. Common use cases include priority levels
    (High Priority, Urgent), work preferences (Remote, Hybrid), or sourcing
    channels (Referral, LinkedIn Recruiter, etc.).

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this tag
        tag_name: Name of the tag (e.g., "High Priority", "Urgent", "Remote", "Referral")
        tag_order: Order in which this tag appears in the UI (1, 2, 3, etc.)
        is_default: Whether this is a default tag (applied to new organizations)
        is_active: Whether this tag is currently active and visible
        color: Optional color code for UI display (e.g., "#EF4444" for red)
        description: Optional description of when to use this tag
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "candidate_tags"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tag_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateTag(id={self.id}, org={self.organization_id}, tag={self.tag_name})>"
