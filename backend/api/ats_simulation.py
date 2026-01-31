"""
ATS (Applicant Tracking System) Simulation endpoints.

This module provides endpoints for LLM-based ATS evaluation of resumes
against job postings, similar to how commercial ATS systems work.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from analyzers import (
    evaluate_resume_ats,
    get_ats_simulator,
    get_simple_ats_checker,
)
from models import Resume, ResumeAnalysis, JobVacancy, ATSResult

logger = logging.getLogger(__name__)

router = APIRouter()


class ATSEvaluationRequest(BaseModel):
    """Request model for ATS evaluation."""

    resume_id: str = Field(..., description="Resume UUID or ID to evaluate")
    vacancy_id: str = Field(..., description="JobVacancy UUID to evaluate against")
    use_llm: bool = Field(
        default=True,
        description="Use LLM-based evaluation if available (falls back to rule-based if not)",
    )


class ATSEvaluationResponse(BaseModel):
    """Response model for ATS evaluation."""

    resume_id: str = Field(..., description="Resume identifier")
    vacancy_id: str = Field(..., description="Vacancy identifier")
    passed: bool = Field(..., description="Whether resume passes ATS threshold")
    overall_score: float = Field(..., description="Combined ATS score (0-1)")
    keyword_score: float = Field(..., description="Keyword matching score (0-1)")
    experience_score: float = Field(..., description="Experience relevance score (0-1)")
    education_score: float = Field(..., description="Education match score (0-1)")
    fit_score: float = Field(..., description="Overall fit assessment (0-1)")
    looks_professional: bool = Field(..., description="Professional format check")
    disqualified: bool = Field(..., description="Has disqualifying issues")
    visual_issues: List[str] = Field(default_factory=list, description="Visual/formatting issues")
    ats_issues: List[str] = Field(default_factory=list, description="ATS-specific concerns")
    missing_keywords: List[str] = Field(default_factory=list, description="Missing important keywords")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    feedback: str = Field(..., description="Detailed feedback")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    processing_time_ms: float = Field(..., description="Processing time")


class BatchATSEvaluationRequest(BaseModel):
    """Request model for batch ATS evaluation."""

    vacancy_id: str = Field(..., description="JobVacancy UUID to evaluate against")
    resume_ids: List[str] = Field(..., description="List of resume IDs to evaluate")
    use_llm: bool = Field(
        default=True,
        description="Use LLM-based evaluation if available",
    )


@router.post(
    "/evaluate",
    response_model=ATSEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def evaluate_ats_endpoint(
    request: Request,
    evaluation_request: ATSEvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Evaluate a resume against a job posting using ATS simulation.

    This endpoint performs comprehensive ATS evaluation using either:
    1. LLM-based evaluation (if API key is configured) - more accurate
    2. Rule-based evaluation (fallback) - faster but less sophisticated

    The ATS evaluation scores:
    - **keyword_score**: How well resume contains required skills
    - **experience_score**: Relevance and sufficiency of experience
    - **education_score**: How well education matches requirements
    - **fit_score**: Overall assessment of candidate fit

    Args:
        request: FastAPI request object
        evaluation_request: ATS evaluation request with resume_id and vacancy_id
        db: Database session

    Returns:
        JSON response with comprehensive ATS evaluation results

    Raises:
        HTTPException(404): If resume or vacancy not found
        HTTPException(500): If evaluation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "xyz-789-uvw",
        ...     "use_llm": True
        ... }
        >>> response = requests.post("/api/ats/evaluate", json=data)
        >>> response.json()
        {
            "resume_id": "abc-123-def",
            "vacancy_id": "xyz-789-uvw",
            "passed": True,
            "overall_score": 0.75,
            "keyword_score": 0.8,
            "experience_score": 0.7,
            "education_score": 0.8,
            "fit_score": 0.7,
            "looks_professional": True,
            "disqualified": False,
            "visual_issues": [],
            "ats_issues": [],
            "missing_keywords": ["Docker"],
            "suggestions": ["Add Docker experience"],
            "feedback": "Strong candidate with relevant experience...",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "processing_time_ms": 1250.5
        }
    """
    start_time = time.time()

    try:
        # Parse resume_id
        try:
            resume_uuid = UUID(evaluation_request.resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume_id format: {evaluation_request.resume_id}",
            )

        # Parse vacancy_id
        try:
            vacancy_uuid = UUID(evaluation_request.vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vacancy_id format: {evaluation_request.vacancy_id}",
            )

        # Fetch resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {evaluation_request.resume_id}",
            )

        # Fetch vacancy
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {evaluation_request.vacancy_id}",
            )

        # Get resume text
        resume_text = resume.raw_text
        if not resume_text:
            # Try to get from ResumeAnalysis
            analysis_query = select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume_uuid
            )
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()
            if analysis:
                resume_text = analysis.raw_text or ""

        if not resume_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text is empty or not available",
            )

        # Get candidate skills if available
        candidate_skills = []
        if resume.status == "COMPLETED":
            analysis_query = select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume_uuid
            )
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()
            if analysis and analysis.skills:
                candidate_skills = analysis.skills

        # Perform ATS evaluation
        logger.info(
            f"Evaluating ATS for resume {evaluation_request.resume_id} "
            f"against vacancy {evaluation_request.vacancy_id}"
        )

        ats_result = await evaluate_resume_ats(
            resume_text=resume_text,
            job_title=vacancy.title,
            job_description=vacancy.description or "",
            required_skills=vacancy.required_skills or [],
            use_llm=evaluation_request.use_llm,
        )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Save result to database
        try:
            # Check if result already exists
            existing_result_query = select(ATSResult).where(
                ATSResult.resume_id == resume_uuid,
                ATSResult.vacancy_id == vacancy_uuid
            )
            existing_result_obj = await db.execute(existing_result_query)
            existing_result = existing_result_obj.scalar_one_or_none()

            if existing_result:
                # Update existing
                existing_result.passed = ats_result.passed
                existing_result.overall_score = ats_result.overall_score
                existing_result.keyword_score = ats_result.keyword_score
                existing_result.experience_score = ats_result.experience_score
                existing_result.education_score = ats_result.education_score
                existing_result.fit_score = ats_result.fit_score
                existing_result.looks_professional = ats_result.looks_professional
                existing_result.disqualified = ats_result.disqualified
                existing_result.visual_issues = ats_result.visual_issues
                existing_result.ats_issues = ats_result.ats_issues
                existing_result.missing_keywords = ats_result.missing_keywords
                existing_result.suggestions = ats_result.suggestions
                existing_result.feedback = ats_result.feedback
                existing_result.provider = ats_result.provider
                existing_result.model = ats_result.model
                logger.info(f"Updated existing ATS result: {existing_result.id}")
            else:
                # Create new
                new_ats_result = ATSResult(
                    resume_id=resume_uuid,
                    vacancy_id=vacancy_uuid,
                    passed=ats_result.passed,
                    overall_score=ats_result.overall_score,
                    keyword_score=ats_result.keyword_score,
                    experience_score=ats_result.experience_score,
                    education_score=ats_result.education_score,
                    fit_score=ats_result.fit_score,
                    looks_professional=ats_result.looks_professional,
                    disqualified=ats_result.disqualified,
                    visual_issues=ats_result.visual_issues,
                    ats_issues=ats_result.ats_issues,
                    missing_keywords=ats_result.missing_keywords,
                    suggestions=ats_result.suggestions,
                    feedback=ats_result.feedback,
                    provider=ats_result.provider,
                    model=ats_result.model,
                )
                db.add(new_ats_result)
                logger.info(f"Created new ATS result for resume {resume_uuid}")

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save ATS result: {e}")
            await db.rollback()

        # Build response
        response_data = {
            "resume_id": evaluation_request.resume_id,
            "vacancy_id": evaluation_request.vacancy_id,
            **ats_result.to_dict(),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"ATS evaluation completed: passed={ats_result.passed}, "
            f"score={ats_result.overall_score:.2f}, "
            f"provider={ats_result.provider}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ATS evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS evaluation failed: {str(e)}",
        ) from e


