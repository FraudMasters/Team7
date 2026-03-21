"""
Pydantic schemas for ranking weights API.

This module provides request/response models for:
- Custom ranking weight profile management
- Profile creation, updates, and retrieval
- Weight normalization and validation
- Preset profile access
- Version history tracking

These schemas ensure data validation and serialization for the ranking
weights API endpoints.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Preset type literal
PresetType = Literal["technical", "sales", "executive", "balanced"]


class RankingWeightProfileCreate(BaseModel):
    """Request model for creating a ranking weight profile."""

    organization_id: Optional[str] = Field(None, description="Organization identifier")
    vacancy_id: Optional[str] = Field(None, description="Vacancy identifier (for vacancy-specific profiles)")
    name: str = Field(..., description="Human-readable name for this profile", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)

    # 13 ranking feature weights
    overall_match_score_weight: float = Field(
        0.077,
        description="Weight for overall composite match score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    keyword_score_weight: float = Field(
        0.077,
        description="Weight for keyword-based matching score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    tfidf_score_weight: float = Field(
        0.077,
        description="Weight for TF-IDF matching score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    vector_score_weight: float = Field(
        0.077,
        description="Weight for vector similarity score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    skills_match_ratio_weight: float = Field(
        0.077,
        description="Weight for skills match ratio (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    experience_months_weight: float = Field(
        0.077,
        description="Weight for total experience duration (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    experience_relevance_weight: float = Field(
        0.077,
        description="Weight for experience relevance (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    education_level_weight: float = Field(
        0.077,
        description="Weight for education level (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    recent_experience_weight: float = Field(
        0.077,
        description="Weight for recent experience (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    skill_rarity_weight: float = Field(
        0.077,
        description="Weight for skill rarity/uniqueness (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    title_similarity_weight: float = Field(
        0.077,
        description="Weight for job title similarity (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    freshness_score_weight: float = Field(
        0.077,
        description="Weight for profile/resume freshness (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    completeness_score_weight: float = Field(
        0.076,
        description="Weight for profile completeness (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )

    is_active: bool = Field(True, description="Whether this profile is active")
    is_preset: bool = Field(False, description="Whether this is a system preset profile")
    preset_type: Optional[PresetType] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who is creating this profile")
    change_reason: Optional[str] = Field(None, description="Reason for creating this profile", max_length=1000)

    @field_validator("preset_type")
    @classmethod
    def validate_preset_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that preset_type is only set if is_preset is True."""
        if v is not None and not info.data.get("is_preset", False):
            raise ValueError("preset_type can only be set for preset profiles")
        return v


class RankingWeightProfileUpdate(BaseModel):
    """Request model for updating a ranking weight profile."""

    name: Optional[str] = Field(None, description="Human-readable name for this profile", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)

    # 13 ranking feature weights (all optional for partial updates)
    overall_match_score_weight: Optional[float] = Field(None, description="Weight for overall composite match score (0.0 to 1.0)", ge=0.0, le=1.0)
    keyword_score_weight: Optional[float] = Field(None, description="Weight for keyword-based matching score (0.0 to 1.0)", ge=0.0, le=1.0)
    tfidf_score_weight: Optional[float] = Field(None, description="Weight for TF-IDF matching score (0.0 to 1.0)", ge=0.0, le=1.0)
    vector_score_weight: Optional[float] = Field(None, description="Weight for vector similarity score (0.0 to 1.0)", ge=0.0, le=1.0)
    skills_match_ratio_weight: Optional[float] = Field(None, description="Weight for skills match ratio (0.0 to 1.0)", ge=0.0, le=1.0)
    experience_months_weight: Optional[float] = Field(None, description="Weight for total experience duration (0.0 to 1.0)", ge=0.0, le=1.0)
    experience_relevance_weight: Optional[float] = Field(None, description="Weight for experience relevance (0.0 to 1.0)", ge=0.0, le=1.0)
    education_level_weight: Optional[float] = Field(None, description="Weight for education level (0.0 to 1.0)", ge=0.0, le=1.0)
    recent_experience_weight: Optional[float] = Field(None, description="Weight for recent experience (0.0 to 1.0)", ge=0.0, le=1.0)
    skill_rarity_weight: Optional[float] = Field(None, description="Weight for skill rarity/uniqueness (0.0 to 1.0)", ge=0.0, le=1.0)
    title_similarity_weight: Optional[float] = Field(None, description="Weight for job title similarity (0.0 to 1.0)", ge=0.0, le=1.0)
    freshness_score_weight: Optional[float] = Field(None, description="Weight for profile/resume freshness (0.0 to 1.0)", ge=0.0, le=1.0)
    completeness_score_weight: Optional[float] = Field(None, description="Weight for profile completeness (0.0 to 1.0)", ge=0.0, le=1.0)

    is_active: Optional[bool] = Field(None, description="Whether this profile is active")
    updated_by: Optional[str] = Field(None, description="User ID who is updating this profile")
    change_reason: Optional[str] = Field(None, description="Reason for this update", max_length=1000)


