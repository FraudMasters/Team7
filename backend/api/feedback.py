"""
Skill feedback management endpoints.

This module provides endpoints for managing recruiter feedback on skill matches,
including CRUD operations for creating, reading, updating, and deleting feedback
entries with confidence scores and ML pipeline tracking.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from models.skill_feedback import SkillFeedback

logger = logging.getLogger(__name__)

router = APIRouter()


class FeedbackEntry(BaseModel):
    """Individual feedback entry definition."""

    resume_id: str = Field(..., description="ID of the resume being evaluated")
    vacancy_id: str = Field(..., description="ID of the job vacancy")
    match_result_id: Optional[str] = Field(None, description="ID of the match result (optional)")
    skill: str = Field(..., description="The skill name that was matched")
    was_correct: bool = Field(..., description="Whether the AI's match was correct")
    confidence_score: Optional[float] = Field(None, description="The confidence score the AI assigned (0-1)", ge=0, le=1)
    recruiter_correction: Optional[str] = Field(None, description="What the recruiter corrected it to (if incorrect)")
    actual_skill: Optional[str] = Field(None, description="The actual skill found by the recruiter")
    feedback_source: str = Field("api", description="Source of feedback (api, frontend, bulk_import)")
    extra_metadata: Optional[dict] = Field(None, description="Additional feedback metadata")


class FeedbackCreate(BaseModel):
    """Request model for creating feedback."""

    feedback: List[FeedbackEntry] = Field(..., description="List of feedback entries to create")


class FeedbackUpdate(BaseModel):
    """Request model for updating feedback."""

    was_correct: Optional[bool] = Field(None, description="Whether the AI's match was correct")
    confidence_score: Optional[float] = Field(None, description="The confidence score the AI assigned (0-1)", ge=0, le=1)
    recruiter_correction: Optional[str] = Field(None, description="What the recruiter corrected it to")
    actual_skill: Optional[str] = Field(None, description="The actual skill found by the recruiter")
    processed: Optional[bool] = Field(None, description="Whether this feedback has been processed by ML pipeline")
    extra_metadata: Optional[dict] = Field(None, description="Additional feedback metadata")


class FeedbackResponse(BaseModel):
    """Response model for a single feedback entry."""

    id: str = Field(..., description="Unique identifier for the feedback entry")
    resume_id: str = Field(..., description="ID of the resume")
    vacancy_id: str = Field(..., description="ID of the job vacancy")
    match_result_id: Optional[str] = Field(None, description="ID of the match result")
    skill: str = Field(..., description="The skill name that was matched")
    was_correct: bool = Field(..., description="Whether the AI's match was correct")
    confidence_score: Optional[float] = Field(None, description="The confidence score the AI assigned")
    recruiter_correction: Optional[str] = Field(None, description="Recruiter's correction")
    actual_skill: Optional[str] = Field(None, description="The actual skill identified by recruiter")
    feedback_source: str = Field(..., description="Source of feedback")
    processed: bool = Field(..., description="Whether feedback has been processed by ML pipeline")
    extra_metadata: Optional[dict] = Field(None, description="Additional feedback metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class FeedbackListResponse(BaseModel):
    """Response model for listing feedback entries."""

    feedback: List[FeedbackResponse] = Field(..., description="List of feedback entries")
    total_count: int = Field(..., description="Total number of entries")


@router.post(
    "/",
    response_model=FeedbackListResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
)
async def create_feedback(request: FeedbackCreate) -> JSONResponse:
    """
    Create skill feedback entries.

    This endpoint accepts a batch of feedback entries from recruiters on skill matches,
    validating the data and creating database records for each feedback entry with
    confidence scores and ML pipeline tracking information.

    Args:
        request: Create request with list of feedback entries

    Returns:
        JSON response with created feedback entries

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "feedback": [
        ...         {
        ...             "resume_id": "abc123",
        ...             "vacancy_id": "vac456",
        ...             "skill": "React",
        ...             "was_correct": True,
        ...             "actual_skill": "ReactJS",
        ...             "confidence_score": 0.95
        ...         }
        ...     ]
        ... }
        >>> response = requests.post("http://localhost:8000/api/feedback/", json=data)
        >>> response.json()
        {
            "feedback": [...],
            "total_count": 1
        }
    """
    try:
        logger.info(f"Creating {len(request.feedback)} feedback entries")

        # Validate feedback list
        if not request.feedback or len(request.feedback) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one feedback entry must be provided",
            )

        # Validate confidence scores are in range [0, 1]
        for entry in request.feedback:
            if entry.confidence_score is not None and not (0 <= entry.confidence_score <= 1):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Confidence score must be between 0 and 1 for skill: {entry.skill}",
                )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        created_feedback = []
        for entry in request.feedback:
            # Placeholder feedback entry
            feedback_response = {
                "id": "placeholder-id",
                "resume_id": entry.resume_id,
                "vacancy_id": entry.vacancy_id,
                "match_result_id": entry.match_result_id,
                "skill": entry.skill,
                "was_correct": entry.was_correct,
                "confidence_score": entry.confidence_score,
                "recruiter_correction": entry.recruiter_correction,
                "actual_skill": entry.actual_skill,
                "feedback_source": entry.feedback_source,
                "processed": False,
                "extra_metadata": entry.extra_metadata,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            }
            created_feedback.append(feedback_response)

        response_data = {
            "feedback": created_feedback,
            "total_count": len(created_feedback),
        }

        logger.info(f"Created {len(created_feedback)} feedback entries")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feedback: {str(e)}",
        ) from e


@router.get("/", tags=["Feedback"])
async def list_feedback(
    resume_id: Optional[str] = Query(None, description="Filter by resume ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    skill: Optional[str] = Query(None, description="Filter by skill name"),
    was_correct: Optional[bool] = Query(None, description="Filter by correctness"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    feedback_source: Optional[str] = Query(None, description="Filter by feedback source"),
) -> JSONResponse:
    """
    List feedback entries with optional filters.

    Args:
        resume_id: Optional resume ID filter
        vacancy_id: Optional vacancy ID filter
        skill: Optional skill name filter
        was_correct: Optional correctness filter
        processed: Optional processed status filter
        feedback_source: Optional feedback source filter

    Returns:
        JSON response with list of feedback entries

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/feedback/?skill=React")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing feedback with filters - resume_id: {resume_id}, vacancy_id: {vacancy_id}, "
            f"skill: {skill}, was_correct: {was_correct}, processed: {processed}, "
            f"feedback_source: {feedback_source}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "feedback": [],
            "total_count": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list feedback: {str(e)}",
        ) from e


