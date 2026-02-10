"""
Candidate tag management endpoints.

This module provides endpoints for managing organization-specific candidate tags,
including CRUD operations for creating, reading, updating, and deleting tag
configurations, as well as assigning/removing tags from candidates (resumes).
Tags enable flexible categorization and prioritization (e.g., 'High Priority', 'Remote', 'Referral').
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType
from models.resume import Resume
from analyzers.tag_suggester import TagSuggester

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum resume text length to prevent processing timeouts
MAX_RESUME_TEXT_LENGTH = 50000  # 50,000 characters (~10 pages of text)


class CandidateTagCreate(BaseModel):
    """Request model for creating a candidate tag."""

    organization_id: str = Field(..., description="Organization ID that owns this tag")
    tag_name: str = Field(..., min_length=1, max_length=100, description="Name of the tag (e.g., 'High Priority', 'Remote')")
    tag_order: int = Field(0, ge=0, description="Order in which this tag appears in the UI")
    is_default: bool = Field(False, description="Whether this is a default tag for new organizations")
    is_active: bool = Field(True, description="Whether this tag is currently active")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code for UI display (e.g., #EF4444)")
    description: Optional[str] = Field(None, max_length=500, description="Description of when to use this tag")


class CandidateTagUpdate(BaseModel):
    """Request model for updating a candidate tag."""

    tag_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the tag")
    tag_order: Optional[int] = Field(None, ge=0, description="Order in which this tag appears in the UI")
    is_default: Optional[bool] = Field(None, description="Whether this is a default tag")
    is_active: Optional[bool] = Field(None, description="Whether this tag is currently active")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code for UI display")
    description: Optional[str] = Field(None, max_length=500, description="Description of when to use this tag")


class CandidateTagResponse(BaseModel):
    """Response model for a single candidate tag."""

    id: str = Field(..., description="Unique identifier for the tag")
    organization_id: str = Field(..., description="Organization ID that owns this tag")
    tag_name: str = Field(..., description="Name of the tag")
    tag_order: int = Field(..., description="Order of this tag in the UI")
    is_default: bool = Field(..., description="Whether this is a default tag")
    is_active: bool = Field(..., description="Whether this tag is currently active")
    color: Optional[str] = Field(None, description="Hex color code for UI display")
    description: Optional[str] = Field(None, description="Description of when to use this tag")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CandidateTagListResponse(BaseModel):
    """Response model for listing candidate tags."""

    organization_id: str = Field(..., description="Organization ID")
    tags: List[CandidateTagResponse] = Field(..., description="List of candidate tags")
    total_count: int = Field(..., description="Total number of tags")


class AssignTagRequest(BaseModel):
    """Request model for assigning a tag to a candidate."""

    tag_id: str = Field(..., description="Tag ID to assign to the candidate")
    recruiter_id: Optional[str] = Field(None, description="Optional recruiter ID who is assigning the tag")


class CandidateTagsResponse(BaseModel):
    """Response model for tags assigned to a candidate."""

    resume_id: str = Field(..., description="Resume ID")
    tags: List[CandidateTagResponse] = Field(..., description="List of tags assigned to this candidate")
    total_count: int = Field(..., description="Total number of tags assigned")


class TagSuggestion(BaseModel):
    """Response model for a single tag suggestion."""

    id: str = Field(..., description="Unique identifier for the tag")
    organization_id: str = Field(..., description="Organization ID that owns this tag")
    tag_name: str = Field(..., description="Name of the tag")
    tag_order: int = Field(..., description="Order of this tag in the UI")
    is_default: bool = Field(..., description="Whether this is a default tag")
    is_active: bool = Field(..., description="Whether this tag is currently active")
    color: Optional[str] = Field(None, description="Hex color code for UI display")
    description: Optional[str] = Field(None, description="Description of when to use this tag")
    usage_count: int = Field(..., description="Number of times this tag has been used")


class TagSuggestionsResponse(BaseModel):
    """Response model for tag suggestions."""

    organization_id: str = Field(..., description="Organization ID")
    suggestions: List[TagSuggestion] = Field(..., description="List of tag suggestions")
    total_count: int = Field(..., description="Total number of suggestions")


class MergeTagsRequest(BaseModel):
    """Request model for merging two tags."""

    source_tag_id: str = Field(..., description="ID of the tag to merge from (will be deleted)")
    target_tag_id: str = Field(..., description="ID of the tag to merge into (will be kept)")


class MergeTagsResponse(BaseModel):
    """Response model for tag merge operation."""

    message: str = Field(..., description="Success message")
    source_tag_id: str = Field(..., description="ID of the source tag that was deleted")
    target_tag_id: str = Field(..., description="ID of the target tag")
    candidates_transferred: int = Field(..., description="Number of candidates transferred from source to target tag")


class IntelligentTagSuggestion(BaseModel):
    """Individual intelligent tag suggestion with relevance score."""

    id: str = Field(..., description="Unique identifier for the tag")
    organization_id: str = Field(..., description="Organization ID that owns this tag")
    tag_name: str = Field(..., description="Name of the tag")
    tag_order: int = Field(..., description="Order of this tag in the UI")
    is_default: bool = Field(..., description="Whether this is a default tag")
    is_active: bool = Field(..., description="Whether this tag is currently active")
    color: Optional[str] = Field(None, description="Hex color code for UI display")
    description: Optional[str] = Field(None, description="Description of when to use this tag")
    relevance_score: float = Field(..., description="Relevance score (0-1)")


class IntelligentTagSuggestionResponse(BaseModel):
    """Response model for intelligent tag suggestions."""

    organization_id: str = Field(..., description="Organization ID")
    resume_id: str = Field(..., description="Resume ID that was analyzed")
    suggestions: List[IntelligentTagSuggestion] = Field(..., description="List of intelligent tag suggestions")
    keywords_extracted: List[str] = Field(..., description="Keywords extracted from resume for reference")
    total_count: int = Field(..., description="Total number of suggestions returned")


@router.post(
    "/",
    response_model=CandidateTagResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Tags"],
)
async def create_candidate_tag(
    request: CandidateTagCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a candidate tag for an organization.

    This endpoint creates a new tag configuration for a specific organization,
    enabling flexible categorization and prioritization of candidates.

    Args:
        request: Request body containing tag details
        db: Database session

    Returns:
        JSON response with created tag details

    Raises:
        HTTPException(409): If tag with same name already exists for this organization
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/candidate-tags/",
        ...     json={
        ...         "organization_id": "org-123",
        ...         "tag_name": "High Priority",
        ...         "tag_order": 1,
        ...         "is_default": False,
        ...         "is_active": True,
        ...         "color": "#EF4444",
        ...         "description": "For urgent or high-priority candidates"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating candidate tag '{request.tag_name}' for organization: {request.organization_id}")

        # Check if tag with same name already exists for this organization
        existing = await db.execute(
            select(CandidateTag).where(
                CandidateTag.organization_id == request.organization_id,
                CandidateTag.tag_name == request.tag_name,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{request.tag_name}' already exists for this organization",
            )

        # Create new tag
        new_tag = CandidateTag(
            organization_id=request.organization_id,
            tag_name=request.tag_name,
            tag_order=request.tag_order,
            is_default=request.is_default,
            is_active=request.is_active,
            color=request.color,
            description=request.description,
        )
        db.add(new_tag)
        await db.flush()

        response_data = {
            "id": str(new_tag.id),
            "organization_id": new_tag.organization_id,
            "tag_name": new_tag.tag_name,
            "tag_order": new_tag.tag_order,
            "is_default": new_tag.is_default,
            "is_active": new_tag.is_active,
            "color": new_tag.color,
            "description": new_tag.description,
            "created_at": new_tag.created_at.isoformat(),
            "updated_at": new_tag.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created candidate tag '{request.tag_name}' with ID: {new_tag.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate tag: {str(e)}",
        ) from e


@router.get("/", tags=["Candidate Tags"])
async def list_candidate_tags(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List candidate tags with optional filters.

    This endpoint retrieves tag configurations with support for filtering
    by organization, active status, and default status.

    Args:
        organization_id: Optional organization ID filter
        is_active: Optional active status filter
        is_default: Optional default status filter
        db: Database session

    Returns:
        JSON response with list of tags

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("/api/candidate-tags/?organization_id=org-123")
        >>> response.json()
        {
            "organization_id": "org-123",
            "tags": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Listing candidate tags with filters - organization_id: {organization_id}, is_active: {is_active}")

        # Build query
        query = select(CandidateTag)

        if organization_id:
            query = query.where(CandidateTag.organization_id == organization_id)
        if is_active is not None:
            query = query.where(CandidateTag.is_active == is_active)
        if is_default is not None:
            query = query.where(CandidateTag.is_default == is_default)

        query = query.order_by(CandidateTag.tag_order, CandidateTag.tag_name)

        result = await db.execute(query)
        tags = result.scalars().all()

        # If organization_id filter was provided, use it in response
        response_org_id = organization_id if organization_id and len(tags) > 0 else "all"

        # Build response
        tags_data = []
        for tag in tags:
            tags_data.append({
                "id": str(tag.id),
                "organization_id": tag.organization_id,
                "tag_name": tag.tag_name,
                "tag_order": tag.tag_order,
                "is_default": tag.is_default,
                "is_active": tag.is_active,
                "color": tag.color,
                "description": tag.description,
                "created_at": tag.created_at.isoformat(),
                "updated_at": tag.updated_at.isoformat(),
            })

        response_data = {
            "organization_id": response_org_id,
            "tags": tags_data,
            "total_count": len(tags_data),
        }

        logger.info(f"Retrieved {len(tags_data)} candidate tags")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing candidate tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidate tags: {str(e)}",
        ) from e


@router.get("/suggestions", tags=["Candidate Tags"])
async def get_tag_suggestions(
    organization_id: str = Query(..., description="Organization ID to get suggestions for"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of suggestions to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get tag suggestions based on usage for an organization.

    This endpoint returns the most frequently used tags for an organization,
    sorted by usage count (number of times tags have been added to candidates).
    Useful for displaying popular tags in autocomplete and suggestion UIs.

    Args:
        organization_id: Organization ID to get suggestions for
        limit: Maximum number of suggestions to return (default: 10, max: 100)
        db: Database session

    Returns:
        JSON response with list of tag suggestions

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("/api/candidate-tags/suggestions?organization_id=org-123&limit=5")
        >>> response.json()
        {
            "organization_id": "org-123",
            "suggestions": [
                {
                    "id": "tag-1",
                    "organization_id": "org-123",
                    "tag_name": "High Priority",
                    "usage_count": 25,
                    ...
                }
            ],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Getting tag suggestions for organization: {organization_id}, limit: {limit}")

        # Query for tags with their usage counts
        # We need to find TAG_ADDED activities that haven't been removed
        # This is complex because we need to account for TAG_REMOVED activities

        # First, get all tags for the organization that are active
        tags_result = await db.execute(
            select(CandidateTag).where(
                CandidateTag.organization_id == organization_id,
                CandidateTag.is_active == True,
            ).order_by(CandidateTag.tag_order, CandidateTag.tag_name)
        )
        tags = tags_result.scalars().all()

        if not tags:
            # No tags found for this organization
            response_data = {
                "organization_id": organization_id,
                "suggestions": [],
                "total_count": 0,
            }
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data,
            )

        # For each tag, calculate its current usage (number of resumes currently tagged)
        tag_usage = {}
        for tag in tags:
            # Find the latest TAG_ADDED activity for each candidate
            # A tag is currently assigned if the latest activity for a tag on a candidate is TAG_ADDED
            tag_added_subquery = (
                select(
                    CandidateActivity.candidate_id,
                    func.max(CandidateActivity.created_at).label('latest_added')
                )
                .where(
                    CandidateActivity.tag_id == tag.id,
                    CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                )
                .group_by(CandidateActivity.candidate_id)
                .subquery()
            )

            # Count candidates where the latest activity for this tag is TAG_ADDED (not TAG_REMOVED)
            usage_result = await db.execute(
                select(func.count(func.distinct(tag_added_subquery.c.candidate_id)))
                .select_from(tag_added_subquery)
                .where(
                    ~select(CandidateActivity)
                    .where(
                        CandidateActivity.candidate_id == tag_added_subquery.c.candidate_id,
                        CandidateActivity.tag_id == tag.id,
                        CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                        CandidateActivity.created_at > tag_added_subquery.c.latest_added,
                    )
                    .exists()
                )
            )
            usage_count = usage_result.scalar() or 0
            tag_usage[str(tag.id)] = usage_count

        # Build suggestions list, sorted by usage count (descending), then by tag_order
        suggestions_data = []
        for tag in tags:
            suggestions_data.append({
                "id": str(tag.id),
                "organization_id": tag.organization_id,
                "tag_name": tag.tag_name,
                "tag_order": tag.tag_order,
                "is_default": tag.is_default,
                "is_active": tag.is_active,
                "color": tag.color,
                "description": tag.description,
                "usage_count": tag_usage.get(str(tag.id), 0),
            })

        # Sort by usage count (descending), then by tag_order
        suggestions_data.sort(key=lambda x: (-x["usage_count"], x["tag_order"]))

        # Apply limit
        suggestions_data = suggestions_data[:limit]

        response_data = {
            "organization_id": organization_id,
            "suggestions": suggestions_data,
            "total_count": len(suggestions_data),
        }

        logger.info(f"Retrieved {len(suggestions_data)} tag suggestions for organization: {organization_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error getting tag suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag suggestions: {str(e)}",
        ) from e


@router.get(
    "/intelligent-suggestions",
    response_model=IntelligentTagSuggestionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Candidate Tags"],
)
async def get_intelligent_tag_suggestions(
    organization_id: str = Query(..., description="Organization ID to get suggestions for"),
    resume_id: str = Query(..., description="Resume ID to analyze for tag suggestions"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of suggestions to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get intelligent tag suggestions based on resume content analysis.

    This endpoint analyzes a candidate's resume to extract keywords and intelligently
    match them against the organization's tags. Suggestions are scored based on
    keyword matching accuracy and returned in order of relevance.

    Args:
        organization_id: Organization ID to get suggestions for
        resume_id: Resume ID to analyze for tag suggestions
        limit: Maximum number of suggestions to return (default: 10, max: 100)
        db: Database session

    Returns:
        JSON response with intelligent tag suggestions and relevance scores

    Raises:
        HTTPException(404): If organization or resume is not found
        HTTPException(422): If validation fails
        HTTPException(500): If analysis or database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/candidate-tags/intelligent-suggestions"
        ...     "?organization_id=org-123&resume_id=resume-456&limit=5"
        ... )
        >>> response.json()
        {
            "organization_id": "org-123",
            "resume_id": "resume-456",
            "suggestions": [
                {
                    "id": "tag-1",
                    "organization_id": "org-123",
                    "tag_name": "Senior Developer",
                    "relevance_score": 0.85,
                    ...
                },
                ...
            ],
            "keywords_extracted": ["python", "django", "postgresql"],
            "total_count": 5
        }
    """
    try:
        logger.info(
            f"Generating intelligent tag suggestions for organization={organization_id}, "
            f"resume={resume_id}, limit={limit}"
        )

        # Validate organization_id
        if not organization_id or len(organization_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization ID cannot be empty",
            )

        # Validate resume_id
        if not resume_id or len(resume_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume ID cannot be empty",
            )

        # Fetch resume to get raw text
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Get resume text for analysis
        resume_text = resume.raw_text or ""
        if not resume_text:
            logger.warning(f"Resume {resume_id} has no text content")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "organization_id": organization_id,
                    "resume_id": resume_id,
                    "suggestions": [],
                    "keywords_extracted": [],
                    "total_count": 0,
                },
            )

        # Truncate resume text if too long to prevent processing timeouts
        original_length = len(resume_text)
        if original_length > MAX_RESUME_TEXT_LENGTH:
            logger.info(
                f"Resume text length ({original_length} chars) exceeds limit, "
                f"truncating to {MAX_RESUME_TEXT_LENGTH} chars"
            )
            resume_text = resume_text[:MAX_RESUME_TEXT_LENGTH]

        # Detect language for keyword extraction (default to english)
        language = "english" if not resume.language or resume.language.startswith("en") else resume.language

        # Fetch all active organization tags
        tags_result = await db.execute(
            select(CandidateTag).where(
                CandidateTag.organization_id == organization_id,
                CandidateTag.is_active == True,
            ).order_by(CandidateTag.tag_order, CandidateTag.tag_name)
        )
        tags = tags_result.scalars().all()

        if not tags:
            logger.info(f"No active tags found for organization: {organization_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "organization_id": organization_id,
                    "resume_id": resume_id,
                    "suggestions": [],
                    "keywords_extracted": [],
                    "total_count": 0,
                },
            )

        # Convert tags to format expected by TagSuggester
        organization_tags = []
        for tag in tags:
            organization_tags.append({
                "id": str(tag.id),
                "organization_id": tag.organization_id,
                "tag_name": tag.tag_name,
                "tag_order": tag.tag_order,
                "is_default": tag.is_default,
                "is_active": tag.is_active,
                "color": tag.color,
                "description": tag.description,
            })

        # Use TagSuggester to generate intelligent suggestions
        suggester = TagSuggester(min_score=0.3, fuzzy_threshold=0.6)
        suggestion_result = suggester.suggest_tags(
            resume_text=resume_text,
            organization_tags=organization_tags,
            limit=limit,
            language=language
        )

        if suggestion_result.get("error"):
            logger.warning(f"Tag suggestion returned error: {suggestion_result['error']}")
            # Return empty suggestions rather than failing
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "organization_id": organization_id,
                    "resume_id": resume_id,
                    "suggestions": [],
                    "keywords_extracted": [],
                    "total_count": 0,
                },
            )

        # Build response with suggestions
        suggestions_data = []
        for suggestion in suggestion_result.get("suggestions", []):
            suggestions_data.append({
                "id": suggestion.get("id"),
                "organization_id": suggestion.get("organization_id"),
                "tag_name": suggestion.get("tag_name"),
                "tag_order": suggestion.get("tag_order"),
                "is_default": suggestion.get("is_default"),
                "is_active": suggestion.get("is_active"),
                "color": suggestion.get("color"),
                "description": suggestion.get("description"),
                "relevance_score": suggestion.get("score", 0.0),
            })

        response_data = {
            "organization_id": organization_id,
            "resume_id": resume_id,
            "suggestions": suggestions_data,
            "keywords_extracted": suggestion_result.get("keywords_extracted", []),
            "total_count": len(suggestions_data),
        }

        logger.info(
            f"Generated {len(suggestions_data)} intelligent tag suggestions "
            f"for resume {resume_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {resume_id}",
        )
    except Exception as e:
        logger.error(f"Error generating intelligent tag suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate intelligent tag suggestions: {str(e)}",
        ) from e


