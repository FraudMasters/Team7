"""
Candidate Portal API endpoints for dashboard data aggregation.

This module provides endpoints for the candidate self-service portal,
aggregating data from applications, interviews, documents, and communications
into unified dashboard views.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_application import JobApplication, ApplicationStatus
from models.job_vacancy import JobVacancy
from models.interview import Interview, InterviewStatus
from models.candidate_document import CandidateDocument, DocumentType
from models.user import User
from dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class ApplicationSummaryItem(BaseModel):
    """Summary of a job application for dashboard display."""

    id: str = Field(..., description="Application ID")
    vacancy_id: str = Field(..., description="Vacancy ID")
    vacancy_title: str = Field(..., description="Job title")
    status: str = Field(..., description="Application status")
    submitted_at: str = Field(..., description="Submission timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class InterviewSummaryItem(BaseModel):
    """Summary of an upcoming interview for dashboard display."""

    id: str = Field(..., description="Interview ID")
    title: str = Field(..., description="Interview title")
    interview_type: str = Field(..., description="Type of interview")
    scheduled_start: str = Field(..., description="Interview start time")
    scheduled_end: str = Field(..., description="Interview end time")
    status: str = Field(..., description="Interview status")
    location: Optional[str] = Field(None, description="Physical location")
    meeting_link: Optional[str] = Field(None, description="Virtual meeting link")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Related job title")


class DocumentSummaryItem(BaseModel):
    """Summary of a candidate document for dashboard display."""

    id: str = Field(..., description="Document ID")
    document_type: str = Field(..., description="Type of document")
    filename: str = Field(..., description="Original filename")
    description: Optional[str] = Field(None, description="Document description")
    uploaded_at: str = Field(..., description="Upload timestamp")


class ApplicationStats(BaseModel):
    """Statistics about candidate's applications."""

    total: int = Field(..., description="Total number of applications")
    pending: int = Field(0, description="Applications in PENDING status")
    submitted: int = Field(0, description="Applications in SUBMITTED status")
    under_review: int = Field(0, description="Applications in UNDER_REVIEW status")
    accepted: int = Field(0, description="Applications ACCEPTED")
    rejected: int = Field(0, description="Applications REJECTED")