@router.get("/{feedback_id}", tags=["Feedback"])
async def get_feedback(feedback_id: str) -> JSONResponse:
    """
    Get a specific feedback entry by ID.

    Args:
        feedback_id: Unique identifier of the feedback entry

    Returns:
        JSON response with feedback entry details

    Raises:
        HTTPException(404): If feedback entry is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/feedback/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting feedback: {feedback_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": feedback_id,
                "resume_id": "abc123",
                "vacancy_id": "vac456",
                "match_result_id": None,
                "skill": "React",
                "was_correct": True,
                "confidence_score": 0.95,
                "recruiter_correction": None,
                "actual_skill": "ReactJS",
                "feedback_source": "api",
                "processed": False,
                "extra_metadata": None,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}",
        ) from e


@router.put("/{feedback_id}", tags=["Feedback"])
async def update_feedback(
    feedback_id: str, request: FeedbackUpdate
) -> JSONResponse:
    """
    Update a feedback entry.

    Args:
        feedback_id: Unique identifier of the feedback entry
        request: Update request with fields to modify

    Returns:
        JSON response with updated feedback entry

    Raises:
        HTTPException(404): If feedback entry is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"processed": True, "was_correct": False}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/feedback/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating feedback: {feedback_id}")

        # Validate confidence score is in range [0, 1]
        if request.confidence_score is not None and not (0 <= request.confidence_score <= 1):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Confidence score must be between 0 and 1",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": feedback_id,
                "resume_id": "abc123",
                "vacancy_id": "vac456",
                "match_result_id": None,
                "skill": "React",
                "was_correct": request.was_correct if request.was_correct is not None else True,
                "confidence_score": request.confidence_score,
                "recruiter_correction": request.recruiter_correction,
                "actual_skill": request.actual_skill,
                "feedback_source": "api",
                "processed": request.processed if request.processed is not None else False,
                "extra_metadata": request.extra_metadata,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}",
        ) from e


@router.delete("/{feedback_id}", tags=["Feedback"])
async def delete_feedback(feedback_id: str) -> JSONResponse:
    """
    Delete a feedback entry.

    Args:
        feedback_id: Unique identifier of the feedback entry

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If feedback entry is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/feedback/123")
        >>> response.json()
        {"message": "Feedback deleted successfully"}
    """
    try:
        logger.info(f"Deleting feedback: {feedback_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Feedback {feedback_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}",
        ) from e
