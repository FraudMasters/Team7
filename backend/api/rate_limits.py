"""
Rate limit management endpoints.

This module provides endpoints for:
- Listing and managing rate limit policies for organizations
- Viewing current API usage statistics
- Managing IP blocklists for DDoS protection
- Configuring tiered rate limits based on user roles

Provides administrative interfaces for monitoring and controlling API rate limits.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.rate_limit_config import RateLimitConfig
from models.ip_blocklist import IPBlocklist
from services.rate_limit_service import get_rate_limit_service, RateLimitService, RateLimitTier

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class RateLimitPolicyInfo(BaseModel):
    """Information about a rate limit policy."""

    id: str = Field(..., description="Policy ID (UUID)")
    organization_id: str = Field(..., description="Organization ID")
    endpoint_pattern: Optional[str] = Field(None, description="Endpoint pattern (e.g., /api/v1/*)")
    requests_per_window: int = Field(..., description="Maximum requests per time window")
    window_size_seconds: int = Field(..., description="Time window size in seconds")
    role_type: Optional[str] = Field(None, description="Role type for role-based limits")
    is_enabled: bool = Field(..., description="Whether policy is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class RateLimitPolicyCreate(BaseModel):
    """Request model for creating a rate limit policy."""

    organization_id: str = Field(..., description="Organization ID")
    endpoint_pattern: Optional[str] = Field(None, description="Optional endpoint pattern")
    requests_per_window: int = Field(..., description="Maximum requests per time window", ge=1)
    window_size_seconds: int = Field(..., description="Time window size in seconds", ge=1)
    role_type: Optional[str] = Field(None, description="Optional role type (admin, org_admin, user, anonymous)")
    is_enabled: bool = Field(True, description="Whether to enable the policy")


class RateLimitPolicyUpdate(BaseModel):
    """Request model for updating a rate limit policy."""

    endpoint_pattern: Optional[str] = Field(None, description="Endpoint pattern")
    requests_per_window: Optional[int] = Field(None, description="Maximum requests per time window", ge=1)
    window_size_seconds: Optional[int] = Field(None, description="Time window size in seconds", ge=1)
    role_type: Optional[str] = Field(None, description="Role type for role-based limits")
    is_enabled: Optional[bool] = Field(None, description="Whether to enable the policy")


class RateLimitPolicyResponse(BaseModel):
    """Response model for rate limit policy operations."""

    id: str = Field(..., description="Policy ID")
    message: str = Field(..., description="Success message")
    policy: RateLimitPolicyInfo = Field(..., description="Policy details")


class RateLimitPoliciesResponse(BaseModel):
    """Response model for listing rate limit policies."""

    organization_id: Optional[str] = Field(None, description="Organization filter applied")
    total_policies: int = Field(..., description="Total number of policies")
    policies: List[RateLimitPolicyInfo] = Field(..., description="List of rate limit policies")


class APIUsageStats(BaseModel):
    """API usage statistics for an identifier."""

    identifier: str = Field(..., description="User ID, IP, or other identifier")
    tier: str = Field(..., description="Rate limit tier applied")
    limit: int = Field(..., description="Rate limit for this tier")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_at: int = Field(..., description="Unix timestamp when limit resets")
    window_used_percent: float = Field(..., description="Percentage of window used")


class APIUsageResponse(BaseModel):
    """Response model for API usage statistics."""

    stats: List[APIUsageStats] = Field(..., description="Usage statistics")
    total_identifiers: int = Field(..., description="Total number of identifiers tracked")


class IPBlocklistInfo(BaseModel):
    """Information about a blocked IP or network."""

    id: str = Field(..., description="Block entry ID")
    ip_address: Optional[str] = Field(None, description="Blocked IP address")
    cidr: Optional[str] = Field(None, description="Blocked CIDR range")
    block_reason: Optional[str] = Field(None, description="Reason for block")
    is_active: bool = Field(..., description="Whether block is active")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    created_by: Optional[str] = Field(None, description="Who created this block")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class IPBlockCreate(BaseModel):
    """Request model for adding an IP or network to blocklist."""

    ip_address: Optional[str] = Field(None, description="Individual IP address to block")
    cidr: Optional[str] = Field(None, description="CIDR range to block")
    block_reason: Optional[str] = Field(None, description="Reason for blocking")
    duration_seconds: Optional[int] = Field(None, description="Block duration in seconds", ge=1)
    created_by: Optional[str] = Field(None, description="User or system creating the block")


class IPBlockResponse(BaseModel):
    """Response model for IP block operations."""

    id: str = Field(..., description="Block entry ID")
    message: str = Field(..., description="Success message")
    block: IPBlocklistInfo = Field(..., description="Block details")


class IPBlocklistResponse(BaseModel):
    """Response model for listing IP blocklist."""

    total_blocks: int = Field(..., description="Total number of blocks")
    active_blocks: int = Field(..., description="Number of active blocks")
    blocks: List[IPBlocklistInfo] = Field(..., description="List of blocked IPs/networks")


@router.get(
    "/policies",
    response_model=RateLimitPoliciesResponse,
    tags=["Rate Limits"],
)
async def list_rate_limit_policies(
    request: Request,
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List rate limit policies with optional filters.

    Returns a paginated list of rate limit policies. Can be filtered by
    organization, role type, or enabled status. Useful for monitoring
    and managing rate limit configurations.

    Args:
        request: FastAPI request object
        organization_id: Optional filter by organization ID
        role_type: Optional filter by role type
        is_enabled: Optional filter by enabled status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of rate limit policies

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all policies
        >>> response = requests.get("http://localhost:8000/api/rate-limits/policies")
        >>> # Filter by organization
        >>> response = requests.get("http://localhost:8000/api/rate-limits/policies?organization_id=org123")
        >>> # Filter by role
        >>> response = requests.get("http://localhost:8000/api/rate-limits/policies?role_type=user")
    """
    try:
        logger.info(
            f"Fetching rate limit policies - organization_id: {organization_id}, "
            f"role_type: {role_type}, is_enabled: {is_enabled}, skip: {skip}, limit: {limit}"
        )

        # Build query
        query = select(RateLimitConfig)

        # Apply filters
        if organization_id:
            query = query.where(RateLimitConfig.organization_id == organization_id)
        if role_type:
            query = query.where(RateLimitConfig.role_type == role_type)
        if is_enabled is not None:
            query = query.where(RateLimitConfig.is_enabled == is_enabled)

        # Order by created_at descending (newest first)
        query = query.order_by(RateLimitConfig.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        policies = result.scalars().all()

        # Convert to response format
        policies_list = []
        for policy in policies:
            policies_list.append({
                "id": str(policy.id),
                "organization_id": policy.organization_id,
                "endpoint_pattern": policy.endpoint_pattern,
                "requests_per_window": policy.requests_per_window,
                "window_size_seconds": policy.window_size_seconds,
                "role_type": policy.role_type,
                "is_enabled": policy.is_enabled,
                "created_at": policy.created_at.isoformat() if policy.created_at else None,
                "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
            })

        logger.info(f"Retrieved {len(policies_list)} rate limit policies")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "organization_id": organization_id,
                "total_policies": len(policies_list),
                "policies": policies_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing rate limit policies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rate limit policies: {str(e)}",
        ) from e


