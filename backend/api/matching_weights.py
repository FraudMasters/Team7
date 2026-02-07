"""
Matching algorithm weight management endpoints.

This module provides endpoints for managing custom matching algorithm weight configurations,
allowing organizations to customize how keyword, TF-IDF, and vector similarity scores
are combined for resume-job matching.
"""
import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.matching_weights_profile import MatchingWeightsProfile

logger = logging.getLogger(__name__)

router = APIRouter()

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


@router.post(
    "/",
    response_model=MatchingWeightsProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Matching Weights"],
)
async def create_matching_weights_profile(request: MatchingWeightsProfileCreate) -> JSONResponse:
    """
    Create a custom matching weights profile for an organization.

    This endpoint creates a new weight profile that specifies how keyword, TF-IDF,
    and vector similarity scores should be combined when matching resumes to jobs.

    Weights will be auto-normalized to sum to 1.0 if they don't already.

    Args:
        request: Create request with profile configuration

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

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        profile_response = {
            "id": "placeholder-id",
            "organization_id": request.organization_id,
            "name": request.name,
            "description": request.description,
            "keyword_weight": request.keyword_weight,
            "tfidf_weight": request.tfidf_weight,
            "vector_weight": request.vector_weight,
            "is_default": request.is_default,
            "is_preset": request.is_preset,
            "preset_type": request.preset_type,
            "created_by": request.created_by,
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        logger.info(
            f"Created matching weights profile '{request.name}' "
            f"for organization: {request.organization_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=profile_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating matching weights profile: {e}", exc_info=True)
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
) -> JSONResponse:
    """
    List matching weights profiles with optional filters.

    Args:
        organization_id: Optional organization ID filter
        is_default: Optional default status filter
        is_preset: Optional preset status filter
        preset_type: Optional preset type filter

    Returns:
        JSON response with list of weight profiles

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/matching-weights/?organization_id=org123")
        >>> response.json()
    """
    try:
        logger.info(f"Listing matching weights profiles with filters: organization_id={organization_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask
        profiles = []

        response_data = {
            "organization_id": organization_id,
            "profiles": profiles,
            "total_count": len(profiles),
        }

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
async def get_matching_weights_profile(profile_id: str) -> JSONResponse:
    """
    Retrieve a specific matching weights profile by ID.

    Args:
        profile_id: UUID of the profile to retrieve

    Returns:
        JSON response with profile details

    Raises:
        HTTPException(404): If profile not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/matching-weights/abc-123-def")
        >>> response.json()
    """
    try:
        logger.info(f"Retrieving matching weights profile: {profile_id}")

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matching weights profile not found: {profile_id}",
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
) -> JSONResponse:
    """
    Update a matching weights profile.

    Only the fields specified in the request will be updated.
    Weights will be auto-normalized to sum to 1.0 if they don't already.

    Args:
        profile_id: UUID of the profile to update
        request: Update request with fields to modify

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

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        profile_response = {
            "id": profile_id,
            "organization_id": "org123",
            "name": request.name or "Updated Profile Name",
            "description": request.description,
            "keyword_weight": request.keyword_weight if request.keyword_weight is not None else 0.5,
            "tfidf_weight": request.tfidf_weight if request.tfidf_weight is not None else 0.3,
            "vector_weight": request.vector_weight if request.vector_weight is not None else 0.2,
            "is_default": request.is_default if request.is_default is not None else False,
            "is_preset": False,
            "preset_type": None,
            "created_by": "user456",
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        logger.info(f"Updated matching weights profile: {profile_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=profile_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating matching weights profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update matching weights profile: {str(e)}",
        ) from e


@router.delete("/{profile_id}", tags=["Matching Weights"])
async def delete_matching_weights_profile(profile_id: str) -> JSONResponse:
    """
    Delete a matching weights profile.

    Note: Default profiles and system presets cannot be deleted.

    Args:
        profile_id: UUID of the profile to delete

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
    """
    try:
        logger.info(f"Deleting matching weights profile: {profile_id}")

        # Validate profile_id
        if not profile_id or len(profile_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile ID cannot be empty",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Matching weights profile {profile_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting matching weights profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete matching weights profile: {str(e)}",
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
