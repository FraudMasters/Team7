"""
Pydantic schemas for ranking accuracy analytics.

This module provides schema definitions for ML recommendation ranking metrics,
including feedback conversion rates, top-N recommendation success rates,
and overall ranking accuracy indicators.
"""
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackConversionMetrics(BaseModel):
    """Feedback conversion metrics for ranked recommendations."""

    total_recommendations: int = Field(
        ..., description="Total number of ranked recommendations generated"
    )
    recommendations_with_feedback: int = Field(
        ..., description="Number of recommendations that received recruiter feedback"
    )
    feedback_rate: float = Field(
        ..., description="Proportion of recommendations with feedback (0-1)"
    )
    positive_feedback_count: int = Field(
        ..., description="Number of recommendations with positive feedback (approved/advanced)"
    )
    negative_feedback_count: int = Field(
        ..., description="Number of recommendations with negative feedback (rejected/dismissed)"
    )
    positive_feedback_rate: float = Field(
        ..., description="Proportion of feedback that was positive (0-1)"
    )


class TopNRecommendationMetrics(BaseModel):
    """Top-N recommendation success rate metrics."""

    top_1_success_rate: float = Field(
        ..., description="Success rate for top-1 ranked candidates (0-1)"
    )
    top_3_success_rate: float = Field(
        ..., description="Success rate for top-3 ranked candidates (0-1)"
    )
    top_5_success_rate: float = Field(
        ..., description="Success rate for top-5 ranked candidates (0-1)"
    )
    top_10_success_rate: float = Field(
        ..., description="Success rate for top-10 ranked candidates (0-1)"
    )
    top_1_hired_count: int = Field(
        ..., description="Number of top-1 ranked candidates hired"
    )
    top_5_hired_count: int = Field(
        ..., description="Number of top-5 ranked candidates hired"
    )
    top_10_hired_count: int = Field(
        ..., description="Number of top-10 ranked candidates hired"
    )
    total_hires: int = Field(
        ..., description="Total number of hires in the period"
    )


class RankingConfidenceMetrics(BaseModel):
    """Ranking confidence distribution metrics."""

    high_confidence_count: int = Field(
        ..., description="Recommendations with high confidence score (>0.8)"
    )
    medium_confidence_count: int = Field(
        ..., description="Recommendations with medium confidence score (0.5-0.8)"
    )
    low_confidence_count: int = Field(
        ..., description="Recommendations with low confidence score (<0.5)"
    )
    avg_confidence_score: float = Field(
        ..., description="Average ranking confidence score across all recommendations (0-1)"
    )
    confidence_accuracy_correlation: Optional[float] = Field(
        None, description="Correlation between confidence score and actual success (0-1)"
    )


class RankingPerformanceTrend(BaseModel):
    """Ranking performance trend over time."""

    period: str = Field(..., description="Time period identifier (e.g., '2024-01')")
    success_rate: float = Field(..., description="Overall success rate for the period (0-1)")
    feedback_rate: float = Field(..., description="Feedback rate for the period (0-1)")
    avg_confidence: float = Field(..., description="Average confidence for the period (0-1)")
    total_recommendations: int = Field(..., description="Total recommendations in the period")


class RankingMetricsResponse(BaseModel):
    """Response model for ranking accuracy analytics."""

    feedback_conversion: FeedbackConversionMetrics = Field(
        ..., description="Feedback conversion metrics"
    )
    top_n_performance: TopNRecommendationMetrics = Field(
        ..., description="Top-N recommendation success rate metrics"
    )
    confidence_distribution: RankingConfidenceMetrics = Field(
        ..., description="Ranking confidence distribution metrics"
    )
    trends: Optional[list[RankingPerformanceTrend]] = Field(
        None, description="Performance trends over time"
    )
    period_start: Optional[str] = Field(
        None, description="Start date of the analysis period (ISO 8601)"
    )
    period_end: Optional[str] = Field(
        None, description="End date of the analysis period (ISO 8601)"
    )
    total_vacancies_analyzed: int = Field(
        ..., description="Total number of vacancies with ranking data"
    )


class RankingMetricsByVacancy(BaseModel):
    """Ranking metrics breakdown by individual vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    vacancy_title: str = Field(..., description="Job vacancy title")
    top_5_success_rate: float = Field(..., description="Top-5 success rate for this vacancy (0-1)")
    feedback_rate: float = Field(..., description="Feedback rate for this vacancy (0-1)")
    total_recommendations: int = Field(..., description="Total recommendations for this vacancy")
    hired_from_top_5: int = Field(..., description="Number hired from top-5 recommendations")
    avg_confidence: float = Field(..., description="Average ranking confidence (0-1)")


class RankingMetricsByRecruiter(BaseModel):
    """Ranking metrics breakdown by individual recruiter."""

    recruiter_id: str = Field(..., description="Recruiter UUID")
    recruiter_name: str = Field(..., description="Recruiter full name")
    top_5_success_rate: float = Field(..., description="Top-5 success rate for this recruiter (0-1)")
    feedback_rate: float = Field(..., description="Feedback rate for this recruiter (0-1)")
    total_recommendations_received: int = Field(
        ..., description="Total recommendations received by this recruiter"
    )
    positive_feedback_rate: float = Field(
        ..., description="Proportion of positive feedback given (0-1)"
    )


class RankingLeaderboardResponse(BaseModel):
    """Response model for ranking metrics leaderboards."""

    top_vacancies: list[RankingMetricsByVacancy] = Field(
        ..., description="Vacancies with best ranking performance"
    )
    recruiter_engagement: list[RankingMetricsByRecruiter] = Field(
        ..., description="Recruiter engagement with ranking recommendations"
    )
    period_start: Optional[str] = Field(
        None, description="Start date of the analysis period (ISO 8601)"
    )
    period_end: Optional[str] = Field(
        None, description="End date of the analysis period (ISO 8601)"
    )
