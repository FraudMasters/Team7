"""
Bulk operation endpoints for job vacancies.

This module provides endpoints for:
- Bulk deleting multiple vacancies
- Bulk updating vacancy status (active/inactive)
- Bulk duplicating vacancies
- Bulk assigning vacancies to organizations

These operations follow the same pattern as bulk candidate actions.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_vacancy import JobVacancy
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class BulkDeleteRequest(BaseModel):
    """Request model for bulk deleting vacancies."""

    vacancy_ids: List[str] = Field(..., description="List of vacancy IDs to delete", min_length=1)


class BulkStatusUpdateRequest(BaseModel):
    """Request model for bulk updating vacancy status."""

    vacancy_ids: List[str] = Field(..., description="List of vacancy IDs to update", min_length=1)
    is_active: bool = Field(..., description="New active status (True for active, False for inactive)")


class BulkDuplicateRequest(BaseModel):
    """Request model for bulk duplicating vacancies."""

    vacancy_ids: List[str] = Field(..., description="List of vacancy IDs to duplicate", min_length=1)


class BulkAssignRequest(BaseModel):
    """Request model for bulk assigning vacancies to an organization."""

    vacancy_ids: List[str] = Field(..., description="List of vacancy IDs to assign", min_length=1)
    organization_id: str = Field(..., description="Target organization ID")


# Result Models
class BulkOperationResult(BaseModel):
    """Result of a single vacancy operation in a bulk operation."""

    vacancy_id: str = Field(..., description="Vacancy ID")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Success or error message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data (e.g., new vacancy ID for duplicates)")


# Response Models
class BulkDeleteResponse(BaseModel):
    """Response model for bulk delete operations."""

    total_requested: int = Field(..., description="Total number of vacancies requested to delete")
    successful: int = Field(..., description="Number of successfully deleted vacancies")
    failed: int = Field(..., description="Number of vacancies that failed to delete")
    results: List[BulkOperationResult] = Field(..., description="Individual results for each vacancy")


class BulkStatusUpdateResponse(BaseModel):
    """Response model for bulk status update operations."""

    total_requested: int = Field(..., description="Total number of vacancies requested to update")
    successful: int = Field(..., description="Number of successfully updated vacancies")
    failed: int = Field(..., description="Number of vacancies that failed to update")
    results: List[BulkOperationResult] = Field(..., description="Individual results for each vacancy")


class BulkDuplicateResponse(BaseModel):
    """Response model for bulk duplicate operations."""

    total_requested: int = Field(..., description="Total number of vacancies requested to duplicate")
    successful: int = Field(..., description="Number of successfully duplicated vacancies")
    failed: int = Field(..., description="Number of vacancies that failed to duplicate")
    results: List[BulkOperationResult] = Field(..., description="Individual results for each vacancy")


class BulkAssignResponse(BaseModel):
    """Response model for bulk assign operations."""

    total_requested: int = Field(..., description="Total number of vacancies requested to assign")
    successful: int = Field(..., description="Number of successfully assigned vacancies")
    failed: int = Field(..., description="Number of vacancies that failed to assign")
    results: List[BulkOperationResult] = Field(..., description="Individual results for each vacancy")


# Helper function to convert vacancy to dict for audit logging
def _vacancy_to_dict(vacancy: JobVacancy) -> dict:
    """Convert JobVacancy model to dict for audit logging."""
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
        "is_active": vacancy.is_active,
        "organization_id": str(vacancy.organization_id) if vacancy.organization_id else None,
    }


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    tags=["Vacancies"],
)
async def bulk_delete_vacancies(
    request: Request,
    bulk_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Bulk delete multiple job vacancies.

    This endpoint allows deleting multiple vacancies at once.
    Returns detailed results for each vacancy including success/failure status.

    Args:
        request: FastAPI request object
        bulk_request: Bulk delete request with list of vacancy IDs
        db: Database session

    Returns:
        JSON response with bulk delete results including:
        - total_requested: Total number of vacancies requested to delete
        - successful: Number of successfully deleted vacancies
        - failed: Number of vacancies that failed to delete
        - results: Individual results for each vacancy

    Raises:
        HTTPException(400): If vacancy_ids list is empty
        HTTPException(500): If database operation fails

    Example:
        >>> delete_request = {
        ...     "vacancy_ids": ["uuid1", "uuid2", "uuid3"]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/bulk-delete",
        ...     json=delete_request
        ... )
    """
    try:
        # Validate input
        if not bulk_request.vacancy_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vacancy_ids list cannot be empty",
            )

        vacancy_ids = bulk_request.vacancy_ids
        results = []
        successful_count = 0
        failed_count = 0
        ip_address, user_agent = get_request_context(request)

        # Process each vacancy ID
        for vacancy_id in vacancy_ids:
            try:
                # Validate UUID format
                try:
                    vacancy_uuid = UUID(vacancy_id)
                except ValueError:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Invalid UUID format: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Query vacancy from database
                query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
                result = await db.execute(query)
                vacancy = result.scalar_one_or_none()

                if not vacancy:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Vacancy not found: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Capture before state for audit log
                before_state = _vacancy_to_dict(vacancy)

                # Delete vacancy
                await db.delete(vacancy)

                # Log audit event for this deletion
                await log_audit_event(
                    db=db,
                    action_type=AuditActionType.VACANCY_DELETED,
                    entity_type="vacancy",
                    entity_id=vacancy.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    before_value=before_state,
                )

                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=True,
                        message=f"Successfully deleted vacancy: {vacancy.title}",
                        data=None,
                    )
                )
                successful_count += 1
                logger.info(f"Deleted vacancy: {vacancy_id} - {vacancy.title}")

            except Exception as e:
                # Continue processing other vacancies even if one fails
                logger.error(f"Error deleting vacancy {vacancy_id}: {e}", exc_info=True)
                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=False,
                        message=f"Error deleting vacancy: {str(e)}",
                        data=None,
                    )
                )
                failed_count += 1

        # Commit all deletions at once
        await db.commit()

        response_data = BulkDeleteResponse(
            total_requested=len(vacancy_ids),
            successful=successful_count,
            failed=failed_count,
            results=results,
        )

        logger.info(
            f"Bulk delete completed: {successful_count}/{len(vacancy_ids)} successful, "
            f"{failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk delete: {str(e)}",
        ) from e