@router.get(
    "/results/{resume_id}/{vacancy_id}",
    response_model=ATSEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def get_ats_result(
    resume_id: str,
    vacancy_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get cached ATS evaluation result for a resume-vacancy pair.

    Args:
        resume_id: Resume UUID
        vacancy_id: JobVacancy UUID
        db: Database session

    Returns:
        Cached ATS evaluation result

    Raises:
        HTTPException(404): If result not found

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/ats/results/abc-123-def/xyz-789-uvw"
        ... )
        >>> response.json()
        {
            "resume_id": "abc-123-def",
            "vacancy_id": "xyz-789-uvw",
            "passed": True,
            "overall_score": 0.75,
            ...
        }
    """
    try:
        resume_uuid = UUID(resume_id)
        vacancy_uuid = UUID(vacancy_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format",
        )

    # Query for existing result
    result_query = select(ATSResult).where(
        ATSResult.resume_id == resume_uuid,
        ATSResult.vacancy_id == vacancy_uuid
    )
    result_obj = await db.execute(result_query)
    result = result_obj.scalar_one_or_none()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ATS result not found for resume {resume_id} and vacancy {vacancy_id}",
        )

    # Build response
    response_data = {
        "resume_id": resume_id,
        "vacancy_id": vacancy_id,
        "passed": result.passed,
        "overall_score": result.overall_score,
        "keyword_score": result.keyword_score or 0.0,
        "experience_score": result.experience_score or 0.0,
        "education_score": result.education_score or 0.0,
        "fit_score": result.fit_score or 0.0,
        "looks_professional": result.looks_professional,
        "disqualified": result.disqualified,
        "visual_issues": result.visual_issues or [],
        "ats_issues": result.ats_issues or [],
        "missing_keywords": result.missing_keywords or [],
        "suggestions": result.suggestions or [],
        "feedback": result.feedback or "",
        "provider": result.provider or "unknown",
        "model": result.model or "unknown",
        "processing_time_ms": 0.0,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data,
    )


@router.post(
    "/batch-evaluate",
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def batch_evaluate_ats(
    request: BatchATSEvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Evaluate multiple resumes against a single job posting.

    Args:
        request: Batch evaluation request with vacancy_id and list of resume_ids
        db: Database session

    Returns:
        JSON response with list of ATS evaluation results

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(500): If evaluation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "xyz-789-uvw",
        ...     "resume_ids": ["abc-123", "def-456", "ghi-789"],
        ...     "use_llm": True
        ... }
        >>> response = requests.post("/api/ats/batch-evaluate", json=data)
        >>> response.json()
        {
            "vacancy_id": "xyz-789-uvw",
            "results": [
                {"resume_id": "abc-123", "passed": True, "overall_score": 0.75, ...},
                {"resume_id": "def-456", "passed": False, "overall_score": 0.45, ...},
                {"resume_id": "ghi-789", "passed": True, "overall_score": 0.85, ...}
            ],
            "total_count": 3,
            "passed_count": 2,
            "processing_time_ms": 3500.5
        }
    """
    start_time = time.time()

    try:
        # Parse vacancy_id
        try:
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vacancy_id format: {request.vacancy_id}",
            )

        # Fetch vacancy
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {request.vacancy_id}",
            )

        logger.info(f"Batch ATS evaluation for {len(request.resume_ids)} resumes against vacancy {request.vacancy_id}")

        # Check which LLM method to use
        simulator = get_ats_simulator() if request.use_llm else None
        checker = get_simple_ats_checker() if not simulator else None

        if not simulator and not checker:
            # Both unavailable - return error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM API not configured and rule-based checker unavailable",
            )

        results = []
        passed_count = 0

        # Get resume data for all resumes
        resume_uuids = []
        for resume_id in request.resume_ids:
            try:
                resume_uuid = UUID(resume_id)
                resume_uuids.append(resume_id)
            except ValueError:
                continue

        # Fetch all resumes
        resumes_query = select(Resume).where(
            Resume.id.in_(resume_uuids)
        )
        resumes_result = await db.execute(resumes_query)
        resumes = resumes_result.scalars().all()

        # Create resume lookup
        resume_lookup = {str(r.id): r for r in resumes}

        # Evaluate each resume
        for resume_id in request.resume_ids:
            resume = resume_lookup.get(resume_id)
            if not resume:
                # Resume not found, add placeholder result
                results.append({
                    "resume_id": resume_id,
                    "error": "Resume not found",
                })
                continue

            # Get resume text
            resume_text = resume.raw_text or ""

            # Try to get from analysis if empty
            if not resume_text:
                analysis_query = select(ResumeAnalysis).where(
                    ResumeAnalysis.resume_id == UUID(resume_id)
                )
                analysis_result = await db.execute(analysis_query)
                analysis = analysis_result.scalar_one_or_none()
                if analysis:
                    resume_text = analysis.raw_text or ""

            if not resume_text:
                results.append({
                    "resume_id": resume_id,
                    "error": "Resume text not available",
                })
                continue

            # Perform evaluation
            try:
                if simulator:
                    ats_result = await simulator.evaluate_ats(
                        resume_text=resume_text,
                        job_title=vacancy.title,
                        job_description=vacancy.description or "",
                        required_skills=vacancy.required_skills or [],
                    )
                else:
                    ats_result = checker.check_ats(
                        resume_text=resume_text,
                        job_title=vacancy.title,
                        job_description=vacancy.description or "",
                        required_skills=vacancy.required_skills or [],
                    )

                if ats_result.passed:
                    passed_count += 1

                results.append({
                    "resume_id": resume_id,
                    **ats_result.to_dict(),
                })

            except Exception as e:
                logger.error(f"Error evaluating resume {resume_id}: {e}")
                results.append({
                    "resume_id": resume_id,
                    "error": str(e),
                })

        processing_time_ms = (time.time() - start_time) * 1000

        # Sort by overall score descending
        for r in results:
            if "error" not in r:
                r["overall_score"] = round(r.get("overall_score", 0), 4)
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        response_data = {
            "vacancy_id": request.vacancy_id,
            "results": results,
            "total_count": len(results),
            "passed_count": passed_count,
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Batch ATS evaluation completed: {passed_count}/{len(results)} passed, "
            f"time={processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch ATS evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ATS evaluation failed: {str(e)}",
        ) from e


@router.get(
    "/config",
    tags=["ATS Simulation"],
)
async def get_ats_config() -> JSONResponse:
    """
    Get current ATS simulation configuration.

    Returns information about:
    - Available LLM providers
    - Configured provider
    - Default model
    - ATS threshold settings

    Examples:
        >>> import requests
        >>> response = requests.get("/api/ats/config")
        >>> response.json()
        {
            "llm_configured": true,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "threshold": 0.6,
            "weights": {
                "keyword": 0.3,
                "experience": 0.3,
                "education": 0.2,
                "fit": 0.2
            }
        }
    """
    from config import get_settings

    settings = get_settings()
    simulator = get_ats_simulator()

    response_data = {
        "llm_configured": simulator is not None,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "threshold": settings.ats_threshold,
        "weights": {
            "keyword": settings.ats_keyword_weight,
            "experience": settings.ats_experience_weight,
            "education": settings.ats_education_weight,
            "fit": settings.ats_fit_weight,
        },
        "visual_check_enabled": settings.ats_visual_check_enabled,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data,
    )
