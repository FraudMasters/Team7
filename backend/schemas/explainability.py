"""
Pydantic schemas for AI explainability and transparency dashboard.

This module provides schema definitions for ML model explainability features,
including confidence metrics with uncertainty quantification, feature importance
visualizations, candidate ranking rationale, and performance trend tracking.
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
        ..., description="Predictions with high confidence score (>0.8)"
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

    name: str = Field(..., description="Feature name identifier")
    importance: float = Field(..., description="Importance score (0-1, normalized)")
    description: str = Field(
        ..., description="Human-readable description of what this feature measures"
    )


class FeatureImportanceResponse(BaseModel):
    """Response model for feature importance from the trained model."""

    features: list[FeatureImportanceItem] = Field(
        ..., description="List of features with their importance scores"
    )
    model_version: str = Field(
        "1.0.0", description="Version identifier of the trained model"
    )
    model_type: str = Field(
        "random_forest", description="Type of ML model used for ranking"
    )
    total_features: int = Field(
        ..., description="Total number of features used by the model"
    )


# =============================================================================
# Ranking Rationale Schemas
# =============================================================================


class FeatureContribution(BaseModel):
    """Contribution of a single feature to a candidate's ranking."""

    name: str = Field(..., description="Feature name identifier")
    value: float = Field(..., description="Raw feature value for this candidate")
    contribution: float = Field(
        ..., description="Weighted contribution to the final score (can be negative)"
    )
    impact: str = Field(
        ..., description="Impact direction: 'positive', 'negative', or 'neutral'"
    )


class RankingRationaleConfidenceInterval(BaseModel):
    """Confidence interval for a specific ranking prediction."""

    lower: float = Field(..., description="Lower bound of prediction confidence (0-1)")
    upper: float = Field(..., description="Upper bound of prediction confidence (0-1)")


class RankingRationaleResponse(BaseModel):
    """Response model for explaining a specific candidate's ranking."""

    candidate_id: str = Field(..., description="UUID of the candidate")
    rank_score: float = Field(..., description="Overall ranking score (0-1)")
    rank_position: int = Field(..., description="Position in the ranked list (1-based)")
    narrative: str = Field(
        ..., description="Human-readable explanation of why this candidate received this ranking"
    )
    feature_contributions: list[FeatureContribution] = Field(
        ..., description="Breakdown of how each feature contributed to the ranking"
    )
    strengths: list[str] = Field(
        ..., description="List of candidate's strengths identified by the model"
    )
    weaknesses: list[str] = Field(
        ..., description="List of candidate's weaknesses or areas for improvement"
    )
    confidence_interval: RankingRationaleConfidenceInterval = Field(
        ..., description="Confidence interval for this specific prediction"
    )


# =============================================================================
# Performance Trends Schemas
# =============================================================================


class PerformanceMetricPoint(BaseModel):
    """Single data point in the performance metrics time series."""

    date: str = Field(..., description="Date of the measurement (ISO 8601)")
    accuracy: float = Field(..., description="Accuracy score for this period (0-1)")
    f1_score: float = Field(..., description="F1 score for this period (0-1)")
    ndcg_score: float = Field(
        ..., description="Normalized Discounted Cumulative Gain for this period (0-1)"
    )
    sample_size: int = Field(
        ..., description="Number of predictions evaluated in this period"
    )


class PerformanceAggregates(BaseModel):
    """Aggregated statistics over the analysis period."""

    avg_accuracy: float = Field(..., description="Average accuracy over the period (0-1)")
    avg_f1: float = Field(..., description="Average F1 score over the period (0-1)")
    accuracy_change_pct: float = Field(
        ..., description="Percentage change in accuracy from start to end of period"
    )


class PerformanceTrendsResponse(BaseModel):
    """Response model for model performance metrics over time."""

    period: str = Field(
        ..., description="Analysis period identifier (e.g., '7d', '30d', '90d')"
    )
    trend_direction: str = Field(
        ..., description="Overall trend: 'improving', 'stable', or 'declining'"
    )
    metrics: list[PerformanceMetricPoint] = Field(
        ..., description="Time series of performance metrics"
    )
    aggregates: PerformanceAggregates = Field(
        ..., description="Aggregated statistics for the period"
    )
    period_start: Optional[str] = Field(
        None, description="Start date of the analysis period (ISO 8601)"
    )
    period_end: Optional[str] = Field(
        None, description="End date of the analysis period (ISO 8601)"
    )
    total_predictions: int = Field(
        ..., description="Total number of predictions analyzed in this period"
    )
