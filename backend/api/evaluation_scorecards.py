"""
Evaluation scorecard management endpoints.

This module provides endpoints for managing individual evaluator scorecards,
including CRUD operations for creating, reading, updating, and deleting scorecards
with support for criteria responses and aggregate scoring.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.evaluation_criteria import EvaluationCriteria
from models.evaluation_scorecard import EvaluationScorecard
from models.evaluation_template import EvaluationTemplate
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class CriteriaResponse(BaseModel):
    """Individual criteria response definition."""

    criteria_id: str = Field(..., description="ID of the criteria being evaluated")
    score: float = Field(..., description="Score given for this criteria", ge=0)
    comments: Optional[str] = Field(None, description="Optional comments for this criteria")


class ScorecardCreate(BaseModel):
    """Request model for creating an evaluation scorecard."""

    template_id: str = Field(..., description="ID of the evaluation template being used")
    resume_id: str = Field(..., description="ID of the resume (candidate) being evaluated")
    evaluator_id: Optional[str] = Field(None, description="ID of the recruiter/evaluator")
    criteria_responses: List[CriteriaResponse] = Field(
        ..., min_length=1, description="List of criteria responses"
    )
    overall_score: Optional[float] = Field(None, description="Optional overall score", ge=0)
    status: str = Field("draft", description="Status of the scorecard (draft, in_progress, completed)")
    evaluator_comments: Optional[str] = Field(None, description="Overall comments from evaluator")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")


class ScorecardUpdate(BaseModel):
    """Request model for updating an evaluation scorecard."""

    criteria_responses: Optional[List[CriteriaResponse]] = Field(None, description="List of criteria responses")
    overall_score: Optional[float] = Field(None, description="Optional overall score", ge=0)
    status: Optional[str] = Field(None, description="Status of the scorecard")
    evaluator_comments: Optional[str] = Field(None, description="Overall comments from evaluator")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")


class ScorecardStatusUpdate(BaseModel):
    """Request model for updating scorecard status."""

    status: str = Field(..., description="New status for the scorecard (draft, in_progress, completed)")


class CriteriaResponseData(BaseModel):
    """Response model for a single criteria response."""

    criteria_id: str = Field(..., description="ID of the criteria")
    score: float = Field(..., description="Score for this criteria")
    comments: Optional[str] = Field(None, description="Comments for this criteria")


class ScorecardResponse(BaseModel):
    """Response model for a single evaluation scorecard."""

    id: str = Field(..., description="Unique identifier for the scorecard")
    template_id: str = Field(..., description="ID of the evaluation template")
    resume_id: str = Field(..., description="ID of the resume (candidate)")
    evaluator_id: Optional[str] = Field(None, description="ID of the evaluator")
    criteria_responses: List[CriteriaResponseData] = Field(..., description="List of criteria responses")
    overall_score: Optional[float] = Field(None, description="Overall score")
    status: str = Field(..., description="Status of the scorecard")
    evaluator_comments: Optional[str] = Field(None, description="Evaluator comments")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ScorecardListResponse(BaseModel):
    """Response model for listing evaluation scorecards."""

    scorecards: List[ScorecardResponse] = Field(..., description="List of scorecards")
    total_count: int = Field(..., description="Total number of scorecards")


class EvaluatorScoreBreakdown(BaseModel):
    """Score breakdown for a single evaluator."""

    evaluator_id: Optional[str] = Field(None, description="ID of the evaluator")
    overall_score: Optional[float] = Field(None, description="Overall score from this evaluator")
    criteria_scores: dict = Field(..., description="Dictionary of criteria_id -> score")
    status: str = Field(..., description="Status of the scorecard")
    scorecard_id: str = Field(..., description="ID of the scorecard")


class AggregateScoresResponse(BaseModel):
    """Response model for aggregate score calculations."""

    resume_id: str = Field(..., description="ID of the resume/candidate")
    total_evaluators: int = Field(..., description="Number of evaluators")
    average_scores: dict = Field(..., description="Average score per criteria across all evaluators")
    overall_average: float = Field(..., description="Overall average score across all evaluators")
    weighted_score: float = Field(..., description="Weighted score using template criteria weights")
    scores_by_evaluator: List[EvaluatorScoreBreakdown] = Field(
        ..., description="Breakdown of scores by each evaluator"
    )
    completion_rate: float = Field(..., description="Percentage of evaluators who completed their scorecards")


class ScorecardComparisonData(BaseModel):
    """Scorecard data for a single candidate in comparison."""

    resume_id: str = Field(..., description="ID of the resume/candidate")
    scorecards: List[ScorecardResponse] = Field(..., description="List of scorecards for this candidate")
    total_evaluators: int = Field(..., description="Number of evaluators for this candidate")
    average_overall_score: float = Field(..., description="Average overall score across all evaluators")


class ScorecardComparisonResponse(BaseModel):
    """Response model for scorecard comparison."""

    template_id: str = Field(..., description="ID of the evaluation template")
    template_name: Optional[str] = Field(None, description="Name of the evaluation template")
    candidates: List[ScorecardComparisonData] = Field(
        ..., description="List of candidates with their scorecard data"
    )
    total_candidates: int = Field(..., description="Number of candidates being compared")
    comparison_criteria: List[dict] = Field(..., description="List of criteria from the template")
    created_at: str = Field(..., description="Timestamp of comparison")


@router.post(
    "/",
    response_model=ScorecardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Evaluation Scorecards"],
)
async def create_scorecard(
    request: ScorecardCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create an evaluation scorecard.

    This endpoint creates a new scorecard for evaluating a candidate based on
    an evaluation template. Each scorecard contains responses to the template's
    criteria with scores and optional comments.

    Args:
        request: Request body containing scorecard details
        db: Database session

    Returns:
        JSON response with created scorecard details

    Raises:
        HTTPException(404): If template or resume is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/evaluation-scorecards/",
        ...     json={
        ...         "template_id": "template-uuid",
        ...         "resume_id": "resume-uuid",
        ...         "evaluator_id": "evaluator-uuid",
        ...         "criteria_responses": [
        ...             {
        ...                 "criteria_id": "criteria-uuid",
        ...                 "score": 4.0,
        ...                 "comments": "Strong technical skills"
        ...             }
        ...         ],
        ...         "status": "in_progress"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(
            f"Creating scorecard for template: {request.template_id}, "
            f"resume: {request.resume_id}"
        )

        # Verify template exists
        template_result = await db.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == UUID(request.template_id))
        )
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation template not found: {request.template_id}",
            )

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(request.resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {request.resume_id}",
            )

        # Convert criteria_responses to the format expected by the database
        criteria_responses_dict = {}
        for response in request.criteria_responses:
            criteria_responses_dict[response.criteria_id] = {
                "score": response.score,
                "comments": response.comments,
            }

        # Create new scorecard
        new_scorecard = EvaluationScorecard(
            template_id=UUID(request.template_id),
            resume_id=UUID(request.resume_id),
            evaluator_id=UUID(request.evaluator_id) if request.evaluator_id else None,
            criteria_responses=criteria_responses_dict,
            overall_score=request.overall_score,
            status=request.status,
            evaluator_comments=request.evaluator_comments,
            extra_metadata=request.extra_metadata,
        )
        db.add(new_scorecard)
        await db.flush()

        # Convert criteria_responses back to list format for response
        response_criteria = [
            {
                "criteria_id": criteria_id,
                "score": data["score"],
                "comments": data.get("comments"),
            }
            for criteria_id, data in new_scorecard.criteria_responses.items()
        ]

        response_data = {
            "id": str(new_scorecard.id),
            "template_id": str(new_scorecard.template_id),
            "resume_id": str(new_scorecard.resume_id),
            "evaluator_id": str(new_scorecard.evaluator_id) if new_scorecard.evaluator_id else None,
            "criteria_responses": response_criteria,
            "overall_score": float(new_scorecard.overall_score) if new_scorecard.overall_score else None,
            "status": new_scorecard.status,
            "evaluator_comments": new_scorecard.evaluator_comments,
            "extra_metadata": new_scorecard.extra_metadata,
            "created_at": new_scorecard.created_at.isoformat(),
            "updated_at": new_scorecard.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created scorecard with ID: {new_scorecard.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error creating scorecard: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scorecard: {str(e)}",
        ) from e


@router.get("/", tags=["Evaluation Scorecards"])
async def list_scorecards(
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    resume_id: Optional[str] = Query(None, description="Filter by resume ID"),
    evaluator_id: Optional[str] = Query(None, description="Filter by evaluator ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List evaluation scorecards with optional filters.

    This endpoint retrieves scorecards with support for filtering by template,
    resume, evaluator, and status.

    Args:
        template_id: Optional template ID filter
        resume_id: Optional resume ID filter
        evaluator_id: Optional evaluator ID filter
        status: Optional status filter
        db: Database session

    Returns:
        JSON response with list of scorecards

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/evaluation-scorecards/?resume_id=resume-uuid")
        >>> response.json()
        {
            "scorecards": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(
            f"Listing scorecards with filters - template_id: {template_id}, "
            f"resume_id: {resume_id}, evaluator_id: {evaluator_id}, status: {status}"
        )

        # Build query
        query = select(EvaluationScorecard)

        if template_id:
            query = query.where(EvaluationScorecard.template_id == UUID(template_id))
        if resume_id:
            query = query.where(EvaluationScorecard.resume_id == UUID(resume_id))
        if evaluator_id:
            query = query.where(EvaluationScorecard.evaluator_id == UUID(evaluator_id))
        if status:
            query = query.where(EvaluationScorecard.status == status)

        query = query.order_by(EvaluationScorecard.created_at.desc())

        result = await db.execute(query)
        scorecards = result.scalars().all()

        # Build response
        scorecards_data = []
        for scorecard in scorecards:
            # Convert criteria_responses from dict to list
            response_criteria = [
                {
                    "criteria_id": criteria_id,
                    "score": data["score"],
                    "comments": data.get("comments"),
                }
                for criteria_id, data in scorecard.criteria_responses.items()
            ]

            scorecards_data.append({
                "id": str(scorecard.id),
                "template_id": str(scorecard.template_id),
                "resume_id": str(scorecard.resume_id),
                "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
                "criteria_responses": response_criteria,
                "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
                "status": scorecard.status,
                "evaluator_comments": scorecard.evaluator_comments,
                "extra_metadata": scorecard.extra_metadata,
                "created_at": scorecard.created_at.isoformat(),
                "updated_at": scorecard.updated_at.isoformat(),
            })

        response_data = {
            "scorecards": scorecards_data,
            "total_count": len(scorecards_data),
        }

        logger.info(f"Retrieved {len(scorecards_data)} scorecards")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error listing scorecards: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scorecards: {str(e)}",
        ) from e


@router.get(
    "/aggregate",
    response_model=AggregateScoresResponse,
    tags=["Evaluation Scorecards"],
)
async def get_aggregate_scores(
    resume_id: str = Query(..., description="ID of the resume/candidate"),
    template_id: Optional[str] = Query(None, description="Optional filter by template ID"),
    status_filter: Optional[str] = Query(
        None, description="Optional status filter (e.g., 'completed')"
    ),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get aggregate score calculations for a candidate across all evaluators.

    This endpoint calculates and returns aggregate scores for a candidate based on
    all evaluation scorecards. It includes average scores across evaluators,
    weighted scores using template criteria weights, and per-evaluator breakdowns.

    Args:
        resume_id: ID of the resume/candidate
        template_id: Optional filter by template ID
        status_filter: Optional status filter (e.g., 'completed')
        db: Database session

    Returns:
        JSON response with aggregate score calculations

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/evaluation-scorecards/aggregate?resume_id=resume-123"
        ... )
        >>> response.json()
        {
            "resume_id": "resume-123",
            "total_evaluators": 3,
            "average_scores": {
                "criteria-1": 4.0,
                "criteria-2": 3.67
            },
            "overall_average": 3.83,
            "weighted_score": 3.91,
            "scores_by_evaluator": [
                {
                    "evaluator_id": "evaluator-1",
                    "overall_score": 4.0,
                    "criteria_scores": {"criteria-1": 4.0, "criteria-2": 4.0},
                    "status": "completed",
                    "scorecard_id": "scorecard-1"
                }
            ],
            "completion_rate": 0.67
        }
    """
    try:
        logger.info(
            f"Calculating aggregate scores for resume: {resume_id}, "
            f"template_id: {template_id}, status_filter: {status_filter}"
        )

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Build query for scorecards
        query = select(EvaluationScorecard).where(EvaluationScorecard.resume_id == UUID(resume_id))

        if template_id:
            query = query.where(EvaluationScorecard.template_id == UUID(template_id))

        if status_filter:
            query = query.where(EvaluationScorecard.status == status_filter)

        result = await db.execute(query)
        scorecards = result.scalars().all()

        if not scorecards:
            logger.info(f"No scorecards found for resume: {resume_id}")
            # Return empty aggregation
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "resume_id": resume_id,
                    "total_evaluators": 0,
                    "average_scores": {},
                    "overall_average": 0.0,
                    "weighted_score": 0.0,
                    "scores_by_evaluator": [],
                    "completion_rate": 0.0,
                },
            )

        # Get criteria weights from the template
        # Use the first scorecard's template (all should use the same template if template_id was specified)
        template_id_for_criteria = scorecards[0].template_id

        criteria_result = await db.execute(
            select(EvaluationCriteria).where(
                EvaluationCriteria.template_id == template_id_for_criteria
            )
        )
        all_criteria = criteria_result.scalars().all()

        # Build criteria weight map: criteria_id -> weight
        criteria_weights = {
            str(criteria.id): float(criteria.weight) for criteria in all_criteria
        }

        # Calculate aggregate scores
        total_evaluators = len(scorecards)
        criteria_scores_sum = {}  # criteria_id -> sum of scores
        criteria_counts = {}  # criteria_id -> count of evaluators who scored this criteria

        scores_by_evaluator = []
        overall_scores = []

        completed_count = 0

        for scorecard in scorecards:
            if scorecard.status == "completed":
                completed_count += 1

            # Build evaluator breakdown
            evaluator_scores = {
                criteria_id: data["score"]
                for criteria_id, data in scorecard.criteria_responses.items()
            }

            # Add to scores_by_evaluator
            scores_by_evaluator.append({
                "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
                "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
                "criteria_scores": evaluator_scores,
                "status": scorecard.status,
                "scorecard_id": str(scorecard.id),
            })

            # Track overall score if present
            if scorecard.overall_score is not None:
                overall_scores.append(float(scorecard.overall_score))

            # Aggregate criteria scores
            for criteria_id, data in scorecard.criteria_responses.items():
                score = data["score"]
                if criteria_id not in criteria_scores_sum:
                    criteria_scores_sum[criteria_id] = 0.0
                    criteria_counts[criteria_id] = 0
                criteria_scores_sum[criteria_id] += score
                criteria_counts[criteria_id] += 1

        # Calculate average scores per criteria
        average_scores = {
            criteria_id: criteria_scores_sum[criteria_id] / criteria_counts[criteria_id]
            for criteria_id in criteria_scores_sum
        }

        # Calculate overall average
        overall_average = (
            sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        )

        # Calculate weighted score
        # Weighted score = sum(average_score * weight) / sum(weights)
        weighted_sum = 0.0
        total_weight = 0.0

        for criteria_id, avg_score in average_scores.items():
            weight = criteria_weights.get(criteria_id, 1.0)  # Default weight if not found
            weighted_sum += avg_score * weight
            total_weight += weight

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Calculate completion rate
        completion_rate = completed_count / total_evaluators if total_evaluators > 0 else 0.0

        response_data = {
            "resume_id": resume_id,
            "total_evaluators": total_evaluators,
            "average_scores": average_scores,
            "overall_average": round(overall_average, 2),
            "weighted_score": round(weighted_score, 2),
            "scores_by_evaluator": scores_by_evaluator,
            "completion_rate": round(completion_rate, 2),
        }

        logger.info(
            f"Calculated aggregate scores for resume: {resume_id} - "
            f"total_evaluators: {total_evaluators}, overall_average: {response_data['overall_average']}, "
            f"weighted_score: {response_data['weighted_score']}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error calculating aggregate scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate aggregate scores: {str(e)}",
        ) from e


