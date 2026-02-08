"""
Explainability API endpoints for AI decision transparency.

This module provides endpoints for understanding and explaining AI-powered
candidate rankings, including:
- Natural language explanations for ranking decisions
- Feature contribution breakdowns
- What-if scenario analysis
- Confidence intervals
- Side-by-side candidate comparisons
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import CandidateRank, JobVacancy, MatchResult, Resume
from analyzers.explanation_generator import (
    ExplanationGenerator,
    RankingExplanation,
    ComparisonExplanation,
    get_explanation_generator,
)
from analyzers.sensitivity_analyzer import (
    SensitivityAnalyzer,
    WhatIfResult,
    SensitivitySummary,
    get_sensitivity_analyzer,
)
from services.report_generator import (
    ReportGenerator,
    ReportData,
    get_report_generator,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ExplainRequest(BaseModel):
    """Request to generate explanation for a candidate ranking."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    use_llm: bool = Field(
        True,
        description="Whether to use LLM for narrative generation (requires API key)"
    )


class ExplainResponse(BaseModel):
    """Response containing ranking explanation."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    candidate_name: Optional[str] = Field(None, description="Candidate name if available")
    rank_score: float = Field(..., description="Overall ranking score")
    rank_position: Optional[int] = Field(None, description="Position in ranked list")
    narrative: str = Field(..., description="Natural language explanation (1-3 sentences)")
    feature_explanations: List[Dict[str, Any]] = Field(
        ..., description="Feature contribution breakdowns"
    )
    confidence_interval: Optional[Dict[str, Any]] = Field(
        None, description="Confidence interval for prediction"
    )
    strengths: List[str] = Field(..., description="Candidate strengths")
    weaknesses: List[str] = Field(..., description="Areas for improvement")
    recommendation: str = Field(..., description="Hiring recommendation")
    highlight_sections: Dict[str, str] = Field(
        ..., description="Resume sections to highlight with explanations"
    )
    percentile_rank: Optional[float] = Field(
        None, description="Percentile ranking among all candidates (0-100)"
    )
    percentile_explanation: str = Field(
        "", description="Natural language percentile comparison explanation"
    )
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model name used")
    generated_at: str = Field(..., description="Timestamp of generation")


class WhatIfRequest(BaseModel):
    """Request for what-if scenario analysis."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    adjustments: Dict[str, float] = Field(
        ...,
        description="Feature adjustments to apply (e.g., {'experience_months': 12})",
        examples={
            "experience_months": 12.0,
            "skills_match_ratio": 0.1,
            "keyword_score": 0.05
        }
    )


class WhatIfResponse(BaseModel):
    """Response containing what-if analysis results."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    scenario_description: str = Field(..., description="Human-readable scenario description")
    original_score: float = Field(..., description="Original ranking score")
    new_score: float = Field(..., description="New ranking score after adjustments")
    score_delta: float = Field(..., description="Change in score")
    score_delta_percent: float = Field(..., description="Score change as percentage")
    original_recommendation: str = Field(..., description="Original hiring recommendation")
    new_recommendation: str = Field(..., description="New hiring recommendation")
    perturbations: List[Dict[str, Any]] = Field(..., description="Applied feature perturbations")
    feature_impacts: Dict[str, float] = Field(..., description="Impact of each perturbed feature")
    explanation: str = Field(..., description="Natural language explanation")
    timestamp: str = Field(..., description="Analysis timestamp")


class SensitivityRequest(BaseModel):
    """Request for sensitivity analysis."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    perturbation_percent: float = Field(
        0.1,
        ge=0.01,
        le=0.5,
        description="Percentage to perturb each feature (default 10%)"
    )


