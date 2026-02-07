"""
Context API endpoints for knowledge graph operations.

This module provides endpoints for interacting with the Graphiti knowledge graph,
including episode ingestion, semantic search, and health monitoring.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request and Response Models


class EpisodeRequest(BaseModel):
    """Request model for adding an episode to the knowledge graph."""

    name: str = Field(..., description="Name/title of the episode", min_length=1, max_length=500)
    body: str = Field(..., description="Main content of the episode", min_length=1)
    source: str = Field(
        default="manual",
        description="Source identifier (e.g., 'resume', 'vacancy', 'conversation', 'manual')",
    )
    source_description: str = Field(
        default="Manually added via API",
        description="Human-readable description of the source",
    )
    reference_time: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp for the episode (defaults to current time)",
    )


class EpisodeResponse(BaseModel):
    """Response model for episode creation."""

    episode_id: str = Field(..., description="UUID of the created episode")
    status: str = Field(..., description="Status of the operation")
    name: str = Field(..., description="Name of the episode")


class SearchResult(BaseModel):
    """Single search result from the knowledge graph."""

    name: str = Field(..., description="Name of the matching episode")
    body: str = Field(..., description="Content of the matching episode")
    score: float = Field(..., description="Relevance score (0-1)")
    uuid: str = Field(..., description="UUID of the episode")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class SearchResponse(BaseModel):
    """Response model for semantic search."""

    query: str = Field(..., description="The search query that was executed")
    results: List[SearchResult] = Field(..., description="List of search results")
    count: int = Field(..., description="Number of results returned")


class HealthResponse(BaseModel):
    """Response model for health check."""

    healthy: bool = Field(..., description="Overall health status")
    initialized: bool = Field(..., description="Whether the service is initialized")
    neo4j_connected: bool = Field(..., description="Whether Neo4j is connected")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    episode_count: int = Field(..., description="Total number of episodes in the graph")


# Endpoints


@router.post(
    "/episodes",
    response_model=EpisodeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Context"],
)
async def add_episode(request: EpisodeRequest) -> JSONResponse:
    """
    Add a new episode to the knowledge graph.

    Episodes represent contextual information such as resume content,
    vacancy descriptions, or interaction history. This endpoint allows
    manual ingestion of episodes into the graph.

    Args:
        request: Episode data including name, body, source, and optional timestamp

    Returns:
        JSON response with episode ID and status

    Raises:
        HTTPException: If episode addition fails (500) or service is unavailable (503)

    Example:
        >>> POST /api/context/episodes
        {
            "name": "Software Engineer Resume",
            "body": "John Doe - Senior Python Developer with 5 years experience...",
            "source": "resume",
            "source_description": "Uploaded resume file"
        }
    """
    try:
        service = get_graphiti_service()

        # Add the episode
        episode_id = await service.add_episode(
            name=request.name,
            body=request.body,
            source=request.source,
            source_description=request.source_description,
            reference_time=request.reference_time or datetime.utcnow(),
        )

        logger.info(f"Added episode: {request.name} ({episode_id})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "episode_id": episode_id,
                "status": "created",
                "name": request.name,
            },
        )

    except RuntimeError as e:
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph service not available. Please try again later.",
        ) from e

    except ValueError as e:
        logger.warning(f"Invalid episode data: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(f"Failed to add episode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add episode to knowledge graph",
        ) from e


@router.get(
    "/search",
    response_model=SearchResponse,
    tags=["Context"],
)
async def search_context(
    query: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
) -> JSONResponse:
    """
    Search the knowledge graph for relevant context.

    Performs semantic search across all episodes to find relevant information.
    The search uses vector embeddings to find semantically similar content.

    Args:
        query: Search query text
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        JSON response with search results ranked by relevance score

    Raises:
        HTTPException: If search fails (500) or service is unavailable (503)

    Example:
        >>> GET /api/context/search?q=python+developer&limit=5
        {
            "query": "python developer",
            "results": [
                {
                    "name": "Software Engineer Resume",
                    "body": "...",
                    "score": 0.95,
                    "uuid": "abc-123",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "count": 1
        }
    """
    try:
        service = get_graphiti_service()

        # Perform search
        results = await service.search(query=query, limit=limit)

        # Convert to response format
        search_results = [
            {
                "name": r.get("name", ""),
                "body": r.get("body", ""),
                "score": r.get("score", 0.0),
                "uuid": r.get("uuid", ""),
                "created_at": r.get("created_at"),
            }
            for r in results
        ]

        logger.debug(f"Search for '{query}' returned {len(search_results)} results")

        return JSONResponse(
            content={
                "query": query,
                "results": search_results,
                "count": len(search_results),
            }
        )

    except RuntimeError as e:
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph service not available. Please try again later.",
        ) from e

    except Exception as e:
        logger.error(f"Failed to search knowledge graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge graph",
        ) from e


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Context"],
)
async def health_check() -> JSONResponse:
    """
    Check the health of the Graphiti service and Neo4j connection.

    Returns the current status of the knowledge graph service including
    initialization state, Neo4j connectivity, and episode count.

    Returns:
        JSON response with health status information

    Example:
        >>> GET /api/context/health
        {
            "healthy": true,
            "initialized": true,
            "neo4j_connected": true,
            "error": null,
            "episode_count": 42
        }
    """
    try:
        service = get_graphiti_service()

        # Get health status
        health = await service.health_check()

        # Get episode count if service is healthy
        episode_count = 0
        if health.get("healthy"):
            try:
                episode_count = await service.get_episode_count()
            except Exception as e:
                logger.warning(f"Failed to get episode count: {e}")

        health["episode_count"] = episode_count

        return JSONResponse(content=health)

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "healthy": False,
                "initialized": False,
                "neo4j_connected": False,
                "error": str(e),
                "episode_count": 0,
            },
        )
