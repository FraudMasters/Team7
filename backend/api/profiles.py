"""
Job seeker profile management endpoints.

This module provides endpoints for:
- Getting the current user's job seeker profile
- Creating a new job seeker profile
- Updating an existing job seeker profile

Job seekers use these endpoints to manage their professional profile information.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_seeker_profile import JobSeekerProfile
from models.user import User
from models.organization import Organization
from models.resume import Resume
from dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class JobSeekerProfileCreate(BaseModel):
    """Request model for creating a job seeker profile."""

    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="City, state or country of residence")
    bio: Optional[str] = Field(None, description="Professional summary or biography")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or website URL")
    years_of_experience: Optional[float] = Field(None, description="Total years of work experience", ge=0)
    current_title: Optional[str] = Field(None, description="Current or most recent job title")
    current_company: Optional[str] = Field(None, description="Current or most recent company")
    industry: Optional[str] = Field(None, description="Industry of expertise")
    job_seeker_status: Optional[str] = Field(None, description="Current employment status (actively_looking, open, not_looking)")
    preferred_locations: Optional[str] = Field(None, description="Preferred job locations (comma-separated)")
    preferred_job_types: Optional[str] = Field(None, description="Preferred employment types (comma-separated)")
    expected_salary: Optional[str] = Field(None, description="Expected salary range")
    resume_id: Optional[str] = Field(None, description="Primary/default resume for this profile")


class JobSeekerProfileUpdate(BaseModel):
    """Request model for updating a job seeker profile."""

    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="City, state or country of residence")
    bio: Optional[str] = Field(None, description="Professional summary or biography")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or website URL")
    years_of_experience: Optional[float] = Field(None, description="Total years of work experience", ge=0)
    current_title: Optional[str] = Field(None, description="Current or most recent job title")
    current_company: Optional[str] = Field(None, description="Current or most recent company")
    industry: Optional[str] = Field(None, description="Industry of expertise")
    job_seeker_status: Optional[str] = Field(None, description="Current employment status (actively_looking, open, not_looking)")
    preferred_locations: Optional[str] = Field(None, description="Preferred job locations (comma-separated)")
    preferred_job_types: Optional[str] = Field(None, description="Preferred employment types (comma-separated)")
    expected_salary: Optional[str] = Field(None, description="Expected salary range")
    resume_id: Optional[str] = Field(None, description="Primary/default resume for this profile")


class JobSeekerProfileResponse(BaseModel):
    """Response model for a job seeker profile."""

    id: str = Field(..., description="Profile ID")
    user_id: str = Field(..., description="User ID that owns this profile")
    organization_id: str = Field(..., description="Organization ID")
    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="City, state or country of residence")
    bio: Optional[str] = Field(None, description="Professional summary or biography")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or website URL")
    years_of_experience: Optional[float] = Field(None, description="Total years of work experience")
    current_title: Optional[str] = Field(None, description="Current or most recent job title")
    current_company: Optional[str] = Field(None, description="Current or most recent company")
    industry: Optional[str] = Field(None, description="Industry of expertise")
    job_seeker_status: Optional[str] = Field(None, description="Current employment status")
    preferred_locations: Optional[str] = Field(None, description="Preferred job locations")
    preferred_job_types: Optional[str] = Field(None, description="Preferred employment types")
    expected_salary: Optional[str] = Field(None, description="Expected salary range")
    resume_id: Optional[str] = Field(None, description="Primary/default resume ID")
    created_at: str = Field(..., description="Profile creation timestamp")
    updated_at: str = Field(..., description="Profile last update timestamp")


@router.get(
    "/me",
    response_model=JobSeekerProfileResponse,
    tags=["Profiles"],
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the current user's job seeker profile.

    Returns the job seeker profile associated with the authenticated user.
    If the user doesn't have a profile yet, returns a 404 error.

    Args:
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with the user's profile data

    Raises:
        HTTPException(404): If the user doesn't have a profile
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/profiles/me",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "id": "...",
            "user_id": "...",
            "location": "San Francisco, CA",
            "bio": "Software engineer...",
            ...
        }
    """
    try:
        logger.info(f"Fetching profile for user: {current_user.id}")

        # Get the user's profile
        result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            logger.info(f"No profile found for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first.",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "organization_id": str(profile.organization_id),
                "phone": profile.phone,
                "location": profile.location,
                "bio": profile.bio,
                "linkedin_url": profile.linkedin_url,
                "portfolio_url": profile.portfolio_url,
                "years_of_experience": profile.years_of_experience,
                "current_title": profile.current_title,
                "current_company": profile.current_company,
                "industry": profile.industry,
                "job_seeker_status": profile.job_seeker_status,
                "preferred_locations": profile.preferred_locations,
                "preferred_job_types": profile.preferred_job_types,
                "expected_salary": profile.expected_salary,
                "resume_id": str(profile.resume_id) if profile.resume_id else None,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}",
        ) from e


