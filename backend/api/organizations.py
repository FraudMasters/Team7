"""
Organization management endpoints.

This module provides endpoints for managing organizations, including CRUD operations
for creating, reading, updating, and deleting organizations with support for
multi-tenant customization.
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
from models.organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class OrganizationCreate(BaseModel):
    """Request model for creating an organization."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    domain: Optional[str] = Field(None, max_length=255, description="Organization domain")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to organization logo")
    is_active: bool = Field(True, description="Whether organization is active")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class OrganizationUpdate(BaseModel):
    """Request model for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="URL-friendly identifier")
    domain: Optional[str] = Field(None, max_length=255, description="Organization domain")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to organization logo")
    is_active: Optional[bool] = Field(None, description="Whether organization is active")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        import re
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class OrganizationResponse(BaseModel):
    """Response model for a single organization."""

    id: str = Field(..., description="Unique identifier for the organization")
    name: str = Field(..., description="Organization name")
    slug: str = Field(..., description="URL-friendly identifier")
    domain: Optional[str] = Field(None, description="Organization domain")
    logo_url: Optional[str] = Field(None, description="URL to organization logo")
    is_active: bool = Field(..., description="Whether organization is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class OrganizationListResponse(BaseModel):
    """Response model for listing organizations."""

    organizations: List[OrganizationResponse] = Field(..., description="List of organizations")
    total_count: int = Field(..., description="Total number of organizations")


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
)
async def create_organization(
    request: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new organization.

    This endpoint creates a new organization with multi-tenant support for
    customized hiring workflows, branding, and configurations.

    Args:
        request: Request body containing organization details
        db: Database session

    Returns:
        JSON response with created organization details

    Raises:
        HTTPException(409): If slug or domain already exists
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/organizations/",
        ...     json={
        ...         "name": "Test Organization",
        ...         "slug": "test-org",
        ...         "domain": "example.com",
        ...         "is_active": True
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating organization '{request.name}' with slug: {request.slug}")

        # Check if slug already exists
        existing_slug = await db.execute(
            select(Organization).where(Organization.slug == request.slug)
        )
        if existing_slug.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with slug '{request.slug}' already exists",
            )

        # Check if domain already exists
        if request.domain:
            existing_domain = await db.execute(
                select(Organization).where(Organization.domain == request.domain)
            )
            if existing_domain.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Organization with domain '{request.domain}' already exists",
                )

        # Create new organization with UUID
        org_id = str(uuid4())
        new_org = Organization(
            id=org_id,
            name=request.name,
            slug=request.slug,
            domain=request.domain,
            logo_url=request.logo_url,
            is_active=request.is_active,
        )
        db.add(new_org)
        await db.flush()

        response_data = {
            "id": new_org.id,
            "name": new_org.name,
            "slug": new_org.slug,
            "domain": new_org.domain,
            "logo_url": new_org.logo_url,
            "is_active": new_org.is_active,
            "created_at": new_org.created_at.isoformat(),
            "updated_at": new_org.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created organization '{request.name}' with ID: {new_org.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}",
        ) from e


@router.get("/", tags=["Organizations"])
async def list_organizations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or slug"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List organizations with optional filters.

    This endpoint retrieves organizations with support for filtering by
    active status and searching by name or slug.

    Args:
        is_active: Optional active status filter
        search: Optional search term for name or slug
        db: Database session

    Returns:
        JSON response with list of organizations

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/organizations/")
        >>> response.json()
        {
            "organizations": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Listing organizations with filters - is_active: {is_active}, search: {search}")

        # Build query
        query = select(Organization)

        if is_active is not None:
            query = query.where(Organization.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Organization.name.ilike(search_pattern)) |
                (Organization.slug.ilike(search_pattern))
            )

        query = query.order_by(Organization.name)

        result = await db.execute(query)
        organizations = result.scalars().all()

        # Build response
        organizations_data = []
        for org in organizations:
            organizations_data.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "domain": org.domain,
                "logo_url": org.logo_url,
                "is_active": org.is_active,
                "created_at": org.created_at.isoformat(),
                "updated_at": org.updated_at.isoformat(),
            })

        response_data = {
            "organizations": organizations_data,
            "total_count": len(organizations_data),
        }

        logger.info(f"Retrieved {len(organizations_data)} organizations")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing organizations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}",
        ) from e


@router.get("/{organization_id}", tags=["Organizations"])
async def get_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific organization by ID.

    This endpoint retrieves detailed information about a single organization.

    Args:
        organization_id: UUID of the organization
        db: Database session

    Returns:
        JSON response with organization details

    Raises:
        HTTPException(404): If organization is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/organizations/org-uuid")
        >>> response.json()
        {
            "id": "org-uuid",
            "name": "Test Organization",
            "slug": "test-org",
            ...
        }
    """
    try:
        logger.info(f"Retrieving organization: {organization_id}")

        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization not found: {organization_id}",
            )

        response_data = {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "domain": org.domain,
            "logo_url": org.logo_url,
            "is_active": org.is_active,
            "created_at": org.created_at.isoformat(),
            "updated_at": org.updated_at.isoformat(),
        }

        logger.info(f"Retrieved organization: {organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization: {str(e)}",
        ) from e


