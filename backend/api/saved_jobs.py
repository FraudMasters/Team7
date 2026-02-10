"""
Saved Jobs API endpoints for managing job seeker's saved/bookmarked jobs.

This module provides endpoints for job seekers to save, unsave, and list
jobs they have bookmarked for later review and application.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.saved_job import SavedJob
from models.job_vacancy import JobVacancy
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SaveJobRequest(BaseModel):
    """Request model for saving a job."""

    vacancy_id: str = Field(..., description="Job vacancy ID to save")
    user_id: str = Field(..., description="User ID who is saving the job")


class SavedJobResponse(BaseModel):
    """Response model for a saved job."""

    id: str = Field(..., description="Saved job ID")
    user_id: str = Field(..., description="User ID who saved the job")
    vacancy_id: str = Field(..., description="Job vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Job vacancy title")
    vacancy_description: Optional[str] = Field(None, description="Job vacancy description")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SavedJobsListResponse(BaseModel):
    """Response model for listing saved jobs."""

    total: int = Field(..., description="Total number of saved jobs")
    saved_jobs: list[SavedJobResponse] = Field(..., description="List of saved jobs")


def _saved_job_to_response(saved_job: SavedJob, vacancy: Optional[JobVacancy] = None) -> dict:
    """Convert SavedJob model to response dict."""
    response = {
        "id": str(saved_job.id),
        "user_id": str(saved_job.user_id),
        "vacancy_id": str(saved_job.vacancy_id),
        "vacancy_title": None,
        "vacancy_description": None,
        "created_at": saved_job.created_at.isoformat() if saved_job.created_at else None,
        "updated_at": saved_job.updated_at.isoformat() if saved_job.updated_at else None,
    }

    if vacancy:
        response["vacancy_title"] = vacancy.title
        response["vacancy_description"] = vacancy.description

    return response


@router.post(
    "/save",
    response_model=SavedJobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Saved Jobs"],
)
async def save_job(
    request: Request,
    save_data: SaveJobRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Save a job vacancy.

    This endpoint allows job seekers to save/bookmark a job vacancy for later review.
    Attempting to save the same job twice will return a 409 Conflict error.

    Args:
        request: FastAPI request object
        save_data: Save job data (vacancy_id, user_id)
        db: Database session

    Returns:
        JSON response with saved job details

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(409): If job already saved by this user
        HTTPException(500): If database operation fails

    Example:
        >>> save_data = {"vacancy_id": "abc-123-def", "user_id": "user-uuid"}
        >>> response = requests.post("/api/saved-jobs/save", json=save_data)
    """
    try:
        # Parse vacancy_id and user_id as UUIDs
        try:
            vacancy_uuid = UUID(save_data.vacancy_id)
            user_uuid = UUID(save_data.user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}",
            ) from e

        # Check if vacancy exists
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {save_data.vacancy_id}",
            )

        # Check if job already saved by this user
        existing_query = select(SavedJob).where(
            SavedJob.user_id == user_uuid,
            SavedJob.vacancy_id == vacancy_uuid
        )
        existing_result = await db.execute(existing_query)
        existing_saved_job = existing_result.scalar_one_or_none()

        if existing_saved_job:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job already saved by this user",
            )

        # Create new SavedJob instance
        new_saved_job = SavedJob(
            user_id=user_uuid,
            vacancy_id=vacancy_uuid,
        )

        db.add(new_saved_job)
        await db.commit()
        await db.refresh(new_saved_job)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.JOB_SAVED,
            entity_type="saved_job",
            entity_id=new_saved_job.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value=_saved_job_to_response(new_saved_job, vacancy),
        )

        logger.info(f"Saved job: {new_saved_job.id} - vacancy: {vacancy.title} for user: {user_uuid}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_saved_job_to_response(new_saved_job, vacancy),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving job: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save job: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=SavedJobsListResponse,
    tags=["Saved Jobs"],
)
async def list_saved_jobs(
    request: Request,
    user_id: str = Query(..., description="User ID to get saved jobs for"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List saved jobs for a user.

    Returns a paginated list of all saved jobs for a specific user,
    including the vacancy details.

    Args:
        request: FastAPI request object
        user_id: User ID to get saved jobs for
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of saved jobs and total count

    Raises:
        HTTPException(400): Invalid user ID format
        HTTPException(500): If data retrieval fails

    Example:
        >>> response = requests.get("/api/saved-jobs/?user_id=user-uuid&limit=10")
        >>> saved_jobs = response.json()
    """
    try:
        # Parse user_id as UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user ID format: {user_id}",
            )

        logger.info(f"Listing saved jobs for user: {user_uuid}")

        # Get total count
        count_query = select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user_uuid)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Query saved jobs with vacancy details
        query = (
            select(SavedJob, JobVacancy)
            .join(JobVacancy, SavedJob.vacancy_id == JobVacancy.id)
            .where(SavedJob.user_id == user_uuid)
            .order_by(SavedJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        # Convert to response format
        saved_jobs_list = []
        for saved_job, vacancy in rows:
            saved_jobs_list.append(_saved_job_to_response(saved_job, vacancy))

        logger.info(f"Retrieved {len(saved_jobs_list)} saved jobs for user {user_uuid} (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "saved_jobs": saved_jobs_list,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing saved jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list saved jobs: {str(e)}",
        ) from e


@router.get(
    "/check",
    tags=["Saved Jobs"],
)
async def check_job_saved(
    request: Request,
    vacancy_id: str = Query(..., description="Vacancy ID to check"),
    user_id: str = Query(..., description="User ID to check for"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Check if a job is saved by a user.

    Returns whether a specific job vacancy is saved by a specific user.

    Args:
        request: FastAPI request object
        vacancy_id: Vacancy ID to check
        user_id: User ID to check for
        db: Database session

    Returns:
        JSON response with is_saved boolean and saved_job_id if saved

    Raises:
        HTTPException(400): Invalid UUID format
        HTTPException(500): If check fails

    Example:
        >>> response = requests.get("/api/saved-jobs/check?vacancy_id=vac-uuid&user_id=user-uuid")
        >>> result = response.json()
        >>> # {"is_saved": true, "saved_job_id": "saved-job-uuid"}
    """
    try:
        # Parse vacancy_id and user_id as UUIDs
        try:
            vacancy_uuid = UUID(vacancy_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format",
            )

        # Check if job is saved
        query = select(SavedJob).where(
            SavedJob.user_id == user_uuid,
            SavedJob.vacancy_id == vacancy_uuid
        )
        result = await db.execute(query)
        saved_job = result.scalar_one_or_none()

        is_saved = saved_job is not None
        saved_job_id = str(saved_job.id) if saved_job else None

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "is_saved": is_saved,
                "saved_job_id": saved_job_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking if job saved: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check if job saved: {str(e)}",
        ) from e


@router.delete(
    "/{saved_job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Saved Jobs"],
)
async def unsave_job(
    request: Request,
    saved_job_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Unsave a job (delete saved job).

    Permanently removes a saved job from the user's saved jobs list.

    Args:
        request: FastAPI request object
        saved_job_id: Saved job ID to delete
        db: Database session

    Returns:
        HTTP 204 No Content on successful deletion

    Raises:
        HTTPException(400): Invalid saved job ID format
        HTTPException(404): Saved job not found
        HTTPException(500): If database operation fails

    Example:
        >>> response = requests.delete("/api/saved-jobs/saved-job-uuid")
        >>> response.status_code
        204
    """
    try:
        # Parse saved_job_id as UUID
        try:
            saved_job_uuid = UUID(saved_job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid saved job ID format: {saved_job_id}",
            )

        # Get the saved job
        query = select(SavedJob).where(SavedJob.id == saved_job_uuid)
        result = await db.execute(query)
        saved_job = result.scalar_one_or_none()

        if not saved_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved job not found: {saved_job_id}",
            )

        # Capture before state for audit log
        before_state = _saved_job_to_response(saved_job)

        # Delete saved job
        await db.delete(saved_job)
        await db.commit()

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.JOB_UNSAVED,
            entity_type="saved_job",
            entity_id=saved_job.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
        )

        logger.info(f"Unsaved job: {saved_job_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving job: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsave job: {str(e)}",
        ) from e


@router.delete(
    "/unsave",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Saved Jobs"],
)
async def unsave_job_by_vacancy(
    request: Request,
    vacancy_id: str = Query(..., description="Vacancy ID to unsave"),
    user_id: str = Query(..., description="User ID who saved the job"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Unsave a job by vacancy and user ID.

    Removes a saved job using the vacancy_id and user_id combination
    instead of the saved_job ID. This is a convenience endpoint.

    Args:
        request: FastAPI request object
        vacancy_id: Vacancy ID to unsave
        user_id: User ID who saved the job
        db: Database session

    Returns:
        HTTP 204 No Content on successful deletion

    Raises:
        HTTPException(400): Invalid UUID format
        HTTPException(404): Saved job not found
        HTTPException(500): If database operation fails

    Example:
        >>> response = requests.delete("/api/saved-jobs/unsave?vacancy_id=vac-uuid&user_id=user-uuid")
        >>> response.status_code
        204
    """
    try:
        # Parse vacancy_id and user_id as UUIDs
        try:
            vacancy_uuid = UUID(vacancy_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format",
            )

        # Get the saved job
        query = select(SavedJob).where(
            SavedJob.user_id == user_uuid,
            SavedJob.vacancy_id == vacancy_uuid
        )
        result = await db.execute(query)
        saved_job = result.scalar_one_or_none()

        if not saved_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved job not found",
            )

        # Capture before state for audit log
        before_state = _saved_job_to_response(saved_job)

        # Delete saved job
        await db.delete(saved_job)
        await db.commit()

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.JOB_UNSAVED,
            entity_type="saved_job",
            entity_id=saved_job.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
        )

        logger.info(f"Unsaved job: vacancy={vacancy_id}, user={user_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving job: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsave job: {str(e)}",
        ) from e
