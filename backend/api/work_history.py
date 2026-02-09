"""
Work history API endpoints for job seeker profile management.

This module provides endpoints for:
- Listing work history entries for the current user's profile
- Creating a new work history entry
- Updating an existing work history entry
- Deleting a work history entry

Job seekers use these endpoints to manage their work experience history
as part of their professional profile.
"""
import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from models.work_history import WorkHistory, EmploymentType
from models.job_seeker_profile import JobSeekerProfile

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class WorkHistoryItem(BaseModel):
    """Response model for a single work history entry."""

    id: str = Field(..., description="Unique identifier for the work history entry")
    resume_id: str = Field(..., description="Resume ID this entry belongs to")
    company_name: str = Field(..., description="Name of the company/organization")
    position_title: str = Field(..., description="Job title/position held")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if current)")
    description: Optional[str] = Field(None, description="Description of responsibilities and achievements")
    location: Optional[str] = Field(None, description="City, state or country of work location")
    employment_type: str = Field(..., description="Type of employment (full-time, part-time, etc.)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class WorkHistoryListResponse(BaseModel):
    """Response model for a list of work history entries."""

    work_history: List[WorkHistoryItem] = Field(..., description="List of work history entries")
    count: int = Field(..., description="Total number of work history entries")


# Request Models
class WorkHistoryCreate(BaseModel):
    """Request model for creating a work history entry."""

    company_name: str = Field(..., description="Name of the company/organization", min_length=1, max_length=255)
    position_title: str = Field(..., description="Job title/position held", min_length=1, max_length=255)
    start_date: str = Field(..., description="Start date (ISO format, e.g., 2020-01-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if currently employed)")
    description: Optional[str] = Field(None, description="Description of responsibilities and achievements")
    location: Optional[str] = Field(None, description="City, state or country of work location", max_length=255)
    employment_type: str = Field(EmploymentType.FULL_TIME, description="Type of employment")

    @validator("employment_type")
    def validate_employment_type(cls, v):
        """Validate employment type is a valid enum value."""
        valid_types = [e.value for e in EmploymentType]
        if v not in valid_types:
            raise ValueError(f"employment_type must be one of: {', '.join(valid_types)}")
        return v


class WorkHistoryUpdate(BaseModel):
    """Request model for updating a work history entry."""

    company_name: Optional[str] = Field(None, description="Name of the company/organization", min_length=1, max_length=255)
    position_title: Optional[str] = Field(None, description="Job title/position held", min_length=1, max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (ISO format, e.g., 2020-01-01)")
    end_date: Optional[str] = Field(None, description="End date (ISO format, null if currently employed)")
    description: Optional[str] = Field(None, description="Description of responsibilities and achievements")
    location: Optional[str] = Field(None, description="City, state or country of work location", max_length=255)
    employment_type: Optional[str] = Field(None, description="Type of employment")

    @validator("employment_type")
    def validate_employment_type(cls, v):
        """Validate employment type is a valid enum value."""
        if v is not None:
            valid_types = [e.value for e in EmploymentType]
            if v not in valid_types:
                raise ValueError(f"employment_type must be one of: {', '.join(valid_types)}")
        return v


class WorkHistoryCreateResponse(BaseModel):
    """Response model for work history creation."""

    id: str = Field(..., description="Unique identifier for the created work history entry")
    company_name: str = Field(..., description="Name of the company")
    position_title: str = Field(..., description="Job title")
    message: str = Field(..., description="Success message")


@router.get(
    "/",
    response_model=WorkHistoryListResponse,
    tags=["Work History"],
)
async def get_work_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all work history entries for the current user's profile.

    Returns a list of work history entries associated with the current user's
    job seeker profile, ordered by start date (most recent first).

    Args:
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with list of work history entries

    Raises:
        HTTPException(404): If the user doesn't have a profile
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/profiles/me/work-history",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "work_history": [
                {
                    "id": "...",
                    "company_name": "Tech Corp",
                    "position_title": "Senior Developer",
                    "start_date": "2020-01-01",
                    "end_date": null,
                    ...
                }
            ],
            "count": 1
        }
    """
    try:
        logger.info(f"Fetching work history for user: {current_user.id}")

        # Get the user's job seeker profile
        profile_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            logger.info(f"No profile found for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first.",
            )

        # Query work history entries for this profile
        # WorkHistory is linked via resume_id, so we need to get the profile's resume
        if not profile.resume_id:
            # No resume associated with profile, return empty list
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "work_history": [],
                    "count": 0,
                },
            )

        try:
            resume_uuid = UUID(profile.resume_id)
        except ValueError:
            logger.error(f"Invalid resume_id format in profile: {profile.resume_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "work_history": [],
                    "count": 0,
                },
            )

        query = (
            select(WorkHistory)
            .where(WorkHistory.resume_id == resume_uuid)
            .order_by(WorkHistory.start_date.desc().nulls_last(), WorkHistory.created_at.desc())
        )
        result = await db.execute(query)
        work_entries = result.scalars().all()

        # Convert to response format
        work_history_list = []
        for entry in work_entries:
            work_history_list.append({
                "id": str(entry.id),
                "resume_id": str(entry.resume_id),
                "company_name": entry.company_name,
                "position_title": entry.position_title,
                "start_date": entry.start_date.isoformat() if entry.start_date else None,
                "end_date": entry.end_date.isoformat() if entry.end_date else None,
                "description": entry.description,
                "location": entry.location,
                "employment_type": entry.employment_type.value if entry.employment_type else EmploymentType.FULL_TIME.value,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            })

        logger.info(f"Retrieved {len(work_history_list)} work history entries for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "work_history": work_history_list,
                "count": len(work_history_list),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work history for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get work history: {str(e)}",
        ) from e


@router.post(
    "",
    response_model=WorkHistoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Work History"],
)
async def create_work_history(
    work_data: WorkHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new work history entry for the current user's profile.

    Creates a new work history entry associated with the user's job seeker profile.
    Requires the user to have a profile with an associated resume.

    Args:
        work_data: Work history data to create
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with created work history ID and details

    Raises:
        HTTPException(404): If the user doesn't have a profile or resume
        HTTPException(400): If request data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "company_name": "Tech Corp",
        ...     "position_title": "Senior Developer",
        ...     "start_date": "2020-01-01",
        ...     "employment_type": "FULL_TIME"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/profiles/me/work-history",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "company_name": "Tech Corp",
            "position_title": "Senior Developer",
            "message": "Work history entry created successfully"
        }
    """
    try:
        logger.info(f"Creating work history for user: {current_user.id}")

        # Get the user's job seeker profile
        profile_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            logger.info(f"No profile found for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first.",
            )

        # Check if profile has an associated resume
        if not profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume associated with profile. Please add a resume to your profile first.",
            )

        try:
            resume_uuid = UUID(profile.resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume_id format in profile: {profile.resume_id}",
            )

        # Parse dates
        try:
            start_date_obj = date.fromisoformat(work_data.start_date)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid start_date format: {work_data.start_date}. Use ISO format (YYYY-MM-DD).",
            ) from e

        end_date_obj = None
        if work_data.end_date:
            try:
                end_date_obj = date.fromisoformat(work_data.end_date)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {work_data.end_date}. Use ISO format (YYYY-MM-DD).",
                ) from e

        # Parse employment type
        try:
            employment_type_enum = EmploymentType(work_data.employment_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid employment_type: {work_data.employment_type}",
            ) from e

        # Create new work history entry
        new_entry = WorkHistory(
            resume_id=str(resume_uuid),
            company_name=work_data.company_name,
            position_title=work_data.position_title,
            start_date=start_date_obj,
            end_date=end_date_obj,
            description=work_data.description,
            location=work_data.location,
            employment_type=employment_type_enum,
        )

        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)

        logger.info(f"Created work history entry {new_entry.id} for user {current_user.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_entry.id),
                "company_name": new_entry.company_name,
                "position_title": new_entry.position_title,
                "message": "Work history entry created successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work history for user {current_user.id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create work history: {str(e)}",
        ) from e