@router.post(
    "/bulk-update-status",
    response_model=BulkStatusUpdateResponse,
    tags=["Vacancies"],
)
async def bulk_update_vacancy_status(
    request: Request,
    bulk_request: BulkStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Bulk update the active status of multiple job vacancies.

    This endpoint allows activating or deactivating multiple vacancies at once.
    Returns detailed results for each vacancy including success/failure status.

    Args:
        request: FastAPI request object
        bulk_request: Bulk status update request with list of vacancy IDs and new status
        db: Database session

    Returns:
        JSON response with bulk status update results including:
        - total_requested: Total number of vacancies requested to update
        - successful: Number of successfully updated vacancies
        - failed: Number of vacancies that failed to update
        - results: Individual results for each vacancy

    Raises:
        HTTPException(400): If vacancy_ids list is empty
        HTTPException(500): If database operation fails

    Example:
        >>> status_request = {
        ...     "vacancy_ids": ["uuid1", "uuid2", "uuid3"],
        ...     "is_active": False
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/bulk-update-status",
        ...     json=status_request
        ... )
    """
    try:
        # Validate input
        if not bulk_request.vacancy_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vacancy_ids list cannot be empty",
            )

        vacancy_ids = bulk_request.vacancy_ids
        new_status = bulk_request.is_active
        results = []
        successful_count = 0
        failed_count = 0
        ip_address, user_agent = get_request_context(request)

        # Process each vacancy ID
        for vacancy_id in vacancy_ids:
            try:
                # Validate UUID format
                try:
                    vacancy_uuid = UUID(vacancy_id)
                except ValueError:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Invalid UUID format: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Query vacancy from database
                query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
                result = await db.execute(query)
                vacancy = result.scalar_one_or_none()

                if not vacancy:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Vacancy not found: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Capture before state for audit log
                before_state = _vacancy_to_dict(vacancy)

                # Update vacancy status
                vacancy.is_active = new_status

                # Log audit event for this status update
                await log_audit_event(
                    db=db,
                    action_type=AuditActionType.VACANCY_UPDATED,
                    entity_type="vacancy",
                    entity_id=vacancy.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    before_value=before_state,
                    after_value=_vacancy_to_dict(vacancy),
                )

                status_text = "activated" if new_status else "deactivated"
                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=True,
                        message=f"Successfully {status_text} vacancy: {vacancy.title}",
                        data={"is_active": new_status},
                    )
                )
                successful_count += 1
                logger.info(f"Updated vacancy status: {vacancy_id} - {vacancy.title} -> is_active={new_status}")

            except Exception as e:
                # Continue processing other vacancies even if one fails
                logger.error(f"Error updating vacancy status {vacancy_id}: {e}", exc_info=True)
                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=False,
                        message=f"Error updating vacancy status: {str(e)}",
                        data=None,
                    )
                )
                failed_count += 1

        # Commit all updates at once
        await db.commit()

        response_data = BulkStatusUpdateResponse(
            total_requested=len(vacancy_ids),
            successful=successful_count,
            failed=failed_count,
            results=results,
        )

        logger.info(
            f"Bulk status update completed: {successful_count}/{len(vacancy_ids)} successful, "
            f"{failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk status update: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk status update: {str(e)}",
        ) from e


@router.post(
    "/bulk-duplicate",
    response_model=BulkDuplicateResponse,
    tags=["Vacancies"],
)
async def bulk_duplicate_vacancies(
    request: Request,
    bulk_request: BulkDuplicateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Bulk duplicate multiple job vacancies.

    This endpoint allows creating copies of multiple vacancies at once.
    The duplicated vacancies will have "Copy of" prefixed to their title.
    Returns detailed results for each vacancy including success/failure status
    and the IDs of the newly created vacancies.

    Args:
        request: FastAPI request object
        bulk_request: Bulk duplicate request with list of vacancy IDs
        db: Database session

    Returns:
        JSON response with bulk duplicate results including:
        - total_requested: Total number of vacancies requested to duplicate
        - successful: Number of successfully duplicated vacancies
        - failed: Number of vacancies that failed to duplicate
        - results: Individual results for each vacancy with new vacancy IDs

    Raises:
        HTTPException(400): If vacancy_ids list is empty
        HTTPException(500): If database operation fails

    Example:
        >>> duplicate_request = {
        ...     "vacancy_ids": ["uuid1", "uuid2", "uuid3"]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/bulk-duplicate",
        ...     json=duplicate_request
        ... )
    """
    try:
        # Validate input
        if not bulk_request.vacancy_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vacancy_ids list cannot be empty",
            )

        vacancy_ids = bulk_request.vacancy_ids
        results = []
        successful_count = 0
        failed_count = 0
        ip_address, user_agent = get_request_context(request)

        # Process each vacancy ID
        for vacancy_id in vacancy_ids:
            try:
                # Validate UUID format
                try:
                    vacancy_uuid = UUID(vacancy_id)
                except ValueError:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Invalid UUID format: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Query vacancy from database
                query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
                result = await db.execute(query)
                vacancy = result.scalar_one_or_none()

                if not vacancy:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Vacancy not found: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Create a duplicate of the vacancy
                new_vacancy = JobVacancy(
                    title=f"Copy of {vacancy.title}",
                    description=vacancy.description,
                    required_skills=vacancy.required_skills.copy() if vacancy.required_skills else [],
                    min_experience_months=vacancy.min_experience_months,
                    additional_requirements=vacancy.additional_requirements.copy() if vacancy.additional_requirements else [],
                    industry=vacancy.industry,
                    work_format=vacancy.work_format,
                    location=vacancy.location,
                    salary_min=vacancy.salary_min,
                    salary_max=vacancy.salary_max,
                    english_level=vacancy.english_level,
                    employment_type=vacancy.employment_type,
                    organization_id=vacancy.organization_id,
                    is_active=vacancy.is_active,
                    source=vacancy.source,
                )

                db.add(new_vacancy)
                await db.flush()
                await db.refresh(new_vacancy)

                # Log audit event for this duplication
                await log_audit_event(
                    db=db,
                    action_type=AuditActionType.VACANCY_CREATED,
                    entity_type="vacancy",
                    entity_id=new_vacancy.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    after_value=_vacancy_to_dict(new_vacancy),
                    metadata={
                        "duplicated_from": str(vacancy.id),
                        "original_title": vacancy.title,
                    },
                )

                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=True,
                        message=f"Successfully duplicated vacancy: {vacancy.title}",
                        data={
                            "new_vacancy_id": str(new_vacancy.id),
                            "new_title": new_vacancy.title,
                        },
                    )
                )
                successful_count += 1
                logger.info(
                    f"Duplicated vacancy: {vacancy_id} -> {new_vacancy.id} - "
                    f"{vacancy.title} -> {new_vacancy.title}"
                )

            except Exception as e:
                # Continue processing other vacancies even if one fails
                logger.error(f"Error duplicating vacancy {vacancy_id}: {e}", exc_info=True)
                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=False,
                        message=f"Error duplicating vacancy: {str(e)}",
                        data=None,
                    )
                )
                failed_count += 1

        # Commit all duplications at once
        await db.commit()

        response_data = BulkDuplicateResponse(
            total_requested=len(vacancy_ids),
            successful=successful_count,
            failed=failed_count,
            results=results,
        )

        logger.info(
            f"Bulk duplication completed: {successful_count}/{len(vacancy_ids)} successful, "
            f"{failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk duplication: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk duplication: {str(e)}",
        ) from e