@router.post(
    "/policies",
    response_model=RateLimitPolicyResponse,
    tags=["Rate Limits"],
)
async def create_rate_limit_policy(
    request: Request,
    policy_data: RateLimitPolicyCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new rate limit policy.

    Creates a new rate limit policy for an organization. Policies can be
    endpoint-specific or apply globally. Role-based policies override
    default tier limits.

    Args:
        request: FastAPI request object
        policy_data: Rate limit policy details
        db: Database session

    Returns:
        JSON response with created policy details

    Raises:
        HTTPException(400): Invalid policy data
        HTTPException(500): If creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org123",
        ...     "requests_per_window": 1000,
        ...     "window_size_seconds": 60,
        ...     "role_type": "user"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/rate-limits/policies",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Creating rate limit policy for organization {policy_data.organization_id}")

        # Create new policy
        new_policy = RateLimitConfig(
            organization_id=policy_data.organization_id,
            endpoint_pattern=policy_data.endpoint_pattern,
            requests_per_window=policy_data.requests_per_window,
            window_size_seconds=policy_data.window_size_seconds,
            role_type=policy_data.role_type,
            is_enabled=policy_data.is_enabled,
        )

        db.add(new_policy)
        await db.commit()
        await db.refresh(new_policy)

        logger.info(f"Created rate limit policy {new_policy.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_policy.id),
                "message": "Rate limit policy created successfully",
                "policy": {
                    "id": str(new_policy.id),
                    "organization_id": new_policy.organization_id,
                    "endpoint_pattern": new_policy.endpoint_pattern,
                    "requests_per_window": new_policy.requests_per_window,
                    "window_size_seconds": new_policy.window_size_seconds,
                    "role_type": new_policy.role_type,
                    "is_enabled": new_policy.is_enabled,
                    "created_at": new_policy.created_at.isoformat() if new_policy.created_at else None,
                    "updated_at": new_policy.updated_at.isoformat() if new_policy.updated_at else None,
                },
            },
        )

    except Exception as e:
        logger.error(f"Error creating rate limit policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rate limit policy: {str(e)}",
        ) from e


