"""
User preferences management endpoints.

This module provides endpoints for managing user preferences, including:
- Profile information (name, email, role, avatar)
- Language preference for UI localization
- Dashboard configuration (layout, widgets, settings)
- Filter preferences for candidate searches (experience, languages, location, etc.)
- API keys management for external service integrations
"""
import logging
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user_preferences import UserPreferences

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported languages
SupportedLanguage = Literal["en", "ru"]
DEFAULT_LANGUAGE: SupportedLanguage = "en"

# Default preferences ID (single global preferences record for now)
DEFAULT_PREFERENCES_ID = 1


class LanguagePreferenceResponse(BaseModel):
    """Response model for language preference endpoint."""

    language: SupportedLanguage = Field(..., description="Current language preference (en or ru)")


class LanguagePreferenceUpdate(BaseModel):
    """Request model for updating language preference."""

    language: SupportedLanguage = Field(..., description="Language preference to set (en or ru)")


class UserProfileResponse(BaseModel):
    """Response model for user profile endpoint."""

    name: Optional[str] = Field(None, description="User's display name")
    email: Optional[str] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role (e.g., recruiter, hiring_manager)")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")


class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""

    name: Optional[str] = Field(None, description="User's display name", max_length=255)
    email: Optional[str] = Field(None, description="User's email address", max_length=255)
    role: Optional[str] = Field(None, description="User's role (e.g., recruiter, hiring_manager)", max_length=100)
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image", max_length=512)


class DashboardConfigResponse(BaseModel):
    """Response model for dashboard configuration endpoint."""

    layout: Optional[str] = Field(None, description="Dashboard layout type (e.g., grid, list)")
    widgets: Optional[Dict[str, Any]] = Field(None, description="Widget configuration and settings")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional dashboard settings")


class DashboardConfigUpdate(BaseModel):
    """Request model for updating dashboard configuration."""

    layout: Optional[str] = Field(None, description="Dashboard layout type (e.g., grid, list)")
    widgets: Optional[Dict[str, Any]] = Field(None, description="Widget configuration and settings")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional dashboard settings")


class FilterPreferencesResponse(BaseModel):
    """Response model for filter preferences endpoint."""

    default_filters: Dict[str, Any] = Field(..., description="Default filter settings for searches")


class FilterPreferencesUpdate(BaseModel):
    """Request model for updating filter preferences."""

    default_filters: Dict[str, Any] = Field(..., description="Default filter settings to set")


class ApiKeyCreate(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(..., description="Name/label for the API key (e.g., 'OpenAI', 'Anthropic')", min_length=1, max_length=100)
    key: str = Field(..., description="The API key string", min_length=1)
    service: str = Field(..., description="Service name (e.g., 'openai', 'anthropic', 'custom')", min_length=1, max_length=50)


class ApiKeyResponse(BaseModel):
    """Response model for a single API key."""

    id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Name/label for the API key")
    service: str = Field(..., description="Service name")
    key: str = Field(..., description="The API key string (masked)")
    created_at: str = Field(..., description="Creation timestamp")


class ApiKeyListResponse(BaseModel):
    """Response model for listing API keys."""

    total: int = Field(..., description="Total number of API keys")
    api_keys: List[ApiKeyResponse] = Field(..., description="List of API keys")


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


async def get_or_create_preferences(db: AsyncSession) -> UserPreferences:
    """
    Get existing preferences or create default preferences.

    Args:
        db: Database session

    Returns:
        UserPreferences instance
    """
    # Try to get existing preferences
    query = select(UserPreferences).where(UserPreferences.id == DEFAULT_PREFERENCES_ID)
    result = await db.execute(query)
    preferences = result.scalar_one_or_none()

    # Create default preferences if not exists
    if not preferences:
        preferences = UserPreferences(
            id=DEFAULT_PREFERENCES_ID,
            language=DEFAULT_LANGUAGE,
        )
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)

    return preferences


