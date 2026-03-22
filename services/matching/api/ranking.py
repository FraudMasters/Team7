"""
Эндпоинты ранжирования резюме для сортировки кандидатов по качеству совпадения.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для ранжирования резюме на основе их совпадения
с вакансиями, используя различные критерии, такие как процент совпадения навыков,
опыт и пользовательские веса.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.match_result import MatchResult

from analyzers import EnhancedSkillMatcher

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")


class RankingWeights(BaseModel):
    """Custom weights for ranking criteria."""

    skill_match_weight: float = Field(
        0.25, description="Weight for skill match percentage (0.0-1.0)", ge=0, le=1
    )
    experience_weight: float = Field(
        0.15, description="Weight for experience match (0.0-1.0)", ge=0, le=1
    )
    education_weight: float = Field(
        0.10, description="Weight for education match (0.0-1.0)", ge=0, le=1
    )
    location_weight: float = Field(
        0.05, description="Weight for location match (0.0-1.0)", ge=0, le=1
    )
    keyword_weight: float = Field(
        0.10, description="Weight for keyword matching (0.0-1.0)", ge=0, le=1
    )
    tfidf_weight: float = Field(
        0.10, description="Weight for TF-IDF similarity (0.0-1.0)", ge=0, le=1
    )
    vector_weight: float = Field(
        0.10, description="Weight for vector similarity (0.0-1.0)", ge=0, le=1
    )
    recency_weight: float = Field(
        0.05, description="Weight for resume recency (0.0-1.0)", ge=0, le=1
    )
    culture_fit_weight: float = Field(
        0.05, description="Weight for culture fit (0.0-1.0)", ge=0, le=1
    )
    salary_match_weight: float = Field(
        0.02, description="Weight for salary match (0.0-1.0)", ge=0, le=1
    )
    availability_weight: float = Field(
        0.01, description="Weight for availability match (0.0-1.0)", ge=0, le=1
    )
    certifications_weight: float = Field(
        0.01, description="Weight for certifications match (0.0-1.0)", ge=0, le=1
    )
    industry_experience_weight: float = Field(
        0.01, description="Weight for industry experience (0.0-1.0)", ge=0, le=1
    )


class RankingRequest(BaseModel):
    """Request model for ranking resumes against a vacancy."""

    vacancy_id: str = Field(..., description="ID of the job vacancy")
    resume_ids: List[str] = Field(
        ..., description="List of resume IDs to rank", min_length=1
    )
    vacancy_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional vacancy data. If not provided, will use cached match results."
    )
    weights: Optional[RankingWeights] = Field(
        None, description="Optional custom weights for ranking criteria"
    )
    filter_min_match: Optional[float] = Field(
        None, description="Minimum match percentage to include (0-100)", ge=0, le=100
    )


class RankingResponse(BaseModel):
    """Response model for resume ranking."""

    vacancy_id: str = Field(..., description="ID of the job vacancy")
    ranked_resumes: List[Dict[str, Any]] = Field(..., description="List of ranked resumes with scores")
    total_resumes: int = Field(..., description="Total number of resumes ranked")
    filtered_count: int = Field(..., description="Number of resumes filtered out")
    weights_used: RankingWeights = Field(..., description="Weights used for ranking")


@router.post(
    "/rank",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    tags=["Ranking"],
)
async def rank_resumes(
    request: RankingRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Rank resumes against a job vacancy using weighted criteria.

    This endpoint ranks multiple resumes based on their match with a job vacancy,
    using customizable weights for 13 different features.

    Ranking Formula (13 features):
    score = (skill_match_weight * skill_score) +
            (experience_weight * experience_score) +
            (education_weight * education_score) +
            (location_weight * location_score) +
            (keyword_weight * keyword_score) +
            (tfidf_weight * tfidf_score) +
            (vector_weight * vector_score) +
            (recency_weight * recency_score) +
            (culture_fit_weight * culture_fit_score) +
            (salary_match_weight * salary_match_score) +
            (availability_weight * availability_score) +
            (certifications_weight * certifications_score) +
            (industry_experience_weight * industry_experience_score)

    Args:
        request: Ranking request with vacancy_id, resume_ids, and optional weights
        db: Database session

    Returns:
        JSON response with ranked resumes and their scores

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If vacancy or resumes are not found
        HTTPException(500): If ranking processing fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "vacancy-123",
        ...     "resume_ids": ["resume1", "resume2", "resume3"],
        ...     "weights": {
        ...         "skill_match_weight": 0.25,
        ...         "experience_weight": 0.15,
        ...         "education_weight": 0.10,
        ...         "location_weight": 0.05,
        ...         "keyword_weight": 0.10,
        ...         "tfidf_weight": 0.10,
        ...         "vector_weight": 0.10,
        ...         "recency_weight": 0.05,
        ...         "culture_fit_weight": 0.05,
        ...         "salary_match_weight": 0.02,
        ...         "availability_weight": 0.01,
        ...         "certifications_weight": 0.01,
        ...         "industry_experience_weight": 0.01
        ...     },
        ...     "filter_min_match": 50
        ... }
        >>> response = requests.post("http://localhost:8001/api/ranking/rank", json=data)
        >>> response.json()
        {
            "vacancy_id": "vacancy-123",
            "ranked_resumes": [
                {
                    "resume_id": "resume2",
                    "rank": 1,
                    "overall_score": 0.85,
                    "skill_match_score": 0.90,
                    "experience_score": 0.80,
                    "education_score": 0.75,
                    "location_score": 0.70,
                    "keyword_score": 0.85,
                    "tfidf_score": 0.82,
                    "vector_score": 0.88,
                    "recency_score": 0.75,
                    "culture_fit_score": 0.70,
                    "salary_match_score": 0.95,
                    "availability_score": 1.0,
                    "certifications_score": 0.80,
                    "industry_experience_score": 0.85,
                    "match_percentage": 90.0
                },
                {
                    "resume_id": "resume1",
                    "rank": 2,
                    "overall_score": 0.72,
                    ...
                }
            ],
            "total_resumes": 3,
            "filtered_count": 0,
            "weights_used": {
                "skill_match_weight": 0.25,
                "experience_weight": 0.15,
                ...
            }
        }
    """
    try:
        logger.info(
            f"Ranking {len(request.resume_ids)} resumes for vacancy {request.vacancy_id}"
        )

        # Use custom weights or defaults
        weights = request.weights or RankingWeights()

        # Validate weights sum to approximately 1.0
        total_weight = (
            weights.skill_match_weight +
            weights.experience_weight +
            weights.education_weight +
            weights.location_weight +
            weights.keyword_weight +
            weights.tfidf_weight +
            weights.vector_weight +
            weights.recency_weight +
            weights.culture_fit_weight +
            weights.salary_match_weight +
            weights.availability_weight +
            weights.certifications_weight +
            weights.industry_experience_weight
        )
        if abs(total_weight - 1.0) > 0.1:
            logger.warning(
                f"Weights sum to {total_weight}, not 1.0. Normalizing weights."
            )
            # Normalize weights
            weights.skill_match_weight /= total_weight
            weights.experience_weight /= total_weight
            weights.education_weight /= total_weight
            weights.location_weight /= total_weight
            weights.keyword_weight /= total_weight
            weights.tfidf_weight /= total_weight
            weights.vector_weight /= total_weight
            weights.recency_weight /= total_weight
            weights.culture_fit_weight /= total_weight
            weights.salary_match_weight /= total_weight
            weights.availability_weight /= total_weight
            weights.certifications_weight /= total_weight
            weights.industry_experience_weight /= total_weight

        # Get vacancy data or use cached match results
        vacancy_data = request.vacancy_data
        min_experience = 0

        if vacancy_data:
            min_experience = vacancy_data.get("min_experience_months", 0)
        else:
            # Try to get cached match results from database
            try:
                vacancy_uuid = UUID(request.vacancy_id)
                match_results = []
                for resume_id in request.resume_ids:
                    try:
                        resume_uuid = UUID(resume_id)
                        query = select(MatchResult).where(
                            MatchResult.vacancy_id == vacancy_uuid,
                            MatchResult.resume_id == resume_uuid
                        )
                        result = await db.execute(query)
                        match = result.scalar_one_or_none()
                        if match:
                            match_results.append(match)
                    except ValueError:
                        logger.warning(f"Invalid resume_id format: {resume_id}")
                        continue

                if match_results:
                    logger.info(f"Found {len(match_results)} cached match results")
                    # Build ranking from cached results
                    ranked_resumes = []
                    filtered_count = 0

                    for match in match_results:
                        match_percentage = match.match_percentage

                        # Apply minimum match filter if specified
                        if request.filter_min_match and match_percentage < request.filter_min_match:
                            filtered_count += 1
                            continue

                        # Calculate component scores for all 13 features
                        skill_score = match_percentage / 100

                        # Extract scores from match result or use defaults
                        experience_score = 1.0 if match.experience_verified else 0.5
                        education_score = 0.5  # Default - to be enhanced with actual data
                        location_score = 0.5  # Default - to be enhanced with actual data
                        keyword_score = match.keyword_score if match.keyword_score is not None else 0.5
                        tfidf_score = match.tfidf_score if match.tfidf_score is not None else 0.5
                        vector_score = match.vector_score if match.vector_score is not None else 0.5
                        recency_score = 0.5  # Default - to be enhanced with resume date
                        culture_fit_score = 0.5  # Default - to be enhanced with culture analysis
                        salary_match_score = 0.5  # Default - to be enhanced with salary data
                        availability_score = 0.5  # Default - to be enhanced with availability data
                        certifications_score = 0.5  # Default - to be enhanced with certifications data
                        industry_experience_score = 0.5  # Default - to be enhanced with industry data

                        # Calculate overall score using all 13 weighted features
                        overall_score = (
                            weights.skill_match_weight * skill_score +
                            weights.experience_weight * experience_score +
                            weights.education_weight * education_score +
                            weights.location_weight * location_score +
                            weights.keyword_weight * keyword_score +
                            weights.tfidf_weight * tfidf_score +
                            weights.vector_weight * vector_score +
                            weights.recency_weight * recency_score +
                            weights.culture_fit_weight * culture_fit_score +
                            weights.salary_match_weight * salary_match_score +
                            weights.availability_weight * availability_score +
                            weights.certifications_weight * certifications_score +
                            weights.industry_experience_weight * industry_experience_score
                        )

                        # Extract matched and missing skills
                        matched_skills = [
                            s["skill"] for s in match.matched_skills if s.get("matched", False)
                        ]
                        missing_skills = [
                            s["skill"] for s in match.missing_skills if not s.get("matched", True)
                        ]

                        ranked_resumes.append({
                            "resume_id": str(match.resume_id),
                            "match_percentage": match_percentage,
                            "overall_score": round(overall_score, 3),
                            "skill_match_score": round(skill_score, 3),
                            "experience_score": round(experience_score, 3),
                            "education_score": round(education_score, 3),
                            "location_score": round(location_score, 3),
                            "keyword_score": round(keyword_score, 3),
                            "tfidf_score": round(tfidf_score, 3),
                            "vector_score": round(vector_score, 3),
                            "recency_score": round(recency_score, 3),
                            "culture_fit_score": round(culture_fit_score, 3),
                            "salary_match_score": round(salary_match_score, 3),
                            "availability_score": round(availability_score, 3),
                            "certifications_score": round(certifications_score, 3),
                            "industry_experience_score": round(industry_experience_score, 3),
                            "matched_skills": matched_skills,
                            "missing_skills": missing_skills,
                        })

                    # Sort by overall score descending
                    ranked_resumes.sort(key=lambda x: x["overall_score"], reverse=True)

                    # Assign ranks
                    for idx, resume in enumerate(ranked_resumes, start=1):
                        resume["rank"] = idx

                    response_data = {
                        "vacancy_id": request.vacancy_id,
                        "ranked_resumes": ranked_resumes,
                        "total_resumes": len(ranked_resumes) + filtered_count,
                        "filtered_count": filtered_count,
                        "weights_used": weights.model_dump(),
                    }

                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content=response_data,
                    )

            except ValueError:
                logger.warning("Invalid vacancy_id format for database lookup")

        # If no cached results or vacancy_data provided, perform fresh matching
        logger.info("No cached results found, performing fresh matching")

        ranked_resumes = []
        filtered_count = 0

        for resume_id in request.resume_ids:
            try:
                # Find resume file
                file_path = None
                for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
                    potential_path = UPLOAD_DIR / f"{resume_id}{ext}"
                    if potential_path.exists():
                        file_path = potential_path
                        break

                if not file_path:
                    logger.warning(f"Resume file not found: {resume_id}")
                    continue

                # Extract text
                from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

                file_ext = file_path.suffix.lower()
                if file_ext == ".pdf":
                    result = extract_text_from_pdf(file_path)
                elif file_ext == ".docx":
                    result = extract_text_from_docx(file_path)
                else:
                    continue

                if result.get("error") or not result.get("text"):
                    logger.warning(f"Failed to extract text from {resume_id}")
                    continue

                resume_text = result.get("text", "")

                # Extract skills
                try:
                    from services.data_extractor.analyzers import (
                        extract_resume_keywords,
                        extract_resume_entities,
                    )

                    keywords_result = extract_resume_keywords(resume_text, language="en")
                    entities_result = extract_resume_entities(resume_text, language="en")

                    resume_skills = list(set(
                        (keywords_result.get("keywords") or []) +
                        (keywords_result.get("keyphrases") or []) +
                        (entities_result.get("technical_skills") or [])
                    ))
                except ImportError:
                    resume_skills = []

                # Match skills
                if vacancy_data:
                    enhanced_matcher = EnhancedSkillMatcher()
                    required_skills = vacancy_data.get("required_skills", [])

                    if isinstance(required_skills, str):
                        required_skills = [required_skills]

                    matched_count = 0
                    matched_skills = []
                    missing_skills = []

                    for skill in required_skills:
                        match_result = enhanced_matcher.match_with_context(
                            resume_skills=resume_skills,
                            required_skill=skill,
                            use_fuzzy=True
                        )

                        if match_result["matched"]:
                            matched_count += 1
                            matched_skills.append(skill)
                        else:
                            missing_skills.append(skill)

                    match_percentage = (
                        round((matched_count / len(required_skills) * 100), 2)
                        if required_skills else 0.0
                    )
                else:
                    match_percentage = 0.0
                    matched_skills = []
                    missing_skills = []

                # Apply minimum match filter if specified
                if request.filter_min_match and match_percentage < request.filter_min_match:
                    filtered_count += 1
                    continue

                # Calculate component scores for all 13 features
                skill_score = match_percentage / 100

                # Use defaults for features not yet computed in fresh matching
                experience_score = 0.5  # Default - to be enhanced with actual data
                education_score = 0.5  # Default - to be enhanced with actual data
                location_score = 0.5  # Default - to be enhanced with actual data
                keyword_score = 0.5  # Default - to be enhanced with actual data
                tfidf_score = 0.5  # Default - to be enhanced with actual data
                vector_score = 0.5  # Default - to be enhanced with actual data
                recency_score = 0.5  # Default - to be enhanced with resume date
                culture_fit_score = 0.5  # Default - to be enhanced with culture analysis
                salary_match_score = 0.5  # Default - to be enhanced with salary data
                availability_score = 0.5  # Default - to be enhanced with availability data
                certifications_score = 0.5  # Default - to be enhanced with certifications data
                industry_experience_score = 0.5  # Default - to be enhanced with industry data

                # Calculate overall score using all 13 weighted features
                overall_score = (
                    weights.skill_match_weight * skill_score +
                    weights.experience_weight * experience_score +
                    weights.education_weight * education_score +
                    weights.location_weight * location_score +
                    weights.keyword_weight * keyword_score +
                    weights.tfidf_weight * tfidf_score +
                    weights.vector_weight * vector_score +
                    weights.recency_weight * recency_score +
                    weights.culture_fit_weight * culture_fit_score +
                    weights.salary_match_weight * salary_match_score +
                    weights.availability_weight * availability_score +
                    weights.certifications_weight * certifications_score +
                    weights.industry_experience_weight * industry_experience_score
                )

                ranked_resumes.append({
                    "resume_id": resume_id,
                    "match_percentage": match_percentage,
                    "overall_score": round(overall_score, 3),
                    "skill_match_score": round(skill_score, 3),
                    "experience_score": round(experience_score, 3),
                    "education_score": round(education_score, 3),
                    "location_score": round(location_score, 3),
                    "keyword_score": round(keyword_score, 3),
                    "tfidf_score": round(tfidf_score, 3),
                    "vector_score": round(vector_score, 3),
                    "recency_score": round(recency_score, 3),
                    "culture_fit_score": round(culture_fit_score, 3),
                    "salary_match_score": round(salary_match_score, 3),
                    "availability_score": round(availability_score, 3),
                    "certifications_score": round(certifications_score, 3),
                    "industry_experience_score": round(industry_experience_score, 3),
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                })

            except Exception as e:
                logger.error(f"Error processing resume {resume_id}: {e}")
                continue

        # Sort by overall score descending
        ranked_resumes.sort(key=lambda x: x["overall_score"], reverse=True)

        # Assign ranks
        for idx, resume in enumerate(ranked_resumes, start=1):
            resume["rank"] = idx

        response_data = {
            "vacancy_id": request.vacancy_id,
            "ranked_resumes": ranked_resumes,
            "total_resumes": len(ranked_resumes) + filtered_count,
            "filtered_count": filtered_count,
            "weights_used": weights.model_dump(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ranking resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rank resumes: {str(e)}",
        ) from e


@router.get("/top-candidates/{vacancy_id}", tags=["Ranking"])
async def get_top_candidates(
    vacancy_id: str,
    limit: int = Query(10, description="Number of top candidates to return", ge=1, le=100),
    min_match: float = Query(0, description="Minimum match percentage (0-100)", ge=0, le=100),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get top candidates for a vacancy from cached match results.

    This endpoint retrieves the top-ranking candidates for a specific vacancy
    based on previously calculated match results stored in the database.

    Args:
        vacancy_id: ID of the job vacancy
        limit: Maximum number of candidates to return (default: 10, max: 100)
        min_match: Minimum match percentage filter (0-100)
        db: Database session

    Returns:
        JSON response with list of top candidates

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8001/api/ranking/top-candidates/vacancy-123?limit=5&min_match=70"
        ... )
        >>> response.json()
        {
            "vacancy_id": "vacancy-123",
            "top_candidates": [
                {
                    "resume_id": "resume-abc",
                    "rank": 1,
                    "match_percentage": 95.5,
                    "overall_score": 0.92
                },
                ...
            ],
            "total_candidates": 5
        }
    """
    try:
        logger.info(f"Getting top {limit} candidates for vacancy {vacancy_id}")

        # Parse vacancy_id as UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy_id format: {vacancy_id}",
            )

        # Query match results for this vacancy
        query = select(MatchResult).where(
            MatchResult.vacancy_id == vacancy_uuid
        )

        # Apply minimum match filter
        if min_match > 0:
            query = query.where(MatchResult.match_percentage >= min_match)

        # Order by match percentage descending
        query = query.order_by(MatchResult.match_percentage.desc())

        # Apply limit
        query = query.limit(limit)

        result = await db.execute(query)
        matches = result.scalars().all()

        top_candidates = []
        for idx, match in enumerate(matches, start=1):
            matched_skills = [
                s["skill"] for s in match.matched_skills if s.get("matched", False)
            ]
            missing_skills = [
                s["skill"] for s in match.missing_skills if not s.get("matched", True)
            ]

            top_candidates.append({
                "resume_id": str(match.resume_id),
                "rank": idx,
                "match_percentage": match.match_percentage,
                "overall_score": match.overall_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "recommendation": match.recommendation,
            })

        response_data = {
            "vacancy_id": vacancy_id,
            "top_candidates": top_candidates,
            "total_candidates": len(top_candidates),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top candidates: {str(e)}",
        ) from e
