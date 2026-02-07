"""
Workflow management endpoints.

This module provides endpoints for:
- Creating workflow automations with triggers and actions
- Listing and managing workflow definitions
- Viewing workflow execution history
- Activating, pausing, and archiving workflows
- Manually triggering workflow executions

Supports no-code/low-code workflow automation with "if X then Y" logic.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowTriggerType,
    WorkflowStatus,
    ExecutionStatus,
    ActionType,
)
from models.api_key import APIKey

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class TriggerConfig(BaseModel):
    """Configuration for a workflow trigger."""

    type: str = Field(..., description="Trigger type: webhook, schedule, or manual")
    event: Optional[str] = Field(None, description="Event type for webhook triggers (e.g., candidate.created)")
    cron_expression: Optional[str] = Field(None, description="Cron expression for schedule triggers")
    webhook_url: Optional[str] = Field(None, description="Generated webhook URL for webhook triggers")


class ActionConfig(BaseModel):
    """Configuration for a workflow action."""

    type: str = Field(..., description="Action type to execute")
    config: Dict[str, Any] = Field(default_factory=dict, description="Action-specific configuration")
    label: Optional[str] = Field(None, description="Human-readable label for this action")


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""

    name: str = Field(..., description="Workflow name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Workflow description")
    trigger: TriggerConfig = Field(..., description="Trigger configuration")
    actions: List[ActionConfig] = Field(
        ...,
        description="List of actions to execute when triggered",
        min_length=1,
    )
    api_key_id: Optional[str] = Field(None, description="Optional API key ID to associate with this workflow")

    @field_validator("trigger")
    def validate_trigger(cls, v):
        """Validate trigger configuration based on type."""
        valid_types = [t.value for t in WorkflowTriggerType]
        if v.type not in valid_types:
            raise ValueError(
                f"Invalid trigger type: {v.type}. Must be one of: {', '.join(valid_types)}"
            )

        if v.type == WorkflowTriggerType.WEBHOOK.value and not v.event:
            raise ValueError("event is required for webhook triggers")

        if v.type == WorkflowTriggerType.SCHEDULE.value and not v.cron_expression:
            raise ValueError("cron_expression is required for schedule triggers")

        return v

    @field_validator("actions")
    def validate_actions(cls, v):
        """Validate action types."""
        valid_types = [a.value for a in ActionType]
        for action in v:
            if action.type not in valid_types:
                raise ValueError(
                    f"Invalid action type: {action.type}. "
                    f"Valid types are: {', '.join(valid_types)}"
                )
        return v


class UpdateWorkflowRequest(BaseModel):
    """Request model for updating a workflow."""

    name: Optional[str] = Field(None, description="Workflow name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Workflow description")
    trigger: Optional[TriggerConfig] = Field(None, description="Trigger configuration")
    actions: Optional[List[ActionConfig]] = Field(
        None,
        description="List of actions to execute when triggered",
        min_length=1,
    )

    @field_validator("trigger")
    def validate_trigger(cls, v):
        """Validate trigger configuration based on type."""
        if v is not None:
            valid_types = [t.value for t in WorkflowTriggerType]
            if v.type not in valid_types:
                raise ValueError(
                    f"Invalid trigger type: {v.type}. Must be one of: {', '.join(valid_types)}"
                )

            if v.type == WorkflowTriggerType.WEBHOOK.value and not v.event:
                raise ValueError("event is required for webhook triggers")

            if v.type == WorkflowTriggerType.SCHEDULE.value and not v.cron_expression:
                raise ValueError("cron_expression is required for schedule triggers")

        return v

    @field_validator("actions")
    def validate_actions(cls, v):
        """Validate action types."""
        if v is not None:
            valid_types = [a.value for a in ActionType]
            for action in v:
                if action.type not in valid_types:
                    raise ValueError(
                        f"Invalid action type: {action.type}. "
                        f"Valid types are: {', '.join(valid_types)}"
                    )
        return v


class WorkflowResponse(BaseModel):
    """Response model for workflow creation."""

    id: str = Field(..., description="Workflow UUID")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    trigger_type: str = Field(..., description="Trigger type")
    trigger_config: Dict[str, Any] = Field(..., description="Trigger configuration")
    actions: List[Dict[str, Any]] = Field(..., description="Workflow actions")
    status: str = Field(..., description="Workflow status")
    version: int = Field(..., description="Workflow version")
    is_active: bool = Field(..., description="Whether workflow is active")
    api_key_id: Optional[str] = Field(None, description="Associated API key ID")
    last_executed_at: Optional[str] = Field(None, description="Last successful execution timestamp")
    execution_count: int = Field(..., description="Total execution count")
    success_count: int = Field(..., description="Successful execution count")
    failure_count: int = Field(..., description="Failed execution count")
    success_rate: float = Field(..., description="Success rate percentage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message: str = Field(..., description="Success message")


class WorkflowListItem(BaseModel):
    """Response model for a workflow in list view."""

    id: str = Field(..., description="Workflow UUID")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    trigger_type: str = Field(..., description="Trigger type")
    status: str = Field(..., description="Workflow status")
    is_active: bool = Field(..., description="Whether workflow is active")
    execution_count: int = Field(..., description="Total execution count")
    success_rate: float = Field(..., description="Success rate percentage")
    last_executed_at: Optional[str] = Field(None, description="Last execution timestamp")
    created_at: str = Field(..., description="Creation timestamp")


class ExecutionInfo(BaseModel):
    """Information about a workflow execution."""

    id: str = Field(..., description="Execution UUID")
    workflow_id: str = Field(..., description="Workflow UUID")
    status: str = Field(..., description="Execution status")
    trigger_type: str = Field(..., description="Trigger type")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_seconds: Optional[int] = Field(None, description="Execution duration in seconds")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    created_at: str = Field(..., description="Creation timestamp")


class ExecutionDetail(BaseModel):
    """Detailed response model for a workflow execution."""

    id: str = Field(..., description="Execution UUID")
    workflow_id: str = Field(..., description="Workflow UUID")
    status: str = Field(..., description="Execution status")
    trigger_type: str = Field(..., description="Trigger type")
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="Data that triggered execution")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data passed to workflow")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data from workflow")
    action_results: Optional[List[Dict[str, Any]]] = Field(None, description="Results from each action")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_seconds: Optional[int] = Field(None, description="Execution duration in seconds")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ExecuteWorkflowRequest(BaseModel):
    """Request model for manual workflow execution."""

    input_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional input data to pass to the workflow",
    )


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Workflows"],
)
async def create_workflow(
    request: Request,
    workflow_data: CreateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new workflow.

    Creates a workflow automation with triggers and actions.
    Workflows can be triggered by webhooks, schedules, or manual execution.

    Args:
        request: FastAPI request object
        workflow_data: Workflow details (name, description, trigger, actions, optional api_key_id)
        db: Database session

    Returns:
        JSON response with created workflow details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If api_key_id is provided but key not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Notify on new candidate",
        ...     "description": "Send notification when a candidate is created",
        ...     "trigger": {"type": "webhook", "event": "candidate.created"},
        ...     "actions": [{"type": "log", "config": {"message": "Candidate created"}}]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/workflows/",
        ...     json=data
        ... )
        >>> workflow = response.json()
    """
    try:
        logger.info(
            f"Creating workflow - name: {workflow_data.name}, "
            f"trigger_type: {workflow_data.trigger.type}"
        )

        # Validate api_key_id if provided
        api_key_uuid = None
        if workflow_data.api_key_id:
            try:
                api_key_uuid = UUID(workflow_data.api_key_id)
                # Verify API key exists
                api_key_query = select(APIKey).where(APIKey.id == api_key_uuid)
                api_key_result = await db.execute(api_key_query)
                api_key = api_key_result.scalar_one_or_none()
                if not api_key:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"API key not found: {workflow_data.api_key_id}",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid API key ID format: {workflow_data.api_key_id}",
                )

        # Build trigger config
        trigger_config = {
            "type": workflow_data.trigger.type,
        }
        if workflow_data.trigger.event:
            trigger_config["event"] = workflow_data.trigger.event
        if workflow_data.trigger.cron_expression:
            trigger_config["cron_expression"] = workflow_data.trigger.cron_expression

        # Build actions list
        actions_list = []
        for action in workflow_data.actions:
            action_dict = {
                "type": action.type,
                "config": action.config,
            }
            if action.label:
                action_dict["label"] = action.label
            actions_list.append(action_dict)

        # Create the workflow
        new_workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            trigger_type=WorkflowTriggerType(workflow_data.trigger.type),
            trigger_config=trigger_config,
            actions=actions_list,
            status=WorkflowStatus.DRAFT,
            version=1,
            is_active=False,
            api_key_id=api_key_uuid,
        )

        db.add(new_workflow)
        await db.commit()
        await db.refresh(new_workflow)

        logger.info(f"Workflow created successfully: {new_workflow.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_workflow.id),
                "name": new_workflow.name,
                "description": new_workflow.description,
                "trigger_type": new_workflow.trigger_type.value,
                "trigger_config": new_workflow.trigger_config,
                "actions": new_workflow.actions,
                "status": new_workflow.status.value,
                "version": new_workflow.version,
                "is_active": new_workflow.is_active,
                "api_key_id": str(new_workflow.api_key_id) if new_workflow.api_key_id else None,
                "last_executed_at": new_workflow.last_executed_at.isoformat() if new_workflow.last_executed_at else None,
                "execution_count": new_workflow.execution_count,
                "success_count": new_workflow.success_count,
                "failure_count": new_workflow.failure_count,
                "success_rate": round(new_workflow.success_rate, 2),
                "created_at": new_workflow.created_at.isoformat() if new_workflow.created_at else None,
                "updated_at": new_workflow.updated_at.isoformat() if new_workflow.updated_at else None,
                "message": "Workflow created successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=List[WorkflowListItem],
    tags=["Workflows"],
)
async def list_workflows(
    request: Request,
    status_filter: Optional[str] = Query(None, description="Filter by workflow status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all workflows.

    Returns a paginated list of workflows with their metadata.
    Can be filtered by status, active status, and trigger type.

    Args:
        request: FastAPI request object
        status_filter: Optional filter by workflow status
        is_active: Optional filter by active status
        trigger_type: Optional filter by trigger type
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of workflows

    Raises:
        HTTPException(400): If filter values are invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all workflows
        >>> response = requests.get("http://localhost:8000/api/workflows/")
        >>> # Get only active workflows
        >>> response = requests.get("http://localhost:8000/api/workflows/?is_active=true")
        >>> # Get webhook workflows
        >>> response = requests.get("http://localhost:8000/api/workflows/?trigger_type=webhook")
        >>> workflows = response.json()
    """
    try:
        logger.info(
            f"Fetching workflows - status: {status_filter}, is_active: {is_active}, "
            f"trigger_type: {trigger_type}, skip: {skip}, limit: {limit}"
        )

        # Build query
        query = select(Workflow)

        # Apply filters
        if status_filter:
            try:
                status_enum = WorkflowStatus(status_filter)
                query = query.where(Workflow.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. "
                    f"Valid values are: {', '.join([s.value for s in WorkflowStatus])}",
                )

        if is_active is not None:
            query = query.where(Workflow.is_active == is_active)

        if trigger_type:
            try:
                trigger_enum = WorkflowTriggerType(trigger_type)
                query = query.where(Workflow.trigger_type == trigger_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid trigger_type: {trigger_type}. "
                    f"Valid values are: {', '.join([t.value for t in WorkflowTriggerType])}",
                )

        # Order by most recently created
        query = query.order_by(Workflow.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        workflows = result.scalars().all()

        # Convert to response format
        workflows_list = []
        for wf in workflows:
            workflows_list.append({
                "id": str(wf.id),
                "name": wf.name,
                "description": wf.description,
                "trigger_type": wf.trigger_type.value,
                "status": wf.status.value,
                "is_active": wf.is_active,
                "execution_count": wf.execution_count,
                "success_rate": round(wf.success_rate, 2),
                "last_executed_at": wf.last_executed_at.isoformat() if wf.last_executed_at else None,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
            })

        logger.info(f"Retrieved {len(workflows_list)} workflows")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=workflows_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}",
        ) from e


@router.get(
    "/{workflow_id}",
    tags=["Workflows"],
)
async def get_workflow(
    request: Request,
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific workflow.

    Returns details for a specific workflow including its configuration
    and execution statistics.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        JSON response with workflow details

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}"
        ... )
        >>> workflow = response.json()
    """
    try:
        logger.info(f"Fetching workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        workflow_data = {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "trigger_type": workflow.trigger_type.value,
            "trigger_config": workflow.trigger_config,
            "actions": workflow.actions,
            "status": workflow.status.value,
            "version": workflow.version,
            "is_active": workflow.is_active,
            "api_key_id": str(workflow.api_key_id) if workflow.api_key_id else None,
            "last_executed_at": workflow.last_executed_at.isoformat() if workflow.last_executed_at else None,
            "execution_count": workflow.execution_count,
            "success_count": workflow.success_count,
            "failure_count": workflow.failure_count,
            "success_rate": round(workflow.success_rate, 2),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=workflow_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow: {str(e)}",
        ) from e


@router.put(
    "/{workflow_id}",
    tags=["Workflows"],
)
async def update_workflow(
    request: Request,
    workflow_id: str,
    workflow_data: UpdateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a workflow.

    Updates the name, description, trigger, or actions of an existing workflow.
    When updating trigger or actions, the version number is incremented.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        workflow_data: Updated workflow details
        db: Database session

    Returns:
        JSON response with updated workflow details

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Updated workflow name",
        ...     "description": "Updated description"
        ... }
        >>> response = requests.put(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}",
        ...     json=data
        ... )
        >>> workflow = response.json()
    """
    try:
        logger.info(f"Updating workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Update fields if provided
        if workflow_data.name is not None:
            workflow.name = workflow_data.name
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        if workflow_data.trigger is not None:
            # Build trigger config
            trigger_config = {
                "type": workflow_data.trigger.type,
            }
            if workflow_data.trigger.event:
                trigger_config["event"] = workflow_data.trigger.event
            if workflow_data.trigger.cron_expression:
                trigger_config["cron_expression"] = workflow_data.trigger.cron_expression

            workflow.trigger_type = WorkflowTriggerType(workflow_data.trigger.type)
            workflow.trigger_config = trigger_config
            workflow.version += 1
        if workflow_data.actions is not None:
            # Build actions list
            actions_list = []
            for action in workflow_data.actions:
                action_dict = {
                    "type": action.type,
                    "config": action.config,
                }
                if action.label:
                    action_dict["label"] = action.label
                actions_list.append(action_dict)

            workflow.actions = actions_list
            workflow.version += 1

        await db.commit()
        await db.refresh(workflow)

        logger.info(f"Workflow updated successfully: {workflow_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(workflow.id),
                "name": workflow.name,
                "description": workflow.description,
                "trigger_type": workflow.trigger_type.value,
                "trigger_config": workflow.trigger_config,
                "actions": workflow.actions,
                "status": workflow.status.value,
                "version": workflow.version,
                "is_active": workflow.is_active,
                "api_key_id": str(workflow.api_key_id) if workflow.api_key_id else None,
                "last_executed_at": workflow.last_executed_at.isoformat() if workflow.last_executed_at else None,
                "execution_count": workflow.execution_count,
                "success_count": workflow.success_count,
                "failure_count": workflow.failure_count,
                "success_rate": round(workflow.success_rate, 2),
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                "message": "Workflow updated successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}",
        ) from e


@router.delete(
    "/{workflow_id}",
    tags=["Workflows"],
)
async def delete_workflow(
    request: Request,
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a workflow.

    Permanently deletes a workflow and all its execution history.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        JSON response with deletion confirmation

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}"
        ... )
        >>> result = response.json()
    """
    try:
        logger.info(f"Deleting workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Delete the workflow (cascade will delete executions)
        await db.delete(workflow)
        await db.commit()

        logger.info(f"Workflow deleted successfully: {workflow_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": workflow_id,
                "message": "Workflow deleted successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {str(e)}",
        ) from e


@router.post(
    "/{workflow_id}/activate",
    tags=["Workflows"],
)
async def activate_workflow(
    request: Request,
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Activate a workflow.

    Activates a workflow so it can be triggered by its configured trigger.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        JSON response with activated workflow details

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}/activate"
        ... )
        >>> result = response.json()
        >>> assert result["is_active"] == True
    """
    try:
        logger.info(f"Activating workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Check if already active
        if workflow.is_active:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": str(workflow.id),
                    "name": workflow.name,
                    "is_active": workflow.is_active,
                    "status": workflow.status.value,
                    "message": "Workflow is already active",
                },
            )

        # Activate the workflow
        workflow.activate()
        await db.commit()
        await db.refresh(workflow)

        logger.info(f"Workflow activated successfully: {workflow_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(workflow.id),
                "name": workflow.name,
                "is_active": workflow.is_active,
                "status": workflow.status.value,
                "message": "Workflow activated successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating workflow {workflow_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate workflow: {str(e)}",
        ) from e


@router.post(
    "/{workflow_id}/pause",
    tags=["Workflows"],
)
async def pause_workflow(
    request: Request,
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Pause a workflow.

    Pauses a workflow so it will not be triggered until reactivated.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        JSON response with paused workflow details

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}/pause"
        ... )
        >>> result = response.json()
        >>> assert result["is_active"] == False
    """
    try:
        logger.info(f"Pausing workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Check if already paused
        if not workflow.is_active:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": str(workflow.id),
                    "name": workflow.name,
                    "is_active": workflow.is_active,
                    "status": workflow.status.value,
                    "message": "Workflow is already paused",
                },
            )

        # Pause the workflow
        workflow.pause()
        await db.commit()
        await db.refresh(workflow)

        logger.info(f"Workflow paused successfully: {workflow_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(workflow.id),
                "name": workflow.name,
                "is_active": workflow.is_active,
                "status": workflow.status.value,
                "message": "Workflow paused successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing workflow {workflow_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause workflow: {str(e)}",
        ) from e


