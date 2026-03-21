"""
Pydantic schemas for resume optimization.

This module provides schema definitions for the enhanced resume optimization
feature, including completeness scoring, ATS compatibility, skill gap analysis,
and comprehensive optimization suggestions.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SuggestionType(str, Enum):
    """Types of optimization suggestions."""

    KEYWORD = "keyword"
    FORMATTING = "formatting"
    CONTENT = "content"
    ATS = "ats"
    COMPLETENESS = "completeness"
    SKILL_GAP = "skill_gap"


class SuggestionPriority(str, Enum):
    """Priority levels for optimization suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionCategory(str, Enum):
    """Categories for optimization suggestions."""

    KEYWORDS = "keywords"
    STRUCTURE = "structure"
    READABILITY = "readability"
    IMPACT = "impact"
    ACTION_VERBS = "action_verbs"
    SUMMARY = "summary"
    ACTIVE_LANGUAGE = "active_language"
    ACHIEVEMENTS = "achievements"
    MISSING_SECTION = "missing_section"
    ATS_COMPATIBILITY = "ats_compatibility"
    SKILL_MATCH = "skill_match"


class OptimizationSuggestion(BaseModel):
    """Individual optimization suggestion with detailed recommendations."""

    type: SuggestionType = Field(
        ...,
        description="Type of suggestion (keyword, formatting, content, ats, completeness, skill_gap)",
    )
    priority: SuggestionPriority = Field(
        ...,
        description="Priority level (high, medium, low)",
    )
    category: SuggestionCategory = Field(
        ...,
        description="Specific category within the type",
    )
    title: str = Field(
        ...,
        description="Short, actionable title for the suggestion",
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the issue or opportunity",
    )
    current_state: Optional[str] = Field(
        None,
        description="Description of the current state or issue",
    )
    recommendation: str = Field(
        ...,
        description="Specific recommendation for improvement",
    )
    examples: Optional[List[str]] = Field(
        None,
        description="Examples demonstrating the recommended change",
    )


class CompletenessResult(BaseModel):
    """Resume completeness analysis result."""

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Completeness score from 0-100, based on presence of key sections",
    )
    missing_sections: List[str] = Field(
        default_factory=list,
        description="List of missing section names (e.g., 'education', 'certifications', 'projects')",
    )
    present_sections: List[str] = Field(
        default_factory=list,
        description="List of present section names",
    )
    suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="Completeness-specific suggestions for missing sections",
    )


class ATSResult(BaseModel):
    """ATS (Applicant Tracking System) compatibility analysis result."""

    passed: bool = Field(
        ...,
        description="Whether the resume passes minimum ATS threshold",
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall ATS compatibility score (0-1)",
    )
    keyword_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Keyword matching score (0-1)",
    )
    experience_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Experience relevance score (0-1)",
    )
    education_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Education match score (0-1)",
    )
    fit_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall fit score (0-1)",
    )
    ats_issues: List[str] = Field(
        default_factory=list,
        description="List of ATS-specific issues detected",
    )
    visual_issues: List[str] = Field(
        default_factory=list,
        description="List of visual/formatting issues that may affect ATS parsing",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="ATS improvement suggestions",
    )
    feedback: Optional[str] = Field(
        None,
        description="Detailed ATS feedback and recommendations",
    )


class GapSeverity(str, Enum):
    """Severity levels for skill gaps."""

    CRITICAL = "critical"
    MODERATE = "moderate"
    MINIMAL = "minimal"
    NONE = "none"