@router.get(
    "/{entry_id}",
    response_model=WorkHistoryItem,
    tags=["Work History"],
)
async def get_work_history_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a single work history entry by ID.

    Returns the specified work history entry if it belongs to the current user.

    Args:
        entry_id: UUID of the work history entry
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with work history entry details

    Raises:
        HTTPException(400): If entry_id is invalid format
        HTTPException(404): If entry not found or doesn't belong to user
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/profiles/me/work-history/123",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "id": "123",
            "company_name": "Tech Corp",
            "position_title": "Senior Developer",
            ...
        }
    """
    try:
        logger.info(f"Fetching work history entry {entry_id} for user: {current_user.id}")

        # Validate entry_id format
        try:
            entry_uuid = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid work history entry ID format: {entry_id}",
            )

        # Get the user's profile to verify ownership
        profile_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or resume not found.",
            )

        # Query work history entry
        query = select(WorkHistory).where(WorkHistory.id == entry_uuid)
        result = await db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work history entry not found: {entry_id}",
            )

        # Verify ownership - entry must belong to user's resume
        if str(entry.resume_id) != str(profile.resume_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This work history entry belongs to another user.",
            )

        # Convert to response format
        response_data = {
            "id": str(entry.id),
            "resume_id": str(entry.resume_id),
            "company_name": entry.company_name,
            "position_title": entry.position_title,
            "start_date": entry.start_date.isoformat() if entry.start_date else None,
            "end_date": entry.end_date.isoformat() if entry.end_date else None,
            "description": entry.description,
            "location": entry.location,
            "employment_type": entry.employment_type.value if entry.employment_type else EmploymentType.FULL_TIME.value,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work history entry {entry_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get work history entry: {str(e)}",
        ) from e


@router.put(
    "/{entry_id}",
    response_model=WorkHistoryItem,
    tags=["Work History"],
)
async def update_work_history_entry(
    entry_id: str,
    work_data: WorkHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing work history entry.

    Updates the specified work history entry with the provided data.
    Only updates fields that are provided (partial update supported).

    Args:
        entry_id: UUID of the work history entry to update
        work_data: Work history data to update
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        JSON response with updated work history entry details

    Raises:
        HTTPException(400): If entry_id is invalid format or data is invalid
        HTTPException(404): If entry not found or doesn't belong to user
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "position_title": "Lead Developer",
        ...     "description": "Led team of 5 developers"
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/profiles/me/work-history/123",
        ...     headers={"Authorization": "Bearer <token>"},
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "123",
            "company_name": "Tech Corp",
            "position_title": "Lead Developer",
            ...
        }
    """
    try:
        logger.info(f"Updating work history entry {entry_id} for user: {current_user.id}")

        # Validate entry_id format
        try:
            entry_uuid = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid work history entry ID format: {entry_id}",
            )

        # Get the user's profile to verify ownership
        profile_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or resume not found.",
            )

        # Query work history entry
        query = select(WorkHistory).where(WorkHistory.id == entry_uuid)
        result = await db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work history entry not found: {entry_id}",
            )

        # Verify ownership
        if str(entry.resume_id) != str(profile.resume_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This work history entry belongs to another user.",
            )

        # Update provided fields
        if work_data.company_name is not None:
            entry.company_name = work_data.company_name
        if work_data.position_title is not None:
            entry.position_title = work_data.position_title
        if work_data.description is not None:
            entry.description = work_data.description
        if work_data.location is not None:
            entry.location = work_data.location
        if work_data.employment_type is not None:
            try:
                entry.employment_type = EmploymentType(work_data.employment_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid employment_type: {work_data.employment_type}",
                )

        # Parse and update dates if provided
        if work_data.start_date is not None:
            try:
                entry.start_date = date.fromisoformat(work_data.start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {work_data.start_date}. Use ISO format (YYYY-MM-DD).",
                )

        if work_data.end_date is not None:
            try:
                entry.end_date = date.fromisoformat(work_data.end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {work_data.end_date}. Use ISO format (YYYY-MM-DD).",
                )

        await db.commit()
        await db.refresh(entry)

        logger.info(f"Updated work history entry {entry_id}")

        # Convert to response format
        response_data = {
            "id": str(entry.id),
            "resume_id": str(entry.resume_id),
            "company_name": entry.company_name,
            "position_title": entry.position_title,
            "start_date": entry.start_date.isoformat() if entry.start_date else None,
            "end_date": entry.end_date.isoformat() if entry.end_date else None,
            "description": entry.description,
            "location": entry.location,
            "employment_type": entry.employment_type.value if entry.employment_type else EmploymentType.FULL_TIME.value,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work history entry {entry_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update work history entry: {str(e)}",
        ) from e


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Work History"],
)
async def delete_work_history_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a work history entry.

    Permanently removes the specified work history entry from the database.

    Args:
        entry_id: UUID of the work history entry to delete
        current_user: The authenticated user (injected by JWT token)
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(400): If entry_id is invalid format
        HTTPException(404): If entry not found or doesn't belong to user
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/profiles/me/work-history/123",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.status_code
        204
    """
    try:
        logger.info(f"Deleting work history entry {entry_id} for user: {current_user.id}")

        # Validate entry_id format
        try:
            entry_uuid = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid work history entry ID format: {entry_id}",
            )

        # Get the user's profile to verify ownership
        profile_result = await db.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == str(current_user.id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile or not profile.resume_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or resume not found.",
            )

        # Query work history entry
        query = select(WorkHistory).where(WorkHistory.id == entry_uuid)
        result = await db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work history entry not found: {entry_id}",
            )

        # Verify ownership
        if str(entry.resume_id) != str(profile.resume_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This work history entry belongs to another user.",
            )

        # Delete the entry
        await db.delete(entry)
        await db.commit()

        logger.info(f"Deleted work history entry {entry_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting work history entry {entry_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete work history entry: {str(e)}",
        ) from e
