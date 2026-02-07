"""
TeamComment model for collaborative threaded discussions on candidates
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class TeamComment(Base, UUIDMixin, TimestampMixin):
    """
    TeamComment model for collaborative threaded discussions on candidates

    This model enables team collaboration through threaded comment discussions
    on candidate profiles. Team members can discuss candidates, reply to each
    other's comments creating nested threads, and @mention colleagues.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume (candidate being discussed)
        author_id: Foreign key to Recruiter (author of the comment)
        parent_comment_id: Optional foreign key to TeamComment (for threaded replies)
        content: The comment content
        is_resolved: Whether the comment thread is resolved/closed
        is_deleted: Soft delete flag (comments are marked deleted, not removed)
        edits_count: Number of times the comment has been edited
        created_at: Timestamp when comment was created (inherited)
        updated_at: Timestamp when comment was last updated (inherited)
    """

    __tablename__ = "team_comments"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_comment_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("team_comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    edits_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<TeamComment(id={self.id}, resume_id={self.resume_id}, author_id={self.author_id}, is_resolved={self.is_resolved})>"