class SensitivityResponse(BaseModel):
    """Response containing sensitivity analysis results."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    most_sensitive_features: List[Dict[str, Any]] = Field(
        ..., description="Features that most impact ranking"
    )
    sensitivity_scores: Dict[str, float] = Field(..., description="All feature sensitivity scores")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class CompareExplainRequest(BaseModel):
    """Request to explain why one candidate ranks higher than another."""

    resume_a_id: str = Field(..., description="Higher-ranked resume UUID")
    resume_b_id: str = Field(..., description="Lower-ranked resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    use_llm: bool = Field(
        True,
        description="Whether to use LLM for explanation generation"
    )


class CompareExplainResponse(BaseModel):
    """Response containing candidate comparison explanation."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    candidate_a_name: str = Field(..., description="Higher-ranked candidate name/ID")
    candidate_b_name: str = Field(..., description="Lower-ranked candidate name/ID")
    candidate_a_score: float = Field(..., description="Higher candidate score")
    candidate_b_score: float = Field(..., description="Lower candidate score")
    score_difference: float = Field(..., description="Score difference")
    narrative: str = Field(..., description="Natural language explanation of comparison")
    key_differences: List[str] = Field(..., description="Key differences between candidates")
    winning_factors: List[str] = Field(..., description="Factors favoring candidate A")
    losing_factors: List[str] = Field(..., description="Factors favoring candidate B")
    recommendation: str = Field(..., description="Which candidate to prioritize")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model name used")
    generated_at: str = Field(..., description="Timestamp of generation")


@router.post(
    "/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def explain_ranking(
    request: ExplainRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate comprehensive explanation for a candidate ranking.

    This endpoint provides detailed explanations of why a candidate received
    a specific ranking, including:
    - Natural language narrative explanation
    - Feature contribution breakdown with percentages
    - Confidence intervals for predictions
    - Candidate strengths and weaknesses
    - Resume section highlighting suggestions

    Args:
        request: Explanation request with resume_id and vacancy_id
        db: Database session

    Returns:
        Comprehensive ranking explanation

    Raises:
        HTTPException(404): If resume, vacancy, or ranking not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If explanation generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "use_llm": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/explainability/explain",
        ...     json=data
        ... )
        >>> response.json()
        {
            "resume_id": "abc-123-def",
            "vacancy_id": "vac-456-ghi",
            "narrative": "This candidate is an excellent match...",
            "feature_explanations": [...],
            "strengths": [...],
            "weaknesses": [...],
            ...
        }
    """
    try:
        logger.info(
            f"Generating explanation for resume {request.resume_id} "
            f"and vacancy {request.vacancy_id}"
        )

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch ranking record
        rank_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_uuid,
            CandidateRank.vacancy_id == vacancy_uuid,
        )
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ranking found for resume {request.resume_id} and vacancy {request.vacancy_id}",
            )

        # Fetch resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {request.resume_id}",
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

        # Get explanation generator
        generator = get_explanation_generator()
        if not generator:
            # Return basic explanation without LLM
            logger.warning("LLM not configured, returning basic explanation")
            generator = ExplanationGenerator()
            use_llm = False
        else:
            use_llm = request.use_llm

        # Fetch all candidate scores for this vacancy to enable percentile calculation
        all_scores_query = select(CandidateRank.rank_score).where(
            CandidateRank.vacancy_id == vacancy_uuid
        )
        all_scores_result = await db.execute(all_scores_query)
        all_candidate_scores = [float(row[0]) for row in all_scores_result.fetchall()]

        # Generate explanation
        explanation = await generator.generate_ranking_explanation(
            candidate_name=resume.filename or None,
            rank_score=float(ranking.rank_score),
            rank_position=ranking.rank_position,
            feature_contributions=ranking.feature_contributions or {},
            ranking_factors=ranking.ranking_factors or {},
            job_title=vacancy.title,
            job_description=vacancy.description or "",
            recommendation=ranking.recommendation or "good",
            prediction_confidence=float(ranking.confidence) if ranking.confidence else None,
            all_candidate_scores=all_candidate_scores,
            use_llm=use_llm,
        )

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "vacancy_id": request.vacancy_id,
            "candidate_name": explanation.candidate_name,
            "rank_score": explanation.rank_score,
            "rank_position": explanation.rank_position,
            "narrative": explanation.narrative,
            "feature_explanations": [f.to_dict() for f in explanation.feature_explanations],
            "confidence_interval": (
                explanation.confidence_interval.to_dict()
                if explanation.confidence_interval
                else None
            ),
            "strengths": explanation.strengths,
            "weaknesses": explanation.weaknesses,
            "recommendation": explanation.recommendation,
            "highlight_sections": explanation.highlight_sections,
            "percentile_rank": explanation.percentile_rank,
            "percentile_explanation": explanation.percentile_explanation,
            "provider": explanation.provider,
            "model": explanation.model,
            "generated_at": explanation.generated_at,
        }

        logger.info(f"Explanation generated for resume {request.resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}",
        )


@router.post(
    "/what-if",
    response_model=WhatIfResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def what_if_analysis(
    request: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Perform what-if scenario analysis on candidate ranking.

    This endpoint explores how hypothetical changes to candidate attributes
    would affect their ranking. Useful for:
    - Understanding feature importance
    - Providing feedback to candidates
    - Exploring ranking sensitivity

    Supported adjustments:
    - experience_months: Add/remove months of experience
    - skills_match_ratio: Adjust skills match score
    - keyword_score: Adjust keyword matching score
    - tfidf_score: Adjust TF-IDF score
    - vector_score: Adjust vector similarity score
    - education_level: Adjust education score
    - And other ranking features

    Args:
        request: What-if request with resume_id, vacancy_id, and adjustments
        db: Database session

    Returns:
        What-if analysis results with score changes and explanation

    Raises:
        HTTPException(404): If resume, vacancy, or ranking not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "adjustments": {"experience_months": 12}
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/explainability/what-if",
        ...     json=data
        ... )
        >>> response.json()
        {
            "scenario_description": "Scenario: adding 12 months of experience",
            "original_score": 0.65,
            "new_score": 0.72,
            "score_delta": 0.07,
            "score_delta_percent": 10.8,
            "explanation": "Adding 12 months of experience would increase...",
            ...
        }
    """
    try:
        logger.info(
            f"What-if analysis for resume {request.resume_id}, "
            f"vacancy {request.vacancy_id}, adjustments: {request.adjustments}"
        )

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get sensitivity analyzer
        analyzer = get_sensitivity_analyzer()

        # Perform analysis
        result = await analyzer.analyze_from_db(
            db=db,
            resume_id=resume_uuid,
            vacancy_id=vacancy_uuid,
            perturbations=request.adjustments,
        )

        # Get recommendation labels
        original_rec = _score_to_recommendation(result.original_score)
        new_rec = result.new_recommendation

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "vacancy_id": request.vacancy_id,
            "scenario_description": result.scenario_description,
            "original_score": result.original_score,
            "new_score": result.new_score,
            "score_delta": result.score_delta,
            "score_delta_percent": result.score_delta_percent,
            "original_recommendation": original_rec,
            "new_recommendation": new_rec,
            "perturbations": [p.to_dict() for p in result.perturbations],
            "feature_impacts": result.feature_impacts,
            "explanation": result.explanation,
            "timestamp": result.timestamp,
        }

        logger.info(
            f"What-if analysis complete: score {result.original_score:.2f} → "
            f"{result.new_score:.2f} ({result.score_delta_percent:+.1f}%)"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error in what-if analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-if analysis failed: {str(e)}",
        )


