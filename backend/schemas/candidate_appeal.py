"""
Pydantic schemas for candidate appeals API.

This module provides schema definitions for the candidate appeals system,
allowing candidates to challenge AI ranking decisions and provide additional
context that may have been missed during initial evaluation. Supports multiple
appeal types (ranking_position, score_explanation, missing_skills) with
supporting documentation and recruiter review workflows.
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# Appeal Submission Schemas
# =============================================================================


class AppealCreate(BaseModel):
    """Request model for creating a candidate appeal."""

    candidate_rank_id: str = Field(
        ..., description="UUID of the candidate rank being appealed"
    )
    candidate_email: EmailStr = Field(
        ..., description="Email address of the candidate submitting the appeal"
    )
    appeal_type: str = Field(
        ..., description="Type of appeal: ranking_position, score_explanation, or missing_skills"
    )
    appeal_text: str = Field(
        ..., description="Candidate's explanation and additional context (min 10 characters)", min_length=10
    )
    supporting_documents: Optional[dict] = Field(
        None, description="Metadata for uploaded supporting documents (e.g., certifications, portfolios)"
    )


class AppealUpdate(BaseModel):
    """Request model for updating an appeal (recruiter use)."""

    status: Optional[str] = Field(
        None, description="Appeal status: pending, under_review, accepted, rejected"
    )
    reviewer_id: Optional[str] = Field(
        None, description="UUID of the recruiter reviewing the appeal"
    )
    review_notes: Optional[str] = Field(
        None, description="Internal notes from the reviewer"
    )
    resolution_outcome: Optional[str] = Field(
        None, description="Description of final action taken (e.g., 'Re-ranked with new information')"
    )


# =============================================================================
# Appeal Response Schemas
# =============================================================================


class AppealResponse(BaseModel):
    """Response model for a single appeal."""

    id: str = Field(..., description="Unique identifier for the appeal")
    candidate_rank_id: str = Field(..., description="UUID of the candidate rank")
    candidate_email: str = Field(..., description="Email of the candidate")
    appeal_type: str = Field(..., description="Type of appeal")
    appeal_text: str = Field(..., description="Appeal explanation text")
    supporting_documents: Optional[dict] = Field(None, description="Supporting documents metadata")
    status: str = Field(..., description="Current status of the appeal")
    reviewer_id: Optional[str] = Field(None, description="UUID of reviewing recruiter")
    review_notes: Optional[str] = Field(None, description="Reviewer notes")
    resolution_outcome: Optional[str] = Field(None, description="Final resolution description")
    created_at: str = Field(..., description="Timestamp when appeal was created (ISO 8601)")
    updated_at: str = Field(..., description="Timestamp when appeal was last updated (ISO 8601)")


class AppealListResponse(BaseModel):
    """Response model for listing appeals."""

    appeals: list[AppealResponse] = Field(..., description="List of appeals")
    total_count: int = Field(..., description="Total number of appeals matching filters")


class AppealReviewRequest(BaseModel):
    """Request model for reviewing an appeal (recruiter action)."""

    status: str = Field(
        ..., description="New status: under_review, accepted, or rejected"
    )
    review_notes: Optional[str] = Field(
        None, description="Reviewer's internal notes"
    )
    resolution_outcome: Optional[str] = Field(
        None, description="Description of action taken or decision rationale"
    )
