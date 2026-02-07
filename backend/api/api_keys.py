"""
API key management endpoints.

This module provides endpoints for:
- Generating new API keys with configurable scopes and rate limits
- Listing all API keys with their metadata
- Revoking (deactivating) API keys
- Viewing API key details

API keys are used to authenticate and authorize access to the developer API,
with support for granular scopes and rate limiting.
"""
import hashlib
import logging
import secrets
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.api_key import APIKey, APIKeyScope

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class GenerateAPIKeyRequest(BaseModel):
    """Request model for generating a new API key."""

    name: str = Field(..., description="User-friendly name for the API key", min_length=1, max_length=255)
    scopes: List[str] = Field(
        ...,
        description="List of scopes/permissions for the API key",
        min_length=1,
    )
    rate_limit: Optional[Dict[str, int]] = Field(
        None,
        description="Optional rate limit configuration (requests_per_minute, requests_per_hour, requests_per_day)",
    )
    expires_at: Optional[str] = Field(
        None,
        description="Optional expiration timestamp (ISO 8601 format)",
    )

    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate that all scopes are valid APIKeyScope values."""
        valid_scopes = [scope.value for scope in APIKeyScope]
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}. Valid scopes are: {', '.join(valid_scopes)}")
        return v

    @validator("rate_limit")
    def validate_rate_limit(cls, v):
        """Validate rate limit configuration."""
        if v is not None:
            allowed_keys = {"requests_per_minute", "requests_per_hour", "requests_per_day"}
            invalid_keys = set(v.keys()) - allowed_keys
            if invalid_keys:
                raise ValueError(f"Invalid rate limit keys: {', '.join(invalid_keys)}. Allowed keys: {', '.join(allowed_keys)}")
            for key, value in v.items():
                if not isinstance(value, int) or value <= 0:
                    raise ValueError(f"Rate limit {key} must be a positive integer")
        return v


class GenerateAPIKeyResponse(BaseModel):
    """Response model for API key generation."""

    id: str = Field(..., description="API key UUID")
    key: str = Field(..., description="The generated API key (only shown once)")
    key_prefix: str = Field(..., description="First 8 characters of the key for identification")
    name: str = Field(..., description="User-friendly name")
    scopes: List[str] = Field(..., description="Assigned scopes")
    rate_limit: Dict[str, int] = Field(..., description="Rate limit configuration")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Warning message about saving the key")


class APIKeyListItem(BaseModel):
    """Response model for an API key in list view."""

    id: str = Field(..., description="API key UUID")
    key_prefix: str = Field(..., description="First 8 characters of the key")
    name: str = Field(..., description="User-friendly name")
    scopes: List[str] = Field(..., description="Assigned scopes")
    rate_limit: Dict[str, int] = Field(..., description="Rate limit configuration")
    is_active: bool = Field(..., description="Whether the key is active")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[str] = Field(None, description="Last usage timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class RevokeAPIKeyResponse(BaseModel):
    """Response model for API key revocation."""

    id: str = Field(..., description="API key UUID")
    key_prefix: str = Field(..., description="First 8 characters of the key")
    name: str = Field(..., description="User-friendly name")
    is_active: bool = Field(..., description="Status after revocation (should be false)")
    message: str = Field(..., description="Success message")


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        A 64-character hex string (32 bytes) for use as an API key.

    Example:
        >>> key = generate_api_key()
        >>> len(key)
        64
    """
    return secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The API key to hash

    Returns:
        The SHA-256 hash of the API key as a hex string

    Example:
        >>> key = "test_key_12345"
        >>> hashed = hash_api_key(key)
        >>> len(hashed)
        64
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post(
    "/generate",
    response_model=GenerateAPIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["API Keys"],
)
async def generate_api_key_endpoint(
    request: Request,
    key_data: GenerateAPIKeyRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate a new API key.

    Creates a new API key with the specified name, scopes, and rate limits.
    The actual API key is only returned once during creation, so make sure
    to save it securely.

    Rate limit defaults (if not specified):
    - requests_per_minute: 60
    - requests_per_hour: 1000
    - requests_per_day: 10000

    Args:
        request: FastAPI request object
        key_data: API key generation details (name, scopes, optional rate_limit, optional expires_at)
        db: Database session

    Returns:
        JSON response with the generated API key and metadata

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Production Integration Key",
        ...     "scopes": ["read:candidates", "read:vacancies", "write:webhooks"]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/api-keys/generate",
        ...     json=data
        ... )
        >>> result = response.json()
        >>> api_key = result["key"]  # Save this securely!
    """
    try:
        logger.info(f"Generating new API key: {key_data.name}")

        # Generate the API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = api_key[:8]

        # Set default rate limits if not provided
        rate_limit = key_data.rate_limit
        if rate_limit is None:
            rate_limit = {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
            }

        # Parse expiration date if provided
        expires_at = None
        if key_data.expires_at:
            from datetime import datetime
            try:
                expires_at = datetime.fromisoformat(key_data.expires_at.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid expires_at format: {key_data.expires_at}. Use ISO 8601 format.",
                ) from e

        # Create the API key record
        new_key = APIKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_data.name,
            scopes=key_data.scopes,
            rate_limit=rate_limit,
            expires_at=expires_at,
            is_active=True,
        )

        db.add(new_key)
        await db.commit()
        await db.refresh(new_key)

        logger.info(f"API key generated successfully: {new_key.id} (prefix: {key_prefix})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_key.id),
                "key": api_key,
                "key_prefix": key_prefix,
                "name": new_key.name,
                "scopes": new_key.scopes,
                "rate_limit": new_key.rate_limit,
                "expires_at": new_key.expires_at.isoformat() if new_key.expires_at else None,
                "created_at": new_key.created_at.isoformat() if new_key.created_at else None,
                "message": "IMPORTANT: Save this API key securely. It will not be shown again.",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating API key: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate API key: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=List[APIKeyListItem],
    tags=["API Keys"],
)
async def list_api_keys(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all API keys.

    Returns a paginated list of API keys with their metadata.
    The actual API keys are not included in the response (only the prefix).

    Args:
        request: FastAPI request object
        is_active: Optional filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of API keys

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all API keys
        >>> response = requests.get("http://localhost:8000/api/api-keys/")
        >>> # Get only active keys
        >>> response = requests.get("http://localhost:8000/api/api-keys/?is_active=true")
        >>> # Get paginated results
        >>> response = requests.get("http://localhost:8000/api/api-keys/?skip=0&limit=10")
        >>> keys = response.json()
    """
    try:
        logger.info(f"Fetching API keys - is_active: {is_active}, skip: {skip}, limit: {limit}")

        # Build query
        query = select(APIKey)

        # Apply filters
        if is_active is not None:
            query = query.where(APIKey.is_active == is_active)

        # Order by most recently created
        query = query.order_by(APIKey.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        api_keys = result.scalars().all()

        # Convert to response format
        keys_list = []
        for key in api_keys:
            keys_list.append({
                "id": str(key.id),
                "key_prefix": key.key_prefix,
                "name": key.name,
                "scopes": key.scopes,
                "rate_limit": key.rate_limit,
                "is_active": key.is_active,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "updated_at": key.updated_at.isoformat() if key.updated_at else None,
            })

        logger.info(f"Retrieved {len(keys_list)} API keys")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=keys_list,
        )

    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        ) from e


