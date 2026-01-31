"""
Matching weight profile management endpoints.

This module provides endpoints for creating, reading, updating, and deleting
custom weight profiles for the unified matching algorithm. Recruiters can
adjust the relative importance of Keyword, TF-IDF, and Vector similarity
matching methods for different hiring scenarios.
"""
import logging
from decimal import InvalidOperation
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from i18n.backend_translations import get_error_message, get_success_message
from models.matching_weights import (
    MatchingWeightProfile,
    MatchingWeightVersion,
    PRESET_PROFILES,
    create_preset_profiles,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================


class MatchingWeightsBase(BaseModel):
    """Base fields for matching weight profile."""

    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    description: Optional[str] = Field(None, description="When to use this profile")
    keyword_weight: float = Field(..., ge=0, le=1, description="Keyword matching weight (0-1)")
    tfidf_weight: float = Field(..., ge=0, le=1, description="TF-IDF matching weight (0-1)")
    vector_weight: float = Field(..., ge=0, le=1, description="Vector matching weight (0-1)")

    @field_validator('keyword_weight', 'tfidf_weight', 'vector_weight')
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Validate individual weight is in valid range."""
        return round(v, 3)

    @field_validator('vector_weight')
    @classmethod
    def validate_total(cls, v: float, info: ValidationInfo) -> float:
        """Validate that weights sum to approximately 1.0."""
        if info.data:
            keyword = info.data.get('keyword_weight', 0)
            tfidf = info.data.get('tfidf_weight', 0)
            total = keyword + tfidf + v
            if abs(total - 1.0) > 0.01:
                raise ValueError(
                    f"Weights must sum to 1.0 (current sum: {total:.3f}). "
                    "Use the /normalize endpoint or adjust values."
                )
        return v


class MatchingWeightsCreate(MatchingWeightsBase):
    """Request model for creating a custom weight profile."""

    organization_id: Optional[str] = Field(None, description="Organization ID for org-specific profile")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID for vacancy-specific profile")
    change_reason: Optional[str] = Field(None, description="Reason for creating this profile")


class MatchingWeightsUpdate(BaseModel):
    """Request model for updating a weight profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    keyword_weight: Optional[float] = Field(None, ge=0, le=1)
    tfidf_weight: Optional[float] = Field(None, ge=0, le=1)
    vector_weight: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    change_reason: Optional[str] = Field(None, description="Reason for the change")

    @field_validator('keyword_weight', 'tfidf_weight', 'vector_weight')
    @classmethod
    def validate_weights(cls, v: Optional[float]) -> Optional[float]:
        """Validate and round weight values."""
        return round(v, 3) if v is not None else None


class MatchingWeightsResponse(BaseModel):
    """Response model for a weight profile."""

    id: str
    name: str
    description: Optional[str]
    organization_id: Optional[str]
    vacancy_id: Optional[str]
    is_preset: bool
    is_active: bool
    keyword_weight: float
    tfidf_weight: float
    vector_weight: float
    weights_percentage: dict[str, int]  # For UI display
    version: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    updated_by: Optional[str]

    model_config = {"from_attributes": True}


class MatchingWeightsListResponse(BaseModel):
    """Response model for listing weight profiles."""

    profiles: list[MatchingWeightsResponse]
    total_count: int
    preset_count: int
    custom_count: int


class PresetProfileResponse(BaseModel):
    """Response model for a preset profile."""

    name: str
    description: str
    keyword_weight: float
    tfidf_weight: float
    vector_weight: float
    weights_percentage: dict[str, int]
    use_case: str  # When to use this preset


class PresetsResponse(BaseModel):
    """Response model for all preset profiles."""

    presets: list[PresetProfileResponse]


class ApplyWeightsRequest(BaseModel):
    """Request model for applying weights to re-match candidates."""

    vacancy_id: str
    profile_id: Optional[str] = Field(None, description="Weight profile to use")
    weights: Optional[MatchingWeightsUpdate] = Field(None, description="Or custom weights")
    re_match_candidates: bool = Field(True, description="Whether to trigger re-matching")


class ApplyWeightsResponse(BaseModel):
    """Response model for applying weights."""

    vacancy_id: str
    weights_applied: dict[str, float]
    profile_used: Optional[str]
    candidates_affected: int
    processing_time_ms: float


class VersionHistoryResponse(BaseModel):
    """Response model for version history."""

    versions: list[dict[str, Any]]
    total_count: int


class NormalizeWeightsRequest(BaseModel):
    """Request model for normalizing weights."""

    keyword_weight: float = Field(..., ge=0)
    tfidf_weight: float = Field(..., ge=0)
    vector_weight: float = Field(..., ge=0)


class NormalizedWeightsResponse(BaseModel):
    """Response model for normalized weights."""

    keyword_weight: float
    tfidf_weight: float
    vector_weight: float
    original_sum: float
    normalized: bool


# ==================== Helper Functions ====================


def _extract_locale(request: Optional[Request]) -> str:
    """Extract Accept-Language header from request."""
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


def _model_to_response(profile: MatchingWeightProfile) -> MatchingWeightsResponse:
    """Convert database model to API response."""
    return MatchingWeightsResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        organization_id=str(profile.organization_id) if profile.organization_id else None,
        vacancy_id=str(profile.vacancy_id) if profile.vacancy_id else None,
        is_preset=profile.is_preset,
        is_active=profile.is_active,
        keyword_weight=profile.keyword_weight,
        tfidf_weight=profile.tfidf_weight,
        vector_weight=profile.vector_weight,
        weights_percentage=profile.get_weights_as_percentage(),
        version=profile.version,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        created_by=str(profile.created_by) if profile.created_by else None,
        updated_by=str(profile.updated_by) if profile.updated_by else None,
    )


