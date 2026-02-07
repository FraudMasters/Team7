"""
IP whitelist management endpoints for organization access control.

This module provides endpoints for creating, reading, updating, and deleting
IP whitelist entries for organizations. Supports CIDR notation (e.g., 192.168.1.0/24)
and IP ranges (e.g., 192.168.1.1 - 192.168.1.100).
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, IPvAnyAddress, conint, constr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ip_whitelist import IPWhitelist
from models.security_config import SecurityConfig

logger = logging.getLogger(__name__)

router = APIRouter()


class IPWhitelistItemResponse(BaseModel):
    """Response model for a single IP whitelist entry."""

    id: str = Field(..., description="Entry ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Entry name/description")
    cidr: Optional[str] = Field(None, description="CIDR notation (e.g., 192.168.1.0/24)")
    ip_range_start: Optional[str] = Field(None, description="IP range start address")
    ip_range_end: Optional[str] = Field(None, description="IP range end address")
    is_active: bool = Field(..., description="Whether entry is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class IPWhitelistListResponse(BaseModel):
    """Response model for IP whitelist entries list."""

    entries: List[IPWhitelistItemResponse] = Field(..., description="List of entries")
    total_count: int = Field(..., description="Total number of entries")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Entries per page")


class IPWhitelistCreateRequest(BaseModel):
    """Request model for creating a new IP whitelist entry."""

    organization_id: str = Field(..., description="Organization ID")
    name: constr(min_length=1, max_length=255) = Field(
        ..., description="Entry name/description"
    )
    cidr: Optional[str] = Field(None, description="CIDR notation (e.g., 192.168.1.0/24)")
    ip_range_start: Optional[str] = Field(None, description="IP range start address")
    ip_range_end: Optional[str] = Field(None, description="IP range end address")
    is_active: bool = Field(True, description="Whether entry is active")


class IPWhitelistUpdateRequest(BaseModel):
    """Request model for updating an IP whitelist entry."""

    name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Entry name")
    cidr: Optional[str] = Field(None, description="CIDR notation")
    ip_range_start: Optional[str] = Field(None, description="IP range start address")
    ip_range_end: Optional[str] = Field(None, description="IP range end address")
    is_active: Optional[bool] = Field(None, description="Whether entry is active")


class IPWhitelistDeleteResponse(BaseModel):
    """Response model for delete operation."""

    id: str = Field(..., description="Deleted entry ID")
    message: str = Field(..., description="Deletion confirmation message")


class IPWhitelistStatsResponse(BaseModel):
    """Response model for IP whitelist statistics."""

    total_entries: int = Field(..., description="Total number of entries")
    active_entries: int = Field(..., description="Number of active entries")
    inactive_entries: int = Field(..., description="Number of inactive entries")
    cidr_entries: int = Field(..., description="Number of CIDR notation entries")
    range_entries: int = Field(..., description="Number of IP range entries")


def validate_cidr(cidr: str) -> bool:
    """
    Validate CIDR notation format.

    Args:
        cidr: CIDR string to validate

    Returns:
        True if valid CIDR notation
    """
    try:
        from ipaddress import ip_network

        ip_network(cidr, strict=False)
        return True
    except (ValueError, TypeError):
        return False


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format.

    Args:
        ip: IP address string to validate

    Returns:
        True if valid IP address
    """
    try:
        from ipaddress import ip_address

        ip_address(ip)
        return True
    except (ValueError, TypeError):
        return False


