"""
CandidateRank model for storing AI-powered candidate ranking scores
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateRank(Base, UUIDMixin, TimestampMixin):
    """
    CandidateRank model for storing AI-powered candidate ranking results

    This model stores the computed ranking scores for candidates based on
    machine learning models that consider multiple factors like skills match,
    experience relevance, education quality, and other features.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this ranking
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        rank_score: Overall ranking score (0-1) from ML model
        rank_position: Position in ranked list (1=best)
        model_version: Version of the ranking model used
        model_type: Type of model (random_forest, gradient_boosting, etc.)
        is_experiment: Whether this candidate is in an A/B test experiment
        experiment_group: A/B test group (control/treatment)
        feature_contributions: JSON object with SHAP values for each feature
        ranking_factors: JSON object with detailed factor scores
        prediction_confidence: Model's confidence in the prediction (0-1)
        explanation_narrative: Natural language explanation (1-3 sentences) from LLM
        confidence_interval: JSON object with lower/upper bounds for uncertainty
        resume_highlights: JSON object mapping features to resume sections for highlighting
        recommendation: Hiring recommendation (excellent/good/maybe/poor)
        extra_metadata: Additional metadata about the ranking
    """

    __tablename__ = "candidate_ranks"

    organization_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Main ranking score
    rank_score: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.0
    )
    rank_position: Mapped[Optional[int]] = mapped_column(
        Numeric(10, 0), nullable=True, default=None
    )

    # Model metadata
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="v1.0"
    )
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="random_forest"
    )

    # A/B testing
    is_experiment: Mapped[bool] = mapped_column(nullable=False, default=False)
    experiment_group: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )  # 'control' or 'treatment'

    # Explainability
    feature_contributions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ranking_factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    prediction_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )

    # Enhanced explainability (for dashboard)
    explanation_narrative: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )  # LLM-generated natural language explanation (1-3 sentences)
    confidence_interval: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )  # {"lower": 0.65, "upper": 0.85} for uncertainty bounds
    resume_highlights: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )  # Feature-to-section mapping for highlighting: {"skills_match": {"section": "skills", "offset": 100, "length": 50}}

    # Recommendation
    recommendation: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )  # excellent, good, maybe, poor

    # Additional metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CandidateRank(id={self.id}, org={self.organization_id}, "
            f"resume_id={self.resume_id}, vacancy_id={self.vacancy_id}, "
            f"rank_score={self.rank_score}, recommendation={self.recommendation})>"
        )


class RankingFeedback(Base, UUIDMixin, TimestampMixin):
    """
    RankingFeedback model for storing recruiter feedback on AI rankings

    This model captures recruiter feedback to continuously improve the
    ranking models through supervised learning.

    Attributes:
        id: UUID primary key
        rank_id: Foreign key to CandidateRank
        recruiter_id: Optional foreign key to Recruiter
        feedback_type: Type of feedback (thumbs_up/down, hire/reject, rating)
        was_helpful: Whether the AI ranking was helpful
        actual_outcome: Actual hiring outcome (hired, rejected, pending)
        adjusted_score: Recruiter's adjusted score if they disagreed
        comments: Optional text comments
        feedback_source: Source of feedback (web_ui, api, bulk)
    """

    __tablename__ = "ranking_feedback"

    rank_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidate_ranks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, default=None
    )

    # Feedback data
    feedback_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="thumbs"
    )  # thumbs, rating, outcome
    was_helpful: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    actual_outcome: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )  # hired, rejected, interviewing, pending
    adjusted_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    rating: Mapped[Optional[int]] = mapped_column(
        Numeric(3, 0), nullable=True, default=None
    )  # 1-5 star rating
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Metadata
    feedback_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="web_ui"
    )  # web_ui, api, bulk_import

    def __repr__(self) -> str:
        return (
            f"<RankingFeedback(id={self.id}, rank_id={self.rank_id}, "
            f"was_helpful={self.was_helpful}, outcome={self.actual_outcome})>"
        )
