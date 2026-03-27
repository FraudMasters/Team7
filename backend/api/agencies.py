"""
Agency management endpoints.

This module provides endpoints for managing recruitment agencies, including CRUD operations
for creating, reading, updating, and deleting agencies with support for
multi-tenant agency mode.
"""
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.agency import Agency
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class AgencyCreate(BaseModel):
    """Request model for creating an agency."""

    name: str = Field(..., min_length=1, max_length=255, description="Agency name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    domain: Optional[str] = Field(None, max_length=255, description="Agency domain")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to agency logo")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email for agency")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone for agency")
    is_active: bool = Field(True, description="Whether agency is active")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class AgencyUpdate(BaseModel):
    """Request model for updating an agency."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Agency name")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="URL-friendly identifier")
    domain: Optional[str] = Field(None, max_length=255, description="Agency domain")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to agency logo")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email for agency")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone for agency")
    is_active: Optional[bool] = Field(None, description="Whether agency is active")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        import re
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class AgencyResponse(BaseModel):
    """Response model for a single agency."""

    id: str = Field(..., description="Unique identifier for the agency")
    name: str = Field(..., description="Agency name")
    slug: str = Field(..., description="URL-friendly identifier")
    domain: Optional[str] = Field(None, description="Agency domain")
    logo_url: Optional[str] = Field(None, description="URL to agency logo")
    contact_email: Optional[str] = Field(None, description="Contact email for agency")
    contact_phone: Optional[str] = Field(None, description="Contact phone for agency")
    is_active: bool = Field(..., description="Whether agency is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class AgencyListResponse(BaseModel):
    """Response model for listing agencies."""

    agencies: List[AgencyResponse] = Field(..., description="List of agencies")
    total_count: int = Field(..., description="Total number of agencies")


@router.post(
    "/",
    response_model=AgencyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Agencies"],
)
async def create_agency(
    request: AgencyCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new agency.

    This endpoint creates a new agency with multi-tenant support for
    recruitment agencies managing multiple client organizations.

    Args:
        request: Request body containing agency details
        db: Database session

    Returns:
        JSON response with created agency details

    Raises:
        HTTPException(409): If slug or domain already exists
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/agencies/",
        ...     json={
        ...         "name": "Test Agency",
        ...         "slug": "test-agency",
        ...         "domain": "example.com",
        ...         "is_active": True
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating agency '{request.name}' with slug: {request.slug}")

        # Check if slug already exists
        existing_slug = await db.execute(
            select(Agency).where(Agency.slug == request.slug)
        )
        if existing_slug.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agency with slug '{request.slug}' already exists",
            )

        # Check if domain already exists
        if request.domain:
            existing_domain = await db.execute(
                select(Agency).where(Agency.domain == request.domain)
            )
            if existing_domain.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Agency with domain '{request.domain}' already exists",
                )

        # Create new agency with UUID
        agency_id = str(uuid4())
        new_agency = Agency(
            id=agency_id,
            name=request.name,
            slug=request.slug,
            domain=request.domain,
            logo_url=request.logo_url,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            is_active=request.is_active,
        )
        db.add(new_agency)
        await db.flush()

        response_data = {
            "id": new_agency.id,
            "name": new_agency.name,
            "slug": new_agency.slug,
            "domain": new_agency.domain,
            "logo_url": new_agency.logo_url,
            "contact_email": new_agency.contact_email,
            "contact_phone": new_agency.contact_phone,
            "is_active": new_agency.is_active,
            "created_at": new_agency.created_at.isoformat(),
            "updated_at": new_agency.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created agency '{request.name}' with ID: {new_agency.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agency: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agency: {str(e)}",
        ) from e


@router.get("/", tags=["Agencies"])
async def list_agencies(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or slug"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List agencies with optional filters.

    This endpoint retrieves all agencies with optional filtering by active status
    and search by name or slug.

    Args:
        is_active: Filter by active status (optional)
        search: Search by name or slug (optional)
        db: Database session

    Returns:
        JSON response with list of agencies and total count

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/agencies/")
        >>> response.status_code
        200
        >>> response.json()["total_count"]
        1
    """
    try:
        logger.info(f"Listing agencies - is_active: {is_active}, search: {search}")

        # Build query
        query = select(Agency)

        # Apply filters
        if is_active is not None:
            query = query.where(Agency.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Agency.name.ilike(search_pattern)) | (Agency.slug.ilike(search_pattern))
            )

        # Order by name
        query = query.order_by(Agency.name)

        # Execute query
        result = await db.execute(query)
        agencies = result.scalars().all()

        # Build response
        agencies_data = [
            {
                "id": agency.id,
                "name": agency.name,
                "slug": agency.slug,
                "domain": agency.domain,
                "logo_url": agency.logo_url,
                "contact_email": agency.contact_email,
                "contact_phone": agency.contact_phone,
                "is_active": agency.is_active,
                "created_at": agency.created_at.isoformat(),
                "updated_at": agency.updated_at.isoformat(),
            }
            for agency in agencies
        ]

        response_data = {
            "agencies": agencies_data,
            "total_count": len(agencies_data),
        }

        logger.info(f"Found {len(agencies_data)} agencies")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing agencies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agencies: {str(e)}",
        ) from e


