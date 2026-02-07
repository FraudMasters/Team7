"""
Saved searches CRUD endpoints.

This module provides endpoints for:
- Creating saved searches with query and filters
- Listing all saved searches
- Getting a specific saved search
- Updating saved searches
- Deleting saved searches

Saved searches allow recruiters to store complex search queries and filter
configurations for reuse and automatic alert matching.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.saved_search import SavedSearch

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SavedSearchCreate(BaseModel):
    """Request model for creating a saved search."""

    name: str = Field(..., description="User-provided name for the saved search", min_length=1, max_length=255)
    query: str = Field(..., description="Search query string with boolean operators", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter settings (skills, experience_years, location, etc.)")


class SavedSearchUpdate(BaseModel):
    """Request model for updating a saved search."""

    name: Optional[str] = Field(None, description="Updated name for the saved search", min_length=1, max_length=255)
    query: Optional[str] = Field(None, description="Updated search query string", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Updated filter settings")


class SavedSearchResponse(BaseModel):
    """Response model for a saved search."""

    id: str = Field(..., description="Saved search UUID")
    name: str = Field(..., description="Saved search name")
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(..., description="Filter settings")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SavedSearchListResponse(BaseModel):
    """Response model for listing saved searches."""

    total: int = Field(..., description="Total number of saved searches")
    saved_searches: List[SavedSearchResponse] = Field(..., description="List of saved searches")


@router.post(
    "/",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Saved Searches"],
)
async def create_saved_search(
    request: Request,
    search_data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new saved search.

    Creates a saved search with the provided name, query, and optional filters.
    Saved searches can be reused later and will be checked against new resumes
    for automatic alerts.

    Args:
        request: FastAPI request object
        search_data: Saved search creation data (name, query, filters)
        db: Database session

    Returns:
        JSON response with created saved search details

    Raises:
        HTTPException(400): Invalid request data
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Senior Python Developers",
        ...     "query": "Python AND Django",
        ...     "filters": {"min_experience_years": 5}
        ... }
        >>> response = requests.post(
        ...     "/api/saved-searches/",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Creating saved search: {search_data.name}")

        # Create new saved search
        saved_search = SavedSearch(
            name=search_data.name,
            query=search_data.query,
            filters=search_data.filters or {},
        )

        db.add(saved_search)
        await db.commit()
        await db.refresh(saved_search)

        logger.info(f"Saved search created with ID: {saved_search.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(saved_search.id),
                "name": saved_search.name,
                "query": saved_search.query,
                "filters": saved_search.filters or {},
                "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None,
                "updated_at": saved_search.updated_at.isoformat() if saved_search.updated_at else None,
            },
        )

    except Exception as e:
        logger.error(f"Error creating saved search: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create saved search: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=SavedSearchListResponse,
    tags=["Saved Searches"],
)
async def list_saved_searches(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Filter by name (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all saved searches.

    Returns a paginated list of all saved searches. Can be filtered by name.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        search: Optional filter by name (case-insensitive partial match)
        db: Database session

    Returns:
        JSON response with list of saved searches and total count

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all saved searches
        >>> response = requests.get("/api/saved-searches/")
        >>> # Search by name
        >>> response = requests.get("/api/saved-searches/?search=python")
        >>> saved_searches = response.json()
    """
    try:
        logger.info(f"Listing saved searches - skip: {skip}, limit: {limit}, search: {search}")

        # Build base query
        query = select(SavedSearch)

        # Apply search filter if provided
        if search:
            query = query.where(SavedSearch.name.ilike(f"%{search}%"))

        # Get total count
        count_query = select(func.count()).select_from(SavedSearch)
        if search:
            count_query = count_query.where(SavedSearch.name.ilike(f"%{search}%"))

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Order by most recently created and apply pagination
        query = query.order_by(SavedSearch.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        saved_searches = result.scalars().all()

        # Convert to response format
        saved_searches_list = []
        for saved_search in saved_searches:
            saved_searches_list.append({
                "id": str(saved_search.id),
                "name": saved_search.name,
                "query": saved_search.query,
                "filters": saved_search.filters or {},
                "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None,
                "updated_at": saved_search.updated_at.isoformat() if saved_search.updated_at else None,
            })

        logger.info(f"Retrieved {len(saved_searches_list)} saved searches (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "saved_searches": saved_searches_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing saved searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list saved searches: {str(e)}",
        ) from e


@router.get(
    "/{saved_search_id}",
    response_model=SavedSearchResponse,
    tags=["Saved Searches"],
)
async def get_saved_search(
    request: Request,
    saved_search_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific saved search.

    Retrieves details of a specific saved search by its UUID.

    Args:
        request: FastAPI request object
        saved_search_id: Saved search UUID
        db: Database session

    Returns:
        JSON response with saved search details

    Raises:
        HTTPException(400): Invalid saved search ID format
        HTTPException(404): Saved search not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/saved-searches/abc-123-def"
        ... )
        >>> saved_search = response.json()
    """
    try:
        logger.info(f"Fetching saved search: {saved_search_id}")

        # Parse saved_search_id as UUID
        try:
            saved_search_uuid = UUID(saved_search_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid saved search ID format: {saved_search_id}",
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == saved_search_uuid)
        result = await db.execute(query)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved search not found: {saved_search_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(saved_search.id),
                "name": saved_search.name,
                "query": saved_search.query,
                "filters": saved_search.filters or {},
                "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None,
                "updated_at": saved_search.updated_at.isoformat() if saved_search.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved search {saved_search_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get saved search: {str(e)}",
        ) from e


@router.put(
    "/{saved_search_id}",
    response_model=SavedSearchResponse,
    tags=["Saved Searches"],
)
async def update_saved_search(
    request: Request,
    saved_search_id: str,
    search_data: SavedSearchUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a saved search.

    Updates the name, query, and/or filters of an existing saved search.
    Only fields that are provided in the request will be updated.

    Args:
        request: FastAPI request object
        saved_search_id: Saved search UUID
        search_data: Updated saved search data (partial update supported)
        db: Database session

    Returns:
        JSON response with updated saved search details

    Raises:
        HTTPException(400): Invalid saved search ID format
        HTTPException(404): Saved search not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Search Name"}
        >>> response = requests.put(
        ...     "/api/saved-searches/abc-123-def",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Updating saved search: {saved_search_id}")

        # Parse saved_search_id as UUID
        try:
            saved_search_uuid = UUID(saved_search_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid saved search ID format: {saved_search_id}",
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == saved_search_uuid)
        result = await db.execute(query)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved search not found: {saved_search_id}",
            )

        # Update fields if provided
        if search_data.name is not None:
            saved_search.name = search_data.name
        if search_data.query is not None:
            saved_search.query = search_data.query
        if search_data.filters is not None:
            saved_search.filters = search_data.filters

        await db.commit()
        await db.refresh(saved_search)

        logger.info(f"Saved search {saved_search_id} updated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(saved_search.id),
                "name": saved_search.name,
                "query": saved_search.query,
                "filters": saved_search.filters or {},
                "created_at": saved_search.created_at.isoformat() if saved_search.created_at else None,
                "updated_at": saved_search.updated_at.isoformat() if saved_search.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating saved search {saved_search_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update saved search: {str(e)}",
        ) from e


@router.delete(
    "/{saved_search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Saved Searches"],
)
async def delete_saved_search(
    request: Request,
    saved_search_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a saved search.

    Permanently deletes a saved search. This action cannot be undone.

    Args:
        request: FastAPI request object
        saved_search_id: Saved search UUID
        db: Database session

    Returns:
        HTTP 204 No Content on successful deletion

    Raises:
        HTTPException(400): Invalid saved search ID format
        HTTPException(404): Saved search not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "/api/saved-searches/abc-123-def"
        ... )
    """
    try:
        logger.info(f"Deleting saved search: {saved_search_id}")

        # Parse saved_search_id as UUID
        try:
            saved_search_uuid = UUID(saved_search_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid saved search ID format: {saved_search_id}",
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == saved_search_uuid)
        result = await db.execute(query)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved search not found: {saved_search_id}",
            )

        # Delete the saved search
        await db.delete(saved_search)
        await db.commit()

        logger.info(f"Saved search {saved_search_id} deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting saved search {saved_search_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete saved search: {str(e)}",
        ) from e