@router.get(
    "/compare",
    response_model=ScorecardComparisonResponse,
    tags=["Evaluation Scorecards"],
)
async def compare_scorecards(
    resume_ids: str = Query(..., description="Comma-separated list of resume IDs to compare (2-5 candidates)"),
    template_id: str = Query(..., description="ID of the evaluation template to compare against"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Compare evaluation scorecards for multiple candidates side-by-side.

    This endpoint retrieves and compares scorecards for multiple candidates
    based on the same evaluation template. It provides a side-by-side view
    of how different evaluators rated each candidate across the same criteria.

    Features:
    - Side-by-side comparison of candidate scorecards
    - Average score calculation per candidate
    - Template criteria included for reference
    - Supports 2-5 candidates per comparison

    Args:
        resume_ids: Comma-separated list of resume IDs (2-5 candidates)
        template_id: ID of the evaluation template
        db: Database session

    Returns:
        JSON response with side-by-side comparison data

    Raises:
        HTTPException(404): If template or any resume is not found
        HTTPException(422): If validation fails (e.g., invalid resume count)
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/evaluation-scorecards/compare?resume_ids=resume-1,resume-2,resume-3&template_id=template-123"
        ... )
        >>> response.json()
        {
            "template_id": "template-123",
            "template_name": "Technical Interview Template",
            "candidates": [
                {
                    "resume_id": "resume-1",
                    "scorecards": [...],
                    "total_evaluators": 2,
                    "average_overall_score": 4.25
                },
                {
                    "resume_id": "resume-2",
                    "scorecards": [...],
                    "total_evaluators": 3,
                    "average_overall_score": 3.92
                }
            ],
            "total_candidates": 2,
            "comparison_criteria": [...],
            "created_at": "2024-01-25T10:30:00Z"
        }
    """
    try:
        logger.info(
            f"Comparing scorecards for resume_ids: {resume_ids}, template_id: {template_id}"
        )

        # Parse and validate resume_ids
        resume_id_list = [rid.strip() for rid in resume_ids.split(",") if rid.strip()]

        if len(resume_id_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least 2 resumes must be provided for comparison",
            )
        if len(resume_id_list) > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Maximum 5 resumes can be compared at once",
            )

        # Verify template exists
        template_result = await db.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == UUID(template_id))
        )
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation template not found: {template_id}",
            )

        # Get criteria from template for comparison reference
        criteria_result = await db.execute(
            select(EvaluationCriteria).where(
                EvaluationCriteria.template_id == UUID(template_id)
            ).order_by(EvaluationCriteria.display_order)
        )
        criteria_list = criteria_result.scalars().all()

        comparison_criteria = [
            {
                "id": str(criteria.id),
                "name": criteria.name,
                "description": criteria.description,
                "criteria_type": criteria.criteria_type,
                "weight": float(criteria.weight) if criteria.weight else 1.0,
                "min_score": float(criteria.min_score) if criteria.min_score else 0,
                "max_score": float(criteria.max_score) if criteria.max_score else 5,
            }
            for criteria in criteria_list
        ]

        # Build comparison data for each candidate
        candidates_data = []

        for resume_id in resume_id_list:
            try:
                # Verify resume exists
                resume_result = await db.execute(
                    select(Resume).where(Resume.id == UUID(resume_id))
                )
                resume = resume_result.scalar_one_or_none()

                if not resume:
                    logger.warning(f"Resume not found: {resume_id}, skipping")
                    continue

                # Get all scorecards for this resume with this template
                scorecards_result = await db.execute(
                    select(EvaluationScorecard).where(
                        EvaluationScorecard.resume_id == UUID(resume_id),
                        EvaluationScorecard.template_id == UUID(template_id)
                    ).order_by(EvaluationScorecard.created_at.desc())
                )
                scorecards = scorecards_result.scalars().all()

                # Convert scorecards to response format
                scorecard_responses = []
                total_evaluators = len(scorecards)
                overall_scores = []

                for scorecard in scorecards:
                    # Convert criteria_responses from dict to list
                    response_criteria = [
                        {
                            "criteria_id": criteria_id,
                            "score": data["score"],
                            "comments": data.get("comments"),
                        }
                        for criteria_id, data in scorecard.criteria_responses.items()
                    ]

                    scorecard_responses.append({
                        "id": str(scorecard.id),
                        "template_id": str(scorecard.template_id),
                        "resume_id": str(scorecard.resume_id),
                        "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
                        "criteria_responses": response_criteria,
                        "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
                        "status": scorecard.status,
                        "evaluator_comments": scorecard.evaluator_comments,
                        "extra_metadata": scorecard.extra_metadata,
                        "created_at": scorecard.created_at.isoformat(),
                        "updated_at": scorecard.updated_at.isoformat(),
                    })

                    # Track overall score for average calculation
                    if scorecard.overall_score is not None:
                        overall_scores.append(float(scorecard.overall_score))

                # Calculate average overall score
                average_overall_score = (
                    sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
                )

                candidates_data.append({
                    "resume_id": resume_id,
                    "scorecards": scorecard_responses,
                    "total_evaluators": total_evaluators,
                    "average_overall_score": round(average_overall_score, 2),
                })

            except ValueError:
                logger.warning(f"Invalid resume_id format: {resume_id}, skipping")
                continue
            except Exception as e:
                logger.error(f"Error processing resume {resume_id}: {e}", exc_info=True)
                continue

        # Check if we have any valid candidates
        if not candidates_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid resumes found or no scorecards exist for the specified resumes and template",
            )

        # Build response
        response_data = {
            "template_id": template_id,
            "template_name": template.name,
            "candidates": candidates_data,
            "total_candidates": len(candidates_data),
            "comparison_criteria": comparison_criteria,
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Generated comparison for {len(candidates_data)} candidates using template: {template_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error comparing scorecards: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare scorecards: {str(e)}",
        ) from e


@router.get("/{scorecard_id}", tags=["Evaluation Scorecards"])
async def get_scorecard(
    scorecard_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific evaluation scorecard by ID.

    This endpoint retrieves detailed information about a single scorecard.

    Args:
        scorecard_id: UUID of the scorecard
        db: Database session

    Returns:
        JSON response with scorecard details

    Raises:
        HTTPException(404): If scorecard is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/evaluation-scorecards/scorecard-uuid")
        >>> response.json()
        {
            "id": "scorecard-uuid",
            "template_id": "template-uuid",
            "resume_id": "resume-uuid",
            ...
        }
    """
    try:
        logger.info(f"Retrieving scorecard: {scorecard_id}")

        result = await db.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.id == UUID(scorecard_id))
        )
        scorecard = result.scalar_one_or_none()

        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation scorecard not found: {scorecard_id}",
            )

        # Convert criteria_responses from dict to list
        response_criteria = [
            {
                "criteria_id": criteria_id,
                "score": data["score"],
                "comments": data.get("comments"),
            }
            for criteria_id, data in scorecard.criteria_responses.items()
        ]

        response_data = {
            "id": str(scorecard.id),
            "template_id": str(scorecard.template_id),
            "resume_id": str(scorecard.resume_id),
            "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
            "criteria_responses": response_criteria,
            "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
            "status": scorecard.status,
            "evaluator_comments": scorecard.evaluator_comments,
            "extra_metadata": scorecard.extra_metadata,
            "created_at": scorecard.created_at.isoformat(),
            "updated_at": scorecard.updated_at.isoformat(),
        }

        logger.info(f"Retrieved scorecard: {scorecard_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {scorecard_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving scorecard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scorecard: {str(e)}",
        ) from e


