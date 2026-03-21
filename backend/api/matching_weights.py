"""
Matching algorithm weight management endpoints.

This module provides endpoints for managing custom matching algorithm weight configurations,
allowing organizations to customize how keyword, TF-IDF, and vector similarity scores
are combined for resume-job matching.
"""
import logging
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.matching_weights_profile import MatchingWeightsProfile
from models.matching_weights_history import MatchingWeightsHistory
from models.ranking_features_weights import RankingFeaturesWeights

logger = logging.getLogger(__name__)

router = APIRouter()


def normalize_weights(keyword_weight: float, tfidf_weight: float, vector_weight: float) -> tuple[float, float, float]:
    """
    Normalize weights so they sum to 1.0.

    If the weights already sum to 1.0 (within a small tolerance), they are returned as-is.
    Otherwise, they are scaled proportionally.

    Args:
        keyword_weight: Weight for keyword matching
        tfidf_weight: Weight for TF-IDF matching
        vector_weight: Weight for vector similarity matching

    Returns:
        Tuple of normalized (keyword_weight, tfidf_weight, vector_weight)
    """
    total = keyword_weight + tfidf_weight + vector_weight

    # If weights sum to approximately 1.0, return as-is
    if abs(total - 1.0) < 0.0001:
        return keyword_weight, tfidf_weight, vector_weight

    # Scale weights proportionally
    if total > 0:
        return (
            keyword_weight / total,
            tfidf_weight / total,
            vector_weight / total,
        )
    else:
        # If all weights are 0, return balanced defaults
        return (0.33, 0.33, 0.34)


# Preset type literal
PresetType = Literal["technical", "creative", "executive", "balanced"]

# Change type literal for history tracking
ChangeType = Literal["create", "update", "delete"]


class MatchingWeightsProfileCreate(BaseModel):
    """Request model for creating a matching weights profile."""

    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for this profile", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)
    keyword_weight: float = Field(..., description="Weight for keyword matching (0.0 to 1.0)", ge=0.0, le=1.0)
    tfidf_weight: float = Field(..., description="Weight for TF-IDF matching (0.0 to 1.0)", ge=0.0, le=1.0)
    vector_weight: float = Field(..., description="Weight for vector similarity matching (0.0 to 1.0)", ge=0.0, le=1.0)
    is_default: bool = Field(False, description="Whether this is the default profile for the organization")
    is_preset: bool = Field(False, description="Whether this is a system preset profile")
    preset_type: Optional[PresetType] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who is creating this profile")

    @field_validator("keyword_weight", "tfidf_weight", "vector_weight")
    @classmethod
    def validate_weights(cls, v: float, info) -> float:
        """Validate that weights are within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v

    @field_validator("preset_type")
    @classmethod
    def validate_preset_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that preset_type is only set if is_preset is True."""
        if v is not None and not info.data.get("is_preset", False):
            raise ValueError("preset_type can only be set for preset profiles")
        return v


class MatchingWeightsProfileUpdate(BaseModel):
    """Request model for updating a matching weights profile."""

    name: Optional[str] = Field(None, description="Human-readable name for this profile", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)
    keyword_weight: Optional[float] = Field(None, description="Weight for keyword matching (0.0 to 1.0)", ge=0.0, le=1.0)
    tfidf_weight: Optional[float] = Field(None, description="Weight for TF-IDF matching (0.0 to 1.0)", ge=0.0, le=1.0)
    vector_weight: Optional[float] = Field(None, description="Weight for vector similarity matching (0.0 to 1.0)", ge=0.0, le=1.0)
    is_default: Optional[bool] = Field(None, description="Whether this is the default profile for the organization")


class MatchingWeightsProfileResponse(BaseModel):
    """Response model for a single matching weights profile."""

    id: str = Field(..., description="Unique identifier for the profile")
    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for this profile")
    description: Optional[str] = Field(None, description="Description of when to use this profile")
    keyword_weight: float = Field(..., description="Weight for keyword matching")
    tfidf_weight: float = Field(..., description="Weight for TF-IDF matching")
    vector_weight: float = Field(..., description="Weight for vector similarity matching")
    is_default: bool = Field(..., description="Whether this is the default profile")
    is_preset: bool = Field(..., description="Whether this is a system preset")
    preset_type: Optional[str] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who created this profile")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class MatchingWeightsListResponse(BaseModel):
    """Response model for listing matching weights profiles."""

    organization_id: Optional[str] = Field(None, description="Organization ID filter used")
    profiles: List[MatchingWeightsProfileResponse] = Field(..., description="List of weight profiles")
    total_count: int = Field(..., description="Total number of profiles")


class RematchRequest(BaseModel):
    """Request model for triggering candidate re-matching."""

    vacancy_id: str = Field(..., description="Vacancy ID to re-match candidates against")


