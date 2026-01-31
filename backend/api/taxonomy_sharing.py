"""
Taxonomy sharing endpoints.

This module provides endpoints for sharing skill taxonomies between organizations,
including listing public taxonomies and forking taxonomies to organizations.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

router = APIRouter()


class PublicTaxonomyResponse(BaseModel):
    """Response model for a single public taxonomy entry."""

    id: str = Field(..., description="Unique identifier for the taxonomy entry")
    industry: str = Field(..., description="Industry sector")
    skill_name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: bool = Field(..., description="Whether this entry is active")
    organization_id: Optional[str] = Field(None, description="Organization that owns this taxonomy")
    source_organization: Optional[str] = Field(None, description="Original organization if forked")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class PublicTaxonomyListResponse(BaseModel):
    """Response model for listing public taxonomies."""

    industry: Optional[str] = Field(None, description="Industry filter applied")
    taxonomies: List[PublicTaxonomyResponse] = Field(..., description="List of public taxonomy entries")
    total_count: int = Field(..., description="Total number of entries")


class TaxonomyForkRequest(BaseModel):
    """Request model for forking a taxonomy."""

    organization_id: str = Field(..., description="Organization ID to fork the taxonomy to")


class TaxonomyForkResponse(BaseModel):
    """Response model for a forked taxonomy."""

    id: str = Field(..., description="Unique identifier for the new taxonomy entry")
    industry: str = Field(..., description="Industry sector")
    skill_name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: bool = Field(..., description="Whether this entry is active")
    organization_id: str = Field(..., description="Organization that owns this taxonomy")
    source_organization: Optional[str] = Field(None, description="Original organization if forked")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


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
        "organization_id": taxonomy.organization_id,
        "source_organization": taxonomy.source_organization,
        "created_at": taxonomy.created_at.isoformat() if taxonomy.created_at else "",
        "updated_at": taxonomy.updated_at.isoformat() if taxonomy.updated_at else "",
    }


@router.get("/public", tags=["Taxonomy Sharing"])
async def list_public_taxonomies(
    industry: Optional[str] = Query(None, description="Filter by industry sector"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List public taxonomies available for sharing.

    This endpoint returns all public taxonomy entries that can be forked
    by other organizations. Results can be filtered by industry.

    Args:
        industry: Optional industry filter
        db: Database session

    Returns:
        JSON response with list of public taxonomy entries

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/taxonomy-sharing/public?industry=healthcare")
        >>> response.json()
        {
            "industry": "healthcare",
            "taxonomies": [...],
            "total_count": 50
        }
    """
    try:
        logger.info(f"Listing public taxonomies with filter - industry: {industry}")

        # Build query
        query = select(SkillTaxonomy).where(SkillTaxonomy.is_public == True)

        if industry:
            query = query.where(SkillTaxonomy.industry == industry)

        query = query.order_by(SkillTaxonomy.industry, SkillTaxonomy.skill_name)

        # Execute query
        result = await db.execute(query)
        taxonomies = result.scalars().all()

        # Convert to response format
        taxonomies_response = [model_to_dict(taxonomy) for taxonomy in taxonomies]

        response_data = {
            "industry": industry,
            "taxonomies": taxonomies_response,
            "total_count": len(taxonomies_response),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing public taxonomies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list public taxonomies: {str(e)}",
        ) from e


@router.post("/{taxonomy_id}/fork", tags=["Taxonomy Sharing"])
async def fork_taxonomy(
    taxonomy_id: str,
    request: TaxonomyForkRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Fork a taxonomy entry to an organization.

    This endpoint creates a copy of a public taxonomy entry for the specified
    organization. The forked taxonomy will reference the original organization
    in the source_organization field.

    Args:
        taxonomy_id: Unique identifier of the taxonomy entry to fork
        request: Fork request with organization_id
        db: Database session

    Returns:
        JSON response with the new forked taxonomy entry

    Raises:
        HTTPException(404): If taxonomy entry is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"organization_id": "org-123"}
        >>> response = requests.post(
        ...     "http://localhost:8000/api/taxonomy-sharing/abc-123/fork",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Forking taxonomy {taxonomy_id} to organization {request.organization_id}")

        # Validate organization_id
        if not request.organization_id or len(request.organization_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization ID cannot be empty",
            )

        # Query the source taxonomy
        query = select(SkillTaxonomy).where(SkillTaxonomy.id == UUID(taxonomy_id))
        result = await db.execute(query)
        source_taxonomy = result.scalar_one_or_none()

        if not source_taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy with ID {taxonomy_id} not found",
            )

        # Check if taxonomy is public
        if not source_taxonomy.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Taxonomy with ID {taxonomy_id} is not public and cannot be forked",
            )

        # Create forked taxonomy
        forked_taxonomy = SkillTaxonomy(
            industry=source_taxonomy.industry,
            skill_name=source_taxonomy.skill_name,
            context=source_taxonomy.context,
            variants=source_taxonomy.variants,
            extra_metadata=source_taxonomy.extra_metadata,
            is_active=source_taxonomy.is_active,
            version=1,
            previous_version_id=None,
            is_latest=True,
            is_public=False,  # Forked taxonomies are not public by default
            organization_id=request.organization_id,
            source_organization=source_taxonomy.organization_id,
        )

        db.add(forked_taxonomy)
        await db.commit()
        await db.refresh(forked_taxonomy)

        logger.info(f"Successfully forked taxonomy {taxonomy_id} to organization {request.organization_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=model_to_dict(forked_taxonomy),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid taxonomy ID format: {taxonomy_id}",
        )
    except Exception as e:
        logger.error(f"Error forking taxonomy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fork taxonomy: {str(e)}",
        ) from e
