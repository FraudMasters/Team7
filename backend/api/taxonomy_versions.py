"""
Taxonomy versioning endpoints.

This module provides endpoints for managing versions of skill taxonomy entries,
including creating new versions, listing version history, and rolling back to
previous versions.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

router = APIRouter()


class TaxonomyVersionResponse(BaseModel):
    """Response model for a taxonomy version."""

    id: str = Field(..., description="Unique identifier for this version")
    industry: str = Field(..., description="Industry sector")
    skill_name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: bool = Field(..., description="Whether this entry is active")
    version: int = Field(..., description="Version number")
    previous_version_id: Optional[str] = Field(None, description="ID of the previous version")
    is_latest: bool = Field(..., description="Whether this is the latest version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class TaxonomyVersionListResponse(BaseModel):
    """Response model for listing taxonomy versions."""

    taxonomy_id: str = Field(..., description="ID of the taxonomy entry")
    skill_name: str = Field(..., description="Canonical name of the skill")
    industry: str = Field(..., description="Industry sector")
    versions: List[TaxonomyVersionResponse] = Field(..., description="List of all versions")
    total_count: int = Field(..., description="Total number of versions")


class TaxonomyVersionCreate(BaseModel):
    """Request model for creating a new version."""

    skill_name: Optional[str] = Field(None, description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: Optional[List[str]] = Field(None, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: Optional[bool] = Field(None, description="Whether this entry is active")


def model_to_dict(taxonomy: SkillTaxonomy) -> dict:
    """Convert SkillTaxonomy model to dictionary."""
    return {
        "id": str(taxonomy.id),
        "industry": taxonomy.industry,
        "skill_name": taxonomy.skill_name,
        "context": taxonomy.context,
        "variants": taxonomy.variants or [],
        "extra_metadata": taxonomy.extra_metadata,
        "is_active": taxonomy.is_active,
        "version": taxonomy.version,
        "previous_version_id": str(taxonomy.previous_version_id) if taxonomy.previous_version_id else None,
        "is_latest": taxonomy.is_latest,
        "created_at": taxonomy.created_at.isoformat() if taxonomy.created_at else "",
        "updated_at": taxonomy.updated_at.isoformat() if taxonomy.updated_at else "",
    }


@router.post("/{taxonomy_id}", response_model=TaxonomyVersionResponse, status_code=status.HTTP_201_CREATED, tags=["Taxonomy Versions"])
async def create_taxonomy_version(
    taxonomy_id: str,
    request: TaxonomyVersionCreate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new version of a taxonomy entry.

    This endpoint creates a new version of an existing taxonomy entry,
    preserving the previous version for rollback capabilities. The new
    version becomes the latest version, and the previous version is
    marked as not latest.

    Args:
        taxonomy_id: ID of the taxonomy entry to version
        request: Update request with fields to modify in the new version
        db: Database session

    Returns:
        JSON response with the newly created version

    Raises:
        HTTPException(404): If taxonomy entry is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "skill_name": "React",
        ...     "variants": ["React", "ReactJS", "React.js", "React Framework"]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/taxonomy-versions/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Creating new version for taxonomy: {taxonomy_id}")

        # Query the latest version of the taxonomy
        query = select(SkillTaxonomy).where(
            SkillTaxonomy.id == UUID(taxonomy_id),
            SkillTaxonomy.is_latest == True
        )
        result = await db.execute(query)
        current_taxonomy = result.scalar_one_or_none()

        if not current_taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Latest version of taxonomy with ID {taxonomy_id} not found",
            )

        # Mark current version as not latest
        current_taxonomy.is_latest = False

        # Determine new version number
        new_version_number = current_taxonomy.version + 1

        # Create new version
        new_version = SkillTaxonomy(
            industry=current_taxonomy.industry,
            skill_name=request.skill_name if request.skill_name is not None else current_taxonomy.skill_name,
            context=request.context if request.context is not None else current_taxonomy.context,
            variants=request.variants if request.variants is not None else current_taxonomy.variants,
            extra_metadata=request.extra_metadata if request.extra_metadata is not None else current_taxonomy.extra_metadata,
            is_active=request.is_active if request.is_active is not None else current_taxonomy.is_active,
            version=new_version_number,
            previous_version_id=current_taxonomy.id,
            is_latest=True,
        )

        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)

        logger.info(f"Created version {new_version_number} for taxonomy {taxonomy_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=model_to_dict(new_version),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid taxonomy ID format: {taxonomy_id}",
        )
    except Exception as e:
        logger.error(f"Error creating taxonomy version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create taxonomy version: {str(e)}",
        ) from e

@router.get("/{taxonomy_id}", response_model=TaxonomyVersionListResponse, tags=["Taxonomy Versions"])
async def list_taxonomy_versions(
    taxonomy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all versions of a taxonomy entry.

    This endpoint retrieves all versions of a taxonomy entry, ordered
    by version number (newest first). Includes both the latest version
    and all historical versions.

    Args:
        taxonomy_id: ID of the taxonomy entry
        db: Database session

    Returns:
        JSON response with list of all versions

    Raises:
        HTTPException(404): If no versions are found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/taxonomy-versions/123")
        >>> response.json()
        {
            "taxonomy_id": "123",
            "skill_name": "React",
            "industry": "tech",
            "versions": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(f"Listing versions for taxonomy: {taxonomy_id}")

        # First, get the latest version to identify the skill
        latest_query = select(SkillTaxonomy).where(
            SkillTaxonomy.id == UUID(taxonomy_id)
        )
        result = await db.execute(latest_query)
        reference_taxonomy = result.scalar_one_or_none()

        if not reference_taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy with ID {taxonomy_id} not found",
            )

        # Get all versions of this taxonomy (either the id matches, or it's in the version chain)
        # We need to find all related versions by traversing the version chain
        all_versions = []

        # Start with the reference taxonomy
        current = reference_taxonomy

        # Traverse forward to find the latest version
        while current:
            if current not in all_versions:
                all_versions.append(current)
            if current.is_latest:
                break
            # Find next version (where previous_version_id points to current)
            next_query = select(SkillTaxonomy).where(
                SkillTaxonomy.previous_version_id == current.id
            )
            next_result = await db.execute(next_query)
            current = next_result.scalar_one_or_none()

        # Traverse backward to find all previous versions
        current = reference_taxonomy
        while current and current.previous_version_id:
            prev_query = select(SkillTaxonomy).where(
                SkillTaxonomy.id == current.previous_version_id
            )
            prev_result = await db.execute(prev_query)
            current = prev_result.scalar_one_or_none()
            if current and current not in all_versions:
                all_versions.append(current)

        # Sort by version number (descending)
        all_versions.sort(key=lambda x: x.version, reverse=True)

        # Convert to response format
        versions_response = [model_to_dict(version) for version in all_versions]

        response_data = {
            "taxonomy_id": taxonomy_id,
            "skill_name": reference_taxonomy.skill_name,
            "industry": reference_taxonomy.industry,
            "versions": versions_response,
            "total_count": len(versions_response),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid taxonomy ID format: {taxonomy_id}",
        )
    except Exception as e:
        logger.error(f"Error listing taxonomy versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list taxonomy versions: {str(e)}",
        ) from e


@router.post("/{taxonomy_id}/rollback/{version_id}", response_model=TaxonomyVersionResponse, tags=["Taxonomy Versions"])
async def rollback_taxonomy_version(
    taxonomy_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Rollback a taxonomy entry to a previous version.

    This endpoint creates a new version that copies the content from a
    previous version, effectively rolling back to that state while
    preserving full version history.

    Args:
        taxonomy_id: ID of the latest taxonomy entry
        version_id: ID of the version to rollback to
        db: Database session

    Returns:
        JSON response with the newly created rollback version

    Raises:
        HTTPException(404): If taxonomy or version is not found
        HTTPException(400): If version is not part of this taxonomy's history
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/taxonomy-versions/123/rollback/456"
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Rolling back taxonomy {taxonomy_id} to version {version_id}")

        # Get the current latest version
        latest_query = select(SkillTaxonomy).where(
            SkillTaxonomy.id == UUID(taxonomy_id),
            SkillTaxonomy.is_latest == True
        )
        result = await db.execute(latest_query)
        current_taxonomy = result.scalar_one_or_none()

        if not current_taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Latest version of taxonomy with ID {taxonomy_id} not found",
            )

        # Get the target version to rollback to
        target_query = select(SkillTaxonomy).where(
            SkillTaxonomy.id == UUID(version_id)
        )
        target_result = await db.execute(target_query)
        target_version = target_result.scalar_one_or_none()

        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target version {version_id} not found",
            )

        # Verify the target version is part of this taxonomy's history
        # by checking if it has the same industry and skill_name
        if (target_version.industry != current_taxonomy.industry or
            target_version.skill_name != current_taxonomy.skill_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version {version_id} is not part of the version history for taxonomy {taxonomy_id}",
            )

        # Mark current version as not latest
        current_taxonomy.is_latest = False

        # Determine new version number
        new_version_number = current_taxonomy.version + 1

        # Create rollback version (copy of target version)
        rollback_version = SkillTaxonomy(
            industry=target_version.industry,
            skill_name=target_version.skill_name,
            context=target_version.context,
            variants=target_version.variants,
            extra_metadata=target_version.extra_metadata,
            is_active=target_version.is_active,
            version=new_version_number,
            previous_version_id=current_taxonomy.id,
            is_latest=True,
        )

        db.add(rollback_version)
        await db.commit()
        await db.refresh(rollback_version)

        logger.info(f"Rolled back taxonomy {taxonomy_id} to version {version_id}, created version {new_version_number}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=model_to_dict(rollback_version),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid taxonomy ID or version ID format",
        )
    except Exception as e:
        logger.error(f"Error rolling back taxonomy version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback taxonomy version: {str(e)}",
        ) from e