class RematchResponse(BaseModel):
    """Response model for re-matching operation."""

    vacancy_id: str = Field(..., description="Vacancy ID that was re-matched")
    profile_id: str = Field(..., description="Weight profile used for re-matching")
    candidates_matched: int = Field(..., description="Number of candidates re-matched")
    status: str = Field(..., description="Status of the re-matching operation")


class CompareWeightsRequest(BaseModel):
    """Request model for comparing two weight profiles."""

    profile_a_id: str = Field(..., description="First profile ID to compare")
    profile_b_id: str = Field(..., description="Second profile ID to compare")
    vacancy_id: str = Field(..., description="Vacancy ID to compare matching results for")


class CompareWeightsResponse(BaseModel):
    """Response model for weight profile comparison."""

    vacancy_id: str = Field(..., description="Vacancy ID used for comparison")
    profile_a: MatchingWeightsProfileResponse = Field(..., description="First profile configuration")
    profile_b: MatchingWeightsProfileResponse = Field(..., description="Second profile configuration")
    differences: List[dict] = Field(..., description="List of candidate score differences between profiles")


# Ranking Features Profile Schemas (13 weight fields)


class RankingFeaturesProfileCreate(BaseModel):
    """Request model for creating a ranking features profile with 13 weight fields."""

    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for this profile", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)
    skill_match_weight: float = Field(..., description="Weight for skill matching (0.0 to 1.0)", ge=0.0, le=1.0)
    experience_weight: float = Field(..., description="Weight for experience matching (0.0 to 1.0)", ge=0.0, le=1.0)
    education_weight: float = Field(..., description="Weight for education matching (0.0 to 1.0)", ge=0.0, le=1.0)
    location_weight: float = Field(..., description="Weight for location matching (0.0 to 1.0)", ge=0.0, le=1.0)
    keyword_weight: float = Field(..., description="Weight for keyword matching (0.0 to 1.0)", ge=0.0, le=1.0)
    tfidf_weight: float = Field(..., description="Weight for TF-IDF matching (0.0 to 1.0)", ge=0.0, le=1.0)
    vector_weight: float = Field(..., description="Weight for vector similarity matching (0.0 to 1.0)", ge=0.0, le=1.0)
    recency_weight: float = Field(..., description="Weight for recency (0.0 to 1.0)", ge=0.0, le=1.0)
    culture_fit_weight: float = Field(..., description="Weight for culture fit (0.0 to 1.0)", ge=0.0, le=1.0)
    salary_match_weight: float = Field(..., description="Weight for salary matching (0.0 to 1.0)", ge=0.0, le=1.0)
    availability_weight: float = Field(..., description="Weight for availability (0.0 to 1.0)", ge=0.0, le=1.0)
    certifications_weight: float = Field(..., description="Weight for certifications (0.0 to 1.0)", ge=0.0, le=1.0)
    industry_experience_weight: float = Field(..., description="Weight for industry experience (0.0 to 1.0)", ge=0.0, le=1.0)
    is_default: bool = Field(False, description="Whether this is the default profile for the organization")
    is_preset: bool = Field(False, description="Whether this is a system preset profile")
    preset_type: Optional[PresetType] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who is creating this profile")

    @field_validator(
        "skill_match_weight",
        "experience_weight",
        "education_weight",
        "location_weight",
        "keyword_weight",
        "tfidf_weight",
        "vector_weight",
        "recency_weight",
        "culture_fit_weight",
        "salary_match_weight",
        "availability_weight",
        "certifications_weight",
        "industry_experience_weight",
    )
    @classmethod
    def validate_weights(cls, v: float, info) -> float:
        """Validate that weights are within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v

    @field_validator("preset_type")
    @classmethod
    def validate_preset_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that preset_type is only set if is_preset is True."""
        if v is not None and not info.data.get("is_preset", False):
            raise ValueError("preset_type can only be set for preset profiles")
        return v