@router.get(
    "",
    response_model=IPWhitelistListResponse,
    summary="List IP whitelist entries",
    description="Retrieve a paginated list of IP whitelist entries with optional filtering",
)
async def list_ip_whitelist_entries(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: conint(ge=1) = Query(1, description="Page number"),
    per_page: conint(ge=1, le=100) = Query(50, description="Entries per page"),
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistListResponse:
    """
    List IP whitelist entries with pagination and filtering.

    Args:
        organization_id: Optional organization ID filter
        is_active: Optional active status filter
        page: Page number (1-indexed)
        per_page: Number of entries per page (max 100)
        db: Database session

    Returns:
        Paginated list of IP whitelist entries
    """
    query = select(IPWhitelist)

    # Apply filters
    if organization_id:
        query = query.where(IPWhitelist.organization_id == organization_id)
    if is_active is not None:
        query = query.where(IPWhitelist.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.order_by(IPWhitelist.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    entries = result.scalars().all()

    return IPWhitelistListResponse(
        entries=[
            IPWhitelistItemResponse(
                id=str(entry.id),
                organization_id=str(entry.organization_id),
                name=entry.name,
                cidr=entry.cidr,
                ip_range_start=entry.ip_range_start,
                ip_range_end=entry.ip_range_end,
                is_active=entry.is_active,
                created_at=entry.created_at.isoformat(),
                updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
            )
            for entry in entries
        ],
        total_count=total_count,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=IPWhitelistItemResponse,
    summary="Create IP whitelist entry",
    description="Create a new IP whitelist entry for an organization",
    status_code=status.HTTP_201_CREATED,
)
async def create_ip_whitelist_entry(
    data: IPWhitelistCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistItemResponse:
    """
    Create a new IP whitelist entry.

    Args:
        data: Entry creation data
        db: Database session

    Returns:
        Created entry details
    """
    # Validate that either CIDR or IP range is provided, not both
    if data.cidr and (data.ip_range_start or data.ip_range_end):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both CIDR and IP range. Use one format only.",
        )

    # Validate CIDR notation if provided
    if data.cidr and not validate_cidr(data.cidr):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CIDR notation: {data.cidr}",
        )

    # Validate IP range if provided
    if data.ip_range_start or data.ip_range_end:
        if not (data.ip_range_start and data.ip_range_end):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both ip_range_start and ip_range_end must be provided for IP range format",
            )
        if not validate_ip_address(data.ip_range_start) or not validate_ip_address(
            data.ip_range_end
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address format in range",
            )

    # Check if organization exists
    org_query = select(SecurityConfig).where(
        SecurityConfig.organization_id == data.organization_id
    )
    org_result = await db.execute(org_query)
    if not org_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {data.organization_id} not found",
        )

    # Create entry
    entry = IPWhitelist(
        organization_id=data.organization_id,
        name=data.name,
        cidr=data.cidr,
        ip_range_start=data.ip_range_start,
        ip_range_end=data.ip_range_end,
        is_active=data.is_active,
    )

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    logger.info(
        f"Created IP whitelist entry {entry.id} for organization {data.organization_id}"
    )

    return IPWhitelistItemResponse(
        id=str(entry.id),
        organization_id=str(entry.organization_id),
        name=entry.name,
        cidr=entry.cidr,
        ip_range_start=entry.ip_range_start,
        ip_range_end=entry.ip_range_end,
        is_active=entry.is_active,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
    )


@router.get(
    "/{entry_id}",
    response_model=IPWhitelistItemResponse,
    summary="Get IP whitelist entry",
    description="Retrieve details of a specific IP whitelist entry",
)
async def get_ip_whitelist_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistItemResponse:
    """
    Get a specific IP whitelist entry by ID.

    Args:
        entry_id: Entry ID
        db: Database session

    Returns:
        Entry details
    """
    query = select(IPWhitelist).where(IPWhitelist.id == entry_id)
    result = await db.execute(query)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found"
        )

    return IPWhitelistItemResponse(
        id=str(entry.id),
        organization_id=str(entry.organization_id),
        name=entry.name,
        cidr=entry.cidr,
        ip_range_start=entry.ip_range_start,
        ip_range_end=entry.ip_range_end,
        is_active=entry.is_active,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
    )


