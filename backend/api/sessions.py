"""
Session endpoints for viewing and managing active user sessions.

This module provides endpoints for retrieving active sessions, revoking specific
sessions, and revoking all sessions for security purposes.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.session import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionItem(BaseModel):
    """Single session item."""

    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User who owns this session")
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    device_type: Optional[str] = Field(None, description="Device type: desktop, mobile, tablet, or unknown")
    user_agent: Optional[str] = Field(None, description="Full user agent string")
    ip_address: Optional[str] = Field(None, description="IP address where session was created")
    location: Optional[str] = Field(None, description="Location derived from IP")
    is_active: bool = Field(..., description="Whether the session is currently active")
    expires_at: Optional[str] = Field(None, description="Session expiration timestamp")
    last_activity_at: str = Field(..., description="Timestamp of last user activity")
    created_at: str = Field(..., description="When the session was created")
    is_current: bool = Field(False, description="Whether this is the current session")


class SessionsResponse(BaseModel):
    """Response model for sessions list."""

    sessions: List[SessionItem] = Field(..., description="List of active sessions")
    total_count: int = Field(..., description="Total number of sessions")


@router.get(
    "/",
    response_model=SessionsResponse,
    tags=["Sessions"],
)
async def get_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get active sessions with filtering options.

    This endpoint retrieves active user sessions across the system, including
    device information, IP addresses, and activity timestamps. Sessions are
    returned in reverse chronological order (most recently active first).

    **Note:** This endpoint requires authentication. In production, you should
    validate the JWT token and extract the user_id to only return sessions
    belonging to the authenticated user.

    Args:
        user_id: Optional filter for specific user (requires admin privileges in production)
        device_type: Optional filter for device type (desktop, mobile, tablet, unknown)
        is_active: Optional filter for active status (true for active, false for revoked)
        limit: Maximum number of sessions to return (default: 100, max: 1000)
        offset: Number of sessions to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of sessions and total count

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If trying to access other user's sessions without admin privileges
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/sessions/?limit=10",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "sessions": [
                {
                    "id": "session-1",
                    "user_id": "user-1",
                    "device_name": "Chrome on Windows",
                    "device_type": "desktop",
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.1",
                    "location": "San Francisco, CA",
                    "is_active": true,
                    "expires_at": "2026-02-01T10:30:00Z",
                    "last_activity_at": "2026-01-31T15:45:00Z",
                    "created_at": "2026-01-31T10:30:00Z",
                    "is_current": true
                }
            ],
            "total_count": 1
        }
    """
    try:
        # TODO: In production, extract user_id from JWT token
        # TODO: Add authorization check - users can only see their own sessions unless admin
        # TODO: Get current session token to mark is_current flag

        # For now, return 401 to indicate authentication is required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token.",
        )

        logger.info(
            f"Fetching sessions - user_id: {user_id}, device_type: {device_type}, "
            f"is_active: {is_active}"
        )

        # Build base query
        query = select(Session)

        # Apply filters
        if user_id:
            try:
                user_uuid = UUID(user_id)
                query = query.where(Session.user_id == user_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user_id format: {user_id}",
                )

        if device_type:
            valid_types = ["desktop", "mobile", "tablet", "unknown"]
            if device_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid device_type: {device_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(Session.device_type == device_type)

        if is_active is not None:
            query = query.where(Session.is_active == is_active)

        # Order by last_activity_at descending (most recent first) and apply pagination
        query = query.order_by(Session.last_activity_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        sessions = result.scalars().all()

        # Build response data
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                "id": str(session.id),
                "user_id": str(session.user_id),
                "device_name": session.device_name,
                "device_type": session.device_type,
                "user_agent": session.user_agent,
                "ip_address": session.ip_address,
                "location": session.location,
                "is_active": session.is_active,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "last_activity_at": session.last_activity_at.isoformat(),
                "created_at": session.created_at.isoformat(),
                "is_current": False,  # TODO: Compare with current session token
            })

        response_data = {
            "sessions": sessions_data,
            "total_count": len(sessions_data),
        }

        logger.info(f"Retrieved {len(sessions_data)} sessions")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        ) from e


