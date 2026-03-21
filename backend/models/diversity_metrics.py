"""
DiversityMetrics model for tracking demographic representation in hiring pipelines

This model stores aggregated diversity and inclusion metrics across the hiring process,
enabling organizations to monitor demographic representation, track progress toward
diversity goals, and ensure equitable hiring practices.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DiversityMetrics(Base, UUIDMixin, TimestampMixin):
    """
    DiversityMetrics model for tracking demographic representation in hiring pipelines

    This model aggregates diversity metrics across job vacancies, pipeline stages,
    and time periods to provide comprehensive insights into demographic representation
    and support data-driven diversity and inclusion initiatives.

    Attributes:
        id: UUID primary key
        organization_id: Foreign key to Organization
        vacancy_id: Foreign key to JobVacancy (optional, for role-specific metrics)
        pipeline_stage_id: Foreign key to PipelineStageTransition (optional, for stage-specific metrics)

        # Time period
        period_start: Start date of the metrics period (YYYY-MM-DD)
        period_end: End date of the metrics period (YYYY-MM-DD)
        period_type: Type of period (daily, weekly, monthly, quarterly, yearly, custom)

        # Demographic group
        demographic_category: Category being tracked (gender, age_group, ethnicity, etc.)
        demographic_value: Specific value within category (e.g., "female", "25-34")

        # Counts and statistics
        total_candidates: Total number of candidates in this group
        total_applicants: Total applicants in this group
        candidates_screened: Number of candidates who passed initial screening
        candidates_interviewed: Number of candidates who were interviewed
        candidates_offered: Number of candidates who received offers
        candidates_hired: Number of candidates who were hired
        candidates_rejected: Number of candidates rejected at any stage

        # Percentages and rates
        representation_percentage: Percentage of total pool this group represents
        screening_rate: Percentage of group that passed screening
        interview_rate: Percentage of group that reached interview stage
        offer_rate: Percentage of group that received offers
        hire_rate: Percentage of group that was hired
        conversion_rate: Overall conversion rate from application to hire

        # Diversity goals and targets
        target_representation: Target percentage for this demographic group
        goal_met: Whether the diversity goal was met
        variance_from_target: Percentage difference from target (positive = above, negative = below)

        # Comparison metrics
        overall_pool_percentage: Percentage this group represents in overall talent pool
        industry_benchmark: Industry standard percentage for this demographic
        prior_period_percentage: Percentage from previous comparable period
        year_over_year_change: Change in representation from same period last year

        # Detailed breakdowns
        stage_breakdown: JSON object with counts per pipeline stage
        source_breakdown: JSON object with counts per application source
        department_breakdown: JSON object with counts per department (if applicable)

        # Trend indicators
        trend_direction: Direction of trend (increasing, decreasing, stable)
        trend_confidence: Confidence level in trend analysis (0-1)

        # Metadata and analysis
        sample_size: Total sample size for statistical validity
        confidence_level: Statistical confidence level (e.g., 0.95)
        margin_of_error: Margin of error for percentages
        data_quality_score: Quality score for underlying data (0-1)
        analysis_notes: Optional notes about the analysis
        metadata: JSON object with additional analysis details
    """

    __tablename__ = "diversity_metrics"

    # References
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    pipeline_stage_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pipeline_stage_transitions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Time period
    period_start: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    period_end: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    period_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # daily, weekly, monthly, quarterly, yearly, custom

    # Demographic group
    demographic_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # gender, age_group, ethnicity, geographic_region, etc.
    demographic_value: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # specific value within category

    # Counts
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_applicants: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_screened: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_interviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_offered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_hired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Percentages and rates (stored as decimals, e.g., 0.45 = 45%)
    representation_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    screening_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    interview_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    offer_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    hire_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    conversion_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # Diversity goals and targets
    target_representation: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    goal_met: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    variance_from_target: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # Can be negative

    # Comparison metrics
    overall_pool_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    industry_benchmark: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    prior_period_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    year_over_year_change: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # Can be negative

    # Detailed breakdowns (JSON objects)
    stage_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    department_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Trend indicators
    trend_direction: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # increasing, decreasing, stable
    trend_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )  # 0-1

    # Statistical validity
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_level: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True, default=0.95
    )
    margin_of_error: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    data_quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )  # 0-1

    # Additional metadata
    analysis_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DiversityMetrics("
            f"id={self.id}, "
            f"period={self.period_start} to {self.period_end}, "
            f"category={self.demographic_category}, "
            f"value={self.demographic_value}, "
            f"representation={self.representation_percentage})>"
        )


class DiversityGoal(Base, UUIDMixin, TimestampMixin):
    """
    DiversityGoal model for storing diversity and inclusion targets

    This model defines organizational goals for demographic representation
    across different categories, enabling goal tracking and progress monitoring.

    Attributes:
        id: UUID primary key
        organization_id: Foreign key to Organization
        vacancy_id: Foreign key to JobVacancy (optional, for role-specific goals)

        # Goal definition
        goal_name: Name of the diversity goal
        goal_description: Detailed description of the goal
        demographic_category: Category being targeted (gender, age_group, ethnicity, etc.)
        demographic_value: Specific value within category

        # Target metrics
        target_percentage: Target percentage for representation
        target_count: Target absolute count (optional)
        baseline_percentage: Starting percentage when goal was set
        baseline_count: Starting count when goal was set

        # Timeline
        start_date: When the goal period starts
        target_date: When the goal should be achieved by
        review_frequency: How often to review progress (monthly, quarterly, etc.)

        # Progress tracking
        current_percentage: Current percentage toward goal
        current_count: Current count toward goal
        progress_percentage: Percentage of goal achieved (0-1)
        on_track: Whether goal is on track for completion

        # Status
        status: Status of the goal (active, achieved, missed, cancelled)
        priority: Priority level (low, medium, high, critical)
        is_public: Whether this goal is publicly communicated

        # Accountability
        owner_id: User ID of person responsible for this goal
        review_notes: JSON array of review notes with timestamps

        # Metadata
        goal_metadata: JSON object with additional goal details
    """

    __tablename__ = "diversity_goals"

    # References
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Goal definition
    goal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    goal_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demographic_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    demographic_value: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    # Target metrics
    target_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    target_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    baseline_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    baseline_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timeline
    start_date: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_date: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    review_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # weekly, monthly, quarterly, yearly

    # Progress tracking
    current_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    current_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )  # 0-1
    on_track: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, achieved, missed, cancelled
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical
    is_public: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Accountability
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )
    review_notes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Metadata
    goal_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DiversityGoal("
            f"id={self.id}, "
            f"name={self.goal_name}, "
            f"category={self.demographic_category}, "
            f"target={self.target_percentage}, "
            f"status={self.status})>"
        )
