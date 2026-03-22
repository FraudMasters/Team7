"""
Model approval workflow endpoints.

This module provides endpoints for managing model deployment approval workflows,
including requesting approval, approving/rejecting requests, and listing
approval requests with filtering capabilities.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.model_approval import ApprovalStatus, ModelApprovalRequest
from models.ml_model_version import MLModelVersion

logger = logging.getLogger(__name__)

router = APIRouter()


class ApprovalRequestCreate(BaseModel):
    """Request model for creating an approval request."""

    model_version_id: str = Field(..., description="UUID of the model version to deploy")
    requested_by: str = Field(..., description="User ID of the requester")
    justification: Optional[str] = Field(None, description="Justification for the deployment")
    target_environment: str = Field("staging", description="Target environment (staging, production)")
    organization_id: str = Field(..., description="Organization ID")


class ApprovalAction(BaseModel):
    """Request model for approval actions (approve/reject)."""

    reviewed_by: str = Field(..., description="User ID of the reviewer")
    review_notes: Optional[str] = Field(None, description="Notes from the review")


class ApprovalResponse(BaseModel):
    """Response model for a single approval request."""

    id: str = Field(..., description="Unique identifier for the approval request")
    model_version_id: str = Field(..., description="UUID of the model version")
    model_name: Optional[str] = Field(None, description="Name of the model")
    model_version: Optional[str] = Field(None, description="Version identifier")
    status: str = Field(..., description="Current approval status")
    requested_by: str = Field(..., description="User ID of the requester")
    reviewed_by: Optional[str] = Field(None, description="User ID of the reviewer")
    requested_at: Optional[str] = Field(None, description="Timestamp when requested")
    reviewed_at: Optional[str] = Field(None, description="Timestamp when reviewed")
    justification: Optional[str] = Field(None, description="Justification for deployment")
    review_notes: Optional[str] = Field(None, description="Notes from the review")
    target_environment: str = Field(..., description="Target environment")
    organization_id: str = Field(..., description="Organization ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ApprovalListResponse(BaseModel):
    """Response model for listing approval requests."""

    approvals: List[ApprovalResponse] = Field(..., description="List of approval requests")
    total_count: int = Field(..., description="Total number of requests")


def _format_approval_response(approval: ModelApprovalRequest, model_version: Optional[MLModelVersion] = None) -> dict:
    """Format a ModelApprovalRequest instance as a response dict."""
    return {
        "id": str(approval.id),
        "model_version_id": str(approval.model_version_id),
        "model_name": model_version.model_name if model_version else None,
        "model_version": model_version.version if model_version else None,
        "status": approval.status.value if approval.status else None,
        "requested_by": approval.requested_by,
        "reviewed_by": approval.reviewed_by,
        "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
        "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
        "justification": approval.justification,
        "review_notes": approval.review_notes,
        "target_environment": approval.target_environment,
        "organization_id": approval.organization_id,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "updated_at": approval.updated_at.isoformat() if approval.updated_at else None,
    }


@router.post(
    "/",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Model Approvals"],
)
async def request_approval(
    request: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new model deployment approval request.

    This endpoint creates a new approval request for deploying a specific
    model version to a target environment. The request will be in 'pending'
    status until reviewed.

    Args:
        request: Approval request with model version ID and requester info
        db: Database session

    Returns:
        JSON response with created approval request

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If model version is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "model_version_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "requested_by": "user123",
        ...     "justification": "Improved accuracy by 5%",
        ...     "target_environment": "production",
        ...     "organization_id": "org1"
        ... }
        >>> response = requests.post("/api/model-approvals/", json=data)
        >>> response.json()
        {
            "id": "...",
            "status": "pending",
            ...
        }
    """
    try:
        logger.info(f"Creating approval request for model version: {request.model_version_id}")

        # Validate model version ID format
        try:
            version_uuid = UUID(request.model_version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid model version UUID format: {e}",
            )

        # Check if model version exists
        model_query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        if model_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {request.model_version_id}",
            )

        # Check if there's already a pending request for this model version
        existing_query = select(ModelApprovalRequest).where(
            ModelApprovalRequest.model_version_id == version_uuid,
            ModelApprovalRequest.status == ApprovalStatus.PENDING,
        )
        existing_result = await db.execute(existing_query)
        existing_approval = existing_result.scalar_one_or_none()

        if existing_approval:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"A pending approval request already exists for this model version",
            )

        # Validate required fields
        if not request.requested_by or len(request.requested_by.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="requested_by cannot be empty",
            )

        if not request.organization_id or len(request.organization_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="organization_id cannot be empty",
            )

        # Create approval request
        now = datetime.now(timezone.utc)
        db_approval = ModelApprovalRequest(
            model_version_id=version_uuid,
            status=ApprovalStatus.PENDING,
            requested_by=request.requested_by,
            requested_at=now,
            justification=request.justification,
            target_environment=request.target_environment,
            organization_id=request.organization_id,
        )
        db.add(db_approval)

        await db.flush()
        await db.commit()
        await db.refresh(db_approval)

        response_data = _format_approval_response(db_approval, model_version)

        logger.info(f"Created approval request {db_approval.id} for model version {request.model_version_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating approval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create approval request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error creating approval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create approval request: {str(e)}",
        ) from e


