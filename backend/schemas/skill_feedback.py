"""
Pydantic schemas for skill feedback validation.

This module provides schema definitions for recruiter feedback on AI skill matching,
including request/response models for CRUD operations, confidence score tracking,
and ML pipeline integration for continuous model improvement.

Note: These schemas are used by the feedback API endpoints defined in api/feedback.py
"""
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Skill Feedback Entry Schemas
# =============================================================================


class SkillFeedbackEntry(BaseModel):
    """Individual skill feedback entry from a recruiter."""

    resume_id: str = Field(
        ..., description="ID of the resume being evaluated"
    )
    vacancy_id: str = Field(
        ..., description="ID of the job vacancy"
    )
    match_result_id: Optional[str] = Field(
        None, description="ID of the match result (optional)"
    )
    skill: str = Field(
        ..., description="The skill name that was matched by the AI"
    )
    was_correct: bool = Field(
        ..., description="Whether the AI's skill match was correct"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="The confidence score the AI assigned to this match (0-1)",
        ge=0,
        le=1,
    )
    recruiter_correction: Optional[str] = Field(
        None, description="What the recruiter corrected the skill to (if incorrect)"
    )
    actual_skill: Optional[str] = Field(
        None, description="The actual skill name identified by the recruiter"
    )
    feedback_source: str = Field(
        "api", description="Source of feedback (api, frontend, bulk_import)"
    )
    extra_metadata: Optional[dict] = Field(
        None, description="Additional feedback metadata and context"
    )


# =============================================================================
# Request Schemas
# =============================================================================


class SkillFeedbackCreate(BaseModel):
    """Request model for creating skill feedback entries."""

    feedback: list[SkillFeedbackEntry] = Field(
        ..., description="List of feedback entries to create"
    )


class SkillFeedbackUpdate(BaseModel):
    """Request model for updating an existing feedback entry."""

    was_correct: Optional[bool] = Field(
        None, description="Whether the AI's match was correct"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="The confidence score the AI assigned (0-1)",
        ge=0,
        le=1,
    )
    recruiter_correction: Optional[str] = Field(
        None, description="What the recruiter corrected the skill to"
    )
    actual_skill: Optional[str] = Field(
        None, description="The actual skill identified by the recruiter"
    )
    processed: Optional[bool] = Field(
        None, description="Whether this feedback has been processed by ML pipeline"
    )
    extra_metadata: Optional[dict] = Field(
        None, description="Additional feedback metadata"
    )


# =============================================================================
# Response Schemas
# =============================================================================


class SkillFeedbackResponse(BaseModel):
    """Response model for a single skill feedback entry."""

    id: str = Field(
        ..., description="Unique identifier for the feedback entry"
    )
    resume_id: str = Field(
        ..., description="ID of the resume"
    )
    vacancy_id: str = Field(
        ..., description="ID of the job vacancy"
    )
    match_result_id: Optional[str] = Field(
        None, description="ID of the match result"
    )
    skill: str = Field(
        ..., description="The skill name that was matched by the AI"
    )
    was_correct: bool = Field(
        ..., description="Whether the AI's match was correct"
    )
    confidence_score: Optional[float] = Field(
        None, description="The confidence score the AI assigned (0-1)"
    )
    recruiter_correction: Optional[str] = Field(
        None, description="Recruiter's correction if the match was incorrect"
    )
    actual_skill: Optional[str] = Field(
        None, description="The actual skill identified by the recruiter"
    )
    feedback_source: str = Field(
        ..., description="Source of feedback (api, frontend, bulk_import)"
    )
    processed: bool = Field(
        ..., description="Whether feedback has been processed by ML pipeline"
    )
    extra_metadata: Optional[dict] = Field(
        None, description="Additional feedback metadata"
    )
    created_at: str = Field(
        ..., description="Creation timestamp (ISO 8601)"
    )
    updated_at: str = Field(
        ..., description="Last update timestamp (ISO 8601)"
    )


class SkillFeedbackListResponse(BaseModel):
    """Response model for listing multiple feedback entries."""

    feedback: list[SkillFeedbackResponse] = Field(
        ..., description="List of feedback entries"
    )
    total_count: int = Field(
        ..., description="Total number of feedback entries"
    )


# =============================================================================
# Analytics Schemas
# =============================================================================


class SkillFeedbackStats(BaseModel):
    """Statistics aggregated from skill feedback data."""

    total_feedback_count: int = Field(
        ..., description="Total number of feedback entries"
    )
    correct_matches_count: int = Field(
        ..., description="Number of correct AI matches"
    )
    incorrect_matches_count: int = Field(
        ..., description="Number of incorrect AI matches"
    )
    accuracy_rate: float = Field(
        ..., description="Overall accuracy rate of AI skill matching (0-1)"
    )
    average_confidence: float = Field(
        ..., description="Average confidence score across all feedback (0-1)"
    )
    processed_count: int = Field(
        ..., description="Number of feedback entries processed by ML pipeline"
    )
    pending_count: int = Field(
        ..., description="Number of feedback entries pending ML processing"
    )


class SkillFeedbackBySkill(BaseModel):
    """Feedback statistics broken down by individual skill."""

    skill_name: str = Field(
        ..., description="Name of the skill"
    )
    total_count: int = Field(
        ..., description="Total feedback entries for this skill"
    )
    correct_count: int = Field(
        ..., description="Correct matches for this skill"
    )
    incorrect_count: int = Field(
        ..., description="Incorrect matches for this skill"
    )
    accuracy_rate: float = Field(
        ..., description="Accuracy rate for this skill (0-1)"
    )
    average_confidence: float = Field(
        ..., description="Average confidence score for this skill (0-1)"
    )
