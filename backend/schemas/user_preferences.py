"""
Pydantic schemas for user preferences API.

This module provides request/response models for:
- User profile management (name, email, role, avatar)
- Language and timezone preferences
- Notification preferences (email, in-app)
- Dashboard configuration
- Filter preferences
- API keys management

These schemas ensure data validation and serialization for the user preferences API.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr


# Profile Management Schemas
class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""

    name: Optional[str] = Field(None, description="User's display name", min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role (e.g., recruiter, hiring_manager)", min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image", max_length=512)


class UserProfileResponse(BaseModel):
    """Response model for user profile."""

    name: Optional[str] = Field(None, description="User's display name")
    email: Optional[str] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")


# Language Preferences Schemas
class LanguagePreferencesUpdate(BaseModel):
    """Request model for updating language preferences."""

    language: Optional[str] = Field(
        None,
        description="User's preferred language code (en, ru, etc.)",
        min_length=2,
        max_length=10
    )
    timezone: Optional[str] = Field(
        None,
        description="User's preferred timezone",
        min_length=1,
        max_length=50
    )


class LanguagePreferencesResponse(BaseModel):
    """Response model for language preferences."""

    language: str = Field(..., description="User's preferred language code")
    timezone: Optional[str] = Field(None, description="User's preferred timezone")


# Notification Preferences Schemas
class NotificationPreferencesUpdate(BaseModel):
    """Request model for updating notification preferences."""

    email_notifications: Optional[bool] = Field(
        None,
        description="Whether user wants to receive email notifications"
    )
    in_app_notifications: Optional[bool] = Field(
        None,
        description="Whether user wants to receive in-app notifications"
    )


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences."""

    email_notifications: bool = Field(..., description="Email notifications enabled")
    in_app_notifications: bool = Field(..., description="In-app notifications enabled")


# Dashboard Configuration Schemas
class DashboardConfigUpdate(BaseModel):
    """Request model for updating dashboard configuration."""

    layout: Optional[str] = Field(None, description="Dashboard layout type (grid, list, etc.)")
    widgets: Optional[List[str]] = Field(None, description="List of widget names in display order")
    widget_settings: Optional[Dict[str, Any]] = Field(None, description="Individual widget configurations")


class DashboardConfigResponse(BaseModel):
    """Response model for dashboard configuration."""

    layout: Optional[str] = Field(None, description="Dashboard layout type")
    widgets: List[str] = Field(default_factory=list, description="List of widgets in order")
    widget_settings: Dict[str, Any] = Field(default_factory=dict, description="Widget configurations")


# Filter Preferences Schemas
class FilterPreferencesUpdate(BaseModel):
    """Request model for updating filter preferences."""

    default_filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Default filter settings for candidate searches"
    )


class FilterPreferencesResponse(BaseModel):
    """Response model for filter preferences."""

    default_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default filter settings for candidate searches"
    )


# API Keys Schemas
class ApiKeyCreate(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(..., description="Friendly name for the API key", min_length=1, max_length=255)
    key: str = Field(..., description="API key value", min_length=1)
    service: str = Field(..., description="Service name (e.g., openai, anthropic)", min_length=1, max_length=100)


class ApiKeyResponse(BaseModel):
    """Response model for an API key."""

    name: str = Field(..., description="API key name")
    service: str = Field(..., description="Service name")
    last_four: Optional[str] = Field(None, description="Last 4 characters of the key for identification")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ApiKeysListResponse(BaseModel):
    """Response model for listing API keys."""

    api_keys: List[ApiKeyResponse] = Field(..., description="List of API keys")


# Comprehensive User Preferences Schemas
class UserPreferencesCreate(BaseModel):
    """Request model for creating user preferences (full object)."""

    language: str = Field(..., description="User's preferred language code", default="en", min_length=2, max_length=10)
    timezone: Optional[str] = Field(None, description="User's preferred timezone", max_length=50)
    email_notifications: bool = Field(True, description="Email notifications enabled")
    in_app_notifications: bool = Field(True, description="In-app notifications enabled")
    name: Optional[str] = Field(None, description="User's display name", max_length=255)
    email: Optional[EmailStr] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role", max_length=100)
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar", max_length=512)
    dashboard_config: Optional[Dict[str, Any]] = Field(None, description="Dashboard configuration")
    filter_preferences: Optional[Dict[str, Any]] = Field(None, description="Filter preferences")
    api_keys: Optional[Dict[str, Any]] = Field(None, description="API keys storage")


class UserPreferencesUpdate(BaseModel):
    """Request model for updating user preferences (partial updates)."""

    language: Optional[str] = Field(None, description="User's preferred language code", min_length=2, max_length=10)
    timezone: Optional[str] = Field(None, description="User's preferred timezone", max_length=50)
    email_notifications: Optional[bool] = Field(None, description="Email notifications enabled")
    in_app_notifications: Optional[bool] = Field(None, description="In-app notifications enabled")
    name: Optional[str] = Field(None, description="User's display name", max_length=255)
    email: Optional[EmailStr] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role", max_length=100)
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar", max_length=512)
    dashboard_config: Optional[Dict[str, Any]] = Field(None, description="Dashboard configuration")
    filter_preferences: Optional[Dict[str, Any]] = Field(None, description="Filter preferences")
    api_keys: Optional[Dict[str, Any]] = Field(None, description="API keys storage")


class UserPreferencesResponse(BaseModel):
    """Response model for complete user preferences."""

    id: str = Field(..., description="User preferences UUID")
    language: str = Field(..., description="User's preferred language code")
    timezone: Optional[str] = Field(None, description="User's preferred timezone")
    email_notifications: bool = Field(..., description="Email notifications enabled")
    in_app_notifications: bool = Field(..., description="In-app notifications enabled")
    name: Optional[str] = Field(None, description="User's display name")
    email: Optional[str] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's role")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar")
    dashboard_config: Dict[str, Any] = Field(..., description="Dashboard configuration")
    filter_preferences: Dict[str, Any] = Field(..., description="Filter preferences")
    api_keys: Dict[str, Any] = Field(..., description="API keys storage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class UserPreferencesListResponse(BaseModel):
    """Response model for listing user preferences."""

    total: int = Field(..., description="Total number of preferences records")
    preferences: List[UserPreferencesResponse] = Field(..., description="List of user preferences")
