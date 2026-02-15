"""
Filter suggestions API endpoints for AI-powered job description analysis.

This module provides endpoints for:
- Analyzing job descriptions to suggest search filters
- Extracting skills, experience, location, education from JD text
- Converting suggestions into ready-to-use search filter configurations

Leverages the JDFilterSuggester service for intelligent filter extraction.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.jd_filter_suggester import (
    JDFilterSuggester,
    FilterSuggestionsResult,
    get_jd_filter_suggester,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class FilterSuggestionRequest(BaseModel):
    """Request model for JD filter suggestions."""

    job_description: str = Field(
        ...,
        description="Job description text to analyze for filter suggestions",
        min_length=10,
        max_length=50000,
    )
    max_skills: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of skills to suggest",
    )
    min_confidence: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for suggestions (0.0-1.0)",
    )


class SuggestedFilterItem(BaseModel):
    """Single suggested filter item."""

    filter_type: str = Field(..., description="Type of filter (skills, location, education_level, languages)")
    value: Any = Field(..., description="The filter value")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    source: str = Field(..., description="Source of suggestion (extracted, inferred, synonym, provided)")
    original_text: Optional[str] = Field(None, description="Original text from JD that led to this suggestion")


class FilterSuggestionResponse(BaseModel):
    """Response model for filter suggestions."""

    skills: List[SuggestedFilterItem] = Field(
        default_factory=list,
        description="List of suggested skill filters with confidence scores",
    )
    min_experience_years: Optional[int] = Field(None, description="Suggested minimum years of experience")
    max_experience_years: Optional[int] = Field(None, description="Suggested maximum years of experience")
    seniority_level: Optional[str] = Field(None, description="Detected seniority level (entry, mid, senior, lead, executive)")
    location: Optional[SuggestedFilterItem] = Field(None, description="Suggested location filter")
    education_level: Optional[SuggestedFilterItem] = Field(None, description="Suggested education level filter")
    languages: List[SuggestedFilterItem] = Field(default_factory=list, description="List of suggested language filters")
    all_filters: List[SuggestedFilterItem] = Field(
        default_factory=list,
        description="Combined list of all suggested filters sorted by confidence",
    )
    confidence: float = Field(..., description="Overall confidence in the suggestions (0.0-1.0)")
    analysis_time_seconds: float = Field(..., description="Time taken to analyze the job description")
    search_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ready-to-use filters dictionary for search API",
    )


class VacancyFilterRequest(BaseModel):
    """Request model for structured vacancy filter suggestions."""

    title: Optional[str] = Field(None, description="Job title", max_length=500)
    description: Optional[str] = Field(None, description="Job description text", max_length=50000)
    skills: Optional[List[str]] = Field(None, description="List of required skills from vacancy")
    requirements: Optional[List[str]] = Field(None, description="List of additional requirements")


@router.post(
    "/suggest",
    response_model=FilterSuggestionResponse,
    tags=["Filter Suggestions"],
)
async def suggest_filters(
    request: Request,
    suggestion_data: FilterSuggestionRequest,
) -> JSONResponse:
    """
    Analyze a job description and suggest search filters.

    This endpoint uses AI-powered analysis to extract relevant search
    filters from job description text. It identifies:
    - Required skills (using synonym matching)
    - Experience requirements (years and seniority level)
    - Location preferences
    - Education requirements
    - Language requirements

    All suggestions include confidence scores indicating the reliability
    of the extraction.

    Args:
        request: FastAPI request object
        suggestion_data: Request containing job description and options

    Returns:
        JSON response with suggested filters, confidence scores, and
        ready-to-use search filter configuration

    Raises:
        HTTPException(400): If job description is too short or invalid
        HTTPException(500): If filter suggestion analysis fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "job_description": "Senior Python Developer with 5+ years
        ...                         experience in Django and AWS. Based in NYC.
        ...                         Bachelor's degree required."
        ... }
        >>> response = requests.post(
        ...     "/api/filter-suggestions/suggest",
        ...     json=data
        ... )
        >>> suggestions = response.json()
        >>> print(suggestions["skills"])
        [{"filter_type": "skills", "value": "Python", "confidence": 0.95, ...}]
        >>> print(suggestions["min_experience_years"])
        5
        >>> print(suggestions["seniority_level"])
        "senior"
    """
    try:
        logger.info(
            f"Analyzing job description for filter suggestions "
            f"(length: {len(suggestion_data.job_description)} chars, "
            f"max_skills: {suggestion_data.max_skills}, "
            f"min_confidence: {suggestion_data.min_confidence})"
        )

        # Get the JD filter suggester
        suggester = get_jd_filter_suggester()

        # Analyze the job description
        result: FilterSuggestionsResult = suggester.suggest_filters(
            job_description=suggestion_data.job_description,
            max_skills=suggestion_data.max_skills,
            min_confidence=suggestion_data.min_confidence,
        )

        logger.info(
            f"JD analysis completed: {len(result.skills)} skills, "
            f"experience: {result.min_experience_years}-{result.max_experience_years} years "
            f"({result.seniority_level}), confidence: {result.confidence:.2f}"
        )

        # Convert result to response format
        response_data = {
            "skills": [s.to_dict() for s in result.skills],
            "min_experience_years": result.min_experience_years,
            "max_experience_years": result.max_experience_years,
            "seniority_level": result.seniority_level,
            "location": result.location.to_dict() if result.location else None,
            "education_level": result.education_level.to_dict() if result.education_level else None,
            "languages": [l.to_dict() for l in result.languages],
            "all_filters": [f.to_dict() for f in result.all_filters],
            "confidence": result.confidence,
            "analysis_time_seconds": result.analysis_time_seconds,
            "search_filters": result.to_search_filters(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError as e:
        logger.error(f"Invalid filter suggestion request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during filter suggestion analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter suggestion analysis failed: {str(e)}",
        ) from e


@router.post(
    "/suggest-vacancy",
    response_model=FilterSuggestionResponse,
    tags=["Filter Suggestions"],
)
async def suggest_filters_from_vacancy(
    request: Request,
    vacancy_data: VacancyFilterRequest,
) -> JSONResponse:
    """
    Analyze structured vacancy data and suggest search filters.

    This endpoint accepts structured vacancy data (title, description,
    skills list, requirements) and generates filter suggestions. Use this
    when you have already-parsed vacancy data rather than raw text.

    Args:
        request: FastAPI request object
        vacancy_data: Structured vacancy data with title, description,
                     skills, and requirements

    Returns:
        JSON response with suggested filters based on the combined
        vacancy data analysis

    Raises:
        HTTPException(400): If no vacancy data fields are provided
        HTTPException(500): If filter suggestion analysis fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "title": "Senior Python Developer",
        ...     "description": "5+ years experience required",
        ...     "skills": ["Python", "Django", "PostgreSQL"],
        ...     "requirements": ["Remote work available", "BS in CS preferred"]
        ... }
        >>> response = requests.post(
        ...     "/api/filter-suggestions/suggest-vacancy",
        ...     json=data
        ... )
        >>> suggestions = response.json()
    """
    try:
        # Validate that at least some data is provided
        if not any([
            vacancy_data.title,
            vacancy_data.description,
            vacancy_data.skills,
            vacancy_data.requirements,
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of title, description, skills, or requirements must be provided",
            )

        logger.info(
            f"Analyzing vacancy data for filter suggestions "
            f"(title: {bool(vacancy_data.title)}, "
            f"description: {bool(vacancy_data.description)}, "
            f"skills: {len(vacancy_data.skills or [])}, "
            f"requirements: {len(vacancy_data.requirements or [])})"
        )

        # Get the JD filter suggester
        suggester = get_jd_filter_suggester()

        # Analyze the structured vacancy data
        result: FilterSuggestionsResult = suggester.suggest_filters_from_vacancy(
            title=vacancy_data.title,
            description=vacancy_data.description,
            skills=vacancy_data.skills,
            requirements=vacancy_data.requirements,
        )

        logger.info(
            f"Vacancy analysis completed: {len(result.skills)} skills, "
            f"experience: {result.min_experience_years}-{result.max_experience_years} years "
            f"({result.seniority_level}), confidence: {result.confidence:.2f}"
        )

        # Convert result to response format
        response_data = {
            "skills": [s.to_dict() for s in result.skills],
            "min_experience_years": result.min_experience_years,
            "max_experience_years": result.max_experience_years,
            "seniority_level": result.seniority_level,
            "location": result.location.to_dict() if result.location else None,
            "education_level": result.education_level.to_dict() if result.education_level else None,
            "languages": [l.to_dict() for l in result.languages],
            "all_filters": [f.to_dict() for f in result.all_filters],
            "confidence": result.confidence,
            "analysis_time_seconds": result.analysis_time_seconds,
            "search_filters": result.to_search_filters(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during vacancy filter suggestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vacancy filter suggestion failed: {str(e)}",
        ) from e