class RankingFeaturesProfileUpdate(BaseModel):
    """Request model for updating a ranking features profile."""

    name: Optional[str] = Field(None, description="Human-readable name for this profile", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of when to use this profile", max_length=1000)
    skill_match_weight: Optional[float] = Field(None, description="Weight for skill matching (0.0 to 1.0)", ge=0.0, le=1.0)
    experience_weight: Optional[float] = Field(None, description="Weight for experience matching (0.0 to 1.0)", ge=0.0, le=1.0)
    education_weight: Optional[float] = Field(None, description="Weight for education matching (0.0 to 1.0)", ge=0.0, le=1.0)
    location_weight: Optional[float] = Field(None, description="Weight for location matching (0.0 to 1.0)", ge=0.0, le=1.0)
    keyword_weight: Optional[float] = Field(None, description="Weight for keyword matching (0.0 to 1.0)", ge=0.0, le=1.0)
    tfidf_weight: Optional[float] = Field(None, description="Weight for TF-IDF matching (0.0 to 1.0)", ge=0.0, le=1.0)
    vector_weight: Optional[float] = Field(None, description="Weight for vector similarity matching (0.0 to 1.0)", ge=0.0, le=1.0)
    recency_weight: Optional[float] = Field(None, description="Weight for recency (0.0 to 1.0)", ge=0.0, le=1.0)
    culture_fit_weight: Optional[float] = Field(None, description="Weight for culture fit (0.0 to 1.0)", ge=0.0, le=1.0)
    salary_match_weight: Optional[float] = Field(None, description="Weight for salary matching (0.0 to 1.0)", ge=0.0, le=1.0)
    availability_weight: Optional[float] = Field(None, description="Weight for availability (0.0 to 1.0)", ge=0.0, le=1.0)
    certifications_weight: Optional[float] = Field(None, description="Weight for certifications (0.0 to 1.0)", ge=0.0, le=1.0)
    industry_experience_weight: Optional[float] = Field(None, description="Weight for industry experience (0.0 to 1.0)", ge=0.0, le=1.0)
    is_default: Optional[bool] = Field(None, description="Whether this is the default profile for the organization")


class RankingFeaturesProfileResponse(BaseModel):
    """Response model for a single ranking features profile."""

    id: str = Field(..., description="Unique identifier for the profile")
    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for this profile")
    description: Optional[str] = Field(None, description="Description of when to use this profile")
    skill_match_weight: float = Field(..., description="Weight for skill matching")
    experience_weight: float = Field(..., description="Weight for experience matching")
    education_weight: float = Field(..., description="Weight for education matching")
    location_weight: float = Field(..., description="Weight for location matching")
    keyword_weight: float = Field(..., description="Weight for keyword matching")
    tfidf_weight: float = Field(..., description="Weight for TF-IDF matching")
    vector_weight: float = Field(..., description="Weight for vector similarity matching")
    recency_weight: float = Field(..., description="Weight for recency")
    culture_fit_weight: float = Field(..., description="Weight for culture fit")
    salary_match_weight: float = Field(..., description="Weight for salary matching")
    availability_weight: float = Field(..., description="Weight for availability")
    certifications_weight: float = Field(..., description="Weight for certifications")
    industry_experience_weight: float = Field(..., description="Weight for industry experience")
    is_default: bool = Field(..., description="Whether this is the default profile")
    is_preset: bool = Field(..., description="Whether this is a system preset")
    preset_type: Optional[str] = Field(None, description="Type of preset if applicable")
    created_by: Optional[str] = Field(None, description="User ID who created this profile")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


@router.post(
    "/",
    response_model=MatchingWeightsProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Matching Weights"],
)
async def create_matching_weights_profile(
    request: MatchingWeightsProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a custom matching weights profile for an organization.

    This endpoint creates a new weight profile that specifies how keyword, TF-IDF,
    and vector similarity scores should be combined when matching resumes to jobs.

    Weights will be auto-normalized to sum to 1.0 if they don't already.

    Args:
        request: Create request with profile configuration
        db: Database session

    Returns:
        JSON response with created profile details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org123",
        ...     "name": "Technical Role Focus",
        ...     "description": "Emphasizes exact skill matching for technical positions",
        ...     "keyword_weight": 0.6,
        ...     "tfidf_weight": 0.3,
        ...     "vector_weight": 0.1,
        ...     "is_default": False,
        ...     "created_by": "user456"
        ... }
        >>> response = requests.post("/api/matching-weights/", json=data)
        >>> response.json()
    """
    try:
        logger.info(
            f"Creating matching weights profile '{request.name}' "
            f"for organization: {request.organization_id}"
        )

        # Validate organization_id
        if not request.organization_id or len(request.organization_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization ID cannot be empty",
            )

        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile name cannot be empty",
            )

        # Check for duplicate profile name in the same organization
        existing_profile = await db.execute(
            select(MatchingWeightsProfile).where(
                MatchingWeightsProfile.organization_id == request.organization_id,
                MatchingWeightsProfile.name == request.name,
            )
        )
        if existing_profile.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile with name '{request.name}' already exists for this organization",
            )

        # Normalize weights to sum to 1.0
        normalized_keyword, normalized_tfidf, normalized_vector = normalize_weights(
            request.keyword_weight,
            request.tfidf_weight,
            request.vector_weight,
        )

        if (normalized_keyword, normalized_tfidf, normalized_vector) != (
            request.keyword_weight,
            request.tfidf_weight,
            request.vector_weight,
        ):
            logger.info(
                f"Normalized weights from ({request.keyword_weight}, {request.tfidf_weight}, {request.vector_weight}) "
                f"to ({normalized_keyword}, {normalized_tfidf}, {normalized_vector})"
            )

        # Create new profile with UUID
        profile_id = str(uuid4())
        new_profile = MatchingWeightsProfile(
            id=profile_id,
            organization_id=request.organization_id,
            name=request.name,
            description=request.description,
            keyword_weight=normalized_keyword,
            tfidf_weight=normalized_tfidf,
            vector_weight=normalized_vector,
            is_default=request.is_default,
            is_preset=request.is_preset,
            preset_type=request.preset_type,
            created_by=request.created_by,
        )
        db.add(new_profile)
        await db.flush()

        # Create history entry for the creation
        history_entry = MatchingWeightsHistory(
            profile_id=new_profile.id,
            organization_id=new_profile.organization_id,
            change_type="create",
            changed_by=request.created_by,
            old_name=None,
            new_name=new_profile.name,
            old_description=None,
            new_description=new_profile.description,
            old_keyword_weight=None,
            new_keyword_weight=new_profile.keyword_weight,
            old_tfidf_weight=None,
            new_tfidf_weight=new_profile.tfidf_weight,
            old_vector_weight=None,
            new_vector_weight=new_profile.vector_weight,
            old_is_default=None,
            new_is_default=new_profile.is_default,
        )
        db.add(history_entry)

        response_data = {
            "id": new_profile.id,
            "organization_id": new_profile.organization_id,
            "name": new_profile.name,
            "description": new_profile.description,
            "keyword_weight": new_profile.keyword_weight,
            "tfidf_weight": new_profile.tfidf_weight,
            "vector_weight": new_profile.vector_weight,
            "is_default": new_profile.is_default,
            "is_preset": new_profile.is_preset,
            "preset_type": new_profile.preset_type,
            "created_by": new_profile.created_by,
            "created_at": new_profile.created_at.isoformat(),
            "updated_at": new_profile.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(
            f"Created matching weights profile '{request.name}' "
            f"for organization: {request.organization_id} with ID: {new_profile.id}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating matching weights profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create matching weights profile: {str(e)}",
        ) from e


@router.get("/", tags=["Matching Weights"])
async def list_matching_weights_profiles(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    is_preset: Optional[bool] = Query(None, description="Filter by preset status"),
    preset_type: Optional[PresetType] = Query(None, description="Filter by preset type"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List matching weights profiles with optional filters.

    This endpoint retrieves matching weights profiles with support for filtering
    by organization, default status, preset status, and preset type.

    Args:
        organization_id: Optional organization ID filter
        is_default: Optional default status filter
        is_preset: Optional preset status filter
        preset_type: Optional preset type filter
        db: Database session

    Returns:
        JSON response with list of weight profiles

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/matching-weights/?organization_id=org123")
        >>> response.json()
        {
            "organization_id": "org123",
            "profiles": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(
            f"Listing matching weights profiles with filters - "
            f"organization_id: {organization_id}, is_default: {is_default}, "
            f"is_preset: {is_preset}, preset_type: {preset_type}"
        )

        # If querying for preset profiles, use RankingFeaturesWeights table (13 weights)
        # Otherwise, use MatchingWeightsProfile table (3 weights) for backward compatibility
        if is_preset is True:
            # Build query for 13-weight ranking features profiles
            query = select(RankingFeaturesWeights)

            if organization_id is not None:
                query = query.where(RankingFeaturesWeights.organization_id == organization_id)

            if is_default is not None:
                query = query.where(RankingFeaturesWeights.is_default == is_default)

            query = query.where(RankingFeaturesWeights.is_preset == True)

            if preset_type is not None:
                query = query.where(RankingFeaturesWeights.preset_type == preset_type)

            query = query.order_by(RankingFeaturesWeights.name)

            result = await db.execute(query)
            profiles = result.scalars().all()

            # Build response with all 13 weight fields
            profiles_data = []
            for profile in profiles:
                profiles_data.append({
                    "id": str(profile.id),
                    "organization_id": profile.organization_id,
                    "name": profile.name,
                    "description": profile.description,
                    "skill_match_weight": profile.skill_match_weight,
                    "experience_weight": profile.experience_weight,
                    "education_weight": profile.education_weight,
                    "location_weight": profile.location_weight,
                    "keyword_weight": profile.keyword_weight,
                    "tfidf_weight": profile.tfidf_weight,
                    "vector_weight": profile.vector_weight,
                    "recency_weight": profile.recency_weight,
                    "culture_fit_weight": profile.culture_fit_weight,
                    "salary_match_weight": profile.salary_match_weight,
                    "availability_weight": profile.availability_weight,
                    "certifications_weight": profile.certifications_weight,
                    "industry_experience_weight": profile.industry_experience_weight,
                    "is_default": profile.is_default,
                    "is_preset": profile.is_preset,
                    "preset_type": profile.preset_type,
                    "created_by": profile.created_by,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                })
        else:
            # Build query for 3-weight matching profiles
            query = select(MatchingWeightsProfile)

            if organization_id is not None:
                query = query.where(MatchingWeightsProfile.organization_id == organization_id)

            if is_default is not None:
                query = query.where(MatchingWeightsProfile.is_default == is_default)

            if is_preset is not None:
                query = query.where(MatchingWeightsProfile.is_preset == is_preset)

            if preset_type is not None:
                query = query.where(MatchingWeightsProfile.preset_type == preset_type)

            query = query.order_by(MatchingWeightsProfile.name)

            result = await db.execute(query)
            profiles = result.scalars().all()

            # Build response with 3 weight fields
            profiles_data = []
            for profile in profiles:
                profiles_data.append({
                    "id": str(profile.id),
                    "organization_id": profile.organization_id,
                    "name": profile.name,
                    "description": profile.description,
                    "keyword_weight": profile.keyword_weight,
                    "tfidf_weight": profile.tfidf_weight,
                    "vector_weight": profile.vector_weight,
                    "is_default": profile.is_default,
                    "is_preset": profile.is_preset,
                    "preset_type": profile.preset_type,
                    "created_by": profile.created_by,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                })

        response_data = {
            "organization_id": organization_id,
            "profiles": profiles_data,
            "total_count": len(profiles_data),
        }

        logger.info(f"Retrieved {len(profiles_data)} matching weights profiles")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing matching weights profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list matching weights profiles: {str(e)}",
        ) from e


@router.get("/{profile_id}", tags=["Matching Weights"])
async def get_matching_weights_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Retrieve a specific matching weights profile by ID.

    This endpoint retrieves detailed information about a single matching weights profile,
    including the weight configuration for keyword, TF-IDF, and vector similarity matching.

    Args:
        profile_id: UUID of the profile to retrieve
        db: Database session

    Returns:
        JSON response with profile details

    Raises:
        HTTPException(404): If profile not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/matching-weights/abc-123-def")
        >>> response.json()
        {
            "id": "abc-123-def",
            "organization_id": "org123",
            "name": "Technical Role Focus",
            "keyword_weight": 0.6,
            "tfidf_weight": 0.3,
            "vector_weight": 0.1,
            ...
        }
    """
    try:
        logger.info(f"Retrieving matching weights profile: {profile_id}")

        result = await db.execute(
            select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matching weights profile not found: {profile_id}",
            )

        response_data = {
            "id": profile.id,
            "organization_id": profile.organization_id,
            "name": profile.name,
            "description": profile.description,
            "keyword_weight": profile.keyword_weight,
            "tfidf_weight": profile.tfidf_weight,
            "vector_weight": profile.vector_weight,
            "is_default": profile.is_default,
            "is_preset": profile.is_preset,
            "preset_type": profile.preset_type,
            "created_by": profile.created_by,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

        logger.info(f"Retrieved matching weights profile: {profile_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving matching weights profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve matching weights profile: {str(e)}",
        ) from e


@router.put("/{profile_id}", tags=["Matching Weights"])
async def update_matching_weights_profile(
    profile_id: str,
    request: MatchingWeightsProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a matching weights profile.

    Only the fields specified in the request will be updated.
    Weights will be auto-normalized to sum to 1.0 if they don't already.

    Args:
        profile_id: UUID of the profile to update
        request: Update request with fields to modify
        db: Database session

    Returns:
        JSON response with updated profile details

    Raises:
        HTTPException(404): If profile not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"keyword_weight": 0.7, "tfidf_weight": 0.2, "vector_weight": 0.1}
        >>> response = requests.put("/api/matching-weights/abc-123-def", json=data)
        >>> response.json()
    """
    try:
        logger.info(f"Updating matching weights profile: {profile_id}")

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # Validate that at least one field is being updated
        if all(
            v is None
            for v in [
                request.name,
                request.description,
                request.keyword_weight,
                request.tfidf_weight,
                request.vector_weight,
                request.is_default,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update",
            )

        # Get existing profile
        result = await db.execute(
            select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matching weights profile not found: {profile_id}",
            )

        # Store old values for history tracking
        old_name = profile.name
        old_description = profile.description
        old_keyword_weight = profile.keyword_weight
        old_tfidf_weight = profile.tfidf_weight
        old_vector_weight = profile.vector_weight
        old_is_default = profile.is_default

        # Track what changed
        changes_made = False

        # Check for duplicate name if name is being changed
        if request.name is not None and request.name != profile.name:
            existing_profile = await db.execute(
                select(MatchingWeightsProfile).where(
                    MatchingWeightsProfile.organization_id == profile.organization_id,
                    MatchingWeightsProfile.name == request.name,
                    MatchingWeightsProfile.id != profile_id,
                )
            )
            if existing_profile.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Profile with name '{request.name}' already exists for this organization",
                )

        # Update fields if provided
        if request.name is not None:
            profile.name = request.name
            changes_made = True

        if request.description is not None:
            profile.description = request.description
            changes_made = True

        # Track if weights are being updated for normalization
        weights_updated = False
        if request.keyword_weight is not None or request.tfidf_weight is not None or request.vector_weight is not None:
            # Get current weights if not provided
            current_keyword = profile.keyword_weight if request.keyword_weight is None else request.keyword_weight
            current_tfidf = profile.tfidf_weight if request.tfidf_weight is None else request.tfidf_weight
            current_vector = profile.vector_weight if request.vector_weight is None else request.vector_weight

            # Normalize weights
            normalized_keyword, normalized_tfidf, normalized_vector = normalize_weights(
                current_keyword,
                current_tfidf,
                current_vector,
            )

            # Apply normalized weights
            if request.keyword_weight is not None:
                profile.keyword_weight = normalized_keyword
            if request.tfidf_weight is not None:
                profile.tfidf_weight = normalized_tfidf
            if request.vector_weight is not None:
                profile.vector_weight = normalized_vector

            if (normalized_keyword, normalized_tfidf, normalized_vector) != (
                current_keyword,
                current_tfidf,
                current_vector,
            ):
                logger.info(
                    f"Normalized weights from ({current_keyword}, {current_tfidf}, {current_vector}) "
                    f"to ({normalized_keyword}, {normalized_tfidf}, {normalized_vector})"
                )

            weights_updated = True
            changes_made = True

        if request.is_default is not None:
            # If setting as default, unset other default profiles for the same organization
            if request.is_default:
                await db.execute(
                    update(MatchingWeightsProfile)
                    .where(
                        MatchingWeightsProfile.organization_id == profile.organization_id,
                        MatchingWeightsProfile.id != profile_id,
                        MatchingWeightsProfile.is_default == True,
                    )
                    .values(is_default=False)
                )
                logger.info(
                    f"Unset {len([p for p in [profile] if p.is_default])} other default profile(s) "
                    f"for organization: {profile.organization_id}"
                )
            profile.is_default = request.is_default
            changes_made = True

        await db.commit()
        await db.refresh(profile)

        # Create history entry for the update
        if changes_made:
            history_entry = MatchingWeightsHistory(
                profile_id=profile.id,
                organization_id=profile.organization_id,
                change_type="update",
                changed_by=profile.created_by,  # Using the profile's created_by as changed_by
                old_name=old_name if old_name != profile.name else None,
                new_name=profile.name if old_name != profile.name else None,
                old_description=old_description if old_description != profile.description else None,
                new_description=profile.description if old_description != profile.description else None,
                old_keyword_weight=old_keyword_weight if old_keyword_weight != profile.keyword_weight else None,
                new_keyword_weight=profile.keyword_weight if old_keyword_weight != profile.keyword_weight else None,
                old_tfidf_weight=old_tfidf_weight if old_tfidf_weight != profile.tfidf_weight else None,
                new_tfidf_weight=profile.tfidf_weight if old_tfidf_weight != profile.tfidf_weight else None,
                old_vector_weight=old_vector_weight if old_vector_weight != profile.vector_weight else None,
                new_vector_weight=profile.vector_weight if old_vector_weight != profile.vector_weight else None,
                old_is_default=old_is_default if old_is_default != profile.is_default else None,
                new_is_default=profile.is_default if old_is_default != profile.is_default else None,
            )
            db.add(history_entry)
            # Separate commit for history entry (already committed main changes)
            await db.commit()

        response_data = {
            "id": profile.id,
            "organization_id": profile.organization_id,
            "name": profile.name,
            "description": profile.description,
            "keyword_weight": profile.keyword_weight,
            "tfidf_weight": profile.tfidf_weight,
            "vector_weight": profile.vector_weight,
            "is_default": profile.is_default,
            "is_preset": profile.is_preset,
            "preset_type": profile.preset_type,
            "created_by": profile.created_by,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

        logger.info(f"Updated matching weights profile: {profile_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating matching weights profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update matching weights profile: {str(e)}",
        ) from e


@router.delete("/{profile_id}", tags=["Matching Weights"])
async def delete_matching_weights_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a matching weights profile.

    This endpoint permanently deletes a matching weights profile.
    Note: Default profiles and system presets cannot be deleted.

    Args:
        profile_id: UUID of the profile to delete
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If profile not found
        HTTPException(400): If profile cannot be deleted (default or preset)
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("/api/matching-weights/abc-123-def")
        >>> response.json()
        {
            "message": "Matching weights profile deleted successfully",
            "id": "abc-123-def"
        }
    """
    try:
        logger.info(f"Deleting matching weights profile: {profile_id}")

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # Check if profile exists
        result = await db.execute(
            select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matching weights profile not found: {profile_id}",
            )

        # Check if profile is a preset - presets cannot be deleted
        if profile.is_preset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System preset profiles cannot be deleted",
            )

        # Check if profile is the default - default profiles cannot be deleted
        if profile.is_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Default profiles cannot be deleted",
            )

        # Store profile data for history before deletion
        profile_for_history = profile

        # Create history entry before deleting
        history_entry = MatchingWeightsHistory(
            profile_id=profile_for_history.id,
            organization_id=profile_for_history.organization_id,
            change_type="delete",
            changed_by=profile_for_history.created_by,
            old_name=profile_for_history.name,
            new_name=None,
            old_description=profile_for_history.description,
            new_description=None,
            old_keyword_weight=profile_for_history.keyword_weight,
            new_keyword_weight=None,
            old_tfidf_weight=profile_for_history.tfidf_weight,
            new_tfidf_weight=None,
            old_vector_weight=profile_for_history.vector_weight,
            new_vector_weight=None,
            old_is_default=profile_for_history.is_default,
            new_is_default=None,
        )
        db.add(history_entry)

        # Delete the profile
        await db.execute(
            delete(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
        )
        await db.commit()

        logger.info(f"Deleted matching weights profile: {profile_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Matching weights profile deleted successfully",
                "id": profile_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting matching weights profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete matching weights profile: {str(e)}",
        ) from e


@router.post("/{profile_id}/set-active", tags=["Matching Weights"])
async def set_active_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Set a matching weights profile as the active/default profile for its organization.

    This endpoint sets the specified profile as the default profile for its organization,
    automatically unsetting any existing default profile for the same organization.

    Args:
        profile_id: UUID of the profile to set as active
        db: Database session

    Returns:
        JSON response with updated profile details

    Raises:
        HTTPException(404): If profile not found
        HTTPException(422): If profile_id is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/matching-weights/abc-123-def/set-active")
        >>> response.json()
        {
            "id": "abc-123-def",
            "organization_id": "org123",
            "name": "Technical Role Focus",
            "is_default": true,
            ...
        }
    """
    try:
        logger.info(f"Setting profile as active: {profile_id}")

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # Get the profile to set as active
        result = await db.execute(
            select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matching weights profile not found: {profile_id}",
            )

        # Update all other profiles in the organization to is_default=False
        from models.matching_weights_profile import MatchingWeightsProfile as MWP
        other_profiles_result = await db.execute(
            select(MWP).where(
                MWP.organization_id == profile.organization_id,
                MWP.id != profile_id,
                MWP.is_default == True,
            )
        )
        other_profiles = other_profiles_result.scalars().all()
        for other_profile in other_profiles:
            other_profile.is_default = False

        # Set the selected profile as active
        profile.is_default = True

        await db.commit()
        await db.refresh(profile)

        response_data = {
            "id": profile.id,
            "organization_id": profile.organization_id,
            "name": profile.name,
            "description": profile.description,
            "keyword_weight": profile.keyword_weight,
            "tfidf_weight": profile.tfidf_weight,
            "vector_weight": profile.vector_weight,
            "is_default": profile.is_default,
            "is_preset": profile.is_preset,
            "preset_type": profile.preset_type,
            "created_by": profile.created_by,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

        logger.info(f"Set profile as active: {profile_id} for organization: {profile.organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting profile as active: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set profile as active: {str(e)}",
        ) from e


@router.post("/{profile_id}/rematch", tags=["Matching Weights"])
async def rematch_candidates_with_profile(
    profile_id: str,
    request: RematchRequest,
) -> JSONResponse:
    """
    Re-match candidates for a vacancy using the specified weight profile.

    This endpoint triggers a re-calculation of match scores for all candidates
    associated with the given vacancy, using the weights from the specified profile.

    Args:
        profile_id: UUID of the weight profile to use for re-matching
        request: Request containing vacancy_id to re-match

    Returns:
        JSON response with re-matching results

    Raises:
        HTTPException(404): If profile or vacancy not found
        HTTPException(500): If re-matching operation fails

    Examples:
        >>> import requests
        >>> data = {"vacancy_id": "vacancy-uuid"}
        >>> response = requests.post("/api/matching-weights/profile-123/rematch", json=data)
        >>> response.json()
    """
    try:
        logger.info(
            f"Re-matching candidates for vacancy {request.vacancy_id} "
            f"using profile {profile_id}"
        )

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # Validate vacancy_id
        if not request.vacancy_id or len(request.vacancy_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Vacancy ID cannot be empty",
            )

        # For now, return placeholder response
        # Actual re-matching logic will be added in a later subtask
        response_data = {
            "vacancy_id": request.vacancy_id,
            "profile_id": profile_id,
            "candidates_matched": 0,
            "status": "completed",
        }

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-matching candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-match candidates: {str(e)}",
        ) from e


@router.post("/compare", tags=["Matching Weights"])
async def compare_weight_profiles(request: CompareWeightsRequest) -> JSONResponse:
    """
    Compare two weight profiles by analyzing their matching results for a vacancy.

    This A/B testing endpoint shows how candidate rankings differ between two
    weight profiles, helping recruiters choose the best configuration.

    The comparison calculates match scores for both profiles and shows:
    - Score differences for each candidate
    - Ranking changes between profiles
    - Which profile produces better matches for the vacancy

    Args:
        request: Request containing profile_a_id, profile_b_id, and vacancy_id

    Returns:
        JSON response with comparison results including profile configurations
        and candidate score differences

    Raises:
        HTTPException(404): If profiles or vacancy not found
        HTTPException(422): If validation fails
        HTTPException(500): If comparison operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "profile_a_id": "profile-a-uuid",
        ...     "profile_b_id": "profile-b-uuid",
        ...     "vacancy_id": "vacancy-uuid"
        ... }
        >>> response = requests.post("/api/matching-weights/compare", json=data)
        >>> comparison = response.json()
        >>> print(comparison['vacancy_id'])
        'vacancy-uuid'
        >>> for diff in comparison['differences']:
        ...     print(f"Candidate {diff['candidate_id']}: {diff['score_difference']:+.2f}")
    """
    try:
        logger.info(
            f"Comparing weight profiles A={request.profile_a_id} and B={request.profile_b_id} "
            f"for vacancy {request.vacancy_id}"
        )

        # Validate profile_a_id
        if not request.profile_a_id or len(request.profile_a_id.strip()) == 0:
            logger.warning("Compare request with empty Profile A ID")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile A ID cannot be empty",
            )

        # Validate profile_b_id
        if not request.profile_b_id or len(request.profile_b_id.strip()) == 0:
            logger.warning("Compare request with empty Profile B ID")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile B ID cannot be empty",
            )

        # Check that profiles are different
        if request.profile_a_id == request.profile_b_id:
            logger.warning(
                f"Compare request with identical profile IDs: {request.profile_a_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile A and Profile B cannot be the same",
            )

        # Validate vacancy_id
        if not request.vacancy_id or len(request.vacancy_id.strip()) == 0:
            logger.warning("Compare request with empty vacancy ID")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Vacancy ID cannot be empty",
            )

        # For now, return placeholder response with proper structure
        # Database integration will be added in a later subtask when we have:
        # - Async database session setup
        # - MatchingWeightsProfile model queries
        # - Actual match score calculation with both profiles
        logger.debug(
            f"Returning placeholder comparison for vacancy {request.vacancy_id} "
            f"(database integration pending)"
        )

        # Placeholder profile data following MatchingWeightsProfileResponse structure
        profile_a_data = {
            "id": request.profile_a_id,
            "organization_id": "org-placeholder",
            "name": "Profile A",
            "description": "First profile for comparison",
            "keyword_weight": 0.5,
            "tfidf_weight": 0.3,
            "vector_weight": 0.2,
            "is_default": False,
            "is_preset": False,
            "preset_type": None,
            "created_by": "user-placeholder",
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        profile_b_data = {
            "id": request.profile_b_id,
            "organization_id": "org-placeholder",
            "name": "Profile B",
            "description": "Second profile for comparison",
            "keyword_weight": 0.3,
            "tfidf_weight": 0.3,
            "vector_weight": 0.4,
            "is_default": False,
            "is_preset": False,
            "preset_type": None,
            "created_by": "user-placeholder",
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        # Placeholder differences showing structure
        # In full implementation, this will contain actual candidate comparison data
        differences_data = []

        response_data = {
            "vacancy_id": request.vacancy_id,
            "profile_a": profile_a_data,
            "profile_b": profile_b_data,
            "differences": differences_data,
        }

        logger.info(
            f"Generated comparison for vacancy {request.vacancy_id} "
            f"({len(differences_data)} candidate differences)"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error comparing weight profiles for vacancy {request.vacancy_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare weight profiles: {str(e)}",
        ) from e
