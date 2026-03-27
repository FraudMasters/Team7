"""
DuplicateReview model for manual review queue of potential duplicates
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ReviewStatus(str, enum.Enum):
    """Status of duplicate reviews in the manual review queue"""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DuplicateReview(Base, UUIDMixin, TimestampMixin):
    """
    DuplicateReview model for manual review queue of potential duplicates

    Tracks potential duplicate candidates that require manual review and approval
    before automatic merging. Used for low-confidence duplicate matches or cases
    requiring human judgment to decide whether to merge or keep separate.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns these candidates
        original_resume_id: ID of the first/original resume
        duplicate_resume_id: ID of the potentially duplicate resume
        confidence_score: Similarity confidence score (0.0 to 1.0)
        status: Current review status (pending, in_review, approved, rejected)
        assigned_reviewer_id: Optional user ID assigned to review this duplicate
        queue_entered_at: Timestamp when duplicate entered the review queue
        review_started_at: Timestamp when review began (status -> in_review)
        review_completed_at: Timestamp when review finished (status -> approved/rejected)
        decision_reason: Optional text explanation for approval/rejection decision
        batch_job_id: Optional ID of batch job that detected this duplicate
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "duplicate_reviews"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    duplicate_resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, index=True
    )
    status: Mapped[ReviewStatus] = mapped_column(
        default=ReviewStatus.PENDING, nullable=False, index=True
    )
    assigned_reviewer_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
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
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    batch_job_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("batch_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    original_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[original_resume_id], backref="duplicate_reviews_as_original"
    )
    duplicate_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[duplicate_resume_id], backref="duplicate_reviews_as_duplicate"
    )
    batch_job: Mapped[Optional["BatchJob"]] = relationship(
        "BatchJob", backref="duplicate_reviews"
    )

    def __repr__(self) -> str:
        return f"<DuplicateReview(id={self.id}, original={self.original_resume_id}, duplicate={self.duplicate_resume_id}, status={self.status})>"