@router.get("/", tags=["Model Approvals"])
async def list_approvals(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, approved, rejected, deployed, cancelled)"),
    requested_by: Optional[str] = Query(None, description="Filter by requester user ID"),
    target_environment: Optional[str] = Query(None, description="Filter by target environment"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List model approval requests with optional filters.

    Args:
        status_filter: Optional status filter (pending, approved, rejected, deployed, cancelled)
        requested_by: Optional requester user ID filter
        target_environment: Optional target environment filter
        organization_id: Optional organization ID filter
        model_name: Optional model name filter
        db: Database session

    Returns:
        JSON response with list of approval requests

    Raises:
        HTTPException(422): If invalid status value provided
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-approvals/?status=pending")
        >>> response.json()
        {
            "approvals": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(
            f"Listing approval requests with filters - status: {status_filter}, "
            f"requested_by: {requested_by}, target_environment: {target_environment}, "
            f"organization_id: {organization_id}, model_name: {model_name}"
        )

        # Build query with filters
        query = select(ModelApprovalRequest)

        if status_filter:
            try:
                status_enum = ApprovalStatus(status_filter.lower())
                query = query.where(ModelApprovalRequest.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status value. Must be one of: {[s.value for s in ApprovalStatus]}",
                )

        if requested_by:
            query = query.where(ModelApprovalRequest.requested_by == requested_by)

        if target_environment:
            query = query.where(ModelApprovalRequest.target_environment == target_environment)

        if organization_id:
            query = query.where(ModelApprovalRequest.organization_id == organization_id)

        # Order by created_at descending
        query = query.order_by(ModelApprovalRequest.created_at.desc())

        result = await db.execute(query)
        approvals = result.scalars().all()

        # Fetch model version info for each approval
        formatted_approvals = []
        for approval in approvals:
            # Get model version details
            model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
            model_result = await db.execute(model_query)
            model_version = model_result.scalar_one_or_none()

            # Apply model_name filter if specified
            if model_name and model_version:
                if model_version.model_name != model_name:
                    continue

            formatted_approvals.append(_format_approval_response(approval, model_version))

        response_data = {
            "approvals": formatted_approvals,
            "total_count": len(formatted_approvals),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error listing approval requests: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list approval requests: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error listing approval requests: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list approval requests: {str(e)}",
        ) from e


@router.get("/{approval_id}", tags=["Model Approvals"])
async def get_approval(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific approval request by ID.

    Args:
        approval_id: Unique identifier of the approval request
        db: Database session

    Returns:
        JSON response with approval request details

    Raises:
        HTTPException(404): If approval request is not found
        HTTPException(422): If approval_id is not a valid UUID
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-approvals/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "...",
            "status": "pending",
            ...
        }
    """
    try:
        logger.info(f"Getting approval request: {approval_id}")

        # Validate UUID format
        try:
            approval_uuid = UUID(approval_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        query = select(ModelApprovalRequest).where(ModelApprovalRequest.id == approval_uuid)
        result = await db.execute(query)
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}",
            )

        # Get model version details
        model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_approval_response(approval, model_version),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting approval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting approval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval request: {str(e)}",
        ) from e


@router.post("/{approval_id}/approve", tags=["Model Approvals"])
async def approve_request(
    approval_id: str,
    request: ApprovalAction,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Approve a model deployment request.

    This endpoint approves a pending approval request, changing its status
    to 'approved'. Only pending requests can be approved.

    Args:
        approval_id: Unique identifier of the approval request
        request: Approval action with reviewer info and notes
        db: Database session

    Returns:
        JSON response with updated approval request

    Raises:
        HTTPException(404): If approval request is not found
        HTTPException(422): If request is not in pending status
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "reviewed_by": "admin123",
        ...     "review_notes": "Approved after thorough review"
        ... }
        >>> response = requests.post(
        ...     "/api/model-approvals/123/approve",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "status": "approved",
            ...
        }
    """
    try:
        logger.info(f"Approving request: {approval_id}")

        # Validate UUID format
        try:
            approval_uuid = UUID(approval_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Validate reviewed_by
        if not request.reviewed_by or len(request.reviewed_by.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reviewed_by cannot be empty",
            )

        # Query existing approval
        query = select(ModelApprovalRequest).where(ModelApprovalRequest.id == approval_uuid)
        result = await db.execute(query)
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}",
            )

        # Check if request is in pending status
        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot approve request with status '{approval.status.value}'. Only pending requests can be approved.",
            )

        # Update approval
        now = datetime.now(timezone.utc)
        approval.status = ApprovalStatus.APPROVED
        approval.reviewed_by = request.reviewed_by
        approval.reviewed_at = now
        approval.review_notes = request.review_notes

        await db.commit()
        await db.refresh(approval)

        # Get model version details
        model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        logger.info(f"Approval request {approval_id} approved by {request.reviewed_by}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_approval_response(approval, model_version),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error approving request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error approving request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {str(e)}",
        ) from e


