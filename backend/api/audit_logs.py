"""
Audit log endpoints for viewing and exporting system activity.

This module provides endpoints for retrieving audit logs of all user actions,
including resume uploads, vacancy creation, candidate ranking updates, user
invitations, role changes, and data exports.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.audit_log import AuditLog, AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


class AuditLogItem(BaseModel):
    """Single audit log item."""

    id: str = Field(..., description="Audit log ID")
    action_type: str = Field(..., description="Type of action performed")
    entity_type: Optional[str] = Field(None, description="Type of entity affected")
    entity_id: Optional[str] = Field(None, description="ID of the affected entity")
    user_id: Optional[str] = Field(None, description="User who performed the action")
    organization_id: Optional[str] = Field(None, description="Organization where action occurred")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    action_data: Optional[dict] = Field(None, description="Additional action-specific data")
    before_value: Optional[dict] = Field(None, description="Entity state before the action")
    after_value: Optional[dict] = Field(None, description="Entity state after the action")
    reason: Optional[str] = Field(None, description="Reason or explanation for the action")
    created_at: str = Field(..., description="When the action occurred")


class AuditLogsResponse(BaseModel):
    """Response model for audit logs list."""

    logs: List[AuditLogItem] = Field(..., description="List of audit logs")
    total_count: int = Field(..., description="Total number of logs matching the filters")


@router.get(
    "/",
    response_model=AuditLogsResponse,
    tags=["Audit Logs"],
)
async def get_audit_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity ID"),
    user_id: Optional[str] = Query(None, description="Filter by user who performed the action"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    start_date: Optional[str] = Query(None, description="Filter logs after this date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Filter logs before this date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get audit logs with filtering options.

    This endpoint retrieves audit logs of all user actions across the system,
    including resume uploads, vacancy creation, candidate ranking updates,
    user invitations, role changes, and data exports.

    Logs are returned in reverse chronological order (newest first).

    Args:
        action_type: Optional filter for specific action type (e.g., 'resume_created', 'user_invited')
        entity_type: Optional filter for entity type (e.g., 'resume', 'vacancy', 'user')
        entity_id: Optional filter for specific entity ID
        user_id: Optional filter for user who performed the action
        organization_id: Optional filter for organization
        start_date: Optional filter to only include logs after this date (ISO 8601 format)
        end_date: Optional filter to only include logs before this date (ISO 8601 format)
        limit: Maximum number of logs to return (default: 100, max: 1000)
        offset: Number of logs to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of audit logs and total count

    Raises:
        HTTPException(400): If action_type is invalid
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit-logs/?limit=10")
        >>> response.json()
        {
            "logs": [
                {
                    "id": "audit-1",
                    "action_type": "resume_created",
                    "entity_type": "resume",
                    "entity_id": "abc-123",
                    "user_id": "user-1",
                    "organization_id": "org-1",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0...",
                    "action_data": {"filename": "resume.pdf"},
                    "before_value": null,
                    "after_value": null,
                    "reason": null,
                    "created_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching audit logs - action_type: {action_type}, entity_type: {entity_type}, "
            f"user_id: {user_id}, organization_id: {organization_id}, "
            f"start_date: {start_date}, end_date: {end_date}"
        )

        # Build base query
        query = select(AuditLog)

        # Apply filters
        if action_type:
            # Validate action type
            valid_types = [t.value for t in AuditActionType]
            if action_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action_type: {action_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(AuditLog.action_type == action_type)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        if entity_id:
            try:
                entity_uuid = UUID(entity_id)
                query = query.where(AuditLog.entity_id == entity_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entity_id format: {entity_id}",
                )

        if user_id:
            try:
                user_uuid = UUID(user_id)
                query = query.where(AuditLog.user_id == user_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user_id format: {user_id}",
                )

        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.where(AuditLog.organization_id == org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.where(AuditLog.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.where(AuditLog.created_at <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Order by created_at descending (newest first) and apply pagination
        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        audit_logs = result.scalars().all()

        # Build response data
        logs_data = []
        for log in audit_logs:
            logs_data.append({
                "id": str(log.id),
                "action_type": log.action_type.value,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "user_id": str(log.user_id) if log.user_id else None,
                "organization_id": str(log.organization_id) if log.organization_id else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "action_data": log.action_data,
                "before_value": log.before_value,
                "after_value": log.after_value,
                "reason": log.reason,
                "created_at": log.created_at.isoformat(),
            })

        response_data = {
            "logs": logs_data,
            "total_count": len(logs_data),
        }

        logger.info(f"Retrieved {len(logs_data)} audit logs")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}",
        ) from e


class ActionTypesResponse(BaseModel):
    """Response model for available action types."""

    action_types: List[str] = Field(..., description="List of available action types")


@router.get(
    "/types",
    response_model=ActionTypesResponse,
    tags=["Audit Logs"],
)
async def get_action_types() -> JSONResponse:
    """
    Get available audit action types.

    This endpoint returns a list of all valid action types that can be used
    for filtering audit logs.

    Returns:
        JSON response with list of action types

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit-logs/types")
        >>> response.json()
        {
            "action_types": [
                "resume_created",
                "resume_updated",
                "resume_deleted",
                "resume_viewed",
                "resume_uploaded",
                "vacancy_created",
                "vacancy_updated",
                "vacancy_deleted",
                "vacancy_viewed",
                "user_created",
                "user_updated",
                "user_deleted",
                "user_invited",
                "user_role_changed",
                "candidate_ranked",
                "candidate_tagged",
                "candidate_note_added",
                "candidate_stage_changed",
                "match_created",
                "match_updated",
                "match_deleted",
                "data_exported",
                "report_generated",
                "settings_updated",
                "backup_created",
                "backup_restored",
                "login_success",
                "login_failed",
                "logout",
                "password_changed"
            ]
        }
    """
    try:
        logger.info("Fetching available audit action types")

        action_types = [t.value for t in AuditActionType]

        response_data = {
            "action_types": action_types,
        }

        logger.info(f"Retrieved {len(action_types)} action types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving action types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve action types: {str(e)}",
        ) from e


class EntityTypesResponse(BaseModel):
    """Response model for common entity types."""

    entity_types: List[str] = Field(..., description="List of common entity types")


@router.get(
    "/entity-types",
    response_model=EntityTypesResponse,
    tags=["Audit Logs"],
)
async def get_entity_types() -> JSONResponse:
    """
    Get common entity types for filtering.

    This endpoint returns a list of common entity types that can be used
    for filtering audit logs.

    Returns:
        JSON response with list of entity types

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit-logs/entity-types")
        >>> response.json()
        {
            "entity_types": [
                "resume",
                "vacancy",
                "user",
                "recruiter",
                "candidate",
                "match",
                "backup",
                "settings"
            ]
        }
    """
    try:
        logger.info("Fetching common entity types")

        # Common entity types in the system
        entity_types = [
            "resume",
            "vacancy",
            "user",
            "recruiter",
            "candidate",
            "match",
            "backup",
            "settings",
        ]

        response_data = {
            "entity_types": entity_types,
        }

        logger.info(f"Retrieved {len(entity_types)} entity types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving entity types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve entity types: {str(e)}",
        ) from e


class AnonymizeLogsResponse(BaseModel):
    """Response model for audit log anonymization."""

    anonymized_count: int = Field(..., description="Number of audit logs anonymized")
    message: str = Field(..., description="Success message")


@router.post(
    "/anonymize/{user_id}",
    response_model=AnonymizeLogsResponse,
    tags=["Audit Logs"],
)
async def anonymize_user_logs(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Anonymize all audit logs for a specific user (GDPR Right to Erasure).

    This endpoint anonymizes personally identifiable information (PII) in audit logs
    for a given user while preserving the audit trail for compliance purposes.
    It sets user_id, ip_address, and user_agent to anonymized values.

    Args:
        user_id: UUID of the user whose logs should be anonymized
        request: FastAPI request object (for audit logging)
        db: Database session

    Returns:
        JSON response with count of anonymized logs and success message

    Raises:
        HTTPException(400): If user_id format is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/audit-logs/anonymize/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.json()
        {
            "anonymized_count": 42,
            "message": "Successfully anonymized 42 audit logs for user"
        }
    """
    try:
        logger.info(f"Anonymizing audit logs for user: {user_id}")

        # Validate user_id format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}. Must be a valid UUID.",
            )

        # Count logs to be anonymized
        count_query = select(AuditLog).where(AuditLog.user_id == user_uuid)
        count_result = await db.execute(count_query)
        logs_to_anonymize = count_result.scalars().all()
        anonymized_count = len(logs_to_anonymize)

        if anonymized_count == 0:
            logger.info(f"No audit logs found for user: {user_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "anonymized_count": 0,
                    "message": "No audit logs found for this user",
                },
            )

        # Anonymize the logs by setting PII fields to None
        update_stmt = (
            update(AuditLog)
            .where(AuditLog.user_id == user_uuid)
            .values(
                user_id=None,
                ip_address=None,
                user_agent=None,
            )
        )
        await db.execute(update_stmt)
        await db.commit()

        # Log the anonymization action itself
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.USER_DELETED,  # Reusing existing action type
            entity_type="audit_log",
            entity_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "anonymized_user_id": user_id,
                "anonymized_count": anonymized_count,
                "reason": "GDPR Right to Erasure - User data anonymization",
            },
        )
        await db.commit()

        logger.info(f"Successfully anonymized {anonymized_count} audit logs for user: {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "anonymized_count": anonymized_count,
                "message": f"Successfully anonymized {anonymized_count} audit logs for user",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error anonymizing audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to anonymize audit logs: {str(e)}",
        ) from e