class SkillLevel(str, Enum):
    """Skill proficiency levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MissingSkillDetail(BaseModel):
    """Detailed information about a missing skill."""

    skill_name: str = Field(
        ...,
        description="Name of the missing skill",
    )
    required_level: Optional[SkillLevel] = Field(
        None,
        description="Required proficiency level for the skill",
    )
    category: Optional[str] = Field(
        None,
        description="Skill category (e.g., 'programming', 'framework', 'tool')",
    )
    importance: Optional[str] = Field(
        None,
        description="Importance level (critical, important, nice-to-have)",
    )
    estimated_time_to_learn: Optional[int] = Field(
        None,
        description="Estimated hours to achieve required proficiency",
    )


class SkillGapResult(BaseModel):
    """Skill gap analysis result."""

    candidate_skills: List[str] = Field(
        default_factory=list,
        description="Skills extracted from the resume",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills required by the job",
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills that match requirements",
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Required skills not found in resume",
    )
    partial_match_skills: Optional[List[str]] = Field(
        None,
        description="Skills present but at insufficient proficiency level",
    )
    missing_skill_details: Optional[List[MissingSkillDetail]] = Field(
        None,
        description="Detailed information about each missing skill",
    )
    gap_severity: GapSeverity = Field(
        ...,
        description="Overall severity of skill gaps (critical, moderate, minimal, none)",
    )
    gap_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of required skills missing (0-100)",
    )
    bridgeability_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score indicating how easily gaps can be bridged (0-1, higher is easier)",
    )
    estimated_time_to_bridge: Optional[int] = Field(
        None,
        description="Estimated total hours to bridge all skill gaps",
    )
    priority_ordering: Optional[List[str]] = Field(
        None,
        description="Skills ordered by priority for learning/development",
    )


class RankingPrediction(BaseModel):
    """Before/after ranking prediction for optimization impact."""

    current_rank: Optional[int] = Field(
        None,
        description="Current predicted rank among candidates",
    )
    current_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Current ranking score (0-1)",
    )
    predicted_rank: Optional[int] = Field(
        None,
        description="Predicted rank after applying optimizations",
    )
    predicted_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Predicted ranking score after optimizations (0-1)",
    )
    rank_improvement: Optional[int] = Field(
        None,
        description="Expected improvement in rank (negative = improvement)",
    )
    score_improvement: Optional[float] = Field(
        None,
        description="Expected improvement in score",
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in the prediction (0-1)",
    )


class EnhancedOptimizationResponse(BaseModel):
    """
    Enhanced response model for resume optimization analysis.

    This is the comprehensive response returned by the optimization endpoint,
    including all analysis results and suggestions.
    """

    resume_id: str = Field(
        ...,
        description="UUID of the resume being optimized",
    )
    status: str = Field(
        ...,
        description="Status of the optimization (completed, failed, pending)",
    )
    suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="List of all optimization suggestions",
    )
    total_suggestions: int = Field(
        ...,
        ge=0,
        description="Total number of suggestions generated",
    )
    high_priority_count: int = Field(
        ...,
        ge=0,
        description="Number of high-priority suggestions",
    )
    medium_priority_count: int = Field(
        ...,
        ge=0,
        description="Number of medium-priority suggestions",
    )
    low_priority_count: int = Field(
        ...,
        ge=0,
        description="Number of low-priority suggestions",
    )
    keywords_found: Optional[List[str]] = Field(
        None,
        description="Keywords found in the resume (if keyword analysis performed)",
    )
    missing_keywords: Optional[List[str]] = Field(
        None,
        description="Important keywords missing from the resume",
    )
    completeness: Optional[CompletenessResult] = Field(
        None,
        description="Resume completeness analysis result",
    )
    ats_result: Optional[ATSResult] = Field(
        None,
        description="ATS compatibility analysis result (if target job provided)",
    )
    skill_gap_result: Optional[SkillGapResult] = Field(
        None,
        description="Skill gap analysis result (if required skills provided)",
    )
    ranking_prediction: Optional[RankingPrediction] = Field(
        None,
        description="Before/after ranking prediction (if vacancy context provided)",
    )
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall optimization score (0-100, higher is better)",
    )
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Time taken to process the optimization request",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if optimization failed",
    )


class OptimizationRequest(BaseModel):
    """Request model for resume optimization."""

    target_job_description: Optional[str] = Field(
        None,
        description="Optional job description for targeted keyword matching and ATS analysis",
    )
    job_title: Optional[str] = Field(
        None,
        description="Optional job title for context",
    )
    required_skills: Optional[List[str]] = Field(
        None,
        description="Optional list of required skills for skill gap analysis",
    )
    check_keywords: bool = Field(
        True,
        description="Whether to perform keyword analysis",
    )
    check_formatting: bool = Field(
        True,
        description="Whether to provide formatting recommendations",
    )
    check_content: bool = Field(
        True,
        description="Whether to provide content improvement suggestions",
    )
    check_ats: bool = Field(
        True,
        description="Whether to perform ATS compatibility check (requires target_job_description)",
    )
    include_ranking_prediction: bool = Field(
        False,
        description="Whether to include before/after ranking prediction (requires vacancy context)",
    )
    vacancy_id: Optional[str] = Field(
        None,
        description="Optional vacancy ID for ranking prediction and comparison",
    )


class ComparisonCandidate(BaseModel):
    """Top-performing candidate for comparison."""

    candidate_id: str = Field(
        ...,
        description="Candidate UUID",
    )
    name: str = Field(
        ...,
        description="Candidate name",
    )
    ranking_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ranking score for this vacancy (0-1)",
    )
    match_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Match percentage for the vacancy",
    )
    key_strengths: List[str] = Field(
        default_factory=list,
        description="Key strengths that led to high ranking",
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Skills this candidate has",
    )


class TopCandidateComparison(BaseModel):
    """Comparison against top-performing candidates."""

    vacancy_id: str = Field(
        ...,
        description="Vacancy UUID being compared against",
    )
    vacancy_title: str = Field(
        ...,
        description="Vacancy job title",
    )
    current_resume_rank: Optional[int] = Field(
        None,
        description="Current rank of this resume among all candidates",
    )
    current_resume_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Current ranking score of this resume (0-1)",
    )
    top_candidates: List[ComparisonCandidate] = Field(
        default_factory=list,
        description="List of top-performing candidates for comparison",
    )
    total_candidates: int = Field(
        ...,
        ge=0,
        description="Total number of candidates for this vacancy",
    )
    skills_gap_vs_top: List[str] = Field(
        default_factory=list,
        description="Skills that top candidates have but this resume lacks",
    )
    competitive_insights: Optional[str] = Field(
        None,
        description="Insights on how to become more competitive",
    )