@router.post("/{approval_id}/reject", tags=["Model Approvals"])
async def reject_request(
    approval_id: str,
    request: ApprovalAction,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Reject a model deployment request.

    This endpoint rejects a pending approval request, changing its status
    to 'rejected'. Only pending requests can be rejected.

    Args:
        approval_id: Unique identifier of the approval request
        request: Approval action with reviewer info and notes
        db: Database session

    Returns:
        JSON response with updated approval request

    Raises:
        HTTPException(404): If approval request is not found
        HTTPException(422): If request is not in pending status
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "reviewed_by": "admin123",
        ...     "review_notes": "Insufficient testing data"
        ... }
        >>> response = requests.post(
        ...     "/api/model-approvals/123/reject",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "...",
            "status": "rejected",
            ...
        }
    """
    try:
        logger.info(f"Rejecting request: {approval_id}")

        # Validate UUID format
        try:
            approval_uuid = UUID(approval_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Validate reviewed_by
        if not request.reviewed_by or len(request.reviewed_by.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reviewed_by cannot be empty",
            )

        # Query existing approval
        query = select(ModelApprovalRequest).where(ModelApprovalRequest.id == approval_uuid)
        result = await db.execute(query)
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}",
            )

        # Check if request is in pending status
        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot reject request with status '{approval.status.value}'. Only pending requests can be rejected.",
            )

        # Update approval
        now = datetime.now(timezone.utc)
        approval.status = ApprovalStatus.REJECTED
        approval.reviewed_by = request.reviewed_by
        approval.reviewed_at = now
        approval.review_notes = request.review_notes

        await db.commit()
        await db.refresh(approval)

        # Get model version details
        model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        logger.info(f"Approval request {approval_id} rejected by {request.reviewed_by}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_approval_response(approval, model_version),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error rejecting request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error rejecting request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject request: {str(e)}",
        ) from e


@router.post("/{approval_id}/cancel", tags=["Model Approvals"])
async def cancel_request(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Cancel a model deployment request.

    This endpoint cancels a pending approval request, changing its status
    to 'cancelled'. Only pending requests can be cancelled.

    Args:
        approval_id: Unique identifier of the approval request
        db: Database session

    Returns:
        JSON response with updated approval request

    Raises:
        HTTPException(404): If approval request is not found
        HTTPException(422): If request is not in pending status
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/model-approvals/123/cancel")
        >>> response.json()
        {
            "id": "...",
            "status": "cancelled",
            ...
        }
    """
    try:
        logger.info(f"Cancelling request: {approval_id}")

        # Validate UUID format
        try:
            approval_uuid = UUID(approval_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query existing approval
        query = select(ModelApprovalRequest).where(ModelApprovalRequest.id == approval_uuid)
        result = await db.execute(query)
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}",
            )

        # Check if request is in pending status
        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot cancel request with status '{approval.status.value}'. Only pending requests can be cancelled.",
            )

        # Update approval
        approval.status = ApprovalStatus.CANCELLED

        await db.commit()
        await db.refresh(approval)

        # Get model version details
        model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        logger.info(f"Approval request {approval_id} cancelled")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_approval_response(approval, model_version),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error cancelling request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error cancelling request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel request: {str(e)}",
        ) from e


