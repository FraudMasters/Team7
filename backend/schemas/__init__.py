"""
Pydantic schemas for request/response validation

This module provides schema definitions for API endpoints.
"""
from .backup import (
    BackupResponse,
    BackupCreate,
    BackupRestoreRequest,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupStatusResponse,
    S3Config,
)

from .user_preferences import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeysListResponse,
    DashboardConfigResponse,
    DashboardConfigUpdate,
    FilterPreferencesResponse,
    FilterPreferencesUpdate,
    LanguagePreferencesResponse,
    LanguagePreferencesUpdate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    UserPreferencesCreate,
    UserPreferencesListResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)

__all__ = [
    "BackupResponse",
    "BackupCreate",
    "BackupRestoreRequest",
    "BackupConfigResponse",
    "BackupConfigUpdate",
    "BackupStatusResponse",
    "S3Config",
    "UserProfileUpdate",
    "UserProfileResponse",
    "LanguagePreferencesUpdate",
    "LanguagePreferencesResponse",
    "NotificationPreferencesUpdate",
    "NotificationPreferencesResponse",
    "DashboardConfigUpdate",
    "DashboardConfigResponse",
    "FilterPreferencesUpdate",
    "FilterPreferencesResponse",
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeysListResponse",
    "UserPreferencesCreate",
    "UserPreferencesUpdate",
    "UserPreferencesResponse",
    "UserPreferencesListResponse",
]
