"""
Skill taxonomy management endpoints.

This module provides endpoints for managing industry-specific skill taxonomies,
including CRUD operations for creating, reading, updating, and deleting skill
taxonomy entries with variants and context information.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.skill_taxonomy import SkillTaxonomy
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class SkillVariant(BaseModel):
    """Individual skill variant definition."""

    name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category (e.g., web_framework, language, database)")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings for this skill")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata (description, category, etc.)")
    is_active: bool = Field(True, description="Whether this taxonomy entry is currently active")


class SkillTaxonomyCreate(BaseModel):
    """Request model for creating skill taxonomies."""

    industry: str = Field(..., description="Industry sector (tech, healthcare, finance, etc.)")
    skills: List[SkillVariant] = Field(..., description="List of skill taxonomy entries to create")


class SkillTaxonomyUpdate(BaseModel):
    """Request model for updating a skill taxonomy."""

    skill_name: Optional[str] = Field(None, description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: Optional[List[str]] = Field(None, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: Optional[bool] = Field(None, description="Whether this entry is active")


class SkillTaxonomyResponse(BaseModel):
    """Response model for a single skill taxonomy entry."""

    id: str = Field(..., description="Unique identifier for the taxonomy entry")
    industry: str = Field(..., description="Industry sector")
    skill_name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    extra_metadata: Optional[dict] = Field(None, description="Additional skill metadata")
    is_active: bool = Field(..., description="Whether this entry is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SkillTaxonomyListResponse(BaseModel):
    """Response model for listing skill taxonomies."""

    industry: str = Field(..., description="Industry sector")
    skills: List[SkillTaxonomyResponse] = Field(..., description="List of skill taxonomy entries")
    total_count: int = Field(..., description="Total number of entries")


@router.post(
    "/",
    response_model=SkillTaxonomyListResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Skill Taxonomies"],
)
async def create_skill_taxonomies(
    request: SkillTaxonomyCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create skill taxonomy entries for an industry.

    This endpoint accepts a batch of skill taxonomy entries for a specific industry,
    validating the data and creating database records for each skill with its variants
    and context information.
    """
    try:
        logger.info(f"Creating {len(request.skills)} skill taxonomies for industry: {request.industry}")

        # Validate industry name
        if not request.industry or len(request.industry.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Industry cannot be empty",
            )

        # Validate skills list
        if not request.skills or len(request.skills) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one skill must be provided",
            )

        created_skills = []
        for skill in request.skills:
            # Check if skill already exists
            existing = await db.execute(
                select(SkillTaxonomy).where(
                    SkillTaxonomy.industry == request.industry,
                    SkillTaxonomy.skill_name == skill.name,
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(f"Skill {skill.name} already exists for industry {request.industry}, skipping")
                continue

            # Create new skill taxonomy
            new_taxonomy = SkillTaxonomy(
                industry=request.industry,
                skill_name=skill.name,
                context=skill.context,
                variants=skill.variants,
                extra_metadata=skill.extra_metadata,
                is_active=skill.is_active,
            )
            db.add(new_taxonomy)
            await db.flush()

            created_skills.append({
                "id": str(new_taxonomy.id),
                "industry": new_taxonomy.industry,
                "skill_name": new_taxonomy.skill_name,
                "context": new_taxonomy.context,
                "variants": new_taxonomy.variants or [],
                "extra_metadata": new_taxonomy.extra_metadata,
                "is_active": new_taxonomy.is_active,
                "created_at": new_taxonomy.created_at.isoformat(),
                "updated_at": new_taxonomy.updated_at.isoformat(),
            })

        await db.commit()

        response_data = {
            "industry": request.industry,
            "skills": created_skills,
            "total_count": len(created_skills),
        }

        logger.info(f"Created {len(created_skills)} skill taxonomies for industry: {request.industry}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill taxonomies: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill taxonomies: {str(e)}",
        ) from e


@router.get("/", tags=["Skill Taxonomies"])
async def list_skill_taxonomies(
    industry: Optional[str] = Query(None, description="Filter by industry sector"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List skill taxonomy entries with optional filters.
    """
    try:
        logger.info(f"Listing skill taxonomies with filters - industry: {industry}, is_active: {is_active}")

        # Build query
        query = select(SkillTaxonomy)

        if industry:
            query = query.where(SkillTaxonomy.industry == industry)
        if is_active is not None:
            query = query.where(SkillTaxonomy.is_active == is_active)

        query = query.order_by(SkillTaxonomy.skill_name)

        result = await db.execute(query)
        taxonomies = result.scalars().all()

        # Build response
        skills_list = [
            {
                "id": str(t.id),
                "industry": t.industry,
                "skill_name": t.skill_name,
                "context": t.context,
                "variants": t.variants or [],
                "extra_metadata": t.extra_metadata,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            }
            for t in taxonomies
        ]

        response_data = {
            "industry": industry or "all",
            "skills": skills_list,
            "total_count": len(skills_list),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing skill taxonomies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill taxonomies: {str(e)}",
        ) from e


@router.get("/{taxonomy_id}", tags=["Skill Taxonomies"])
async def get_skill_taxonomy(
    taxonomy_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific skill taxonomy entry by ID.
    """
    try:
        logger.info(f"Getting skill taxonomy: {taxonomy_id}")

        # Parse UUID
        try:
            taxonomy_uuid = UUID(taxonomy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid taxonomy ID format",
            )

        # Query database
        result = await db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.id == taxonomy_uuid)
        )
        taxonomy = result.scalar_one_or_none()

        if not taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill taxonomy not found: {taxonomy_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(taxonomy.id),
                "industry": taxonomy.industry,
                "skill_name": taxonomy.skill_name,
                "context": taxonomy.context,
                "variants": taxonomy.variants or [],
                "extra_metadata": taxonomy.extra_metadata,
                "is_active": taxonomy.is_active,
                "created_at": taxonomy.created_at.isoformat(),
                "updated_at": taxonomy.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill taxonomy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill taxonomy: {str(e)}",
        ) from e


@router.put("/{taxonomy_id}", tags=["Skill Taxonomies"])
async def update_skill_taxonomy(
    taxonomy_id: str,
    request: SkillTaxonomyUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a skill taxonomy entry.
    """
    try:
        logger.info(f"Updating skill taxonomy: {taxonomy_id}")

        # Parse UUID
        try:
            taxonomy_uuid = UUID(taxonomy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid taxonomy ID format",
            )

        # Get existing taxonomy
        result = await db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.id == taxonomy_uuid)
        )
        taxonomy = result.scalar_one_or_none()

        if not taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill taxonomy not found: {taxonomy_id}",
            )

        # Update fields if provided
        if request.skill_name is not None:
            taxonomy.skill_name = request.skill_name
        if request.context is not None:
            taxonomy.context = request.context
        if request.variants is not None:
            taxonomy.variants = request.variants
        if request.extra_metadata is not None:
            taxonomy.extra_metadata = request.extra_metadata
        if request.is_active is not None:
            taxonomy.is_active = request.is_active

        await db.commit()
        await db.refresh(taxonomy)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(taxonomy.id),
                "industry": taxonomy.industry,
                "skill_name": taxonomy.skill_name,
                "context": taxonomy.context,
                "variants": taxonomy.variants or [],
                "extra_metadata": taxonomy.extra_metadata,
                "is_active": taxonomy.is_active,
                "created_at": taxonomy.created_at.isoformat(),
                "updated_at": taxonomy.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill taxonomy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill taxonomy: {str(e)}",
        ) from e


@router.delete("/{taxonomy_id}", tags=["Skill Taxonomies"])
async def delete_skill_taxonomy(
    taxonomy_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a skill taxonomy entry.
    """
    try:
        logger.info(f"Deleting skill taxonomy: {taxonomy_id}")

        # Parse UUID
        try:
            taxonomy_uuid = UUID(taxonomy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid taxonomy ID format",
            )

        # Get existing taxonomy
        result = await db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.id == taxonomy_uuid)
        )
        taxonomy = result.scalar_one_or_none()

        if not taxonomy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill taxonomy not found: {taxonomy_id}",
            )

        # Delete
        await db.delete(taxonomy)
        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Skill taxonomy deleted successfully", "id": taxonomy_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting skill taxonomy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill taxonomy: {str(e)}",
        ) from e