@router.post("/{approval_id}/deploy", tags=["Model Approvals"])
async def deploy_approved_model(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Deploy an approved model.

    This endpoint marks an approved request as deployed and activates the
    model version in production. Only approved requests can be deployed.

    Args:
        approval_id: Unique identifier of the approval request
        db: Database session

    Returns:
        JSON response with updated approval request and deployment status

    Raises:
        HTTPException(404): If approval request is not found
        HTTPException(422): If request is not in approved status
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/model-approvals/123/deploy")
        >>> response.json()
        {
            "id": "...",
            "status": "deployed",
            ...
        }
    """
    try:
        logger.info(f"Deploying approved request: {approval_id}")

        # Validate UUID format
        try:
            approval_uuid = UUID(approval_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query existing approval
        query = select(ModelApprovalRequest).where(ModelApprovalRequest.id == approval_uuid)
        result = await db.execute(query)
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}",
            )

        # Check if request is in approved status
        if approval.status != ApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot deploy request with status '{approval.status.value}'. Only approved requests can be deployed.",
            )

        # Get model version
        model_query = select(MLModelVersion).where(MLModelVersion.id == approval.model_version_id)
        model_result = await db.execute(model_query)
        model_version = model_result.scalar_one_or_none()

        if model_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {approval.model_version_id}",
            )

        # Deactivate all other versions of the same model
        deactivate_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_version.model_name,
            MLModelVersion.id != model_version.id,
        )
        deactivate_result = await db.execute(deactivate_query)
        other_models = deactivate_result.scalars().all()

        for other_model in other_models:
            other_model.is_active = False

        # Activate the target model
        model_version.is_active = True

        # Update approval status
        approval.status = ApprovalStatus.DEPLOYED

        await db.commit()
        await db.refresh(approval)
        await db.refresh(model_version)

        logger.info(f"Approval request {approval_id} deployed successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                **_format_approval_response(approval, model_version),
                "deployment_status": "success",
                "model_activated": True,
            },
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deploying request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error deploying request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy request: {str(e)}",
        ) from e
