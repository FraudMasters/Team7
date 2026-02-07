"""
Security configuration endpoints for managing organization security settings.

This module provides endpoints for retrieving and updating security configurations
including two-factor authentication settings, session policies, password policies,
SSO requirements, and IP whitelist management.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database import get_db
from models.ip_whitelist import IPWhitelist
from models.security_config import SecurityConfig

logger = logging.getLogger(__name__)

router = APIRouter()


class SecurityConfigResponse(BaseModel):
    """Response model for security configuration."""

    id: str = Field(..., description="Security config ID")
    organization_id: Optional[str] = Field(None, description="Organization ID (null for system default)")
    two_factor_required: bool = Field(..., description="Whether 2FA is mandatory for all users")
    two_factor_enabled: bool = Field(..., description="Whether 2FA is available for users to enable")
    session_timeout_minutes: int = Field(..., description="Session timeout in minutes (0 for no timeout)")
    max_concurrent_sessions: int = Field(..., description="Maximum concurrent sessions per user (0 for unlimited)")
    ip_whitelist_enabled: bool = Field(..., description="Whether IP whitelist restrictions are enforced")
    ip_whitelist_strict: bool = Field(..., description="Block all access when no whitelist is configured")
    password_min_length: int = Field(..., description="Minimum password length in characters")
    password_require_uppercase: bool = Field(..., description="Whether passwords must contain uppercase letters")
    password_require_lowercase: bool = Field(..., description="Whether passwords must contain lowercase letters")
    password_require_numbers: bool = Field(..., description="Whether passwords must contain numbers")
    password_require_special: bool = Field(..., description="Whether passwords must contain special characters")
    password_expiry_days: int = Field(..., description="Password expiry in days (0 for no expiry)")
    sso_required: bool = Field(..., description="Whether SSO is mandatory for authentication")
    sso_only: bool = Field(..., description="Whether only SSO authentication is allowed")
    security_alerts_enabled: bool = Field(..., description="Whether automatic security alerts are enabled")
    failed_login_threshold: int = Field(..., description="Number of failed logins before alert (0 to disable)")
    created_at: str = Field(..., description="When the config was created")
    updated_at: str = Field(..., description="When the config was last updated")


class SecurityConfigUpdate(BaseModel):
    """Request model for updating security configuration."""

    two_factor_required: Optional[bool] = Field(None, description="Whether 2FA is mandatory for all users")
    two_factor_enabled: Optional[bool] = Field(None, description="Whether 2FA is available for users to enable")
    session_timeout_minutes: Optional[int] = Field(None, ge=0, le=10080, description="Session timeout in minutes (0 for no timeout, max 7 days)")
    max_concurrent_sessions: Optional[int] = Field(None, ge=0, le=100, description="Maximum concurrent sessions per user (0 for unlimited)")
    ip_whitelist_enabled: Optional[bool] = Field(None, description="Whether IP whitelist restrictions are enforced")
    ip_whitelist_strict: Optional[bool] = Field(None, description="Block all access when no whitelist is configured")
    password_min_length: Optional[int] = Field(None, ge=8, le=128, description="Minimum password length in characters")
    password_require_uppercase: Optional[bool] = Field(None, description="Whether passwords must contain uppercase letters")
    password_require_lowercase: Optional[bool] = Field(None, description="Whether passwords must contain lowercase letters")
    password_require_numbers: Optional[bool] = Field(None, description="Whether passwords must contain numbers")
    password_require_special: Optional[bool] = Field(None, description="Whether passwords must contain special characters")
    password_expiry_days: Optional[int] = Field(None, ge=0, le=365, description="Password expiry in days (0 for no expiry)")
    sso_required: Optional[bool] = Field(None, description="Whether SSO is mandatory for authentication")
    sso_only: Optional[bool] = Field(None, description="Whether only SSO authentication is allowed")
    security_alerts_enabled: Optional[bool] = Field(None, description="Whether automatic security alerts are enabled")
    failed_login_threshold: Optional[int] = Field(None, ge=0, le=100, description="Number of failed logins before alert (0 to disable)")


class SecurityConfigCreate(BaseModel):
    """Request model for creating security configuration."""

    organization_id: str = Field(..., description="Organization ID")
    two_factor_required: bool = Field(default=False, description="Whether 2FA is mandatory for all users")
    two_factor_enabled: bool = Field(default=True, description="Whether 2FA is available for users to enable")
    session_timeout_minutes: int = Field(default=480, ge=0, le=10080, description="Session timeout in minutes (0 for no timeout, max 7 days)")
    max_concurrent_sessions: int = Field(default=5, ge=0, le=100, description="Maximum concurrent sessions per user (0 for unlimited)")
    ip_whitelist_enabled: bool = Field(default=False, description="Whether IP whitelist restrictions are enforced")
    ip_whitelist_strict: bool = Field(default=False, description="Block all access when no whitelist is configured")
    password_min_length: int = Field(default=8, ge=8, le=128, description="Minimum password length in characters")
    password_require_uppercase: bool = Field(default=True, description="Whether passwords must contain uppercase letters")
    password_require_lowercase: bool = Field(default=True, description="Whether passwords must contain lowercase letters")
    password_require_numbers: bool = Field(default=True, description="Whether passwords must contain numbers")
    password_require_special: bool = Field(default=False, description="Whether passwords must contain special characters")
    password_expiry_days: int = Field(default=0, ge=0, le=365, description="Password expiry in days (0 for no expiry)")
    sso_required: bool = Field(default=False, description="Whether SSO is mandatory for authentication")
    sso_only: bool = Field(default=False, description="Whether only SSO authentication is allowed")
    security_alerts_enabled: bool = Field(default=True, description="Whether automatic security alerts are enabled")
    failed_login_threshold: int = Field(default=5, ge=0, le=100, description="Number of failed logins before alert (0 to disable)")


# IP Whitelist Models

class IPWhitelistItem(BaseModel):
    """Single IP whitelist entry."""

    id: str = Field(..., description="IP whitelist entry ID")
    organization_id: Optional[str] = Field(None, description="Organization ID (null for system-wide whitelist)")
    name: str = Field(..., description="Friendly name for this IP range")
    description: Optional[str] = Field(None, description="Optional description with additional context")
    cidr_notation: Optional[str] = Field(None, description="IP range in CIDR notation (e.g., '192.168.1.0/24')")
    start_ip: Optional[str] = Field(None, description="Starting IP address")
    end_ip: Optional[str] = Field(None, description="Ending IP address")
    is_active: bool = Field(..., description="Whether this IP range is currently enforced")
    created_by: Optional[str] = Field(None, description="User ID who created this whitelist entry")
    created_at: str = Field(..., description="When the whitelist entry was created")
    updated_at: str = Field(..., description="When the whitelist entry was last updated")


class IPWhitelistResponse(BaseModel):
    """Response model for IP whitelist list."""

    entries: List[IPWhitelistItem] = Field(..., description="List of IP whitelist entries")
    total_count: int = Field(..., description="Total number of entries matching the filters")


class IPWhitelistCreate(BaseModel):
    """Request model for creating IP whitelist entry."""

    organization_id: Optional[str] = Field(None, description="Organization ID (omit for system-wide)")
    name: str = Field(..., min_length=1, max_length=255, description="Friendly name for this IP range")
    description: Optional[str] = Field(None, description="Optional description with additional context")
    cidr_notation: Optional[str] = Field(None, max_length=50, description="IP range in CIDR notation (e.g., '192.168.1.0/24')")
    start_ip: Optional[str] = Field(None, max_length=45, description="Starting IP address")
    end_ip: Optional[str] = Field(None, max_length=45, description="Ending IP address")
    is_active: bool = Field(default=True, description="Whether this IP range is currently enforced")


class IPWhitelistUpdate(BaseModel):
    """Request model for updating IP whitelist entry."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Friendly name for this IP range")
    description: Optional[str] = Field(None, description="Optional description with additional context")
    cidr_notation: Optional[str] = Field(None, max_length=50, description="IP range in CIDR notation")
    start_ip: Optional[str] = Field(None, max_length=45, description="Starting IP address")
    end_ip: Optional[str] = Field(None, max_length=45, description="Ending IP address")
    is_active: Optional[bool] = Field(None, description="Whether this IP range is currently enforced")


