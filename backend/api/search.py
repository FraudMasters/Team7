"""
Advanced search API endpoints for candidates.

This module provides endpoints for:
- Searching candidates with full-text search and boolean operators (AND, OR, NOT)
- Filtering candidates by skills, experience, education, location, languages
- Range filters for experience years, match score, and date ranges
- Sorting by relevance, date, or experience
- Search history tracking and retrieval
- Elasticsearch integration for advanced boolean query parsing

Supports both PostgreSQL full-text search and Elasticsearch-based search.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import SearchHistory, Resume, ResumeAnalysis
from services.search_service import SearchService, SearchFilters, get_search_service
from services.elasticsearch_service import (
    ElasticsearchService,
    SearchQuery as ESSearchQuery,
)

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
    use_elasticsearch: bool = Field(False, description="Use Elasticsearch for search (supports advanced boolean queries)")


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
    tag_ids: Optional[List[str]] = Field(None, description="List of tag IDs to filter candidates")


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


class SearchHistoryItem(BaseModel):
    """Single search history item."""

    id: str = Field(..., description="Search history UUID")
    query: Optional[str] = Field(None, description="Search query that was executed")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    results_count: Optional[int] = Field(None, description="Number of results returned")
    execution_time_seconds: Optional[float] = Field(None, description="Time taken to execute search")
    created_at: str = Field(..., description="Timestamp when search was performed")
    recruiter_id: Optional[str] = Field(None, description="ID of recruiter who performed the search")


class SearchHistoryResponse(BaseModel):
    """Response model for search history."""

    total: int = Field(..., description="Total number of search history records")
    history: List[SearchHistoryItem] = Field(..., description="List of search history items")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")


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
        ...     "/api/search/candidates",
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
        ...     "/api/search/candidates",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Searching candidates - query: {search_data.query}, "
            f"filters: {search_data.filters}, skip: {search_data.skip}, "
            f"limit: {search_data.limit}, sort_by: {search_data.sort_by}, "
            f"use_elasticsearch: {search_data.use_elasticsearch}"
        )

        start_time = time.time()

        # Route to Elasticsearch or PostgreSQL based on use_elasticsearch flag
        if search_data.use_elasticsearch:
            # Use Elasticsearch for advanced boolean query support
            es_service = ElasticsearchService()
            await es_service.initialize()

            # Build SearchQuery for Elasticsearch
            es_query = ESSearchQuery(
                query_string=search_data.query,
                skills=search_data.filters.get("skills") if search_data.filters else None,
                min_experience_years=search_data.filters.get("min_experience_years") if search_data.filters else None,
                max_experience_years=search_data.filters.get("max_experience_years") if search_data.filters else None,
                location=search_data.filters.get("location") if search_data.filters else None,
                education_level=search_data.filters.get("education_level") if search_data.filters else None,
                languages=search_data.filters.get("languages") if search_data.filters else None,
                from_=search_data.skip,
                size=search_data.limit,
                sort_by=search_data.sort_by,
                filters=search_data.filters,
            )

            # Execute Elasticsearch search
            es_result = await es_service.search(es_query)

            # Transform Elasticsearch results to API response format
            candidates = []
            for hit in es_result.hits:
                source = hit.get("_source", {})
                candidate = {
                    "id": hit.get("_id"),
                    "score": hit.get("_score"),
                    "resume_id": source.get("resume_id"),
                    "raw_text": source.get("raw_text", "")[:200] + "...",  # Truncate for response
                    "skills": source.get("skills", []),
                    "experience_years": source.get("experience_years"),
                    "education": source.get("education", []),
                    "location": source.get("location"),
                    "languages": source.get("languages", []),
                    "indexed_at": source.get("indexed_at"),
                }
                candidates.append(candidate)

            execution_time = time.time() - start_time

            logger.info(
                f"Elasticsearch search completed: {es_result.total} total candidates, "
                f"returned {len(candidates)} results in {execution_time:.3f}s"
            )

            # Close Elasticsearch client
            await es_service.close()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "total": es_result.total,
                    "candidates": candidates,
                    "query": search_data.query or "",
                    "filters_applied": search_data.filters or {},
                    "execution_time_seconds": execution_time,
                    "skip": search_data.skip,
                    "limit": search_data.limit,
                },
            )

        else:
            # Use PostgreSQL search service
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
                    tag_ids=search_data.filters.get("tag_ids"),
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
                f"PostgreSQL search completed: {result.total} total candidates, "
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
    tag_ids: Optional[str] = Query(None, description="Comma-separated list of tag IDs"),
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
        tag_ids: Comma-separated list of tag IDs
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
        ...     "/api/search/candidates",
        ...     params={"query": "Python AND Django", "limit": 10}
        ... )
        >>> # Filter by experience and location
        >>> response = requests.get(
        ...     "/api/search/candidates",
        ...     params={
        ...         "min_experience_years": 5,
        ...         "location": "Remote",
        ...         "limit": 20
        ...     }
        ... )
        >>> # Filter by skills
        >>> response = requests.get(
        ...     "/api/search/candidates",
        ...     params={
        ...         "skills": "Python, FastAPI, PostgreSQL",
        ...         "min_experience_years": 3
        ...     }
        ... )
        >>> # Filter by tags
        >>> response = requests.get(
        ...     "/api/search/candidates",
        ...     params={
        ...         "tag_ids": "tag-uuid-1,tag-uuid-2",
        ...         "limit": 20
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
        if tag_ids:
            filters_dict["tag_ids"] = [t.strip() for t in tag_ids.split(",")]

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


@router.get(
    "/history",
    response_model=SearchHistoryResponse,
    tags=["Search"],
)
async def get_search_history(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Retrieve search history with pagination.

    This endpoint returns a paginated list of previously executed searches,
    including the query, filters, results count, and execution time.
    Useful for reviewing and repeating previous searches.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        recruiter_id: Optional filter to show only searches by a specific recruiter
        db: Database session

    Returns:
        JSON response with search history records and pagination metadata

    Raises:
        HTTPException(400): If recruiter_id format is invalid
        HTTPException(500): If history retrieval fails

    Examples:
        >>> import requests
        >>> # Get recent search history
        >>> response = requests.get(
        ...     "/api/search/history",
        ...     params={"limit": 20}
        ... )
        >>> # Get history for a specific recruiter
        >>> response = requests.get(
        ...     "/api/search/history",
        ...     params={
        ...         "recruiter_id": "recruiter-uuid",
        ...         "limit": 50
        ...     }
        ... )
    """
    try:
        logger.info(f"Fetching search history - skip: {skip}, limit: {limit}, recruiter_id: {recruiter_id}")

        # Build query
        query = select(SearchHistory).order_by(desc(SearchHistory.created_at))

        # Apply recruiter filter if provided
        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                query = query.where(SearchHistory.recruiter_id == recruiter_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid recruiter_id format",
                )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        history_items = result.scalars().all()

        # Convert to response format
        history_data = []
        for item in history_items:
            history_data.append(
                {
                    "id": str(item.id),
                    "query": item.query,
                    "filters": item.filters or {},
                    "results_count": item.results_count,
                    "execution_time_seconds": item.execution_time_seconds,
                    "created_at": item.created_at.isoformat(),
                    "recruiter_id": str(item.recruiter_id) if item.recruiter_id else None,
                }
            )

        logger.info(f"Retrieved {len(history_data)} search history records (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "history": history_data,
                "skip": skip,
                "limit": limit,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching search history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch search history: {str(e)}",
        ) from e