def _create_version_entry(
    profile: MatchingWeightProfile,
    changed_by: Optional[str],
    version: str,
    change_reason: Optional[str],
) -> MatchingWeightVersion:
    """Create a version history entry."""
    return MatchingWeightVersion(
        profile_id=profile.id,
        keyword_weight=profile.keyword_weight,
        tfidf_weight=profile.tfidf_weight,
        vector_weight=profile.vector_weight,
        changed_by=changed_by,
        version=version,
        change_reason=change_reason,
    )


def _increment_version(current_version: Optional[str]) -> str:
    """Increment version string."""
    if not current_version:
        return "v1.0"

    try:
        # Handle v1.0 format
        if current_version.startswith("v"):
            parts = current_version[1:].split(".")
            if len(parts) == 2:
                major = int(parts[0])
                minor = int(parts[1])
                return f"v{major}.{minor + 1}"
    except (ValueError, IndexError):
        pass

    return f"{current_version}-updated"


# ==================== API Endpoints ====================


@router.get(
    "/profiles",
    response_model=MatchingWeightsListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def list_weight_profiles(
    request: Request,
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy"),
    is_preset: Optional[bool] = Query(None, description="Filter by preset status"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> MatchingWeightsListResponse:
    """
    List all matching weight profiles.

    Returns custom profiles and system presets with filtering options.
    """
    locale = _extract_locale(request)

    try:
        query = select(MatchingWeightProfile)

        # Apply filters
        filters = []
        if organization_id:
            filters.append(MatchingWeightProfile.organization_id == UUID(organization_id))
        if vacancy_id:
            filters.append(MatchingWeightProfile.vacancy_id == UUID(vacancy_id))
        if is_preset is not None:
            filters.append(MatchingWeightProfile.is_preset == is_preset)
        if is_active is not None:
            filters.append(MatchingWeightProfile.is_active == is_active)

        if filters:
            query = query.where(*filters)

        query = query.order_by(MatchingWeightProfile.name)

        result = await db.execute(query)
        profiles = result.scalars().all()

        # Get counts
        preset_count = sum(1 for p in profiles if p.is_preset)
        custom_count = len(profiles) - preset_count

        return MatchingWeightsListResponse(
            profiles=[_model_to_response(p) for p in profiles],
            total_count=len(profiles),
            preset_count=preset_count,
            custom_count=custom_count,
        )

    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except Exception as e:
        logger.error(f"Error listing weight profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.get(
    "/profiles/presets",
    response_model=PresetsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def get_preset_profiles(
    request: Request,
) -> PresetsResponse:
    """
    Get all preset weight profiles.

    Returns system-defined preset profiles (Technical, Creative, Executive, Balanced).
    """
    locale = _extract_locale(request)

    preset_descriptions = {
        "Technical": "Use for technical roles requiring precise skill matching (e.g., developers, engineers). "
                    "Higher keyword weight ensures exact skill requirements are met.",
        "Creative": "Use for creative roles requiring conceptual understanding (e.g., designers, copywriters). "
                   "Higher vector weight captures semantic similarity and creative transferability.",
        "Executive": "Use for executive roles requiring comprehensive evaluation. "
                    "Balanced approach considers skills, experience, and leadership qualities.",
        "Balanced": "Use when unsure of the best approach or for generalist roles. "
                   "Even distribution across all matching methods.",
    }

    presets = []
    for preset in PRESET_PROFILES:
        percentages = {
            "keyword": round(preset["keyword_weight"] * 100),
            "tfidf": round(preset["tfidf_weight"] * 100),
            "vector": round(preset["vector_weight"] * 100),
        }
        presets.append(PresetProfileResponse(
            name=preset["name"],
            description=preset["description"],
            keyword_weight=preset["keyword_weight"],
            tfidf_weight=preset["tfidf_weight"],
            vector_weight=preset["vector_weight"],
            weights_percentage=percentages,
            use_case=preset_descriptions.get(preset["name"], ""),
        ))

    return PresetsResponse(presets=presets)


@router.get(
    "/profiles/{profile_id}",
    response_model=MatchingWeightsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def get_weight_profile(
    profile_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MatchingWeightsResponse:
    """Get a specific weight profile by ID."""
    locale = _extract_locale(request)

    try:
        result = await db.execute(
            select(MatchingWeightProfile).where(MatchingWeightProfile.id == UUID(profile_id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_message("profile_not_found", locale),
            )

        return _model_to_response(profile)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weight profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.post(
    "/profiles",
    response_model=MatchingWeightsResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Matching Weights"],
)
async def create_weight_profile(
    profile_data: MatchingWeightsCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MatchingWeightsResponse:
    """
    Create a custom weight profile.

    Creates a new custom weight profile for an organization or vacancy.
    Weights must sum to 1.0.
    """
    locale = _extract_locale(request)

    try:
        # Check for vacancy-specific profile conflict
        if profile_data.vacancy_id:
            existing = await db.execute(
                select(MatchingWeightProfile).where(
                    MatchingWeightProfile.vacancy_id == UUID(profile_data.vacancy_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=get_error_message("vacancy_profile_exists", locale),
                )

        # Check for duplicate name within organization
        if profile_data.organization_id:
            existing = await db.execute(
                select(MatchingWeightProfile).where(
                    and_(
                        MatchingWeightProfile.organization_id == UUID(profile_data.organization_id),
                        MatchingWeightProfile.name == profile_data.name,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=get_error_message("profile_name_exists", locale),
                )

        # Create new profile
        profile = MatchingWeightProfile(
            name=profile_data.name,
            description=profile_data.description,
            organization_id=UUID(profile_data.organization_id) if profile_data.organization_id else None,
            vacancy_id=UUID(profile_data.vacancy_id) if profile_data.vacancy_id else None,
            keyword_weight=profile_data.keyword_weight,
            tfidf_weight=profile_data.tfidf_weight,
            vector_weight=profile_data.vector_weight,
            is_preset=False,
            is_active=True,
            version="v1.0",
            change_reason=profile_data.change_reason,
        )

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        logger.info(f"Created weight profile: {profile.id} - {profile.name}")

        return _model_to_response(profile)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating weight profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.put(
    "/profiles/{profile_id}",
    response_model=MatchingWeightsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def update_weight_profile(
    profile_id: str,
    profile_data: MatchingWeightsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MatchingWeightsResponse:
    """
    Update a weight profile.

    Updates an existing custom weight profile. Cannot modify preset profiles.
    Creates a version history entry for tracking changes.
    """
    locale = _extract_locale(request)

    try:
        result = await db.execute(
            select(MatchingWeightProfile).where(MatchingWeightProfile.id == UUID(profile_id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_message("profile_not_found", locale),
            )

        if profile.is_preset:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_error_message("cannot_modify_preset", locale),
            )

        # Store old values for version history
        old_weights = {
            "keyword_weight": profile.keyword_weight,
            "tfidf_weight": profile.tfidf_weight,
            "vector_weight": profile.vector_weight,
        }

        # Track if weights changed
        weights_changed = False

        # Update fields
        if profile_data.name is not None:
            profile.name = profile_data.name
        if profile_data.description is not None:
            profile.description = profile_data.description
        if profile_data.is_active is not None:
            profile.is_active = profile_data.is_active

        # Update weights if provided
        if profile_data.keyword_weight is not None:
            profile.keyword_weight = profile_data.keyword_weight
            weights_changed = True
        if profile_data.tfidf_weight is not None:
            profile.tfidf_weight = profile_data.tfidf_weight
            weights_changed = True
        if profile_data.vector_weight is not None:
            profile.vector_weight = profile_data.vector_weight
            weights_changed = True

        # Validate weights if changed
        if weights_changed:
            if not profile.validate_weights():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_error_message("weights_must_sum_to_1", locale),
                )

        # Increment version
        profile.version = _increment_version(profile.version)
        profile.change_reason = profile_data.change_reason

        # Create version history entry
        new_version = _create_version_entry(
            profile,
            changed_by=None,  # Could be extracted from auth token
            version=profile.version,
            change_reason=profile_data.change_reason,
        )
        db.add(new_version)

        await db.commit()
        await db.refresh(profile)

        logger.info(f"Updated weight profile: {profile.id} - {profile.name}")

        return _model_to_response(profile)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating weight profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Matching Weights"],
)
async def delete_weight_profile(
    profile_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a custom weight profile. Preset profiles cannot be deleted."""
    locale = _extract_locale(request)

    try:
        result = await db.execute(
            select(MatchingWeightProfile).where(MatchingWeightProfile.id == UUID(profile_id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_message("profile_not_found", locale),
            )

        if profile.is_preset:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_error_message("cannot_delete_preset", locale),
            )

        await db.delete(profile)
        await db.commit()

        logger.info(f"Deleted weight profile: {profile_id}")

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting weight profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.get(
    "/profiles/{profile_id}/history",
    response_model=VersionHistoryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def get_profile_history(
    profile_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> VersionHistoryResponse:
    """Get version history for a weight profile."""
    locale = _extract_locale(request)

    try:
        # Verify profile exists
        profile_result = await db.execute(
            select(MatchingWeightProfile).where(MatchingWeightProfile.id == UUID(profile_id))
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_message("profile_not_found", locale),
            )

        # Get version history
        result = await db.execute(
            select(MatchingWeightVersion)
            .where(MatchingWeightVersion.profile_id == UUID(profile_id))
            .order_by(MatchingWeightVersion.created_at.desc())
        )
        versions = result.scalars().all()

        version_data = []
        for v in versions:
            version_data.append({
                "id": str(v.id),
                "version": v.version,
                "keyword_weight": v.keyword_weight,
                "tfidf_weight": v.tfidf_weight,
                "vector_weight": v.vector_weight,
                "changed_by": str(v.changed_by) if v.changed_by else None,
                "change_reason": v.change_reason,
                "created_at": v.created_at.isoformat(),
            })

        return VersionHistoryResponse(
            versions=version_data,
            total_count=len(version_data),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )


@router.post(
    "/normalize",
    response_model=NormalizedWeightsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def normalize_weights(
    weights: NormalizeWeightsRequest,
) -> NormalizedWeightsResponse:
    """
    Normalize weights so they sum to 1.0.

    Useful when adjusting weights manually to ensure they remain valid.
    """
    total = weights.keyword_weight + weights.tfidf_weight + weights.vector_weight

    if abs(total - 1.0) < 0.01:
        # Already normalized
        return NormalizedWeightsResponse(
            keyword_weight=weights.keyword_weight,
            tfidf_weight=weights.tfidf_weight,
            vector_weight=weights.vector_weight,
            original_sum=total,
            normalized=False,
        )

    # Normalize
    normalized_kw = round(weights.keyword_weight / total, 3)
    normalized_tfidf = round(weights.tfidf_weight / total, 3)
    normalized_vec = round(weights.vector_weight / total, 3)

    return NormalizedWeightsResponse(
        keyword_weight=normalized_kw,
        tfidf_weight=normalized_tfidf,
        vector_weight=normalized_vec,
        original_sum=total,
        normalized=True,
    )


@router.post(
    "/apply",
    response_model=ApplyWeightsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching Weights"],
)
async def apply_weights(
    request_data: ApplyWeightsRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApplyWeightsResponse:
    """
    Apply custom weights to a vacancy and optionally re-match candidates.

    Either a profile_id or custom weights must be provided.
    If re_match_candidates is true, triggers background re-matching.
    """
    import time

    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        # Get weights to apply
        weights_to_apply = {}
        profile_used = None

        if request_data.profile_id:
            # Load profile
            result = await db.execute(
                select(MatchingWeightProfile).where(
                    MatchingWeightProfile.id == UUID(request_data.profile_id)
                )
            )
            profile = result.scalar_one_or_none()

            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=get_error_message("profile_not_found", locale),
                )

            weights_to_apply = profile.get_weights_as_dict()
            profile_used = profile.name

        elif request_data.weights:
            # Use custom weights
            profile_result = await db.execute(
                select(MatchingWeightProfile).where(
                    MatchingWeightProfile.vacancy_id == UUID(request_data.vacancy_id)
                )
            )
            existing_profile = profile_result.scalar_one_or_none()

            weights_to_apply = {
                "keyword_weight": (
                    request_data.weights.keyword_weight
                    if request_data.weights.keyword_weight is not None
                    else (existing_profile.keyword_weight if existing_profile else 0.5)
                ),
                "tfidf_weight": (
                    request_data.weights.tfidf_weight
                    if request_data.weights.tfidf_weight is not None
                    else (existing_profile.tfidf_weight if existing_profile else 0.3)
                ),
                "vector_weight": (
                    request_data.weights.vector_weight
                    if request_data.weights.vector_weight is not None
                    else (existing_profile.vector_weight if existing_profile else 0.2)
                ),
            }

            total = sum(weights_to_apply.values())
            if abs(total - 1.0) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_error_message("weights_must_sum_to_1", locale),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either profile_id or weights must be provided",
            )

        # Get vacancy
        vacancy_result = await db.execute(
            select(MatchingWeightProfile).where(
                MatchingWeightProfile.vacancy_id == UUID(request_data.vacancy_id)
            )
        )
        # ... (implement re-matching logic)

        processing_time_ms = (time.time() - start_time) * 1000

        return ApplyWeightsResponse(
            vacancy_id=request_data.vacancy_id,
            weights_applied=weights_to_apply,
            profile_used=profile_used,
            candidates_affected=0,  # To be implemented with re-matching
            processing_time_ms=round(processing_time_ms, 2),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_message("invalid_uuid", locale),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying weights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("database_error", locale),
        )
