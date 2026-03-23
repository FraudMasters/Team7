"""
Pydantic schemas for AI explainability and transparency dashboard.

This module provides schema definitions for ML model explainability features,
including confidence metrics with uncertainty quantification, feature importance
visualizations, candidate ranking rationale, and performance trend tracking.

Note: These schemas match the actual API response models defined in api/analytics.py
"""
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Confidence Metrics Schemas
# =============================================================================


class ConfidenceInterval(BaseModel):
    """Confidence interval bounds for uncertainty quantification."""

    lower: float = Field(
        ..., description="Lower bound of the confidence interval (0-1)"
    )
    upper: float = Field(
        ..., description="Upper bound of the confidence interval (0-1)"
    )
    confidence_level: float = Field(
        0.95, description="Statistical confidence level (e.g., 0.95 for 95%)"
    )


class ConfidenceDistribution(BaseModel):
    """Distribution of predictions across confidence levels."""

    high_confidence_count: int = Field(
        ..., description="Predictions with high confidence score (>=0.8)"
    )
    medium_confidence_count: int = Field(
        ..., description="Predictions with medium confidence score (0.5-0.8)"
    )
    low_confidence_count: int = Field(
        ..., description="Predictions with low confidence score (<0.5)"
    )


class ConfidenceMetricsResponse(BaseModel):
    """Response model for model confidence metrics."""

    average_confidence: float = Field(
        ..., description="Average confidence score across all predictions (0-1)"
    )
    confidence_interval: ConfidenceInterval = Field(
        ..., description="Confidence interval with uncertainty bounds"
    )
    distribution: ConfidenceDistribution = Field(
        ..., description="Distribution of predictions across confidence levels"
    )
    confidence_accuracy_correlation: Optional[float] = Field(
        None, description="Correlation between confidence score and actual accuracy (0-1)"
    )


# =============================================================================
# Feature Importance Schemas
# =============================================================================


class FeatureImportanceItem(BaseModel):
    """Single feature importance entry with description."""

    feature_name: str = Field(
        ..., description="Name of the feature used in ML model"
    )
    importance_score: float = Field(
        ..., description="Normalized importance score (0-1)"
    )
    rank: int = Field(
        ..., description="Rank of this feature by importance (1 = most important)"
    )
    description: str = Field(
        ..., description="Human-readable description of the feature"
    )
    category: str = Field(
        ..., description="Category of the feature (matching, experience, etc.)"
    )


class FeatureImportanceResponse(BaseModel):
    """Response model for feature importance from the trained model."""

    features: list[FeatureImportanceItem] = Field(
        ..., description="List of features with their importance scores, sorted by importance"
    )
    model_version: str = Field(
        "1.0.0", description="Version identifier of the trained model"
    )
    model_type: str = Field(
        "random_forest", description="Type of ML model used for ranking"
    )
    total_features: int = Field(
        ..., description="Total number of features in the model"
    )
    last_updated: str = Field(
        ..., description="Timestamp when model was last trained/updated (ISO 8601)"
    )


# =============================================================================
# Ranking Rationale Schemas
# =============================================================================


class RankingFactorDetail(BaseModel):
    """Detail of a single ranking factor."""

    factor_name: str = Field(
        ..., description="Name of the ranking factor"
    )
    score: float = Field(
        ..., description="Score for this factor (0-1 normalized)"
    )
    weight: float = Field(
        ..., description="Weight/importance of this factor in the final score"
    )
    contribution: float = Field(
        ..., description="Contribution to final score (score * weight)"
    )
    description: str = Field(
        ..., description="Human-readable explanation of this factor"
    )
    raw_value: Optional[float] = Field(
        None, description="Raw value before normalization"
    )


class SkillsMatchDetail(BaseModel):
    """Detailed skills match information."""

    matched_skills: list[str] = Field(
        ..., description="Skills the candidate has that match requirements"
    )
    missing_skills: list[str] = Field(
        ..., description="Required skills the candidate lacks"
    )
    additional_skills: list[str] = Field(
        ..., description="Extra skills the candidate has beyond requirements"
    )
    match_percentage: float = Field(
        ..., description="Percentage of required skills matched (0-100)"
    )


