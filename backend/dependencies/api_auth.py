"""
FastAPI dependencies for API key authentication and authorization.

This module provides dependency injection functions for FastAPI endpoints
to extract and validate API keys for developer API authentication.
It integrates with the APIKey model for key validation and scope checking.

Dependencies provided:
- get_api_key: Extract and return the validated API key from Authorization header
- require_scope: Check if the API key has required scope(s)
"""
import hashlib
import logging
from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.api_key import APIKey

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The API key to hash

    Returns:
        The SHA-256 hash of the API key as a hex string
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """
    Dependency to extract and validate an API key from the Authorization header.

    This function validates the API key from the Authorization header,
    retrieves the corresponding APIKey from the database, and returns it.
    It raises an HTTPException if the key is invalid, expired, or inactive.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session (injected by FastAPI)

    Returns:
        APIKey: The validated API key object

    Raises:
        HTTPException: If authentication fails (401 Unauthorized)
            - Missing or invalid API key
            - Expired API key
            - Inactive API key
            - API key not found

    Example:
        @router.get("/data")
        async def get_data(api_key: APIKey = Depends(get_api_key)):
            return {"key_prefix": api_key.key_prefix, "scopes": api_key.scopes}
    """
    # Check if credentials are provided
    if credentials is None:
        logger.warning("API key authentication attempt without credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key_value = credentials.credentials

    try:
        # Hash the provided API key
        key_hash = hash_api_key(api_key_value)

        # Look up the API key in the database
        result = await db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            logger.warning(f"API key not found: {api_key_value[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if the API key is valid (active and not expired)
        if not api_key.is_valid():
            if not api_key.is_active:
                logger.warning(f"Inactive API key used: {api_key.key_prefix}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key has been revoked",
                )
            else:
                logger.warning(f"Expired API key used: {api_key.key_prefix}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key has expired",
                )

        # Update last_used_at timestamp
        api_key.last_used_at = datetime.utcnow()
        await db.commit()

        logger.debug(f"API key authenticated successfully: {api_key.key_prefix}")
        return api_key

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error during API key authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_api_key_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[APIKey]:
    """
    Optional version of get_api_key that returns None instead of raising.

    This dependency attempts to extract and validate the API key but returns
    None if authentication fails instead of raising an exception. Useful for
    endpoints that have different behavior for authenticated vs anonymous access.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session (injected by FastAPI)

    Returns:
        APIKey or None: The validated API key object, or None if not authenticated

    Example:
        @router.get("/public-data")
        async def get_public_data(
            api_key: Optional[APIKey] = Depends(get_api_key_optional)
        ):
            if api_key:
                return {"data": "customized", "key_prefix": api_key.key_prefix}
            return {"data": "generic"}
    """
    # Check if credentials are provided
    if credentials is None:
        return None

    api_key_value = credentials.credentials

    try:
        # Hash the provided API key
        key_hash = hash_api_key(api_key_value)

        # Look up the API key in the database
        result = await db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        if api_key is None or not api_key.is_valid():
            return None

        # Update last_used_at timestamp
        api_key.last_used_at = datetime.utcnow()
        await db.commit()

        logger.debug(f"Optional API key authentication successful: {api_key.key_prefix}")
        return api_key

    except Exception as e:
        logger.debug(f"Optional API key authentication failed: {e}")
        return None


async def require_scope(
    *scope_names: str,
    api_key: APIKey = Depends(get_api_key),
) -> APIKey:
    """
    Dependency to require specific scope(s) for endpoint access.

    This function checks if the current API key has at least one of the
    required scopes. If the API key's scopes don't include any of the
    allowed scopes, it raises a 403 Forbidden exception.

    Args:
        *scope_names: Variable number of scope names to check (API key needs at least one)
        api_key: Authenticated API key (injected by FastAPI)

    Returns:
        APIKey: The authenticated API key object (if authorized)

    Raises:
        HTTPException: If authorization fails (403 Forbidden)
            - API key doesn't have any of the required scopes

    Example:
        # Require read:candidates scope
        @router.get("/candidates")
        async def list_candidates(
            api_key: APIKey = Depends(require_scope("read:candidates"))
        ):
            return {"candidates": [...]}

        # Require either read or write scope
        @router.get("/data")
        async def get_data(
            api_key: APIKey = Depends(
                require_scope("read:data", "write:data")
            )
        ):
            return {"data": [...]}
    """
    # Check if the API key has any of the required scopes
    has_required_scope = any(api_key.has_scope(scope) for scope in scope_names)

    if not has_required_scope:
        logger.warning(
            f"API key {api_key.key_prefix} attempted to access endpoint "
            f"requiring scopes {scope_names} but has {api_key.scopes}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key requires one of these scopes: {', '.join(scope_names)}",
        )

    logger.debug(f"API key {api_key.key_prefix} authorized with scopes {api_key.scopes}")
    return api_key


def create_scope_dependency(*scope_names: str):
    """
    Factory function to create a scope requirement dependency.

    This is a convenience function to create reusable scope dependencies
    without having to use functools.partial.

    Args:
        *scope_names: Variable number of scope names to require

    Returns:
        A FastAPI dependency function that checks for the required scopes

    Example:
        # Create a reusable dependency
        RequireReadCandidates = create_scope_dependency("read:candidates")

        @router.get("/candidates")
        async def list_candidates(
            api_key: APIKey = Depends(RequireReadCandidates)
        ):
            return {"candidates": [...]}
    """
    async def scope_checker(api_key: APIKey = Depends(get_api_key)) -> APIKey:
        return await require_scope(*scope_names, api_key=api_key)

    return scope_checker
