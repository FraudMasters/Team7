"""
OAuth 2.0 endpoints for calendar integrations.

This module provides endpoints for:
- OAuth 2.0 authentication with Google Calendar
- OAuth 2.0 authentication with Outlook Calendar
- Token exchange and storage
- State management for CSRF protection

Supports seamless integration with external calendar providers for
interview scheduling and availability management.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.calendar_connection import CalendarConnection, CalendarProvider, ConnectionStatus
from models.recruiter import Recruiter
from utils.redis_client import cache_set, cache_get, cache_delete

logger = logging.getLogger(__name__)

router = APIRouter()


# OAuth endpoints for Google Calendar
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# OAuth endpoints for Outlook Calendar
OUTLOOK_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
OUTLOOK_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
OUTLOOK_SCOPES = [
    "https://graph.microsoft.com/Calendars.ReadWrite",
    "https://graph.microsoft.com/User.Read",
]


# Request/Response Models
class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback processing."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="State parameter for CSRF protection")
    recruiter_id: str = Field(..., description="ID of the recruiter connecting calendar")


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback processing."""

    success: bool = Field(..., description="Whether the callback was processed successfully")
    message: str = Field(..., description="Status message")
    connection_id: Optional[str] = Field(None, description="Calendar connection ID (if successful)")
    provider: str = Field(..., description="Calendar provider (google or outlook)")


def _generate_state() -> str:
    """
    Generate a cryptographically secure random state parameter.

    State parameters are used in OAuth 2.0 to prevent CSRF attacks.

    Returns:
        A URL-safe random string suitable for use as OAuth state
    """
    state = secrets.token_urlsafe(32)
    logger.debug("Generated OAuth state parameter")
    return state


def _build_google_auth_url(state: str, redirect_uri: str) -> str:
    """
    Build Google OAuth authorization URL.

    Args:
        state: State parameter for CSRF protection
        redirect_uri: OAuth redirect URI

    Returns:
        Complete Google authorization URL
    """
    params = {
        "client_id": "YOUR_GOOGLE_CLIENT_ID",  # TODO: Replace with settings value
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _build_outlook_auth_url(state: str, redirect_uri: str) -> str:
    """
    Build Outlook/Microsoft OAuth authorization URL.

    Args:
        state: State parameter for CSRF protection
        redirect_uri: OAuth redirect URI

    Returns:
        Complete Outlook authorization URL
    """
    params = {
        "client_id": "YOUR_OUTLOOK_CLIENT_ID",  # TODO: Replace with settings value
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(OUTLOOK_SCOPES),
        "state": state,
        "response_mode": "query",
    }
    return f"{OUTLOOK_AUTH_URL}?{urlencode(params)}"


async def _exchange_google_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange Google authorization code for access token.

    Args:
        code: Authorization code from Google
        redirect_uri: OAuth redirect URI (must match authorization request)

    Returns:
        Dictionary containing access_token, refresh_token, expires_in

    Raises:
        HTTPException: If token exchange fails
    """
    data = {
        "code": code,
        "client_id": "YOUR_GOOGLE_CLIENT_ID",  # TODO: Replace with settings value
        "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",  # TODO: Replace with settings value
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    logger.info("Exchanging Google authorization code for access token")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            token_data = response.json()

            if "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Token response missing access_token",
                )

            logger.info("Successfully exchanged Google authorization code for access token")
            return token_data

    except httpx.HTTPStatusError as e:
        error_response = e.response.text
        logger.error(f"Google token exchange failed: {error_response}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange authorization code: {error_response}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during Google token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during token exchange: {str(e)}",
        ) from e


async def _exchange_outlook_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange Outlook authorization code for access token.

    Args:
        code: Authorization code from Outlook
        redirect_uri: OAuth redirect URI (must match authorization request)

    Returns:
        Dictionary containing access_token, refresh_token, expires_in

    Raises:
        HTTPException: If token exchange fails
    """
    data = {
        "code": code,
        "client_id": "YOUR_OUTLOOK_CLIENT_ID",  # TODO: Replace with settings value
        "client_secret": "YOUR_OUTLOOK_CLIENT_SECRET",  # TODO: Replace with settings value
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    logger.info("Exchanging Outlook authorization code for access token")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OUTLOOK_TOKEN_URL,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            token_data = response.json()

            if "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Token response missing access_token",
                )

            logger.info("Successfully exchanged Outlook authorization code for access token")
            return token_data

    except httpx.HTTPStatusError as e:
        error_response = e.response.text
        logger.error(f"Outlook token exchange failed: {error_response}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange authorization code: {error_response}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during Outlook token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during token exchange: {str(e)}",
        ) from e


@router.get(
    "/google/authorize",
    response_class=RedirectResponse,
    tags=["OAuth", "Calendar"],
)
async def google_authorize(
    request: Request,
    recruiter_id: str = Query(..., description="ID of the recruiter connecting calendar"),
) -> RedirectResponse:
    """
    Initiate Google Calendar OAuth 2.0 authorization flow.

    This endpoint generates a Google authorization URL and redirects the user
    to Google's consent screen to grant calendar access permissions.

    Args:
        request: FastAPI request object
        recruiter_id: ID of the recruiter connecting their calendar

    Returns:
        Redirect response to Google authorization URL

    Raises:
        HTTPException(400): If recruiter_id is invalid
        HTTPException(404): If recruiter not found
        HTTPException(500): If OAuth URL generation fails

    Examples:
        >>> # User clicks "Connect Google Calendar" button
        >>> # Frontend redirects to:
        >>> # GET /api/oauth/google/authorize?recruiter_id=uuid-here
        >>> # User is redirected to Google consent screen
        >>> # After authorization, Google redirects back to callback URL
    """
    try:
        logger.info(f"Initiating Google Calendar OAuth for recruiter {recruiter_id}")

        # Generate state for CSRF protection
        state = _generate_state()

        # Store state in Redis with recruiter_id for verification
        state_key = f"oauth_state:{state}"
        await cache_set(
            key=state_key,
            value={"recruiter_id": recruiter_id, "provider": "google"},
            ttl_seconds=600,  # 10 minutes
        )

        # Build redirect URI (using request to get base URL)
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/oauth/google/callback"

        # Build authorization URL
        auth_url = _build_google_auth_url(state, redirect_uri)

        logger.info(f"Redirecting to Google OAuth authorization URL for recruiter {recruiter_id}")

        # Return 307 redirect to Google authorization page
        return RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Google Calendar authorization: {str(e)}",
        ) from e