@router.put(
    "/{entry_id}",
    response_model=IPWhitelistItemResponse,
    summary="Update IP whitelist entry",
    description="Update an existing IP whitelist entry",
)
async def update_ip_whitelist_entry(
    entry_id: UUID,
    data: IPWhitelistUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistItemResponse:
    """
    Update an IP whitelist entry.

    Args:
        entry_id: Entry ID
        data: Update data
        db: Database session

    Returns:
        Updated entry details
    """
    query = select(IPWhitelist).where(IPWhitelist.id == entry_id)
    result = await db.execute(query)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found"
        )

    # Validate CIDR notation if being updated
    if data.cidr is not None and not validate_cidr(data.cidr):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CIDR notation: {data.cidr}",
        )

    # Validate IP range if being updated
    if data.ip_range_start or data.ip_range_end:
        if data.ip_range_start and not validate_ip_address(data.ip_range_start):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address format in ip_range_start",
            )
        if data.ip_range_end and not validate_ip_address(data.ip_range_end):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address format in ip_range_end",
            )

    # Update fields
    if data.name is not None:
        entry.name = data.name
    if data.cidr is not None:
        entry.cidr = data.cidr
    if data.ip_range_start is not None:
        entry.ip_range_start = data.ip_range_start
    if data.ip_range_end is not None:
        entry.ip_range_end = data.ip_range_end
    if data.is_active is not None:
        entry.is_active = data.is_active

    entry.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(entry)

    logger.info(f"Updated IP whitelist entry {entry_id}")

    return IPWhitelistItemResponse(
        id=str(entry.id),
        organization_id=str(entry.organization_id),
        name=entry.name,
        cidr=entry.cidr,
        ip_range_start=entry.ip_range_start,
        ip_range_end=entry.ip_range_end,
        is_active=entry.is_active,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
    )


@router.delete(
    "/{entry_id}",
    response_model=IPWhitelistDeleteResponse,
    summary="Delete IP whitelist entry",
    description="Delete an IP whitelist entry",
)
async def delete_ip_whitelist_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistDeleteResponse:
    """
    Delete an IP whitelist entry.

    Args:
        entry_id: Entry ID
        db: Database session

    Returns:
        Deletion confirmation
    """
    query = select(IPWhitelist).where(IPWhitelist.id == entry_id)
    result = await db.execute(query)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found"
        )

    await db.delete(entry)
    await db.commit()

    logger.info(f"Deleted IP whitelist entry {entry_id}")

    return IPWhitelistDeleteResponse(
        id=str(entry_id), message=f"IP whitelist entry {entry_id} deleted successfully"
    )


@router.get(
    "/stats/summary",
    response_model=IPWhitelistStatsResponse,
    summary="Get IP whitelist statistics",
    description="Retrieve statistics about IP whitelist entries",
)
async def get_ip_whitelist_stats(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    db: AsyncSession = Depends(get_db),
) -> IPWhitelistStatsResponse:
    """
    Get IP whitelist statistics.

    Args:
        organization_id: Optional organization ID filter
        db: Database session

    Returns:
        IP whitelist statistics
    """
    # Base query
    base_query = select(IPWhitelist)
    if organization_id:
        base_query = base_query.where(IPWhitelist.organization_id == organization_id)

    # Get counts
    total_query = select(func.count()).select_from(base_query.subquery())
    total_entries = (await db.execute(total_query)).scalar() or 0

    active_query = select(func.count()).select_from(
        base_query.where(IPWhitelist.is_active == True).subquery()
    )
    active_entries = (await db.execute(active_query)).scalar() or 0

    inactive_query = select(func.count()).select_from(
        base_query.where(IPWhitelist.is_active == False).subquery()
    )
    inactive_entries = (await db.execute(inactive_query)).scalar() or 0

    cidr_query = select(func.count()).select_from(
        base_query.where(IPWhitelist.cidr != None).subquery()
    )
    cidr_entries = (await db.execute(cidr_query)).scalar() or 0

    range_query = select(func.count()).select_from(
        base_query.where(IPWhitelist.ip_range_start != None).subquery()
    )
    range_entries = (await db.execute(range_query)).scalar() or 0

    return IPWhitelistStatsResponse(
        total_entries=total_entries,
        active_entries=active_entries,
        inactive_entries=inactive_entries,
        cidr_entries=cidr_entries,
        range_entries=range_entries,
    )
