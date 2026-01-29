"""
Job Vacancy API endpoints for creating and managing job requisitions.

This module provides endpoints for recruiters to create, view, update,
and delete job vacancy requests that define the candidate profile they're looking for.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Import analyzers for matching
from analyzers import (
    extract_resume_entities,
    EnhancedSkillMatcher,
)
from database import get_db
from models.job_vacancy import JobVacancy

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
        >>> response = requests.post("http://localhost:8000/api/vacancies/", json=vacancy_data)
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


@router.get("/", response_model=list[VacancyResponse], tags=["Vacancies"])
async def list_vacancies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
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
        >>> response = requests.get("http://localhost:8000/api/vacancies/?limit=10")
        >>> vacancies = response.json()
    """
    try:
        # Query vacancies from database
        query = select(JobVacancy).order_by(JobVacancy.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        # Convert to response format
        vacancies_list = [_vacancy_to_response(v) for v in vacancies]

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
            upload_dir = Path("data/uploads")
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
            upload_dir = Path("data/uploads")
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
        >>> response = requests.get("http://localhost:8000/api/vacancies/123")
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
        >>> response = requests.put("http://localhost:8000/api/vacancies/123", json=update_data)
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
        >>> response = requests.delete("http://localhost:8000/api/vacancies/123")
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

        # Delete vacancy
        await db.delete(vacancy)
        await db.commit()

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