@router.get(
    "/{workflow_id}/executions",
    tags=["Workflows"],
)
async def get_workflow_executions(
    request: Request,
    workflow_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by execution status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get execution history for a workflow.

    Returns a paginated list of executions for a specific workflow.
    Useful for monitoring and debugging workflow performance.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        status_filter: Optional filter by execution status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of executions

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}/executions"
        ... )
        >>> executions = response.json()
    """
    try:
        logger.info(
            f"Fetching executions for workflow {workflow_id} - "
            f"status: {status_filter}, skip: {skip}, limit: {limit}"
        )

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Verify workflow exists
        workflow_query = select(Workflow).where(Workflow.id == workflow_uuid)
        workflow_result = await db.execute(workflow_query)
        workflow = workflow_result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Build query for executions
        query = select(WorkflowExecution).where(
            WorkflowExecution.workflow_id == workflow_uuid
        )

        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = ExecutionStatus(status_filter)
                query = query.where(WorkflowExecution.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. "
                    f"Valid values are: {', '.join([s.value for s in ExecutionStatus])}",
                )

        # Order by most recently created
        query = query.order_by(
            WorkflowExecution.created_at.desc()
        ).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        executions = result.scalars().all()

        # Convert to response format
        executions_list = []
        for exe in executions:
            executions_list.append({
                "id": str(exe.id),
                "workflow_id": str(exe.workflow_id),
                "status": exe.status.value,
                "trigger_type": exe.trigger_type.value,
                "error_message": exe.error_message,
                "duration_seconds": exe.duration_seconds,
                "started_at": exe.started_at.isoformat() if exe.started_at else None,
                "completed_at": exe.completed_at.isoformat() if exe.completed_at else None,
                "created_at": exe.created_at.isoformat() if exe.created_at else None,
            })

        logger.info(f"Retrieved {len(executions_list)} executions for workflow {workflow_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "workflow_id": workflow_id,
                "total_executions": len(executions_list),
                "executions": executions_list,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching executions for workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch executions: {str(e)}",
        ) from e


@router.post(
    "/{workflow_id}/execute",
    tags=["Workflows"],
)
async def execute_workflow(
    request: Request,
    workflow_id: str,
    execute_data: ExecuteWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Manually trigger a workflow execution.

    Creates a new execution record and runs the workflow with optional input data.

    Args:
        request: FastAPI request object
        workflow_id: Workflow UUID
        execute_data: Optional input data for the workflow
        db: Database session

    Returns:
        JSON response with execution details

    Raises:
        HTTPException(400): If workflow_id is not a valid UUID
        HTTPException(404): If workflow not found
        HTTPException(500): If execution fails

    Examples:
        >>> import requests
        >>> data = {"input_data": {"candidate_id": "abc-123"}}
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/workflows/{workflow_id}/execute",
        ...     json=data
        ... )
        >>> execution = response.json()
    """
    try:
        logger.info(f"Manually executing workflow: {workflow_id}")

        # Parse workflow_id as UUID
        try:
            workflow_uuid = UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow ID format: {workflow_id}",
            )

        # Get the workflow
        query = select(Workflow).where(Workflow.id == workflow_uuid)
        result = await db.execute(query)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow_uuid,
            status=ExecutionStatus.PENDING,
            trigger_type=WorkflowTriggerType.MANUAL,
            trigger_data={"source": "api"},
            input_data=execute_data.input_data,
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        # Start execution
        execution.start()

        # For now, just mark as completed with a simple log action
        # In a full implementation, this would execute the actual workflow actions
        action_results = []
        for action in workflow.actions:
            if action.get("type") == ActionType.LOG.value:
                message = action.get("config", {}).get("message", "Workflow executed")
                action_results.append({
                    "type": "log",
                    "status": "success",
                    "message": message,
                })
                logger.info(f"Workflow {workflow_id} - Log action: {message}")

        execution.complete(output_data={"action_results": action_results})

        # Record execution on workflow
        workflow.record_execution(success=True)

        await db.commit()
        await db.refresh(execution)

        logger.info(f"Workflow executed successfully: {workflow_id}, execution: {execution.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(execution.id),
                "workflow_id": str(execution.workflow_id),
                "status": execution.status.value,
                "trigger_type": execution.trigger_type.value,
                "input_data": execution.input_data,
                "output_data": execution.output_data,
                "action_results": execution.action_results,
                "duration_seconds": execution.duration_seconds,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "message": "Workflow executed successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}",
        ) from e
