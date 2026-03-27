"""
Search analytics endpoints.

This module provides endpoints for:
- Getting recent search queries
- Getting popular search queries
- Getting searches that returned zero results

Search analytics help recruiters understand search patterns, optimize search
performance, and improve search UX based on usage data.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.search_analytics import SearchQuery, PopularSearch
from models.search_relevance_config import SearchRelevanceConfig

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class SearchQueryResponse(BaseModel):
    """Response model for a search query."""

    id: str = Field(..., description="Search query UUID")
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter settings")
    results_count: int = Field(..., description="Number of results returned")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    search_type: Optional[str] = Field(None, description="Type of search performed")
    created_at: str = Field(..., description="Timestamp when search was performed")


class RecentSearchesResponse(BaseModel):
    """Response model for recent searches."""

    total: int = Field(..., description="Total number of recent searches")
    searches: List[SearchQueryResponse] = Field(..., description="List of recent search queries")


class PopularSearchResponse(BaseModel):
    """Response model for a popular search."""

    id: str = Field(..., description="Popular search UUID")
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Common filter settings")
    search_count: int = Field(..., description="Number of times this query has been searched")
    avg_results_count: Optional[float] = Field(None, description="Average number of results returned")
    avg_click_through_rate: Optional[float] = Field(None, description="Average click-through rate")
    last_searched_at: str = Field(..., description="Timestamp when query was last searched")


class PopularSearchesResponse(BaseModel):
    """Response model for popular searches."""

    total: int = Field(..., description="Total number of popular searches")
    searches: List[PopularSearchResponse] = Field(..., description="List of popular search queries")


class ZeroResultSearchResponse(BaseModel):
    """Response model for a zero-result search."""

    id: str = Field(..., description="Search query UUID")
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter settings")
    search_type: Optional[str] = Field(None, description="Type of search performed")
    created_at: str = Field(..., description="Timestamp when search was performed")


class ZeroResultSearchesResponse(BaseModel):
    """Response model for zero-result searches."""

    total: int = Field(..., description="Total number of zero-result searches")
    searches: List[ZeroResultSearchResponse] = Field(..., description="List of searches with zero results")


@router.get(
    "/recent",
    response_model=RecentSearchesResponse,
    tags=["Search Analytics"],
)
async def get_recent_searches(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recent searches to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get recent search queries.

    Returns a list of recent search queries ordered by creation time (most recent first).
    This helps recruiters see recent search activity and repeat common searches.

    Args:
        request: FastAPI request object
        limit: Maximum number of searches to return (default: 20, max: 100)
        skip: Number of records to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with recent search queries

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/search/analytics/recent?limit=10"
        ... )
    """
    try:
        logger.info(f"Fetching recent searches (limit={limit}, skip={skip})")

        # Query recent searches ordered by created_at descending
        stmt = (
            select(SearchQuery)
            .order_by(desc(SearchQuery.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        searches = result.scalars().all()

        # Get total count
        count_stmt = select(SearchQuery)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        logger.info(f"Found {len(searches)} recent searches (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "searches": [
                    {
                        "id": str(search.id),
                        "query": search.query,
                        "filters": search.filters or {},
                        "results_count": search.results_count,
                        "execution_time_ms": search.execution_time_ms,
                        "search_type": search.search_type,
                        "created_at": search.created_at.isoformat() if search.created_at else None,
                    }
                    for search in searches
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error fetching recent searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent searches: {str(e)}",
        ) from e


@router.get(
    "/popular",
    response_model=PopularSearchesResponse,
    tags=["Search Analytics"],
)
async def get_popular_searches(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of popular searches to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    min_search_count: int = Query(2, ge=1, description="Minimum search count to be considered popular"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get popular search queries.

    Returns a list of popular search queries ordered by search count (most popular first).
    This helps recruiters discover commonly used searches and search trends.

    Args:
        request: FastAPI request object
        limit: Maximum number of searches to return (default: 20, max: 100)
        skip: Number of records to skip for pagination (default: 0)
        min_search_count: Minimum search count to be considered popular (default: 2)
        db: Database session

    Returns:
        JSON response with popular search queries

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/search/analytics/popular?limit=10&min_search_count=5"
        ... )
    """
    try:
        logger.info(
            f"Fetching popular searches (limit={limit}, skip={skip}, min_count={min_search_count})"
        )

        # Query popular searches ordered by search_count descending
        stmt = (
            select(PopularSearch)
            .where(PopularSearch.search_count >= min_search_count)
            .order_by(desc(PopularSearch.search_count))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        searches = result.scalars().all()

        # Get total count of popular searches
        count_stmt = select(PopularSearch).where(PopularSearch.search_count >= min_search_count)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        logger.info(f"Found {len(searches)} popular searches (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "searches": [
                    {
                        "id": str(search.id),
                        "query": search.query,
                        "filters": search.filters or {},
                        "search_count": search.search_count,
                        "avg_results_count": search.avg_results_count,
                        "avg_click_through_rate": search.avg_click_through_rate,
                        "last_searched_at": search.last_searched_at.isoformat() if search.last_searched_at else None,
                    }
                    for search in searches
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error fetching popular searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch popular searches: {str(e)}",
        ) from e


@router.get(
    "/zero-results",
    response_model=ZeroResultSearchesResponse,
    tags=["Search Analytics"],
)
async def get_zero_result_searches(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of zero-result searches to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get searches that returned zero results.

    Returns a list of search queries that returned no results, ordered by creation time
    (most recent first). This helps identify gaps in the candidate database or issues
    with search queries that need improvement.

    Args:
        request: FastAPI request object
        limit: Maximum number of searches to return (default: 20, max: 100)
        skip: Number of records to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with zero-result search queries

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/search/analytics/zero-results?limit=10"
        ... )
    """
    try:
        logger.info(f"Fetching zero-result searches (limit={limit}, skip={skip})")

        # Query searches with zero results ordered by created_at descending
        stmt = (
            select(SearchQuery)
            .where(SearchQuery.results_count == 0)
            .order_by(desc(SearchQuery.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        searches = result.scalars().all()

        # Get total count of zero-result searches
        count_stmt = select(SearchQuery).where(SearchQuery.results_count == 0)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        logger.info(f"Found {len(searches)} zero-result searches (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "searches": [
                    {
                        "id": str(search.id),
                        "query": search.query,
                        "filters": search.filters or {},
                        "search_type": search.search_type,
                        "created_at": search.created_at.isoformat() if search.created_at else None,
                    }
                    for search in searches
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error fetching zero-result searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch zero-result searches: {str(e)}",
        ) from e


# Request/Response Models for Relevance Config
class RelevanceConfigRequest(BaseModel):
    """Request model for updating relevance configuration."""

    name: Optional[str] = Field(None, description="Name/description of configuration")
    skills_boost: float = Field(1.0, ge=0.1, le=10.0, description="Skills field boost value")
    experience_boost: float = Field(1.0, ge=0.1, le=10.0, description="Experience field boost value")
    education_boost: float = Field(1.0, ge=0.1, le=10.0, description="Education field boost value")
    location_boost: Optional[float] = Field(1.0, ge=0.1, le=10.0, description="Location field boost value")


class RelevanceConfigResponse(BaseModel):
    """Response model for relevance configuration."""

    id: str = Field(..., description="Configuration UUID")
    name: str = Field(..., description="Name/description of configuration")
    skills_boost: float = Field(..., description="Skills field boost value")
    experience_boost: float = Field(..., description="Experience field boost value")
    education_boost: float = Field(..., description="Education field boost value")
    location_boost: float = Field(..., description="Location field boost value")
    is_active: bool = Field(..., description="Whether this configuration is active")
    created_at: str = Field(..., description="Timestamp when configuration was created")
    updated_at: str = Field(..., description="Timestamp when configuration was last updated")


@router.get(
    "/relevance-config",
    response_model=RelevanceConfigResponse,
    tags=["Search Analytics"],
)
async def get_relevance_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the active search relevance configuration.

    Returns the currently active relevance boost configuration that determines
    how different fields are weighted in search result scoring.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with active relevance configuration

    Raises:
        HTTPException(404): If no active configuration is found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/search/analytics/relevance-config"
        ... )
    """
    try:
        logger.info("Fetching active relevance configuration")

        # Query for active configuration
        stmt = select(SearchRelevanceConfig).where(
            SearchRelevanceConfig.is_active == True
        ).limit(1)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            # Create default configuration if none exists
            logger.info("No active configuration found, creating default")
            config = SearchRelevanceConfig(
                name="Default",
                skills_boost=1.0,
                experience_boost=1.0,
                education_boost=1.0,
                location_boost=1.0,
                is_active=True,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)

        logger.info(f"Found active configuration: {config.name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(config.id),
                "name": config.name,
                "skills_boost": config.skills_boost,
                "experience_boost": config.experience_boost,
                "education_boost": config.education_boost,
                "location_boost": config.location_boost,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching relevance configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch relevance configuration: {str(e)}",
        ) from e


@router.put(
    "/relevance-config",
    response_model=RelevanceConfigResponse,
    tags=["Search Analytics"],
)
async def update_relevance_config(
    request: Request,
    config_request: RelevanceConfigRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the active search relevance configuration.

    Updates the boost values for different fields in search result scoring.
    Higher boost values give more weight to that field in relevance calculations.

    Args:
        request: FastAPI request object
        config_request: New configuration values
        db: Database session

    Returns:
        JSON response with updated relevance configuration

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "/api/search/analytics/relevance-config",
        ...     json={
        ...         "skills_boost": 2.0,
        ...         "experience_boost": 1.5,
        ...         "education_boost": 1.0
        ...     }
        ... )
    """
    try:
        logger.info(f"Updating relevance configuration: {config_request.dict()}")

        # Get or create active configuration
        stmt = select(SearchRelevanceConfig).where(
            SearchRelevanceConfig.is_active == True
        ).limit(1)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            # Create new configuration if none exists
            logger.info("No active configuration found, creating new")
            config = SearchRelevanceConfig(
                name=config_request.name or "Default",
                skills_boost=config_request.skills_boost,
                experience_boost=config_request.experience_boost,
                education_boost=config_request.education_boost,
                location_boost=config_request.location_boost or 1.0,
                is_active=True,
            )
            db.add(config)
        else:
            # Update existing configuration
            logger.info(f"Updating existing configuration: {config.name}")
            if config_request.name:
                config.name = config_request.name
            config.skills_boost = config_request.skills_boost
            config.experience_boost = config_request.experience_boost
            config.education_boost = config_request.education_boost
            if config_request.location_boost:
                config.location_boost = config_request.location_boost

        await db.commit()
        await db.refresh(config)

        logger.info(f"Successfully updated relevance configuration: {config.name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(config.id),
                "name": config.name,
                "skills_boost": config.skills_boost,
                "experience_boost": config.experience_boost,
                "education_boost": config.education_boost,
                "location_boost": config.location_boost,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            },
        )

    except Exception as e:
        logger.error(f"Error updating relevance configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update relevance configuration: {str(e)}",
        ) from e
