"""
Ranking weight management endpoints.

This module provides endpoints for managing custom ranking weight configurations,
allowing organizations to customize how different ranking features are weighted
when ranking candidates for job vacancies.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ranking_weights_profile import RankingWeightProfile
from models.ranking_weights_history import RankingWeightVersion
from schemas.ranking_weights import (
    RankingWeightProfileCreate,
    RankingWeightProfileUpdate,
    RankingWeightProfileResponse,
    RankingWeightProfileListResponse,
    RankingWeightVersionResponse,
    NormalizeWeightsRequest,
    NormalizeWeightsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def normalize_weights(
    overall_match_score_weight: float = 0.0,
    keyword_score_weight: float = 0.0,
    tfidf_score_weight: float = 0.0,
    vector_score_weight: float = 0.0,
    skills_match_ratio_weight: float = 0.0,
    experience_months_weight: float = 0.0,
    experience_relevance_weight: float = 0.0,
    education_level_weight: float = 0.0,
    recent_experience_weight: float = 0.0,
    skill_rarity_weight: float = 0.0,
    title_similarity_weight: float = 0.0,
    freshness_score_weight: float = 0.0,
    completeness_score_weight: float = 0.0,
) -> tuple:
    """
    Normalize weights so they sum to 1.0.

    If the weights already sum to 1.0 (within a small tolerance), they are returned as-is.
    Otherwise, they are scaled proportionally.

    Args:
        All 13 ranking feature weights

    Returns:
        Tuple of normalized weights in same order
    """
    total = (
        overall_match_score_weight +
        keyword_score_weight +
        tfidf_score_weight +
        vector_score_weight +
        skills_match_ratio_weight +
        experience_months_weight +
        experience_relevance_weight +
        education_level_weight +
        recent_experience_weight +
        skill_rarity_weight +
        title_similarity_weight +
        freshness_score_weight +
        completeness_score_weight
    )

    # If weights sum to approximately 1.0, return as-is
    if abs(total - 1.0) < 0.0001:
        return (
            overall_match_score_weight,
            keyword_score_weight,
            tfidf_score_weight,
            vector_score_weight,
            skills_match_ratio_weight,
            experience_months_weight,
            experience_relevance_weight,
            education_level_weight,
            recent_experience_weight,
            skill_rarity_weight,
            title_similarity_weight,
            freshness_score_weight,
            completeness_score_weight,
        )

    # Scale weights proportionally
    if total > 0:
        return (
            overall_match_score_weight / total,
            keyword_score_weight / total,
            tfidf_score_weight / total,
            vector_score_weight / total,
            skills_match_ratio_weight / total,
            experience_months_weight / total,
            experience_relevance_weight / total,
            education_level_weight / total,
            recent_experience_weight / total,
            skill_rarity_weight / total,
            title_similarity_weight / total,
            freshness_score_weight / total,
            completeness_score_weight / total,
        )
    else:
        # If all weights are 0, return balanced defaults
        return (0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.076)


@router.get(
    "/profiles/presets",
    response_model=RankingWeightProfileListResponse,
    tags=["Ranking Weights"],
)
async def get_preset_profiles(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all system preset ranking weight profiles.

    Returns preset profiles like Technical, Sales, Executive, and Balanced
    that organizations can use as starting points or templates.

    Args:
        db: Database session

    Returns:
        JSON response with list of preset profiles

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/ranking-weights/profiles/presets")
        >>> presets = response.json()["profiles"]
    """
    try:
        stmt = select(RankingWeightProfile).where(
            RankingWeightProfile.is_preset == True
        ).order_by(RankingWeightProfile.name)

        result = await db.execute(stmt)
        profiles = result.scalars().all()

        response_profiles = [
            RankingWeightProfileResponse(
                id=str(p.id),
                organization_id=str(p.organization_id) if p.organization_id else None,
                vacancy_id=str(p.vacancy_id) if p.vacancy_id else None,
                name=p.name,
                description=p.description,
                overall_match_score_weight=p.overall_match_score_weight,
                keyword_score_weight=p.keyword_score_weight,
                tfidf_score_weight=p.tfidf_score_weight,
                vector_score_weight=p.vector_score_weight,
                skills_match_ratio_weight=p.skills_match_ratio_weight,
                experience_months_weight=p.experience_months_weight,
                experience_relevance_weight=p.experience_relevance_weight,
                education_level_weight=p.education_level_weight,
                recent_experience_weight=p.recent_experience_weight,
                skill_rarity_weight=p.skill_rarity_weight,
                title_similarity_weight=p.title_similarity_weight,
                freshness_score_weight=p.freshness_score_weight,
                completeness_score_weight=p.completeness_score_weight,
                is_active=p.is_active,
                is_preset=p.is_preset,
                preset_type=p.preset_type,
                created_by=str(p.created_by) if p.created_by else None,
                updated_by=str(p.updated_by) if p.updated_by else None,
                version=p.version,
                change_reason=p.change_reason,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in profiles
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "organization_id": None,
                "vacancy_id": None,
                "profiles": [p.model_dump() for p in response_profiles],
                "total_count": len(response_profiles),
            }
        )
    except Exception as e:
        logger.error(f"Error getting preset profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve preset profiles: {str(e)}"
        )


