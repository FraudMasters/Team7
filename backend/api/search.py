"""
Advanced search API endpoints for candidates.

This module provides endpoints for:
- Searching candidates with full-text search and boolean operators (AND, OR, NOT)
- Filtering candidates by skills, experience, education, location, languages
- Range filters for experience years, match score, and date ranges
- Sorting by relevance, date, or experience

Leverages PostgreSQL full-text search for fast, flexible queries.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.search_service import SearchService, SearchFilters, get_search_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class SearchRequest(BaseModel):
    """Request model for candidate search."""

    query: Optional[str] = Field(None, description="Search query with boolean operators (AND, OR, NOT)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for search")
    skip: int = Field(0, ge=0, description="Number of results to skip (pagination)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results to return")
    sort_by: str = Field("relevance", description="Sort field: relevance, date, or experience")


class FilterRequest(BaseModel):
    """Filter configuration for candidate search."""

    skills: Optional[List[str]] = Field(None, description="List of required skills (OR logic within list)")
    min_experience_years: Optional[int] = Field(None, ge=0, description="Minimum years of experience")
    max_experience_years: Optional[int] = Field(None, ge=0, description="Maximum years of experience")
    location: Optional[str] = Field(None, description="Location filter")
    education_level: Optional[str] = Field(None, description="Minimum education level")
    languages: Optional[List[str]] = Field(None, description="List of required languages")
    min_match_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum match score (0-100)")
    max_match_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum match score (0-100)")
    date_from: Optional[str] = Field(None, description="Start date filter (ISO 8601 format)")
    date_to: Optional[str] = Field(None, description="End date filter (ISO 8601 format)")
    vacancy_id: Optional[str] = Field(None, description="Filter by vacancy ID")
    stage_id: Optional[str] = Field(None, description="Filter by workflow stage ID or name")


# Response Models
class CandidateSearchResult(BaseModel):
    """Single candidate search result."""

    id: str = Field(..., description="Resume UUID")
    filename: str = Field(..., description="Resume filename")
    status: str = Field(..., description="Resume processing status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    current_stage: str = Field(..., description="Current workflow stage")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID if any")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    total_experience_months: Optional[int] = Field(None, description="Total experience in months")
    experience_years: Optional[float] = Field(None, description="Total experience in years")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history")
    language: Optional[str] = Field(None, description="Detected language")
    quality_score: Optional[float] = Field(None, description="Resume quality score")


class SearchResponse(BaseModel):
    """Response model for candidate search."""

    total: int = Field(..., description="Total number of matching candidates")
    candidates: List[Dict[str, Any]] = Field(..., description="List of candidate results")
    query: str = Field(..., description="Search query that was executed")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    execution_time_seconds: float = Field(..., description="Time taken to execute search")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum number of results returned")


@router.post(
    "/candidates",
    response_model=SearchResponse,
    tags=["Search"],
)
async def search_candidates(
    request: Request,
    search_data: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for candidates with advanced filters and boolean operators.

    This endpoint provides powerful candidate search capabilities including:
    - Full-text search with boolean operators (AND, OR, NOT)
    - Multi-field filtering: skills, experience, education, location, languages
    - Range filters: experience years, match score, date ranges
    - Flexible sorting by relevance, date, or experience

    Examples of boolean search queries:
    - "Python AND Django" - Candidates with both Python and Django
    - "Python OR Django" - Candidates with either Python or Django
    - "Python NOT Flask" - Candidates with Python but not Flask
    - "Python Django" - Implicit AND (same as "Python AND Django")

    Args:
        request: FastAPI request object
        search_data: Search request with query, filters, pagination, and sorting
        db: Database session

    Returns:
        JSON response with search results, total count, and execution metadata

    Raises:
        HTTPException(400): If filter parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Search with query and filters
        >>> data = {
        ...     "query": "Python AND Django",
        ...     "filters": {
        ...         "min_experience_years": 3,
        ...         "max_experience_years": 10,
        ...         "location": "Remote"
        ...     },
        ...     "limit": 10
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/search/candidates",
        ...     json=data
        ... )
        >>> # Filter by skills only
        >>> data = {
        ...     "filters": {
        ...         "skills": ["Python", "FastAPI"],
        ...         "min_experience_years": 5
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/search/candidates",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Searching candidates - query: {search_data.query}, "
            f"filters: {search_data.filters}, skip: {search_data.skip}, "
            f"limit: {search_data.limit}, sort_by: {search_data.sort_by}"
        )

        # Get search service
        search_service = get_search_service(db)

        # Build SearchFilters from request data
        filters = None
        if search_data.filters:
            filters = SearchFilters(
                skills=search_data.filters.get("skills"),
                min_experience_years=search_data.filters.get("min_experience_years"),
                max_experience_years=search_data.filters.get("max_experience_years"),
                location=search_data.filters.get("location"),
                education_level=search_data.filters.get("education_level"),
                languages=search_data.filters.get("languages"),
                min_match_score=search_data.filters.get("min_match_score"),
                max_match_score=search_data.filters.get("max_match_score"),
                date_from=search_data.filters.get("date_from"),
                date_to=search_data.filters.get("date_to"),
                vacancy_id=search_data.filters.get("vacancy_id"),
                stage_id=search_data.filters.get("stage_id"),
            )

        # Execute search
        result = await search_service.search_candidates(
            query=search_data.query,
            filters=filters,
            skip=search_data.skip,
            limit=search_data.limit,
            sort_by=search_data.sort_by,
        )

        logger.info(
            f"Search completed: {result.total} total candidates, "
            f"returned {len(result.candidates)} results in "
            f"{result.execution_time_seconds:.3f}s"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "filters_applied": result.filters_applied,
                "execution_time_seconds": result.execution_time_seconds,
                "skip": search_data.skip,
                "limit": search_data.limit,
            },
        )

    except ValueError as e:
        logger.error(f"Invalid search parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during candidate search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get(
    "/candidates",
    response_model=SearchResponse,
    tags=["Search"],
)
async def search_candidates_get(
    request: Request,
    query: Optional[str] = Query(None, description="Search query with boolean operators"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
    min_experience_years: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    max_experience_years: Optional[int] = Query(None, ge=0, description="Maximum years of experience"),
    location: Optional[str] = Query(None, description="Location filter"),
    education_level: Optional[str] = Query(None, description="Minimum education level"),
    languages: Optional[str] = Query(None, description="Comma-separated list of languages"),
    min_match_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum match score"),
    max_match_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum match score"),
    date_from: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    date_to: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    stage_id: Optional[str] = Query(None, description="Filter by workflow stage"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of results"),
    sort_by: str = Query("relevance", description="Sort field: relevance, date, or experience"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for candidates using GET request with query parameters.

    This is an alternative to the POST endpoint that uses query parameters
    instead of a JSON body. Useful for simple searches and browser-based queries.

    Args:
        request: FastAPI request object
        query: Search query with boolean operators
        skills: Comma-separated list of skills (e.g., "Python, Django, FastAPI")
        min_experience_years: Minimum years of experience
        max_experience_years: Maximum years of experience
        location: Location filter
        education_level: Minimum education level
        languages: Comma-separated list of languages
        min_match_score: Minimum match score (0-100)
        max_match_score: Maximum match score (0-100)
        date_from: Start date filter (ISO 8601 format)
        date_to: End date filter (ISO 8601 format)
        vacancy_id: Filter by vacancy ID
        stage_id: Filter by workflow stage
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return
        sort_by: Sort field (relevance, date, experience)
        db: Database session

    Returns:
        JSON response with search results and metadata

    Raises:
        HTTPException(400): If filter parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Simple search with query
        >>> response = requests.get(
        ...     "http://localhost:8000/api/search/candidates",
        ...     params={"query": "Python AND Django", "limit": 10}
        ... )
        >>> # Filter by experience and location
        >>> response = requests.get(
        ...     "http://localhost:8000/api/search/candidates",
        ...     params={
        ...         "min_experience_years": 5,
        ...         "location": "Remote",
        ...         "limit": 20
        ...     }
        ... )
        >>> # Filter by skills
        >>> response = requests.get(
        ...     "http://localhost:8000/api/search/candidates",
        ...     params={
        ...         "skills": "Python, FastAPI, PostgreSQL",
        ...         "min_experience_years": 3
        ...     }
        ... )
    """
    try:
        logger.info(
            f"GET search - query: {query}, skills: {skills}, "
            f"experience: {min_experience_years}-{max_experience_years}, "
            f"location: {location}"
        )

        # Get search service
        search_service = get_search_service(db)

        # Build filters from query parameters
        filters_dict = {}
        if skills:
            filters_dict["skills"] = [s.strip() for s in skills.split(",")]
        if min_experience_years is not None:
            filters_dict["min_experience_years"] = min_experience_years
        if max_experience_years is not None:
            filters_dict["max_experience_years"] = max_experience_years
        if location:
            filters_dict["location"] = location
        if education_level:
            filters_dict["education_level"] = education_level
        if languages:
            filters_dict["languages"] = [l.strip() for l in languages.split(",")]
        if min_match_score is not None:
            filters_dict["min_match_score"] = min_match_score
        if max_match_score is not None:
            filters_dict["max_match_score"] = max_match_score
        if date_from:
            filters_dict["date_from"] = date_from
        if date_to:
            filters_dict["date_to"] = date_to
        if vacancy_id:
            filters_dict["vacancy_id"] = vacancy_id
        if stage_id:
            filters_dict["stage_id"] = stage_id

        filters = SearchFilters(**filters_dict) if filters_dict else None

        # Execute search
        result = await search_service.search_candidates(
            query=query,
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
        )

        logger.info(
            f"GET search completed: {result.total} total, "
            f"returned {len(result.candidates)} results"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "filters_applied": result.filters_applied,
                "execution_time_seconds": result.execution_time_seconds,
                "skip": skip,
                "limit": limit,
            },
        )

    except ValueError as e:
        logger.error(f"Invalid search parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during candidate search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e
