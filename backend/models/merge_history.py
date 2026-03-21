"""
MergeHistory model for tracking profile merge operations
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class MergeHistory(Base, UUIDMixin, TimestampMixin):
    """
    MergeHistory model for tracking profile merge operations

    Stores comprehensive records of profile merges to maintain data lineage,
    enable merge auditing, and support undo operations. Tracks which profiles
    were merged, who performed the merge, and what data was combined.

    Attributes:
        id: UUID primary key
        organization_id: Organization where the merge occurred
        source_resume_id: ID of the resume that was merged FROM (duplicate)
        target_resume_id: ID of the resume that was merged INTO (primary)
        merged_by_user_id: ID of the user who performed the merge
        merge_timestamp: When the merge was performed
        merge_data: JSON object with details about merged fields and conflicts resolved
        undo_data: JSON object with data needed to reverse the merge operation
        reason: Optional text explanation for why profiles were merged
        can_undo: Whether this merge can be undone (some merges may be irreversible)
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "merge_history"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    merged_by_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    merge_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    merge_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    undo_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    can_undo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    source_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[source_resume_id], backref="merged_into"
    )
    target_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[target_resume_id], backref="merged_from"
    )

    def __repr__(self) -> str:
        return f"<MergeHistory(id={self.id}, source={self.source_resume_id}, target={self.target_resume_id})>"