@router.post(
    "/profiles",
    response_model=RankingWeightProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ranking Weights"],
)
async def create_ranking_weight_profile(
    request: RankingWeightProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a custom ranking weight profile for an organization or vacancy.

    This endpoint creates a new weight profile that specifies how different
    ranking features should be weighted when ranking candidates.

    Weights will be auto-normalized to sum to 1.0 if they don't already.

    Args:
        request: Create request with profile configuration
        db: Database session

    Returns:
        JSON response with created profile details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(409): If profile with same name exists for organization
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org123",
        ...     "name": "Skills-Focused",
        ...     "description": "Prioritize candidates with strong skill matches",
        ...     "skills_match_ratio_weight": 0.5,
        ...     "overall_match_score_weight": 0.3,
        ...     "keyword_score_weight": 0.2
        ... }
        >>> response = requests.post("http://localhost:8000/api/ranking-weights/profiles", json=data)
    """
    try:
        # Check if profile with same name exists for this organization
        if request.organization_id:
            stmt = select(RankingWeightProfile).where(
                RankingWeightProfile.organization_id == request.organization_id,
                RankingWeightProfile.name == request.name
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Profile with name '{request.name}' already exists for this organization"
                )

        # Normalize weights
        normalized = normalize_weights(
            overall_match_score_weight=request.overall_match_score_weight,
            keyword_score_weight=request.keyword_score_weight,
            tfidf_score_weight=request.tfidf_score_weight,
            vector_score_weight=request.vector_score_weight,
            skills_match_ratio_weight=request.skills_match_ratio_weight,
            experience_months_weight=request.experience_months_weight,
            experience_relevance_weight=request.experience_relevance_weight,
            education_level_weight=request.education_level_weight,
            recent_experience_weight=request.recent_experience_weight,
            skill_rarity_weight=request.skill_rarity_weight,
            title_similarity_weight=request.title_similarity_weight,
            freshness_score_weight=request.freshness_score_weight,
            completeness_score_weight=request.completeness_score_weight,
        )

        # Create profile
        profile = RankingWeightProfile(
            organization_id=request.organization_id,
            vacancy_id=request.vacancy_id,
            name=request.name,
            description=request.description,
            overall_match_score_weight=normalized[0],
            keyword_score_weight=normalized[1],
            tfidf_score_weight=normalized[2],
            vector_score_weight=normalized[3],
            skills_match_ratio_weight=normalized[4],
            experience_months_weight=normalized[5],
            experience_relevance_weight=normalized[6],
            education_level_weight=normalized[7],
            recent_experience_weight=normalized[8],
            skill_rarity_weight=normalized[9],
            title_similarity_weight=normalized[10],
            freshness_score_weight=normalized[11],
            completeness_score_weight=normalized[12],
            is_active=request.is_active,
            is_preset=request.is_preset,
            preset_type=request.preset_type,
            created_by=request.created_by,
            version="v1.0",
            change_reason=request.change_reason,
        )

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        # Create version history entry
        version = RankingWeightVersion(
            profile_id=profile.id,
            overall_match_score_weight=profile.overall_match_score_weight,
            keyword_score_weight=profile.keyword_score_weight,
            tfidf_score_weight=profile.tfidf_score_weight,
            vector_score_weight=profile.vector_score_weight,
            skills_match_ratio_weight=profile.skills_match_ratio_weight,
            experience_months_weight=profile.experience_months_weight,
            experience_relevance_weight=profile.experience_relevance_weight,
            education_level_weight=profile.education_level_weight,
            recent_experience_weight=profile.recent_experience_weight,
            skill_rarity_weight=profile.skill_rarity_weight,
            title_similarity_weight=profile.title_similarity_weight,
            freshness_score_weight=profile.freshness_score_weight,
            completeness_score_weight=profile.completeness_score_weight,
            changed_by=request.created_by,
            version="v1.0",
            change_reason=request.change_reason or "Initial profile creation",
        )
        db.add(version)
        await db.commit()

        logger.info(f"Created ranking weight profile: {profile.name} (ID: {profile.id})")

        response = RankingWeightProfileResponse(
            id=str(profile.id),
            organization_id=str(profile.organization_id) if profile.organization_id else None,
            vacancy_id=str(profile.vacancy_id) if profile.vacancy_id else None,
            name=profile.name,
            description=profile.description,
            overall_match_score_weight=profile.overall_match_score_weight,
            keyword_score_weight=profile.keyword_score_weight,
            tfidf_score_weight=profile.tfidf_score_weight,
            vector_score_weight=profile.vector_score_weight,
            skills_match_ratio_weight=profile.skills_match_ratio_weight,
            experience_months_weight=profile.experience_months_weight,
            experience_relevance_weight=profile.experience_relevance_weight,
            education_level_weight=profile.education_level_weight,
            recent_experience_weight=profile.recent_experience_weight,
            skill_rarity_weight=profile.skill_rarity_weight,
            title_similarity_weight=profile.title_similarity_weight,
            freshness_score_weight=profile.freshness_score_weight,
            completeness_score_weight=profile.completeness_score_weight,
            is_active=profile.is_active,
            is_preset=profile.is_preset,
            preset_type=profile.preset_type,
            created_by=str(profile.created_by) if profile.created_by else None,
            updated_by=str(profile.updated_by) if profile.updated_by else None,
            version=profile.version,
            change_reason=profile.change_reason,
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ranking weight profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ranking weight profile: {str(e)}"
        )


@router.get(
    "/profiles",
    response_model=RankingWeightProfileListResponse,
    tags=["Ranking Weights"],
)
async def get_ranking_weight_profiles(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    is_preset: Optional[bool] = Query(None, description="Filter by preset flag"),
    is_active: Optional[bool] = Query(True, description="Filter by active flag"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get ranking weight profiles with optional filters.

    Returns profiles matching the specified filters. If no filters are provided,
    returns all active profiles.

    Args:
        organization_id: Filter by organization ID
        vacancy_id: Filter by vacancy ID
        is_preset: Filter by preset flag
        is_active: Filter by active flag (defaults to True)
        db: Database session

    Returns:
        JSON response with list of profiles

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/ranking-weights/profiles?organization_id=org123")
    """
    try:
        stmt = select(RankingWeightProfile)

        # Apply filters
        if organization_id is not None:
            stmt = stmt.where(RankingWeightProfile.organization_id == organization_id)
        if vacancy_id is not None:
            stmt = stmt.where(RankingWeightProfile.vacancy_id == vacancy_id)
        if is_preset is not None:
            stmt = stmt.where(RankingWeightProfile.is_preset == is_preset)
        if is_active is not None:
            stmt = stmt.where(RankingWeightProfile.is_active == is_active)

        stmt = stmt.order_by(RankingWeightProfile.created_at.desc())

        result = await db.execute(stmt)
        profiles = result.scalars().all()

        response_profiles = [
            RankingWeightProfileResponse(
                id=str(p.id),
                organization_id=str(p.organization_id) if p.organization_id else None,
                vacancy_id=str(p.vacancy_id) if p.vacancy_id else None,
                name=p.name,
                description=p.description,
                overall_match_score_weight=p.overall_match_score_weight,
                keyword_score_weight=p.keyword_score_weight,
                tfidf_score_weight=p.tfidf_score_weight,
                vector_score_weight=p.vector_score_weight,
                skills_match_ratio_weight=p.skills_match_ratio_weight,
                experience_months_weight=p.experience_months_weight,
                experience_relevance_weight=p.experience_relevance_weight,
                education_level_weight=p.education_level_weight,
                recent_experience_weight=p.recent_experience_weight,
                skill_rarity_weight=p.skill_rarity_weight,
                title_similarity_weight=p.title_similarity_weight,
                freshness_score_weight=p.freshness_score_weight,
                completeness_score_weight=p.completeness_score_weight,
                is_active=p.is_active,
                is_preset=p.is_preset,
                preset_type=p.preset_type,
                created_by=str(p.created_by) if p.created_by else None,
                updated_by=str(p.updated_by) if p.updated_by else None,
                version=p.version,
                change_reason=p.change_reason,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in profiles
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "organization_id": organization_id,
                "vacancy_id": vacancy_id,
                "profiles": [p.model_dump() for p in response_profiles],
                "total_count": len(response_profiles),
            }
        )
    except Exception as e:
        logger.error(f"Error getting ranking weight profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ranking weight profiles: {str(e)}"
        )