@router.get("/{tag_id}", tags=["Candidate Tags"])
async def get_candidate_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific candidate tag by ID.

    This endpoint retrieves detailed information about a single tag.

    Args:
        tag_id: UUID of the tag
        db: Database session

    Returns:
        JSON response with tag details

    Raises:
        HTTPException(404): If tag is not found
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Retrieving candidate tag: {tag_id}")

        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        response_data = {
            "id": str(tag.id),
            "organization_id": tag.organization_id,
            "tag_name": tag.tag_name,
            "tag_order": tag.tag_order,
            "is_default": tag.is_default,
            "is_active": tag.is_active,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
        }

        logger.info(f"Retrieved candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate tag: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate tag: {str(e)}",
        ) from e


@router.get("/resume/{resume_id}", tags=["Candidate Tags"])
async def get_resume_tags(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all tags assigned to a specific resume.

    This endpoint retrieves all tags that are currently assigned to a candidate (resume)
    by checking for tag assignment activities.

    Args:
        resume_id: UUID of the resume
        db: Database session

    Returns:
        JSON response with list of tags assigned to this resume

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Retrieving tags for resume: {resume_id}")

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Get all tag_added activities for this resume
        # We need to find tags that have been added and not subsequently removed
        activities_result = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(resume_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
            ).order_by(CandidateActivity.created_at.desc())
        )
        all_tag_activities = activities_result.scalars().all()

        # Get unique tag IDs that haven't been removed
        assigned_tag_ids = set()
        for activity in all_tag_activities:
            if activity.tag_id:
                # Check if this tag has been removed after this activity
                removal_result = await db.execute(
                    select(CandidateActivity).where(
                        CandidateActivity.candidate_id == UUID(resume_id),
                        CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                        CandidateActivity.tag_id == activity.tag_id,
                        CandidateActivity.created_at > activity.created_at,
                    ).limit(1)
                )
                removal_activity = removal_result.scalar_one_or_none()

                if not removal_activity:
                    assigned_tag_ids.add(activity.tag_id)

        # Fetch tag details
        tags_data = []
        if assigned_tag_ids:
            tags_result = await db.execute(
                select(CandidateTag).where(CandidateTag.id.in_(assigned_tag_ids))
            )
            tags = tags_result.scalars().all()

            for tag in tags:
                tags_data.append({
                    "id": str(tag.id),
                    "organization_id": tag.organization_id,
                    "tag_name": tag.tag_name,
                    "tag_order": tag.tag_order,
                    "is_default": tag.is_default,
                    "is_active": tag.is_active,
                    "color": tag.color,
                    "description": tag.description,
                    "created_at": tag.created_at.isoformat(),
                    "updated_at": tag.updated_at.isoformat(),
                })

        response_data = {
            "resume_id": resume_id,
            "tags": tags_data,
            "total_count": len(tags_data),
        }

        logger.info(f"Retrieved {len(tags_data)} tags for resume: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {resume_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving resume tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume tags: {str(e)}",
        ) from e


