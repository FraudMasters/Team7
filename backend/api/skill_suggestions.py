"""
Skill suggestion endpoints.

This module provides endpoints for auto-suggesting relevant skills based on
industry and job description. It uses intelligent matching to find the most
relevant skills from industry-specific taxonomies.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

router = APIRouter()


class SkillSuggestionRequest(BaseModel):
    """Request model for skill suggestions."""

    industry: str = Field(..., description="Industry sector (tech, healthcare, finance, etc.)")
    title: str = Field(..., description="Job title")
    description: Optional[str] = Field("", description="Job description")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of suggestions to return")


class SuggestedSkill(BaseModel):
    """Individual skill suggestion with relevance score."""

    skill_name: str = Field(..., description="Canonical name of the skill")
    context: Optional[str] = Field(None, description="Context category")
    variants: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    relevance_score: float = Field(..., description="Relevance score (0-1)")


class SkillSuggestionResponse(BaseModel):
    """Response model for skill suggestions."""

    industry: str = Field(..., description="Industry sector")
    job_title: str = Field(..., description="Job title")
    suggestions: List[SuggestedSkill] = Field(..., description="List of suggested skills")
    total_count: int = Field(..., description="Number of suggestions returned")


def calculate_relevance_score(
    skill_name: str,
    variants: List[str],
    context: Optional[str],
    job_title: str,
    job_description: str,
) -> float:
    """
    Calculate relevance score for a skill based on job title and description.

    The score is calculated based on:
    - Exact matches in title (highest weight)
    - Partial matches in title (medium weight)
    - Matches in description (lower weight)
    - Context matches

    Args:
        skill_name: Canonical name of the skill
        variants: List of alternative names for the skill
        context: Context category
        job_title: Job title text
        job_description: Job description text

    Returns:
        Relevance score between 0.0 and 1.0

    Example:
        >>> score = calculate_relevance_score(
        ...     "React", ["ReactJS", "React.js"], "web_framework",
        ...     "Senior React Developer", "Looking for React expert..."
        ... )
        >>> print(score)
        0.85
    """
    score = 0.0
    title_lower = job_title.lower()
    description_lower = job_description.lower()

    # All skill variants to check
    all_skill_names = [skill_name.lower()] + [v.lower() for v in variants]

    # Check title matches (highest weight)
    for skill_variant in all_skill_names:
        if skill_variant in title_lower:
            # Exact word match in title
            if f" {skill_variant} " in f" {title_lower} ":
                score += 0.5
            # Partial match in title
            else:
                score += 0.3

    # Check description matches (lower weight)
    for skill_variant in all_skill_names:
        if skill_variant in description_lower:
            score += 0.2

    # Context match bonus
    if context:
        context_lower = context.lower()
        title_desc_lower = title_lower + " " + description_lower
        if context_lower in title_desc_lower:
            score += 0.1

    # Cap score at 1.0
    return min(score, 1.0)


@router.post(
    "/suggest",
    response_model=SkillSuggestionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Skill Suggestions"],
)
async def suggest_skills(
    request: SkillSuggestionRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Suggest relevant skills based on industry and job description.

    This endpoint analyzes the job title and description to find the most
    relevant skills from the industry-specific taxonomy. Skills are scored
    based on keyword matching and returned in order of relevance.

    Args:
        request: Suggestion request with industry, title, description, and limit
        db: Database session

    Returns:
        JSON response with suggested skills and relevance scores

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "industry": "healthcare",
        ...     "title": "Senior Registered Nurse",
        ...     "description": "ICU, patient care, medical records...",
        ...     "limit": 20
        ... }
        >>> response = requests.post("http://localhost:8000/api/skill-suggestions/suggest", json=data)
        >>> response.json()
        {
            "industry": "healthcare",
            "job_title": "Senior Registered Nurse",
            "suggestions": [
                {
                    "skill_name": "Patient Care",
                    "context": "clinical",
                    "variants": ["Patient Care", "Caregiving"],
                    "relevance_score": 0.9
                },
                ...
            ],
            "total_count": 15
        }
    """
    try:
        logger.info(
            f"Suggesting skills for industry={request.industry}, "
            f"title={request.title}, limit={request.limit}"
        )

        # Validate industry
        if not request.industry or len(request.industry.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Industry cannot be empty",
            )

        # Validate title
        if not request.title or len(request.title.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Job title cannot be empty",
            )

        # Combine title and description for matching
        job_text = f"{request.title} {request.description or ''}"

        # Query industry taxonomies
        query = select(SkillTaxonomy).where(
            SkillTaxonomy.industry == request.industry,
            SkillTaxonomy.is_active == True,
        )
        result = await db.execute(query)
        taxonomies = result.scalars().all()

        if not taxonomies:
            logger.warning(f"No taxonomies found for industry: {request.industry}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "industry": request.industry,
                    "job_title": request.title,
                    "suggestions": [],
                    "total_count": 0,
                },
            )

        # Calculate relevance scores for all skills
        scored_skills = []
        for taxonomy in taxonomies:
            variants = taxonomy.variants or []
            score = calculate_relevance_score(
                skill_name=taxonomy.skill_name,
                variants=variants,
                context=taxonomy.context,
                job_title=request.title,
                job_description=request.description or "",
            )

            # Only include skills with some relevance
            if score > 0:
                scored_skills.append(
                    {
                        "skill_name": taxonomy.skill_name,
                        "context": taxonomy.context,
                        "variants": variants,
                        "relevance_score": score,
                    }
                )

        # Sort by relevance score (descending)
        scored_skills.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Apply limit
        limited_suggestions = scored_skills[: request.limit]

        response_data = {
            "industry": request.industry,
            "job_title": request.title,
            "suggestions": limited_suggestions,
            "total_count": len(limited_suggestions),
        }

        logger.info(
            f"Returning {len(limited_suggestions)} skill suggestions for {request.industry}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting skills: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest skills: {str(e)}",
        ) from e
