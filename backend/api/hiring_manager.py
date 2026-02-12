"""
Hiring Manager Portal API endpoints.

This module provides endpoints for the simplified hiring manager interface,
including:
- Dashboard statistics showing candidates pending review
- Review queue with candidate filtering
- One-click approve/reject actions with optional rationale
- Evaluation summaries showing recruiter feedback and team consensus
- Notifications for candidates requiring manager review

Designed for hiring managers who need quick access to candidate review
without full recruiter administrative features.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.notification import Notification, NotificationType
from models.recruiter import Recruiter

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class PendingReviewStats(BaseModel):
    """Statistics for candidates pending manager review."""

    total_pending: int = Field(..., description="Total candidates awaiting manager review")
    urgent_count: int = Field(..., description="Candidates marked as urgent/priority")
    new_this_week: int = Field(..., description="New candidates added this week")
    average_wait_days: float = Field(..., description="Average days candidates have been waiting")


class VacancyStats(BaseModel):
    """Statistics for a single vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    vacancy_title: str = Field(..., description="Job title")
    pending_review: int = Field(..., description="Candidates pending review for this vacancy")
    total_candidates: int = Field(..., description="Total candidates in pipeline")
    stage: str = Field(..., description="Current hiring stage for the vacancy")


class RecentActivity(BaseModel):
    """Recent activity for the hiring manager."""

    activity_type: str = Field(..., description="Type of activity (approved, rejected, interviewed)")
    candidate_name: str = Field(..., description="Candidate name")
    vacancy_title: str = Field(..., description="Related job title")
    timestamp: str = Field(..., description="When the activity occurred")


class DashboardStatsResponse(BaseModel):
    """Response model for hiring manager dashboard statistics."""

    pending_review: PendingReviewStats = Field(..., description="Pending review statistics")
    my_vacancies: List[VacancyStats] = Field(..., description="Vacancies assigned to this manager")
    recent_activity: List[RecentActivity] = Field(..., description="Recent review activity")
    quick_stats: Dict[str, Any] = Field(..., description="Quick statistics for dashboard cards")


# Review Queue Models
class RecruiterFeedback(BaseModel):
    """Recruiter feedback for a candidate in the review queue."""

    recruiter_name: str = Field(..., description="Name of the recruiter who provided feedback")
    rating: Optional[int] = Field(None, description="Rating given by recruiter (1-5)")
    recommendation: Optional[str] = Field(None, description="Recruiter recommendation (approve/reject/maybe)")
    notes: Optional[str] = Field(None, description="Recruiter notes about the candidate")
    created_at: str = Field(..., description="When the feedback was provided")


class ReviewQueueCandidate(BaseModel):
    """A candidate in the hiring manager's review queue."""

    id: str = Field(..., description="Unique identifier (resume ID)")
    filename: str = Field(..., description="Resume filename")
    candidate_name: Optional[str] = Field(None, description="Candidate name extracted from resume")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Job title for the vacancy")
    current_stage: str = Field(..., description="Current workflow stage")
    stage_name: str = Field(..., description="Display name of current stage")
    priority: Optional[str] = Field(None, description="Priority level (urgent, high, normal, low)")
    days_in_stage: float = Field(..., description="Number of days in current stage")
    match_score: Optional[float] = Field(None, description="AI-calculated match score (0-1)")
    recruiter_feedback: List[RecruiterFeedback] = Field(
        default_factory=list, description="Feedback from recruiters"
    )
    team_consensus: Optional[str] = Field(None, description="Team consensus (approve/reject/mixed)")
    tags: List[str] = Field(default_factory=list, description="Tags assigned to this candidate")
    created_at: str = Field(..., description="When the candidate was added")
    updated_at: str = Field(..., description="Last update timestamp")


class ReviewQueueResponse(BaseModel):
    """Response model for the review queue."""

    total_candidates: int = Field(..., description="Total number of candidates in review queue")
    candidates: List[ReviewQueueCandidate] = Field(..., description="List of candidates awaiting review")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied to this result")
    pagination: Dict[str, int] = Field(..., description="Pagination information (skip, limit, total)")


# Approve/Reject Models
class CandidateApprovalRequest(BaseModel):
    """Request model for approving a candidate."""

    rationale: Optional[str] = Field(None, description="Optional rationale for the approval decision")
    next_stage: Optional[str] = Field(None, description="Optional next stage to move candidate to (default: offer)")


class CandidateRejectionRequest(BaseModel):
    """Request model for rejecting a candidate."""

    rationale: Optional[str] = Field(None, description="Optional rationale for the rejection decision")
    rejection_reason: Optional[str] = Field(None, description="Category of rejection reason (e.g., skills_match, culture_fit, experience)")
    notify_candidate: Optional[bool] = Field(False, description="Whether to send rejection notification to candidate")