class RevokeSessionResponse(BaseModel):
    """Response model for session revocation."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="ID of the revoked session")


@router.delete(
    "/{session_id}",
    response_model=RevokeSessionResponse,
    tags=["Sessions"],
)
async def revoke_session(
    session_id: str,
    reason: Optional[str] = Query(None, description="Reason for revocation (e.g., 'user_logout', 'security_reset')"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Revoke a specific session.

    This endpoint revokes a specific session by ID, effectively logging out
    the user from that device. The session is marked as inactive and a
    revocation timestamp is recorded.

    **Note:** This endpoint requires authentication. Users can only revoke
    their own sessions unless they have admin privileges.

    Args:
        session_id: ID of the session to revoke
        reason: Optional reason for revocation
        db: Database session

    Returns:
        JSON response with success message

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If trying to revoke another user's session without admin privileges
        HTTPException(404): If session not found
        HTTPException(400): If session is already revoked
        HTTPException(500): If revocation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/sessions/abc-123?reason=user_logout",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "message": "Session revoked successfully",
            "session_id": "abc-123"
        }
    """
    try:
        # TODO: In production, extract user_id from JWT token
        # TODO: Add authorization check - users can only revoke their own sessions unless admin

        # For now, return 401 to indicate authentication is required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token.",
        )

        logger.info(f"Revoking session: {session_id}, reason: {reason}")

        # Validate session_id format
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session_id format: {session_id}",
            )

        # Get the session
        query = select(Session).where(Session.id == session_uuid)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Check if session is already revoked
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already revoked: {session_id}",
            )

        # TODO: Check if session belongs to current user or user is admin

        # Revoke the session
        revoke_reason = reason or "user_logout"
        await db.execute(
            update(Session)
            .where(Session.id == session_uuid)
            .values(
                is_active=False,
                revoked_at=datetime.now(),
                revoke_reason=revoke_reason,
            )
        )
        await db.commit()

        logger.info(f"Successfully revoked session: {session_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Session revoked successfully",
                "session_id": session_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}",
        ) from e


class RevokeAllResponse(BaseModel):
    """Response model for revoking all sessions."""

    message: str = Field(..., description="Success message")
    revoked_count: int = Field(..., description="Number of sessions revoked")


@router.delete(
    "/revoke-all",
    response_model=RevokeAllResponse,
    tags=["Sessions"],
)
async def revoke_all_sessions(
    user_id: str = Query(..., description="User ID to revoke all sessions for"),
    exclude_current: bool = Query(True, description="Whether to exclude the current session from revocation"),
    reason: Optional[str] = Query("security_reset", description="Reason for revocation"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Revoke all sessions for a user.

    This endpoint revokes all active sessions for a specific user. This is useful
    for security purposes, such as when a user changes their password or suspects
    unauthorized access.

    By default, the current session (the one making the request) is excluded from
    revocation to avoid logging out the user who initiated the action.

    **Note:** This endpoint requires authentication. Users can only revoke their
    own sessions unless they have admin privileges.

    Args:
        user_id: User ID to revoke all sessions for
        exclude_current: Whether to exclude the current session (default: true)
        reason: Reason for revocation (default: "security_reset")
        db: Database session

    Returns:
        JSON response with success message and count of revoked sessions

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If trying to revoke another user's sessions without admin privileges
        HTTPException(400): If user_id format is invalid
        HTTPException(500): If revocation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/sessions/revoke-all?user_id=abc-123&reason=password_change",
        ...     headers={"Authorization": "Bearer <token>"}
        ... )
        >>> response.json()
        {
            "message": "All sessions revoked successfully",
            "revoked_count": 3
        }
    """
    try:
        # TODO: In production, extract user_id from JWT token
        # TODO: Add authorization check - users can only revoke their own sessions unless admin
        # TODO: Get current session token to exclude from revocation if exclude_current is True

        # For now, return 401 to indicate authentication is required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token.",
        )

        logger.info(
            f"Revoking all sessions for user: {user_id}, "
            f"exclude_current: {exclude_current}, reason: {reason}"
        )

        # Validate user_id format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}",
            )

        # TODO: Check if user_id matches current user or user is admin

        # Build query to revoke all active sessions for user
        query = (
            update(Session)
            .where(Session.user_id == user_uuid)
            .where(Session.is_active == True)
        )

        # TODO: If exclude_current is True, exclude current session token
        # if exclude_current:
        #     current_token = get_current_session_token()
        #     query = query.where(Session.token != current_token)

        # Get count before revocation
        count_query = select(Session).where(
            Session.user_id == user_uuid,
            Session.is_active == True,
        )
        # TODO: Apply exclude_current filter here too
        count_result = await db.execute(count_query)
        sessions_to_revoke = count_result.scalars().all()
        revoked_count = len(sessions_to_revoke)

        # Perform revocation
        revoke_reason = reason or "security_reset"
        query = query.values(
            is_active=False,
            revoked_at=datetime.now(),
            revoke_reason=revoke_reason,
        )

        await db.execute(query)
        await db.commit()

        logger.info(f"Successfully revoked {revoked_count} sessions for user: {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "All sessions revoked successfully",
                "revoked_count": revoked_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke all sessions: {str(e)}",
        ) from e