@router.post(
    "/me",
    response_model=JobSeekerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Profiles"],
)
async def create_my_profile(
    profile_data: JobSeekerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new job seeker profile for the current user.

    Creates a new job seeker profile for the authenticated user.
    Each user can only have one profile. Returns an error if a profile
    already exists for the user.

    Args:
        profile_data: Profile data to create
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with the created profile data

    Raises:
        HTTPException(400): If the user already has a profile
        HTTPException(400): If the specified resume_id is invalid
        HTTPException(500): If profile creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "location": "San Francisco, CA",
        ...     "bio": "Software engineer with 5 years experience...",
        ...     "years_of_experience": 5.0,
        ...     "current_title": "Senior Software Engineer"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/profiles/me",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "user_id": "...",
            "location": "San Francisco, CA",
            ...
        }
    """
    try:
        logger.info(f"Creating profile for user: {current_user.id}")

        # Check if user already has a profile
        existing_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        existing_profile = existing_result.scalar_one_or_none()

        if existing_profile:
            logger.warning(f"User {current_user.id} already has a profile")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists. Use PUT to update your profile.",
            )

        # Validate resume_id if provided
        resume_uuid = None
        if profile_data.resume_id:
            try:
                resume_uuid = UUID(profile_data.resume_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid resume_id format: {profile_data.resume_id}",
                )

            # Verify the resume exists
            resume_result = await db.execute(
                select(Resume).where(Resume.id == resume_uuid)
            )
            resume = resume_result.scalar_one_or_none()

            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resume not found: {profile_data.resume_id}",
                )

        # Get or create a default organization for the job seeker
        # For now, use the first organization or create a personal one
        org_result = await db.execute(
            select(Organization).limit(1)
        )
        organization = org_result.scalar_one_or_none()

        if not organization:
            # Create a default personal organization for job seekers
            organization = Organization(
                name=f"{current_user.email}'s Organization",
                industry="Other",
                company_size="1-10",
            )
            db.add(organization)
            await db.flush()
            logger.info(f"Created default organization {organization.id} for user {current_user.id}")

        # Create the profile
        new_profile = JobSeekerProfile(
            user_id=str(current_user.id),
            organization_id=str(organization.id),
            phone=profile_data.phone,
            location=profile_data.location,
            bio=profile_data.bio,
            linkedin_url=profile_data.linkedin_url,
            portfolio_url=profile_data.portfolio_url,
            years_of_experience=profile_data.years_of_experience,
            current_title=profile_data.current_title,
            current_company=profile_data.current_company,
            industry=profile_data.industry,
            job_seeker_status=profile_data.job_seeker_status,
            preferred_locations=profile_data.preferred_locations,
            preferred_job_types=profile_data.preferred_job_types,
            expected_salary=profile_data.expected_salary,
            resume_id=str(resume_uuid) if resume_uuid else None,
        )

        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)

        logger.info(f"Profile created successfully for user {current_user.id}: {new_profile.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_profile.id),
                "user_id": str(new_profile.user_id),
                "organization_id": str(new_profile.organization_id),
                "phone": new_profile.phone,
                "location": new_profile.location,
                "bio": new_profile.bio,
                "linkedin_url": new_profile.linkedin_url,
                "portfolio_url": new_profile.portfolio_url,
                "years_of_experience": new_profile.years_of_experience,
                "current_title": new_profile.current_title,
                "current_company": new_profile.current_company,
                "industry": new_profile.industry,
                "job_seeker_status": new_profile.job_seeker_status,
                "preferred_locations": new_profile.preferred_locations,
                "preferred_job_types": new_profile.preferred_job_types,
                "expected_salary": new_profile.expected_salary,
                "resume_id": str(new_profile.resume_id) if new_profile.resume_id else None,
                "created_at": new_profile.created_at.isoformat() if new_profile.created_at else None,
                "updated_at": new_profile.updated_at.isoformat() if new_profile.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile for user {current_user.id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}",
        ) from e


@router.put(
    "/me",
    response_model=JobSeekerProfileResponse,
    tags=["Profiles"],
)
async def update_my_profile(
    profile_data: JobSeekerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the current user's job seeker profile.

    Updates the job seeker profile for the authenticated user.
    Only updates fields that are provided in the request.

    Args:
        profile_data: Profile data to update (partial updates supported)
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with the updated profile data

    Raises:
        HTTPException(404): If the user doesn't have a profile
        HTTPException(400): If the specified resume_id is invalid
        HTTPException(500): If profile update fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "location": "New York, NY",
        ...     "years_of_experience": 6.0
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/profiles/me",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "user_id": "...",
            "location": "New York, NY",
            ...
        }
    """
    try:
        logger.info(f"Updating profile for user: {current_user.id}")

        # Get the user's profile
        result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            logger.info(f"No profile found for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first.",
            )

        # Validate resume_id if provided
        if profile_data.resume_id is not None:
            if profile_data.resume_id:  # Non-empty string
                try:
                    resume_uuid = UUID(profile_data.resume_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid resume_id format: {profile_data.resume_id}",
                    )

                # Verify the resume exists
                resume_result = await db.execute(
                    select(Resume).where(Resume.id == resume_uuid)
                )
                resume = resume_result.scalar_one_or_none()

                if not resume:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Resume not found: {profile_data.resume_id}",
                    )

                profile.resume_id = str(resume_uuid)
            else:
                # Empty string or None means clear the resume_id
                profile.resume_id = None

        # Update only provided fields
        if profile_data.phone is not None:
            profile.phone = profile_data.phone
        if profile_data.location is not None:
            profile.location = profile_data.location
        if profile_data.bio is not None:
            profile.bio = profile_data.bio
        if profile_data.linkedin_url is not None:
            profile.linkedin_url = profile_data.linkedin_url
        if profile_data.portfolio_url is not None:
            profile.portfolio_url = profile_data.portfolio_url
        if profile_data.years_of_experience is not None:
            profile.years_of_experience = profile_data.years_of_experience
        if profile_data.current_title is not None:
            profile.current_title = profile_data.current_title
        if profile_data.current_company is not None:
            profile.current_company = profile_data.current_company
        if profile_data.industry is not None:
            profile.industry = profile_data.industry
        if profile_data.job_seeker_status is not None:
            profile.job_seeker_status = profile_data.job_seeker_status
        if profile_data.preferred_locations is not None:
            profile.preferred_locations = profile_data.preferred_locations
        if profile_data.preferred_job_types is not None:
            profile.preferred_job_types = profile_data.preferred_job_types
        if profile_data.expected_salary is not None:
            profile.expected_salary = profile_data.expected_salary

        await db.commit()
        await db.refresh(profile)

        logger.info(f"Profile updated successfully for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "organization_id": str(profile.organization_id),
                "phone": profile.phone,
                "location": profile.location,
                "bio": profile.bio,
                "linkedin_url": profile.linkedin_url,
                "portfolio_url": profile.portfolio_url,
                "years_of_experience": profile.years_of_experience,
                "current_title": profile.current_title,
                "current_company": profile.current_company,
                "industry": profile.industry,
                "job_seeker_status": profile.job_seeker_status,
                "preferred_locations": profile.preferred_locations,
                "preferred_job_types": profile.preferred_job_types,
                "expected_salary": profile.expected_salary,
                "resume_id": str(profile.resume_id) if profile.resume_id else None,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        ) from e
