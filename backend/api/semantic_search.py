"""
Semantic Search API endpoints for natural language candidate search.

This module provides endpoints for:
- Semantic search with natural language queries
- LLM-powered candidate matching beyond keywords
- Hybrid search combining semantic and keyword matching
- Detailed match explanations for individual candidates
- Multi-language query support

Leverages LLMSemanticMatcher for deep semantic understanding.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.semantic_search_service import (
    SemanticSearchService,
    SemanticSearchFilters,
    get_semantic_search_service,
)
from services.search_service import SearchFilters

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class SemanticSearchRequest(BaseModel):
    """Request model for semantic candidate search."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    vacancy_id: Optional[str] = Field(None, description="Optional job vacancy ID for context")
    min_semantic_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum semantic similarity score (0-1)")
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic scoring (0-1)")
    keyword_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for keyword matching (0-1)")
    use_hybrid: bool = Field(True, description="Whether to use hybrid search combining semantic and keyword")
    language: Optional[str] = Field(None, description="Language code for query (en, ru, etc.)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Traditional filter criteria")
    skip: int = Field(0, ge=0, description="Number of results to skip (pagination)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results to return")


class SemanticSearchFiltersModel(BaseModel):
    """Filter configuration for semantic search."""

    skills: Optional[List[str]] = Field(None, description="List of required skills")
    min_experience_years: Optional[int] = Field(None, ge=0, description="Minimum years of experience")
    max_experience_years: Optional[int] = Field(None, ge=0, description="Maximum years of experience")
    location: Optional[str] = Field(None, description="Location filter")
    education_level: Optional[str] = Field(None, description="Minimum education level")


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search combining semantic and keyword matching."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    semantic_weight: float = Field(0.6, ge=0.0, le=1.0, description="Weight for semantic scoring (0-1)")
    keyword_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for keyword matching (0-1)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Traditional filter criteria")
    skip: int = Field(0, ge=0, description="Number of results to skip (pagination)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results to return")


# Response Models
class SemanticMatchExplanationModel(BaseModel):
    """Match explanation for a candidate."""

    semantic_score: float = Field(..., description="Overall semantic similarity score (0-1)")
    skill_match_score: float = Field(..., description="Skills alignment score (0-1)")
    experience_relevance_score: float = Field(..., description="Experience relevance score (0-1)")
    context_fit_score: float = Field(..., description="Overall contextual fit score (0-1)")
    matched_skills: List[str] = Field(default_factory=list, description="Skills that directly matched")
    inferred_skills: List[str] = Field(default_factory=list, description="Skills inferred from context")
    transferable_skills: List[str] = Field(default_factory=list, description="Transferable skills identified")
    explanation: str = Field(..., description="Human-readable explanation of the match")


class SemanticCandidateResult(BaseModel):
    """Single candidate semantic search result."""

    id: str = Field(..., description="Resume UUID")
    filename: str = Field(..., description="Resume filename")
    status: str = Field(..., description="Resume processing status")
    created_at: str = Field(..., description="Creation timestamp")
    semantic_score: float = Field(..., description="Semantic similarity score (0-1)")
    keyword_score: float = Field(..., description="Keyword matching score (0-1)")
    final_score: float = Field(..., description="Combined final score")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience_years: Optional[float] = Field(None, description="Total experience in years")
    language: Optional[str] = Field(None, description="Detected language")
    match_explanation: Optional[SemanticMatchExplanationModel] = Field(None, description="Detailed match explanation")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""

    total: int = Field(..., description="Total number of matching candidates")
    candidates: List[Dict[str, Any]] = Field(..., description="List of candidate results")
    query: str = Field(..., description="Search query that was executed")
    execution_time_seconds: float = Field(..., description="Time taken to execute search")
    semantic_scores_used: bool = Field(..., description="Whether semantic scoring was applied")
    fallback_used: bool = Field(..., description="Whether fallback to keyword search was used")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum number of results returned")


class MatchExplanationRequest(BaseModel):
    """Request model for semantic match explanation."""

    query: str = Field(..., min_length=1, description="Natural language query")
    resume_id: str = Field(..., description="Resume UUID to explain")
    vacancy_id: Optional[str] = Field(None, description="Optional vacancy ID for job context")


