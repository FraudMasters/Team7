"""
Job Vacancy API endpoints with database integration and matching functionality.

This module provides endpoints for managing job vacancies in the database
and matching resumes against all available vacancies.
"""
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_vacancy import JobVacancy
from analyzers import EnhancedSkillMatcher
from analyzers.hf_skill_extractor import extract_resume_keywords, extract_resume_entities

logger = logging.getLogger(__name__)

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
    salary_min: Optional[int] = Field(None, ge=0, description="Min salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Max salary")
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
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class MatchResult(BaseModel):
    """Match result for a single vacancy."""

    vacancy_id: str = Field(..., description="Vacancy ID")
    vacancy_title: str = Field(..., description="Job title")
    match_percentage: float = Field(..., description="Match percentage (0-100)")
    matched_skills: List[str] = Field(..., description="Matched skills")
    missing_skills: List[str] = Field(..., description="Missing skills")
    additional_matched: List[str] = Field(default=[], description="Matched additional skills")
    experience_match: bool = Field(default=False, description="Experience requirement met")


class AllVacanciesMatchResponse(BaseModel):
    """Response model for matching against all vacancies."""

    resume_id: str = Field(..., description="Resume ID")
    total_vacancies: int = Field(..., description="Total vacancies checked")
    matches: List[MatchResult] = Field(..., description="List of match results")
    best_match: Optional[MatchResult] = Field(None, description="Best matching vacancy")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


def _extract_locale(request: Optional[Request]) -> str:
    """Extract Accept-Language header from request."""
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


def model_to_dict(vacancy: JobVacancy) -> dict:
    """Convert JobVacancy model to dictionary."""
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
        "created_at": vacancy.created_at.isoformat() if vacancy.created_at else "",
        "updated_at": vacancy.updated_at.isoformat() if vacancy.updated_at else "",
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
    Create a new job vacancy in the database.

    This endpoint allows recruiters to create a new job vacancy request
    that defines the candidate profile they're looking for.

    Args:
        request: FastAPI request object
        vacancy: Vacancy data
        db: Database session

    Returns:
        JSON response with created vacancy

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails
    """
    try:
        # Create new vacancy
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
        )

        db.add(new_vacancy)
        await db.commit()
        await db.refresh(new_vacancy)

        logger.info(f"Created vacancy: {new_vacancy.id} - {new_vacancy.title}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=model_to_dict(new_vacancy),
        )

    except Exception as e:
        logger.error(f"Error creating vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vacancy: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=List[VacancyResponse],
    tags=["Vacancies"],
)
async def list_vacancies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all job vacancies from the database.

    Returns a paginated list of all job vacancies stored in the database.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of vacancies
    """
    try:
        # Query vacancies
        result = await db.execute(
            select(JobVacancy)
            .order_by(JobVacancy.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        vacancies = result.scalars().all()

        # Convert to list of dicts
        vacancies_list = [model_to_dict(v) for v in vacancies]

        logger.info(f"Listed {len(vacancies_list)} vacancies")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=vacancies_list,
        )

    except Exception as e:
        logger.error(f"Error listing vacancies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vacancies: {str(e)}",
        ) from e


@router.get(
    "/{vacancy_id}",
    response_model=VacancyResponse,
    tags=["Vacancies"],
)
async def get_vacancy(
    request: Request,
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a specific job vacancy by ID.

    Args:
        request: FastAPI request object
        vacancy_id: Vacancy UUID
        db: Database session

    Returns:
        JSON response with vacancy details

    Raises:
        HTTPException(404): If vacancy not found
    """
    try:
        # Query vacancy
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        )
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy {vacancy_id} not found",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=model_to_dict(vacancy),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy {vacancy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vacancy: {str(e)}",
        ) from e


@router.put(
    "/{vacancy_id}",
    response_model=VacancyResponse,
    tags=["Vacancies"],
)
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
        vacancy_id: Vacancy UUID
        vacancy: Updated vacancy data
        db: Database session

    Returns:
        JSON response with updated vacancy

    Raises:
        HTTPException(404): If vacancy not found
    """
    try:
        # Query vacancy
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        )
        db_vacancy = result.scalar_one_or_none()

        if not db_vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy {vacancy_id} not found",
            )

        # Update fields
        if vacancy.title is not None:
            db_vacancy.title = vacancy.title
        if vacancy.description is not None:
            db_vacancy.description = vacancy.description
        if vacancy.required_skills is not None:
            db_vacancy.required_skills = vacancy.required_skills
        if vacancy.min_experience_months is not None:
            db_vacancy.min_experience_months = vacancy.min_experience_months
        if vacancy.additional_requirements is not None:
            db_vacancy.additional_requirements = vacancy.additional_requirements
        if vacancy.industry is not None:
            db_vacancy.industry = vacancy.industry
        if vacancy.work_format is not None:
            db_vacancy.work_format = vacancy.work_format
        if vacancy.location is not None:
            db_vacancy.location = vacancy.location
        if vacancy.salary_min is not None:
            db_vacancy.salary_min = vacancy.salary_min
        if vacancy.salary_max is not None:
            db_vacancy.salary_max = vacancy.salary_max
        if vacancy.english_level is not None:
            db_vacancy.english_level = vacancy.english_level
        if vacancy.employment_type is not None:
            db_vacancy.employment_type = vacancy.employment_type

        await db.commit()
        await db.refresh(db_vacancy)

        logger.info(f"Updated vacancy: {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=model_to_dict(db_vacancy),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vacancy {vacancy_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vacancy: {str(e)}",
        ) from e


