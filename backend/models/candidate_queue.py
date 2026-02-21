"""
CandidateQueueItem model for candidate review queue management
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class QueuePriority(str, enum.Enum):
    """Priority levels for candidates in the review queue"""

    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QueueStatus(str, enum.Enum):
    """Status of candidates in the review queue"""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class CandidateQueueItem(Base, UUIDMixin, TimestampMixin):
    """
    CandidateQueueItem model for managing the candidate review queue

    This model provides a structured queue system for recruiters to systematically
    review and process candidates. It includes priority sorting, status tracking,
    and workflow management to ensure no candidate falls through the cracks.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume (the candidate being reviewed)
        vacancy_id: Optional foreign key to JobVacancy (the position applied for)
        priority: Priority level for sorting (urgent, high, medium, low)
        status: Current review status (pending, in_review, completed, skipped)
        assigned_recruiter_id: Foreign key to Recruiter for workload management
        queue_entered_at: Timestamp when candidate entered the queue
        review_started_at: Timestamp when review began (status -> in_review)
        review_completed_at: Timestamp when review finished (status -> completed/skipped)
        notes: Optional notes about the queue item
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "candidate_queue_items"

    resume_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUIDMixin]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    priority: Mapped[QueuePriority] = mapped_column(
        default=QueuePriority.MEDIUM, nullable=False, index=True
    )
    status: Mapped[QueueStatus] = mapped_column(
        default=QueueStatus.PENDING, nullable=False, index=True
    )
    assigned_recruiter_id: Mapped[Optional[UUIDMixin]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    queue_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    review_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateQueueItem(id={self.id}, resume_id={self.resume_id}, priority={self.priority}, status={self.status})>"