@router.put("/{tag_id}", tags=["Candidate Tags"])
async def update_candidate_tag(
    tag_id: str,
    request: CandidateTagUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a candidate tag.

    This endpoint updates an existing tag configuration.
    Only the fields specified in the request body will be updated.

    Args:
        tag_id: UUID of the tag
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated tag details

    Raises:
        HTTPException(404): If tag is not found
        HTTPException(409): If tag name conflicts with existing tag
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Updating candidate tag: {tag_id}")

        # Get existing tag
        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        # Update fields if provided
        if request.tag_name is not None:
            # Check if new name conflicts with existing tag
            existing = await db.execute(
                select(CandidateTag).where(
                    CandidateTag.organization_id == tag.organization_id,
                    CandidateTag.tag_name == request.tag_name,
                    CandidateTag.id != UUID(tag_id),
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag '{request.tag_name}' already exists for this organization",
                )
            tag.tag_name = request.tag_name

        if request.tag_order is not None:
            tag.tag_order = request.tag_order
        if request.is_default is not None:
            tag.is_default = request.is_default
        if request.is_active is not None:
            tag.is_active = request.is_active
        if request.color is not None:
            tag.color = request.color
        if request.description is not None:
            tag.description = request.description

        await db.commit()
        await db.refresh(tag)

        response_data = {
            "id": str(tag.id),
            "organization_id": tag.organization_id,
            "tag_name": tag.tag_name,
            "tag_order": tag.tag_order,
            "is_default": tag.is_default,
            "is_active": tag.is_active,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
        }

        logger.info(f"Updated candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error updating candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate tag: {str(e)}",
        ) from e


@router.delete("/{tag_id}", tags=["Candidate Tags"])
async def delete_candidate_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a candidate tag.

    This endpoint permanently deletes a tag configuration.
    This action cannot be undone.

    Args:
        tag_id: UUID of the tag
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If tag is not found
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Deleting candidate tag: {tag_id}")

        # Check if tag exists
        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        # Delete the tag
        await db.execute(
            delete(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        await db.commit()

        logger.info(f"Deleted candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Candidate tag deleted successfully",
                "id": tag_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate tag: {str(e)}",
        ) from e


@router.post("/resume/{resume_id}/assign", tags=["Candidate Tags"])
async def assign_tag_to_resume(
    resume_id: str,
    request: AssignTagRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Assign a tag to a candidate (resume).

    This endpoint assigns a tag to a resume, creating an activity record
    to track when the tag was added.

    Args:
        resume_id: UUID of the resume
        request: Request body containing tag_id and optional recruiter_id
        db: Database session

    Returns:
        JSON response confirming the assignment

    Raises:
        HTTPException(404): If resume or tag is not found
        HTTPException(409): If tag is already assigned to this resume
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Assigning tag {request.tag_id} to resume: {resume_id}")

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Verify tag exists
        tag_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(request.tag_id))
        )
        tag = tag_result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag not found: {request.tag_id}",
            )

        # Check if tag is already assigned (has been added and not removed)
        existing_assignment = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(resume_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                CandidateActivity.tag_id == UUID(request.tag_id),
            ).order_by(CandidateActivity.created_at.desc()).limit(1)
        )
        last_activity = existing_assignment.scalar_one_or_none()

        if last_activity:
            # Check if there's been a removal after this addition
            removal_result = await db.execute(
                select(CandidateActivity).where(
                    CandidateActivity.candidate_id == UUID(resume_id),
                    CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                    CandidateActivity.tag_id == UUID(request.tag_id),
                    CandidateActivity.created_at > last_activity.created_at,
                ).limit(1)
            )
            removal_activity = removal_result.scalar_one_or_none()

            if not removal_activity:
                # Tag is currently assigned
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag '{tag.tag_name}' is already assigned to this resume",
                )

        # Create activity record for tag assignment
        activity = CandidateActivity(
            activity_type=CandidateActivityType.TAG_ADDED,
            candidate_id=UUID(resume_id),
            tag_id=UUID(request.tag_id),
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            activity_data={"tag_name": tag.tag_name, "color": tag.color},
        )
        db.add(activity)
        await db.flush()

        await db.commit()

        logger.info(f"Assigned tag '{tag.tag_name}' to resume: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": f"Tag '{tag.tag_name}' assigned successfully",
                "resume_id": resume_id,
                "tag_id": request.tag_id,
                "activity_id": str(activity.id),
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error assigning tag to resume: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign tag to resume: {str(e)}",
        ) from e