@router.put(
    "/policies",
    response_model=RateLimitPolicyResponse,
    tags=["Rate Limits"],
)
async def update_rate_limit_policy_by_org(
    request: Request,
    policy_data: RateLimitPolicyUpdate,
    organization_id: str = Query(..., description="Organization ID"),
    role_type: Optional[str] = Query(None, description="Role type to match"),
    endpoint_pattern: Optional[str] = Query(None, description="Endpoint pattern to match"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update rate limit policy for an organization.

    Updates the first matching rate limit policy for the specified organization.
    Match criteria: organization_id (required), optional role_type, optional endpoint_pattern.
    If multiple policies match, updates the most recently created one.

    Args:
        request: FastAPI request object
        policy_data: Fields to update
        organization_id: Organization ID (required)
        role_type: Optional role type to match for policy selection
        endpoint_pattern: Optional endpoint pattern to match for policy selection
        db: Database session

    Returns:
        JSON response with updated policy details

    Raises:
        HTTPException(404): No matching policy found
        HTTPException(500): If update fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "requests_per_window": 2000,
        ...     "is_enabled": True
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/rate-limits/policies?organization_id=org123",
        ...     json=data
        ... )
        >>> # Update with role filter
        >>> response = requests.put(
        ...     "http://localhost:8000/api/rate-limits/policies?organization_id=org123&role_type=user",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Updating rate limit policy for organization {organization_id}, "
            f"role_type: {role_type}, endpoint_pattern: {endpoint_pattern}"
        )

        # Build query to find matching policy
        query = select(RateLimitConfig).where(
            RateLimitConfig.organization_id == organization_id
        )

        # Apply optional filters
        if role_type:
            query = query.where(RateLimitConfig.role_type == role_type)
        if endpoint_pattern:
            query = query.where(RateLimitConfig.endpoint_pattern == endpoint_pattern)

        # Order by created_at descending to get most recent policy
        query = query.order_by(RateLimitConfig.created_at.desc()).limit(1)

        # Execute query
        result = await db.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rate limit policy found for organization {organization_id} with specified criteria",
            )

        # Update fields if provided
        if policy_data.endpoint_pattern is not None:
            policy.endpoint_pattern = policy_data.endpoint_pattern
        if policy_data.requests_per_window is not None:
            policy.requests_per_window = policy_data.requests_per_window
        if policy_data.window_size_seconds is not None:
            policy.window_size_seconds = policy_data.window_size_seconds
        if policy_data.role_type is not None:
            policy.role_type = policy_data.role_type
        if policy_data.is_enabled is not None:
            policy.is_enabled = policy_data.is_enabled

        await db.commit()
        await db.refresh(policy)

        logger.info(f"Updated rate limit policy {policy.id} for organization {organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(policy.id),
                "message": "Rate limit policy updated successfully",
                "policy": {
                    "id": str(policy.id),
                    "organization_id": policy.organization_id,
                    "endpoint_pattern": policy.endpoint_pattern,
                    "requests_per_window": policy.requests_per_window,
                    "window_size_seconds": policy.window_size_seconds,
                    "role_type": policy.role_type,
                    "is_enabled": policy.is_enabled,
                    "created_at": policy.created_at.isoformat() if policy.created_at else None,
                    "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rate limit policy for organization {organization_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rate limit policy: {str(e)}",
        ) from e


@router.put(
    "/policies/{policy_id}",
    response_model=RateLimitPolicyResponse,
    tags=["Rate Limits"],
)
async def update_rate_limit_policy(
    request: Request,
    policy_id: str,
    policy_data: RateLimitPolicyUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing rate limit policy.

    Updates the specified rate limit policy. Only provided fields are updated.
    Useful for adjusting rate limits or enabling/disabling policies.

    Args:
        request: FastAPI request object
        policy_id: Policy UUID
        policy_data: Fields to update
        db: Database session

    Returns:
        JSON response with updated policy details

    Raises:
        HTTPException(404): Policy not found
        HTTPException(500): If update fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "requests_per_window": 2000,
        ...     "is_enabled": True
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/rate-limits/policies/policy-uuid",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Updating rate limit policy {policy_id}")

        # Parse policy_id as UUID
        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid policy ID format: {policy_id}",
            )

        # Get existing policy
        query = select(RateLimitConfig).where(RateLimitConfig.id == policy_uuid)
        result = await db.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rate limit policy not found: {policy_id}",
            )

        # Update fields if provided
        if policy_data.endpoint_pattern is not None:
            policy.endpoint_pattern = policy_data.endpoint_pattern
        if policy_data.requests_per_window is not None:
            policy.requests_per_window = policy_data.requests_per_window
        if policy_data.window_size_seconds is not None:
            policy.window_size_seconds = policy_data.window_size_seconds
        if policy_data.role_type is not None:
            policy.role_type = policy_data.role_type
        if policy_data.is_enabled is not None:
            policy.is_enabled = policy_data.is_enabled

        await db.commit()
        await db.refresh(policy)

        logger.info(f"Updated rate limit policy {policy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(policy.id),
                "message": "Rate limit policy updated successfully",
                "policy": {
                    "id": str(policy.id),
                    "organization_id": policy.organization_id,
                    "endpoint_pattern": policy.endpoint_pattern,
                    "requests_per_window": policy.requests_per_window,
                    "window_size_seconds": policy.window_size_seconds,
                    "role_type": policy.role_type,
                    "is_enabled": policy.is_enabled,
                    "created_at": policy.created_at.isoformat() if policy.created_at else None,
                    "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rate limit policy {policy_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rate limit policy: {str(e)}",
        ) from e


@router.get(
    "/usage",
    response_model=APIUsageResponse,
    tags=["Rate Limits"],
)
async def get_api_usage(
    request: Request,
    identifiers: Optional[List[str]] = Query(None, description="List of identifiers to check"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get current API usage statistics.

    Returns current rate limit usage for specified identifiers (user IDs, IPs, etc.).
    Useful for monitoring API usage and planning capacity.

    Args:
        request: FastAPI request object
        identifiers: Optional list of identifiers to check (default: return sample)
        db: Database session

    Returns:
        JSON response with usage statistics

    Raises:
        HTTPException(500): If retrieval fails

    Examples:
        >>> import requests
        >>> # Get usage for specific users
        >>> response = requests.get(
        ...     "http://localhost:8000/api/rate-limits/usage?identifiers=user1&identifiers=user2"
        ... )
        >>> # Get sample usage
        >>> response = requests.get("http://localhost:8000/api/rate-limits/usage")
    """
    try:
        logger.info(f"Fetching API usage for {len(identifiers) if identifiers else 0} identifiers")

        # Get rate limit service
        rate_limit_service = get_rate_limit_service()

        # If no identifiers provided, return empty response or sample data
        if not identifiers:
            logger.info("No identifiers provided, returning empty usage stats")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "stats": [],
                    "total_identifiers": 0,
                },
            )

        usage_stats = []

        # Get usage for each identifier
        for identifier in identifiers:
            try:
                # Check rate limit for this identifier
                # Note: This doesn't actually consume a request, just checks the status
                # We'll use a default tier for checking
                result = rate_limit_service.check_rate_limit(
                    identifier=identifier,
                    tier=RateLimitTier.USER,
                    endpoint="usage_check",
                )

                # Calculate window usage percentage
                window_used_percent = (result.limit - result.remaining) / result.limit * 100 if result.limit > 0 else 0

                usage_stats.append({
                    "identifier": identifier,
                    "tier": result.tier.value,
                    "limit": result.limit,
                    "remaining": result.remaining,
                    "reset_at": result.reset_at,
                    "window_used_percent": round(window_used_percent, 2),
                })

            except Exception as e:
                logger.warning(f"Error getting usage for identifier {identifier}: {e}")
                # Continue with other identifiers
                continue

        logger.info(f"Retrieved usage stats for {len(usage_stats)} identifiers")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "stats": usage_stats,
                "total_identifiers": len(usage_stats),
            },
        )

    except Exception as e:
        logger.error(f"Error getting API usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API usage: {str(e)}",
        ) from e


@router.get(
    "/blocklist",
    response_model=IPBlocklistResponse,
    tags=["Rate Limits"],
)
async def list_ip_blocklist(
    request: Request,
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List IP blocklist entries.

    Returns a paginated list of blocked IP addresses and networks.
    Can be filtered by IP address or active status.

    Args:
        request: FastAPI request object
        ip_address: Optional filter by IP address
        is_active: Optional filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of blocked IPs/networks

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all blocks
        >>> response = requests.get("http://localhost:8000/api/rate-limits/blocklist")
        >>> # Get active blocks only
        >>> response = requests.get("http://localhost:8000/api/rate-limits/blocklist?is_active=true")
        >>> # Check specific IP
        >>> response = requests.get(
        ...     "http://localhost:8000/api/rate-limits/blocklist?ip_address=192.168.1.1"
        ... )
    """
    try:
        logger.info(
            f"Fetching IP blocklist - ip_address: {ip_address}, "
            f"is_active: {is_active}, skip: {skip}, limit: {limit}"
        )

        # Build query
        query = select(IPBlocklist)

        # Apply filters
        if ip_address:
            query = query.where(IPBlocklist.ip_address == ip_address)
        if is_active is not None:
            query = query.where(IPBlocklist.is_active == is_active)

        # Order by created_at descending (newest first)
        query = query.order_by(IPBlocklist.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        blocks = result.scalars().all()

        # Count active blocks
        active_count = 0
        for block in blocks:
            if block.is_active:
                active_count += 1

        # Convert to response format
        blocks_list = []
        for block in blocks:
            blocks_list.append({
                "id": str(block.id),
                "ip_address": block.ip_address,
                "cidr": block.cidr,
                "block_reason": block.block_reason,
                "is_active": block.is_active,
                "expires_at": block.expires_at.isoformat() if block.expires_at else None,
                "created_by": block.created_by,
                "created_at": block.created_at.isoformat() if block.created_at else None,
                "updated_at": block.updated_at.isoformat() if block.updated_at else None,
            })

        logger.info(f"Retrieved {len(blocks_list)} IP blocklist entries ({active_count} active)")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_blocks": len(blocks_list),
                "active_blocks": active_count,
                "blocks": blocks_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing IP blocklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list IP blocklist: {str(e)}",
        ) from e


@router.post(
    "/blocklist",
    response_model=IPBlockResponse,
    tags=["Rate Limits"],
)
async def add_to_ip_blocklist(
    request: Request,
    block_data: IPBlockCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Add an IP address or network to the blocklist.

    Blocks the specified IP address or CIDR range. Optionally set an
    expiration time for temporary blocks. Useful for responding to
    abusive behavior or DDoS attacks.

    Args:
        request: FastAPI request object
        block_data: IP block details
        db: Database session

    Returns:
        JSON response with created block entry

    Raises:
        HTTPException(400): Invalid block data (must provide ip_address or cidr)
        HTTPException(500): If creation fails

    Examples:
        >>> import requests
        >>> # Block a specific IP for 1 hour
        >>> data = {
        ...     "ip_address": "192.168.1.100",
        ...     "block_reason": "Abusive behavior",
        ...     "duration_seconds": 3600,
        ...     "created_by": "admin@example.com"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/rate-limits/blocklist",
        ...     json=data
        ... )
        >>> # Block a CIDR range permanently
        >>> data = {
        ...     "cidr": "10.0.0.0/8",
        ...     "block_reason": "DDoS attack source"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/rate-limits/blocklist",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Adding to IP blocklist - ip: {block_data.ip_address}, cidr: {block_data.cidr}")

        # Validate that either ip_address or cidr is provided
        if not block_data.ip_address and not block_data.cidr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either ip_address or cidr",
            )

        # Calculate expiration time if duration is provided
        expires_at = None
        if block_data.duration_seconds:
            expires_at = datetime.now(timezone.utc) + __import__('datetime').timedelta(
                seconds=block_data.duration_seconds
            )

        # Create new block entry
        new_block = IPBlocklist(
            ip_address=block_data.ip_address,
            cidr=block_data.cidr,
            block_reason=block_data.block_reason,
            is_active=True,
            expires_at=expires_at,
            created_by=block_data.created_by,
        )

        db.add(new_block)
        await db.commit()
        await db.refresh(new_block)

        logger.info(f"Added IP blocklist entry {new_block.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_block.id),
                "message": "IP blocklist entry created successfully",
                "block": {
                    "id": str(new_block.id),
                    "ip_address": new_block.ip_address,
                    "cidr": new_block.cidr,
                    "block_reason": new_block.block_reason,
                    "is_active": new_block.is_active,
                    "expires_at": new_block.expires_at.isoformat() if new_block.expires_at else None,
                    "created_by": new_block.created_by,
                    "created_at": new_block.created_at.isoformat() if new_block.created_at else None,
                    "updated_at": new_block.updated_at.isoformat() if new_block.updated_at else None,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to IP blocklist: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to IP blocklist: {str(e)}",
        ) from e


@router.delete(
    "/blocklist/{block_id}",
    response_model=IPBlockResponse,
    tags=["Rate Limits"],
)
async def remove_from_ip_blocklist(
    request: Request,
    block_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Remove an entry from the IP blocklist.

    Deactivates the specified IP blocklist entry. The record is kept
    for audit purposes but marked as inactive.

    Args:
        request: FastAPI request object
        block_id: Block entry UUID
        db: Database session

    Returns:
        JSON response with deactivated block details

    Raises:
        HTTPException(404): Block entry not found
        HTTPException(500): If deletion fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/rate-limits/blocklist/block-uuid"
        ... )
    """
    try:
        logger.info(f"Removing IP blocklist entry {block_id}")

        # Parse block_id as UUID
        try:
            block_uuid = UUID(block_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid block ID format: {block_id}",
            )

        # Get existing block
        query = select(IPBlocklist).where(IPBlocklist.id == block_uuid)
        result = await db.execute(query)
        block = result.scalar_one_or_none()

        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IP blocklist entry not found: {block_id}",
            )

        # Deactivate the block
        block.is_active = False
        await db.commit()
        await db.refresh(block)

        logger.info(f"Deactivated IP blocklist entry {block_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(block.id),
                "message": "IP blocklist entry deactivated successfully",
                "block": {
                    "id": str(block.id),
                    "ip_address": block.ip_address,
                    "cidr": block.cidr,
                    "block_reason": block.block_reason,
                    "is_active": block.is_active,
                    "expires_at": block.expires_at.isoformat() if block.expires_at else None,
                    "created_by": block.created_by,
                    "created_at": block.created_at.isoformat() if block.created_at else None,
                    "updated_at": block.updated_at.isoformat() if block.updated_at else None,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from IP blocklist: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from IP blocklist: {str(e)}",
        ) from e