@router.get(
    "/language",
    response_model=LanguagePreferenceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def get_language_preference(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the current language preference.

    Returns the currently selected language for the UI.
    Default is 'en' (English) if not previously set.

    Args:
        request: FastAPI request object
        db: Database session

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
        logger.info("Retrieving language preference from database")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        logger.info(f"Retrieved language preference: {preferences.language}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"language": preferences.language},
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
async def update_language_preference(
    request: Request,
    update_data: LanguagePreferenceUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the language preference.

    Sets the language preference for the UI. Supported languages are:
    - 'en' (English)
    - 'ru' (Russian)

    Args:
        request: FastAPI request object
        update_data: Request body containing the language to set
        db: Database session

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
    try:
        # Validate language
        language = validate_language(update_data.language)

        logger.info(f"Updating language preference to: {language}")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        # Update the language preference
        old_language = preferences.language
        preferences.language = language

        await db.commit()
        await db.refresh(preferences)

        logger.info(f"Language preference updated successfully from {old_language} to {preferences.language}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"language": preferences.language},
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error updating language preference: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update language preference: {str(e)}",
        ) from e


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def get_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the user profile.

    Returns the user's profile information including name, email, role, and avatar URL.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with user profile information

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/preferences/profile")
        >>> response.json()
        {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "recruiter",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    """
    try:
        logger.info("Retrieving user profile from database")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        logger.info(f"Retrieved user profile for: {preferences.email or 'unspecified email'}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "name": preferences.name,
                "email": preferences.email,
                "role": preferences.role,
                "avatar_url": preferences.avatar_url,
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}",
        ) from e


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def update_user_profile(
    request: Request,
    update_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the user profile.

    Updates the user's profile information. Only fields that are provided in the
    request will be updated. Fields not provided will remain unchanged.

    Args:
        request: FastAPI request object
        update_data: Request body containing profile fields to update
        db: Database session

    Returns:
        JSON response with updated profile information

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Test User",
        ...     "email": "test@example.com",
        ...     "role": "recruiter"
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/preferences/profile",
        ...     json=data
        ... )
        >>> response.json()
        {
            "name": "Test User",
            "email": "test@example.com",
            "role": "recruiter",
            "avatar_url": null
        }
    """
    try:
        logger.info("Updating user profile")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        # Update fields if provided
        updated_fields = []
        if update_data.name is not None:
            preferences.name = update_data.name
            updated_fields.append("name")
        if update_data.email is not None:
            preferences.email = update_data.email
            updated_fields.append("email")
        if update_data.role is not None:
            preferences.role = update_data.role
            updated_fields.append("role")
        if update_data.avatar_url is not None:
            preferences.avatar_url = update_data.avatar_url
            updated_fields.append("avatar_url")

        await db.commit()
        await db.refresh(preferences)

        logger.info(f"User profile updated successfully. Updated fields: {', '.join(updated_fields) if updated_fields else 'none'}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "name": preferences.name,
                "email": preferences.email,
                "role": preferences.role,
                "avatar_url": preferences.avatar_url,
            },
        )

    except Exception as e:
        logger.error(f"Error updating user profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}",
        ) from e


@router.get(
    "/dashboard",
    response_model=DashboardConfigResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def get_dashboard_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the dashboard configuration.

    Returns the current dashboard configuration including layout, widgets, and settings.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with dashboard configuration

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/preferences/dashboard")
        >>> response.json()
        {
            "layout": "grid",
            "widgets": {"metrics": {"enabled": true, "position": "top"}},
            "settings": {"refresh_interval": 60}
        }
    """
    try:
        logger.info("Retrieving dashboard configuration from database")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        dashboard_config = preferences.dashboard_config or {}

        logger.info(f"Retrieved dashboard configuration: {dashboard_config}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "layout": dashboard_config.get("layout"),
                "widgets": dashboard_config.get("widgets"),
                "settings": dashboard_config.get("settings"),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving dashboard configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard configuration: {str(e)}",
        ) from e


@router.put(
    "/dashboard",
    response_model=DashboardConfigResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def update_dashboard_config(
    request: Request,
    update_data: DashboardConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the dashboard configuration.

    Updates the dashboard configuration with the provided layout, widgets, and settings.
    Only fields that are provided in the request will be updated. Fields not provided
    will remain unchanged.

    Args:
        request: FastAPI request object
        update_data: Request body containing dashboard fields to update
        db: Database session

    Returns:
        JSON response with updated dashboard configuration

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> data = {
        ...     "layout": "grid",
        ...     "widgets": {"metrics": {"enabled": True}, "recent-candidates": {"enabled": True}}
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/preferences/dashboard",
        ...     json=data
        ... )
        >>> response.json()
        {
            "layout": "grid",
            "widgets": {"metrics": {"enabled": true}, "recent-candidates": {"enabled": true}},
            "settings": null
        }
    """
    try:
        logger.info("Updating dashboard configuration")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        # Get current dashboard config or create new one
        dashboard_config = preferences.dashboard_config or {}

        # Update fields if provided
        updated_fields = []
        if update_data.layout is not None:
            dashboard_config["layout"] = update_data.layout
            updated_fields.append("layout")
        if update_data.widgets is not None:
            dashboard_config["widgets"] = update_data.widgets
            updated_fields.append("widgets")
        if update_data.settings is not None:
            dashboard_config["settings"] = update_data.settings
            updated_fields.append("settings")

        # Save the updated dashboard config
        preferences.dashboard_config = dashboard_config

        await db.commit()
        await db.refresh(preferences)

        logger.info(f"Dashboard configuration updated successfully. Updated fields: {', '.join(updated_fields) if updated_fields else 'none'}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "layout": dashboard_config.get("layout"),
                "widgets": dashboard_config.get("widgets"),
                "settings": dashboard_config.get("settings"),
            },
        )

    except Exception as e:
        logger.error(f"Error updating dashboard configuration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dashboard configuration: {str(e)}",
        ) from e


@router.get(
    "/filters",
    response_model=FilterPreferencesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def get_filter_preferences(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the filter preferences.

    Returns the default filter settings that are used when searching candidates.
    These filters can include experience years, languages, location, skills, and more.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with filter preferences

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/preferences/filters")
        >>> response.json()
        {
            "default_filters": {
                "experience_years": [0, 10],
                "languages": ["en", "ru"]
            }
        }
    """
    try:
        logger.info("Retrieving filter preferences from database")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        filter_prefs = preferences.filter_preferences or {}

        logger.info(f"Retrieved filter preferences: {filter_prefs}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"default_filters": filter_prefs},
        )

    except Exception as e:
        logger.error(f"Error retrieving filter preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve filter preferences: {str(e)}",
        ) from e


@router.put(
    "/filters",
    response_model=FilterPreferencesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Preferences"],
)
async def update_filter_preferences(
    request: Request,
    update_data: FilterPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the filter preferences.

    Updates the default filter settings used when searching candidates.
    These filters will be applied as defaults when performing candidate searches.

    Common filter fields include:
    - experience_years: Range of years of experience [min, max]
    - languages: List of preferred languages ["en", "ru", etc.]
    - location: Geographic location filter
    - skills: List of required or preferred skills
    - salary_range: Expected salary range [min, max]

    Args:
        request: FastAPI request object
        update_data: Request body containing filter preferences to set
        db: Database session

    Returns:
        JSON response with updated filter preferences

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> data = {
        ...     "default_filters": {
        ...         "experience_years": [0, 10],
        ...         "languages": ["en", "ru"]
        ...     }
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/preferences/filters",
        ...     json=data
        ... )
        >>> response.json()
        {
            "default_filters": {
                "experience_years": [0, 10],
                "languages": ["en", "ru"]
            }
        }
    """
    try:
        logger.info("Updating filter preferences")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        # Update the filter preferences
        old_filters = preferences.filter_preferences or {}
        preferences.filter_preferences = update_data.default_filters

        await db.commit()
        await db.refresh(preferences)

        logger.info(f"Filter preferences updated successfully from {old_filters} to {preferences.filter_preferences}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"default_filters": preferences.filter_preferences or {}},
        )

    except Exception as e:
        logger.error(f"Error updating filter preferences: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update filter preferences: {str(e)}",
        ) from e


@router.post(
    "/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Preferences"],
)
async def create_api_key(
    request: Request,
    key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new API key.

    Adds a new API key to the user's preferences for external service integrations.
    The key is stored securely and can be used for AI services, job boards, or other integrations.

    Args:
        request: FastAPI request object
        key_data: API key creation data (name, key, service)
        db: Database session

    Returns:
        JSON response with created API key details

    Raises:
        HTTPException(400): Invalid request data
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "OpenAI",
        ...     "key": "sk-test-key",
        ...     "service": "openai"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/preferences/api-keys",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Creating API key for service: {key_data.service}")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        # Get current API keys or create new dict
        api_keys = preferences.api_keys or {}

        # Check for duplicate name
        if key_data.name in api_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"API key with name '{key_data.name}' already exists",
            )

        # Generate a unique ID for this key
        import time
        key_id = str(int(time.time() * 1000))

        # Add the new API key
        api_keys[key_id] = {
            "name": key_data.name,
            "key": key_data.key,
            "service": key_data.service,
            "created_at": preferences.updated_at.isoformat() if preferences.updated_at else None,
        }

        # Save the updated API keys
        preferences.api_keys = api_keys
        await db.commit()
        await db.refresh(preferences)

        logger.info(f"API key created with ID: {key_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": key_id,
                "name": key_data.name,
                "service": key_data.service,
                "key": _mask_api_key(key_data.key),
                "created_at": api_keys[key_id]["created_at"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        ) from e


@router.get(
    "/api-keys",
    response_model=ApiKeyListResponse,
    tags=["Preferences"],
)
async def list_api_keys(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all API keys.

    Returns a list of all stored API keys for external service integrations.
    The actual key values are masked for security, showing only the last few characters.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with list of API keys and total count

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/preferences/api-keys")
        >>> api_keys = response.json()
    """
    try:
        logger.info("Listing API keys")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        api_keys = preferences.api_keys or {}

        # Convert to response format with masked keys
        api_keys_list = []
        for key_id, key_data in api_keys.items():
            api_keys_list.append({
                "id": key_id,
                "name": key_data.get("name", ""),
                "service": key_data.get("service", ""),
                "key": _mask_api_key(key_data.get("key", "")),
                "created_at": key_data.get("created_at", ""),
            })

        logger.info(f"Retrieved {len(api_keys_list)} API keys")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": len(api_keys_list),
                "api_keys": api_keys_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        ) from e


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Preferences"],
)
async def delete_api_key(
    request: Request,
    key_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an API key.

    Permanently removes an API key from the user's preferences.
    This action cannot be undone.

    Args:
        request: FastAPI request object
        key_id: Unique identifier of the API key to delete
        db: Database session

    Returns:
        HTTP 204 No Content on successful deletion

    Raises:
        HTTPException(404): API key not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/preferences/api-keys/1234567890"
        ... )
    """
    try:
        logger.info(f"Deleting API key: {key_id}")

        # Get or create preferences
        preferences = await get_or_create_preferences(db)

        api_keys = preferences.api_keys or {}

        # Check if the key exists
        if key_id not in api_keys:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}",
            )

        # Delete the API key
        del api_keys[key_id]
        preferences.api_keys = api_keys

        await db.commit()
        await db.refresh(preferences)

        logger.info(f"API key {key_id} deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key {key_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}",
        ) from e


def _mask_api_key(key: str) -> str:
    """
    Mask an API key for security, showing only the last 4 characters.

    Args:
        key: The API key to mask

    Returns:
        Masked API key string
    """
    if not key or len(key) <= 4:
        return "****"
    return f"{'*' * (len(key) - 4)}{key[-4:]}"