class DashboardResponse(BaseModel):
    """Unified dashboard data for candidate portal."""

    user_id: str = Field(..., description="Candidate user ID")
    applications: List[ApplicationSummaryItem] = Field(..., description="Recent applications")
    application_stats: ApplicationStats = Field(..., description="Application statistics")
    upcoming_interviews: List[InterviewSummaryItem] = Field(..., description="Upcoming interviews")
    recent_documents: List[DocumentSummaryItem] = Field(..., description="Recently uploaded documents")
    total_documents: int = Field(..., description="Total document count")


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["Candidate Portal"],
)
async def get_candidate_dashboard(
    request: Request,
    limit: int = Query(10, ge=1, le=100, description="Max items per section"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get unified dashboard data for authenticated candidate.

    Aggregates key data from multiple sources to provide a comprehensive
    overview of the candidate's current status:
    - Recent job applications with status
    - Application statistics by status
    - Upcoming scheduled interviews
    - Recently uploaded documents

    Args:
        request: FastAPI request object
        limit: Maximum number of items to return per section (default: 10)
        db: Database session
        current_user: Authenticated user (candidate)

    Returns:
        JSON response with aggregated dashboard data

    Raises:
        HTTPException(401): If user is not authenticated
        HTTPException(500): If data retrieval fails

    Example:
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidate-portal/dashboard",
        ...     headers={"Authorization": f"Bearer {token}"}
        ... )
        >>> data = response.json()
        >>> print(f"You have {data['application_stats']['total']} applications")
    """
    try:
        user_id = current_user.id

        # Fetch recent applications with vacancy details
        applications_query = (
            select(JobApplication, JobVacancy.title)
            .outerjoin(JobVacancy, JobApplication.vacancy_id == JobVacancy.id)
            .where(JobApplication.user_id == user_id)
            .order_by(JobApplication.created_at.desc())
            .limit(limit)
        )
        applications_result = await db.execute(applications_query)
        applications_data = applications_result.all()

        applications = [
            ApplicationSummaryItem(
                id=str(app.id),
                vacancy_id=str(app.vacancy_id),
                vacancy_title=vacancy_title or "Unknown Position",
                status=app.status.value,
                submitted_at=app.created_at.isoformat() if app.created_at else None,
                updated_at=app.updated_at.isoformat() if app.updated_at else None,
            )
            for app, vacancy_title in applications_data
        ]

        # Fetch application statistics
        stats_query = (
            select(
                JobApplication.status,
                func.count(JobApplication.id).label("count")
            )
            .where(JobApplication.user_id == user_id)
            .group_by(JobApplication.status)
        )
        stats_result = await db.execute(stats_query)
        stats_data = stats_result.all()

        # Build stats dict
        stats_dict = {stat.value: 0 for stat in ApplicationStatus}
        for status_value, count in stats_data:
            stats_dict[status_value.value] = count

        application_stats = ApplicationStats(
            total=sum(stats_dict.values()),
            pending=stats_dict.get(ApplicationStatus.PENDING.value, 0),
            submitted=stats_dict.get(ApplicationStatus.SUBMITTED.value, 0),
            under_review=stats_dict.get(ApplicationStatus.UNDER_REVIEW.value, 0),
            accepted=stats_dict.get(ApplicationStatus.ACCEPTED.value, 0),
            rejected=stats_dict.get(ApplicationStatus.REJECTED.value, 0),
        )

        # Fetch upcoming interviews
        # First, get candidate's resume IDs (interviews are linked to resumes)
        from models.resume import Resume
        resume_query = select(Resume.id).where(Resume.user_id == user_id)
        resume_result = await db.execute(resume_query)
        resume_ids = [row[0] for row in resume_result.all()]

        if resume_ids:
            now = datetime.now(timezone.utc)
            interviews_query = (
                select(Interview, JobVacancy.title)
                .outerjoin(JobVacancy, Interview.vacancy_id == JobVacancy.id)
                .where(
                    and_(
                        Interview.candidate_id.in_(resume_ids),
                        Interview.scheduled_start >= now,
                        Interview.status.in_([
                            InterviewStatus.SCHEDULED,
                            InterviewStatus.CONFIRMED,
                            InterviewStatus.RESCHEDULED
                        ])
                    )
                )
                .order_by(Interview.scheduled_start.asc())
                .limit(limit)
            )
            interviews_result = await db.execute(interviews_query)
            interviews_data = interviews_result.all()

            upcoming_interviews = [
                InterviewSummaryItem(
                    id=str(interview.id),
                    title=interview.title,
                    interview_type=interview.interview_type.value,
                    scheduled_start=interview.scheduled_start.isoformat(),
                    scheduled_end=interview.scheduled_end.isoformat(),
                    status=interview.status.value,
                    location=interview.location,
                    meeting_link=interview.meeting_link,
                    vacancy_id=str(interview.vacancy_id) if interview.vacancy_id else None,
                    vacancy_title=vacancy_title,
                )
                for interview, vacancy_title in interviews_data
            ]
        else:
            upcoming_interviews = []

        # Fetch recent documents
        documents_query = (
            select(CandidateDocument)
            .where(CandidateDocument.user_id == user_id)
            .order_by(CandidateDocument.created_at.desc())
            .limit(limit)
        )
        documents_result = await db.execute(documents_query)
        documents_data = documents_result.scalars().all()

        recent_documents = [
            DocumentSummaryItem(
                id=str(doc.id),
                document_type=doc.document_type.value,
                filename=doc.filename,
                description=doc.description,
                uploaded_at=doc.created_at.isoformat() if doc.created_at else None,
            )
            for doc in documents_data
        ]

        # Get total document count
        total_docs_query = (
            select(func.count(CandidateDocument.id))
            .where(CandidateDocument.user_id == user_id)
        )
        total_docs_result = await db.execute(total_docs_query)
        total_documents = total_docs_result.scalar() or 0

        # Build response
        response_data = DashboardResponse(
            user_id=str(user_id),
            applications=applications,
            application_stats=application_stats,
            upcoming_interviews=upcoming_interviews,
            recent_documents=recent_documents,
            total_documents=total_documents,
        )

        logger.info(
            f"Dashboard data retrieved for user {user_id}: "
            f"{len(applications)} applications, "
            f"{len(upcoming_interviews)} interviews, "
            f"{len(recent_documents)} documents"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except Exception as e:
        logger.error(f"Failed to retrieve dashboard data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


@router.get(
    "/applications",
    response_model=List[ApplicationSummaryItem],
    tags=["Candidate Portal"],
)
async def get_candidate_applications(
    request: Request,
    status_filter: Optional[str] = Query(None, description="Filter by application status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get all applications for authenticated candidate with optional filtering.

    Args:
        request: FastAPI request object
        status_filter: Optional status to filter applications (e.g., "SUBMITTED", "UNDER_REVIEW")
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user (candidate)

    Returns:
        JSON response with list of applications

    Raises:
        HTTPException(400): Invalid status filter
        HTTPException(401): If user is not authenticated
        HTTPException(500): If data retrieval fails

    Example:
        >>> # Get all submitted applications
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidate-portal/applications",
        ...     params={"status_filter": "SUBMITTED"},
        ...     headers={"Authorization": f"Bearer {token}"}
        ... )
    """
    try:
        user_id = current_user.id

        # Build query
        query = (
            select(JobApplication, JobVacancy.title)
            .outerjoin(JobVacancy, JobApplication.vacancy_id == JobVacancy.id)
            .where(JobApplication.user_id == user_id)
        )

        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = ApplicationStatus(status_filter)
                query = query.where(JobApplication.status == status_enum)
            except ValueError:
                valid_statuses = [s.value for s in ApplicationStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Valid values: {valid_statuses}",
                )

        # Apply pagination and ordering
        query = query.order_by(JobApplication.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        applications_data = result.all()

        # Build response
        applications = [
            ApplicationSummaryItem(
                id=str(app.id),
                vacancy_id=str(app.vacancy_id),
                vacancy_title=vacancy_title or "Unknown Position",
                status=app.status.value,
                submitted_at=app.created_at.isoformat() if app.created_at else None,
                updated_at=app.updated_at.isoformat() if app.updated_at else None,
            )
            for app, vacancy_title in applications_data
        ]

        logger.info(
            f"Retrieved {len(applications)} applications for user {user_id} "
            f"(status_filter={status_filter}, skip={skip}, limit={limit})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=[app.model_dump() for app in applications],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve applications for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications",
        )


@router.get(
    "/interviews",
    response_model=List[InterviewSummaryItem],
    tags=["Candidate Portal"],
)
async def get_candidate_interviews(
    request: Request,
    upcoming_only: bool = Query(True, description="Only show upcoming interviews"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get all interviews for authenticated candidate.

    Args:
        request: FastAPI request object
        upcoming_only: If True, only return future interviews (default: True)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user (candidate)

    Returns:
        JSON response with list of interviews

    Raises:
        HTTPException(401): If user is not authenticated
        HTTPException(500): If data retrieval fails

    Example:
        >>> # Get all upcoming interviews
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidate-portal/interviews",
        ...     headers={"Authorization": f"Bearer {token}"}
        ... )
    """
    try:
        user_id = current_user.id

        # Get candidate's resume IDs (interviews are linked to resumes)
        from models.resume import Resume
        resume_query = select(Resume.id).where(Resume.user_id == user_id)
        resume_result = await db.execute(resume_query)
        resume_ids = [row[0] for row in resume_result.all()]

        if not resume_ids:
            logger.info(f"User {user_id} has no resumes, returning empty interviews list")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=[],
            )

        # Build query
        query = (
            select(Interview, JobVacancy.title)
            .outerjoin(JobVacancy, Interview.vacancy_id == JobVacancy.id)
            .where(Interview.candidate_id.in_(resume_ids))
        )

        # Apply upcoming filter if requested
        if upcoming_only:
            now = datetime.now(timezone.utc)
            query = query.where(Interview.scheduled_start >= now)

        # Apply ordering and pagination
        query = query.order_by(Interview.scheduled_start.asc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        interviews_data = result.all()

        # Build response
        interviews = [
            InterviewSummaryItem(
                id=str(interview.id),
                title=interview.title,
                interview_type=interview.interview_type.value,
                scheduled_start=interview.scheduled_start.isoformat(),
                scheduled_end=interview.scheduled_end.isoformat(),
                status=interview.status.value,
                location=interview.location,
                meeting_link=interview.meeting_link,
                vacancy_id=str(interview.vacancy_id) if interview.vacancy_id else None,
                vacancy_title=vacancy_title,
            )
            for interview, vacancy_title in interviews_data
        ]

        logger.info(
            f"Retrieved {len(interviews)} interviews for user {user_id} "
            f"(upcoming_only={upcoming_only}, skip={skip}, limit={limit})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=[interview.model_dump() for interview in interviews],
        )

    except Exception as e:
        logger.error(f"Failed to retrieve interviews for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interviews",
        )