@router.get(
    "/outlook/authorize",
    response_class=RedirectResponse,
    tags=["OAuth", "Calendar"],
)
async def outlook_authorize(
    request: Request,
    recruiter_id: str = Query(..., description="ID of the recruiter connecting calendar"),
) -> RedirectResponse:
    """
    Initiate Outlook Calendar OAuth 2.0 authorization flow.

    This endpoint generates an Outlook authorization URL and redirects the user
    to Microsoft's consent screen to grant calendar access permissions.

    Args:
        request: FastAPI request object
        recruiter_id: ID of the recruiter connecting their calendar

    Returns:
        Redirect response to Outlook authorization URL

    Raises:
        HTTPException(400): If recruiter_id is invalid
        HTTPException(404): If recruiter not found
        HTTPException(500): If OAuth URL generation fails

    Examples:
        >>> # User clicks "Connect Outlook Calendar" button
        >>> # Frontend redirects to:
        >>> # GET /api/oauth/outlook/authorize?recruiter_id=uuid-here
        >>> # User is redirected to Microsoft consent screen
        >>> # After authorization, Microsoft redirects back to callback URL
    """
    try:
        logger.info(f"Initiating Outlook Calendar OAuth for recruiter {recruiter_id}")

        # Generate state for CSRF protection
        state = _generate_state()

        # Store state in Redis with recruiter_id for verification
        state_key = f"oauth_state:{state}"
        await cache_set(
            key=state_key,
            value={"recruiter_id": recruiter_id, "provider": "outlook"},
            ttl_seconds=600,  # 10 minutes
        )

        # Build redirect URI (using request to get base URL)
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/oauth/outlook/callback"

        # Build authorization URL
        auth_url = _build_outlook_auth_url(state, redirect_uri)

        logger.info(f"Redirecting to Outlook OAuth authorization URL for recruiter {recruiter_id}")

        # Return 307 redirect to Outlook authorization page
        return RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating Outlook OAuth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Outlook Calendar authorization: {str(e)}",
        ) from e


