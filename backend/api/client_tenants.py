"""
Client tenant management endpoints.

This module provides endpoints for managing client tenant relationships between
recruitment agencies and their client organizations, including CRUD operations
for creating, reading, updating, and deleting client tenant records.
"""
import logging
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.client_tenant import ClientTenant, ClientTenantStatus
from models.agency import Agency
from models.organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class ClientTenantCreate(BaseModel):
    """Request model for creating a client tenant."""

    agency_id: str = Field(..., description="Agency ID")
    organization_id: str = Field(..., description="Organization ID")
    status: Optional[str] = Field(ClientTenantStatus.ACTIVE, description="Client tenant status")
    is_primary: bool = Field(True, description="Whether this is the primary agency for the organization")


class ClientTenantUpdate(BaseModel):
    """Request model for updating a client tenant."""

    status: Optional[str] = Field(None, description="Client tenant status")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary agency for the organization")


class ClientTenantResponse(BaseModel):
    """Response model for a single client tenant."""

    id: str = Field(..., description="Unique identifier for the client tenant")
    agency_id: str = Field(..., description="Agency ID")
    organization_id: str = Field(..., description="Organization ID")
    status: str = Field(..., description="Client tenant status")
    is_primary: bool = Field(..., description="Whether this is the primary agency")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ClientTenantListResponse(BaseModel):
    """Response model for listing client tenants."""

    client_tenants: List[ClientTenantResponse] = Field(..., description="List of client tenants")
    total_count: int = Field(..., description="Total number of client tenants")