@router.get(
    "/config",
    response_model=SecurityConfigResponse,
    tags=["Security Config"],
)
async def get_security_config(
    organization_id: Optional[str] = Query(None, description="Organization ID (omit for system default)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get security configuration.

    This endpoint retrieves security configuration for an organization or the system default.
    If an organization_id is provided and no config exists for that organization,
    the system default configuration is returned.

    Args:
        organization_id: Optional organization ID to get config for (omit for system default)
        db: Database session

    Returns:
        JSON response with security configuration

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/security/config")
        >>> response.json()
        {
            "id": "config-1",
            "organization_id": null,
            "two_factor_required": false,
            "two_factor_enabled": true,
            "session_timeout_minutes": 480,
            "max_concurrent_sessions": 5,
            "ip_whitelist_enabled": false,
            "ip_whitelist_strict": false,
            "password_min_length": 8,
            "password_require_uppercase": true,
            "password_require_lowercase": true,
            "password_require_numbers": true,
            "password_require_special": false,
            "password_expiry_days": 0,
            "sso_required": false,
            "sso_only": false,
            "security_alerts_enabled": true,
            "failed_login_threshold": 5,
            "created_at": "2026-01-31T10:30:00Z",
            "updated_at": "2026-01-31T10:30:00Z"
        }
    """
    try:
        logger.info(f"Fetching security config - organization_id: {organization_id}")

        # If organization_id is provided, try to get org-specific config
        config = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = select(SecurityConfig).where(SecurityConfig.organization_id == org_uuid)
                result = await db.execute(query)
                config = result.scalars().first()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        # If no org-specific config found, get system default
        if config is None:
            query = select(SecurityConfig).where(SecurityConfig.organization_id.is_(None))
            result = await db.execute(query)
            config = result.scalars().first()

        # If no system default exists, return error
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No security configuration found. Please create a system default configuration.",
            )

        response_data = {
            "id": str(config.id),
            "organization_id": str(config.organization_id) if config.organization_id else None,
            "two_factor_required": config.two_factor_required,
            "two_factor_enabled": config.two_factor_enabled,
            "session_timeout_minutes": config.session_timeout_minutes,
            "max_concurrent_sessions": config.max_concurrent_sessions,
            "ip_whitelist_enabled": config.ip_whitelist_enabled,
            "ip_whitelist_strict": config.ip_whitelist_strict,
            "password_min_length": config.password_min_length,
            "password_require_uppercase": config.password_require_uppercase,
            "password_require_lowercase": config.password_require_lowercase,
            "password_require_numbers": config.password_require_numbers,
            "password_require_special": config.password_require_special,
            "password_expiry_days": config.password_expiry_days,
            "sso_required": config.sso_required,
            "sso_only": config.sso_only,
            "security_alerts_enabled": config.security_alerts_enabled,
            "failed_login_threshold": config.failed_login_threshold,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }

        logger.info(f"Retrieved security config for {organization_id or 'system default'}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving security config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security config: {str(e)}",
        ) from e


@router.put(
    "/config",
    response_model=SecurityConfigResponse,
    tags=["Security Config"],
)
async def update_security_config(
    organization_id: Optional[str] = Query(None, description="Organization ID (omit for system default)"),
    config_update: SecurityConfigUpdate = SecurityConfigUpdate(),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update security configuration.

    This endpoint updates security configuration for an organization or the system default.
    If an organization_id is provided and no config exists for that organization,
    a new configuration is created based on the system default.

    Args:
        organization_id: Optional organization ID to update config for (omit for system default)
        config_update: Security configuration fields to update
        db: Database session

    Returns:
        JSON response with updated security configuration

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(500): If data update fails

    Examples:
        >>> import requests
        >>> data = {"two_factor_required": True, "session_timeout_minutes": 240}
        >>> response = requests.put("http://localhost:8000/api/security/config", json=data)
        >>> response.json()
        {
            "id": "config-1",
            "organization_id": null,
            "two_factor_required": true,
            "session_timeout_minutes": 240,
            ...
        }
    """
    try:
        logger.info(f"Updating security config - organization_id: {organization_id}")

        # Find existing config
        config = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = select(SecurityConfig).where(SecurityConfig.organization_id == org_uuid)
                result = await db.execute(query)
                config = result.scalars().first()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        # If no org-specific config, get or create system default
        if config is None:
            query = select(SecurityConfig).where(SecurityConfig.organization_id.is_(None))
            result = await db.execute(query)
            config = result.scalars().first()

            # Create system default if it doesn't exist
            if config is None:
                config = SecurityConfig()
                db.add(config)
                await db.flush()

        # Update fields from request
        update_data = config_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        await db.commit()
        await db.refresh(config)

        response_data = {
            "id": str(config.id),
            "organization_id": str(config.organization_id) if config.organization_id else None,
            "two_factor_required": config.two_factor_required,
            "two_factor_enabled": config.two_factor_enabled,
            "session_timeout_minutes": config.session_timeout_minutes,
            "max_concurrent_sessions": config.max_concurrent_sessions,
            "ip_whitelist_enabled": config.ip_whitelist_enabled,
            "ip_whitelist_strict": config.ip_whitelist_strict,
            "password_min_length": config.password_min_length,
            "password_require_uppercase": config.password_require_uppercase,
            "password_require_lowercase": config.password_require_lowercase,
            "password_require_numbers": config.password_require_numbers,
            "password_require_special": config.password_require_special,
            "password_expiry_days": config.password_expiry_days,
            "sso_required": config.sso_required,
            "sso_only": config.sso_only,
            "security_alerts_enabled": config.security_alerts_enabled,
            "failed_login_threshold": config.failed_login_threshold,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }

        logger.info(f"Updated security config for {organization_id or 'system default'}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating security config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update security config: {str(e)}",
        ) from e


@router.post(
    "/config",
    response_model=SecurityConfigResponse,
    tags=["Security Config"],
)
async def create_security_config(
    config_create: SecurityConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create security configuration for an organization.

    This endpoint creates a new security configuration for a specific organization.
    Only organization-specific configs can be created through this endpoint.
    System default config is auto-created on first access.

    Args:
        config_create: Security configuration to create
        db: Database session

    Returns:
        JSON response with created security configuration

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(409): If config already exists for this organization
        HTTPException(500): If creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org-123",
        ...     "two_factor_required": True,
        ...     "session_timeout_minutes": 240
        ... }
        >>> response = requests.post("http://localhost:8000/api/security/config", json=data)
        >>> response.json()
        {
            "id": "config-2",
            "organization_id": "org-123",
            "two_factor_required": true,
            "session_timeout_minutes": 240,
            ...
        }
    """
    try:
        logger.info(f"Creating security config for organization: {config_create.organization_id}")

        # Validate organization_id format
        try:
            org_uuid = UUID(config_create.organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid organization_id format: {config_create.organization_id}",
            )

        # Check if config already exists for this organization
        existing_query = select(SecurityConfig).where(SecurityConfig.organization_id == org_uuid)
        existing_result = await db.execute(existing_query)
        existing_config = existing_result.scalars().first()

        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Security configuration already exists for organization {config_create.organization_id}",
            )

        # Create new config
        config = SecurityConfig(
            organization_id=org_uuid,
            two_factor_required=config_create.two_factor_required,
            two_factor_enabled=config_create.two_factor_enabled,
            session_timeout_minutes=config_create.session_timeout_minutes,
            max_concurrent_sessions=config_create.max_concurrent_sessions,
            ip_whitelist_enabled=config_create.ip_whitelist_enabled,
            ip_whitelist_strict=config_create.ip_whitelist_strict,
            password_min_length=config_create.password_min_length,
            password_require_uppercase=config_create.password_require_uppercase,
            password_require_lowercase=config_create.password_require_lowercase,
            password_require_numbers=config_create.password_require_numbers,
            password_require_special=config_create.password_require_special,
            password_expiry_days=config_create.password_expiry_days,
            sso_required=config_create.sso_required,
            sso_only=config_create.sso_only,
            security_alerts_enabled=config_create.security_alerts_enabled,
            failed_login_threshold=config_create.failed_login_threshold,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        response_data = {
            "id": str(config.id),
            "organization_id": str(config.organization_id) if config.organization_id else None,
            "two_factor_required": config.two_factor_required,
            "two_factor_enabled": config.two_factor_enabled,
            "session_timeout_minutes": config.session_timeout_minutes,
            "max_concurrent_sessions": config.max_concurrent_sessions,
            "ip_whitelist_enabled": config.ip_whitelist_enabled,
            "ip_whitelist_strict": config.ip_whitelist_strict,
            "password_min_length": config.password_min_length,
            "password_require_uppercase": config.password_require_uppercase,
            "password_require_lowercase": config.password_require_lowercase,
            "password_require_numbers": config.password_require_numbers,
            "password_require_special": config.password_require_special,
            "password_expiry_days": config.password_expiry_days,
            "sso_required": config.sso_required,
            "sso_only": config.sso_only,
            "security_alerts_enabled": config.security_alerts_enabled,
            "failed_login_threshold": config.failed_login_threshold,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }

        logger.info(f"Created security config for organization: {config_create.organization_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating security config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create security config: {str(e)}",
        ) from e


# IP Whitelist Endpoints


@router.get(
    "/ip-whitelist",
    response_model=IPWhitelistResponse,
    tags=["IP Whitelist"],
)
async def get_ip_whitelist(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get IP whitelist entries with filtering options.

    This endpoint retrieves IP whitelist entries for organizations or system-wide.
    IP whitelist entries enable organizations to restrict access to approved IP addresses or ranges.

    Entries are returned in reverse chronological order (newest first).

    Args:
        organization_id: Optional filter for organization ID
        is_active: Optional filter for active status
        limit: Maximum number of entries to return (default: 100, max: 1000)
        offset: Number of entries to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of IP whitelist entries and total count

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/security/ip-whitelist?limit=10")
        >>> response.json()
        {
            "entries": [
                {
                    "id": "whitelist-1",
                    "organization_id": "org-123",
                    "name": "Office Network",
                    "description": "Main office IP range",
                    "cidr_notation": "192.168.1.0/24",
                    "start_ip": null,
                    "end_ip": null,
                    "is_active": true,
                    "created_by": "user-1",
                    "created_at": "2026-01-31T10:30:00Z",
                    "updated_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching IP whitelist entries - organization_id: {organization_id}, "
            f"is_active: {is_active}"
        )

        # Build base query
        query = select(IPWhitelist)

        # Apply filters
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.where(IPWhitelist.organization_id == org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        if is_active is not None:
            query = query.where(IPWhitelist.is_active == is_active)

        # Order by created_at descending (newest first) and apply pagination
        query = query.order_by(IPWhitelist.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        whitelist_entries = result.scalars().all()

        # Build response data
        entries_data = []
        for entry in whitelist_entries:
            entries_data.append({
                "id": str(entry.id),
                "organization_id": str(entry.organization_id) if entry.organization_id else None,
                "name": entry.name,
                "description": entry.description,
                "cidr_notation": entry.cidr_notation,
                "start_ip": entry.start_ip,
                "end_ip": entry.end_ip,
                "is_active": entry.is_active,
                "created_by": str(entry.created_by) if entry.created_by else None,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
            })

        response_data = {
            "entries": entries_data,
            "total_count": len(entries_data),
        }

        logger.info(f"Retrieved {len(entries_data)} IP whitelist entries")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving IP whitelist entries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve IP whitelist entries: {str(e)}",
        ) from e


@router.post(
    "/ip-whitelist",
    response_model=IPWhitelistItem,
    tags=["IP Whitelist"],
)
async def create_ip_whitelist_entry(
    entry_create: IPWhitelistCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create IP whitelist entry.

    This endpoint creates a new IP whitelist entry for an organization or system-wide.
    IP whitelist entries enable organizations to restrict access to approved IP addresses or ranges.

    Args:
        entry_create: IP whitelist entry to create
        db: Database session

    Returns:
        JSON response with created IP whitelist entry

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(400): If neither cidr_notation nor start_ip/end_ip are provided
        HTTPException(500): If creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org-123",
        ...     "name": "Office Network",
        ...     "description": "Main office IP range",
        ...     "cidr_notation": "192.168.1.0/24",
        ...     "is_active": True
        ... }
        >>> response = requests.post("http://localhost:8000/api/security/ip-whitelist", json=data)
        >>> response.json()
        {
            "id": "whitelist-1",
            "organization_id": "org-123",
            "name": "Office Network",
            "description": "Main office IP range",
            "cidr_notation": "192.168.1.0/24",
            "start_ip": null,
            "end_ip": null,
            "is_active": true,
            "created_by": null,
            "created_at": "2026-01-31T10:30:00Z",
            "updated_at": "2026-01-31T10:30:00Z"
        }
    """
    try:
        logger.info(f"Creating IP whitelist entry: {entry_create.name}")

        # Validate organization_id format if provided
        org_uuid = None
        if entry_create.organization_id:
            try:
                org_uuid = UUID(entry_create.organization_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {entry_create.organization_id}",
                )

        # Validate that either cidr_notation or start_ip/end_ip are provided
        if not entry_create.cidr_notation and not (entry_create.start_ip and entry_create.end_ip):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either cidr_notation or both start_ip and end_ip must be provided",
            )

        # Create new entry
        entry = IPWhitelist(
            organization_id=org_uuid,
            name=entry_create.name,
            description=entry_create.description,
            cidr_notation=entry_create.cidr_notation,
            start_ip=entry_create.start_ip,
            end_ip=entry_create.end_ip,
            is_active=entry_create.is_active,
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        response_data = {
            "id": str(entry.id),
            "organization_id": str(entry.organization_id) if entry.organization_id else None,
            "name": entry.name,
            "description": entry.description,
            "cidr_notation": entry.cidr_notation,
            "start_ip": entry.start_ip,
            "end_ip": entry.end_ip,
            "is_active": entry.is_active,
            "created_by": str(entry.created_by) if entry.created_by else None,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }

        logger.info(f"Created IP whitelist entry: {entry.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating IP whitelist entry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create IP whitelist entry: {str(e)}",
        ) from e


@router.put(
    "/ip-whitelist/{entry_id}",
    response_model=IPWhitelistItem,
    tags=["IP Whitelist"],
)
async def update_ip_whitelist_entry(
    entry_id: str,
    entry_update: IPWhitelistUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update IP whitelist entry.

    This endpoint updates an existing IP whitelist entry.

    Args:
        entry_id: ID of the IP whitelist entry to update
        entry_update: IP whitelist entry fields to update
        db: Database session

    Returns:
        JSON response with updated IP whitelist entry

    Raises:
        HTTPException(400): If entry_id format is invalid
        HTTPException(404): If entry is not found
        HTTPException(400): If neither cidr_notation nor start_ip/end_ip are provided
        HTTPException(500): If update fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Office Network", "is_active": False}
        >>> response = requests.put("http://localhost:8000/api/security/ip-whitelist/whitelist-1", json=data)
        >>> response.json()
        {
            "id": "whitelist-1",
            "name": "Updated Office Network",
            "is_active": false,
            ...
        }
    """
    try:
        logger.info(f"Updating IP whitelist entry: {entry_id}")

        # Validate entry_id format
        try:
            entry_uuid = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entry_id format: {entry_id}",
            )

        # Find existing entry
        query = select(IPWhitelist).where(IPWhitelist.id == entry_uuid)
        result = await db.execute(query)
        entry = result.scalars().first()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IP whitelist entry not found: {entry_id}",
            )

        # Update fields from request
        update_data = entry_update.model_dump(exclude_unset=True)

        # Validate IP specification if being updated
        if "cidr_notation" in update_data or "start_ip" in update_data or "end_ip" in update_data:
            cidr = update_data.get("cidr_notation", entry.cidr_notation)
            start_ip = update_data.get("start_ip", entry.start_ip)
            end_ip = update_data.get("end_ip", entry.end_ip)

            if not cidr and not (start_ip and end_ip):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either cidr_notation or both start_ip and end_ip must be provided",
                )

        for field, value in update_data.items():
            setattr(entry, field, value)

        await db.commit()
        await db.refresh(entry)

        response_data = {
            "id": str(entry.id),
            "organization_id": str(entry.organization_id) if entry.organization_id else None,
            "name": entry.name,
            "description": entry.description,
            "cidr_notation": entry.cidr_notation,
            "start_ip": entry.start_ip,
            "end_ip": entry.end_ip,
            "is_active": entry.is_active,
            "created_by": str(entry.created_by) if entry.created_by else None,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }

        logger.info(f"Updated IP whitelist entry: {entry.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating IP whitelist entry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update IP whitelist entry: {str(e)}",
        ) from e


@router.delete(
    "/ip-whitelist/{entry_id}",
    tags=["IP Whitelist"],
)
async def delete_ip_whitelist_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete IP whitelist entry.

    This endpoint deletes an existing IP whitelist entry.

    Args:
        entry_id: ID of the IP whitelist entry to delete
        db: Database session

    Returns:
        JSON response with success message

    Raises:
        HTTPException(400): If entry_id format is invalid
        HTTPException(404): If entry is not found
        HTTPException(500): If deletion fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/security/ip-whitelist/whitelist-1")
        >>> response.json()
        {
            "message": "IP whitelist entry deleted successfully"
        }
    """
    try:
        logger.info(f"Deleting IP whitelist entry: {entry_id}")

        # Validate entry_id format
        try:
            entry_uuid = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entry_id format: {entry_id}",
            )

        # Find existing entry
        query = select(IPWhitelist).where(IPWhitelist.id == entry_uuid)
        result = await db.execute(query)
        entry = result.scalars().first()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IP whitelist entry not found: {entry_id}",
            )

        # Delete entry
        await db.delete(entry)
        await db.commit()

        logger.info(f"Deleted IP whitelist entry: {entry_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "IP whitelist entry deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting IP whitelist entry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete IP whitelist entry: {str(e)}",
        ) from e
