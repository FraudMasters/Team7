"""
Pydantic schemas for candidate comparison explanations.

This module provides schema definitions for side-by-side candidate comparison
analysis, including score differentials, factor-by-factor breakdowns, and
natural language explanations of ranking differences.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Comparison Request/Response Schemas
# =============================================================================


class CompareRequest(BaseModel):
    """Request to compare two candidates side-by-side."""

    resume_id_a: str = Field(..., description="First candidate resume UUID")
    resume_id_b: str = Field(..., description="Second candidate resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID for comparison context")
    use_llm: bool = Field(
        True,
        description="Whether to use LLM for natural language explanation generation"
    )


class CandidateInfo(BaseModel):
    """Information about a candidate in the comparison."""

    resume_id: str = Field(..., description="Resume UUID")
    candidate_name: str = Field(..., description="Candidate name or filename")
    rank_score: float = Field(..., description="Overall ranking score (0-1)")
    rank_position: Optional[int] = Field(
        None, description="Position in ranked list (1-based)"
    )
    confidence: float = Field(..., description="Model confidence score (0-1)")


class FactorComparison(BaseModel):
    """Factor-by-factor comparison between two candidates."""

    factor_name: str = Field(..., description="Name of the ranking factor")
    candidate_a_score: float = Field(
        ..., description="Candidate A's score for this factor (0-1)"
    )
    candidate_b_score: float = Field(
        ..., description="Candidate B's score for this factor (0-1)"
    )
    difference: float = Field(
        ..., description="Score difference (A - B), positive means A is stronger"
    )
    winner: str = Field(
        ..., description="Which candidate is stronger for this factor: 'A', 'B', or 'tie'"
    )
    explanation: str = Field(
        ..., description="Brief explanation of the difference in this factor"
    )


class ScoreDifferential(BaseModel):
    """Overall score differential analysis."""

    score_difference: float = Field(
        ..., description="Absolute score difference between candidates"
    )
    score_difference_percent: float = Field(
        ..., description="Score difference as percentage (0-100)"
    )
    higher_candidate: str = Field(
        ..., description="Which candidate scored higher: 'A' or 'B'"
    )
    margin_category: str = Field(
        ..., description="Margin category: 'significant', 'moderate', or 'slight'"
    )


class StrengthsWeaknessesTable(BaseModel):
    """Side-by-side strengths and weaknesses comparison."""

    candidate_a_strengths: List[str] = Field(
        ..., description="List of candidate A's key strengths"
    )
    candidate_b_strengths: List[str] = Field(
        ..., description="List of candidate B's key strengths"
    )
    candidate_a_weaknesses: List[str] = Field(
        ..., description="List of candidate A's areas for improvement"
    )
    candidate_b_weaknesses: List[str] = Field(
        ..., description="List of candidate B's areas for improvement"
    )


class CompareResponse(BaseModel):
    """Response containing comprehensive candidate comparison analysis."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    candidate_a_info: CandidateInfo = Field(
        ..., description="Information about candidate A"
    )
    candidate_b_info: CandidateInfo = Field(
        ..., description="Information about candidate B"
    )
    score_differential: ScoreDifferential = Field(
        ..., description="Overall score differential analysis"
    )
    factor_by_factor_comparison: List[FactorComparison] = Field(
        ..., description="Detailed factor-by-factor comparison breakdown"
    )
    winner_narrative: str = Field(
        ..., description="Natural language explanation of why one candidate ranks higher"
    )
    key_differences: List[str] = Field(
        ..., description="List of the most important differences between candidates"
    )
    strengths_weaknesses_table: StrengthsWeaknessesTable = Field(
        ..., description="Side-by-side strengths and weaknesses comparison"
    )
    recommendation: str = Field(
        ..., description="Recommendation on which candidate to prioritize"
    )
    provider: str = Field(..., description="LLM provider used for narrative generation")
    model: str = Field(..., description="Model name used for narrative generation")
    generated_at: str = Field(..., description="Timestamp of generation (ISO 8601)")