@router.get(
    "/{key_id}",
    response_model=APIKeyListItem,
    tags=["API Keys"],
)
async def get_api_key(
    request: Request,
    key_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific API key's details.

    Returns metadata for a specific API key by its UUID.
    The actual API key is not included in the response.

    Args:
        request: FastAPI request object
        key_id: API key UUID
        db: Database session

    Returns:
        JSON response with API key details

    Raises:
        HTTPException(400): If key_id is not a valid UUID
        HTTPException(404): If API key not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(f"http://localhost:8000/api/api-keys/{key_id}")
        >>> key_data = response.json()
    """
    try:
        logger.info(f"Fetching API key: {key_id}")

        # Parse key_id as UUID
        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid API key ID format: {key_id}",
            )

        # Get the API key
        query = select(APIKey).where(APIKey.id == key_uuid)
        result = await db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}",
            )

        key_data = {
            "id": str(api_key.id),
            "key_prefix": api_key.key_prefix,
            "name": api_key.name,
            "scopes": api_key.scopes,
            "rate_limit": api_key.rate_limit,
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
            "updated_at": api_key.updated_at.isoformat() if api_key.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=key_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key {key_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key: {str(e)}",
        ) from e


@router.post(
    "/{key_id}/revoke",
    response_model=RevokeAPIKeyResponse,
    tags=["API Keys"],
)
async def revoke_api_key(
    request: Request,
    key_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Revoke an API key.

    Deactivates an API key by setting is_active to false.
    The key can still be viewed but cannot be used for API authentication.

    Args:
        request: FastAPI request object
        key_id: API key UUID
        db: Database session

    Returns:
        JSON response with revoked API key details

    Raises:
        HTTPException(400): If key_id is not a valid UUID
        HTTPException(404): If API key not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(f"http://localhost:8000/api/api-keys/{key_id}/revoke")
        >>> result = response.json()
        >>> assert result["is_active"] == False
    """
    try:
        logger.info(f"Revoking API key: {key_id}")

        # Parse key_id as UUID
        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid API key ID format: {key_id}",
            )

        # Get the API key
        query = select(APIKey).where(APIKey.id == key_uuid)
        result = await db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}",
            )

        # Check if already revoked
        if not api_key.is_active:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": str(api_key.id),
                    "key_prefix": api_key.key_prefix,
                    "name": api_key.name,
                    "is_active": api_key.is_active,
                    "message": "API key is already revoked",
                },
            )

        # Revoke the key
        api_key.is_active = False
        await db.commit()
        await db.refresh(api_key)

        logger.info(f"API key revoked successfully: {key_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(api_key.id),
                "key_prefix": api_key.key_prefix,
                "name": api_key.name,
                "is_active": api_key.is_active,
                "message": "API key revoked successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key {key_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}",
        ) from e