@router.delete("/resume/{resume_id}/tags/{tag_id}", tags=["Candidate Tags"])
async def remove_tag_from_resume(
    resume_id: str,
    tag_id: str,
    recruiter_id: Optional[str] = Query(None, description="Optional recruiter ID who is removing the tag"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Remove a tag from a candidate (resume).

    This endpoint removes a tag from a resume by creating a TAG_REMOVED activity record.

    Args:
        resume_id: UUID of the resume
        tag_id: UUID of the tag to remove
        recruiter_id: Optional recruiter ID who is removing the tag
        db: Database session

    Returns:
        JSON response confirming the removal

    Raises:
        HTTPException(404): If resume or tag is not found
        HTTPException(409): If tag is not currently assigned to this resume
        HTTPException(500): If an internal error occurs
    """
    try:
        logger.info(f"Removing tag {tag_id} from resume: {resume_id}")

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Verify tag exists
        tag_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = tag_result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag not found: {tag_id}",
            )

        # Check if tag is currently assigned
        existing_assignment = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(resume_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                CandidateActivity.tag_id == UUID(tag_id),
            ).order_by(CandidateActivity.created_at.desc()).limit(1)
        )
        last_activity = existing_assignment.scalar_one_or_none()

        if not last_activity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{tag.tag_name}' is not assigned to this resume",
            )

        # Check if there's been a removal after this addition
        removal_result = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(resume_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                CandidateActivity.tag_id == UUID(tag_id),
                CandidateActivity.created_at > last_activity.created_at,
            ).limit(1)
        )
        removal_activity = removal_result.scalar_one_or_none()

        if removal_activity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{tag.tag_name}' has already been removed from this resume",
            )

        # Create activity record for tag removal
        activity = CandidateActivity(
            activity_type=CandidateActivityType.TAG_REMOVED,
            candidate_id=UUID(resume_id),
            tag_id=UUID(tag_id),
            recruiter_id=UUID(recruiter_id) if recruiter_id else None,
            activity_data={"tag_name": tag.tag_name, "color": tag.color},
        )
        db.add(activity)
        await db.flush()

        await db.commit()

        logger.info(f"Removed tag '{tag.tag_name}' from resume: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Tag '{tag.tag_name}' removed successfully",
                "resume_id": resume_id,
                "tag_id": tag_id,
                "activity_id": str(activity.id),
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error removing tag from resume: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tag from resume: {str(e)}",
        ) from e


@router.post("/merge", tags=["Candidate Tags"])
async def merge_tags(
    request: MergeTagsRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Merge two tags together.

    This endpoint merges a source tag into a target tag. All candidates currently
    assigned the source tag will be assigned the target tag (if not already assigned),
    and then the source tag will be deleted.

    Args:
        request: Request body containing source_tag_id and target_tag_id
        db: Database session

    Returns:
        JSON response confirming the merge and the number of candidates transferred

    Raises:
        HTTPException(400): If source and target tags are the same
        HTTPException(404): If either tag is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/candidate-tags/merge",
        ...     json={
        ...         "source_tag_id": "old-tag-uuid",
        ...         "target_tag_id": "keep-tag-uuid"
        ...     }
        ... )
        >>> response.status_code
        200
    """
    try:
        logger.info(f"Merging tags - source: {request.source_tag_id}, target: {request.target_tag_id}")

        # Validate source and target are different
        if request.source_tag_id == request.target_tag_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target tags cannot be the same",
            )

        # Get source tag
        source_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(request.source_tag_id))
        )
        source_tag = source_result.scalar_one_or_none()

        if not source_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source tag not found: {request.source_tag_id}",
            )

        # Get target tag
        target_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(request.target_tag_id))
        )
        target_tag = target_result.scalar_one_or_none()

        if not target_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target tag not found: {request.target_tag_id}",
            )

        # Find all candidates currently assigned the source tag
        # We need to find candidates where the latest activity for the source tag is TAG_ADDED
        source_tag_added_subquery = (
            select(
                CandidateActivity.candidate_id,
                func.max(CandidateActivity.created_at).label('latest_added')
            )
            .where(
                CandidateActivity.tag_id == UUID(request.source_tag_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
            )
            .group_by(CandidateActivity.candidate_id)
            .subquery()
        )

        # Get candidates where latest source tag activity is TAG_ADDED (not TAG_REMOVED)
        candidates_with_source_tag_result = await db.execute(
            select(source_tag_added_subquery.c.candidate_id)
            .select_from(source_tag_added_subquery)
            .where(
                ~select(CandidateActivity)
                .where(
                    CandidateActivity.candidate_id == source_tag_added_subquery.c.candidate_id,
                    CandidateActivity.tag_id == UUID(request.source_tag_id),
                    CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                    CandidateActivity.created_at > source_tag_added_subquery.c.latest_added,
                )
                .exists()
            )
        )
        candidates_with_source_tag = candidates_with_source_tag_result.scalars().all()

        logger.info(f"Found {len(candidates_with_source_tag)} candidates with source tag")

        # Transfer candidates to target tag
        candidates_transferred = 0

        for candidate_id in candidates_with_source_tag:
            # Check if candidate already has target tag
            target_tag_added_result = await db.execute(
                select(CandidateActivity).where(
                    CandidateActivity.candidate_id == candidate_id,
                    CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                    CandidateActivity.tag_id == UUID(request.target_tag_id),
                ).order_by(CandidateActivity.created_at.desc()).limit(1)
            )
            last_target_activity = target_tag_added_result.scalar_one_or_none()

            target_already_assigned = False
            if last_target_activity:
                # Check if there's been a removal after this addition
                target_removal_result = await db.execute(
                    select(CandidateActivity).where(
                        CandidateActivity.candidate_id == candidate_id,
                        CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                        CandidateActivity.tag_id == UUID(request.target_tag_id),
                        CandidateActivity.created_at > last_target_activity.created_at,
                    ).limit(1)
                )
                target_removal = target_removal_result.scalar_one_or_none()
                target_already_assigned = (target_removal is None)

            # Only assign target tag if not already assigned
            if not target_already_assigned:
                activity = CandidateActivity(
                    activity_type=CandidateActivityType.TAG_ADDED,
                    candidate_id=candidate_id,
                    tag_id=UUID(request.target_tag_id),
                    activity_data={
                        "tag_name": target_tag.tag_name,
                        "color": target_tag.color,
                        "merged_from": source_tag.tag_name,
                    },
                )
                db.add(activity)
                candidates_transferred += 1

        await db.flush()

        # Delete the source tag
        await db.execute(
            delete(CandidateTag).where(CandidateTag.id == UUID(request.source_tag_id))
        )

        await db.commit()

        logger.info(
            f"Merged tag '{source_tag.tag_name}' into '{target_tag.tag_name}' - "
            f"transferred {candidates_transferred} candidates"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Merged '{source_tag.tag_name}' into '{target_tag.tag_name}' successfully",
                "source_tag_id": request.source_tag_id,
                "target_tag_id": request.target_tag_id,
                "candidates_transferred": candidates_transferred,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error merging tags: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge tags: {str(e)}",
        ) from e
