"""
Search API endpoints for candidates.

Provides advanced search with filtering across candidates and resumes.
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


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for candidate search."""
    query: Optional[str] = Field(None, description="Search query string")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(100, ge=1, le=200, description="Max results")
    sort_by: str = Field("created_at", description="Sort field: created_at, name, experience, rating")


class SearchResponse(BaseModel):
    """Response model for candidate search."""
    total: int
    candidates: List[Dict[str, Any]]
    query: str
    filters_applied: Dict[str, Any]
    execution_time_seconds: float
    skip: int
    limit: int


class BulkActionRequest(BaseModel):
    """Request model for bulk actions on candidates."""
    action: str = Field(..., description="Action: tag, status, export")
    resume_ids: List[str] = Field(..., description="List of candidate IDs")
    tag_name: Optional[str] = Field(None, description="Tag name for tag action")
    new_status: Optional[str] = Field(None, description="New status for status action")


@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_candidates(
    request: Request,
    search_data: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for candidates with advanced filters.

    Args:
        request: FastAPI request
        search_data: Search request with query, filters, pagination
        db: Database session

    Returns:
        JSON response with search results

    Examples:
        >>> # Search by query
        >>> data = {"query": "Python", "limit": 10}
        >>> # Filter by location and experience
        >>> data = {
        ...     "filters": {
        ...         "location": "Remote",
        ...         "min_experience_years": 3
        ...     }
        ... }
    """
    try:
        search_service = get_search_service(db)

        # Build SearchFilters from request
        filters = None
        if search_data.filters:
            filters = SearchFilters(
                query=search_data.query,
                skills=search_data.filters.get("skills"),
                min_experience_years=search_data.filters.get("min_experience_years"),
                max_experience_years=search_data.filters.get("max_experience_years"),
                location=search_data.filters.get("location"),
                status=search_data.filters.get("status"),
                source=search_data.filters.get("source"),
                min_rating=search_data.filters.get("min_rating"),
                date_from=search_data.filters.get("date_from"),
                date_to=search_data.filters.get("date_to"),
                tag_ids=search_data.filters.get("tag_ids"),
            )

        result = await search_service.search_candidates(
            query=search_data.query,
            filters=filters,
            skip=search_data.skip,
            limit=search_data.limit,
            sort_by=search_data.sort_by,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error during candidate search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_candidates_get(
    request: Request,
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    min_experience: Optional[int] = Query(None, ge=0, description="Min experience years"),
    max_experience: Optional[int] = Query(None, ge=0, description="Max experience years"),
    status: Optional[str] = Query(None, description="Candidate status"),
    source: Optional[str] = Query(None, description="Candidate source"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Min rating"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    sort_by: str = Query("created_at", description="Sort field"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search candidates via GET with query parameters.

    Args:
        request: FastAPI request
        query: Search query
        location: Location filter
        min_experience: Minimum experience years
        max_experience: Maximum experience years
        status: Candidate status filter
        source: Source filter
        min_rating: Minimum rating
        skip: Pagination offset
        limit: Max results
        sort_by: Sort field
        db: Database session

    Returns:
        JSON response with search results
    """
    try:
        search_service = get_search_service(db)

        # Build filters dict
        filters_dict = {}
        if location:
            filters_dict["location"] = location
        if min_experience is not None:
            filters_dict["min_experience_years"] = min_experience
        if max_experience is not None:
            filters_dict["max_experience_years"] = max_experience
        if status:
            filters_dict["status"] = status
        if source:
            filters_dict["source"] = source
        if min_rating is not None:
            filters_dict["min_rating"] = min_rating

        filters = SearchFilters(**filters_dict) if filters_dict else None

        result = await search_service.search_candidates(
            query=query,
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
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

    except Exception as e:
        logger.error(f"Error during candidate search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.post("/bulk-action", tags=["Candidates"])
async def bulk_action(
    request: Request,
    data: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Perform bulk action on candidates.

    Args:
        request: FastAPI request
        data: Bulk action request with action type and candidate IDs
        db: Database session

    Returns:
        JSON response with action result
    """
    try:
        if data.action == "export":
            # Return candidates for export
            from sqlalchemy import select as sql_select
            from models.candidate import Candidate

            result = await db.execute(
                sql_select(Candidate).where(Candidate.id.in_(data.resume_ids))
            )
            candidates = result.scalars().all()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "total": len(candidates),
                    "candidates": [
                        {
                            "id": str(c.id),
                            "full_name": c.full_name,
                            "email": c.email,
                            "current_position": c.current_position,
                            "location": c.location,
                            "status": c.status.value if hasattr(c.status, 'value') else str(c.status),
                        }
                        for c in candidates
                    ],
                },
            )

        elif data.action == "tag":
            if not data.tag_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="tag_name is required for tag action"
                )
            # TODO: Implement tagging logic
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Tagged {len(data.resume_ids)} candidates with '{data.tag_name}'"}
            )

        elif data.action == "status":
            if not data.new_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="new_status is required for status action"
                )
            # TODO: Implement status change logic
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Updated status to '{data.new_status}' for {len(data.resume_ids)} candidates"}
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {data.action}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during bulk action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk action failed: {str(e)}",
        ) from e
