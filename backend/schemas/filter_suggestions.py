"""
Pydantic schemas for filter suggestions and alert settings API.

This module provides request/response models for:
- AI-powered job description filter suggestions
- Structured vacancy data filter extraction
- Alert settings configuration for saved searches
- One-click saved search application

These schemas ensure data validation and serialization for the filter
suggestions and alert settings API endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Filter Suggestion Schemas
# ============================================================================

class FilterSuggestionRequest(BaseModel):
    """Request model for JD filter suggestions."""

    job_description: str = Field(
        ...,
        description="Job description text to analyze for filter suggestions",
        min_length=10,
        max_length=50000,
    )
    max_skills: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of skills to suggest",
    )
    min_confidence: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for suggestions (0.0-1.0)",
    )


class SuggestedFilterItem(BaseModel):
    """Single suggested filter item with confidence scoring."""

    filter_type: str = Field(
        ...,
        description="Type of filter (skills, location, education_level, languages)",
    )
    value: Any = Field(..., description="The filter value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    source: str = Field(
        ...,
        description="Source of suggestion (extracted, inferred, synonym, provided)",
    )
    original_text: Optional[str] = Field(
        None,
        description="Original text from JD that led to this suggestion",
    )

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        valid_sources = ["extracted", "inferred", "synonym", "provided"]
        if v not in valid_sources:
            raise ValueError(
                f"Invalid source. Must be one of: {', '.join(valid_sources)}"
            )
        return v


class FilterSuggestionResponse(BaseModel):
    """Response model for filter suggestions."""

    skills: List[SuggestedFilterItem] = Field(
        default_factory=list,
        description="List of suggested skill filters with confidence scores",
    )
    min_experience_years: Optional[int] = Field(
        None,
        description="Suggested minimum years of experience",
        ge=0,
        le=50,
    )
    max_experience_years: Optional[int] = Field(
        None,
        description="Suggested maximum years of experience",
        ge=0,
        le=50,
    )
    seniority_level: Optional[str] = Field(
        None,
        description="Detected seniority level (entry, mid, senior, lead, executive)",
    )
    location: Optional[SuggestedFilterItem] = Field(
        None,
        description="Suggested location filter",
    )
    education_level: Optional[SuggestedFilterItem] = Field(
        None,
        description="Suggested education level filter",
    )
    languages: List[SuggestedFilterItem] = Field(
        default_factory=list,
        description="List of suggested language filters",
    )
    all_filters: List[SuggestedFilterItem] = Field(
        default_factory=list,
        description="Combined list of all suggested filters sorted by confidence",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the suggestions (0.0-1.0)",
    )
    analysis_time_seconds: float = Field(
        ...,
        ge=0.0,
        description="Time taken to analyze the job description",
    )
    search_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ready-to-use filters dictionary for search API",
    )

    @field_validator("seniority_level")
    @classmethod
    def validate_seniority_level(cls, v):
        if v is not None:
            valid_levels = ["entry", "mid", "senior", "lead", "executive"]
            if v not in valid_levels:
                raise ValueError(
                    f"Invalid seniority level. Must be one of: {', '.join(valid_levels)}"
                )
        return v


class VacancyFilterRequest(BaseModel):
    """Request model for structured vacancy filter suggestions."""

    title: Optional[str] = Field(
        None,
        description="Job title",
        max_length=500,
    )
    description: Optional[str] = Field(
        None,
        description="Job description text",
        max_length=50000,
    )
    skills: Optional[List[str]] = Field(
        None,
        description="List of required skills from vacancy",
    )
    requirements: Optional[List[str]] = Field(
        None,
        description="List of additional requirements",
    )


# ============================================================================
# Alert Settings Schemas
# ============================================================================

class AlertSettingsUpdate(BaseModel):
    """Request model for updating alert settings on a saved search."""

    alert_enabled: Optional[bool] = Field(
        None,
        description="Enable or disable alerts for this saved search",
    )
    alert_frequency: Optional[str] = Field(
        None,
        description="Frequency of alerts: 'realtime', 'daily', or 'weekly'",
    )

    @field_validator("alert_frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is not None:
            valid_frequencies = ["realtime", "daily", "weekly"]
            if v not in valid_frequencies:
                raise ValueError(
                    f"Invalid alert_frequency. Must be one of: {', '.join(valid_frequencies)}"
                )
        return v


class AlertSettingsResponse(BaseModel):
    """Response model for alert settings on a saved search."""

    id: str = Field(..., description="Saved search UUID")
    name: str = Field(..., description="Saved search name")
    alert_enabled: bool = Field(..., description="Whether alerts are enabled")
    alert_frequency: Optional[str] = Field(
        None,
        description="Frequency of alerts (realtime, daily, weekly)",
    )
    last_alert_at: Optional[str] = Field(
        None,
        description="ISO timestamp when last alert was sent",
    )


class AlertSettingsListResponse(BaseModel):
    """Response model for listing alert settings across multiple saved searches."""

    total: int = Field(..., description="Total number of saved searches with alerts")
    alerts_enabled_count: int = Field(
        ...,
        description="Number of saved searches with alerts enabled",
    )
    alert_settings: List[AlertSettingsResponse] = Field(
        ...,
        description="List of alert settings for saved searches",
    )


# ============================================================================
# Saved Search Application Schemas
# ============================================================================

class ApplySearchResponse(BaseModel):
    """Response model for applying a saved search (one-click apply)."""

    saved_search_id: str = Field(..., description="UUID of the applied saved search")
    saved_search_name: str = Field(..., description="Name of the saved search")
    total: int = Field(..., description="Total number of matching candidates")
    candidates: List[Dict[str, Any]] = Field(
        ...,
        description="List of candidate results",
    )
    query: str = Field(..., description="Search query that was executed")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters that were applied",
    )
    execution_time_seconds: float = Field(
        ...,
        description="Time taken to execute search",
    )


# ============================================================================
# Combined Saved Search Schemas (with Alert Settings)
# ============================================================================

class SavedSearchWithAlertsCreate(BaseModel):
    """Request model for creating a saved search with optional alert settings."""

    name: str = Field(
        ...,
        description="User-provided name for the saved search",
        min_length=1,
        max_length=255,
    )
    query: str = Field(
        ...,
        description="Search query string with boolean operators",
        min_length=1,
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter settings (skills, experience_years, location, etc.)",
    )
    alert_enabled: Optional[bool] = Field(
        False,
        description="Whether to enable alerts for this saved search",
    )
    alert_frequency: Optional[str] = Field(
        None,
        description="Frequency of alerts if enabled (realtime, daily, weekly)",
    )

    @field_validator("alert_frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is not None:
            valid_frequencies = ["realtime", "daily", "weekly"]
            if v not in valid_frequencies:
                raise ValueError(
                    f"Invalid alert_frequency. Must be one of: {', '.join(valid_frequencies)}"
                )
        return v


class SavedSearchWithAlertsUpdate(BaseModel):
    """Request model for updating a saved search with alert settings."""

    name: Optional[str] = Field(
        None,
        description="Updated name for the saved search",
        min_length=1,
        max_length=255,
    )
    query: Optional[str] = Field(
        None,
        description="Updated search query string",
        min_length=1,
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated filter settings",
    )
    alert_enabled: Optional[bool] = Field(
        None,
        description="Enable or disable alerts",
    )
    alert_frequency: Optional[str] = Field(
        None,
        description="Updated frequency of alerts",
    )

    @field_validator("alert_frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is not None:
            valid_frequencies = ["realtime", "daily", "weekly"]
            if v not in valid_frequencies:
                raise ValueError(
                    f"Invalid alert_frequency. Must be one of: {', '.join(valid_frequencies)}"
                )
        return v


class SavedSearchWithAlertsResponse(BaseModel):
    """Response model for a saved search including alert settings."""

    id: str = Field(..., description="Saved search UUID")
    name: str = Field(..., description="Saved search name")
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(..., description="Filter settings")
    alert_enabled: bool = Field(
        False,
        description="Whether alerts are enabled for this saved search",
    )
    alert_frequency: Optional[str] = Field(
        None,
        description="Frequency of alerts if enabled",
    )
    last_alert_at: Optional[str] = Field(
        None,
        description="Timestamp when last alert was sent",
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SavedSearchListWithAlertsResponse(BaseModel):
    """Response model for listing saved searches with alert settings."""

    total: int = Field(..., description="Total number of saved searches")
    alerts_enabled_count: int = Field(
        ...,
        description="Number of saved searches with alerts enabled",
    )
    saved_searches: List[SavedSearchWithAlertsResponse] = Field(
        ...,
        description="List of saved searches with alert settings",
    )


# ============================================================================
# Bulk Operations Schemas
# ============================================================================

class BulkAlertSettingsUpdate(BaseModel):
    """Request model for updating alert settings on multiple saved searches."""

    saved_search_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of saved search UUIDs to update",
    )
    alert_enabled: Optional[bool] = Field(
        None,
        description="Enable or disable alerts for all specified saved searches",
    )
    alert_frequency: Optional[str] = Field(
        None,
        description="Set alert frequency for all specified saved searches",
    )

    @field_validator("alert_frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is not None:
            valid_frequencies = ["realtime", "daily", "weekly"]
            if v not in valid_frequencies:
                raise ValueError(
                    f"Invalid alert_frequency. Must be one of: {', '.join(valid_frequencies)}"
                )
        return v


class BulkAlertSettingsResponse(BaseModel):
    """Response model for bulk alert settings update."""

    updated_count: int = Field(..., description="Number of saved searches updated")
    failed_count: int = Field(..., description="Number of saved searches that failed to update")
    updated: List[AlertSettingsResponse] = Field(
        ...,
        description="List of successfully updated alert settings",
    )
    failed: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of failed updates with error details",
    )