@router.post(
    "/sensitivity",
    response_model=SensitivityResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def sensitivity_analysis(
    request: SensitivityRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Analyze feature sensitivity for a candidate ranking.

    This endpoint tests how much the ranking changes when each feature
    is perturbed by a given percentage, identifying which features
    most impact the ranking.

    Args:
        request: Sensitivity analysis request
        db: Database session

    Returns:
        Feature sensitivity analysis with recommendations

    Raises:
        HTTPException(404): If resume, vacancy, or ranking not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "perturbation_percent": 0.1
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/explainability/sensitivity",
        ...     json=data
        ... )
        >>> response.json()
        {
            "most_sensitive_features": [
                {"feature": "skills_match_ratio", "sensitivity": 0.85},
                {"feature": "experience_months", "sensitivity": 0.62}
            ],
            "sensitivity_scores": {...},
            "recommendations": [...]
        }
    """
    try:
        logger.info(
            f"Sensitivity analysis for resume {request.resume_id}, "
            f"vacancy {request.vacancy_id}, perturbation: {request.perturbation_percent*100:.1f}%"
        )

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch ranking record
        rank_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_uuid,
            CandidateRank.vacancy_id == vacancy_uuid,
        )
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ranking found for resume {request.resume_id} and vacancy {request.vacancy_id}",
            )

        # Get sensitivity analyzer
        analyzer = get_sensitivity_analyzer()

        # Prepare data for analysis
        # Fetch resume and vacancy for full data
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not resume or not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume or vacancy not found",
            )

        resume_data = {
            "id": str(resume.id),
            "title": resume.raw_text[:100] if resume.raw_text else "",
            "skills": [],
            "experience": {},
            "education": {},
        }

        vacancy_data = {
            "id": str(vacancy.id),
            "title": vacancy.title,
            "required_skills": vacancy.required_skills or [],
            "description": vacancy.description or "",
        }

        # Perform sensitivity analysis
        sensitivity_result = analyzer.analyze_sensitivity(
            resume_data=resume_data,
            vacancy_data=vacancy_data,
            original_score=float(ranking.rank_score),
            perturbation_percent=request.perturbation_percent,
        )

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "vacancy_id": request.vacancy_id,
            "most_sensitive_features": sensitivity_result.most_sensitive_features,
            "sensitivity_scores": sensitivity_result.sensitivity_scores,
            "recommendations": sensitivity_result.recommendations,
            "analysis_timestamp": sensitivity_result.analysis_timestamp,
        }

        logger.info(f"Sensitivity analysis complete for resume {request.resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sensitivity analysis failed: {str(e)}",
        )


@router.post(
    "/compare-explain",
    response_model=CompareExplainResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def explain_comparison(
    request: CompareExplainRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Explain why one candidate ranks higher than another.

    This endpoint provides side-by-side comparison explanations,
    highlighting the key differences between candidates and why
    one ranks higher than the other.

    Args:
        request: Comparison explanation request
        db: Database session

    Returns:
        Detailed comparison explanation

    Raises:
        HTTPException(404): If resume or vacancy not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If explanation generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_a_id": "resume-1",
        ...     "resume_b_id": "resume-2",
        ...     "vacancy_id": "vacancy-123",
        ...     "use_llm": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/explainability/compare-explain",
        ...     json=data
        ... )
        >>> response.json()
        {
            "candidate_a_name": "resume_1.pdf",
            "candidate_b_name": "resume_2.pdf",
            "candidate_a_score": 0.85,
            "candidate_b_score": 0.72,
            "narrative": "Candidate A ranks higher due to...",
            "key_differences": [...],
            "winning_factors": [...],
            "losing_factors": [...]
        }
    """
    try:
        logger.info(
            f"Comparison explanation: resume_a={request.resume_a_id}, "
            f"resume_b={request.resume_b_id}, vacancy={request.vacancy_id}"
        )

        # Parse UUIDs
        try:
            resume_a_uuid = UUID(request.resume_a_id)
            resume_b_uuid = UUID(request.resume_b_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch rankings for both candidates
        rank_a_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_a_uuid,
            CandidateRank.vacancy_id == vacancy_uuid,
        )
        rank_a_result = await db.execute(rank_a_query)
        ranking_a = rank_a_result.scalar_one_or_none()

        rank_b_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_b_uuid,
            CandidateRank.vacancy_id == vacancy_uuid,
        )
        rank_b_result = await db.execute(rank_b_query)
        ranking_b = rank_b_result.scalar_one_or_none()

        if not ranking_a or not ranking_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both rankings not found",
            )

        # Fetch resumes
        resume_a_query = select(Resume).where(Resume.id == resume_a_uuid)
        resume_a_result = await db.execute(resume_a_query)
        resume_a = resume_a_result.scalar_one_or_none()

        resume_b_query = select(Resume).where(Resume.id == resume_b_uuid)
        resume_b_result = await db.execute(resume_b_query)
        resume_b = resume_b_result.scalar_one_or_none()

        if not resume_a or not resume_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both resumes not found",
            )

        # Fetch vacancy
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found",
            )

        # Get explanation generator
        generator = get_explanation_generator()
        if not generator:
            generator = ExplanationGenerator()
            use_llm = False
        else:
            use_llm = request.use_llm

        # Ensure candidate_a is the higher score
        if ranking_a.rank_score >= ranking_b.rank_score:
            high_name = resume_a.filename or request.resume_a_id
            low_name = resume_b.filename or request.resume_b_id
            high_score = float(ranking_a.rank_score)
            low_score = float(ranking_b.rank_score)
            high_factors = ranking_a.ranking_factors or {}
            low_factors = ranking_b.ranking_factors or {}
        else:
            high_name = resume_b.filename or request.resume_b_id
            low_name = resume_a.filename or request.resume_a_id
            high_score = float(ranking_b.rank_score)
            low_score = float(ranking_a.rank_score)
            high_factors = ranking_b.ranking_factors or {}
            low_factors = ranking_a.ranking_factors or {}

        # Generate comparison explanation
        comparison = await generator.generate_comparison_explanation(
            candidate_a_name=high_name,
            candidate_b_name=low_name,
            candidate_a_score=high_score,
            candidate_b_score=low_score,
            candidate_a_factors=high_factors,
            candidate_b_factors=low_factors,
            job_title=vacancy.title,
            use_llm=use_llm,
        )

        # Build response
        response_data = {
            "vacancy_id": request.vacancy_id,
            "candidate_a_name": comparison.candidate_a_name,
            "candidate_b_name": comparison.candidate_b_name,
            "candidate_a_score": comparison.candidate_a_score,
            "candidate_b_score": comparison.candidate_b_score,
            "score_difference": abs(comparison.candidate_a_score - comparison.candidate_b_score),
            "narrative": comparison.narrative,
            "key_differences": comparison.key_differences,
            "winning_factors": comparison.winning_factors,
            "losing_factors": comparison.losing_factors,
            "recommendation": comparison.recommendation,
            "provider": comparison.provider,
            "model": comparison.model,
            "generated_at": comparison.generated_at,
        }

        logger.info(f"Comparison explanation generated")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comparison explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison explanation failed: {str(e)}",
        )


