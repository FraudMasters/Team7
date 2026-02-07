"""
EvaluationScorecard model for individual evaluations with criteria responses
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EvaluationScorecard(Base, UUIDMixin, TimestampMixin):
    """
    EvaluationScorecard model for individual evaluations with criteria responses

    This model stores individual evaluator assessments for a candidate based on
    an evaluation template. Each scorecard contains responses to the template's
    criteria, including scores and optional comments for each criteria.

    Multiple evaluators can create scorecards for the same candidate, which
    can then be aggregated to produce consolidated scores for hiring decisions.

    Attributes:
        id: UUID primary key
        template_id: Foreign key to EvaluationTemplate being used
        resume_id: Foreign key to Resume (candidate being evaluated)
        evaluator_id: Foreign key to Recruiter (person conducting the evaluation)
        criteria_responses: JSON object mapping criteria_id to {score, comments}
        overall_score: Optional overall score for the entire evaluation
        status: Current status of the scorecard (draft, in_progress, completed)
        evaluator_comments: Optional overall comments/feedback from the evaluator
        extra_metadata: JSON object with additional evaluation metadata
        created_at: Timestamp when scorecard was created (inherited)
        updated_at: Timestamp when scorecard was last updated (inherited)
    """

    __tablename__ = "evaluation_scorecards"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluator_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    criteria_responses: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    overall_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    evaluator_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EvaluationScorecard(id={self.id}, template_id={self.template_id}, "
            f"resume_id={self.resume_id}, status={self.status})>"
        )

