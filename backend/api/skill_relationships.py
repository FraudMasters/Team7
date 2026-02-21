"""
Skill relationship management endpoints.

This module provides endpoints for managing relationships between skills,
including CRUD operations for creating, reading, updating, and deleting
skill relationships such as parent-child, similar, prerequisite, and related.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.skill_relationship import SkillRelationship, RelationshipType
from models.skill_taxonomy import SkillTaxonomy
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import TokenData, get_current_token, require_any_role

logger = logging.getLogger(__name__)

router = APIRouter()


class SkillRelationshipCreate(BaseModel):
    """Request model for creating a skill relationship."""

    source_skill_id: str = Field(..., description="UUID of the source skill")
    target_skill_id: str = Field(..., description="UUID of the target skill")
    relationship_type: str = Field(
        ...,
        description="Type of relationship: parent_child, similar, prerequisite, related",
    )
    weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Weight/strength of relationship (0.0-1.0)")
    extra_metadata: Optional[dict] = Field(None, description="Additional relationship metadata")
    is_active: bool = Field(True, description="Whether this relationship is active")


class SkillRelationshipBatchCreate(BaseModel):
    """Request model for creating multiple skill relationships."""

    relationships: List[SkillRelationshipCreate] = Field(
        ..., description="List of relationships to create"
    )


class SkillRelationshipUpdate(BaseModel):
    """Request model for updating a skill relationship."""

    source_skill_id: Optional[str] = Field(None, description="UUID of the source skill")
    target_skill_id: Optional[str] = Field(None, description="UUID of the target skill")
    relationship_type: Optional[str] = Field(None, description="Type of relationship")
    weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Weight/strength of relationship")
    extra_metadata: Optional[dict] = Field(None, description="Additional relationship metadata")
    is_active: Optional[bool] = Field(None, description="Whether this relationship is active")


class SkillRelationshipResponse(BaseModel):
    """Response model for a single skill relationship."""

    id: str = Field(..., description="Unique identifier for the relationship")
    source_skill_id: str = Field(..., description="UUID of the source skill")
    target_skill_id: str = Field(..., description="UUID of the target skill")
    source_skill_name: Optional[str] = Field(None, description="Name of the source skill")
    target_skill_name: Optional[str] = Field(None, description="Name of the target skill")
    relationship_type: str = Field(..., description="Type of relationship")
    weight: Optional[float] = Field(None, description="Weight/strength of relationship")
    extra_metadata: Optional[dict] = Field(None, description="Additional relationship metadata")
    is_active: bool = Field(..., description="Whether this relationship is active")
    organization_id: str = Field(..., description="Organization that owns this relationship")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SkillRelationshipListResponse(BaseModel):
    """Response model for listing skill relationships."""

    relationships: List[SkillRelationshipResponse] = Field(..., description="List of relationships")
    total_count: int = Field(..., description="Total number of relationships")


def validate_relationship_type(relationship_type: str) -> str:
    """Validate and return the relationship type."""
    valid_types = [rt.value for rt in RelationshipType]
    if relationship_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid relationship type: {relationship_type}. Valid types: {valid_types}",
        )
    return relationship_type


async def get_skill_name(db: AsyncSession, skill_id: UUID) -> Optional[str]:
    """Get the skill name for a given skill ID."""
    result = await db.execute(
        select(SkillTaxonomy.skill_name).where(SkillTaxonomy.id == skill_id)
    )
    row = result.scalar_one_or_none()
    return row


@router.post(
    "/",
    response_model=SkillRelationshipListResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Skill Relationships"],
)
async def create_skill_relationships(
    request: SkillRelationshipBatchCreate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_any_role("Admin", "Recruiter")),
) -> JSONResponse:
    """
    Create skill relationship entries.

    This endpoint accepts a batch of skill relationships, validating the data
    and creating database records for each relationship between skills.
    """
    try:
        logger.info(f"Creating {len(request.relationships)} skill relationships")

        # Validate relationships list
        if not request.relationships or len(request.relationships) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one relationship must be provided",
            )

        # Get organization ID from token
        organization_id = token_data.organization_id
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization ID is required",
            )

        created_relationships = []
        for rel in request.relationships:
            # Validate relationship type
            validate_relationship_type(rel.relationship_type)

            # Parse and validate UUIDs
            try:
                source_uuid = UUID(rel.source_skill_id)
                target_uuid = UUID(rel.target_skill_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for relationship, skipping")
                continue

            # Verify source and target skills exist
            source_exists = await db.execute(
                select(SkillTaxonomy.id).where(SkillTaxonomy.id == source_uuid)
            )
            target_exists = await db.execute(
                select(SkillTaxonomy.id).where(SkillTaxonomy.id == target_uuid)
            )

            if not source_exists.scalar_one_or_none():
                logger.warning(f"Source skill {rel.source_skill_id} not found, skipping")
                continue
            if not target_exists.scalar_one_or_none():
                logger.warning(f"Target skill {rel.target_skill_id} not found, skipping")
                continue

            # Check if relationship already exists
            existing = await db.execute(
                select(SkillRelationship).where(
                    SkillRelationship.source_skill_id == source_uuid,
                    SkillRelationship.target_skill_id == target_uuid,
                    SkillRelationship.relationship_type == rel.relationship_type,
                    SkillRelationship.organization_id == organization_id,
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(
                    f"Relationship {rel.source_skill_id} -> {rel.target_skill_id} "
                    f"({rel.relationship_type}) already exists, skipping"
                )
                continue

            # Create new relationship
            new_relationship = SkillRelationship(
                source_skill_id=source_uuid,
                target_skill_id=target_uuid,
                relationship_type=rel.relationship_type,
                weight=rel.weight,
                extra_metadata=rel.extra_metadata,
                is_active=rel.is_active,
                organization_id=organization_id,
            )
            db.add(new_relationship)
            await db.flush()

            # Get skill names for response
            source_name = await get_skill_name(db, source_uuid)
            target_name = await get_skill_name(db, target_uuid)

            created_relationships.append({
                "id": str(new_relationship.id),
                "source_skill_id": str(new_relationship.source_skill_id),
                "target_skill_id": str(new_relationship.target_skill_id),
                "source_skill_name": source_name,
                "target_skill_name": target_name,
                "relationship_type": new_relationship.relationship_type,
                "weight": new_relationship.weight,
                "extra_metadata": new_relationship.extra_metadata,
                "is_active": new_relationship.is_active,
                "organization_id": str(new_relationship.organization_id),
                "created_at": new_relationship.created_at.isoformat(),
                "updated_at": new_relationship.updated_at.isoformat(),
            })

        await db.commit()

        response_data = {
            "relationships": created_relationships,
            "total_count": len(created_relationships),
        }

        logger.info(f"Created {len(created_relationships)} skill relationships")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill relationships: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill relationships: {str(e)}",
        ) from e


@router.get("/", tags=["Skill Relationships"])
async def list_skill_relationships(
    source_skill_id: Optional[str] = Query(None, description="Filter by source skill UUID"),
    target_skill_id: Optional[str] = Query(None, description="Filter by target skill UUID"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_token),
) -> JSONResponse:
    """
    List skill relationship entries with optional filters.
    """
    try:
        logger.info(
            f"Listing skill relationships with filters - "
            f"source: {source_skill_id}, target: {target_skill_id}, "
            f"type: {relationship_type}, is_active: {is_active}"
        )

        # Build query
        query = select(SkillRelationship)

        if source_skill_id:
            try:
                source_uuid = UUID(source_skill_id)
                query = query.where(SkillRelationship.source_skill_id == source_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid source_skill_id format",
                )

        if target_skill_id:
            try:
                target_uuid = UUID(target_skill_id)
                query = query.where(SkillRelationship.target_skill_id == target_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid target_skill_id format",
                )

        if relationship_type:
            validate_relationship_type(relationship_type)
            query = query.where(SkillRelationship.relationship_type == relationship_type)

        if is_active is not None:
            query = query.where(SkillRelationship.is_active == is_active)

        # Filter by organization
        organization_id = token_data.organization_id
        if organization_id:
            query = query.where(SkillRelationship.organization_id == organization_id)

        query = query.order_by(SkillRelationship.created_at.desc())

        result = await db.execute(query)
        relationships = result.scalars().all()

        # Build response with skill names
        relationships_list = []
        for r in relationships:
            source_name = await get_skill_name(db, r.source_skill_id)
            target_name = await get_skill_name(db, r.target_skill_id)

            relationships_list.append({
                "id": str(r.id),
                "source_skill_id": str(r.source_skill_id),
                "target_skill_id": str(r.target_skill_id),
                "source_skill_name": source_name,
                "target_skill_name": target_name,
                "relationship_type": r.relationship_type,
                "weight": r.weight,
                "extra_metadata": r.extra_metadata,
                "is_active": r.is_active,
                "organization_id": str(r.organization_id),
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            })

        response_data = {
            "relationships": relationships_list,
            "total_count": len(relationships_list),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing skill relationships: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill relationships: {str(e)}",
        ) from e


@router.get("/{relationship_id}", tags=["Skill Relationships"])
async def get_skill_relationship(
    relationship_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_token),
) -> JSONResponse:
    """
    Get a specific skill relationship entry by ID.
    """
    try:
        logger.info(f"Getting skill relationship: {relationship_id}")

        # Parse UUID
        try:
            relationship_uuid = UUID(relationship_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid relationship ID format",
            )

        # Query database
        result = await db.execute(
            select(SkillRelationship).where(SkillRelationship.id == relationship_uuid)
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill relationship not found: {relationship_id}",
            )

        # Get skill names
        source_name = await get_skill_name(db, relationship.source_skill_id)
        target_name = await get_skill_name(db, relationship.target_skill_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(relationship.id),
                "source_skill_id": str(relationship.source_skill_id),
                "target_skill_id": str(relationship.target_skill_id),
                "source_skill_name": source_name,
                "target_skill_name": target_name,
                "relationship_type": relationship.relationship_type,
                "weight": relationship.weight,
                "extra_metadata": relationship.extra_metadata,
                "is_active": relationship.is_active,
                "organization_id": str(relationship.organization_id),
                "created_at": relationship.created_at.isoformat(),
                "updated_at": relationship.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill relationship: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill relationship: {str(e)}",
        ) from e


@router.put("/{relationship_id}", tags=["Skill Relationships"])
async def update_skill_relationship(
    relationship_id: str,
    request: SkillRelationshipUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_any_role("Admin", "Recruiter")),
) -> JSONResponse:
    """
    Update a skill relationship entry.
    """
    try:
        logger.info(f"Updating skill relationship: {relationship_id}")

        # Parse UUID
        try:
            relationship_uuid = UUID(relationship_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid relationship ID format",
            )

        # Get existing relationship
        result = await db.execute(
            select(SkillRelationship).where(SkillRelationship.id == relationship_uuid)
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill relationship not found: {relationship_id}",
            )

        # Update fields if provided
        if request.source_skill_id is not None:
            try:
                source_uuid = UUID(request.source_skill_id)
                # Verify skill exists
                exists = await db.execute(
                    select(SkillTaxonomy.id).where(SkillTaxonomy.id == source_uuid)
                )
                if not exists.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Source skill not found: {request.source_skill_id}",
                    )
                relationship.source_skill_id = source_uuid
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid source_skill_id format",
                )

        if request.target_skill_id is not None:
            try:
                target_uuid = UUID(request.target_skill_id)
                # Verify skill exists
                exists = await db.execute(
                    select(SkillTaxonomy.id).where(SkillTaxonomy.id == target_uuid)
                )
                if not exists.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Target skill not found: {request.target_skill_id}",
                    )
                relationship.target_skill_id = target_uuid
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid target_skill_id format",
                )

        if request.relationship_type is not None:
            validate_relationship_type(request.relationship_type)
            relationship.relationship_type = request.relationship_type

        if request.weight is not None:
            relationship.weight = request.weight

        if request.extra_metadata is not None:
            relationship.extra_metadata = request.extra_metadata

        if request.is_active is not None:
            relationship.is_active = request.is_active

        await db.commit()
        await db.refresh(relationship)

        # Get skill names
        source_name = await get_skill_name(db, relationship.source_skill_id)
        target_name = await get_skill_name(db, relationship.target_skill_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(relationship.id),
                "source_skill_id": str(relationship.source_skill_id),
                "target_skill_id": str(relationship.target_skill_id),
                "source_skill_name": source_name,
                "target_skill_name": target_name,
                "relationship_type": relationship.relationship_type,
                "weight": relationship.weight,
                "extra_metadata": relationship.extra_metadata,
                "is_active": relationship.is_active,
                "organization_id": str(relationship.organization_id),
                "created_at": relationship.created_at.isoformat(),
                "updated_at": relationship.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill relationship: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill relationship: {str(e)}",
        ) from e


@router.delete("/{relationship_id}", tags=["Skill Relationships"])
async def delete_skill_relationship(
    relationship_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_any_role("Admin", "Recruiter")),
) -> JSONResponse:
    """
    Delete a skill relationship entry.
    """
    try:
        logger.info(f"Deleting skill relationship: {relationship_id}")

        # Parse UUID
        try:
            relationship_uuid = UUID(relationship_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid relationship ID format",
            )

        # Get existing relationship
        result = await db.execute(
            select(SkillRelationship).where(SkillRelationship.id == relationship_uuid)
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill relationship not found: {relationship_id}",
            )

        # Delete
        await db.delete(relationship)
        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Skill relationship deleted successfully", "id": relationship_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting skill relationship: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill relationship: {str(e)}",
        ) from e


@router.delete("/skill/{skill_id}", tags=["Skill Relationships"])
async def delete_skill_relationships_by_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_any_role("Admin", "Recruiter")),
) -> JSONResponse:
    """
    Delete all relationships for a specific skill (as source or target).
    """
    try:
        logger.info(f"Deleting all relationships for skill: {skill_id}")

        # Parse UUID
        try:
            skill_uuid = UUID(skill_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid skill ID format",
            )

        # Get organization filter
        organization_id = token_data.organization_id

        # Count relationships where skill is source or target
        from sqlalchemy import or_

        count_query = select(SkillRelationship).where(
            or_(
                SkillRelationship.source_skill_id == skill_uuid,
                SkillRelationship.target_skill_id == skill_uuid,
            )
        )
        if organization_id:
            count_query = count_query.where(SkillRelationship.organization_id == organization_id)

        result = await db.execute(count_query)
        relationships = result.scalars().all()
        deleted_count = len(relationships)

        # Delete
        delete_stmt = delete(SkillRelationship).where(
            or_(
                SkillRelationship.source_skill_id == skill_uuid,
                SkillRelationship.target_skill_id == skill_uuid,
            )
        )
        if organization_id:
            delete_stmt = delete_stmt.where(SkillRelationship.organization_id == organization_id)

        await db.execute(delete_stmt)
        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Deleted {deleted_count} relationships for skill: {skill_id}",
                "deleted_count": deleted_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting relationships for skill {skill_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete relationships: {str(e)}",
        ) from e


@router.get("/types/", tags=["Skill Relationships"])
async def list_relationship_types(
    token_data: TokenData = Depends(get_current_token),
) -> JSONResponse:
    """
    List all available relationship types.
    """
    types = [
        {
            "value": rt.value,
            "label": rt.value.replace("_", " ").title(),
            "description": {
                "parent_child": "Hierarchical relationship (e.g., Frontend -> React)",
                "similar": "Similar skills that can be substituted (e.g., React ~ Vue)",
                "prerequisite": "One skill is required before another",
                "related": "General relationship (skills often used together)",
            }.get(rt.value, ""),
        }
        for rt in RelationshipType
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"relationship_types": types, "total_count": len(types)},
    )
