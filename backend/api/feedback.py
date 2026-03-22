"""
Skill feedback management endpoints.

This module provides endpoints for managing recruiter feedback on skill matches,
including CRUD operations for creating, reading, updating, and deleting feedback
entries with confidence scores and ML pipeline tracking.
"""
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.skill_feedback import SkillFeedback

logger = logging.getLogger(__name__)

router = APIRouter()


def _feedback_to_dict(feedback: SkillFeedback) -> dict:
    """
    Convert SkillFeedback model to dictionary for API response.

    Args:
        feedback: SkillFeedback model instance

    Returns:
        Dictionary with feedback data
    """
    return {
        "id": str(feedback.id),
        "resume_id": str(feedback.resume_id),
        "vacancy_id": str(feedback.vacancy_id),
        "match_result_id": str(feedback.match_result_id) if feedback.match_result_id else None,
        "skill": feedback.skill,
        "was_correct": feedback.was_correct,
        "confidence_score": feedback.confidence_score,
        "recruiter_correction": feedback.recruiter_correction,
        "actual_skill": feedback.actual_skill,
        "feedback_source": feedback.feedback_source,
        "processed": feedback.processed,
        "extra_metadata": feedback.extra_metadata,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None,
    }


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
async def create_feedback(
    request: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
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
        >>> response = requests.post("/api/feedback/", json=data)
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

        # Create database records
        created_feedback = []
        for entry in request.feedback:
            # Convert string IDs to UUIDs
            try:
                resume_uuid = UUID(entry.resume_id)
                vacancy_uuid = UUID(entry.vacancy_id)
                match_result_uuid = UUID(entry.match_result_id) if entry.match_result_id else None
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid UUID format: {str(e)}",
                ) from e

            # Create feedback entry
            feedback = SkillFeedback(
                id=uuid4(),
                resume_id=resume_uuid,
                vacancy_id=vacancy_uuid,
                match_result_id=match_result_uuid,
                skill=entry.skill,
                was_correct=entry.was_correct,
                confidence_score=entry.confidence_score,
                recruiter_correction=entry.recruiter_correction,
                actual_skill=entry.actual_skill,
                feedback_source=entry.feedback_source,
                processed=False,
                extra_metadata=entry.extra_metadata,
            )

            db.add(feedback)
            created_feedback.append(feedback)

        # Commit all feedback entries
        await db.commit()

        # Refresh all entries to get timestamps
        for feedback in created_feedback:
            await db.refresh(feedback)

        # Convert to response format
        response_data = {
            "feedback": [_feedback_to_dict(fb) for fb in created_feedback],
            "total_count": len(created_feedback),
        }

        logger.info(f"Created {len(created_feedback)} feedback entries")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error creating feedback: {e}", exc_info=True)
        await db.rollback()
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
    db: AsyncSession = Depends(get_db)
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
        >>> response = requests.get("/api/feedback/?skill=React")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing feedback with filters - resume_id: {resume_id}, vacancy_id: {vacancy_id}, "
            f"skill: {skill}, was_correct: {was_correct}, processed: {processed}, "
            f"feedback_source: {feedback_source}"
        )

        # Build query with filters
        query = select(SkillFeedback)

        if resume_id:
            try:
                resume_uuid = UUID(resume_id)
                query = query.where(SkillFeedback.resume_id == resume_uuid)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid resume_id UUID format: {str(e)}",
                ) from e

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(SkillFeedback.vacancy_id == vacancy_uuid)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy_id UUID format: {str(e)}",
                ) from e

        if skill:
            query = query.where(SkillFeedback.skill == skill)

        if was_correct is not None:
            query = query.where(SkillFeedback.was_correct == was_correct)

        if processed is not None:
            query = query.where(SkillFeedback.processed == processed)

        if feedback_source:
            query = query.where(SkillFeedback.feedback_source == feedback_source)

        # Execute query
        result = await db.execute(query)
        feedback_list = result.scalars().all()

        # Convert to response format
        response_data = {
            "feedback": [_feedback_to_dict(fb) for fb in feedback_list],
            "total_count": len(feedback_list),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error listing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error listing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list feedback: {str(e)}",
        ) from e


@router.get("/{feedback_id}", tags=["Feedback"])
async def get_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
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
        >>> response = requests.get("/api/feedback/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting feedback: {feedback_id}")

        # Convert string ID to UUID
        try:
            feedback_uuid = UUID(feedback_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid feedback_id UUID format: {str(e)}",
            ) from e

        # Query feedback by ID
        result = await db.execute(
            select(SkillFeedback).where(SkillFeedback.id == feedback_uuid)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback entry not found: {feedback_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_feedback_to_dict(feedback),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}",
        ) from e


@router.put("/{feedback_id}", tags=["Feedback"])
async def update_feedback(
    feedback_id: str,
    request: FeedbackUpdate,
    db: AsyncSession = Depends(get_db)
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
        ...     "/api/feedback/123",
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

        # Convert string ID to UUID
        try:
            feedback_uuid = UUID(feedback_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid feedback_id UUID format: {str(e)}",
            ) from e

        # Query feedback by ID
        result = await db.execute(
            select(SkillFeedback).where(SkillFeedback.id == feedback_uuid)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback entry not found: {feedback_id}",
            )

        # Update fields if provided
        if request.was_correct is not None:
            feedback.was_correct = request.was_correct

        if request.confidence_score is not None:
            feedback.confidence_score = request.confidence_score

        if request.recruiter_correction is not None:
            feedback.recruiter_correction = request.recruiter_correction

        if request.actual_skill is not None:
            feedback.actual_skill = request.actual_skill

        if request.processed is not None:
            feedback.processed = request.processed

        if request.extra_metadata is not None:
            feedback.extra_metadata = request.extra_metadata

        # Commit changes
        await db.commit()
        await db.refresh(feedback)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_feedback_to_dict(feedback),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error updating feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}",
        ) from e


@router.delete("/{feedback_id}", tags=["Feedback"])
async def delete_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
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
        >>> response = requests.delete("/api/feedback/123")
        >>> response.json()
        {"message": "Feedback deleted successfully"}
    """
    try:
        logger.info(f"Deleting feedback: {feedback_id}")

        # Convert string ID to UUID
        try:
            feedback_uuid = UUID(feedback_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid feedback_id UUID format: {str(e)}",
            ) from e

        # Query feedback by ID
        result = await db.execute(
            select(SkillFeedback).where(SkillFeedback.id == feedback_uuid)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback entry not found: {feedback_id}",
            )

        # Delete feedback
        await db.delete(feedback)
        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Feedback {feedback_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}",
        ) from e