@router.delete("/industry/{industry}", tags=["Skill Taxonomies"])
async def delete_skill_taxonomies_by_industry(
    industry: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete all skill taxonomy entries for a specific industry.
    """
    try:
        logger.info(f"Deleting all skill taxonomies for industry: {industry}")

        # Count first
        count_result = await db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.industry == industry)
        )
        taxonomies = count_result.scalars().all()
        deleted_count = len(taxonomies)

        # Delete
        await db.execute(
            delete(SkillTaxonomy).where(SkillTaxonomy.industry == industry)
        )
        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Deleted {deleted_count} skill taxonomies for industry: {industry}"},
        )

    except Exception as e:
        logger.error(f"Error deleting skill taxonomies for industry {industry}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill taxonomies: {str(e)}",
        ) from e


@router.post("/load/industry/{industry}", tags=["Skill Taxonomies"])
async def load_industry_taxonomy(
    industry: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Load predefined skills for an industry.

    This endpoint loads common/standard skills for specific industries,
    making it easy to bootstrap the system with known skill taxonomies.
    """
    # Predefined industry skills
    industry_skills = {
        "technology": [
            {"name": "Python", "context": "programming_language", "variants": ["python", "Python 3", "Py3", "py"]},
            {"name": "Java", "context": "programming_language", "variants": ["java", "Java 8", "Java 11", "Java 17"]},
            {"name": "JavaScript", "context": "programming_language", "variants": ["javascript", "JS", "js", "ECMAScript"]},
            {"name": "React", "context": "web_framework", "variants": ["React", "ReactJS", "React.js", "react"]},
            {"name": "Angular", "context": "web_framework", "variants": ["Angular", "angular", "AngularJS"]},
            {"name": "Vue", "context": "web_framework", "variants": ["Vue", "Vue.js", "vuejs"]},
            {"name": "Django", "context": "web_framework", "variants": ["Django", "django", "DRF"]},
            {"name": "FastAPI", "context": "web_framework", "variants": ["FastAPI", "fastapi", "Starlette"]},
            {"name": "Flask", "context": "web_framework", "variants": ["Flask", "flask"]},
            {"name": "PostgreSQL", "context": "database", "variants": ["PostgreSQL", "postgres", "Postgres", "psql"]},
            {"name": "MySQL", "context": "database", "variants": ["MySQL", "mysql"]},
            {"name": "Redis", "context": "database", "variants": ["Redis", "redis"]},
            {"name": "MongoDB", "context": "database", "variants": ["MongoDB", "mongodb", "mongo"]},
            {"name": "Docker", "context": "devops", "variants": ["Docker", "docker"]},
            {"name": "Kubernetes", "context": "devops", "variants": ["Kubernetes", "k8s", "k8s"]},
            {"name": "AWS", "context": "cloud", "variants": ["Amazon Web Services", "AWS", "aws"]},
            {"name": "Git", "context": "vcs", "variants": ["Git", "git"]},
        ],
        "finance": [
            {"name": "Excel", "context": "spreadsheet", "variants": ["Excel", "MS Excel"]},
            {"name": "SAP", "context": "erp", "variants": ["SAP", "sap"]},
            {"name": "QuickBooks", "context": "accounting", "variants": ["QuickBooks", "QB"]},
        ],
        "healthcare": [
            {"name": "HL7", "context": "interoperability", "variants": ["HL7", "hl7"]},
            {"name": "DICOM", "context": "medical_imaging", "variants": ["DICOM", "dicom"]},
        ],
    }

    if industry not in industry_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown industry: {industry}. Available: {list(industry_skills.keys())}",
        )

    skills_data = industry_skills[industry]

    try:
        logger.info(f"Loading {len(skills_data)} predefined skills for industry: {industry}")

        created_count = 0
        for skill_data in skills_data:
            # Check if exists
            existing = await db.execute(
                select(SkillTaxonomy).where(
                    SkillTaxonomy.industry == industry,
                    SkillTaxonomy.skill_name == skill_data["name"],
                )
            )
            if existing.scalar_one_or_none():
                continue

            new_taxonomy = SkillTaxonomy(
                industry=industry,
                skill_name=skill_data["name"],
                context=skill_data["context"],
                variants=skill_data["variants"],
                is_active=True,
            )
            db.add(new_taxonomy)
            created_count += 1

        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "industry": industry,
                "loaded_count": created_count,
                "message": f"Loaded {created_count} skill taxonomies for industry: {industry}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading industry taxonomies: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load industry taxonomies: {str(e)}",
        ) from e


