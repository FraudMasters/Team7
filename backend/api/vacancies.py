"""
Job Vacancy API endpoints for creating and managing job requisitions.

This module provides endpoints for recruiters to create, view, update,
and delete job vacancy requests that define the candidate profile they're looking for.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import time
from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import analyzers for matching
from analyzers import (
    extract_resume_entities,
    EnhancedSkillMatcher,
)
from database import get_db
from models.job_vacancy import JobVacancy
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# Request/Response Models
class VacancyCreateRequest(BaseModel):
    """Request model for creating a new job vacancy."""

    title: str = Field(..., min_length=3, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Job description and responsibilities")
    required_skills: list[str] = Field(..., min_items=1, description="Required technical skills")
    min_experience_months: Optional[int] = Field(None, ge=0, description="Minimum experience in months")
    additional_requirements: Optional[list[str]] = Field(default_factory=list, description="Preferred skills")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    work_format: Optional[str] = Field(None, max_length=50, description="Work format: remote, office, hybrid")
    location: Optional[str] = Field(None, max_length=255, description="Job location")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    english_level: Optional[str] = Field(None, max_length=50, description="Required English level")
    employment_type: Optional[str] = Field(None, max_length=50, description="Employment type: full-time, part-time, contract")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    source: Optional[str] = Field("manual", max_length=50, description="Source of vacancy")


class VacancyUpdateRequest(BaseModel):
    """Request model for updating a job vacancy."""

    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Job title")
    description: Optional[str] = Field(None, min_length=10, description="Job description")
    required_skills: Optional[list[str]] = Field(None, min_items=1, description="Required technical skills")
    min_experience_months: Optional[int] = Field(None, ge=0, description="Minimum experience in months")
    additional_requirements: Optional[list[str]] = Field(None, description="Preferred skills")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    work_format: Optional[str] = Field(None, max_length=50, description="Work format")
    location: Optional[str] = Field(None, max_length=255, description="Job location")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    english_level: Optional[str] = Field(None, max_length=50, description="English level")
    employment_type: Optional[str] = Field(None, max_length=50, description="Employment type")


class VacancyResponse(BaseModel):
    """Response model for job vacancy."""

    id: str = Field(..., description="Vacancy ID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    required_skills: list[str] = Field(..., description="Required skills")
    min_experience_months: Optional[int] = Field(None, description="Minimum experience")
    additional_requirements: list[str] = Field(..., description="Additional skills")
    industry: Optional[str] = Field(None, description="Industry")
    work_format: Optional[str] = Field(None, description="Work format")
    location: Optional[str] = Field(None, description="Location")
    salary_min: Optional[int] = Field(None, description="Min salary")
    salary_max: Optional[int] = Field(None, description="Max salary")
    english_level: Optional[str] = Field(None, description="English level")
    employment_type: Optional[str] = Field(None, description="Employment type")
    external_id: Optional[str] = Field(None, description="External ID")
    source: Optional[str] = Field(None, description="Source")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


<<<<<<< HEAD
class VacancyListResponse(BaseModel):
    """Response model for listing vacancies."""

    total: int = Field(..., description="Total number of vacancies")
    vacancies: list[VacancyResponse] = Field(..., description="List of vacancies")
=======
class VacancySearchRequest(BaseModel):
    """Request model for vacancy search."""

    query: Optional[str] = Field(None, description="Search query with boolean operators (AND, OR, NOT)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for search")
    skip: int = Field(0, ge=0, description="Number of results to skip (pagination)")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of results to return")
    sort_by: str = Field("date", description="Sort field: date, title, or salary")


class VacancySearchResponse(BaseModel):
    """Response model for vacancy search."""

    total: int = Field(..., description="Total number of matching vacancies")
    vacancies: List[Dict[str, Any]] = Field(..., description="List of vacancy results")
    query: str = Field(..., description="Search query that was executed")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    execution_time_seconds: float = Field(..., description="Time taken to execute search")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum number of results returned")
>>>>>>> origin/master


def _vacancy_to_response(vacancy: JobVacancy) -> dict:
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
        "external_id": vacancy.external_id,
        "source": vacancy.source,
        "created_at": vacancy.created_at.isoformat() if vacancy.created_at else None,
        "updated_at": vacancy.updated_at.isoformat() if vacancy.updated_at else None,
    }


@router.post(
    "/",
    response_model=VacancyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Vacancies"],
)
async def create_vacancy(
    request: Request,
    vacancy: VacancyCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new job vacancy.

    This endpoint allows recruiters to create a new job vacancy request
    that defines the candidate profile they're looking for.

    Args:
        request: FastAPI request object
        vacancy: Vacancy data from request body
        db: Database session

    Returns:
        JSON response with created vacancy details

    Example:
        >>> vacancy_data = {
        ...     "title": "Senior Java Developer",
        ...     "description": "We are looking for...",
        ...     "required_skills": ["Java", "Spring", "PostgreSQL"],
        ...     "min_experience_months": 36
        ... }
        >>> response = requests.post("/api/vacancies/", json=vacancy_data)
    """
    try:
        # Create new JobVacancy instance
        new_vacancy = JobVacancy(
            title=vacancy.title,
            description=vacancy.description,
            required_skills=vacancy.required_skills,
            min_experience_months=vacancy.min_experience_months,
            additional_requirements=vacancy.additional_requirements or [],
            industry=vacancy.industry,
            work_format=vacancy.work_format,
            location=vacancy.location,
            salary_min=vacancy.salary_min,
            salary_max=vacancy.salary_max,
            english_level=vacancy.english_level,
            employment_type=vacancy.employment_type,
            external_id=vacancy.external_id,
            source=vacancy.source,
        )

        db.add(new_vacancy)
        await db.commit()
        await db.refresh(new_vacancy)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.VACANCY_CREATED,
            entity_type="vacancy",
            entity_id=new_vacancy.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value=_vacancy_to_response(new_vacancy),
        )

        logger.info(f"Created vacancy: {new_vacancy.id} - {new_vacancy.title}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_vacancy_to_response(new_vacancy),
        )

    except Exception as e:
        logger.error(f"Error creating vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vacancy: {str(e)}",
        ) from e