class RankingWeightProfileResponse(BaseModel):
    """Response model for a single ranking weight profile."""

    id: str = Field(..., description="Unique identifier for the profile")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    vacancy_id: Optional[str] = Field(None, description="Vacancy identifier")
    name: str = Field(..., description="Human-readable name for this profile")
    description: Optional[str] = Field(None, description="Description of when to use this profile")

    # 13 ranking feature weights
    overall_match_score_weight: float = Field(..., description="Weight for overall composite match score")
    keyword_score_weight: float = Field(..., description="Weight for keyword-based matching score")
    tfidf_score_weight: float = Field(..., description="Weight for TF-IDF matching score")
    vector_score_weight: float = Field(..., description="Weight for vector similarity score")
    skills_match_ratio_weight: float = Field(..., description="Weight for skills match ratio")
    experience_months_weight: float = Field(..., description="Weight for total experience duration")
    experience_relevance_weight: float = Field(..., description="Weight for experience relevance")
    education_level_weight: float = Field(..., description="Weight for education level")
    recent_experience_weight: float = Field(..., description="Weight for recent experience")
    skill_rarity_weight: float = Field(..., description="Weight for skill rarity/uniqueness")
    title_similarity_weight: float = Field(..., description="Weight for job title similarity")
    freshness_score_weight: float = Field(..., description="Weight for profile/resume freshness")
    completeness_score_weight: float = Field(..., description="Weight for profile completeness")

    is_active: bool = Field(..., description="Whether this profile is active")
    is_preset: bool = Field(..., description="Whether this is a system preset")
    preset_type: Optional[str] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who created this profile")
    updated_by: Optional[str] = Field(None, description="User ID who last updated this profile")
    version: Optional[str] = Field(None, description="Version tracking for weight changes")
    change_reason: Optional[str] = Field(None, description="Reason for the last weight change")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class RankingWeightProfileListResponse(BaseModel):
    """Response model for listing ranking weight profiles."""

    organization_id: Optional[str] = Field(None, description="Organization ID filter used")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID filter used")
    profiles: List[RankingWeightProfileResponse] = Field(..., description="List of weight profiles")
    total_count: int = Field(..., description="Total number of profiles")