class MatchExplanationResponse(BaseModel):
    """Response model for match explanation."""

    resume_id: str = Field(..., description="Resume UUID")
    semantic_score: float = Field(..., description="Overall semantic similarity score")
    skill_match_score: float = Field(..., description="Skills alignment score")
    experience_relevance_score: float = Field(..., description="Experience relevance score")
    context_fit_score: float = Field(..., description="Contextual fit score")
    matched_skills: List[str] = Field(default_factory=list, description="Skills that matched")
    inferred_skills: List[str] = Field(default_factory=list, description="Skills inferred")
    transferable_skills: List[str] = Field(default_factory=list, description="Transferable skills")
    missing_skills: List[str] = Field(default_factory=list, description="Missing skills")
    explanation: str = Field(..., description="Human-readable explanation")
    used_embeddings: bool = Field(..., description="Whether embeddings were used")


class HybridSearchResponse(BaseModel):
    """Response model for hybrid search."""

    total: int = Field(..., description="Total number of matching candidates")
    candidates: List[Dict[str, Any]] = Field(..., description="List of candidate results")
    query: str = Field(..., description="Search query that was executed")
    execution_time_seconds: float = Field(..., description="Time taken to execute search")
    semantic_scores_used: bool = Field(..., description="Whether semantic scoring was applied")
    fallback_used: bool = Field(..., description="Whether fallback to keyword search was used")
    semantic_weight: float = Field(..., description="Weight applied to semantic scores")
    keyword_weight: float = Field(..., description="Weight applied to keyword scores")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum number of results returned")