class RankingRationaleResponse(BaseModel):
    """Response model for explaining a specific candidate's ranking."""

    candidate_id: str = Field(
        ..., description="UUID of the candidate"
    )
    rank_score: float = Field(
        ..., description="Overall ranking score (0-1)"
    )
    rank_position: int = Field(
        ..., description="Position in the ranked list (1-based)"
    )
    narrative: str = Field(
        ..., description="Human-readable explanation of why this candidate received this ranking"
    )
    factors: list[RankingFactorDetail] = Field(
        ..., description="Breakdown of how each factor contributed to the ranking"
    )
    confidence: float = Field(
        ..., description="Model confidence in the prediction (0-1)"
    )
    strengths: list[str] = Field(
        ..., description="List of candidate's strengths identified by the model"
    )
    weaknesses: list[str] = Field(
        ..., description="List of candidate's weaknesses or areas for improvement"
    )
    skills_match: SkillsMatchDetail = Field(
        ..., description="Detailed skills matching information"
    )
    ranking_rationale: Optional[str] = Field(
        None, description="Detailed explanation of why candidate ranked at this position (when detailed mode is enabled)"
    )
    strengths_analysis: Optional[list[str]] = Field(
        None, description="Detailed analysis of candidate strengths (when detailed mode is enabled)"
    )
    improvement_areas: Optional[list[str]] = Field(
        None, description="Detailed analysis of areas for improvement (when detailed mode is enabled)"
    )
    overall_assessment: Optional[str] = Field(
        None, description="Overall assessment and summary (when detailed mode is enabled)"
    )


# =============================================================================
# Structured Visualization Data Schemas
# =============================================================================


class FeatureCategoryData(BaseModel):
    """Feature grouping data for category-level analysis."""

    category_name: str = Field(
        ..., description="Name of the feature category (e.g., 'Skills Match', 'Experience')"
    )
    category_score: float = Field(
        ..., description="Aggregate score for this category (0-1)"
    )
    weight: float = Field(
        ..., description="Weight/importance of this category in overall ranking"
    )
    features_in_category: list[str] = Field(
        ..., description="List of feature names that belong to this category"
    )
    percentile: Optional[float] = Field(
        None, description="Percentile rank for this category across all candidates (0-100)"
    )


class RelativeComparisonData(BaseModel):
    """Relative comparison metrics between candidates."""

    candidate_a_id: str = Field(
        ..., description="UUID of the first candidate being compared"
    )
    candidate_b_id: str = Field(
        ..., description="UUID of the second candidate being compared"
    )
    score_difference: float = Field(
        ..., description="Difference in overall ranking scores (A - B)"
    )
    key_differentiators: list[str] = Field(
        ..., description="Features that contribute most to the score difference"
    )
    category_comparison: list[dict[str, float]] = Field(
        ..., description="Category-by-category score comparison"
    )
    stronger_candidate: str = Field(
        ..., description="Candidate ID with the higher score"
    )


class PercentileData(BaseModel):
    """Percentile ranking data for a candidate."""

    overall_percentile: float = Field(
        ..., description="Overall percentile rank across all candidates (0-100)"
    )
    category_percentiles: dict[str, float] = Field(
        ..., description="Percentile rank for each feature category"
    )
    rank_position: int = Field(
        ..., description="Absolute position in the ranked list (1-based)"
    )
    total_candidates: int = Field(
        ..., description="Total number of candidates in the ranking pool"
    )
    score_distribution: Optional[list[float]] = Field(
        None, description="Distribution of scores across all candidates for context"
    )


