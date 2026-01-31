"""
CandidateActivity model for tracking candidate stage changes and notes history
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateActivityType(str, enum.Enum):
    """Types of candidate activities that can be tracked"""

    STAGE_CHANGED = "stage_changed"
    NOTE_ADDED = "note_added"
    NOTE_UPDATED = "note_updated"
    NOTE_DELETED = "note_deleted"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    RANKING_CHANGED = "ranking_changed"
    RATING_CHANGED = "rating_changed"
    CONTACT_ATTEMPT = "contact_attempt"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    FEEDBACK_PROVIDED = "feedback_provided"
    STATUS_UPDATED = "status_updated"


class CandidateActivity(Base, UUIDMixin, TimestampMixin):
    """
    CandidateActivity model for tracking candidate stage changes and notes history

    This model maintains a comprehensive audit trail of all candidate-related activities,
    enabling recruiters to track the complete history of a candidate's journey through
    the hiring pipeline. It records stage transitions, notes additions/changes, tag
    modifications, and other significant candidate events.

    Attributes:
        id: UUID primary key
        activity_type: Type of activity that occurred
        candidate_id: Foreign key to the candidate (resume or match result)
        vacancy_id: Optional foreign key to the related job vacancy
        from_stage: Previous hiring stage (for stage changes)
        to_stage: New hiring stage (for stage changes)
        note_id: Optional foreign key to related CandidateNote
        tag_id: Optional foreign key to related CandidateTag
        recruiter_id: Foreign key to Recruiter who performed the action
        activity_data: JSON object with activity-specific data
        reason: Optional text explanation for the activity
        created_at: Timestamp when activity was recorded (inherited)
        updated_at: Timestamp when activity was last updated (inherited)
    """

    __tablename__ = "candidate_activities"

    activity_type: Mapped[CandidateActivityType] = mapped_column(
        String(50), nullable=False, index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    to_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    note_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("candidate_notes.id", ondelete="SET NULL"), nullable=True
    )
    tag_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("candidate_tags.id", ondelete="SET NULL"), nullable=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activity_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateActivity(id={self.id}, type={self.activity_type}, candidate={self.candidate_id})>"