@router.get(
    "/google/callback",
    tags=["OAuth", "Calendar"],
)
async def google_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Handle Google OAuth 2.0 callback and create calendar connection.

    This endpoint is called by Google after the user grants permission.
    It exchanges the authorization code for access tokens and creates
    a calendar connection record.

    Args:
        request: FastAPI request object
        code: Authorization code from Google
        state: State parameter for CSRF verification
        db: Database session

    Returns:
        JSON response with connection status

    Raises:
        HTTPException(400): If state verification fails or code is invalid
        HTTPException(500): If token exchange or database operation fails
    """
    try:
        logger.info("Processing Google OAuth callback")

        # Verify state to prevent CSRF attacks
        state_key = f"oauth_state:{state}"
        state_data = await cache_get(state_key)
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )
        # Delete state to prevent replay attacks
        await cache_delete(state_key)

        recruiter_id = state_data.get("recruiter_id")
        if not recruiter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing recruiter_id in state data",
            )

        # Build redirect URI for token exchange
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/oauth/google/callback"

        # Exchange code for tokens
        token_data = await _exchange_google_code_for_token(code, redirect_uri)

        # Calculate token expiration
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Get calendar email (would need to call Google API to get user info)
        # For now, using a placeholder - this should be implemented in subtask-1-2
        calendar_email = "user@gmail.com"  # TODO: Fetch from Google API

        # Create or update calendar connection
        from api.calendar import create_calendar_connection
        from api.calendar import CalendarConnectionCreate

        connection_create = CalendarConnectionCreate(
            recruiter_id=recruiter_id,
            provider="google",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
        )

        # Call the calendar API to create the connection
        connection_response = await create_calendar_connection(request, connection_create, db)

        logger.info(f"Google Calendar connection created for recruiter {recruiter_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Google Calendar connected successfully",
                "provider": "google",
                "connection_id": connection_response.body.get("id") if hasattr(connection_response, "body") else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Google OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Google Calendar callback: {str(e)}",
        ) from e


@router.get(
    "/outlook/callback",
    tags=["OAuth", "Calendar"],
)
async def outlook_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Outlook"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Handle Outlook OAuth 2.0 callback and create calendar connection.

    This endpoint is called by Microsoft after the user grants permission.
    It exchanges the authorization code for access tokens and creates
    a calendar connection record.

    Args:
        request: FastAPI request object
        code: Authorization code from Outlook
        state: State parameter for CSRF verification
        db: Database session

    Returns:
        JSON response with connection status

    Raises:
        HTTPException(400): If state verification fails or code is invalid
        HTTPException(500): If token exchange or database operation fails
    """
    try:
        logger.info("Processing Outlook OAuth callback")

        # Verify state to prevent CSRF attacks
        state_key = f"oauth_state:{state}"
        state_data = await cache_get(state_key)
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )
        # Delete state to prevent replay attacks
        await cache_delete(state_key)

        recruiter_id = state_data.get("recruiter_id")
        if not recruiter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing recruiter_id in state data",
            )

        # Build redirect URI for token exchange
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/oauth/outlook/callback"

        # Exchange code for tokens
        token_data = await _exchange_outlook_code_for_token(code, redirect_uri)

        # Calculate token expiration
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Get calendar email (would need to call Microsoft Graph API to get user info)
        # For now, using a placeholder - this should be implemented in subtask-1-2
        calendar_email = "user@outlook.com"  # TODO: Fetch from Microsoft Graph API

        # Create or update calendar connection
        from api.calendar import create_calendar_connection
        from api.calendar import CalendarConnectionCreate

        connection_create = CalendarConnectionCreate(
            recruiter_id=recruiter_id,
            provider="outlook",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            token_expires_at=token_expires_at,
            calendar_email=calendar_email,
        )

        # Call the calendar API to create the connection
        connection_response = await create_calendar_connection(request, connection_create, db)

        logger.info(f"Outlook Calendar connection created for recruiter {recruiter_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Outlook Calendar connected successfully",
                "provider": "outlook",
                "connection_id": connection_response.body.get("id") if hasattr(connection_response, "body") else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Outlook OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Outlook Calendar callback: {str(e)}",
        ) from e