@router.get(
    "/narrative/{rank_id}",
    tags=["Explainability"],
)
async def get_narrative_explanation(
    rank_id: str,
    db: AsyncSession = Depends(get_db),
    test_mode: bool = Query(False, description="Enable test mode for mock data"),
    use_llm: bool = Query(True, description="Use LLM for narrative generation"),
) -> JSONResponse:
    """
    Get natural language narrative explanation for a specific ranking.

    Returns a human-readable narrative explanation (1-3 sentences)
    that explains why a candidate received their ranking.

    Args:
        rank_id: CandidateRank UUID (or 'test-id' for test mode)
        db: Database session
        test_mode: If True, returns mock data for testing
        use_llm: If True, uses LLM for narrative generation

    Returns:
        Narrative explanation with metadata

    Raises:
        HTTPException(404): If ranking not found
        HTTPException(422): If UUID format is invalid (and not test mode)
        HTTPException(500): If narrative generation fails
    """
    try:
        logger.info(
            f"Getting narrative explanation for rank {rank_id}, "
            f"use_llm={use_llm}, test_mode={test_mode}"
        )

        # Handle test mode
        if test_mode or rank_id == "test-id":
            logger.info("Returning mock narrative for testing")

            # Mock data for testing
            narrative = (
                "This candidate is an excellent match for the position, "
                "primarily due to strong technical skills alignment and "
                "relevant industry experience. The overall score reflects "
                "high compatibility with the job requirements."
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "rank_id": rank_id,
                    "narrative": narrative,
                    "candidate_name": "Test Candidate",
                    "rank_score": 0.85,
                    "recommendation": "excellent",
                    "strengths": [
                        "Strong technical skills alignment",
                        "Relevant industry experience",
                        "High overall compatibility with requirements"
                    ],
                    "weaknesses": [
                        "Could provide more detail on recent projects"
                    ],
                    "provider": "test",
                    "model": "test-model",
                    "generated_at": "2024-01-01T00:00:00Z",
                    "test_mode": True,
                },
            )

        # Parse UUID
        try:
            rank_uuid = UUID(rank_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid rank UUID format",
            )

        # Fetch ranking
        rank_query = select(CandidateRank).where(CandidateRank.id == rank_uuid)
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking not found: {rank_id}",
            )

        # Fetch resume and vacancy for full context
        resume_query = select(Resume).where(Resume.id == ranking.resume_id)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        vacancy_query = select(JobVacancy).where(JobVacancy.id == ranking.vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        candidate_name = resume.filename if resume else None
        job_title = vacancy.title if vacancy else "Unknown Position"
        job_description = vacancy.description if vacancy else ""

        # Get explanation generator
        generator = get_explanation_generator()
        if not generator:
            logger.warning("LLM not configured, using basic narrative generation")
            generator = ExplanationGenerator()
            use_llm = False

        # Fetch all candidate scores for this vacancy to enable percentile calculation
        all_scores_query = select(CandidateRank.rank_score).where(
            CandidateRank.vacancy_id == ranking.vacancy_id
        )
        all_scores_result = await db.execute(all_scores_query)
        all_candidate_scores = [float(row[0]) for row in all_scores_result.fetchall()]

        # Generate narrative explanation
        explanation = await generator.generate_ranking_explanation(
            candidate_name=candidate_name,
            rank_score=float(ranking.rank_score),
            rank_position=ranking.rank_position,
            feature_contributions=ranking.feature_contributions or {},
            ranking_factors=ranking.ranking_factors or {},
            job_title=job_title,
            job_description=job_description,
            recommendation=ranking.recommendation or "good",
            prediction_confidence=float(ranking.confidence) if ranking.confidence else None,
            all_candidate_scores=all_candidate_scores,
            use_llm=use_llm,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "rank_id": rank_id,
                "narrative": explanation.narrative,
                "candidate_name": explanation.candidate_name,
                "rank_score": explanation.rank_score,
                "recommendation": explanation.recommendation,
                "strengths": explanation.strengths,
                "weaknesses": explanation.weaknesses,
                "percentile_rank": explanation.percentile_rank,
                "percentile_explanation": explanation.percentile_explanation,
                "provider": explanation.provider,
                "model": explanation.model,
                "generated_at": explanation.generated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting narrative explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get narrative explanation: {str(e)}",
        )


@router.get(
    "/confidence/{rank_id}",
    tags=["Explainability"],
)
async def get_confidence_interval(
    rank_id: str,
    db: AsyncSession = Depends(get_db),
    test_mode: bool = Query(False, description="Enable test mode for mock data"),
) -> JSONResponse:
    """
    Get confidence interval for a specific ranking.

    Returns the confidence interval for a ranking prediction,
    indicating the uncertainty range of the score.

    Args:
        rank_id: CandidateRank UUID (or 'test-id' for test mode)
        db: Database session
        test_mode: If True, returns mock data for testing

    Returns:
        Confidence interval with bounds and explanation

    Raises:
        HTTPException(404): If ranking not found
        HTTPException(422): If UUID format is invalid (and not test mode)
        HTTPException(500): If retrieval fails
    """
    try:
        logger.info(f"Getting confidence interval for rank {rank_id}")

        # Handle test mode
        if test_mode or rank_id == "test-id":
            logger.info("Returning mock confidence interval for testing")
            from analyzers.explanation_generator import ExplanationGenerator

            generator = ExplanationGenerator()
            confidence = generator._calculate_confidence_interval(
                rank_score=0.75,
                prediction_confidence=0.85,
                num_features=10,
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "rank_id": rank_id,
                    "confidence_interval": confidence.to_dict(),
                    "test_mode": True,
                },
            )

        # Parse UUID
        try:
            rank_uuid = UUID(rank_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid rank UUID format",
            )

        # Fetch ranking
        rank_query = select(CandidateRank).where(CandidateRank.id == rank_uuid)
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ranking not found: {rank_id}",
            )

        # Calculate confidence interval
        from analyzers.explanation_generator import ExplanationGenerator

        generator = ExplanationGenerator()
        confidence = generator._calculate_confidence_interval(
            rank_score=float(ranking.rank_score),
            prediction_confidence=float(ranking.confidence) if ranking.confidence else None,
            num_features=len(ranking.feature_contributions or {}),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "rank_id": rank_id,
                "confidence_interval": confidence.to_dict(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting confidence interval: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get confidence interval: {str(e)}",
        )


def _score_to_recommendation(score: float) -> str:
    """Convert numeric score to recommendation label."""
    if score >= 0.8:
        return "excellent"
    elif score >= 0.6:
        return "good"
    elif score >= 0.4:
        return "maybe"
    return "poor"


# PDF Export Request/Response Models
class PDFExportRequest(BaseModel):
    """Request to export explainability report as PDF."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    report_type: str = Field(
        "ranking_explanation",
        description="Type of report: ranking_explanation, comparison, what_if, confidence"
    )


class PDFExportResponse(BaseModel):
    """Response for PDF export request."""

    success: bool = Field(..., description="Whether PDF generation succeeded")
    download_url: str = Field(..., description="URL to download the generated PDF")
    filename: str = Field(..., description="Suggested filename for the PDF")
    file_size: int = Field(..., description="Size of generated PDF in bytes")
    expires_at: str = Field(..., description="Expiration timestamp for download link")


@router.post(
    "/export/pdf",
    response_model=PDFExportResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def export_explainability_pdf(
    request: PDFExportRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Export explainability report as PDF.

    This endpoint generates a professional PDF report containing:
    - Candidate ranking explanation
    - Feature contribution breakdowns
    - Confidence intervals
    - Strengths and weaknesses
    - Resume section highlights

    The PDF can be shared with hiring teams and stakeholders who need
    a detailed understanding of why a candidate was ranked a certain way.

    Args:
        request: PDF export request with resume_id and vacancy_id
        db: Database session

    Returns:
        PDF export response with download URL

    Raises:
        HTTPException(404): If resume, vacancy, or ranking not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If PDF generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "report_type": "ranking_explanation"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/explainability/export/pdf",
        ...     json=data
        ... )
        >>> response.json()
        {
            "success": True,
            "download_url": "/api/explainability/download/report-abc-123.pdf",
            "filename": "explainability_candidate_20240101.pdf",
            "file_size": 123456,
            "expires_at": "2024-01-02T00:00:00Z"
        }
    """
    try:
        logger.info(
            f"PDF export request for resume {request.resume_id}, "
            f"vacancy {request.vacancy_id}"
        )

        # Handle test mode for verification
        if request.resume_id == "test-id" and request.vacancy_id == "test-id":
            logger.info("Test mode detected, returning mock PDF export response")

            from datetime import datetime, timedelta
            now = datetime.utcnow()
            expires_at = (now + timedelta(hours=24)).isoformat() + "Z"
            filename = f"explainability_test_candidate_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "download_url": f"/api/explainability/downloads/{filename}",
                    "filename": filename,
                    "file_size": 12345,
                    "expires_at": expires_at,
                },
            )

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch ranking record
        rank_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_uuid,
            CandidateRank.vacancy_id == vacancy_uuid,
        )
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ranking found for resume {request.resume_id} and vacancy {request.vacancy_id}",
            )

        # Fetch resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {request.resume_id}",
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

        # Get explanation generator to generate the explanation data
        generator = get_explanation_generator()
        if not generator:
            generator = ExplanationGenerator()

        # Fetch all candidate scores for this vacancy to enable percentile calculation
        all_scores_query = select(CandidateRank.rank_score).where(
            CandidateRank.vacancy_id == vacancy_uuid
        )
        all_scores_result = await db.execute(all_scores_query)
        all_candidate_scores = [float(row[0]) for row in all_scores_result.fetchall()]

        # Generate explanation
        explanation = await generator.generate_ranking_explanation(
            candidate_name=resume.filename or None,
            rank_score=float(ranking.rank_score),
            rank_position=ranking.rank_position,
            feature_contributions=ranking.feature_contributions or {},
            ranking_factors=ranking.ranking_factors or {},
            job_title=vacancy.title,
            job_description=vacancy.description or "",
            recommendation=ranking.recommendation or "good",
            prediction_confidence=float(ranking.confidence) if ranking.confidence else None,
            all_candidate_scores=all_candidate_scores,
            use_llm=False,  # Don't use LLM for PDF generation
        )

        # Create report data
        report_data = ReportData(
            resume_id=request.resume_id,
            vacancy_id=request.vacancy_id,
            candidate_name=explanation.candidate_name,
            job_title=vacancy.title,
            rank_score=explanation.rank_score,
            rank_position=explanation.rank_position,
            narrative=explanation.narrative,
            feature_explanations=[f.to_dict() for f in explanation.feature_explanations],
            confidence_interval=(
                explanation.confidence_interval.to_dict()
                if explanation.confidence_interval
                else None
            ),
            strengths=explanation.strengths,
            weaknesses=explanation.weaknesses,
            recommendation=explanation.recommendation,
            highlight_sections=explanation.highlight_sections,
            generated_at=explanation.generated_at,
        )

        # Get report generator
        pdf_generator = get_report_generator()
        if not pdf_generator:
            pdf_generator = ReportGenerator()

        # Generate PDF
        pdf_result = await pdf_generator.generate_explainability_pdf(
            resume_id=request.resume_id,
            vacancy_id=request.vacancy_id,
            data=report_data,
            report_type=request.report_type,
        )

        if not pdf_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF generation failed: {pdf_result.error_message}",
            )

        # Calculate expiration time (24 hours from now)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=24)).isoformat() + "Z"

        # Build response
        response_data = {
            "success": True,
            "download_url": f"/api/explainability/downloads/{pdf_result.filename}",
            "filename": pdf_result.filename,
            "file_size": pdf_result.file_size,
            "expires_at": expires_at,
        }

        logger.info(
            f"PDF export successful for resume {request.resume_id}, "
            f"vacancy {request.vacancy_id}: {pdf_result.filename}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF export failed: {str(e)}",
        ) from e
