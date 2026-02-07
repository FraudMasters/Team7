"""
CandidateRecommendation model for storing AI-powered candidate recommendations
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateRecommendation(Base, UUIDMixin, TimestampMixin):
    """
    CandidateRecommendation model for storing proactive AI recommendations

    This model stores various types of proactive recommendations to help recruiters
    discover great candidates they might have missed. Includes:
    - "Candidates Like This": Similar candidates based on vector embeddings
    - "Best Fit for Vacancy": Top candidates for open roles
    - "Candidates at Risk of Loss": Candidates likely to accept competing offers

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume (the recommended candidate)
        vacancy_id: Optional foreign key to JobVacancy (for vacancy-specific recommendations)
        recruiter_id: Optional foreign key to Recruiter (for personalized recommendations)
        recommendation_type: Type of recommendation (similar_candidates, best_fit, at_risk)
        score: Recommendation score (0-1) indicating strength of recommendation
        rank_position: Position in recommendation list (1=best)
        reason: Primary reason for recommendation (skills_match, experience, education, etc.)
        similarity_score: For similar_candidates: cosine similarity from embeddings (0-1)
        risk_score: For at_risk: probability of accepting competing offer (0-1)
        model_version: Version of the recommendation model used
        algorithm: Algorithm used (vector_similarity, collaborative_filtering, hybrid)
        feature_contributions: JSON object with contribution scores for each feature
        explanation: Human-readable explanation of why this candidate is recommended
        context: JSON object with additional context (shared skills, gaps, etc.)
        is_experiment: Whether this recommendation is in an A/B test experiment
        experiment_group: A/B test group (control/treatment)
        times_shown: Number of times this recommendation has been displayed
        times_clicked: Number of times this recommendation was clicked
        click_through_rate: Calculated CTR (times_clicked / times_shown)
        dismissed: Whether the recruiter dismissed this recommendation
        dismissed_reason: Reason for dismissal (not_relevant, poor_fit, etc.)
        extra_metadata: Additional metadata about the recommendation
    """

    __tablename__ = "candidate_recommendations"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, default=None
    )

    # Recommendation type and score
    recommendation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # similar_candidates, best_fit, at_risk
    score: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.0
    )
    rank_position: Mapped[Optional[int]] = mapped_column(
        Numeric(10, 0), nullable=True, default=None
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None
    )  # skills_match, experience, education, location, etc.

    # Type-specific scores
    similarity_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )  # For similar_candidates
    risk_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )  # For at_risk candidates

    # Model metadata
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="v1.0"
    )
    algorithm: Mapped[str] = mapped_column(
        String(50), nullable=False, default="vector_similarity"
    )  # vector_similarity, collaborative_filtering, hybrid

    # Explainability
    feature_contributions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # A/B testing
    is_experiment: Mapped[bool] = mapped_column(nullable=False, default=False)
    experiment_group: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )  # 'control' or 'treatment'

    # Engagement tracking
    times_shown: Mapped[int] = mapped_column(nullable=False, default=0)
    times_clicked: Mapped[int] = mapped_column(nullable=False, default=0)
    click_through_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )

    # Dismissal tracking
    dismissed: Mapped[bool] = mapped_column(nullable=False, default=False)
    dismissed_reason: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )  # not_relevant, poor_fit, already_contacted, other

    # Additional metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CandidateRecommendation(id={self.id}, resume_id={self.resume_id}, "
            f"type={self.recommendation_type}, score={self.score}, "
            f"vacancy_id={self.vacancy_id})>"
        )


class RecommendationFeedback(Base, UUIDMixin, TimestampMixin):
    """
    RecommendationFeedback model for storing recruiter feedback on recommendations

    This model captures recruiter feedback to continuously improve the
    recommendation algorithms through supervised learning and reinforcement.

    Attributes:
        id: UUID primary key
        recommendation_id: Foreign key to CandidateRecommendation
        recruiter_id: Optional foreign key to Recruiter
        feedback_type: Type of feedback (thumbs_up/down, helpful_rating, click, dismiss, hire, reject)
        was_helpful: Whether the recommendation was helpful (for explicit feedback)
        was_actionable: Whether the recruiter took action on the recommendation
        actual_outcome: Actual outcome (hired, rejected, interviewing, pending, not_contacted)
        rating: Numerical rating (1-5 scale)
        comments: Optional text comments
        feedback_source: Source of feedback (web_ui, api, mobile, email)
        implicit_signals: JSON object with implicit feedback (dwell_time, scroll_depth, etc.)
    """

    __tablename__ = "recommendation_feedback"

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidate_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, default=None
    )

    # Feedback data
    feedback_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="thumbs"
    )  # thumbs, rating, click, dismiss, outcome
    was_helpful: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    was_actionable: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    actual_outcome: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )  # hired, rejected, interviewing, pending, not_contacted
    rating: Mapped[Optional[int]] = mapped_column(
        Numeric(3, 0), nullable=True, default=None
    )  # 1-5 star rating
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Metadata
    feedback_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="web_ui"
    )  # web_ui, api, mobile, email
    implicit_signals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RecommendationFeedback(id={self.id}, recommendation_id={self.recommendation_id}, "
            f"feedback_type={self.feedback_type}, was_helpful={self.was_helpful})>"
        )