@router.post(
    "/bulk-assign",
    response_model=BulkAssignResponse,
    tags=["Vacancies"],
)
async def bulk_assign_vacancies(
    request: Request,
    bulk_request: BulkAssignRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Bulk assign multiple job vacancies to an organization.

    This endpoint allows assigning multiple vacancies to a specific organization at once.
    Returns detailed results for each vacancy including success/failure status.

    Args:
        request: FastAPI request object
        bulk_request: Bulk assign request with list of vacancy IDs and target organization ID
        db: Database session

    Returns:
        JSON response with bulk assign results including:
        - total_requested: Total number of vacancies requested to assign
        - successful: Number of successfully assigned vacancies
        - failed: Number of vacancies that failed to assign
        - results: Individual results for each vacancy

    Raises:
        HTTPException(400): If vacancy_ids list is empty or organization_id is invalid
        HTTPException(500): If database operation fails

    Example:
        >>> assign_request = {
        ...     "vacancy_ids": ["uuid1", "uuid2", "uuid3"],
        ...     "organization_id": "org-uuid-123"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/vacancies/bulk-assign",
        ...     json=assign_request
        ... )
    """
    try:
        # Validate input
        if not bulk_request.vacancy_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vacancy_ids list cannot be empty",
            )

        # Validate organization_id format
        try:
            organization_uuid = UUID(bulk_request.organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid organization_id format: {bulk_request.organization_id}",
            )

        vacancy_ids = bulk_request.vacancy_ids
        results = []
        successful_count = 0
        failed_count = 0
        ip_address, user_agent = get_request_context(request)

        # Process each vacancy ID
        for vacancy_id in vacancy_ids:
            try:
                # Validate UUID format
                try:
                    vacancy_uuid = UUID(vacancy_id)
                except ValueError:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Invalid UUID format: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Query vacancy from database
                query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
                result = await db.execute(query)
                vacancy = result.scalar_one_or_none()

                if not vacancy:
                    results.append(
                        BulkOperationResult(
                            vacancy_id=vacancy_id,
                            success=False,
                            message=f"Vacancy not found: {vacancy_id}",
                            data=None,
                        )
                    )
                    failed_count += 1
                    continue

                # Capture before state for audit log
                before_state = _vacancy_to_dict(vacancy)

                # Update vacancy organization
                old_organization_id = vacancy.organization_id
                vacancy.organization_id = organization_uuid

                # Log audit event for this assignment
                await log_audit_event(
                    db=db,
                    action_type=AuditActionType.VACANCY_UPDATED,
                    entity_type="vacancy",
                    entity_id=vacancy.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    before_value=before_state,
                    after_value=_vacancy_to_dict(vacancy),
                    metadata={
                        "bulk_operation": True,
                        "old_organization_id": str(old_organization_id) if old_organization_id else None,
                        "new_organization_id": str(organization_uuid),
                    },
                )

                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=True,
                        message=f"Successfully assigned vacancy '{vacancy.title}' to organization",
                        data={
                            "old_organization_id": str(old_organization_id) if old_organization_id else None,
                            "new_organization_id": str(organization_uuid),
                        },
                    )
                )
                successful_count += 1
                logger.info(
                    f"Assigned vacancy: {vacancy_id} - {vacancy.title} -> organization_id={organization_uuid}"
                )

            except Exception as e:
                # Continue processing other vacancies even if one fails
                logger.error(f"Error assigning vacancy {vacancy_id}: {e}", exc_info=True)
                results.append(
                    BulkOperationResult(
                        vacancy_id=vacancy_id,
                        success=False,
                        message=f"Error assigning vacancy: {str(e)}",
                        data=None,
                    )
                )
                failed_count += 1

        # Commit all assignments at once
        await db.commit()

        response_data = BulkAssignResponse(
            total_requested=len(vacancy_ids),
            successful=successful_count,
            failed=failed_count,
            results=results,
        )

        logger.info(
            f"Bulk assign completed: {successful_count}/{len(vacancy_ids)} successful, "
            f"{failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk assign: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk assign: {str(e)}",
        ) from e
