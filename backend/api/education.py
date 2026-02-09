"""
Education history API endpoints.

This module provides endpoints for creating, updating, and fetching education entries
for job seekers, including schools, degrees, dates, and field of study.
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
from models.education import Education, DegreeType
from models.resume import Resume
from models.job_seeker_profile import JobSeekerProfile
from dependencies.auth import get_current_user
from models.user import User

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


class EducationResponse(BaseModel):
    """Response model for a single education entry."""

    id: str = Field(..., description="Unique identifier for the education entry")
    resume_id: str = Field(..., description="Resume ID this education belongs to")
    institution_name: str = Field(..., description="Name of the institution")
    degree: str = Field(..., description="Degree obtained")
    field_of_study: Optional[str] = Field(None, description="Major or area of study")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Additional details about achievements")
    location: Optional[str] = Field(None, description="Location of the institution")
    degree_type: str = Field(..., description="Type of degree")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class EducationListResponse(BaseModel):
    """Response model for a list of education entries."""

    education: list[EducationResponse] = Field(..., description="List of education entries")
    count: int = Field(..., description="Total number of education entries")


class EducationCreateRequest(BaseModel):
    """Request model for creating an education entry."""

    resume_id: Optional[str] = Field(None, description="Resume ID this education belongs to (optional, will use profile's resume if not provided)")
    institution_name: str = Field(..., description="Name of the institution", min_length=1, max_length=255)
    degree: str = Field(..., description="Degree obtained", min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, description="Major or area of study", max_length=255)
    start_date: str = Field(..., description="Start date (ISO format, e.g., 2018-09-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Additional details about achievements")
    location: Optional[str] = Field(None, description="Location of the institution", max_length=255)
    degree_type: DegreeType = Field(DegreeType.BACHELOR, description="Type of degree")


class EducationUpdateRequest(BaseModel):
    """Request model for updating an education entry."""

    institution_name: Optional[str] = Field(None, description="Name of the institution", min_length=1, max_length=255)
    degree: Optional[str] = Field(None, description="Degree obtained", min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, description="Major or area of study", max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (ISO format, e.g., 2018-09-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Additional details about achievements")
    location: Optional[str] = Field(None, description="Location of the institution", max_length=255)
    degree_type: Optional[DegreeType] = Field(None, description="Type of degree")


class EducationCreateResponse(BaseModel):
    """Response model for education creation endpoint."""

    id: str = Field(..., description="Unique identifier for the created education entry")
    resume_id: str = Field(..., description="Resume ID this education belongs to")
    institution_name: str = Field(..., description="Name of the institution")
    degree: str = Field(..., description="Degree obtained")
    message: str = Field(..., description="Success message")


@router.get(
    "",
    response_model=EducationListResponse,
    tags=["Education"],
)
async def get_education_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get all education entries for the current user.

    This endpoint retrieves all education entries associated with the current user's
    profile resumes, ordered by start date (most recent first).

    Args:
        request: FastAPI request object (for Accept-Language header)
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with list of education entries

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/profiles/me/education",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "education": [
                {
                    "id": "...",
                    "resume_id": "...",
                    "institution_name": "MIT",
                    "degree": "Bachelor of Science",
                    "field_of_study": "Computer Science",
                    "start_date": "2018-09-01",
                    "end_date": "2022-05-31",
                    "description": "Graduated with honors",
                    "location": "Cambridge, MA",
                    "degree_type": "BACHELOR",
                    "created_at": "2026-01-31T00:00:00",
                    "updated_at": "2026-01-31T00:00:00"
                }
            ],
            "count": 1
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Get all resume IDs owned by the current user through their profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"education": [], "count": 0},
            )

        resume_uuid = UUID(profile.resume_id)

        # Query education entries for this resume
        query = (
            select(Education)
            .where(Education.resume_id == resume_uuid)
            .order_by(Education.start_date.desc().nulls_last(), Education.created_at.desc())
        )
        result = await db.execute(query)
        education_entries = result.scalars().all()

        # Convert to response format
        education_list = []
        for edu in education_entries:
            education_list.append({
                "id": str(edu.id),
                "resume_id": str(edu.resume_id),
                "institution_name": edu.institution_name,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "start_date": edu.start_date.isoformat() if edu.start_date else None,
                "end_date": edu.end_date.isoformat() if edu.end_date else None,
                "description": edu.description,
                "location": edu.location,
                "degree_type": edu.degree_type.value,
                "created_at": edu.created_at.isoformat() if edu.created_at else None,
                "updated_at": edu.updated_at.isoformat() if edu.updated_at else None,
            })

        logger.info(f"Retrieved {len(education_list)} education entries for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "education": education_list,
                "count": len(education_list),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching education history for user {current_user.id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/{education_id}",
    response_model=EducationResponse,
    tags=["Education"],
)
async def get_education_entry(
    request: Request,
    education_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a single education entry by ID.

    This endpoint retrieves a specific education entry with all its details.
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        education_id: UUID of the education entry
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with education entry details

    Raises:
        HTTPException(404): If education_id is not found or invalid
        HTTPException(403): If user doesn't own the education entry
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/profiles/me/education/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "institution_name": "MIT",
            "degree": "Bachelor of Science",
            ...
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate education_id format
        try:
            education_uuid = UUID(education_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query education entry by ID
        query = select(Education).where(Education.id == education_uuid)
        result = await db.execute(query)
        education = result.scalar_one_or_none()

        if not education:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(education.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this education entry",
            )

        # Convert to response format
        response_data = {
            "id": str(education.id),
            "resume_id": str(education.resume_id),
            "institution_name": education.institution_name,
            "degree": education.degree,
            "field_of_study": education.field_of_study,
            "start_date": education.start_date.isoformat() if education.start_date else None,
            "end_date": education.end_date.isoformat() if education.end_date else None,
            "description": education.description,
            "location": education.location,
            "degree_type": education.degree_type.value,
            "created_at": education.created_at.isoformat() if education.created_at else None,
            "updated_at": education.updated_at.isoformat() if education.updated_at else None,
        }

        logger.info(f"Retrieved education entry {education_id} for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error fetching education entry {education_id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.post(
    "",
    response_model=EducationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Education"],
)
async def create_education_entry(
    request: Request,
    education_data: EducationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new education entry.

    This endpoint creates a new education entry for the current user.
    The education is associated with the user's profile's resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        education_data: Education data to create
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with created education ID and details

    Raises:
        HTTPException(400): If request data is invalid
        HTTPException(404): If user profile or resume not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "institution_name": "MIT",
        ...     "degree": "Bachelor of Science",
        ...     "field_of_study": "Computer Science",
        ...     "start_date": "2018-09-01",
        ...     "end_date": "2022-05-31",
        ...     "degree_type": "BACHELOR"
        ... }
        >>> response = requests.post(
        ...     "/api/profiles/me/education",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "resume_id": "...",
            "institution_name": "MIT",
            "degree": "Bachelor of Science",
            "message": "Education entry created successfully"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Get the user's profile and associated resume
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first.",
            )

        if not profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume associated with your profile. Please add a resume first.",
            )

        resume_uuid = UUID(profile.resume_id)

        # Verify the resume exists
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated resume not found",
            )

        # Parse dates
        try:
            start_date_obj = date.fromisoformat(education_data.start_date)
        except ValueError:
            error_msg = get_error_message("invalid_date_format", locale)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        end_date_obj = None
        if education_data.end_date:
            try:
                end_date_obj = date.fromisoformat(education_data.end_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        # Create new education entry
        new_education = Education(
            id=uuid4(),
            resume_id=resume_uuid,
            institution_name=education_data.institution_name,
            degree=education_data.degree,
            field_of_study=education_data.field_of_study,
            start_date=start_date_obj,
            end_date=end_date_obj,
            description=education_data.description,
            location=education_data.location,
            degree_type=education_data.degree_type,
        )

        db.add(new_education)
        await db.commit()
        await db.refresh(new_education)

        # Get translated success message
        success_message = get_success_message("education_created", locale)

        logger.info(f"Created education entry {new_education.id} for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_education.id),
                "resume_id": str(new_education.resume_id),
                "institution_name": new_education.institution_name,
                "degree": new_education.degree,
                "message": success_message,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating education entry: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error creating education entry: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.put(
    "/{education_id}",
    response_model=EducationResponse,
    tags=["Education"],
)
async def update_education_entry(
    request: Request,
    education_id: str,
    education_data: EducationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing education entry.

    This endpoint updates a specific education entry with the provided data.
    Only the fields specified in the request will be updated (partial update).
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        education_id: UUID of the education entry to update
        education_data: Education data to update
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with updated education entry details

    Raises:
        HTTPException(404): If education_id is not found
        HTTPException(403): If user doesn't own the education entry
        HTTPException(400): If request data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "degree": "Master of Science",
        ...     "end_date": "2024-05-31"
        ... }
        >>> response = requests.put(
        ...     "/api/profiles/me/education/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "institution_name": "MIT",
            "degree": "Master of Science",
            ...
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate education_id format
        try:
            education_uuid = UUID(education_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query education entry by ID
        query = select(Education).where(Education.id == education_uuid)
        result = await db.execute(query)
        education = result.scalar_one_or_none()

        if not education:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(education.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this education entry",
            )

        # Update fields if provided
        if education_data.institution_name is not None:
            education.institution_name = education_data.institution_name
        if education_data.degree is not None:
            education.degree = education_data.degree
        if education_data.field_of_study is not None:
            education.field_of_study = education_data.field_of_study
        if education_data.description is not None:
            education.description = education_data.description
        if education_data.location is not None:
            education.location = education_data.location
        if education_data.degree_type is not None:
            education.degree_type = education_data.degree_type

        # Parse and update dates if provided
        if education_data.start_date is not None:
            try:
                education.start_date = date.fromisoformat(education_data.start_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        if education_data.end_date is not None:
            try:
                education.end_date = date.fromisoformat(education_data.end_date)
            except ValueError:
                error_msg = get_error_message("invalid_date_format", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        await db.commit()
        await db.refresh(education)

        logger.info(f"Updated education entry {education_id} for user {current_user.id}")

        # Convert to response format
        response_data = {
            "id": str(education.id),
            "resume_id": str(education.resume_id),
            "institution_name": education.institution_name,
            "degree": education.degree,
            "field_of_study": education.field_of_study,
            "start_date": education.start_date.isoformat() if education.start_date else None,
            "end_date": education.end_date.isoformat() if education.end_date else None,
            "description": education.description,
            "location": education.location,
            "degree_type": education.degree_type.value,
            "created_at": education.created_at.isoformat() if education.created_at else None,
            "updated_at": education.updated_at.isoformat() if education.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating education entry {education_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error updating education entry {education_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.delete(
    "/{education_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Education"],
)
async def delete_education_entry(
    request: Request,
    education_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete an education entry by ID.

    This endpoint permanently removes an education entry from the database.
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        education_id: UUID of the education entry to delete
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If education_id is not found or invalid
        HTTPException(403): If user doesn't own the education entry
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "/api/profiles/me/education/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.status_code
        204
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate education_id format
        try:
            education_uuid = UUID(education_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query education entry by ID
        query = select(Education).where(Education.id == education_uuid)
        result = await db.execute(query)
        education = result.scalar_one_or_none()

        if not education:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(education.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this education entry",
            )

        # Delete the education entry
        await db.delete(education)
        await db.commit()

        logger.info(f"Deleted education entry {education_id} for user {current_user.id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting education entry {education_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error deleting education entry {education_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