class CandidateDecisionResponse(BaseModel):
    """Response model for approve/reject decisions."""

    candidate_id: str = Field(..., description="Candidate (resume) UUID")
    decision: str = Field(..., description="Decision made (approved or rejected)")
    previous_stage: str = Field(..., description="Previous stage of the candidate")
    new_stage: str = Field(..., description="New stage of the candidate")
    rationale: Optional[str] = Field(None, description="Rationale provided for the decision")
    decided_at: str = Field(..., description="Timestamp when the decision was made")
    message: str = Field(..., description="Success message")


# Evaluation Summary Models
class FeedbackSummary(BaseModel):
    """Summary of recruiter feedback for a candidate."""

    total_feedback_count: int = Field(..., description="Total number of feedback entries")
    average_rating: Optional[float] = Field(None, description="Average rating across all feedback (1-5)")
    recommendations_breakdown: Dict[str, int] = Field(
        ..., description="Count of each recommendation type (approve, reject, maybe)"
    )
    feedback_list: List[RecruiterFeedback] = Field(
        default_factory=list, description="List of all feedback entries"
    )


class ConsensusDetails(BaseModel):
    """Details about team consensus on a candidate."""

    consensus: Optional[str] = Field(None, description="Overall consensus (approve, reject, mixed, none)")
    approval_rate: float = Field(..., description="Percentage of approvers (0-100)")
    rejection_rate: float = Field(..., description="Percentage of rejecters (0-100)")
    total_reviewers: int = Field(..., description="Total number of reviewers who provided input")
    unanimous: bool = Field(..., description="Whether all reviewers agree")


class EvaluationSummaryResponse(BaseModel):
    """Response model for evaluation summary."""

    candidate_id: str = Field(..., description="Candidate (resume) UUID")
    candidate_name: Optional[str] = Field(None, description="Candidate name extracted from resume")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Job title for the vacancy")
    current_stage: str = Field(..., description="Current workflow stage")
    match_score: Optional[float] = Field(None, description="AI-calculated match score (0-1)")
    feedback_summary: FeedbackSummary = Field(..., description="Summary of recruiter feedback")
    consensus_details: ConsensusDetails = Field(..., description="Team consensus details")
    screening_tier: Optional[str] = Field(None, description="Screening tier (HIGH_PRIORITY, REVIEW, REJECT)")
    tags: List[str] = Field(default_factory=list, description="Tags assigned to this candidate")
    evaluation_date: str = Field(..., description="When this summary was generated")


# Notification Models
class ManagerReviewNotificationRequest(BaseModel):
    """Request model for creating a manager review notification."""

    manager_id: str = Field(..., description="Hiring manager ID to notify")
    candidate_id: str = Field(..., description="Candidate (resume) UUID requiring review")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    priority: Optional[str] = Field(None, description="Priority level (urgent, high, normal, low)")
    message: Optional[str] = Field(None, description="Custom notification message")


class ManagerReviewNotificationResponse(BaseModel):
    """Response model for manager review notification creation."""

    id: str = Field(..., description="Notification ID")
    recipient_id: str = Field(..., description="Hiring manager ID")
    notification_type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    candidate_id: Optional[str] = Field(None, description="Related candidate ID")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID")
    is_read: bool = Field(..., description="Whether the notification has been read")
    created_at: str = Field(..., description="Creation timestamp")
    result: str = Field(..., description="Success message")


class NotificationListResponse(BaseModel):
    """Response model for listing notifications."""

    id: str = Field(..., description="Notification ID")
    recipient_id: str = Field(..., description="Recipient ID")
    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    is_read: bool = Field(..., description="Whether the notification has been read")
    read_at: Optional[str] = Field(None, description="When the notification was read")
    candidate_id: Optional[str] = Field(None, description="Related candidate ID")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID")
    action_url: Optional[str] = Field(None, description="URL for the notification action")
    created_at: str = Field(..., description="Creation timestamp")