@router.post(
    "/candidates",
    response_model=SemanticSearchResponse,
    tags=["Semantic Search"],
)
async def semantic_search_candidates(
    request: Request,
    search_data: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Semantic search for candidates using natural language queries.

    This endpoint provides advanced semantic search capabilities including:
    - Natural language query understanding (e.g., "Find senior Python developers with fintech experience")
    - LLM-powered semantic matching beyond keyword matching
    - Hybrid search combining semantic and keyword approaches
    - Multi-language support for resumes in different languages
    - Explainable results showing why candidates matched

    The endpoint uses large language models to understand the semantic meaning
    of queries and match them to candidate resumes based on context, not just
    keywords.

    Examples of natural language queries:
    - "Find me senior Python developers with team leadership experience"
    - "Looking for frontend developers who know React and have worked on e-commerce projects"
    - "Search for data scientists with machine learning experience in healthcare"

    Args:
        request: FastAPI request object
        search_data: Semantic search request with query, filters, and scoring options
        db: Database session

    Returns:
        JSON response with ranked candidates, semantic scores, and match explanations

    Raises:
        HTTPException(400): If query is empty or parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Natural language search
        >>> data = {
        ...     "query": "Find senior Python developers with team leadership experience",
        ...     "limit": 10
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/candidates",
        ...     json=data
        ... )
        >>> # Search with vacancy context
        >>> data = {
        ...     "query": "Experienced backend developer",
        ...     "vacancy_id": "vacancy-uuid",
        ...     "min_semantic_score": 0.7,
        ...     "limit": 20
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/candidates",
        ...     json=data
        ... )
        >>> # Search with traditional filters
        >>> data = {
        ...     "query": "Senior software engineer",
        ...     "filters": {
        ...         "min_experience_years": 5,
        ...         "location": "Remote"
        ...     },
        ...     "semantic_weight": 0.8,
        ...     "keyword_weight": 0.2
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/candidates",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Semantic search - query: {search_data.query}, "
            f"vacancy_id: {search_data.vacancy_id}, "
            f"use_hybrid: {search_data.use_hybrid}, "
            f"min_score: {search_data.min_semantic_score}"
        )

        # Get semantic search service
        search_service = get_semantic_search_service(db)

        # Extract traditional filters from request
        traditional_filters = {}
        if search_data.filters:
            filters_model = SemanticSearchFiltersModel(**search_data.filters)
            traditional_filters = {
                "skills": filters_model.skills,
                "min_experience_years": filters_model.min_experience_years,
                "max_experience_years": filters_model.max_experience_years,
                "location": filters_model.location,
                "education_level": filters_model.education_level,
            }

        # Build semantic search filters
        filters = SemanticSearchFilters(
            query=search_data.query,
            vacancy_id=search_data.vacancy_id,
            min_semantic_score=search_data.min_semantic_score,
            semantic_weight=search_data.semantic_weight,
            keyword_weight=search_data.keyword_weight,
            use_hybrid=search_data.use_hybrid,
            language=search_data.language,
            skills=traditional_filters.get("skills"),
            min_experience_years=traditional_filters.get("min_experience_years"),
            max_experience_years=traditional_filters.get("max_experience_years"),
            location=traditional_filters.get("location"),
            education_level=traditional_filters.get("education_level"),
            skip=search_data.skip,
            limit=search_data.limit,
        )

        # Execute semantic search
        result = await search_service.semantic_search_candidates(filters)

        logger.info(
            f"Semantic search completed: {result.total} total candidates, "
            f"returned {len(result.candidates)} results in "
            f"{result.execution_time_seconds:.3f}s, "
            f"semantic_used: {result.semantic_scores_used}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "execution_time_seconds": result.execution_time_seconds,
                "semantic_scores_used": result.semantic_scores_used,
                "fallback_used": result.fallback_used,
                "filters_applied": result.filters_applied,
                "skip": search_data.skip,
                "limit": search_data.limit,
            },
        )

    except ValueError as e:
        logger.error(f"Invalid semantic search parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        ) from e


@router.get(
    "/candidates",
    response_model=SemanticSearchResponse,
    tags=["Semantic Search"],
)
async def semantic_search_candidates_get(
    request: Request,
    query: str = Query(..., min_length=1, description="Natural language search query"),
    vacancy_id: Optional[str] = Query(None, description="Optional job vacancy ID for context"),
    min_semantic_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum semantic score"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Semantic weight"),
    keyword_weight: float = Query(0.3, ge=0.0, le=1.0, description="Keyword weight"),
    use_hybrid: bool = Query(True, description="Use hybrid search"),
    language: Optional[str] = Query(None, description="Language code"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
    min_experience_years: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    max_experience_years: Optional[int] = Query(None, ge=0, description="Maximum years of experience"),
    location: Optional[str] = Query(None, description="Location filter"),
    education_level: Optional[str] = Query(None, description="Minimum education level"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Semantic search for candidates using GET request with query parameters.

    This is an alternative to the POST endpoint that uses query parameters
    instead of a JSON body. Useful for simple searches and browser-based queries.

    Args:
        request: FastAPI request object
        query: Natural language search query
        vacancy_id: Optional job vacancy ID for context
        min_semantic_score: Minimum semantic similarity score (0-1)
        semantic_weight: Weight for semantic scoring (0-1)
        keyword_weight: Weight for keyword matching (0-1)
        use_hybrid: Whether to use hybrid search
        language: Language code for query
        skills: Comma-separated list of skills
        min_experience_years: Minimum years of experience
        max_experience_years: Maximum years of experience
        location: Location filter
        education_level: Minimum education level
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return
        db: Database session

    Returns:
        JSON response with ranked candidates and semantic scores

    Raises:
        HTTPException(400): If parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Simple semantic search
        >>> response = requests.get(
        ...     "http://localhost:8000/api/semantic-search/candidates",
        ...     params={
        ...         "query": "Find senior Python developers",
        ...         "limit": 10
        ...     }
        ... )
        >>> # Search with filters
        >>> response = requests.get(
        ...     "http://localhost:8000/api/semantic-search/candidates",
        ...     params={
        ...         "query": "Senior backend engineer",
        ...         "min_experience_years": 5,
        ...         "location": "Remote",
        ...         "min_semantic_score": 0.7
        ...     }
        ... )
    """
    try:
        logger.info(
            f"GET semantic search - query: {query}, "
            f"vacancy_id: {vacancy_id}, "
            f"min_score: {min_semantic_score}"
        )

        # Get semantic search service
        search_service = get_semantic_search_service(db)

        # Parse skills if provided
        skills_list = None
        if skills:
            skills_list = [s.strip() for s in skills.split(",")]

        # Build semantic search filters
        filters = SemanticSearchFilters(
            query=query,
            vacancy_id=vacancy_id,
            min_semantic_score=min_semantic_score,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            use_hybrid=use_hybrid,
            language=language,
            skills=skills_list,
            min_experience_years=min_experience_years,
            max_experience_years=max_experience_years,
            location=location,
            education_level=education_level,
            skip=skip,
            limit=limit,
        )

        # Execute semantic search
        result = await search_service.semantic_search_candidates(filters)

        logger.info(
            f"GET semantic search completed: {result.total} total, "
            f"returned {len(result.candidates)} results"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "execution_time_seconds": result.execution_time_seconds,
                "semantic_scores_used": result.semantic_scores_used,
                "fallback_used": result.fallback_used,
                "filters_applied": result.filters_applied,
                "skip": skip,
                "limit": limit,
            },
        )

    except ValueError as e:
        logger.error(f"Invalid semantic search parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        ) from e


@router.post(
    "/explain",
    response_model=MatchExplanationResponse,
    tags=["Semantic Search"],
)
async def explain_match_post(
    request: Request,
    explanation_request: MatchExplanationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get detailed explanation of why a resume matches a query (POST endpoint).

    This endpoint provides semantic match explanations showing:
    - Overall semantic similarity score
    - Skill match score with matched/inferred/missing skills
    - Experience relevance score
    - Context fit score
    - Human-readable explanation of the match

    The POST version allows passing parameters in JSON body for easier
    integration with frontend components and better handling of complex queries.

    Args:
        request: FastAPI request object
        explanation_request: Match explanation request with query and resume_id
        db: Database session

    Returns:
        JSON response with detailed match explanation

    Raises:
        HTTPException(400): If parameters are invalid or LLM unavailable
        HTTPException(404): If resume not found
        HTTPException(500): If explanation generation fails

    Examples:
        >>> import requests
        >>> # Get match explanation
        >>> data = {
        ...     "query": "Find senior Python developers with leadership experience",
        ...     "resume_id": "abc-123-resume-id"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/explain",
        ...     json=data
        ... )
        >>> # With vacancy context
        >>> data = {
        ...     "query": "Backend engineer",
        ...     "resume_id": "abc-123-resume-id",
        ...     "vacancy_id": "vacancy-uuid"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/explain",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"POST explain match - resume: {explanation_request.resume_id}, "
            f"query: {explanation_request.query}, "
            f"vacancy_id: {explanation_request.vacancy_id}"
        )

        # Get semantic search service
        search_service = get_semantic_search_service(db)

        # Get match explanation
        explanation = await search_service.explain_match(
            query=explanation_request.query,
            resume_id=explanation_request.resume_id,
            vacancy_id=explanation_request.vacancy_id,
        )

        logger.info(
            f"POST match explanation generated: semantic_score={explanation.semantic_score:.3f}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=explanation.to_dict(),
        )

    except ValueError as e:
        logger.error(f"POST match explanation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "LLM unavailable" in str(e) else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error generating POST match explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate match explanation: {str(e)}",
        ) from e


@router.get(
    "/explain/{resume_id}",
    response_model=MatchExplanationResponse,
    tags=["Semantic Search"],
)
async def explain_match(
    request: Request,
    resume_id: str,
    query: str = Query(..., min_length=1, description="Natural language query"),
    vacancy_id: Optional[str] = Query(None, description="Optional vacancy ID for context"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get detailed explanation of why a resume matches a query (GET endpoint).

    This endpoint provides semantic match explanations showing:
    - Overall semantic similarity score
    - Skill match score with matched/inferred/missing skills
    - Experience relevance score
    - Context fit score
    - Human-readable explanation of the match

    Args:
        request: FastAPI request object
        resume_id: Resume UUID to explain
        query: Natural language query
        vacancy_id: Optional vacancy ID for job context
        db: Database session

    Returns:
        JSON response with detailed match explanation

    Raises:
        HTTPException(400): If parameters are invalid or LLM unavailable
        HTTPException(404): If resume not found
        HTTPException(500): If explanation generation fails

    Examples:
        >>> import requests
        >>> # Get match explanation
        >>> response = requests.get(
        ...     "http://localhost:8000/api/semantic-search/explain/resume-uuid",
        ...     params={
        ...         "query": "Senior Python developer with leadership experience"
        ...         }
        ...     )
        >>> # With vacancy context
        >>> response = requests.get(
        ...     "http://localhost:8000/api/semantic-search/explain/resume-uuid",
        ...     params={
        ...         "query": "Backend engineer",
        ...         "vacancy_id": "vacancy-uuid"
        ...     }
        ... )
    """
    try:
        logger.info(
            f"Explaining match for resume: {resume_id}, "
            f"query: {query}, "
            f"vacancy_id: {vacancy_id}"
        )

        # Get semantic search service
        search_service = get_semantic_search_service(db)

        # Get match explanation
        explanation = await search_service.explain_match(
            query=query,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
        )

        logger.info(
            f"Match explanation generated: semantic_score={explanation.semantic_score:.3f}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=explanation.to_dict(),
        )

    except ValueError as e:
        logger.error(f"Match explanation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "LLM unavailable" in str(e) else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error generating match explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate match explanation: {str(e)}",
        ) from e


@router.post(
    "/hybrid",
    response_model=HybridSearchResponse,
    tags=["Semantic Search"],
)
async def hybrid_search(
    request: Request,
    search_data: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Hybrid search combining semantic and keyword matching.

    This endpoint provides the best of both worlds:
    - Semantic understanding using LLM-powered natural language processing
    - Traditional keyword matching for exact skill/term matching
    - Configurable weights to balance between semantic and keyword approaches
    - Faster than pure semantic search with better relevance than pure keyword

    The hybrid approach is ideal for:
    - Finding candidates with specific skills while also understanding context
    - Balancing precision (keyword) with recall (semantic)
    - Handling variations in job titles and descriptions
    - Searches that need both exact matches and conceptual understanding

    Args:
        request: FastAPI request object
        search_data: Hybrid search request with query, weights, and optional filters
        db: Database session

    Returns:
        JSON response with ranked candidates, both semantic and keyword scores,
        and combined final score

    Raises:
        HTTPException(400): If query is empty or parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Balanced hybrid search
        >>> data = {
        ...     "query": "React developer with TypeScript",
        ...     "semantic_weight": 0.6,
        ...     "keyword_weight": 0.4,
        ...     "limit": 10
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/hybrid",
        ...     json=data
        ... )
        >>> # Semantic-focused search with filters
        >>> data = {
        ...     "query": "Senior Python backend engineer",
        ...     "semantic_weight": 0.8,
        ...     "keyword_weight": 0.2,
        ...     "filters": {
        ...         "min_experience_years": 5,
        ...         "location": "Remote"
        ...     },
        ...     "limit": 20
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/hybrid",
        ...     json=data
        ... )
        >>> # Keyword-focused search
        >>> data = {
        ...     "query": "Java Spring developer",
        ...     "semantic_weight": 0.3,
        ...     "keyword_weight": 0.7,
        ...     "filters": {
        ...         "skills": ["Java", "Spring", "PostgreSQL"]
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/semantic-search/hybrid",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Hybrid search - query: {search_data.query}, "
            f"semantic_weight: {search_data.semantic_weight}, "
            f"keyword_weight: {search_data.keyword_weight}, "
            f"skip: {search_data.skip}, limit: {search_data.limit}"
        )

        # Get semantic search service
        search_service = get_semantic_search_service(db)

        # Extract traditional filters from request
        traditional_filters = None
        if search_data.filters:
            filters_model = SemanticSearchFiltersModel(**search_data.filters)
            traditional_filters = SearchFilters(
                skills=filters_model.skills,
                min_experience_years=filters_model.min_experience_years,
                max_experience_years=filters_model.max_experience_years,
                location=filters_model.location,
                education_level=filters_model.education_level,
            )

        # Execute hybrid search
        result = await search_service.hybrid_search(
            query=search_data.query,
            semantic_weight=search_data.semantic_weight,
            keyword_weight=search_data.keyword_weight,
            filters=traditional_filters,
            skip=search_data.skip,
            limit=search_data.limit,
        )

        logger.info(
            f"Hybrid search completed: {result.total} total candidates, "
            f"returned {len(result.candidates)} results in "
            f"{result.execution_time_seconds:.3f}s, "
            f"semantic_used: {result.semantic_scores_used}"
        )

        # Build filters applied dict
        filters_applied = result.filters_applied.copy()
        if search_data.filters:
            filters_applied.update(search_data.filters)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "execution_time_seconds": result.execution_time_seconds,
                "semantic_scores_used": result.semantic_scores_used,
                "fallback_used": result.fallback_used,
                "semantic_weight": search_data.semantic_weight,
                "keyword_weight": search_data.keyword_weight,
                "filters_applied": filters_applied,
                "skip": search_data.skip,
                "limit": search_data.limit,
            },
        )

    except ValueError as e:
        logger.error(f"Invalid hybrid search parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error during hybrid search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}",
        ) from e