@router.get(
    "/profiles/{profile_id}",
    response_model=RankingWeightProfileResponse,
    tags=["Ranking Weights"],
)
async def get_ranking_weight_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific ranking weight profile by ID.

    Args:
        profile_id: Profile UUID
        db: Database session

    Returns:
        JSON response with profile details

    Raises:
        HTTPException(404): If profile not found

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/ranking-weights/profiles/abc-123")
    """
    try:
        stmt = select(RankingWeightProfile).where(RankingWeightProfile.id == profile_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking weight profile not found: {profile_id}"
            )

        response = RankingWeightProfileResponse(
            id=str(profile.id),
            organization_id=str(profile.organization_id) if profile.organization_id else None,
            vacancy_id=str(profile.vacancy_id) if profile.vacancy_id else None,
            name=profile.name,
            description=profile.description,
            overall_match_score_weight=profile.overall_match_score_weight,
            keyword_score_weight=profile.keyword_score_weight,
            tfidf_score_weight=profile.tfidf_score_weight,
            vector_score_weight=profile.vector_score_weight,
            skills_match_ratio_weight=profile.skills_match_ratio_weight,
            experience_months_weight=profile.experience_months_weight,
            experience_relevance_weight=profile.experience_relevance_weight,
            education_level_weight=profile.education_level_weight,
            recent_experience_weight=profile.recent_experience_weight,
            skill_rarity_weight=profile.skill_rarity_weight,
            title_similarity_weight=profile.title_similarity_weight,
            freshness_score_weight=profile.freshness_score_weight,
            completeness_score_weight=profile.completeness_score_weight,
            is_active=profile.is_active,
            is_preset=profile.is_preset,
            preset_type=profile.preset_type,
            created_by=str(profile.created_by) if profile.created_by else None,
            updated_by=str(profile.updated_by) if profile.updated_by else None,
            version=profile.version,
            change_reason=profile.change_reason,
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ranking weight profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ranking weight profile: {str(e)}"
        )


@router.put(
    "/profiles/{profile_id}",
    response_model=RankingWeightProfileResponse,
    tags=["Ranking Weights"],
)
async def update_ranking_weight_profile(
    profile_id: str,
    request: RankingWeightProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a ranking weight profile.

    Updates the specified fields of a profile. Weights will be auto-normalized
    if any weight fields are updated.

    Args:
        profile_id: Profile UUID
        request: Update request with fields to change
        db: Database session

    Returns:
        JSON response with updated profile details

    Raises:
        HTTPException(404): If profile not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"skills_match_ratio_weight": 0.6, "change_reason": "Increased emphasis on skills"}
        >>> response = requests.put("http://localhost:8000/api/ranking-weights/profiles/abc-123", json=data)
    """
    try:
        stmt = select(RankingWeightProfile).where(RankingWeightProfile.id == profile_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking weight profile not found: {profile_id}"
            )

        # Update fields
        update_data = request.model_dump(exclude_unset=True)

        # Track if weights were updated
        weights_updated = any(
            key.endswith("_weight") and key in update_data
            for key in update_data
        )

        # Apply updates
        for field, value in update_data.items():
            if hasattr(profile, field) and value is not None:
                setattr(profile, field, value)

        # Normalize weights if any were updated
        if weights_updated:
            profile.normalize_weights()

            # Increment version
            current_version = profile.version or "v1.0"
            if current_version.startswith("v"):
                try:
                    major, minor = current_version[1:].split(".")
                    new_minor = int(minor) + 1
                    profile.version = f"v{major}.{new_minor}"
                except:
                    profile.version = "v1.1"
            else:
                profile.version = "v1.1"

            # Create version history entry
            version = RankingWeightVersion(
                profile_id=profile.id,
                overall_match_score_weight=profile.overall_match_score_weight,
                keyword_score_weight=profile.keyword_score_weight,
                tfidf_score_weight=profile.tfidf_score_weight,
                vector_score_weight=profile.vector_score_weight,
                skills_match_ratio_weight=profile.skills_match_ratio_weight,
                experience_months_weight=profile.experience_months_weight,
                experience_relevance_weight=profile.experience_relevance_weight,
                education_level_weight=profile.education_level_weight,
                recent_experience_weight=profile.recent_experience_weight,
                skill_rarity_weight=profile.skill_rarity_weight,
                title_similarity_weight=profile.title_similarity_weight,
                freshness_score_weight=profile.freshness_score_weight,
                completeness_score_weight=profile.completeness_score_weight,
                changed_by=request.updated_by,
                version=profile.version,
                change_reason=request.change_reason or "Profile updated",
            )
            db.add(version)

        await db.commit()
        await db.refresh(profile)

        logger.info(f"Updated ranking weight profile: {profile.name} (ID: {profile.id})")

        response = RankingWeightProfileResponse(
            id=str(profile.id),
            organization_id=str(profile.organization_id) if profile.organization_id else None,
            vacancy_id=str(profile.vacancy_id) if profile.vacancy_id else None,
            name=profile.name,
            description=profile.description,
            overall_match_score_weight=profile.overall_match_score_weight,
            keyword_score_weight=profile.keyword_score_weight,
            tfidf_score_weight=profile.tfidf_score_weight,
            vector_score_weight=profile.vector_score_weight,
            skills_match_ratio_weight=profile.skills_match_ratio_weight,
            experience_months_weight=profile.experience_months_weight,
            experience_relevance_weight=profile.experience_relevance_weight,
            education_level_weight=profile.education_level_weight,
            recent_experience_weight=profile.recent_experience_weight,
            skill_rarity_weight=profile.skill_rarity_weight,
            title_similarity_weight=profile.title_similarity_weight,
            freshness_score_weight=profile.freshness_score_weight,
            completeness_score_weight=profile.completeness_score_weight,
            is_active=profile.is_active,
            is_preset=profile.is_preset,
            preset_type=profile.preset_type,
            created_by=str(profile.created_by) if profile.created_by else None,
            updated_by=str(profile.updated_by) if profile.updated_by else None,
            version=profile.version,
            change_reason=profile.change_reason,
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ranking weight profile {profile_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ranking weight profile: {str(e)}"
        )


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Ranking Weights"],
)
async def delete_ranking_weight_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a ranking weight profile.

    Soft deletes the profile by setting is_active to False.

    Args:
        profile_id: Profile UUID
        db: Database session

    Raises:
        HTTPException(404): If profile not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/ranking-weights/profiles/abc-123")
    """
    try:
        stmt = select(RankingWeightProfile).where(RankingWeightProfile.id == profile_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking weight profile not found: {profile_id}"
            )

        # Soft delete by setting is_active to False
        profile.is_active = False
        await db.commit()

        logger.info(f"Deleted ranking weight profile: {profile.name} (ID: {profile.id})")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ranking weight profile {profile_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ranking weight profile: {str(e)}"
        )


@router.get(
    "/profiles/{profile_id}/history",
    response_model=List[RankingWeightVersionResponse],
    tags=["Ranking Weights"],
)
async def get_profile_history(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get version history for a ranking weight profile.

    Returns all historical versions of the profile, showing how weights
    have changed over time.

    Args:
        profile_id: Profile UUID
        db: Database session

    Returns:
        JSON response with list of version history entries

    Raises:
        HTTPException(404): If profile not found

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/ranking-weights/profiles/abc-123/history")
    """
    try:
        # Check if profile exists
        stmt = select(RankingWeightProfile).where(RankingWeightProfile.id == profile_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking weight profile not found: {profile_id}"
            )

        # Get version history
        stmt = select(RankingWeightVersion).where(
            RankingWeightVersion.profile_id == profile_id
        ).order_by(RankingWeightVersion.created_at.desc())

        result = await db.execute(stmt)
        versions = result.scalars().all()

        response_versions = [
            RankingWeightVersionResponse(
                id=str(v.id),
                profile_id=str(v.profile_id),
                overall_match_score_weight=v.overall_match_score_weight,
                keyword_score_weight=v.keyword_score_weight,
                tfidf_score_weight=v.tfidf_score_weight,
                vector_score_weight=v.vector_score_weight,
                skills_match_ratio_weight=v.skills_match_ratio_weight,
                experience_months_weight=v.experience_months_weight,
                experience_relevance_weight=v.experience_relevance_weight,
                education_level_weight=v.education_level_weight,
                recent_experience_weight=v.recent_experience_weight,
                skill_rarity_weight=v.skill_rarity_weight,
                title_similarity_weight=v.title_similarity_weight,
                freshness_score_weight=v.freshness_score_weight,
                completeness_score_weight=v.completeness_score_weight,
                changed_by=str(v.changed_by) if v.changed_by else None,
                version=v.version,
                change_reason=v.change_reason,
                created_at=v.created_at.isoformat(),
                updated_at=v.updated_at.isoformat(),
            )
            for v in versions
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=[v.model_dump() for v in response_versions]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile history for {profile_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile history: {str(e)}"
        )


@router.post(
    "/normalize",
    response_model=NormalizeWeightsResponse,
    tags=["Ranking Weights"],
)
async def normalize_ranking_weights(
    request: NormalizeWeightsRequest,
) -> JSONResponse:
    """
    Normalize ranking weights to sum to 1.0.

    Utility endpoint that takes a set of weights and returns them normalized
    so they sum to 1.0. Useful for previewing weight adjustments before saving.

    Args:
        request: Weights to normalize (only provided weights will be used)

    Returns:
        JSON response with normalized weights

    Examples:
        >>> import requests
        >>> data = {"skills_match_ratio_weight": 0.5, "overall_match_score_weight": 0.3}
        >>> response = requests.post("http://localhost:8000/api/ranking-weights/normalize", json=data)
    """
    try:
        # Get provided weights or use defaults
        weights = request.model_dump(exclude_unset=True)

        # Fill in missing weights with 0
        all_weights = {
            "overall_match_score_weight": weights.get("overall_match_score_weight", 0.0),
            "keyword_score_weight": weights.get("keyword_score_weight", 0.0),
            "tfidf_score_weight": weights.get("tfidf_score_weight", 0.0),
            "vector_score_weight": weights.get("vector_score_weight", 0.0),
            "skills_match_ratio_weight": weights.get("skills_match_ratio_weight", 0.0),
            "experience_months_weight": weights.get("experience_months_weight", 0.0),
            "experience_relevance_weight": weights.get("experience_relevance_weight", 0.0),
            "education_level_weight": weights.get("education_level_weight", 0.0),
            "recent_experience_weight": weights.get("recent_experience_weight", 0.0),
            "skill_rarity_weight": weights.get("skill_rarity_weight", 0.0),
            "title_similarity_weight": weights.get("title_similarity_weight", 0.0),
            "freshness_score_weight": weights.get("freshness_score_weight", 0.0),
            "completeness_score_weight": weights.get("completeness_score_weight", 0.0),
        }

        normalized = normalize_weights(**all_weights)

        response = NormalizeWeightsResponse(
            overall_match_score_weight=normalized[0],
            keyword_score_weight=normalized[1],
            tfidf_score_weight=normalized[2],
            vector_score_weight=normalized[3],
            skills_match_ratio_weight=normalized[4],
            experience_months_weight=normalized[5],
            experience_relevance_weight=normalized[6],
            education_level_weight=normalized[7],
            recent_experience_weight=normalized[8],
            skill_rarity_weight=normalized[9],
            title_similarity_weight=normalized[10],
            freshness_score_weight=normalized[11],
            completeness_score_weight=normalized[12],
            total=sum(normalized),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )
    except Exception as e:
        logger.error(f"Error normalizing weights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize weights: {str(e)}"
        )
