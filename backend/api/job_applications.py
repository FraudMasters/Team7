"""
Job Application API endpoints for submitting and managing job applications.

This module provides endpoints for job seekers to submit applications,
view their application history, and track application status.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_application import JobApplication, ApplicationStatus
from models.job_vacancy import JobVacancy
from models.resume import Resume
from models.user import User
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context
from dependencies.auth import get_current_user_optional
from services.notification_service import get_notification_service
from models.notification import NotificationType

from config import get_settings
from tasks.notification_tasks import send_application_status_notification

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# Request/Response Models
class JobApplicationSubmitRequest(BaseModel):
    """Request model for submitting a job application."""

    vacancy_id: str = Field(..., description="ID of the vacancy to apply for")
    resume_id: Optional[str] = Field(None, description="ID of the resume to submit")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    cover_letter: Optional[str] = Field(None, max_length=5000, description="Cover letter text")


class JobApplicationResponse(BaseModel):
    """Response model for job application."""

    id: str = Field(..., description="Application ID")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    vacancy_title: Optional[str] = Field(None, description="Title of the vacancy")
    resume_id: Optional[str] = Field(None, description="ID of the resume submitted")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    status: str = Field(..., description="Application status")
    created_at: str = Field(..., description="Submission timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class JobApplicationsListResponse(BaseModel):
    """Response model for listing job applications."""

    applications: list[JobApplicationResponse] = Field(..., description="List of applications")
    total: int = Field(..., description="Total count of applications")
    limit: int = Field(..., description="Page size")
    skip: int = Field(..., description="Number of records skipped")


class UpdateApplicationStatusRequest(BaseModel):
    """Request model for updating application status."""

    status: str = Field(..., description="New application status")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the status change")


class UpdateApplicationStatusResponse(BaseModel):
    """Response model for updating application status."""

    id: str = Field(..., description="Application ID")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    vacancy_title: Optional[str] = Field(None, description="Title of the vacancy")
    email: str = Field(..., description="Contact email")
    status: str = Field(..., description="New application status")
    old_status: str = Field(..., description="Previous application status")
    notification_queued: bool = Field(..., description="Whether notification was queued")
    updated_at: str = Field(..., description="Update timestamp")
    message: str = Field(..., description="Success message")


def _application_to_response(application: JobApplication, vacancy_title: Optional[str] = None) -> dict:
    """Convert JobApplication model to response dict."""
    return {
        "id": str(application.id),
        "vacancy_id": str(application.vacancy_id),
        "vacancy_title": vacancy_title,
        "resume_id": str(application.resume_id) if application.resume_id else None,
        "email": application.email or "",
        "phone": application.phone,
        "cover_letter": application.cover_letter,
        "status": application.status.value,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }


@router.post(
    "/submit",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Job Applications"],
)
async def submit_application(
    request: Request,
    application_data: JobApplicationSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> JSONResponse:
    """
    Submit a job application.

    This endpoint allows job seekers to submit an application for a job vacancy.
    If the user is authenticated, the application is linked to their account.
    Otherwise, it's submitted as a guest application.

    Args:
        request: FastAPI request object
        application_data: Application data from request body
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        JSON response with created application details

    Raises:
        HTTPException(404): If vacancy or resume not found
        HTTPException(400): If validation fails

    Example:
        >>> application_data = {
        ...     "vacancy_id": "vacancy-uuid",
        ...     "resume_id": "resume-uuid",
        ...     "email": "test@example.com",
        ...     "phone": "+1234567890",
        ...     "cover_letter": "I am interested in this position"
        ... }
        >>> response = requests.post("/api/job-applications/submit", json=application_data)
    """
    try:
        # Parse and validate vacancy_id
        try:
            vacancy_uuid = UUID(application_data.vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vacancy ID format",
            )

        # Check if vacancy exists
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found",
            )

        # Validate resume_id if provided
        resume_uuid = None
        if application_data.resume_id:
            try:
                resume_uuid = UUID(application_data.resume_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid resume ID format",
                )

            # Check if resume exists
            resume_query = select(Resume).where(Resume.id == resume_uuid)
            resume_result = await db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume not found",
                )

            # If user is authenticated, verify they own the resume
            if current_user and resume.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Resume does not belong to the authenticated user",
                )

        # Determine user_id
        user_id = current_user.id if current_user else None

        # Check if user already applied for this vacancy
        if user_id:
            existing_query = select(JobApplication).where(
                JobApplication.user_id == user_id,
                JobApplication.vacancy_id == vacancy_uuid
            )
            existing_result = await db.execute(existing_query)
            existing_application = existing_result.scalar_one_or_none()

            if existing_application:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already applied for this vacancy",
                )

        # Create new JobApplication instance
        new_application = JobApplication(
            user_id=user_id,
            vacancy_id=vacancy_uuid,
            resume_id=resume_uuid,
            email=application_data.email,
            phone=application_data.phone,
            cover_letter=application_data.cover_letter,
            status=ApplicationStatus.SUBMITTED,
        )

        db.add(new_application)
        await db.commit()
        await db.refresh(new_application)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.MATCH_CREATED,  # Using existing type for now
            entity_type="job_application",
            entity_id=new_application.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value=_application_to_response(new_application, vacancy.title),
        )

        logger.info(f"Created job application: {new_application.id} for vacancy {vacancy_uuid}")

        # Send notification to recruiters/hiring managers
        try:
            notification_service = get_notification_service()

            # Get all users who should be notified (recruiters, hiring managers)
            # For now, we'll skip this as we need to determine who to notify
            # This could be based on vacancy.created_by or organization members
            logger.info(f"Application notification for vacancy {vacancy.title} - notification sending to be implemented")

            # TODO: Determine which users to notify about the new application
            # This would typically include:
            # - The vacancy creator
            # - Organization recruiters
            # - Hiring managers for this vacancy

        except Exception as notification_error:
            # Don't fail application if notification fails
            logger.warning(f"Failed to send application notification: {notification_error}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_application_to_response(new_application, vacancy.title),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting application: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}",
        ) from e


@router.get(
    "/my-applications",
    response_model=JobApplicationsListResponse,
    tags=["Job Applications"],
)
async def get_my_applications(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by application status"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> JSONResponse:
    """
    Get the current user's job applications.

    Returns a paginated list of job applications submitted by the current user.
    If the user is not authenticated, returns an empty list.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status_filter: Optional filter by application status
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        JSON response with list of applications

    Raises:
        HTTPException(401): If user is not authenticated

    Example:
        >>> response = requests.get("/api/job-applications/my-applications?limit=10")
        >>> applications = response.json()
    """
    try:
        # Require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view applications",
            )

        # Build query with filters
        query = select(JobApplication).where(JobApplication.user_id == current_user.id)

        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = ApplicationStatus(status_filter.upper())
                query = query.where(JobApplication.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}",
                )

        # Order by created_at descending and apply pagination
        query = query.order_by(JobApplication.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        applications = result.scalars().all()

        # Get total count
        count_query = select(JobApplication).where(JobApplication.user_id == current_user.id)
        if status_filter:
            count_query = count_query.where(JobApplication.status == status_enum)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Fetch vacancy titles for each application
        application_list = []
        for app in applications:
            # Get vacancy details
            vacancy_query = select(JobVacancy).where(JobVacancy.id == app.vacancy_id)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()
            vacancy_title = vacancy.title if vacancy else None

            application_list.append(_application_to_response(app, vacancy_title))

        # Log audit event for viewing applications
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.MATCH_CREATED,  # Using existing type for now
            entity_type="job_applications_list",
            entity_id=current_user.id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "applications": application_list,
                "total": total,
                "limit": limit,
                "skip": skip,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting applications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get applications: {str(e)}",
        ) from e


@router.get(
    "/{application_id}",
    response_model=JobApplicationResponse,
    tags=["Job Applications"],
)
async def get_application(
    request: Request,
    application_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> JSONResponse:
    """
    Get a specific job application by ID.

    Returns the application details if the user is the owner.

    Args:
        request: FastAPI request object
        application_id: UUID of the application
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        JSON response with application details

    Raises:
        HTTPException(404): If application not found
        HTTPException(403): If user is not the owner

    Example:
        >>> response = requests.get("/api/job-applications/123")
        >>> application = response.json()
    """
    try:
        # Parse application_id
        try:
            application_uuid = UUID(application_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid application ID format",
            )

        # Query application from database
        query = select(JobApplication).where(JobApplication.id == application_uuid)
        result = await db.execute(query)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        # Check if user is the owner
        if current_user and application.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this application",
            )

        # Get vacancy details
        vacancy_query = select(JobVacancy).where(JobVacancy.id == application.vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()
        vacancy_title = vacancy.title if vacancy else None

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_application_to_response(application, vacancy_title),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application: {str(e)}",
        ) from e


@router.patch(
    "/{application_id}/status",
    response_model=UpdateApplicationStatusResponse,
    tags=["Job Applications"],
)
async def update_application_status(
    request: Request,
    application_id: str,
    status_data: UpdateApplicationStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> JSONResponse:
    """
    Update a job application status.

    This endpoint allows updating the status of a job application and triggers
    an email notification to the candidate about the status change.

    Args:
        request: FastAPI request object
        application_id: UUID of the application
        status_data: New status data from request body
        db: Database session
        current_user: Authenticated user (optional, for audit)

    Returns:
        JSON response with updated application details

    Raises:
        HTTPException(400): If application ID or status format is invalid
        HTTPException(404): If application not found
        HTTPException(500): If update fails

    Example:
        >>> status_data = {
        ...     "status": "UNDER_REVIEW",
        ...     "notes": "Application moved to review queue"
        ... }
        >>> response = requests.patch("/api/job-applications/123/status", json=status_data)
    """
    try:
        # Parse application_id
        try:
            application_uuid = UUID(application_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid application ID format",
            )

        # Validate status
        try:
            new_status = ApplicationStatus(status_data.status.upper())
        except ValueError:
            valid_statuses = [s.value for s in ApplicationStatus]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Query application from database
        query = select(JobApplication).where(JobApplication.id == application_uuid)
        result = await db.execute(query)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        # Store old status for comparison and notification
        old_status = application.status

        # Update status
        application.status = new_status
        await db.commit()
        await db.refresh(application)

        # Get vacancy details for notification
        vacancy_query = select(JobVacancy).where(JobVacancy.id == application.vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()
        vacancy_title = vacancy.title if vacancy else "Position"

        # Get user details for notification
        user_query = select(User).where(User.id == application.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        notification_queued = False

        # Queue notification task if status changed and user exists
        if old_status != new_status and user:
            try:
                # Queue Celery task to send notification
                send_application_status_notification.delay(
                    application_id=str(application.id),
                    user_id=str(user.id),
                    user_email=user.email,
                    user_name=user.full_name if hasattr(user, 'full_name') else user.email,
                    vacancy_id=str(application.vacancy_id),
                    vacancy_title=vacancy_title,
                    old_status=old_status.value,
                    new_status=new_status.value,
                    additional_notes=status_data.notes,
                )
                notification_queued = True
                logger.info(
                    f"Queued notification for application {application.id}: "
                    f"{old_status.value} -> {new_status.value}"
                )
            except Exception as notification_error:
                # Don't fail the status update if notification queueing fails
                logger.error(
                    f"Failed to queue notification for application {application.id}: "
                    f"{notification_error}",
                    exc_info=True,
                )

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.MATCH_CREATED,  # Using existing type for now
            entity_type="job_application_status_change",
            entity_id=application.id,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value={"status": old_status.value},
            after_value={"status": new_status.value, "notes": status_data.notes},
        )

        logger.info(
            f"Updated application {application.id} status: "
            f"{old_status.value} -> {new_status.value}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(application.id),
                "vacancy_id": str(application.vacancy_id),
                "vacancy_title": vacancy_title,
                "email": application.email or "",
                "status": new_status.value,
                "old_status": old_status.value,
                "notification_queued": notification_queued,
                "updated_at": application.updated_at.isoformat() if application.updated_at else None,
                "message": f"Application status updated to {new_status.value}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application status: {str(e)}",
        ) from e
