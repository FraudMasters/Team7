"""
Candidate activity timeline endpoints.

This module provides endpoints for retrieving candidate activity history,
including stage changes, notes additions/changes, tag modifications,
and other significant candidate events throughout the hiring process.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate_activity import CandidateActivity, CandidateActivityType
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class ActivityItem(BaseModel):
    """Single activity item in the timeline."""

    id: str = Field(..., description="Activity ID")
    activity_type: str = Field(..., description="Type of activity (e.g., 'stage_changed', 'note_added')")
    candidate_id: str = Field(..., description="Candidate (resume) ID")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID if applicable")
    from_stage: Optional[str] = Field(None, description="Previous stage for stage changes")
    to_stage: Optional[str] = Field(None, description="New stage for stage changes")
    note_id: Optional[str] = Field(None, description="Related note ID if applicable")
    tag_id: Optional[str] = Field(None, description="Related tag ID if applicable")
    recruiter_id: Optional[str] = Field(None, description="Recruiter who performed the action")
    activity_data: Optional[dict] = Field(None, description="Additional activity-specific data")
    reason: Optional[str] = Field(None, description="Reason or explanation for the activity")
    created_at: str = Field(..., description="When the activity occurred")


class ActivityTimelineResponse(BaseModel):
    """Response model for candidate activity timeline."""

    resume_id: str = Field(..., description="Resume ID")
    activities: List[ActivityItem] = Field(..., description="List of activities in chronological order")
    total_count: int = Field(..., description="Total number of activities")


@router.get(
    "/",
    response_model=ActivityTimelineResponse,
    tags=["Candidate Activities"],
)
async def get_candidate_activities(
    resume_id: Optional[str] = Query(None, description="Filter by resume (candidate) ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of activities to return"),
    offset: int = Query(0, ge=0, description="Number of activities to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get candidate activity timeline.

    This endpoint retrieves the activity history for a candidate, including
    stage changes, notes additions/changes, tag modifications, and other
    significant events throughout the hiring process.

    Activities are returned in reverse chronological order (newest first).

    Args:
        resume_id: Optional filter to get activities for a specific resume
        activity_type: Optional filter for specific activity type (e.g., 'stage_changed', 'note_added')
        vacancy_id: Optional filter for specific vacancy
        limit: Maximum number of activities to return (default: 100)
        offset: Number of activities to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of activities in chronological order

    Raises:
        HTTPException(404): If resume_id is provided and resume not found
        HTTPException(400): If activity_type is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/candidate-activities/?resume_id=abc-123")
        >>> response.json()
        {
            "resume_id": "abc-123",
            "activities": [
                {
                    "id": "act-1",
                    "activity_type": "stage_changed",
                    "candidate_id": "abc-123",
                    "vacancy_id": "vac-1",
                    "from_stage": "screening",
                    "to_stage": "interview",
                    "note_id": null,
                    "tag_id": null,
                    "recruiter_id": "rec-1",
                    "activity_data": null,
                    "reason": "Candidate passed initial screening",
                    "created_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching candidate activities - resume_id: {resume_id}, "
            f"activity_type: {activity_type}, vacancy_id: {vacancy_id}"
        )

        # Build base query
        query = select(CandidateActivity)

        # Apply filters
        if resume_id:
            # Verify resume exists
            resume_result = await db.execute(
                select(Resume).where(Resume.id == UUID(resume_id))
            )
            resume = resume_result.scalar_one_or_none()

            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume not found: {resume_id}",
                )

            query = query.where(CandidateActivity.candidate_id == UUID(resume_id))

        if vacancy_id:
            query = query.where(CandidateActivity.vacancy_id == UUID(vacancy_id))

        if activity_type:
            # Validate activity type
            valid_types = [t.value for t in CandidateActivityType]
            if activity_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid activity_type: {activity_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(CandidateActivity.activity_type == activity_type)

        # Order by created_at descending (newest first) and apply pagination
        query = query.order_by(CandidateActivity.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        activities = result.scalars().all()

        # Build response data
        activities_data = []
        for activity in activities:
            activities_data.append({
                "id": str(activity.id),
                "activity_type": activity.activity_type.value,
                "candidate_id": str(activity.candidate_id),
                "vacancy_id": str(activity.vacancy_id) if activity.vacancy_id else None,
                "from_stage": activity.from_stage,
                "to_stage": activity.to_stage,
                "note_id": str(activity.note_id) if activity.note_id else None,
                "tag_id": str(activity.tag_id) if activity.tag_id else None,
                "recruiter_id": str(activity.recruiter_id) if activity.recruiter_id else None,
                "activity_data": activity.activity_data,
                "reason": activity.reason,
                "created_at": activity.created_at.isoformat(),
            })

        # Use the resume_id from filter or first activity if not specified
        response_resume_id = resume_id if resume_id else (
            str(activities[0].candidate_id) if activities else "all"
        )

        response_data = {
            "resume_id": response_resume_id,
            "activities": activities_data,
            "total_count": len(activities_data),
        }

        logger.info(f"Retrieved {len(activities_data)} candidate activities")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format provided",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate activities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate activities: {str(e)}",
        ) from e


class ActivityTypesResponse(BaseModel):
    """Response model for available activity types."""

    activity_types: List[str] = Field(..., description="List of available activity types")


@router.get(
    "/types",
    response_model=ActivityTypesResponse,
    tags=["Candidate Activities"],
)
async def get_activity_types() -> JSONResponse:
    """
    Get available candidate activity types.

    This endpoint returns a list of all valid activity types that can be used
    for filtering candidate activities.

    Returns:
        JSON response with list of activity types

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/candidate-activities/types")
        >>> response.json()
        {
            "activity_types": [
                "stage_changed",
                "note_added",
                "note_updated",
                "note_deleted",
                "tag_added",
                "tag_removed",
                "ranking_changed",
                "rating_changed",
                "contact_attempt",
                "interview_scheduled",
                "feedback_provided",
                "status_updated"
            ]
        }
    """
    try:
        logger.info("Fetching available activity types")

        activity_types = [t.value for t in CandidateActivityType]

        response_data = {
            "activity_types": activity_types,
        }

        logger.info(f"Retrieved {len(activity_types)} activity types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving activity types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity types: {str(e)}",
        ) from e