@router.put("/{organization_id}", tags=["Organizations"])
async def update_organization(
    organization_id: str,
    request: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an organization.

    This endpoint updates an existing organization configuration.
    Only the fields specified in the request body will be updated.

    Args:
        organization_id: UUID of the organization
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated organization details

    Raises:
        HTTPException(404): If organization is not found
        HTTPException(409): If slug or domain conflicts
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/organizations/org-uuid",
        ...     json={
        ...         "name": "Updated Organization",
        ...         "is_active": False
        ...     }
        ... )
        >>> response.json()
        {
            "id": "org-uuid",
            "name": "Updated Organization",
            "is_active": false,
            ...
        }
    """
    try:
        logger.info(f"Updating organization: {organization_id}")

        # Get existing organization
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization not found: {organization_id}",
            )

        # Update fields if provided
        if request.name is not None:
            org.name = request.name

        if request.slug is not None:
            # Check if new slug conflicts with existing organization
            existing = await db.execute(
                select(Organization).where(
                    Organization.slug == request.slug,
                    Organization.id != organization_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Organization with slug '{request.slug}' already exists",
                )
            org.slug = request.slug

        if request.domain is not None:
            # Check if new domain conflicts with existing organization
            if request.domain:  # Only check if domain is not None/empty
                existing = await db.execute(
                    select(Organization).where(
                        Organization.domain == request.domain,
                        Organization.id != organization_id,
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Organization with domain '{request.domain}' already exists",
                    )
            org.domain = request.domain

        if request.logo_url is not None:
            org.logo_url = request.logo_url

        if request.is_active is not None:
            org.is_active = request.is_active

        await db.commit()
        await db.refresh(org)

        response_data = {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "domain": org.domain,
            "logo_url": org.logo_url,
            "is_active": org.is_active,
            "created_at": org.created_at.isoformat(),
            "updated_at": org.updated_at.isoformat(),
        }

        logger.info(f"Updated organization: {organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}",
        ) from e


@router.delete("/{organization_id}", tags=["Organizations"])
async def delete_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete an organization.

    This endpoint permanently deletes an organization configuration.
    This action cannot be undone.

    Args:
        organization_id: UUID of the organization
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If organization is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/organizations/org-uuid")
        >>> response.json()
        {
            "message": "Organization deleted successfully",
            "id": "org-uuid"
        }
    """
    try:
        logger.info(f"Deleting organization: {organization_id}")

        # Check if organization exists
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization not found: {organization_id}",
            )

        # Delete the organization
        await db.execute(
            delete(Organization).where(Organization.id == organization_id)
        )
        await db.commit()

        logger.info(f"Deleted organization: {organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Organization deleted successfully",
                "id": organization_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}",
        ) from e
