"""
CandidateNote model for collaborative notes and comments on candidates
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateNote(Base, UUIDMixin, TimestampMixin):
    """
    CandidateNote model for collaborative notes and comments on candidates

    This model enables team collaboration by allowing recruiters and hiring managers
    to add notes and comments to candidate profiles. Notes can be private or visible
    to the entire team, supporting coordinated hiring decisions.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        recruiter_id: Optional foreign key to Recruiter (author of the note)
        content: The note or comment content
        is_private: Whether the note is private (only visible to author) or team-visible
        created_at: Timestamp when note was created (inherited)
        updated_at: Timestamp when note was last updated (inherited)
    """

    __tablename__ = "candidate_notes"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<CandidateNote(id={self.id}, resume_id={self.resume_id}, is_private={self.is_private})>"