class ExplainRankingResponse(BaseModel):
    """Enhanced response model for explaining a candidate's ranking with visualization data."""

    candidate_id: str = Field(
        ..., description="UUID of the candidate being explained"
    )
    vacancy_id: str = Field(
        ..., description="UUID of the vacancy this ranking is for"
    )
    rank_score: float = Field(
        ..., description="Overall ranking score (0-1)"
    )
    rank_position: int = Field(
        ..., description="Position in the ranked list (1-based)"
    )
    confidence: float = Field(
        ..., description="Model confidence in the prediction (0-1)"
    )
    narrative: str = Field(
        ..., description="Human-readable explanation of the ranking"
    )
    factors: list[RankingFactorDetail] = Field(
        ..., description="Breakdown of ranking factors with contributions"
    )
    feature_categories: list[FeatureCategoryData] = Field(
        ..., description="Feature importance grouped by category for visualization"
    )
    percentile_data: PercentileData = Field(
        ..., description="Percentile ranking information"
    )
    relative_comparisons: Optional[list[RelativeComparisonData]] = Field(
        None, description="Comparisons with other candidates if requested"
    )
    strengths: list[str] = Field(
        ..., description="List of candidate's key strengths"
    )
    weaknesses: list[str] = Field(
        ..., description="List of candidate's areas for improvement"
    )
    skills_match: SkillsMatchDetail = Field(
        ..., description="Detailed skills matching information"
    )


# =============================================================================
# Performance Trends Schemas
# =============================================================================


class PerformanceTrendPoint(BaseModel):
    """Single point in a performance trend time series."""

    timestamp: str = Field(
        ..., description="ISO 8601 timestamp for this data point"
    )
    accuracy: Optional[float] = Field(
        None, description="Model accuracy at this point"
    )
    precision: Optional[float] = Field(
        None, description="Model precision at this point"
    )
    recall: Optional[float] = Field(
        None, description="Model recall at this point"
    )
    f1_score: Optional[float] = Field(
        None, description="Model F1 score at this point"
    )
    sample_count: int = Field(
        ..., description="Number of samples in this period"
    )


class ModelPerformanceTrend(BaseModel):
    """Performance trend for a single model."""

    model_name: str = Field(
        ..., description="Name of the model"
    )
    model_version: str = Field(
        ..., description="Version of the model"
    )
    current_accuracy: float = Field(
        ..., description="Current accuracy score"
    )
    current_f1_score: float = Field(
        ..., description="Current F1 score"
    )
    trend_direction: str = Field(
        ..., description="Overall trend direction: 'improving', 'declining', or 'stable'"
    )
    trend_change_pct: float = Field(
        ..., description="Percentage change in F1 score over the period"
    )
    data_points: list[PerformanceTrendPoint] = Field(
        ..., description="Time series data points for the period"
    )
    alert_status: Optional[str] = Field(
        None, description="Alert status if performance is degraded"
    )


class PerformanceTrendsResponse(BaseModel):
    """Response model for model performance metrics over time."""

    period: str = Field(
        ..., description="The time period for the trends (e.g., '7d', '30d', '90d')"
    )
    start_date: str = Field(
        ..., description="Start date of the period (ISO 8601)"
    )
    end_date: str = Field(
        ..., description="End date of the period (ISO 8601)"
    )
    models: list[ModelPerformanceTrend] = Field(
        ..., description="Performance trends for each tracked model"
    )
    overall_trend: str = Field(
        ..., description="Overall system trend: 'improving', 'declining', or 'stable'"
    )
    total_evaluations: int = Field(
        ..., description="Total model evaluations in the period"
    )


# =============================================================================
# Legacy Aliases (for backward compatibility)
# =============================================================================

# These aliases maintain backward compatibility with code that uses the old names

FeatureContribution = RankingFactorDetail
"""Alias for backward compatibility - use RankingFactorDetail instead."""

RankingRationaleConfidenceInterval = ConfidenceInterval
"""Alias for backward compatibility."""

PerformanceMetricPoint = PerformanceTrendPoint
"""Alias for backward compatibility - use PerformanceTrendPoint instead."""

PerformanceAggregates = ModelPerformanceTrend
"""Alias for backward compatibility - structure differs, use ModelPerformanceTrend instead."""
