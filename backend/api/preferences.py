"""
User preferences management endpoints.

This module provides endpoints for managing user preferences, including language
preference for UI localization.
"""
import logging
from typing import Dict, Literal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported languages
SupportedLanguage = Literal["en", "ru"]
DEFAULT_LANGUAGE: SupportedLanguage = "en"

# In-memory storage for language preference (will be replaced with database in future)
# For now, this is a simple global state that can be extended to per-user preferences
_current_language: SupportedLanguage = DEFAULT_LANGUAGE


class LanguagePreferenceResponse(BaseModel):
    """Response model for language preference endpoint."""

    language: SupportedLanguage = Field(..., description="Current language preference (en or ru)")


class LanguagePreferenceUpdate(BaseModel):
    """Request model for updating language preference."""

    language: SupportedLanguage = Field(..., description="Language preference to set (en or ru)")


def validate_language(language: str) -> SupportedLanguage:
    """
    Validate that the language is supported.

    Args:
        language: Language code to validate

    Raises:
        HTTPException: If language is not supported
    """
    if language not in ["en", "ru"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported language '{language}'. Supported languages: en, ru",
        )
    return language  # type: ignore


@router.get(
    "/language",
    response_model=LanguagePreferenceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def get_language_preference() -> JSONResponse:
    """
    Get the current language preference.

    Returns the currently selected language for the UI.
    Default is 'en' (English) if not previously set.

    Returns:
        JSON response with current language preference

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/preferences/language")
        >>> response.json()
        {
            "language": "en"
        }
    """
    try:
        logger.info(f"Retrieving language preference: {_current_language}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"language": _current_language},
        )

    except Exception as e:
        logger.error(f"Error retrieving language preference: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language preference: {str(e)}",
        ) from e


@router.put(
    "/language",
    response_model=LanguagePreferenceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def update_language_preference(request: LanguagePreferenceUpdate) -> JSONResponse:
    """
    Update the language preference.

    Sets the language preference for the UI. Supported languages are:
    - 'en' (English)
    - 'ru' (Russian)

    Args:
        request: Request body containing the language to set

    Returns:
        JSON response with updated language preference

    Raises:
        HTTPException(422): If language is not supported
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/preferences/language",
        ...     json={"language": "ru"}
        ... )
        >>> response.json()
        {
            "language": "ru"
        }
    """
    global _current_language

    try:
        # Validate language
        language = validate_language(request.language)

        logger.info(f"Updating language preference from {_current_language} to {language}")

        # Update the language preference
        _current_language = language

        logger.info(f"Language preference updated successfully: {_current_language}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"language": _current_language},
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error updating language preference: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update language preference: {str(e)}",
        ) from e