@router.delete(
    "/{vacancy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Vacancies"],
)
async def delete_vacancy(
    request: Request,
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a job vacancy.

    Args:
        request: FastAPI request object
        vacancy_id: Vacancy UUID
        db: Database session

    Returns:
        Empty response on success

    Raises:
        HTTPException(404): If vacancy not found
    """
    try:
        # Query vacancy
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
        )
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy {vacancy_id} not found",
            )

        await db.delete(vacancy)
        await db.commit()

        logger.info(f"Deleted vacancy: {vacancy_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vacancy {vacancy_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vacancy: {str(e)}",
        ) from e


@router.post(
    "/match-all",
    response_model=AllVacanciesMatchResponse,
    tags=["Vacancies"],
)
async def match_resume_against_all_vacancies(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Match a resume against ALL job vacancies in the database.

    This endpoint extracts skills from a resume and compares them against all
    available job vacancies, returning a ranked list of matches.

    Args:
        request: FastAPI request object
        resume_id: Resume file ID (without extension)
        db: Database session

    Returns:
        JSON response with all match results

    Raises:
        HTTPException(404): If resume file not found
        HTTPException(500): If processing fails

    Example:
        >>> POST /api/vacancies/match-all?resume_id=abc123
        {
            "resume_id": "abc123",
            "total_vacancies": 5,
            "matches": [
                {
                    "vacancy_id": "...",
                    "vacancy_title": "Senior Python Developer",
                    "match_percentage": 85.5,
                    "matched_skills": ["Python", "Django"],
                    "missing_skills": ["Kubernetes"],
                    ...
                },
                ...
            ],
            "best_match": {...},
            "processing_time_ms": 1234.56
        }
    """
    import time
    from pathlib import Path

    start_time = time.time()

    try:
        # Find resume file
        upload_dir = Path("data/uploads")
        resume_files = list(upload_dir.glob(f"{resume_id}.*"))

        if not resume_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file with ID '{resume_id}' not found",
            )

        file_path = resume_files[0]
        logger.info(f"Matching resume {resume_id} against all vacancies")

        # Extract text from resume
        if file_path.suffix == ".pdf":
            from services.data_extractor.extract import extract_text_from_pdf
            result = extract_text_from_pdf(str(file_path))
            resume_text = result.get("text", "")
        elif file_path.suffix == ".docx":
            from services.data_extractor.extract import extract_text_from_docx
            result = extract_text_from_docx(str(file_path))
            resume_text = result.get("text", "")
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

        # Get all vacancies from database
        result = await db.execute(select(JobVacancy))
        vacancies = result.scalars().all()

        if not vacancies:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "resume_id": resume_id,
                    "total_vacancies": 0,
                    "matches": [],
                    "best_match": None,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                },
            )

        # Match against each vacancy
        matcher = EnhancedSkillMatcher()
        matches = []

        for vacancy in vacancies:
            # Combine required and additional skills
            all_vacancy_skills = set(vacancy.required_skills or [])
            if vacancy.additional_requirements:
                all_vacancy_skills.update(vacancy.additional_requirements)

            # Calculate match
            match_result = matcher.calculate_match_score(
                resume_skills=resume_skills,
                vacancy_skills=list(all_vacancy_skills),
                required_skills=vacancy.required_skills or [],
            )

            # Check experience match
            experience_match = True
            if vacancy.min_experience_months:
                # This would require experience data from resume analysis
                # For now, assume match
                experience_match = True

            # Determine additional skills matched
            required_set = set(vacancy.required_skills or [])
            additional_skills = vacancy.additional_requirements or []
            additional_matched = [
                skill for skill in additional_skills
                if skill in resume_skills and skill not in required_set
            ]

            matches.append({
                "vacancy_id": str(vacancy.id),
                "vacancy_title": vacancy.title,
                "match_percentage": match_result["match_percentage"],
                "matched_skills": match_result["matched_skills"],
                "missing_skills": match_result["missing_skills"],
                "additional_matched": additional_matched,
                "experience_match": experience_match,
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
