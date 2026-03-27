"""
CandidateAppeal model for storing candidate appeals against ranking decisions
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateAppeal(Base, UUIDMixin, TimestampMixin):
    """
    CandidateAppeal model for storing candidate appeals and challenges to AI rankings

    This model enables candidates to submit appeals when they believe their ranking
    is inaccurate, providing additional context, skills, or information that may
    have been missed during the initial evaluation. Appeals are reviewed by recruiters
    who can accept, reject, or trigger re-ranking based on new information.

    Attributes:
        id: UUID primary key
        candidate_rank_id: Foreign key to CandidateRank (the ranking being appealed)
        candidate_email: Email address of the candidate submitting the appeal
        appeal_type: Type of appeal (ranking_position, score_explanation, missing_skills)
        appeal_text: Candidate's explanation and additional context
        supporting_documents: JSON metadata for uploaded supporting documents
        status: Current status (pending, under_review, accepted, rejected)
        reviewer_id: Optional foreign key to Recruiter who reviewed the appeal
        review_notes: Internal notes from the reviewer
        resolution_outcome: Final outcome description or action taken
        created_at: Timestamp when appeal was submitted
        updated_at: Timestamp when appeal was last modified
    """

    __tablename__ = "candidate_appeals"

    # Core appeal information
    candidate_rank_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidate_ranks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # Appeal details
    appeal_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ranking_position"
    )  # ranking_position, score_explanation, missing_skills
    appeal_text: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_documents: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )  # {"documents": [{"filename": "cert.pdf", "url": "s3://...", "type": "certification"}]}

    # Review and status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, under_review, accepted, rejected
    reviewer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, default=None
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    resolution_outcome: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )  # Description of final action taken (e.g., "Re-ranked with new information", "No change warranted")

    def __repr__(self) -> str:
        return (
            f"<CandidateAppeal(id={self.id}, candidate_rank_id={self.candidate_rank_id}, "
            f"appeal_type={self.appeal_type}, status={self.status})>"
        )
