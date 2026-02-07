"""
CommentMention model for tracking @mentions in team comments
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CommentMention(Base, UUIDMixin, TimestampMixin):
    """
    CommentMention model for tracking @mentions in team comments

    Attributes:
        id: UUID primary key
        comment_id: Foreign key to TeamComment
        mentioned_user_id: Foreign key to Recruiter (user being mentioned)
        is_read: Whether the mention has been read by the mentioned user
        read_at: Timestamp when the mention was marked as read
        created_at: Timestamp when mention was created (inherited)
        updated_at: Timestamp when mention was last updated (inherited)
    """

    __tablename__ = "comment_mentions"

    comment_id: Mapped[UUID] = mapped_column(
        ForeignKey("team_comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentioned_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<CommentMention(id={self.id}, comment_id={self.comment_id}, mentioned_user_id={self.mentioned_user_id}, is_read={self.is_read})>"