@router.post(
    "/",
    response_model=ClientTenantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Client Tenants"],
)
async def create_client_tenant(
    request: ClientTenantCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new client tenant relationship.

    This endpoint creates a new relationship between a recruitment agency and
    a client organization, allowing the agency to manage candidates and jobs
    for that organization.

    Args:
        request: Request body containing client tenant details
        db: Database session

    Returns:
        JSON response with created client tenant details

    Raises:
        HTTPException(404): If agency or organization not found
        HTTPException(409): If relationship already exists
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/client-tenants/",
        ...     json={
        ...         "agency_id": "test-uuid",
        ...         "organization_id": "test-org-uuid",
        ...         "status": "active",
        ...         "is_primary": True
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating client tenant for agency '{request.agency_id}' and organization '{request.organization_id}'")

        # Verify agency exists
        existing_agency = await db.execute(
            select(Agency).where(Agency.id == request.agency_id)
        )
        if not existing_agency.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agency with id '{request.agency_id}' not found",
            )

        # Verify organization exists
        existing_org = await db.execute(
            select(Organization).where(Organization.id == request.organization_id)
        )
        if not existing_org.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{request.organization_id}' not found",
            )

        # Check if relationship already exists
        existing_relationship = await db.execute(
            select(ClientTenant).where(
                ClientTenant.agency_id == request.agency_id,
                ClientTenant.organization_id == request.organization_id
            )
        )
        if existing_relationship.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Client tenant relationship already exists between agency '{request.agency_id}' and organization '{request.organization_id}'",
            )

        # Validate status
        if request.status and request.status not in [s.value for s in ClientTenantStatus]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in ClientTenantStatus])}",
            )

        # Create new client tenant with UUID
        client_tenant_id = str(uuid4())
        new_client_tenant = ClientTenant(
            id=client_tenant_id,
            agency_id=request.agency_id,
            organization_id=request.organization_id,
            status=request.status or ClientTenantStatus.ACTIVE,
            is_primary=request.is_primary,
        )
        db.add(new_client_tenant)
        await db.flush()

        response_data = {
            "id": new_client_tenant.id,
            "agency_id": new_client_tenant.agency_id,
            "organization_id": new_client_tenant.organization_id,
            "status": new_client_tenant.status,
            "is_primary": new_client_tenant.is_primary,
            "created_at": new_client_tenant.created_at.isoformat(),
            "updated_at": new_client_tenant.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created client tenant with ID: {new_client_tenant.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating client tenant: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client tenant: {str(e)}",
        ) from e


@router.get("/", tags=["Client Tenants"])
async def list_client_tenants(
    agency_id: Optional[str] = Query(None, description="Filter by agency ID"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_primary: Optional[bool] = Query(None, description="Filter by primary flag"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List client tenants with optional filters.

    This endpoint retrieves a list of client tenant relationships with support
    for filtering by agency, organization, status, and primary flag.

    Args:
        agency_id: Optional agency ID filter
        organization_id: Optional organization ID filter
        status: Optional status filter
        is_primary: Optional primary flag filter
        db: Database session

    Returns:
        JSON response with list of client tenants and total count

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/client-tenants/",
        ...     params={"agency_id": "test-uuid"}
        ... )
        >>> response.status_code
        200
    """
    try:
        query = select(ClientTenant)

        # Apply filters
        if agency_id:
            query = query.where(ClientTenant.agency_id == agency_id)
        if organization_id:
            query = query.where(ClientTenant.organization_id == organization_id)
        if status:
            query = query.where(ClientTenant.status == status)
        if is_primary is not None:
            query = query.where(ClientTenant.is_primary == is_primary)

        result = await db.execute(query)
        client_tenants = result.scalars().all()

        response_data = {
            "client_tenants": [
                {
                    "id": ct.id,
                    "agency_id": ct.agency_id,
                    "organization_id": ct.organization_id,
                    "status": ct.status,
                    "is_primary": ct.is_primary,
                    "created_at": ct.created_at.isoformat(),
                    "updated_at": ct.updated_at.isoformat(),
                }
                for ct in client_tenants
            ],
            "total_count": len(client_tenants),
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error listing client tenants: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list client tenants: {str(e)}",
        ) from e


@router.get("/{client_tenant_id}", tags=["Client Tenants"])
async def get_client_tenant(
    client_tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific client tenant by ID.

    Args:
        client_tenant_id: Client tenant ID
        db: Database session

    Returns:
        JSON response with client tenant details

    Raises:
        HTTPException(404): If client tenant not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/client-tenants/test-uuid"
        ... )
        >>> response.status_code
        200
    """
    try:
        result = await db.execute(
            select(ClientTenant).where(ClientTenant.id == client_tenant_id)
        )
        client_tenant = result.scalar_one_or_none()

        if not client_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client tenant with id '{client_tenant_id}' not found",
            )

        response_data = {
            "id": client_tenant.id,
            "agency_id": client_tenant.agency_id,
            "organization_id": client_tenant.organization_id,
            "status": client_tenant.status,
            "is_primary": client_tenant.is_primary,
            "created_at": client_tenant.created_at.isoformat(),
            "updated_at": client_tenant.updated_at.isoformat(),
        }

        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client tenant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client tenant: {str(e)}",
        ) from e


@router.put("/{client_tenant_id}", tags=["Client Tenants"])
async def update_client_tenant(
    client_tenant_id: str,
    request: ClientTenantUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a client tenant.

    Args:
        client_tenant_id: Client tenant ID
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated client tenant details

    Raises:
        HTTPException(404): If client tenant not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/client-tenants/test-uuid",
        ...     json={"status": "inactive"}
        ... )
        >>> response.status_code
        200
    """
    try:
        result = await db.execute(
            select(ClientTenant).where(ClientTenant.id == client_tenant_id)
        )
        client_tenant = result.scalar_one_or_none()

        if not client_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client tenant with id '{client_tenant_id}' not found",
            )

        # Validate status if provided
        if request.status and request.status not in [s.value for s in ClientTenantStatus]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in ClientTenantStatus])}",
            )

        # Update fields
        if request.status is not None:
            client_tenant.status = request.status
        if request.is_primary is not None:
            client_tenant.is_primary = request.is_primary

        await db.flush()

        response_data = {
            "id": client_tenant.id,
            "agency_id": client_tenant.agency_id,
            "organization_id": client_tenant.organization_id,
            "status": client_tenant.status,
            "is_primary": client_tenant.is_primary,
            "created_at": client_tenant.created_at.isoformat(),
            "updated_at": client_tenant.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Updated client tenant with ID: {client_tenant_id}")

        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client tenant: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client tenant: {str(e)}",
        ) from e


@router.delete("/{client_tenant_id}", tags=["Client Tenants"])
async def delete_client_tenant(
    client_tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a client tenant.

    Args:
        client_tenant_id: Client tenant ID
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If client tenant not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/client-tenants/test-uuid"
        ... )
        >>> response.status_code
        200
    """
    try:
        result = await db.execute(
            select(ClientTenant).where(ClientTenant.id == client_tenant_id)
        )
        client_tenant = result.scalar_one_or_none()

        if not client_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client tenant with id '{client_tenant_id}' not found",
            )

        await db.execute(
            delete(ClientTenant).where(ClientTenant.id == client_tenant_id)
        )
        await db.commit()

        logger.info(f"Deleted client tenant with ID: {client_tenant_id}")

        return JSONResponse(
            content={"message": f"Client tenant with id '{client_tenant_id}' deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting client tenant: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client tenant: {str(e)}",
        ) from e
