"""
Data retention policy management endpoints.

This module provides endpoints for managing organization-specific and global data retention policies,
including CRUD operations for creating, reading, updating, and deleting retention policy configurations
with customizable retention periods, actions, and legal basis documentation for GDPR compliance.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.data_retention_policy import DataRetentionPolicy, RetentionEntityType, RetentionActionType
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class RetentionPolicyCreate(BaseModel):
    """Request model for creating a retention policy."""

    policy_name: str = Field(..., min_length=1, max_length=200, description="Human-readable name for the policy")
    entity_type: str = Field(..., description="Type of entity this policy applies to (e.g., 'resume', 'candidate_data')")
    retention_days: int = Field(365, ge=1, description="Number of days to retain data before action")
    action_type: str = Field("delete", description="Action to take when retention period expires (e.g., 'delete', 'anonymize')")
    organization_id: Optional[str] = Field(None, description="Organization ID (None for global policies)")
    is_active: bool = Field(True, description="Whether the policy is currently active")
    description: Optional[str] = Field(None, description="Description of the policy's purpose")
    legal_basis: Optional[str] = Field(None, max_length=100, description="Legal basis for retention (e.g., 'legitimate_interest', 'contract')")
    deletion_reason: Optional[str] = Field(None, max_length=500, description="Reason to record in audit logs when deleting data")


class RetentionPolicyUpdate(BaseModel):
    """Request model for updating a retention policy."""

    policy_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Human-readable name for the policy")
    entity_type: Optional[str] = Field(None, description="Type of entity this policy applies to")
    retention_days: Optional[int] = Field(None, ge=1, description="Number of days to retain data before action")
    action_type: Optional[str] = Field(None, description="Action to take when retention period expires")
    organization_id: Optional[str] = Field(None, description="Organization ID (None for global policies)")
    is_active: Optional[bool] = Field(None, description="Whether the policy is currently active")
    description: Optional[str] = Field(None, description="Description of the policy's purpose")
    legal_basis: Optional[str] = Field(None, max_length=100, description="Legal basis for retention")
    deletion_reason: Optional[str] = Field(None, max_length=500, description="Reason to record in audit logs when deleting data")


class RetentionPolicyResponse(BaseModel):
    """Response model for a single retention policy."""

    id: str = Field(..., description="Unique identifier for the retention policy")
    policy_name: str = Field(..., description="Human-readable name for the policy")
    entity_type: str = Field(..., description="Type of entity this policy applies to")
    retention_days: int = Field(..., description="Number of days to retain data before action")
    action_type: str = Field(..., description="Action to take when retention period expires")
    organization_id: Optional[str] = Field(None, description="Organization ID (None for global policies)")
    is_active: bool = Field(..., description="Whether the policy is currently active")
    description: Optional[str] = Field(None, description="Description of the policy's purpose")
    legal_basis: Optional[str] = Field(None, description="Legal basis for retention")
    deletion_reason: Optional[str] = Field(None, description="Reason to record in audit logs when deleting data")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class RetentionPolicyListResponse(BaseModel):
    """Response model for listing retention policies."""

    organization_id: Optional[str] = Field(..., description="Organization ID filter (None for all/global)")
    policies: List[RetentionPolicyResponse] = Field(..., description="List of retention policies")
    total_count: int = Field(..., description="Total number of policies")


@router.post(
    "/",
    response_model=RetentionPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Retention Policies"],
)
async def create_retention_policy(
    request: RetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a data retention policy.

    This endpoint creates a new data retention policy for GDPR compliance,
    allowing organizations to define how long different types of data should be retained
    and what action to take when the retention period expires. Policies can be
    organization-specific or global (applies to all organizations).

    Args:
        request: Request body containing retention policy details
        db: Database session

    Returns:
        JSON response with created retention policy details

    Raises:
        HTTPException(422): If validation fails or invalid entity/action type
        HTTPException(409): If policy with same name and organization already exists
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/retention-policies/",
        ...     json={
        ...         "policy_name": "Default Retention",
        ...         "entity_type": "resume",
        ...         "retention_days": 365,
        ...         "action_type": "delete",
        ...         "organization_id": None,
        ...         "is_active": True,
        ...         "description": "Default policy for resume retention",
        ...         "legal_basis": "legitimate_interest",
        ...         "deletion_reason": "Retention period expired"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "policy-uuid",
            "policy_name": "Default Retention",
            "entity_type": "resume",
            "retention_days": 365,
            "action_type": "delete",
            "organization_id": null,
            "is_active": true,
            "description": "Default policy for resume retention",
            "legal_basis": "legitimate_interest",
            "deletion_reason": "Retention period expired",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    """
    try:
        logger.info(f"Creating retention policy '{request.policy_name}' for organization: {request.organization_id}")

        # Validate entity_type
        try:
            validated_entity_type = RetentionEntityType(request.entity_type)
        except ValueError:
            valid_types = [e.value for e in RetentionEntityType]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid entity_type '{request.entity_type}'. Must be one of: {', '.join(valid_types)}",
            )

        # Validate action_type
        try:
            validated_action_type = RetentionActionType(request.action_type)
        except ValueError:
            valid_actions = [a.value for a in RetentionActionType]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid action_type '{request.action_type}'. Must be one of: {', '.join(valid_actions)}",
            )

        # Check if policy with same name already exists for this organization/global
        existing_query = select(DataRetentionPolicy).where(
            DataRetentionPolicy.policy_name == request.policy_name,
        )

        if request.organization_id:
            existing_query = existing_query.where(
                DataRetentionPolicy.organization_id == UUID(request.organization_id)
            )
        else:
            # Check for global policies
            existing_query = existing_query.where(
                DataRetentionPolicy.organization_id.is_(None)
            )

        existing = await db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Retention policy '{request.policy_name}' already exists for this scope",
            )

        # Create new retention policy
        new_policy = DataRetentionPolicy(
            policy_name=request.policy_name,
            entity_type=validated_entity_type,
            retention_days=request.retention_days,
            action_type=validated_action_type,
            organization_id=UUID(request.organization_id) if request.organization_id else None,
            is_active=request.is_active,
            description=request.description,
            legal_basis=request.legal_basis,
            deletion_reason=request.deletion_reason,
        )
        db.add(new_policy)
        await db.flush()

        response_data = {
            "id": str(new_policy.id),
            "policy_name": new_policy.policy_name,
            "entity_type": new_policy.entity_type.value,
            "retention_days": new_policy.retention_days,
            "action_type": new_policy.action_type.value,
            "organization_id": str(new_policy.organization_id) if new_policy.organization_id else None,
            "is_active": new_policy.is_active,
            "description": new_policy.description,
            "legal_basis": new_policy.legal_basis,
            "deletion_reason": new_policy.deletion_reason,
            "created_at": new_policy.created_at.isoformat(),
            "updated_at": new_policy.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created retention policy '{request.policy_name}' with ID: {new_policy.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating retention policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create retention policy: {str(e)}",
        ) from e


@router.get("/", tags=["Retention Policies"])
async def list_retention_policies(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID (None for global policies)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List retention policies with optional filters.

    This endpoint retrieves data retention policies with support for filtering
    by organization, entity type, and active status.

    Args:
        organization_id: Optional organization ID filter (None for global policies only)
        entity_type: Optional entity type filter
        is_active: Optional active status filter
        db: Database session

    Returns:
        JSON response with list of retention policies

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/retention-policies/?organization_id=org-123")
        >>> response.json()
        {
            "organization_id": "org-123",
            "policies": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(f"Listing retention policies with filters - organization_id: {organization_id}, entity_type: {entity_type}, is_active: {is_active}")

        # Build query
        query = select(DataRetentionPolicy)

        if organization_id:
            query = query.where(DataRetentionPolicy.organization_id == UUID(organization_id))
        elif organization_id is None and not entity_type and is_active is None:
            # If no filters specified, get all policies
            pass
        else:
            # If organization_id is explicitly None (not just omitted), get global policies
            pass

        if entity_type:
            query = query.where(DataRetentionPolicy.entity_type == entity_type)
        if is_active is not None:
            query = query.where(DataRetentionPolicy.is_active == is_active)

        query = query.order_by(DataRetentionPolicy.policy_name)

        result = await db.execute(query)
        policies = result.scalars().all()

        # Determine response organization_id
        response_org_id = organization_id if organization_id else None

        # Build response
        policies_data = []
        for policy in policies:
            policies_data.append({
                "id": str(policy.id),
                "policy_name": policy.policy_name,
                "entity_type": policy.entity_type.value,
                "retention_days": policy.retention_days,
                "action_type": policy.action_type.value,
                "organization_id": str(policy.organization_id) if policy.organization_id else None,
                "is_active": policy.is_active,
                "description": policy.description,
                "legal_basis": policy.legal_basis,
                "deletion_reason": policy.deletion_reason,
                "created_at": policy.created_at.isoformat(),
                "updated_at": policy.updated_at.isoformat(),
            })

        response_data = {
            "organization_id": response_org_id,
            "policies": policies_data,
            "total_count": len(policies_data),
        }

        logger.info(f"Retrieved {len(policies_data)} retention policies")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing retention policies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list retention policies: {str(e)}",
        ) from e


@router.get("/{policy_id}", tags=["Retention Policies"])
async def get_retention_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific retention policy by ID.

    This endpoint retrieves detailed information about a single retention policy.

    Args:
        policy_id: UUID of the retention policy
        db: Database session

    Returns:
        JSON response with retention policy details

    Raises:
        HTTPException(404): If retention policy is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/retention-policies/policy-uuid")
        >>> response.json()
        {
            "id": "policy-uuid",
            "policy_name": "Default Retention",
            "entity_type": "resume",
            ...
        }
    """
    try:
        logger.info(f"Retrieving retention policy: {policy_id}")

        result = await db.execute(
            select(DataRetentionPolicy).where(DataRetentionPolicy.id == UUID(policy_id))
        )
        policy = result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retention policy not found: {policy_id}",
            )

        response_data = {
            "id": str(policy.id),
            "policy_name": policy.policy_name,
            "entity_type": policy.entity_type.value,
            "retention_days": policy.retention_days,
            "action_type": policy.action_type.value,
            "organization_id": str(policy.organization_id) if policy.organization_id else None,
            "is_active": policy.is_active,
            "description": policy.description,
            "legal_basis": policy.legal_basis,
            "deletion_reason": policy.deletion_reason,
            "created_at": policy.created_at.isoformat(),
            "updated_at": policy.updated_at.isoformat(),
        }

        logger.info(f"Retrieved retention policy: {policy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {policy_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve retention policy: {str(e)}",
        ) from e


@router.put("/{policy_id}", tags=["Retention Policies"])
async def update_retention_policy(
    policy_id: str,
    request: RetentionPolicyUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a retention policy.

    This endpoint updates an existing retention policy configuration.
    Only the fields specified in the request body will be updated.

    Args:
        policy_id: UUID of the retention policy
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated retention policy details

    Raises:
        HTTPException(404): If retention policy is not found
        HTTPException(422): If validation fails
        HTTPException(409): If policy name conflicts with existing policy
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/retention-policies/policy-uuid",
        ...     json={
        ...         "retention_days": 730,
        ...         "is_active": False
        ...     }
        ... )
        >>> response.json()
        {
            "id": "policy-uuid",
            "retention_days": 730,
            "is_active": false,
            ...
        }
    """
    try:
        logger.info(f"Updating retention policy: {policy_id}")

        # Get existing policy
        result = await db.execute(
            select(DataRetentionPolicy).where(DataRetentionPolicy.id == UUID(policy_id))
        )
        policy = result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retention policy not found: {policy_id}",
            )

        # Update fields if provided
        if request.policy_name is not None:
            # Check if new name conflicts with existing policy
            existing_query = select(DataRetentionPolicy).where(
                DataRetentionPolicy.policy_name == request.policy_name,
                DataRetentionPolicy.id != UUID(policy_id),
            )

            # Maintain same scope (organization or global)
            if policy.organization_id:
                existing_query = existing_query.where(
                    DataRetentionPolicy.organization_id == policy.organization_id
                )
            else:
                existing_query = existing_query.where(
                    DataRetentionPolicy.organization_id.is_(None)
                )

            existing = await db.execute(existing_query)
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Retention policy '{request.policy_name}' already exists for this scope",
                )
            policy.policy_name = request.policy_name

        if request.entity_type is not None:
            try:
                policy.entity_type = RetentionEntityType(request.entity_type)
            except ValueError:
                valid_types = [e.value for e in RetentionEntityType]
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid entity_type '{request.entity_type}'. Must be one of: {', '.join(valid_types)}",
                )

        if request.retention_days is not None:
            policy.retention_days = request.retention_days

        if request.action_type is not None:
            try:
                policy.action_type = RetentionActionType(request.action_type)
            except ValueError:
                valid_actions = [a.value for a in RetentionActionType]
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid action_type '{request.action_type}'. Must be one of: {', '.join(valid_actions)}",
                )

        if request.organization_id is not None:
            policy.organization_id = UUID(request.organization_id) if request.organization_id else None

        if request.is_active is not None:
            policy.is_active = request.is_active
        if request.description is not None:
            policy.description = request.description
        if request.legal_basis is not None:
            policy.legal_basis = request.legal_basis
        if request.deletion_reason is not None:
            policy.deletion_reason = request.deletion_reason

        await db.commit()
        await db.refresh(policy)

        response_data = {
            "id": str(policy.id),
            "policy_name": policy.policy_name,
            "entity_type": policy.entity_type.value,
            "retention_days": policy.retention_days,
            "action_type": policy.action_type.value,
            "organization_id": str(policy.organization_id) if policy.organization_id else None,
            "is_active": policy.is_active,
            "description": policy.description,
            "legal_basis": policy.legal_basis,
            "deletion_reason": policy.deletion_reason,
            "created_at": policy.created_at.isoformat(),
            "updated_at": policy.updated_at.isoformat(),
        }

        logger.info(f"Updated retention policy: {policy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {policy_id}",
        )
    except Exception as e:
        logger.error(f"Error updating retention policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update retention policy: {str(e)}",
        ) from e


@router.delete("/{policy_id}", tags=["Retention Policies"])
async def delete_retention_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a retention policy.

    This endpoint permanently deletes a retention policy configuration.
    This action cannot be undone.

    Args:
        policy_id: UUID of the retention policy
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If retention policy is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/retention-policies/policy-uuid")
        >>> response.json()
        {
            "message": "Retention policy deleted successfully",
            "id": "policy-uuid"
        }
    """
    try:
        logger.info(f"Deleting retention policy: {policy_id}")

        # Check if policy exists
        result = await db.execute(
            select(DataRetentionPolicy).where(DataRetentionPolicy.id == UUID(policy_id))
        )
        policy = result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retention policy not found: {policy_id}",
            )

        # Delete the policy
        await db.execute(
            delete(DataRetentionPolicy).where(DataRetentionPolicy.id == UUID(policy_id))
        )
        await db.commit()

        logger.info(f"Deleted retention policy: {policy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Retention policy deleted successfully",
                "id": policy_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {policy_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting retention policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete retention policy: {str(e)}",
        ) from e
