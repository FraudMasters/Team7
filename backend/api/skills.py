"""
Skills API endpoints.

This module provides endpoints for creating, updating, and fetching skills
for job seekers, including skill names, categories, proficiency levels, and experience.
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.skill import Skill, ProficiencyLevel
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


class SkillResponse(BaseModel):
    """Response model for a single skill entry."""

    id: str = Field(..., description="Unique identifier for the skill")
    resume_id: str = Field(..., description="Resume ID this skill belongs to")
    name: str = Field(..., description="Name of the skill")
    category: Optional[str] = Field(None, description="Category of the skill")
    proficiency_level: str = Field(..., description="Level of proficiency")
    years_of_experience: Optional[float] = Field(None, description="Years of experience with this skill")
    description: Optional[str] = Field(None, description="Additional details about the skill")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SkillListResponse(BaseModel):
    """Response model for a list of skills."""

    skills: list[SkillResponse] = Field(..., description="List of skills")
    count: int = Field(..., description="Total number of skills")


class SkillCreateRequest(BaseModel):
    """Request model for creating a skill entry."""

    resume_id: Optional[str] = Field(None, description="Resume ID this skill belongs to (optional, will use profile's resume if not provided)")
    name: str = Field(..., description="Name of the skill", min_length=1, max_length=255)
    category: Optional[str] = Field(None, description="Category of the skill", max_length=100)
    proficiency_level: ProficiencyLevel = Field(ProficiencyLevel.INTERMEDIATE, description="Level of proficiency")
    years_of_experience: Optional[float] = Field(None, description="Years of experience with this skill", ge=0)
    description: Optional[str] = Field(None, description="Additional details about the skill")

    @validator('years_of_experience')
    def validate_years_of_experience(cls, v):
        if v is not None and v < 0:
            raise ValueError('years_of_experience must be non-negative')
        return v


class SkillUpdateRequest(BaseModel):
    """Request model for updating a skill entry."""

    name: Optional[str] = Field(None, description="Name of the skill", min_length=1, max_length=255)
    category: Optional[str] = Field(None, description="Category of the skill", max_length=100)
    proficiency_level: Optional[ProficiencyLevel] = Field(None, description="Level of proficiency")
    years_of_experience: Optional[float] = Field(None, description="Years of experience with this skill", ge=0)
    description: Optional[str] = Field(None, description="Additional details about the skill")

    @validator('years_of_experience')
    def validate_years_of_experience(cls, v):
        if v is not None and v < 0:
            raise ValueError('years_of_experience must be non-negative')
        return v


class SkillCreateResponse(BaseModel):
    """Response model for skill creation endpoint."""

    id: str = Field(..., description="Unique identifier for the created skill")
    resume_id: str = Field(..., description="Resume ID this skill belongs to")
    name: str = Field(..., description="Name of the skill")
    message: str = Field(..., description="Success message")


@router.get(
    "",
    response_model=SkillListResponse,
    tags=["Skills"],
)
async def get_skills(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get all skills for the current user.

    This endpoint retrieves all skills associated with the current user's
    profile resumes, ordered by category and name.

    Args:
        request: FastAPI request object (for Accept-Language header)
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with list of skills

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/profiles/me/skills",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "skills": [
                {
                    "id": "...",
                    "resume_id": "...",
                    "name": "Python",
                    "category": "Programming",
                    "proficiency_level": "ADVANCED",
                    "years_of_experience": 5.0,
                    "description": "Expert in Django and FastAPI",
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
                content={"skills": [], "count": 0},
            )

        resume_uuid = UUID(profile.resume_id)

        # Query skills for this resume
        query = (
            select(Skill)
            .where(Skill.resume_id == resume_uuid)
            .order_by(Skill.category.nulls_last(), Skill.name)
        )
        result = await db.execute(query)
        skills = result.scalars().all()

        # Convert to response format
        skills_list = []
        for skill in skills:
            skills_list.append({
                "id": str(skill.id),
                "resume_id": str(skill.resume_id),
                "name": skill.name,
                "category": skill.category,
                "proficiency_level": skill.proficiency_level.value,
                "years_of_experience": skill.years_of_experience,
                "description": skill.description,
                "created_at": skill.created_at.isoformat() if skill.created_at else None,
                "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
            })

        logger.info(f"Retrieved {len(skills_list)} skills for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "skills": skills_list,
                "count": len(skills_list),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching skills for user {current_user.id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
    tags=["Skills"],
)
async def get_skill(
    request: Request,
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a single skill by ID.

    This endpoint retrieves a specific skill with all its details.
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        skill_id: UUID of the skill
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with skill details

    Raises:
        HTTPException(404): If skill_id is not found or invalid
        HTTPException(403): If user doesn't own the skill
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/profiles/me/skills/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Python",
            "category": "Programming",
            ...
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate skill_id format
        try:
            skill_uuid = UUID(skill_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query skill by ID
        query = select(Skill).where(Skill.id == skill_uuid)
        result = await db.execute(query)
        skill = result.scalar_one_or_none()

        if not skill:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(skill.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this skill",
            )

        # Convert to response format
        response_data = {
            "id": str(skill.id),
            "resume_id": str(skill.resume_id),
            "name": skill.name,
            "category": skill.category,
            "proficiency_level": skill.proficiency_level.value,
            "years_of_experience": skill.years_of_experience,
            "description": skill.description,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
        }

        logger.info(f"Retrieved skill {skill_id} for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error fetching skill {skill_id}: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.post(
    "",
    response_model=SkillCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Skills"],
)
async def create_skill(
    request: Request,
    skill_data: SkillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new skill entry.

    This endpoint creates a new skill for the current user.
    The skill is associated with the user's profile's resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        skill_data: Skill data to create
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with created skill ID and details

    Raises:
        HTTPException(400): If request data is invalid
        HTTPException(404): If user profile or resume not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Python",
        ...     "category": "Programming",
        ...     "proficiency_level": "ADVANCED",
        ...     "years_of_experience": 5.0,
        ...     "description": "Expert in Django and FastAPI"
        ... }
        >>> response = requests.post(
        ...     "/api/profiles/me/skills",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "resume_id": "...",
            "name": "Python",
            "message": "Skill created successfully"
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

        # Create new skill entry
        new_skill = Skill(
            id=uuid4(),
            resume_id=resume_uuid,
            name=skill_data.name,
            category=skill_data.category,
            proficiency_level=skill_data.proficiency_level,
            years_of_experience=skill_data.years_of_experience,
            description=skill_data.description,
        )

        db.add(new_skill)
        await db.commit()
        await db.refresh(new_skill)

        # Get translated success message
        success_message = get_success_message("skill_created", locale)

        logger.info(f"Created skill {new_skill.id} for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_skill.id),
                "resume_id": str(new_skill.resume_id),
                "name": new_skill.name,
                "message": success_message,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating skill: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error creating skill: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.put(
    "/{skill_id}",
    response_model=SkillResponse,
    tags=["Skills"],
)
async def update_skill(
    request: Request,
    skill_id: str,
    skill_data: SkillUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing skill entry.

    This endpoint updates a specific skill with the provided data.
    Only the fields specified in the request will be updated (partial update).
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        skill_id: UUID of the skill to update
        skill_data: Skill data to update
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with updated skill details

    Raises:
        HTTPException(404): If skill_id is not found
        HTTPException(403): If user doesn't own the skill
        HTTPException(400): If request data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "proficiency_level": "EXPERT",
        ...     "years_of_experience": 7.0
        ... }
        >>> response = requests.put(
        ...     "/api/profiles/me/skills/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Python",
            "proficiency_level": "EXPERT",
            ...
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate skill_id format
        try:
            skill_uuid = UUID(skill_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query skill by ID
        query = select(Skill).where(Skill.id == skill_uuid)
        result = await db.execute(query)
        skill = result.scalar_one_or_none()

        if not skill:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(skill.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this skill",
            )

        # Update fields if provided
        if skill_data.name is not None:
            skill.name = skill_data.name
        if skill_data.category is not None:
            skill.category = skill_data.category
        if skill_data.proficiency_level is not None:
            skill.proficiency_level = skill_data.proficiency_level
        if skill_data.years_of_experience is not None:
            skill.years_of_experience = skill_data.years_of_experience
        if skill_data.description is not None:
            skill.description = skill_data.description

        await db.commit()
        await db.refresh(skill)

        logger.info(f"Updated skill {skill_id} for user {current_user.id}")

        # Convert to response format
        response_data = {
            "id": str(skill.id),
            "resume_id": str(skill.resume_id),
            "name": skill.name,
            "category": skill.category,
            "proficiency_level": skill.proficiency_level.value,
            "years_of_experience": skill.years_of_experience,
            "description": skill.description,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating skill {skill_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error updating skill {skill_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Skills"],
)
async def delete_skill(
    request: Request,
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a skill entry by ID.

    This endpoint permanently removes a skill from the database.
    The user must own the associated resume.

    Args:
        request: FastAPI request object (for Accept-Language header)
        skill_id: UUID of the skill to delete
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If skill_id is not found or invalid
        HTTPException(403): If user doesn't own the skill
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "/api/profiles/me/skills/123e4567-e89b-12d3-a456-426614174000",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.status_code
        204
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate skill_id format
        try:
            skill_uuid = UUID(skill_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Query skill by ID
        query = select(Skill).where(Skill.id == skill_uuid)
        result = await db.execute(query)
        skill = result.scalar_one_or_none()

        if not skill:
            error_msg = get_error_message("not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Verify ownership through the user's profile
        profile_query = select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id or str(skill.resume_id) != profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this skill",
            )

        # Delete the skill
        await db.delete(skill)
        await db.commit()

        logger.info(f"Deleted skill {skill_id} for user {current_user.id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting skill {skill_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error deleting skill {skill_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