@router.get("/", response_model=VacancyListResponse, tags=["Vacancies"])
async def list_vacancies(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all job vacancies.

    Returns a paginated list of all job vacancies.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of vacancies

    Example:
        >>> response = requests.get("/api/vacancies/?limit=10")
        >>> vacancies = response.json()
    """
    try:
        logger.info(f"Listing vacancies - skip: {skip}, limit: {limit}")

        # Get total count
        count_query = select(func.count()).select_from(JobVacancy)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Query vacancies from database with pagination
        query = select(JobVacancy).order_by(JobVacancy.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        # Convert to response format
        vacancies_list = [_vacancy_to_response(v) for v in vacancies]

        logger.info(f"Retrieved {len(vacancies_list)} vacancies (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "vacancies": vacancies_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing vacancies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vacancies: {str(e)}",
        ) from e


@router.post(
    "/search",
    response_model=VacancySearchResponse,
    tags=["Vacancies"],
)
async def search_vacancies(
    request: Request,
    search_data: VacancySearchRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Search for vacancies with advanced filters.

    This endpoint provides powerful vacancy search capabilities including:
    - Full-text search with boolean operators (AND, OR, NOT)
    - Multi-field filtering: work_format, location, salary, employment_type, industry, etc.
    - Flexible sorting by date, title, or salary

    Examples of boolean search queries:
    - "Python AND Django" - Vacancies with both Python and Django
    - "Python OR Django" - Vacancies with either Python or Django
    - "Python NOT Flask" - Vacancies with Python but not Flask
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
        >>> # Search with filters
        >>> data = {
        ...     "filters": {
        ...         "work_format": "remote",
        ...         "location": "New York",
        ...         "salary_min": 50000,
        ...         "salary_max": 100000,
        ...         "employment_type": "full-time"
        ...     },
        ...     "limit": 10
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/search",
        ...     json=data
        ... )
        >>> # Search with query
        >>> data = {
        ...     "query": "Python AND Django",
        ...     "sort_by": "date"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/search",
        ...     json=data
        ... )
    """
    start_time = time.time()

    try:
        logger.info(
            f"Searching vacancies - query: {search_data.query}, "
            f"filters: {search_data.filters}, skip: {search_data.skip}, "
            f"limit: {search_data.limit}, sort_by: {search_data.sort_by}"
        )

        # Build base query
        query = select(JobVacancy)

        # Apply full-text search if query is provided
        if search_data.query:
            # Simple boolean search implementation
            # For more advanced search, consider using PostgreSQL full-text search
            search_terms = search_data.query.split()

            # Build OR conditions for title and description
            or_conditions = []
            for term in search_terms:
                # Skip boolean operators
                if term.upper() in ["AND", "OR", "NOT"]:
                    continue

                # Case-insensitive search in title and description
                or_conditions.append(JobVacancy.title.ilike(f"%{term}%"))
                or_conditions.append(JobVacancy.description.ilike(f"%{term}%"))

            if or_conditions:
                query = query.where(or_(*or_conditions))

        # Apply filters if provided
        filters_applied = {}
        if search_data.filters:
            # Work format filter
            if "work_format" in search_data.filters:
                work_format = search_data.filters["work_format"]
                if work_format:
                    query = query.where(JobVacancy.work_format == work_format)
                    filters_applied["work_format"] = work_format

            # Location filter
            if "location" in search_data.filters:
                location = search_data.filters["location"]
                if location:
                    query = query.where(JobVacancy.location.ilike(f"%{location}%"))
                    filters_applied["location"] = location

            # Salary range filter
            if "salary_min" in search_data.filters:
                salary_min = search_data.filters["salary_min"]
                if salary_min is not None:
                    query = query.where(JobVacancy.salary_min >= salary_min)
                    filters_applied["salary_min"] = salary_min

            if "salary_max" in search_data.filters:
                salary_max = search_data.filters["salary_max"]
                if salary_max is not None:
                    query = query.where(JobVacancy.salary_max <= salary_max)
                    filters_applied["salary_max"] = salary_max

            # Employment type filter
            if "employment_type" in search_data.filters:
                employment_type = search_data.filters["employment_type"]
                if employment_type:
                    query = query.where(JobVacancy.employment_type == employment_type)
                    filters_applied["employment_type"] = employment_type

            # Industry filter
            if "industry" in search_data.filters:
                industry = search_data.filters["industry"]
                if industry:
                    query = query.where(JobVacancy.industry.ilike(f"%{industry}%"))
                    filters_applied["industry"] = industry

            # English level filter
            if "english_level" in search_data.filters:
                english_level = search_data.filters["english_level"]
                if english_level:
                    query = query.where(JobVacancy.english_level == english_level)
                    filters_applied["english_level"] = english_level

            # Minimum experience filter
            if "min_experience_months" in search_data.filters:
                min_exp = search_data.filters["min_experience_months"]
                if min_exp is not None:
                    query = query.where(JobVacancy.min_experience_months <= min_exp)
                    filters_applied["min_experience_months"] = min_exp

            # Source filter
            if "source" in search_data.filters:
                source = search_data.filters["source"]
                if source:
                    query = query.where(JobVacancy.source == source)
                    filters_applied["source"] = source

            # Skills filter (check if any required skill matches)
            if "skills" in search_data.filters:
                skills = search_data.filters["skills"]
                if skills and isinstance(skills, list):
                    # Check if any of the filter skills are in the vacancy's required_skills
                    for skill in skills:
                        query = query.where(JobVacancy.required_skills.contains([skill]))
                    filters_applied["skills"] = skills

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one() or 0

        # Apply sorting
        if search_data.sort_by == "title":
            query = query.order_by(JobVacancy.title.asc())
        elif search_data.sort_by == "salary":
            # Sort by average salary (min + max) / 2
            query = query.order_by(
                ((JobVacancy.salary_min + JobVacancy.salary_max) / 2).desc()
            )
        else:  # default: date
            query = query.order_by(JobVacancy.created_at.desc())

        # Apply pagination
        query = query.offset(search_data.skip).limit(search_data.limit)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        # Convert to response format
        vacancies_list = [_vacancy_to_response(v) for v in vacancies]

        execution_time = time.time() - start_time

        logger.info(
            f"Vacancy search completed: {total} total vacancies, "
            f"returned {len(vacancies_list)} results in "
            f"{execution_time:.3f}s"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "vacancies": vacancies_list,
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
        logger.error(f"Error during vacancy search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get(
    "/search",
    response_model=VacancySearchResponse,
    tags=["Vacancies"],
)
async def search_vacancies_get(
    request: Request,
    query: Optional[str] = Query(None, description="Search query with boolean operators"),
    work_format: Optional[str] = Query(None, description="Work format: remote, office, hybrid"),
    location: Optional[str] = Query(None, description="Job location"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    employment_type: Optional[str] = Query(None, description="Employment type: full-time, part-time, contract"),
    industry: Optional[str] = Query(None, description="Industry sector"),
    english_level: Optional[str] = Query(None, description="Required English level"),
    min_experience_months: Optional[int] = Query(None, ge=0, description="Minimum experience in months"),
    skills: Optional[str] = Query(None, description="Comma-separated list of required skills"),
    source: Optional[str] = Query(None, description="Source of vacancy"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of results"),
    sort_by: str = Query("date", description="Sort field: date, title, or salary"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Search for vacancies using GET request with query parameters.

    This is an alternative to the POST endpoint that uses query parameters
    instead of a JSON body. Useful for simple searches and browser-based queries.

    Args:
        request: FastAPI request object
        query: Search query with boolean operators
        work_format: Work format filter (remote, office, hybrid)
        location: Location filter
        salary_min: Minimum salary filter
        salary_max: Maximum salary filter
        employment_type: Employment type filter (full-time, part-time, contract)
        industry: Industry sector filter
        english_level: English level filter
        min_experience_months: Minimum experience in months
        skills: Comma-separated list of required skills
        source: Source filter
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return
        sort_by: Sort field (date, title, salary)
        db: Database session

    Returns:
        JSON response with search results and metadata

    Raises:
        HTTPException(400): If filter parameters are invalid
        HTTPException(500): If search execution fails

    Examples:
        >>> import requests
        >>> # Search by work format and employment type
        >>> response = requests.get(
        ...     "http://localhost:8000/api/vacancies/search",
        ...     params={"work_format": "remote", "employment_type": "full-time"}
        ... )
        >>> # Filter by salary range
        >>> response = requests.get(
        ...     "http://localhost:8000/api/vacancies/search",
        ...     params={"salary_min": 50000, "salary_max": 100000}
        ... )
        >>> # Filter by skills
        >>> response = requests.get(
        ...     "http://localhost:8000/api/vacancies/search",
        ...     params={"skills": "Python, Django, FastAPI"}
        ... )
    """
    start_time = time.time()

    try:
        logger.info(
            f"GET search vacancies - query: {query}, work_format: {work_format}, "
            f"employment_type: {employment_type}, location: {location}"
        )

        # Build base query
        sql_query = select(JobVacancy)

        # Apply full-text search if query is provided
        if query:
            # Simple boolean search implementation
            search_terms = query.split()

            # Build OR conditions for title and description
            or_conditions = []
            for term in search_terms:
                # Skip boolean operators
                if term.upper() in ["AND", "OR", "NOT"]:
                    continue

                # Case-insensitive search in title and description
                or_conditions.append(JobVacancy.title.ilike(f"%{term}%"))
                or_conditions.append(JobVacancy.description.ilike(f"%{term}%"))

            if or_conditions:
                sql_query = sql_query.where(or_(*or_conditions))

        # Build filters from query parameters
        filters_applied = {}

        # Work format filter
        if work_format:
            sql_query = sql_query.where(JobVacancy.work_format == work_format)
            filters_applied["work_format"] = work_format

        # Location filter
        if location:
            sql_query = sql_query.where(JobVacancy.location.ilike(f"%{location}%"))
            filters_applied["location"] = location

        # Salary range filter
        if salary_min is not None:
            sql_query = sql_query.where(JobVacancy.salary_min >= salary_min)
            filters_applied["salary_min"] = salary_min

        if salary_max is not None:
            sql_query = sql_query.where(JobVacancy.salary_max <= salary_max)
            filters_applied["salary_max"] = salary_max

        # Employment type filter
        if employment_type:
            sql_query = sql_query.where(JobVacancy.employment_type == employment_type)
            filters_applied["employment_type"] = employment_type

        # Industry filter
        if industry:
            sql_query = sql_query.where(JobVacancy.industry.ilike(f"%{industry}%"))
            filters_applied["industry"] = industry

        # English level filter
        if english_level:
            sql_query = sql_query.where(JobVacancy.english_level == english_level)
            filters_applied["english_level"] = english_level

        # Minimum experience filter
        if min_experience_months is not None:
            sql_query = sql_query.where(JobVacancy.min_experience_months <= min_experience_months)
            filters_applied["min_experience_months"] = min_experience_months

        # Source filter
        if source:
            sql_query = sql_query.where(JobVacancy.source == source)
            filters_applied["source"] = source

        # Skills filter (check if any required skill matches)
        if skills:
            skills_list = [s.strip() for s in skills.split(",")]
            if skills_list:
                # Check if any of the filter skills are in the vacancy's required_skills
                for skill in skills_list:
                    sql_query = sql_query.where(JobVacancy.required_skills.contains([skill]))
                filters_applied["skills"] = skills_list

        # Get total count
        count_query = select(func.count()).select_from(sql_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one() or 0

        # Apply sorting
        if sort_by == "title":
            sql_query = sql_query.order_by(JobVacancy.title.asc())
        elif sort_by == "salary":
            # Sort by average salary (min + max) / 2
            sql_query = sql_query.order_by(
                ((JobVacancy.salary_min + JobVacancy.salary_max) / 2).desc()
            )
        else:  # default: date
            sql_query = sql_query.order_by(JobVacancy.created_at.desc())

        # Apply pagination
        sql_query = sql_query.offset(skip).limit(limit)
        result = await db.execute(sql_query)
        vacancies = result.scalars().all()

        # Convert to response format
        vacancies_list = [_vacancy_to_response(v) for v in vacancies]

        execution_time = time.time() - start_time

        logger.info(
            f"GET search completed: {total} total vacancies, "
            f"returned {len(vacancies_list)} results in {execution_time:.3f}s"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "vacancies": vacancies_list,
                "query": query or "",
                "filters_applied": filters_applied,
                "execution_time_seconds": execution_time,
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
        logger.error(f"Error during vacancy search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get(
    "/match-all",
    tags=["Vacancies"],
)
async def match_resume_with_all_vacancies(
    request: Request,
    resume_id: str = Query(..., description="Resume file ID (without extension)"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Match a resume against ALL available vacancies.

    This endpoint extracts skills from a resume and compares them against all
    job vacancies in the system, returning a ranked list of matches by percentage.

    Args:
        request: FastAPI request object (for Accept-Language header)
        resume_id: Resume file ID (without extension)
        db: Database session

    Returns:
        JSON response with all match results sorted by match percentage

    Raises:
        HTTPException(404): If resume file not found
        HTTPException(500): If processing fails

    Example:
        >>> GET /api/vacancies/match-all?resume_id=abc123
        {
            "resume_id": "abc123",
            "total_vacancies": 5,
            "matches": [...],
            "best_match": {...}
        }
    """
    import time
    from pathlib import Path

    start_time = time.time()

    try:
        # First, try to find resume in database to get file_path
        from models.resume import Resume as ResumeModel

        resume_record = None
        file_path = None

        # Try to parse as UUID for database lookup
        try:
            resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
            resume_result = await db.execute(resume_query)
            resume_record = resume_result.scalar_one_or_none()
        except ValueError:
            # Not a valid UUID, skip database lookup
            pass

        # Determine file path
        if resume_record and resume_record.file_path:
            file_path = Path(resume_record.file_path)
        else:
            # Fallback: look for file by resume_id in uploads directory
            upload_dir = settings.upload_dir
            resume_files = list(upload_dir.glob(f"{resume_id}.*"))
            if resume_files:
                file_path = resume_files[0]

        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file with ID '{resume_id}' not found",
            )

        # Get all vacancies from database
        query = select(JobVacancy)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        logger.info(f"Matching resume {resume_id} against {len(vacancies)} vacancies")

        # Extract text from resume
        if file_path.suffix == ".pdf":
            from services.data_extractor.extract import extract_text_from_pdf
            result_text = extract_text_from_pdf(str(file_path))
            resume_text = result_text.get("text", "")
        elif file_path.suffix == ".docx":
            from services.data_extractor.extract import extract_text_from_docx
            result_text = extract_text_from_docx(str(file_path))
            resume_text = result_text.get("text", "")
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file_path.suffix}",
            )

        if not resume_text or len(resume_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from resume",
            )

        # Extract skills from resume
        entities_result = extract_resume_entities(resume_text)
        resume_skills = entities_result.get("skills") or entities_result.get("technical_skills") or []

        logger.info(f"Extracted {len(resume_skills)} skills from resume")

        # Match against all vacancies
        matcher = EnhancedSkillMatcher()
        matches = []

        for vacancy in vacancies:
            required_skills = vacancy.required_skills or []

            # Match skills using EnhancedSkillMatcher
            match_results = matcher.match_multiple(
                resume_skills=resume_skills,
                required_skills=required_skills,
            )

            # Extract matched and missing skills
            matched_skills = [
                skill for skill, result in match_results.items()
                if result.get("matched", False)
            ]
            missing_skills = [
                skill for skill, result in match_results.items()
                if not result.get("matched", False)
            ]

            # Calculate match percentage
            total_required = len(required_skills)
            match_percentage = (len(matched_skills) / total_required * 100) if total_required > 0 else 0.0

            # Determine additional skills matched
            additional_skills = vacancy.additional_requirements or []
            additional_matched = [
                skill for skill in additional_skills
                if skill in resume_skills and skill not in required_skills
            ]

            matches.append({
                "vacancy_id": str(vacancy.id),
                "vacancy_title": vacancy.title,
                "match_percentage": round(match_percentage, 1),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "additional_matched": additional_matched,
                "salary_min": vacancy.salary_min,
                "salary_max": vacancy.salary_max,
                "location": vacancy.location,
                "work_format": vacancy.work_format,
                "industry": vacancy.industry,
            })

        # Sort by match percentage descending
        matches.sort(key=lambda x: x["match_percentage"], reverse=True)

        # Get best match
        best_match = matches[0] if matches else None

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"Matched resume {resume_id} against {len(matches)} vacancies. "
            f"Best match: {best_match['match_percentage'] if best_match else 0}%"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "resume_id": resume_id,
                "total_vacancies": len(matches),
                "matches": matches,
                "best_match": best_match,
                "processing_time_ms": processing_time_ms,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume {resume_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match resume: {str(e)}",
        ) from e


@router.get(
    "/match/{vacancy_id}",
    tags=["Vacancies"],
)
async def match_resume_with_vacancy(
    request: Request,
    vacancy_id: str,
    resume_id: str = Query(..., description="Resume file ID"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Match a specific resume against a specific vacancy.

    This endpoint provides detailed comparison between a resume and a single job vacancy,
    including matched skills, missing skills, and match percentage.

    Args:
        request: FastAPI request object
        vacancy_id: UUID of the vacancy to match against
        resume_id: Resume file ID (without extension)
        db: Database session

    Returns:
        JSON response with detailed match results

    Raises:
        HTTPException(404): If resume file or vacancy not found

    Example:
        >>> GET /api/vacancies/match/123?vacancy_id=abc&resume_id=xyz
        {
            "resume_id": "xyz",
            "vacancy_id": "123",
            "vacancy_title": "Senior Python Developer",
            "match_percentage": 85.5,
            "matched_skills": ["Python", "Django"],
            "missing_skills": ["Kubernetes"],
            "additional_matched": ["Docker", "Git"],
            "overall_match": true
        }
    """
    import time
    from pathlib import Path

    start_time = time.time()

    try:
        # First, try to find resume in database to get file_path
        from models.resume import Resume as ResumeModel

        resume_record = None
        file_path = None

        # Try to parse as UUID for database lookup
        try:
            resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
            resume_result = await db.execute(resume_query)
            resume_record = resume_result.scalar_one_or_none()
        except ValueError:
            # Not a valid UUID, skip database lookup
            pass

        # Determine file path
        if resume_record and resume_record.file_path:
            file_path = Path(resume_record.file_path)
        else:
            # Fallback: look for file by resume_id in uploads directory
            upload_dir = settings.upload_dir
            resume_files = list(upload_dir.glob(f"{resume_id}.*"))
            if resume_files:
                file_path = resume_files[0]

        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file with ID '{resume_id}' not found",
            )

        # Get vacancy from database
        query = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy with ID '{vacancy_id}' not found",
            )

        logger.info(f"Matching resume {resume_id} against vacancy {vacancy_id}")

        # Extract text from resume
        if file_path.suffix == ".pdf":
            from services.data_extractor.extract import extract_text_from_pdf
            result_text = extract_text_from_pdf(str(file_path))
            resume_text = result_text.get("text", "")
        elif file_path.suffix == ".docx":
            from services.data_extractor.extract import extract_text_from_docx
            result_text = extract_text_from_docx(str(file_path))
            resume_text = result_text.get("text", "")
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file_path.suffix}",
            )

        if not resume_text or len(resume_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from resume",
            )

        # Extract skills from resume
        entities_result = extract_resume_entities(resume_text)
        resume_skills = entities_result.get("skills") or entities_result.get("technical_skills") or []

        logger.info(f"Extracted {len(resume_skills)} skills from resume")

        # Get vacancy skills
        required_skills = vacancy.required_skills or []

        # Match skills using EnhancedSkillMatcher
        matcher = EnhancedSkillMatcher()
        match_results = matcher.match_multiple(
            resume_skills=resume_skills,
            required_skills=required_skills,
        )

        # Build matched and missing skills with highlight info
        matched_skills = [
            {"skill": skill, "matched": True, "highlight": "green"}
            for skill, result in match_results.items()
            if result.get("matched", False)
        ]
        missing_skills = [
            {"skill": skill, "matched": False, "highlight": "red"}
            for skill, result in match_results.items()
            if not result.get("matched", False)
        ]

        # Calculate match percentage
        total_required = len(required_skills)
        match_percentage = (len(matched_skills) / total_required * 100) if total_required > 0 else 0.0

        # Determine additional skills matched
        additional_skills = vacancy.additional_requirements or []
        additional_matched = [
            skill for skill in additional_skills
            if skill in resume_skills and skill not in required_skills
        ]

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"Matched resume {resume_id} with vacancy {vacancy_id}: {match_percentage:.1f}%"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "vacancy_title": vacancy.title,
                "match_percentage": round(match_percentage, 1),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "additional_matched": additional_matched,
                "overall_match": match_percentage >= 50,
                "processing_time": processing_time_ms,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID format",
        )
    except Exception as e:
        logger.error(f"Error matching resume {resume_id} with vacancy {vacancy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match resume with vacancy: {str(e)}",
        ) from e


@router.get("/{vacancy_id}", response_model=VacancyResponse, tags=["Vacancies"])
async def get_vacancy(
    request: Request,
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a specific job vacancy by ID.

    Args:
        request: FastAPI request object
        vacancy_id: UUID of the vacancy
        db: Database session

    Returns:
        JSON response with vacancy details

    Raises:
        HTTPException(404): If vacancy not found

    Example:
        >>> response = requests.get("/api/vacancies/123")
        >>> vacancy = response.json()
    """
    try:
        # Query vacancy from database
        query = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found",
            )

        # Log audit event for viewing vacancy
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.VACANCY_VIEWED,
            entity_type="vacancy",
            entity_id=vacancy.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_vacancy_to_response(vacancy),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID format",
        )
    except Exception as e:
        logger.error(f"Error getting vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vacancy: {str(e)}",
        ) from e


@router.put("/{vacancy_id}", response_model=VacancyResponse, tags=["Vacancies"])
async def update_vacancy(
    request: Request,
    vacancy_id: str,
    vacancy: VacancyUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update a job vacancy.

    Args:
        request: FastAPI request object
        vacancy_id: UUID of the vacancy
        vacancy: Updated vacancy data
        db: Database session

    Returns:
        JSON response with updated vacancy details

    Raises:
        HTTPException(404): If vacancy not found

    Example:
        >>> update_data = {"title": "Lead Java Developer"}
        >>> response = requests.put("/api/vacancies/123", json=update_data)
    """
    try:
        # Query vacancy from database
        query = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        result = await db.execute(query)
        vacancy_obj = result.scalar_one_or_none()

        if not vacancy_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found",
            )

        # Capture before state for audit log
        before_state = _vacancy_to_response(vacancy_obj)

        # Update fields
        if vacancy.title is not None:
            vacancy_obj.title = vacancy.title
        if vacancy.description is not None:
            vacancy_obj.description = vacancy.description
        if vacancy.required_skills is not None:
            vacancy_obj.required_skills = vacancy.required_skills
        if vacancy.min_experience_months is not None:
            vacancy_obj.min_experience_months = vacancy.min_experience_months
        if vacancy.additional_requirements is not None:
            vacancy_obj.additional_requirements = vacancy.additional_requirements
        if vacancy.industry is not None:
            vacancy_obj.industry = vacancy.industry
        if vacancy.work_format is not None:
            vacancy_obj.work_format = vacancy.work_format
        if vacancy.location is not None:
            vacancy_obj.location = vacancy.location
        if vacancy.salary_min is not None:
            vacancy_obj.salary_min = vacancy.salary_min
        if vacancy.salary_max is not None:
            vacancy_obj.salary_max = vacancy.salary_max
        if vacancy.english_level is not None:
            vacancy_obj.english_level = vacancy.english_level
        if vacancy.employment_type is not None:
            vacancy_obj.employment_type = vacancy.employment_type

        # Update timestamp
        vacancy_obj.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(vacancy_obj)

        # Log audit event with before and after values
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.VACANCY_UPDATED,
            entity_type="vacancy",
            entity_id=vacancy_obj.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
            after_value=_vacancy_to_response(vacancy_obj),
        )

        logger.info(f"Updated vacancy: {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_vacancy_to_response(vacancy_obj),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID format",
        )
    except Exception as e:
        logger.error(f"Error updating vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vacancy: {str(e)}",
        ) from e


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Vacancies"])
async def delete_vacancy(
    request: Request,
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a job vacancy.

    Args:
        request: FastAPI request object
        vacancy_id: UUID of the vacancy to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If vacancy not found

    Example:
        >>> response = requests.delete("/api/vacancies/123")
        >>> response.status_code
        204
    """
    try:
        # Query vacancy from database
        query = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found",
            )

        # Capture before state for audit log
        before_state = _vacancy_to_response(vacancy)

        # Delete vacancy
        await db.delete(vacancy)
        await db.commit()

        # Log audit event with before value
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.VACANCY_DELETED,
            entity_type="vacancy",
            entity_id=vacancy.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
        )

        logger.info(f"Deleted vacancy: {vacancy_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy ID format",
        )
    except Exception as e:
        logger.error(f"Error deleting vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vacancy: {str(e)}",
        ) from e