class RankingWeightVersionResponse(BaseModel):
    """Response model for a ranking weight version history entry."""

    id: str = Field(..., description="Unique identifier for the version")
    profile_id: str = Field(..., description="Profile ID this version belongs to")

    # Snapshot of weights at this version
    overall_match_score_weight: float = Field(..., description="Overall match score weight at this version")
    keyword_score_weight: float = Field(..., description="Keyword score weight at this version")
    tfidf_score_weight: float = Field(..., description="TF-IDF score weight at this version")
    vector_score_weight: float = Field(..., description="Vector score weight at this version")
    skills_match_ratio_weight: float = Field(..., description="Skills match ratio weight at this version")
    experience_months_weight: float = Field(..., description="Experience months weight at this version")
    experience_relevance_weight: float = Field(..., description="Experience relevance weight at this version")
    education_level_weight: float = Field(..., description="Education level weight at this version")
    recent_experience_weight: float = Field(..., description="Recent experience weight at this version")
    skill_rarity_weight: float = Field(..., description="Skill rarity weight at this version")
    title_similarity_weight: float = Field(..., description="Title similarity weight at this version")
    freshness_score_weight: float = Field(..., description="Freshness score weight at this version")
    completeness_score_weight: float = Field(..., description="Completeness score weight at this version")

    changed_by: Optional[str] = Field(None, description="User ID who made the change")
    version: str = Field(..., description="Version identifier")
    change_reason: Optional[str] = Field(None, description="Reason for this change")
    created_at: str = Field(..., description="When this version was created")
    updated_at: str = Field(..., description="Last update timestamp")


class NormalizeWeightsRequest(BaseModel):
    """Request model for normalizing ranking weights."""

    # 13 ranking feature weights (all optional, only provided weights will be normalized)
    overall_match_score_weight: Optional[float] = Field(None, description="Weight for overall composite match score", ge=0.0)
    keyword_score_weight: Optional[float] = Field(None, description="Weight for keyword-based matching score", ge=0.0)
    tfidf_score_weight: Optional[float] = Field(None, description="Weight for TF-IDF matching score", ge=0.0)
    vector_score_weight: Optional[float] = Field(None, description="Weight for vector similarity score", ge=0.0)
    skills_match_ratio_weight: Optional[float] = Field(None, description="Weight for skills match ratio", ge=0.0)
    experience_months_weight: Optional[float] = Field(None, description="Weight for total experience duration", ge=0.0)
    experience_relevance_weight: Optional[float] = Field(None, description="Weight for experience relevance", ge=0.0)
    education_level_weight: Optional[float] = Field(None, description="Weight for education level", ge=0.0)
    recent_experience_weight: Optional[float] = Field(None, description="Weight for recent experience", ge=0.0)
    skill_rarity_weight: Optional[float] = Field(None, description="Weight for skill rarity/uniqueness", ge=0.0)
    title_similarity_weight: Optional[float] = Field(None, description="Weight for job title similarity", ge=0.0)
    freshness_score_weight: Optional[float] = Field(None, description="Weight for profile/resume freshness", ge=0.0)
    completeness_score_weight: Optional[float] = Field(None, description="Weight for profile completeness", ge=0.0)


class NormalizeWeightsResponse(BaseModel):
    """Response model for normalized ranking weights."""

    # Normalized weights (sum to 1.0)
    overall_match_score_weight: float = Field(..., description="Normalized overall match score weight")
    keyword_score_weight: float = Field(..., description="Normalized keyword score weight")
    tfidf_score_weight: float = Field(..., description="Normalized TF-IDF score weight")
    vector_score_weight: float = Field(..., description="Normalized vector score weight")
    skills_match_ratio_weight: float = Field(..., description="Normalized skills match ratio weight")
    experience_months_weight: float = Field(..., description="Normalized experience months weight")
    experience_relevance_weight: float = Field(..., description="Normalized experience relevance weight")
    education_level_weight: float = Field(..., description="Normalized education level weight")
    recent_experience_weight: float = Field(..., description="Normalized recent experience weight")
    skill_rarity_weight: float = Field(..., description="Normalized skill rarity weight")
    title_similarity_weight: float = Field(..., description="Normalized title similarity weight")
    freshness_score_weight: float = Field(..., description="Normalized freshness score weight")
    completeness_score_weight: float = Field(..., description="Normalized completeness score weight")

    total: float = Field(..., description="Sum of all weights (should be 1.0)")