@router.post("/load/it", tags=["Skill Taxonomies"])
async def load_it_taxonomy(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Load comprehensive IT taxonomy from JSON file.

    This endpoint loads the complete IT skill taxonomy including:
    - Hard Skills (programming languages, frameworks, tools)
    - Soft Skills (communication, teamwork, etc.)
    - Role definitions with required skills
    - Grade system structure (for future implementation)
    """
    # Path to IT taxonomy JSON file
    taxonomy_path = Path(__file__).parent.parent / "data" / "industry_taxonomies" / "it_taxonomy.json"

    if not taxonomy_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IT taxonomy file not found at {taxonomy_path}",
        )

    try:
        with open(taxonomy_path, "r", encoding="utf-8") as f:
            taxonomy_data = json.load(f)

        logger.info(f"Loading IT taxonomy from {taxonomy_path}")

        created_count = 0
        skipped_count = 0

        # Process hard skills
        async def process_skill_category(category_data: dict, parent_category: str = ""):
            nonlocal created_count, skipped_count

            for key, value in category_data.items():
                if key == "variants" or key == "related_skills" or key == "grade_min":
                    continue

                if isinstance(value, dict):
                    # Check if this is a skill entry (has 'name' field)
                    if "name" in value:
                        skill_data = value
                        skill_name = skill_data.get("name", key)
                        context = skill_data.get("context", parent_category)
                        variants = skill_data.get("variants", [])

                        # Check if skill already exists
                        existing = await db.execute(
                            select(SkillTaxonomy).where(
                                SkillTaxonomy.industry == "it",
                                SkillTaxonomy.skill_name == skill_name,
                            )
                        )
                        if existing.first():
                            skipped_count += 1
                        else:
                            # Include metadata with grade info
                            metadata = {
                                "category": parent_category,
                                "grade_min": skill_data.get("grade_min", "J1"),
                            }
                            if "related_skills" in skill_data:
                                metadata["related_skills"] = skill_data["related_skills"]

                            new_taxonomy = SkillTaxonomy(
                                industry="it",
                                skill_name=skill_name,
                                context=context,
                                variants=variants,
                                extra_metadata=metadata,
                                is_active=True,
                            )
                            db.add(new_taxonomy)
                            created_count += 1
                    else:
                        # Recursively process nested categories
                        new_parent = f"{parent_category}/{key}" if parent_category else key
                        await process_skill_category(value, new_parent)

        # Process hard skills
        if "hard_skills" in taxonomy_data:
            await process_skill_category(taxonomy_data["hard_skills"])

        # Process soft skills (store as a separate type)
        if "soft_skills" in taxonomy_data:
            await process_skill_category(taxonomy_data["soft_skills"])

        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "industry": "it",
                "loaded_count": created_count,
                "skipped_count": skipped_count,
                "message": f"Loaded {created_count} IT skill taxonomies (skipped {skipped_count} existing entries)",
                "metadata": taxonomy_data.get("metadata", {}),
            },
        )

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing IT taxonomy JSON: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse IT taxonomy file: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error loading IT taxonomy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load IT taxonomy: {str(e)}",
        ) from e
