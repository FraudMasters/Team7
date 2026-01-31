"""
Work experience API endpoints.

This module provides endpoints for creating, updating, and fetching structured work
experience entries extracted from resumes, including company names, job titles, dates,
and descriptions.
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.work_experience import WorkExperience

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


class WorkExperienceResponse(BaseModel):
    """Response model for a single work experience entry."""

    id: str = Field(..., description="Unique identifier for the work experience")
    resume_id: str = Field(..., description="Resume ID this experience belongs to")
    company: str = Field(..., description="Company/organization name")
    title: str = Field(..., description="Job title/position")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Job description and responsibilities")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0.0 to 1.0)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class WorkExperienceListResponse(BaseModel):
    """Response model for a list of work experiences."""

    experiences: list[WorkExperienceResponse] = Field(..., description="List of work experiences")
    count: int = Field(..., description="Total number of experiences")
    resume_id: str = Field(..., description="Resume ID")


class WorkExperienceCreateRequest(BaseModel):
    """Request model for creating a work experience entry."""

    resume_id: str = Field(..., description="Resume ID this experience belongs to")
    company: str = Field(..., description="Company/organization name", min_length=1, max_length=255)
    title: str = Field(..., description="Job title/position", min_length=1, max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (ISO format, e.g., 2020-01-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Job description and responsibilities")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0.0 to 1.0)", ge=0.0, le=1.0)


class WorkExperienceUpdateRequest(BaseModel):
    """Request model for updating a work experience entry."""

    company: Optional[str] = Field(None, description="Company/organization name", min_length=1, max_length=255)
    title: Optional[str] = Field(None, description="Job title/position", min_length=1, max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (ISO format, e.g., 2020-01-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Job description and responsibilities")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0.0 to 1.0)", ge=0.0, le=1.0)


class WorkExperienceCreateResponse(BaseModel):
    """Response model for work experience creation endpoint."""

    id: str = Field(..., description="Unique identifier for the created work experience")
    resume_id: str = Field(..., description="Resume ID this experience belongs to")
    company: str = Field(..., description="Company/organization name")
    title: str = Field(..., description="Job title/position")
    message: str = Field(..., description="Success message")


@router.get(
    "/resumes/{resume_id}",
    response_model=WorkExperienceListResponse,
    tags=["Work Experiences"],
)
async def get_work_experiences_by_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get all work experience entries for a specific resume.

    This endpoint retrieves all structured work experience entries that were
    extracted from the specified resume, ordered by start date (most recent first).

    Args:
        request: FastAPI request object (for Accept-Language header)
        resume_id: UUID of the resume
        db: Database session

    Returns:
        JSON response with list of work experiences

    Raises:
        HTTPException(404): If resume_id is invalid
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/work-experiences/resumes/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "experiences": [
                {
                    "id": "...",
                    "resume_id": "...",
                    "company": "Tech Corp",
                    "title": "Senior Developer",
                    "start_date": "2020-01-01",
                    "end_date": null,
                    "description": "Led development of...",
                    "confidence_score": 0.95,
                    "created_at": "2026-01-31T00:00:00",
                    "updated_at": "2026-01-31T00:00:00"
                }
            ],
            "count": 1,
            "resume_id": "..."
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate resume_id format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query work experiences for this resume
        query = (
            select(WorkExperience)
            .where(WorkExperience.resume_id == resume_uuid)
            .order_by(WorkExperience.start_date.desc().nulls_last(), WorkExperience.created_at.desc())
        )
        result = await db.execute(query)
        experiences = result.scalars().all()

        # Convert to response format
        experiences_list = []
        for exp in experiences:
            experiences_list.append({
                "id": str(exp.id),
                "resume_id": str(exp.resume_id),
                "company": exp.company,
                "title": exp.title,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "description": exp.description,
                "confidence_score": exp.confidence_score,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
            })

        logger.info(f"Retrieved {len(experiences_list)} work experiences for resume {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "experiences": experiences_list,
                "count": len(experiences_list),
                "resume_id": resume_id,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error fetching work experiences for resume {resume_id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/{experience_id}",
    response_model=WorkExperienceResponse,
    tags=["Work Experiences"],
)
async def get_work_experience(
    request: Request,
    experience_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a single work experience entry by ID.

    This endpoint retrieves a specific work experience entry with all its details.

    Args:
        request: FastAPI request object (for Accept-Language header)
        experience_id: UUID of the work experience entry
        db: Database session

    Returns:
        JSON response with work experience details

    Raises:
        HTTPException(404): If experience_id is not found or invalid
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/work-experiences/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_id": "...",
            "company": "Tech Corp",
            "title": "Senior Developer",
            "start_date": "2020-01-01",
            "end_date": null,
            "description": "Led development of...",
            "confidence_score": 0.95,
            "created_at": "2026-01-31T00:00:00",
            "updated_at": "2026-01-31T00:00:00"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate experience_id format
        try:
            experience_uuid = UUID(experience_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query work experience by ID
        query = select(WorkExperience).where(WorkExperience.id == experience_uuid)
        result = await db.execute(query)
        experience = result.scalar_one_or_none()

        if not experience:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Convert to response format
        response_data = {
            "id": str(experience.id),
            "resume_id": str(experience.resume_id),
            "company": experience.company,
            "title": experience.title,
            "start_date": experience.start_date.isoformat() if experience.start_date else None,
            "end_date": experience.end_date.isoformat() if experience.end_date else None,
            "description": experience.description,
            "confidence_score": experience.confidence_score,
            "created_at": experience.created_at.isoformat() if experience.created_at else None,
            "updated_at": experience.updated_at.isoformat() if experience.updated_at else None,
        }

        logger.info(f"Retrieved work experience {experience_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error fetching work experience {experience_id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.post(
    "",
    response_model=WorkExperienceCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Work Experiences"],
)
async def create_work_experience(
    request: Request,
    experience_data: WorkExperienceCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new work experience entry.

    This endpoint creates a new structured work experience entry for a resume.
    It validates the resume_id exists and creates the experience record.

    Args:
        request: FastAPI request object (for Accept-Language header)
        experience_data: Work experience data to create
        db: Database session

    Returns:
        JSON response with created work experience ID and details

    Raises:
        HTTPException(404): If resume_id is not found
        HTTPException(400): If request data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "company": "Tech Corp",
        ...     "title": "Senior Developer",
        ...     "start_date": "2020-01-01",
        ...     "description": "Led development of scalable systems"
        ... }
        >>> response = requests.post("http://localhost:8000/api/work-experiences", json=data)
        >>> response.json()
        {
            "id": "...",
            "resume_id": "123e4567-e89b-12d3-a456-426614174000",
            "company": "Tech Corp",
            "title": "Senior Developer",
            "message": "Work experience created successfully"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate resume_id format
        try:
            resume_uuid = UUID(experience_data.resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Check if resume exists
        from models.resume import Resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Parse dates if provided
        start_date_obj = None
        end_date_obj = None

        if experience_data.start_date:
            try:
                start_date_obj = date.fromisoformat(experience_data.start_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        if experience_data.end_date:
            try:
                end_date_obj = date.fromisoformat(experience_data.end_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        # Create new work experience
        new_experience = WorkExperience(
            id=uuid4(),
            resume_id=resume_uuid,
            company=experience_data.company,
            title=experience_data.title,
            start_date=start_date_obj,
            end_date=end_date_obj,
            description=experience_data.description,
            confidence_score=experience_data.confidence_score,
        )

        db.add(new_experience)
        await db.commit()
        await db.refresh(new_experience)

        # Get translated success message
        success_message = get_success_message("work_experience_created", locale)

        logger.info(f"Created work experience {new_experience.id} for resume {resume_uuid}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_experience.id),
                "resume_id": str(new_experience.resume_id),
                "company": new_experience.company,
                "title": new_experience.title,
                "message": success_message,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating work experience: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error creating work experience: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.put(
    "/{experience_id}",
    response_model=WorkExperienceResponse,
    tags=["Work Experiences"],
)
async def update_work_experience(
    request: Request,
    experience_id: str,
    experience_data: WorkExperienceUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing work experience entry.

    This endpoint updates a specific work experience entry with the provided data.
    Only the fields specified in the request will be updated (partial update).

    Args:
        request: FastAPI request object (for Accept-Language header)
        experience_id: UUID of the work experience entry to update
        experience_data: Work experience data to update
        db: Database session

    Returns:
        JSON response with updated work experience details

    Raises:
        HTTPException(404): If experience_id is not found
        HTTPException(400): If request data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "title": "Lead Developer",
        ...     "description": "Led team of 5 developers"
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/work-experiences/123e4567-e89b-12d3-a456-426614174000",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_id": "...",
            "company": "Tech Corp",
            "title": "Lead Developer",
            ...
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate experience_id format
        try:
            experience_uuid = UUID(experience_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query work experience by ID
        query = select(WorkExperience).where(WorkExperience.id == experience_uuid)
        result = await db.execute(query)
        experience = result.scalar_one_or_none()

        if not experience:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Update fields if provided
        if experience_data.company is not None:
            experience.company = experience_data.company
        if experience_data.title is not None:
            experience.title = experience_data.title
        if experience_data.description is not None:
            experience.description = experience_data.description
        if experience_data.confidence_score is not None:
            experience.confidence_score = experience_data.confidence_score

        # Parse and update dates if provided
        if experience_data.start_date is not None:
            try:
                experience.start_date = date.fromisoformat(experience_data.start_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        if experience_data.end_date is not None:
            try:
                experience.end_date = date.fromisoformat(experience_data.end_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        await db.commit()
        await db.refresh(experience)

        logger.info(f"Updated work experience {experience_id}")

        # Convert to response format
        response_data = {
            "id": str(experience.id),
            "resume_id": str(experience.resume_id),
            "company": experience.company,
            "title": experience.title,
            "start_date": experience.start_date.isoformat() if experience.start_date else None,
            "end_date": experience.end_date.isoformat() if experience.end_date else None,
            "description": experience.description,
            "confidence_score": experience.confidence_score,
            "created_at": experience.created_at.isoformat() if experience.created_at else None,
            "updated_at": experience.updated_at.isoformat() if experience.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating work experience {experience_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error updating work experience {experience_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.delete(
    "/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Work Experiences"],
)
async def delete_work_experience(
    request: Request,
    experience_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a work experience entry by ID.

    This endpoint permanently removes a work experience entry from the database.
    This is useful for removing incorrect or duplicate experience entries.

    Args:
        request: FastAPI request object (for Accept-Language header)
        experience_id: UUID of the work experience entry to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If experience_id is not found or invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/work-experiences/123e4567-e89b-12d3-a456-426614174000")
        >>> response.status_code
        204
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate experience_id format
        try:
            experience_uuid = UUID(experience_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query work experience by ID
        query = select(WorkExperience).where(WorkExperience.id == experience_uuid)
        result = await db.execute(query)
        experience = result.scalar_one_or_none()

        if not experience:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Delete the work experience
        await db.delete(experience)
        await db.commit()

        logger.info(f"Deleted work experience {experience_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting work experience {experience_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error deleting work experience {experience_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
