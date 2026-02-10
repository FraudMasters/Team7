"""
Job Search API endpoints for job seekers.

This module provides endpoints for:
- Searching job vacancies with full-text search and boolean operators
- Filtering jobs by location, salary, work format, employment type, industry, skills
- Pagination and sorting for job listings

Leverages PostgreSQL full-text search for fast, flexible queries.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class JobSearchRequest(BaseModel):
    """Request model for job search."""

    query: Optional[str] = Field(None, description="Search query for job title and description")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for search")
    skip: int = Field(0, ge=0, description="Number of results to skip (pagination)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results to return")
    sort_by: str = Field("date", description="Sort field: date, salary_asc, salary_desc, relevance")


class JobSearchFilters(BaseModel):
    """Filter configuration for job search."""

    location: Optional[str] = Field(None, description="Location filter (partial match)")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    work_format: Optional[str] = Field(None, description="Work format: remote, office, hybrid")
    employment_type: Optional[str] = Field(None, description="Employment type: full-time, part-time, contract")
    industry: Optional[str] = Field(None, description="Industry sector filter")
    skills: Optional[List[str]] = Field(None, description="List of required skills (OR logic)")


# Response Models
class JobSearchResult(BaseModel):
    """Single job search result."""

    id: str = Field(..., description="Job vacancy UUID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    required_skills: List[str] = Field(..., description="Required technical skills")
    min_experience_months: Optional[int] = Field(None, description="Minimum experience")
    additional_requirements: List[str] = Field(..., description="Additional skills")
    industry: Optional[str] = Field(None, description="Industry")
    work_format: Optional[str] = Field(None, description="Work format")
    location: Optional[str] = Field(None, description="Location")
    salary_min: Optional[int] = Field(None, description="Min salary")
    salary_max: Optional[int] = Field(None, description="Max salary")
    english_level: Optional[str] = Field(None, description="English level")
    employment_type: Optional[str] = Field(None, description="Employment type")
    created_at: str = Field(..., description="Creation timestamp")


class JobSearchResponse(BaseModel):
    """Response model for job search."""

    total: int = Field(..., description="Total number of matching jobs")
    jobs: List[Dict[str, Any]] = Field(..., description="List of job results")
    query: str = Field(..., description="Search query that was executed")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    execution_time_seconds: float = Field(..., description="Time taken to execute search")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum number of results returned")


def _vacancy_to_dict(vacancy: JobVacancy) -> dict:
    """Convert JobVacancy model to response dict."""
    return {
        "id": str(vacancy.id),
        "title": vacancy.title,
        "description": vacancy.description,
        "required_skills": vacancy.required_skills or [],
        "min_experience_months": vacancy.min_experience_months,
        "additional_requirements": vacancy.additional_requirements or [],
        "industry": vacancy.industry,
        "work_format": vacancy.work_format,
        "location": vacancy.location,
        "salary_min": vacancy.salary_min,
        "salary_max": vacancy.salary_max,
        "english_level": vacancy.english_level,
        "employment_type": vacancy.employment_type,
        "created_at": vacancy.created_at.isoformat() if vacancy.created_at else None,
    }


@router.post(
    "/search",
    response_model=JobSearchResponse,
    tags=["Job Search"],
)
async def search_jobs(
    request: Request,
    search_data: JobSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for jobs with advanced filters.

    This endpoint provides powerful job search capabilities including:
    - Full-text search on job title and description
    - Multi-field filtering: location, salary, work format, employment type, industry, skills
    - Flexible sorting by date, salary, or relevance

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
        ...     "query": "Python developer",
        ...     "filters": {
        ...         "location": "Remote",
        ...         "salary_min": 50000,
        ...         "work_format": "remote"
        ...     },
        ...     "limit": 10
        ... }
        >>> response = requests.post(
        ...     "/api/job-search/search",
        ...     json=data
        ... )
        >>> # Filter by skills only
        >>> data = {
        ...     "filters": {
        ...         "skills": ["Python", "FastAPI"],
        ...         "salary_min": 80000
        ...     }
        ... }
        >>> response = requests.post(
        ...     "/api/job-search/search",
        ...     json=data
        ... )
    """
    start_time = time.time()

    try:
        logger.info(
            f"Searching jobs - query: {search_data.query}, "
            f"filters: {search_data.filters}, skip: {search_data.skip}, "
            f"limit: {search_data.limit}, sort_by: {search_data.sort_by}"
        )

        # Build base query - only active vacancies
        query = select(JobVacancy).where(JobVacancy.is_active == True)

        # Apply full-text search on query
        if search_data.query:
            search_term = f"%{search_data.query}%"
            query = query.where(
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.description.ilike(search_term),
                )
            )

        # Apply filters
        filters_applied = {}
        if search_data.filters:
            filters = search_data.filters

            # Location filter (partial match, case-insensitive)
            if filters.get("location"):
                location_term = f"%{filters['location']}%"
                query = query.where(JobVacancy.location.ilike(location_term))
                filters_applied["location"] = filters["location"]

            # Salary range filter
            if filters.get("salary_min") is not None:
                query = query.where(
                    or_(
                        JobVacancy.salary_min.is_(None),
                        JobVacancy.salary_min >= filters["salary_min"]
                    )
                )
                filters_applied["salary_min"] = filters["salary_min"]

            if filters.get("salary_max") is not None:
                query = query.where(
                    or_(
                        JobVacancy.salary_max.is_(None),
                        JobVacancy.salary_max <= filters["salary_max"]
                    )
                )
                filters_applied["salary_max"] = filters["salary_max"]

            # Work format filter (exact match)
            if filters.get("work_format"):
                query = query.where(JobVacancy.work_format == filters["work_format"].lower())
                filters_applied["work_format"] = filters["work_format"]

            # Employment type filter (exact match)
            if filters.get("employment_type"):
                query = query.where(JobVacancy.employment_type == filters["employment_type"].lower())
                filters_applied["employment_type"] = filters["employment_type"]

            # Industry filter (partial match, case-insensitive)
            if filters.get("industry"):
                industry_term = f"%{filters['industry']}%"
                query = query.where(JobVacancy.industry.ilike(industry_term))
                filters_applied["industry"] = filters["industry"]

            # Skills filter (OR logic - match any skill in required_skills)
            if filters.get("skills"):
                skills_list = filters["skills"]
                if skills_list:
                    # Create conditions for each skill
                    skill_conditions = []
                    for skill in skills_list:
                        skill_conditions.append(JobVacancy.required_skills.contains([skill]))
                    # Combine with OR logic - match any of the skills
                    if skill_conditions:
                        query = query.where(or_(*skill_conditions))
                    filters_applied["skills"] = skills_list

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one() or 0

        # Apply sorting
        sort_by = search_data.sort_by.lower()
        if sort_by == "salary_asc":
            query = query.order_by(JobVacancy.salary_min.asc().nulls_last())
        elif sort_by == "salary_desc":
            query = query.order_by(JobVacancy.salary_min.desc().nulls_last())
        elif sort_by == "relevance":
            # For relevance, we could implement more sophisticated ranking
            # For now, sort by creation date as a relevance proxy
            query = query.order_by(JobVacancy.created_at.desc())
        else:  # default: date
            query = query.order_by(JobVacancy.created_at.desc())

        # Apply pagination
        query = query.offset(search_data.skip).limit(search_data.limit)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        # Convert to response format
        jobs_list = [_vacancy_to_dict(v) for v in vacancies]

        execution_time = time.time() - start_time

        logger.info(
            f"Search completed: {total} total jobs, "
            f"returned {len(jobs_list)} results in "
            f"{execution_time:.3f}s"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "jobs": jobs_list,
                "query": search_data.query or "",
                "filters_applied": filters_applied,
                "execution_time_seconds": execution_time,
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
        logger.error(f"Error during job search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get(
    "/search",
    response_model=JobSearchResponse,
    tags=["Job Search"],
)
async def search_jobs_get(
    request: Request,
    query: Optional[str] = Query(None, description="Search query for job title and description"),
    location: Optional[str] = Query(None, description="Location filter"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    work_format: Optional[str] = Query(None, description="Work format: remote, office, hybrid"),
    employment_type: Optional[str] = Query(None, description="Employment type: full-time, part-time, contract"),
    industry: Optional[str] = Query(None, description="Industry sector filter"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of results"),
    sort_by: str = Query("date", description="Sort field: date, salary_asc, salary_desc, relevance"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for jobs using GET request with query parameters.

    This is an alternative to the POST endpoint that uses query parameters
    instead of a JSON body. Useful for simple searches and browser-based queries.

    Args:
        request: FastAPI request object
        query: Search query for job title and description
        location: Location filter
        salary_min: Minimum salary
        salary_max: Maximum salary
        work_format: Work format (remote, office, hybrid)
        employment_type: Employment type (full-time, part-time, contract)
        industry: Industry sector filter
        skills: Comma-separated list of skills (e.g., "Python, Django, FastAPI")
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return
        sort_by: Sort field (date, salary_asc, salary_desc, relevance)
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
        ...     "/api/job-search/search",
        ...     params={"query": "Python developer", "limit": 10}
        ... )
        >>> # Filter by location and salary
        >>> response = requests.get(
        ...     "/api/job-search/search",
        ...     params={
        ...         "location": "Remote",
        ...         "salary_min": 50000,
        ...         "limit": 20
        ...     }
        ... )
        >>> # Filter by skills
        >>> response = requests.get(
        ...     "/api/job-search/search",
        ...     params={
        ...         "skills": "Python, FastAPI, PostgreSQL",
        ...         "work_format": "remote"
        ...     }
        ... )
    """
    start_time = time.time()

    try:
        logger.info(
            f"GET search - query: {query}, location: {location}, "
            f"salary: {salary_min}-{salary_max}, work_format: {work_format}"
        )

        # Build base query - only active vacancies
        query_obj = select(JobVacancy).where(JobVacancy.is_active == True)

        # Apply full-text search on query
        if query:
            search_term = f"%{query}%"
            query_obj = query_obj.where(
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.description.ilike(search_term),
                )
            )

        # Apply filters
        filters_applied = {}

        # Location filter
        if location:
            location_term = f"%{location}%"
            query_obj = query_obj.where(JobVacancy.location.ilike(location_term))
            filters_applied["location"] = location

        # Salary range filter
        if salary_min is not None:
            query_obj = query_obj.where(
                or_(
                    JobVacancy.salary_min.is_(None),
                    JobVacancy.salary_min >= salary_min
                )
            )
            filters_applied["salary_min"] = salary_min

        if salary_max is not None:
            query_obj = query_obj.where(
                or_(
                    JobVacancy.salary_max.is_(None),
                    JobVacancy.salary_max <= salary_max
                )
            )
            filters_applied["salary_max"] = salary_max

        # Work format filter
        if work_format:
            query_obj = query_obj.where(JobVacancy.work_format == work_format.lower())
            filters_applied["work_format"] = work_format

        # Employment type filter
        if employment_type:
            query_obj = query_obj.where(JobVacancy.employment_type == employment_type.lower())
            filters_applied["employment_type"] = employment_type

        # Industry filter
        if industry:
            industry_term = f"%{industry}%"
            query_obj = query_obj.where(JobVacancy.industry.ilike(industry_term))
            filters_applied["industry"] = industry

        # Skills filter
        if skills:
            skills_list = [s.strip() for s in skills.split(",")]
            if skills_list:
                skill_conditions = []
                for skill in skills_list:
                    skill_conditions.append(JobVacancy.required_skills.contains([skill]))
                if skill_conditions:
                    query_obj = query_obj.where(or_(*skill_conditions))
                filters_applied["skills"] = skills_list

        # Get total count
        count_query = select(func.count()).select_from(query_obj.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one() or 0

        # Apply sorting
        sort_by_lower = sort_by.lower()
        if sort_by_lower == "salary_asc":
            query_obj = query_obj.order_by(JobVacancy.salary_min.asc().nulls_last())
        elif sort_by_lower == "salary_desc":
            query_obj = query_obj.order_by(JobVacancy.salary_min.desc().nulls_last())
        elif sort_by_lower == "relevance":
            query_obj = query_obj.order_by(JobVacancy.created_at.desc())
        else:  # default: date
            query_obj = query_obj.order_by(JobVacancy.created_at.desc())

        # Apply pagination
        query_obj = query_obj.offset(skip).limit(limit)
        result = await db.execute(query_obj)
        vacancies = result.scalars().all()

        # Convert to response format
        jobs_list = [_vacancy_to_dict(v) for v in vacancies]

        execution_time = time.time() - start_time

        logger.info(
            f"GET search completed: {total} total, "
            f"returned {len(jobs_list)} results"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "jobs": jobs_list,
                "query": query or "",
                "filters_applied": filters_applied,
                "execution_time_seconds": execution_time,
                "skip": skip,
                "limit": limit,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during job search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e