@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    tags=["Hiring Manager"],
)
async def get_dashboard_stats(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get hiring manager dashboard statistics.

    This endpoint provides essential statistics for the hiring manager dashboard,
    including candidates pending review, vacancies assigned to the manager,
    recent activity, and quick stats for dashboard cards.

    The dashboard is designed to give hiring managers a quick overview of
    candidates awaiting their review and decision, without overwhelming them
    with full recruiter administrative features.

    Args:
        request: FastAPI request object
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with dashboard statistics including pending review counts,
        vacancy information, recent activity, and quick stats

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/hiring-manager/dashboard")
        >>> response.json()
        {
            "pending_review": {
                "total_pending": 12,
                "urgent_count": 3,
                "new_this_week": 5,
                "average_wait_days": 2.5
            },
            "my_vacancies": [
                {
                    "vacancy_id": "uuid-123",
                    "vacancy_title": "Senior Software Engineer",
                    "pending_review": 8,
                    "total_candidates": 25,
                    "stage": "interview"
                }
            ],
            "recent_activity": [
                {
                    "activity_type": "approved",
                    "candidate_name": "John Doe",
                    "vacancy_title": "Senior Software Engineer",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            ],
            "quick_stats": {
                "approved_this_month": 8,
                "rejected_this_month": 3,
                "interviews_scheduled": 5,
                "avg_time_to_decision_days": 1.5
            }
        }
    """
    try:
        logger.info(
            f"Fetching hiring manager dashboard stats - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "pending_review": {
                "total_pending": 12,
                "urgent_count": 3,
                "new_this_week": 5,
                "average_wait_days": 2.5,
            },
            "my_vacancies": [
                {
                    "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                    "vacancy_title": "Senior Software Engineer",
                    "pending_review": 8,
                    "total_candidates": 25,
                    "stage": "interview",
                },
                {
                    "vacancy_id": "550e8400-e29b-41d4-a716-446655440002",
                    "vacancy_title": "Product Manager",
                    "pending_review": 4,
                    "total_candidates": 15,
                    "stage": "screening",
                },
            ],
            "recent_activity": [
                {
                    "activity_type": "approved",
                    "candidate_name": "John Doe",
                    "vacancy_title": "Senior Software Engineer",
                    "timestamp": "2024-01-15T10:30:00Z",
                },
                {
                    "activity_type": "rejected",
                    "candidate_name": "Jane Smith",
                    "vacancy_title": "Product Manager",
                    "timestamp": "2024-01-15T09:15:00Z",
                },
                {
                    "activity_type": "interviewed",
                    "candidate_name": "Bob Johnson",
                    "vacancy_title": "Senior Software Engineer",
                    "timestamp": "2024-01-14T14:00:00Z",
                },
            ],
            "quick_stats": {
                "approved_this_month": 8,
                "rejected_this_month": 3,
                "interviews_scheduled": 5,
                "avg_time_to_decision_days": 1.5,
            },
        }

        logger.info("Hiring manager dashboard stats retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving hiring manager dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard stats: {str(e)}",
        ) from e


@router.get(
    "/review-queue",
    response_model=ReviewQueueResponse,
    tags=["Hiring Manager"],
)
async def get_review_queue(
    request: Request,
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    priority: Optional[str] = Query(None, description="Filter by priority (urgent, high, normal, low)"),
    stage_id: Optional[str] = Query(None, description="Filter by workflow stage ID or name"),
    search: Optional[str] = Query(None, description="Search candidates by name or filename"),
    min_match_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum match score filter (0-1)"),
    has_recruiter_feedback: Optional[bool] = Query(None, description="Filter candidates with/without recruiter feedback"),
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
) -> JSONResponse:
    """
    Get the hiring manager's review queue with candidate filtering.

    This endpoint provides a list of candidates awaiting manager review,
    with comprehensive filtering capabilities. The review queue shows
    candidates who have progressed through initial screening and are
    ready for hiring manager decision.

    Supports filtering by:
    - Vacancy: Focus on candidates for specific roles
    - Priority: Urgent/high/normal/low priority candidates
    - Stage: Candidates in specific workflow stages
    - Match score: Candidates meeting minimum AI match threshold
    - Recruiter feedback: Candidates with or without recruiter input
    - Search: Text search on candidate name/filename

    Args:
        request: FastAPI request object
        vacancy_id: Optional filter by vacancy UUID
        priority: Optional filter by priority level (urgent, high, normal, low)
        stage_id: Optional filter by workflow stage ID or name
        search: Optional search term for candidate name/filename
        min_match_score: Optional minimum match score threshold (0.0-1.0)
        has_recruiter_feedback: Optional filter for recruiter feedback presence
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return

    Returns:
        JSON response with filtered list of candidates awaiting review,
        including recruiter feedback and team consensus information

    Raises:
        HTTPException(400): Invalid filter parameter format
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all candidates in review queue
        >>> response = requests.get("/api/hiring-manager/review-queue")
        >>> # Filter by vacancy
        >>> response = requests.get(
        ...     "/api/hiring-manager/review-queue",
        ...     params={"vacancy_id": "550e8400-e29b-41d4-a716-446655440001"}
        ... )
        >>> # Get urgent candidates with high match scores
        >>> response = requests.get(
        ...     "/api/hiring-manager/review-queue",
        ...     params={"priority": "urgent", "min_match_score": 0.8}
        ... )
        >>> response.json()
        {
            "total_candidates": 12,
            "candidates": [
                {
                    "id": "uuid-123",
                    "filename": "john_doe_resume.pdf",
                    "candidate_name": "John Doe",
                    "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                    "vacancy_title": "Senior Software Engineer",
                    "current_stage": "interview",
                    "stage_name": "Manager Review",
                    "priority": "urgent",
                    "days_in_stage": 2.5,
                    "match_score": 0.85,
                    "recruiter_feedback": [
                        {
                            "recruiter_name": "Jane Smith",
                            "rating": 4,
                            "recommendation": "approve",
                            "notes": "Strong technical background",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "team_consensus": "approve",
                    "tags": ["senior", "backend"],
                    "created_at": "2024-01-10T09:00:00Z",
                    "updated_at": "2024-01-15T14:30:00Z"
                }
            ],
            "filters_applied": {
                "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                "priority": "urgent",
                "min_match_score": 0.8
            },
            "pagination": {
                "skip": 0,
                "limit": 50,
                "total": 12
            }
        }
    """
    try:
        logger.info(
            f"Fetching hiring manager review queue - vacancy_id: {vacancy_id}, "
            f"priority: {priority}, stage_id: {stage_id}, search: {search}, "
            f"min_match_score: {min_match_score}, has_recruiter_feedback: {has_recruiter_feedback}, "
            f"skip: {skip}, limit: {limit}"
        )

        # Validate priority if provided
        valid_priorities = ["urgent", "high", "normal", "low"]
        if priority and priority.lower() not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}. Must be one of: {', '.join(valid_priorities)}",
            )

        # For now, return placeholder response with sample data
        # Database integration will be added in a later subtask
        sample_candidates = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "filename": "john_doe_resume.pdf",
                "candidate_name": "John Doe",
                "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                "vacancy_title": "Senior Software Engineer",
                "current_stage": "interview",
                "stage_name": "Manager Review",
                "priority": "urgent",
                "days_in_stage": 2.5,
                "match_score": 0.85,
                "recruiter_feedback": [
                    {
                        "recruiter_name": "Jane Smith",
                        "rating": 4,
                        "recommendation": "approve",
                        "notes": "Strong technical background, good culture fit",
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                ],
                "team_consensus": "approve",
                "tags": ["senior", "backend", "python"],
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-15T14:30:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440011",
                "filename": "jane_smith_cv.pdf",
                "candidate_name": "Jane Smith",
                "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                "vacancy_title": "Senior Software Engineer",
                "current_stage": "interview",
                "stage_name": "Manager Review",
                "priority": "high",
                "days_in_stage": 1.5,
                "match_score": 0.78,
                "recruiter_feedback": [
                    {
                        "recruiter_name": "Mike Johnson",
                        "rating": 5,
                        "recommendation": "approve",
                        "notes": "Excellent experience with distributed systems",
                        "created_at": "2024-01-14T16:00:00Z",
                    },
                    {
                        "recruiter_name": "Sarah Williams",
                        "rating": 4,
                        "recommendation": "approve",
                        "notes": "Great communication skills",
                        "created_at": "2024-01-14T17:30:00Z",
                    },
                ],
                "team_consensus": "approve",
                "tags": ["senior", "fullstack", "aws"],
                "created_at": "2024-01-12T11:00:00Z",
                "updated_at": "2024-01-14T18:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440012",
                "filename": "bob_johnson_resume.pdf",
                "candidate_name": "Bob Johnson",
                "vacancy_id": "550e8400-e29b-41d4-a716-446655440002",
                "vacancy_title": "Product Manager",
                "current_stage": "screening",
                "stage_name": "Technical Screen",
                "priority": "normal",
                "days_in_stage": 3.0,
                "match_score": 0.72,
                "recruiter_feedback": [],
                "team_consensus": None,
                "tags": ["mid-level", "product"],
                "created_at": "2024-01-08T14:00:00Z",
                "updated_at": "2024-01-12T10:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440013",
                "filename": "alice_williams_cv.pdf",
                "candidate_name": "Alice Williams",
                "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
                "vacancy_title": "Senior Software Engineer",
                "current_stage": "interview",
                "stage_name": "Manager Review",
                "priority": "low",
                "days_in_stage": 5.0,
                "match_score": 0.65,
                "recruiter_feedback": [
                    {
                        "recruiter_name": "Jane Smith",
                        "rating": 3,
                        "recommendation": "maybe",
                        "notes": "Good potential but limited experience",
                        "created_at": "2024-01-13T09:00:00Z",
                    }
                ],
                "team_consensus": "mixed",
                "tags": ["mid-level", "frontend"],
                "created_at": "2024-01-05T08:00:00Z",
                "updated_at": "2024-01-10T11:00:00Z",
            },
        ]

        # Apply filters to sample data
        filtered_candidates = sample_candidates

        if vacancy_id:
            filtered_candidates = [
                c for c in filtered_candidates if c["vacancy_id"] == vacancy_id
            ]

        if priority:
            filtered_candidates = [
                c for c in filtered_candidates if c["priority"] == priority.lower()
            ]

        if stage_id:
            # Filter by stage name (simplified for placeholder)
            filtered_candidates = [
                c for c in filtered_candidates
                if stage_id.lower() in c["current_stage"].lower()
            ]

        if search:
            search_lower = search.lower()
            filtered_candidates = [
                c for c in filtered_candidates
                if search_lower in c.get("candidate_name", "").lower()
                or search_lower in c["filename"].lower()
            ]

        if min_match_score is not None:
            filtered_candidates = [
                c for c in filtered_candidates
                if c.get("match_score") is not None and c["match_score"] >= min_match_score
            ]

        if has_recruiter_feedback is not None:
            if has_recruiter_feedback:
                filtered_candidates = [
                    c for c in filtered_candidates
                    if len(c.get("recruiter_feedback", [])) > 0
                ]
            else:
                filtered_candidates = [
                    c for c in filtered_candidates
                    if len(c.get("recruiter_feedback", [])) == 0
                ]

        # Apply pagination
        total_count = len(filtered_candidates)
        paginated_candidates = filtered_candidates[skip:skip + limit]

        # Build filters_applied dict
        filters_applied = {}
        if vacancy_id:
            filters_applied["vacancy_id"] = vacancy_id
        if priority:
            filters_applied["priority"] = priority
        if stage_id:
            filters_applied["stage_id"] = stage_id
        if search:
            filters_applied["search"] = search
        if min_match_score is not None:
            filters_applied["min_match_score"] = min_match_score
        if has_recruiter_feedback is not None:
            filters_applied["has_recruiter_feedback"] = has_recruiter_feedback

        response_data = {
            "total_candidates": total_count,
            "candidates": paginated_candidates,
            "filters_applied": filters_applied,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
            },
        }

        logger.info(f"Review queue retrieved successfully: {len(paginated_candidates)} candidates (of {total_count} total)")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving review queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve review queue: {str(e)}",
        ) from e


@router.post(
    "/candidates/{candidate_id}/approve",
    response_model=CandidateDecisionResponse,
    tags=["Hiring Manager"],
)
async def approve_candidate(
    request: Request,
    candidate_id: str,
    approval_data: CandidateApprovalRequest,
) -> JSONResponse:
    """
    One-click approve a candidate with optional rationale.

    This endpoint allows hiring managers to quickly approve a candidate
    with a single action. The candidate will be moved to the offer stage
    (or a specified next stage) and the decision will be recorded.

    Optionally, a rationale can be provided to document the reasoning
    behind the approval decision for future reference.

    Args:
        request: FastAPI request object
        candidate_id: Resume UUID of the candidate to approve
        approval_data: Approval details including optional rationale and next stage

    Returns:
        JSON response with approval confirmation and updated candidate status

    Raises:
        HTTPException(400): Invalid candidate ID format
        HTTPException(404): Candidate not found
        HTTPException(500): If approval operation fails

    Examples:
        >>> import requests
        >>> # Simple approval
        >>> response = requests.post(
        ...     "/api/hiring-manager/candidates/550e8400-e29b-41d4-a716-446655440010/approve"
        ... )
        >>> # Approval with rationale
        >>> response = requests.post(
        ...     "/api/hiring-manager/candidates/550e8400-e29b-41d4-a716-446655440010/approve",
        ...     json={"rationale": "Excellent technical skills and culture fit"}
        >>> )
        >>> response.json()
        {
            "candidate_id": "550e8400-e29b-41d4-a716-446655440010",
            "decision": "approved",
            "previous_stage": "interview",
            "new_stage": "offer",
            "rationale": "Excellent technical skills and culture fit",
            "decided_at": "2024-01-15T10:30:00Z",
            "message": "Candidate approved successfully"
        }
    """
    try:
        logger.info(
            f"Approving candidate {candidate_id} - rationale: {approval_data.rationale}, "
            f"next_stage: {approval_data.next_stage}"
        )

        # Validate candidate_id format
        from uuid import UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask
        from datetime import datetime, timezone

        previous_stage = "interview"  # Placeholder
        new_stage = approval_data.next_stage or "offer"

        response_data = {
            "candidate_id": candidate_id,
            "decision": "approved",
            "previous_stage": previous_stage,
            "new_stage": new_stage,
            "rationale": approval_data.rationale,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "message": "Candidate approved successfully",
        }

        logger.info(f"Candidate {candidate_id} approved, moved to {new_stage} stage")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve candidate: {str(e)}",
        ) from e


@router.post(
    "/candidates/{candidate_id}/reject",
    response_model=CandidateDecisionResponse,
    tags=["Hiring Manager"],
)
async def reject_candidate(
    request: Request,
    candidate_id: str,
    rejection_data: CandidateRejectionRequest,
) -> JSONResponse:
    """
    One-click reject a candidate with optional rationale.

    This endpoint allows hiring managers to quickly reject a candidate
    with a single action. The candidate will be moved to the rejected stage
    and the decision will be recorded.

    Optionally, a rationale and rejection reason category can be provided
    to document the reasoning behind the rejection decision. This data
    helps with analytics and improving the hiring process.

    Args:
        request: FastAPI request object
        candidate_id: Resume UUID of the candidate to reject
        rejection_data: Rejection details including optional rationale and reason

    Returns:
        JSON response with rejection confirmation and updated candidate status

    Raises:
        HTTPException(400): Invalid candidate ID format
        HTTPException(404): Candidate not found
        HTTPException(500): If rejection operation fails

    Examples:
        >>> import requests
        >>> # Simple rejection
        >>> response = requests.post(
        ...     "/api/hiring-manager/candidates/550e8400-e29b-41d4-a716-446655440010/reject"
        ... )
        >>> # Rejection with rationale
        >>> response = requests.post(
        ...     "/api/hiring-manager/candidates/550e8400-e29b-41d4-a716-446655440010/reject",
        ...     json={
        ...         "rationale": "Insufficient experience with required technologies",
        ...         "rejection_reason": "skills_match"
        ...     }
        >>> )
        >>> response.json()
        {
            "candidate_id": "550e8400-e29b-41d4-a716-446655440010",
            "decision": "rejected",
            "previous_stage": "interview",
            "new_stage": "rejected",
            "rationale": "Insufficient experience with required technologies",
            "decided_at": "2024-01-15T10:30:00Z",
            "message": "Candidate rejected successfully"
        }
    """
    try:
        logger.info(
            f"Rejecting candidate {candidate_id} - rationale: {rejection_data.rationale}, "
            f"reason: {rejection_data.rejection_reason}"
        )

        # Validate candidate_id format
        from uuid import UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Validate rejection_reason if provided
        valid_rejection_reasons = [
            "skills_match",
            "experience",
            "culture_fit",
            "salary_expectations",
            "location",
            "availability",
            "other",
        ]
        if rejection_data.rejection_reason and rejection_data.rejection_reason not in valid_rejection_reasons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rejection reason: {rejection_data.rejection_reason}. "
                       f"Must be one of: {', '.join(valid_rejection_reasons)}",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask
        from datetime import datetime, timezone

        previous_stage = "interview"  # Placeholder
        new_stage = "rejected"

        response_data = {
            "candidate_id": candidate_id,
            "decision": "rejected",
            "previous_stage": previous_stage,
            "new_stage": new_stage,
            "rationale": rejection_data.rationale,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "message": "Candidate rejected successfully",
        }

        logger.info(f"Candidate {candidate_id} rejected")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject candidate: {str(e)}",
        ) from e


@router.get(
    "/candidates/{candidate_id}/evaluation",
    response_model=EvaluationSummaryResponse,
    tags=["Hiring Manager"],
)
async def get_evaluation_summary(
    request: Request,
    candidate_id: str,
) -> JSONResponse:
    """
    Get evaluation summary for a candidate showing recruiter feedback and team consensus.

    This endpoint provides a comprehensive summary of all evaluation activity for a
    candidate, including:
    - All recruiter feedback (ratings, recommendations, notes)
    - Team consensus analysis (approval rates, unanimous decisions)
    - Screening tier information
    - AI match score

    This gives hiring managers a complete picture of how the recruitment team
    views a candidate before making their final decision.

    Args:
        request: FastAPI request object
        candidate_id: Resume UUID of the candidate

    Returns:
        JSON response with evaluation summary including recruiter feedback
        and team consensus information

    Raises:
        HTTPException(400): Invalid candidate ID format
        HTTPException(404): Candidate not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/hiring-manager/candidates/550e8400-e29b-41d4-a716-446655440010/evaluation"
        ... )
        >>> response.json()
        {
            "candidate_id": "550e8400-e29b-41d4-a716-446655440010",
            "candidate_name": "John Doe",
            "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
            "vacancy_title": "Senior Software Engineer",
            "current_stage": "interview",
            "match_score": 0.85,
            "feedback_summary": {
                "total_feedback_count": 3,
                "average_rating": 4.3,
                "recommendations_breakdown": {
                    "approve": 2,
                    "maybe": 1,
                    "reject": 0
                },
                "feedback_list": [
                    {
                        "recruiter_name": "Jane Smith",
                        "rating": 4,
                        "recommendation": "approve",
                        "notes": "Strong technical background",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ]
            },
            "consensus_details": {
                "consensus": "approve",
                "approval_rate": 66.67,
                "rejection_rate": 0.0,
                "total_reviewers": 3,
                "unanimous": false
            },
            "screening_tier": "HIGH_PRIORITY",
            "tags": ["senior", "backend", "python"],
            "evaluation_date": "2024-01-15T15:00:00Z"
        }
    """
    try:
        logger.info(f"Fetching evaluation summary for candidate {candidate_id}")

        # Validate candidate_id format
        from uuid import UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask
        from datetime import datetime, timezone

        # Sample feedback data
        sample_feedback = [
            {
                "recruiter_name": "Jane Smith",
                "rating": 4,
                "recommendation": "approve",
                "notes": "Strong technical background, good culture fit. Demonstrated solid experience with Python and distributed systems.",
                "created_at": "2024-01-15T10:30:00Z",
            },
            {
                "recruiter_name": "Mike Johnson",
                "rating": 5,
                "recommendation": "approve",
                "notes": "Excellent experience with distributed systems. Great communication skills during technical interview.",
                "created_at": "2024-01-14T16:00:00Z",
            },
            {
                "recruiter_name": "Sarah Williams",
                "rating": 4,
                "recommendation": "maybe",
                "notes": "Good overall profile but limited experience with cloud platforms. Recommended for follow-up interview.",
                "created_at": "2024-01-14T17:30:00Z",
            },
        ]

        # Calculate feedback summary
        total_feedback = len(sample_feedback)
        ratings = [f["rating"] for f in sample_feedback if f["rating"] is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else None

        recommendations_breakdown = {"approve": 0, "reject": 0, "maybe": 0}
        for feedback in sample_feedback:
            rec = feedback.get("recommendation")
            if rec and rec in recommendations_breakdown:
                recommendations_breakdown[rec] += 1

        feedback_summary = {
            "total_feedback_count": total_feedback,
            "average_rating": round(average_rating, 2) if average_rating else None,
            "recommendations_breakdown": recommendations_breakdown,
            "feedback_list": sample_feedback,
        }

        # Calculate consensus details
        total_reviewers = total_feedback
        approve_count = recommendations_breakdown["approve"]
        reject_count = recommendations_breakdown["reject"]
        approval_rate = (approve_count / total_reviewers * 100) if total_reviewers > 0 else 0.0
        rejection_rate = (reject_count / total_reviewers * 100) if total_reviewers > 0 else 0.0

        # Determine consensus
        if total_reviewers == 0:
            consensus = "none"
            unanimous = True
        elif approve_count == total_reviewers:
            consensus = "approve"
            unanimous = True
        elif reject_count == total_reviewers:
            consensus = "reject"
            unanimous = True
        else:
            consensus = "mixed"
            unanimous = False

        consensus_details = {
            "consensus": consensus,
            "approval_rate": round(approval_rate, 2),
            "rejection_rate": round(rejection_rate, 2),
            "total_reviewers": total_reviewers,
            "unanimous": unanimous,
        }

        response_data = {
            "candidate_id": candidate_id,
            "candidate_name": "John Doe",
            "vacancy_id": "550e8400-e29b-41d4-a716-446655440001",
            "vacancy_title": "Senior Software Engineer",
            "current_stage": "interview",
            "match_score": 0.85,
            "feedback_summary": feedback_summary,
            "consensus_details": consensus_details,
            "screening_tier": "HIGH_PRIORITY",
            "tags": ["senior", "backend", "python"],
            "evaluation_date": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Evaluation summary retrieved for candidate {candidate_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evaluation summary for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluation summary: {str(e)}",
        ) from e


@router.get(
    "/notifications",
    response_model=List[NotificationListResponse],
    tags=["Hiring Manager"],
)
async def list_manager_notifications(
    request: Request,
    type: Optional[str] = Query(None, description="Filter by notification type (e.g., candidate_review_required)"),
    manager_id: Optional[str] = Query(None, description="Filter by manager ID"),
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List notifications for hiring managers with optional type filtering.

    This endpoint provides a way to retrieve notifications for hiring managers,
    with support for filtering by notification type. The `type` query parameter
    supports the `candidate_review_required` notification type.

    Args:
        request: FastAPI request object
        type: Optional filter by notification type (e.g., candidate_review_required)
        manager_id: Optional filter by manager ID
        unread_only: If True, only return unread notifications
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of notifications

    Raises:
        HTTPException(400): Invalid ID format
        HTTPException(404): Manager not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all candidate_review_required notifications
        >>> response = requests.get(
        ...     "/api/hiring-manager/notifications?type=candidate_review_required"
        ... )
        >>> # Get unread notifications for a specific manager
        >>> response = requests.get(
        ...     "/api/hiring-manager/notifications",
        ...     params={"manager_id": "abc-123-def", "unreadOnly": True}
        ... )
    """
    try:
        logger.info(
            f"Fetching manager notifications - type: {type}, manager_id: {manager_id}, "
            f"unreadOnly: {unread_only}, skip: {skip}, limit: {limit}"
        )

        # Build base query
        query = select(Notification)

        # Filter by notification type if provided
        if type:
            query = query.where(Notification.notification_type == type)

        # Filter by manager_id if provided
        if manager_id:
            try:
                manager_uuid = UUID(manager_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid manager_id format: {manager_id}",
                )

            # Verify manager exists
            manager_query = select(Recruiter).where(Recruiter.id == manager_uuid)
            manager_result = await db.execute(manager_query)
            manager = manager_result.scalar_one_or_none()

            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Manager not found: {manager_id}",
                )

            query = query.where(Notification.recipient_id == manager_uuid)

        # Filter by unread status
        if unread_only:
            query = query.where(Notification.is_read == False)

        # Order by most recently created and paginate
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        notifications = result.scalars().all()

        # Convert to response format
        notifications_list = []
        for notification in notifications:
            notifications_list.append({
                "id": str(notification.id),
                "recipient_id": str(notification.recipient_id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "candidate_id": str(notification.candidate_id) if notification.candidate_id else None,
                "vacancy_id": str(notification.vacancy_id) if notification.vacancy_id else None,
                "action_url": notification.action_url,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
            })

        logger.info(f"Retrieved {len(notifications_list)} notifications")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=notifications_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing manager notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        ) from e


@router.post(
    "/notifications/review-required",
    response_model=ManagerReviewNotificationResponse,
    tags=["Hiring Manager"],
)
async def create_review_required_notification(
    request: Request,
    notification_data: ManagerReviewNotificationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a notification for a candidate requiring manager review.

    This endpoint creates a notification to alert hiring managers when a candidate
    requires their review. This is typically triggered when:
    - A candidate completes the recruiter screening stage
    - A candidate's status changes to pending manager review
    - A candidate is flagged for urgent review

    The notification includes links to the candidate's evaluation summary and
    the review queue for quick access.

    Args:
        request: FastAPI request object
        notification_data: Notification details including manager_id, candidate_id,
                          optional vacancy_id, priority, and custom message
        db: Database session

    Returns:
        JSON response with created notification details

    Raises:
        HTTPException(400): Invalid ID format
        HTTPException(404): Manager not found
        HTTPException(500): If notification creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "manager_id": "550e8400-e29b-41d4-a716-446655440001",
        ...     "candidate_id": "550e8400-e29b-41d4-a716-446655440010",
        ...     "vacancy_id": "550e8400-e29b-41d4-a716-446655440002",
        ...     "priority": "urgent",
        ...     "message": "High-priority candidate awaiting your review"
        ... }
        >>> response = requests.post(
        ...     "/api/hiring-manager/notifications/review-required",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "550e8400-e29b-41d4-a716-446655440099",
            "recipient_id": "550e8400-e29b-41d4-a716-446655440001",
            "notification_type": "candidate_review_required",
            "title": "Candidate Requires Your Review",
            "message": "High-priority candidate awaiting your review",
            "candidate_id": "550e8400-e29b-41d4-a716-446655440010",
            "vacancy_id": "550e8400-e29b-41d4-a716-446655440002",
            "is_read": false,
            "created_at": "2024-01-15T10:30:00Z",
            "result": "Notification created successfully"
        }
    """
    try:
        logger.info(
            f"Creating review required notification for manager: {notification_data.manager_id}, "
            f"candidate: {notification_data.candidate_id}"
        )

        # Validate manager_id format
        try:
            manager_uuid = UUID(notification_data.manager_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid manager_id format: {notification_data.manager_id}",
            )

        # Validate candidate_id format
        try:
            candidate_uuid = UUID(notification_data.candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate_id format: {notification_data.candidate_id}",
            )

        # Validate priority if provided
        valid_priorities = ["urgent", "high", "normal", "low"]
        if notification_data.priority and notification_data.priority.lower() not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {notification_data.priority}. Must be one of: {', '.join(valid_priorities)}",
            )

        # Verify manager exists
        manager_query = select(Recruiter).where(Recruiter.id == manager_uuid)
        manager_result = await db.execute(manager_query)
        manager = manager_result.scalar_one_or_none()

        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manager not found: {notification_data.manager_id}",
            )

        # Parse optional vacancy_id
        vacancy_uuid = None
        if notification_data.vacancy_id:
            try:
                vacancy_uuid = UUID(notification_data.vacancy_id)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {notification_data.vacancy_id}")

        # Build notification title and message
        priority_prefix = ""
        if notification_data.priority:
            priority_lower = notification_data.priority.lower()
            if priority_lower == "urgent":
                priority_prefix = "🚨 URGENT: "
            elif priority_lower == "high":
                priority_prefix = "⚡ HIGH PRIORITY: "

        title = f"{priority_prefix}Candidate Requires Your Review"

        if notification_data.message:
            message = notification_data.message
        else:
            message = "A new candidate is waiting for your review and decision."

        # Build action URL for the review queue
        action_url = f"/hiring-manager/review-queue?candidate_id={notification_data.candidate_id}"

        # Create notification
        notification = Notification(
            recipient_id=manager_uuid,
            notification_type=NotificationType.CANDIDATE_REVIEW_REQUIRED,
            title=title,
            message=message,
            data={
                "priority": notification_data.priority,
                "action_required": "review",
            },
            candidate_id=candidate_uuid,
            vacancy_id=vacancy_uuid,
            action_url=action_url,
            is_read=False,
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            f"Review required notification created: {notification.id} for manager {notification_data.manager_id}"
        )

        # Broadcast to WebSocket clients
        try:
            from api.websocket import broadcast_notification
            connections = await broadcast_notification(notification)
            if connections > 0:
                logger.info(
                    f"Notification {notification.id} broadcast to {connections} "
                    f"WebSocket connection(s)"
                )
        except Exception as broadcast_error:
            # Don't fail the request if broadcast fails
            logger.error(
                f"Failed to broadcast notification {notification.id}: {broadcast_error}",
                exc_info=True
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(notification.id),
                "recipient_id": str(notification.recipient_id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "candidate_id": str(notification.candidate_id) if notification.candidate_id else None,
                "vacancy_id": str(notification.vacancy_id) if notification.vacancy_id else None,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "result": "Notification created successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review required notification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}",
        ) from e
