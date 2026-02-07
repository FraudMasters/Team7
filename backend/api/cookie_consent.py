"""
Cookie consent management endpoints.

This module provides endpoints for managing user cookie consent preferences,
including consent for analytics and marketing cookies.
"""
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for cookie consent (will be replaced with database in future)
# For now, this is a simple global state that can be extended to per-user preferences
_current_consent: Dict[str, bool] = {
    "analytics": False,
    "marketing": False,
}


class CookieConsentResponse(BaseModel):
    """Response model for cookie consent endpoint."""

    analytics: bool = Field(..., description="Consent for analytics cookies")
    marketing: bool = Field(..., description="Consent for marketing cookies")


class CookieConsentUpdate(BaseModel):
    """Request model for updating cookie consent."""

    analytics: bool = Field(..., description="Consent for analytics cookies")
    marketing: bool = Field(..., description="Consent for marketing cookies")


def validate_consent(analytics: bool, marketing: bool) -> None:
    """
    Validate that the consent values are proper booleans.

    Args:
        analytics: Analytics cookie consent value
        marketing: Marketing cookie consent value

    Raises:
        HTTPException(422): If consent values are invalid
    """
    # Pydantic already handles type validation, but we can add additional
    # business logic validation here if needed in the future
    if not isinstance(analytics, bool) or not isinstance(marketing, bool):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consent values must be boolean (true or false)",
        )


@router.get(
    "/",
    response_model=CookieConsentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Cookie Consent"],
)
async def get_cookie_consent() -> JSONResponse:
    """
    Get the current cookie consent preferences.

    Returns the current consent status for analytics and marketing cookies.

    Returns:
        JSON response with current cookie consent preferences

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/cookie-consent/")
        >>> response.json()
        {
            "analytics": false,
            "marketing": false
        }
    """
    try:
        logger.info(f"Retrieving cookie consent: {_current_consent}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_current_consent,
        )

    except Exception as e:
        logger.error(f"Error retrieving cookie consent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cookie consent: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=CookieConsentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Cookie Consent"],
)
async def set_cookie_consent(request: CookieConsentUpdate) -> JSONResponse:
    """
    Set cookie consent preferences.

    Sets the consent preferences for analytics and marketing cookies.
    Both preferences must be provided in the request.

    Args:
        request: Request body containing the consent preferences

    Returns:
        JSON response with updated cookie consent preferences

    Raises:
        HTTPException(422): If consent values are invalid
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/cookie-consent/",
        ...     json={"analytics": True, "marketing": False}
        ... )
        >>> response.json()
        {
            "analytics": true,
            "marketing": false
        }
    """
    global _current_consent

    try:
        # Validate consent values
        validate_consent(request.analytics, request.marketing)

        logger.info(
            f"Updating cookie consent from {_current_consent} to "
            f"{{'analytics': {request.analytics}, 'marketing': {request.marketing}}}"
        )

        # Update the consent preferences
        _current_consent = {
            "analytics": request.analytics,
            "marketing": request.marketing,
        }

        logger.info(f"Cookie consent updated successfully: {_current_consent}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_current_consent,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error updating cookie consent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cookie consent: {str(e)}",
        ) from e