@router.get("/{agency_id}", tags=["Agencies"])
async def get_agency(
    agency_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a single agency by ID.

    This endpoint retrieves detailed information about a specific agency.

    Args:
        agency_id: Unique identifier for the agency
        db: Database session

    Returns:
        JSON response with agency details

    Raises:
        HTTPException(404): If agency is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/agencies/123")
        >>> response.status_code
        200
    """
    try:
        logger.info(f"Getting agency with ID: {agency_id}")

        # Retrieve agency
        result = await db.execute(
            select(Agency).where(Agency.id == agency_id)
        )
        agency = result.scalar_one_or_none()

        if not agency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agency with ID '{agency_id}' not found",
            )

        response_data = {
            "id": agency.id,
            "name": agency.name,
            "slug": agency.slug,
            "domain": agency.domain,
            "logo_url": agency.logo_url,
            "contact_email": agency.contact_email,
            "contact_phone": agency.contact_phone,
            "is_active": agency.is_active,
            "created_at": agency.created_at.isoformat(),
            "updated_at": agency.updated_at.isoformat(),
        }

        logger.info(f"Retrieved agency '{agency.name}'")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agency: {str(e)}",
        ) from e


@router.put("/{agency_id}", tags=["Agencies"])
async def update_agency(
    agency_id: str,
    request: AgencyUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing agency.

    This endpoint updates an existing agency's information.

    Args:
        agency_id: Unique identifier for the agency
        request: Request body containing updated agency details
        db: Database session

    Returns:
        JSON response with updated agency details

    Raises:
        HTTPException(404): If agency is not found
        HTTPException(409): If updated slug or domain already exists
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/agencies/123",
        ...     json={"name": "Updated Agency Name"}
        ... )
        >>> response.status_code
        200
    """
    try:
        logger.info(f"Updating agency with ID: {agency_id}")

        # Retrieve existing agency
        result = await db.execute(
            select(Agency).where(Agency.id == agency_id)
        )
        agency = result.scalar_one_or_none()

        if not agency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agency with ID '{agency_id}' not found",
            )

        # Check if updated slug already exists
        if request.slug and request.slug != agency.slug:
            existing_slug = await db.execute(
                select(Agency).where(Agency.slug == request.slug)
            )
            if existing_slug.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Agency with slug '{request.slug}' already exists",
                )

        # Check if updated domain already exists
        if request.domain and request.domain != agency.domain:
            existing_domain = await db.execute(
                select(Agency).where(Agency.domain == request.domain)
            )
            if existing_domain.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Agency with domain '{request.domain}' already exists",
                )

        # Update fields
        if request.name is not None:
            agency.name = request.name
        if request.slug is not None:
            agency.slug = request.slug
        if request.domain is not None:
            agency.domain = request.domain
        if request.logo_url is not None:
            agency.logo_url = request.logo_url
        if request.contact_email is not None:
            agency.contact_email = request.contact_email
        if request.contact_phone is not None:
            agency.contact_phone = request.contact_phone
        if request.is_active is not None:
            agency.is_active = request.is_active

        await db.flush()

        response_data = {
            "id": agency.id,
            "name": agency.name,
            "slug": agency.slug,
            "domain": agency.domain,
            "logo_url": agency.logo_url,
            "contact_email": agency.contact_email,
            "contact_phone": agency.contact_phone,
            "is_active": agency.is_active,
            "created_at": agency.created_at.isoformat(),
            "updated_at": agency.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Updated agency '{agency.name}' with ID: {agency_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agency: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agency: {str(e)}",
        ) from e


@router.delete("/{agency_id}", tags=["Agencies"])
async def delete_agency(
    agency_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete an agency.

    This endpoint deletes an agency from the system.

    Args:
        agency_id: Unique identifier for the agency
        db: Database session

    Returns:
        JSON response with success message

    Raises:
        HTTPException(404): If agency is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/agencies/123")
        >>> response.status_code
        200
    """
    try:
        logger.info(f"Deleting agency with ID: {agency_id}")

        # Check if agency exists
        result = await db.execute(
            select(Agency).where(Agency.id == agency_id)
        )
        agency = result.scalar_one_or_none()

        if not agency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agency with ID '{agency_id}' not found",
            )

        # Delete agency
        await db.execute(
            delete(Agency).where(Agency.id == agency_id)
        )
        await db.commit()

        logger.info(f"Deleted agency with ID: {agency_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Agency with ID '{agency_id}' successfully deleted",
                "id": agency_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agency: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agency: {str(e)}",
        ) from e