@router.put("/{scorecard_id}", tags=["Evaluation Scorecards"])
async def update_scorecard(
    scorecard_id: str,
    request: ScorecardUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an evaluation scorecard.

    This endpoint updates an existing scorecard. Only the fields specified
    in the request body will be updated.

    Args:
        scorecard_id: UUID of the scorecard
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated scorecard details

    Raises:
        HTTPException(404): If scorecard is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/evaluation-scorecards/scorecard-uuid",
        ...     json={
        ...         "status": "completed",
        ...         "overall_score": 4.5,
        ...         "evaluator_comments": "Excellent candidate"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "scorecard-uuid",
            "status": "completed",
            "overall_score": 4.5,
            ...
        }
    """
    try:
        logger.info(f"Updating scorecard: {scorecard_id}")

        # Get existing scorecard
        result = await db.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.id == UUID(scorecard_id))
        )
        scorecard = result.scalar_one_or_none()

        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation scorecard not found: {scorecard_id}",
            )

        # Update fields if provided
        if request.criteria_responses is not None:
            # Convert to dict format
            criteria_responses_dict = {}
            for response in request.criteria_responses:
                criteria_responses_dict[response.criteria_id] = {
                    "score": response.score,
                    "comments": response.comments,
                }
            scorecard.criteria_responses = criteria_responses_dict

        if request.overall_score is not None:
            scorecard.overall_score = request.overall_score
        if request.status is not None:
            scorecard.status = request.status
        if request.evaluator_comments is not None:
            scorecard.evaluator_comments = request.evaluator_comments
        if request.extra_metadata is not None:
            scorecard.extra_metadata = request.extra_metadata

        await db.commit()
        await db.refresh(scorecard)

        # Convert criteria_responses from dict to list
        response_criteria = [
            {
                "criteria_id": criteria_id,
                "score": data["score"],
                "comments": data.get("comments"),
            }
            for criteria_id, data in scorecard.criteria_responses.items()
        ]

        response_data = {
            "id": str(scorecard.id),
            "template_id": str(scorecard.template_id),
            "resume_id": str(scorecard.resume_id),
            "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
            "criteria_responses": response_criteria,
            "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
            "status": scorecard.status,
            "evaluator_comments": scorecard.evaluator_comments,
            "extra_metadata": scorecard.extra_metadata,
            "created_at": scorecard.created_at.isoformat(),
            "updated_at": scorecard.updated_at.isoformat(),
        }

        logger.info(f"Updated scorecard: {scorecard_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {scorecard_id}",
        )
    except Exception as e:
        logger.error(f"Error updating scorecard: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scorecard: {str(e)}",
        ) from e


@router.delete("/{scorecard_id}", tags=["Evaluation Scorecards"])
async def delete_scorecard(
    scorecard_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete an evaluation scorecard.

    This endpoint permanently deletes a scorecard. This action cannot be undone.

    Args:
        scorecard_id: UUID of the scorecard
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If scorecard is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/evaluation-scorecards/scorecard-uuid")
        >>> response.json()
        {
            "message": "Evaluation scorecard deleted successfully",
            "id": "scorecard-uuid"
        }
    """
    try:
        logger.info(f"Deleting scorecard: {scorecard_id}")

        # Check if scorecard exists
        result = await db.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.id == UUID(scorecard_id))
        )
        scorecard = result.scalar_one_or_none()

        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation scorecard not found: {scorecard_id}",
            )

        # Delete the scorecard
        await db.execute(
            delete(EvaluationScorecard).where(EvaluationScorecard.id == UUID(scorecard_id))
        )
        await db.commit()

        logger.info(f"Deleted scorecard: {scorecard_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Evaluation scorecard deleted successfully",
                "id": scorecard_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {scorecard_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting scorecard: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scorecard: {str(e)}",
        ) from e


@router.patch("/{scorecard_id}/status", tags=["Evaluation Scorecards"])
async def update_scorecard_status(
    scorecard_id: str,
    request: ScorecardStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the status of an evaluation scorecard.

    This endpoint allows updating just the status of a scorecard, which is useful
    for tracking completion progress without modifying other fields. Valid statuses
    are: 'draft', 'in_progress', and 'completed'.

    Args:
        scorecard_id: UUID of the scorecard
        request: Request body containing the new status
        db: Database session

    Returns:
        JSON response with updated scorecard details

    Raises:
        HTTPException(404): If scorecard is not found
        HTTPException(400): If status is invalid
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.patch(
        ...     "http://localhost:8000/api/evaluation-scorecards/scorecard-uuid/status",
        ...     json={"status": "completed"}
        ... )
        >>> response.status_code
        200
        >>> response.json()
        {
            "id": "scorecard-uuid",
            "status": "completed",
            ...
        }
    """
    try:
        logger.info(f"Updating scorecard status: {scorecard_id} -> {request.status}")

        # Validate status value
        valid_statuses = ["draft", "in_progress", "completed"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}. "
                       f"Valid statuses are: {', '.join(valid_statuses)}",
            )

        # Get existing scorecard
        result = await db.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.id == UUID(scorecard_id))
        )
        scorecard = result.scalar_one_or_none()

        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation scorecard not found: {scorecard_id}",
            )

        # Update status
        scorecard.status = request.status
        await db.commit()
        await db.refresh(scorecard)

        # Convert criteria_responses from dict to list
        response_criteria = [
            {
                "criteria_id": criteria_id,
                "score": data["score"],
                "comments": data.get("comments"),
            }
            for criteria_id, data in scorecard.criteria_responses.items()
        ]

        response_data = {
            "id": str(scorecard.id),
            "template_id": str(scorecard.template_id),
            "resume_id": str(scorecard.resume_id),
            "evaluator_id": str(scorecard.evaluator_id) if scorecard.evaluator_id else None,
            "criteria_responses": response_criteria,
            "overall_score": float(scorecard.overall_score) if scorecard.overall_score else None,
            "status": scorecard.status,
            "evaluator_comments": scorecard.evaluator_comments,
            "extra_metadata": scorecard.extra_metadata,
            "created_at": scorecard.created_at.isoformat(),
            "updated_at": scorecard.updated_at.isoformat(),
        }

        logger.info(f"Updated scorecard status: {scorecard_id} -> {request.status}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {scorecard_id}",
        )
    except Exception as e:
        logger.error(f"Error updating scorecard status: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scorecard status: {str(e)}",
        ) from e
