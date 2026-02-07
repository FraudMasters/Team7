"""
Celery tasks for workflow execution and automation

This module provides workflow-related tasks including:
- Manual workflow execution
- Scheduled workflow triggers
- Webhook-triggered workflows
- Batch workflow operations
- Workflow health monitoring
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowTriggerType,
    WorkflowStatus,
    ExecutionStatus,
)

# Import workflow_engine - lazy import to avoid module load errors
import sys
from pathlib import Path

def _get_workflow_functions():
    """Lazy import of workflow engine functions."""
    _services_path = Path(__file__).parent.parent / 'services'
    if str(_services_path) not in sys.path:
        sys.path.insert(0, str(_services_path))
    from workflow_engine import get_workflow_engine
    return get_workflow_engine

# For direct imports compatibility
try:
    from services.workflow_engine import get_workflow_engine
except (ImportError, ModuleNotFoundError):
    get_workflow_engine = _get_workflow_functions

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.workflow.execute_workflow",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def execute_workflow_task(
    self,
    workflow_id: str,
    trigger_type: str = "manual",
    trigger_data: Optional[Dict[str, Any]] = None,
    input_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a workflow with the given ID.

    This task executes a workflow with the provided trigger data and input.
    It tracks execution status and results in the database.

    Args:
        workflow_id: UUID of the workflow to execute
        trigger_type: Type of trigger (webhook, schedule, manual)
        trigger_data: Data from the trigger event
        input_data: Additional input data for the workflow

    Returns:
        Dictionary with execution result

    Example:
        >>> result = execute_workflow_task.delay(
        ...     workflow_id="abc-123",
        ...     trigger_type="webhook",
        ...     trigger_data={"event": "candidate.created"}
        ... )
    """
    import asyncio

    logger.info(f"Executing workflow: {workflow_id} (trigger: {trigger_type})")

    async def _execute():
        async with async_session_maker() as session:
            engine = get_workflow_engine(session=session)

            trigger_type_enum = WorkflowTriggerType(trigger_type)

            return await engine.execute_workflow(
                workflow_id=workflow_id,
                trigger_type=trigger_type_enum,
                trigger_data=trigger_data,
                input_data=input_data,
            )

    try:
        result = asyncio.run(_execute())
        logger.info(f"Workflow execution completed: {workflow_id}")
        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)

        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Workflow max retries exceeded: {workflow_id}")
            return {
                "status": "failed",
                "workflow_id": workflow_id,
                "error": str(e),
            }


@shared_task(
    name="tasks.workflow.trigger_webhook_workflow",
    bind=True,
)
def trigger_webhook_workflow_task(
    self,
    webhook_event: str,
    event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Trigger all workflows that listen to a specific webhook event.

    This task finds all active workflows with webhook triggers matching
    the event and executes them asynchronously.

    Args:
        webhook_event: Event type (e.g., "candidate.created", "ranked.updated")
        event_data: Event payload data

    Returns:
        Dictionary with trigger results including list of execution IDs

    Example:
        >>> result = trigger_webhook_workflow_task.delay(
        ...     webhook_event="candidate.created",
        ...     event_data={"candidate_id": "abc-123"}
        ... )
    """
    import asyncio

    logger.info(f"Triggering webhook workflows for event: {webhook_event}")

    async def _trigger():
        async with async_session_maker() as session:
            # Find all active workflows with matching webhook triggers
            result = await session.execute(
                select(Workflow).where(
                    Workflow.is_active == True,
                    Workflow.trigger_type == WorkflowTriggerType.WEBHOOK,
                )
            )
            workflows = result.scalars().all()

            # Filter workflows that match this event
            matching_workflows = []
            for workflow in workflows:
                trigger_config = workflow.trigger_config or {}
                if trigger_config.get("event") == webhook_event:
                    matching_workflows.append(workflow)

            logger.info(
                f"Found {len(matching_workflows)} matching workflows for {webhook_event}"
            )

            # Queue execution tasks for each matching workflow
            execution_ids = []
            for workflow in matching_workflows:
                # Create a new Celery task for each workflow execution
                task_result = execute_workflow_task.delay(
                    workflow_id=str(workflow.id),
                    trigger_type="webhook",
                    trigger_data={
                        "event": webhook_event,
                        "data": event_data,
                    },
                    input_data=event_data,
                )
                execution_ids.append(task_result.id)

            return {
                "event": webhook_event,
                "workflows_triggered": len(matching_workflows),
                "execution_ids": execution_ids,
            }

    try:
        result = asyncio.run(_trigger())
        logger.info(f"Webhook workflows triggered: {result['workflows_triggered']}")
        return result

    except Exception as e:
        logger.error(f"Failed to trigger webhook workflows: {e}", exc_info=True)
        return {
            "status": "failed",
            "event": webhook_event,
            "error": str(e),
        }


@shared_task(
    name="tasks.workflow.execute_scheduled_workflows",
    bind=True,
)
def execute_scheduled_workflows_task(self) -> Dict[str, Any]:
    """
    Execute all scheduled workflows that are due.

    This task is meant to be run by Celery beat on a schedule.
    It finds all active schedule-triggered workflows and checks if
    they are due to run based on their cron configuration.

    Returns:
        Dictionary with execution results

    Example:
        >>> # This would be configured in Celery beat:
        >>> # schedule {
        >>> #   'execute-scheduled-workflows': {
        >>> #     'task': 'tasks.workflow.execute_scheduled_workflows',
        >>> #     'schedule': crontab(minute='*'),  # Every minute
        >>> #   }
        >>> # }
    """
    import asyncio

    logger.info("Checking for scheduled workflows to execute")

    async def _execute():
        async with async_session_maker() as session:
            # Find all active schedule-triggered workflows
            result = await session.execute(
                select(Workflow).where(
                    Workflow.is_active == True,
                    Workflow.trigger_type == WorkflowTriggerType.SCHEDULE,
                )
            )
            workflows = result.scalars().all()

            # Check each workflow to see if it should run now
            from croniter import croniter

            now = datetime.utcnow()
            triggered_workflows = []

            for workflow in workflows:
                trigger_config = workflow.trigger_config or {}
                cron_expression = trigger_config.get("cron")

                if not cron_expression:
                    continue

                # Check if workflow should run based on cron
                try:
                    cron = croniter(cron_expression, workflow.last_executed_at or workflow.created_at)
                    next_run = cron.get_next(datetime)

                    if next_run <= now:
                        triggered_workflows.append(workflow)
                except Exception as e:
                    logger.warning(
                        f"Invalid cron expression for workflow {workflow.id}: {e}"
                    )

            logger.info(f"Found {len(triggered_workflows)} scheduled workflows to execute")

            # Queue execution tasks
            execution_ids = []
            for workflow in triggered_workflows:
                task_result = execute_workflow_task.delay(
                    workflow_id=str(workflow.id),
                    trigger_type="schedule",
                    trigger_data={
                        "cron": workflow.trigger_config.get("cron"),
                        "scheduled_time": now.isoformat(),
                    },
                )
                execution_ids.append(task_result.id)

            return {
                "workflows_executed": len(triggered_workflows),
                "execution_ids": execution_ids,
            }

    try:
        result = asyncio.run(_execute())
        logger.info(f"Scheduled workflows executed: {result['workflows_executed']}")
        return result

    except Exception as e:
        logger.error(f"Failed to execute scheduled workflows: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.workflow.batch_execute_workflows",
    bind=True,
    max_retries=2,
)
def batch_execute_workflows_task(
    self,
    workflow_ids: List[str],
    trigger_type: str = "manual",
    common_input_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute multiple workflows in batch.

    This task executes a list of workflows with optional common input data.
    Each workflow will be executed as a separate Celery task.

    Args:
        workflow_ids: List of workflow UUIDs to execute
        trigger_type: Type of trigger for all workflows
        common_input_data: Input data passed to all workflows

    Returns:
        Dictionary with batch execution results

    Example:
        >>> result = batch_execute_workflows_task.delay(
        ...     workflow_ids=["abc-123", "def-456"],
        ...     trigger_type="manual",
        ...     common_input_data={"candidate_id": "xyz"}
        ... )
    """
    logger.info(f"Batch executing {len(workflow_ids)} workflows")

    task_ids = []
    for workflow_id in workflow_ids:
        try:
            task_result = execute_workflow_task.delay(
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                input_data=common_input_data,
            )
            task_ids.append({
                "workflow_id": workflow_id,
                "task_id": task_result.id,
                "status": "queued",
            })
        except Exception as e:
            logger.error(f"Failed to queue workflow {workflow_id}: {e}")
            task_ids.append({
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
            })

    logger.info(f"Queued {len(task_ids)} workflow executions")

    return {
        "status": "queued",
        "total_workflows": len(workflow_ids),
        "queued_count": len([t for t in task_ids if t["status"] == "queued"]),
        "failed_count": len([t for t in task_ids if t["status"] == "failed"]),
        "tasks": task_ids,
    }


@shared_task(
    name="tasks.workflow.get_workflow_stats",
    bind=True,
)
def get_workflow_stats_task(self, workflow_id: str) -> Dict[str, Any]:
    """
    Get execution statistics for a workflow.

    Args:
        workflow_id: UUID of the workflow

    Returns:
        Dictionary with workflow statistics

    Example:
        >>> result = get_workflow_stats_task.delay(workflow_id="abc-123")
        >>> stats = result.get()
        >>> print(stats['success_rate_percent'])
    """
    import asyncio

    logger.info(f"Getting stats for workflow: {workflow_id}")

    async def _get_stats():
        async with async_session_maker() as session:
            engine = get_workflow_engine(session=session)
            return await engine.get_workflow_stats(workflow_id=workflow_id)

    try:
        stats = asyncio.run(_get_stats())
        return stats

    except Exception as e:
        logger.error(f"Failed to get workflow stats: {e}", exc_info=True)
        return {
            "status": "failed",
            "workflow_id": workflow_id,
            "error": str(e),
        }


@shared_task(
    name="tasks.workflow.cleanup_old_executions",
    bind=True,
)
def cleanup_old_executions_task(
    self,
    retention_days: int = 30,
    keep_failed: bool = True,
) -> Dict[str, Any]:
    """
    Clean up old workflow execution records.

    Args:
        retention_days: Number of days to retain executions
        keep_failed: Whether to keep failed executions longer

    Returns:
        Dictionary with cleanup results

    Example:
        >>> result = cleanup_old_executions_task.delay(retention_days=30)
    """
    import asyncio

    logger.info(f"Cleaning up workflow executions older than {retention_days} days")

    async def _cleanup():
        async with async_session_maker() as session:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Build query
            query = select(WorkflowExecution).where(
                WorkflowExecution.created_at < cutoff_date
            )

            # Optionally keep failed executions
            if keep_failed:
                query = query.where(
                    WorkflowExecution.status != ExecutionStatus.FAILED
                )

            # Also keep running executions
            query = query.where(
                WorkflowExecution.status != ExecutionStatus.RUNNING,
                WorkflowExecution.status != ExecutionStatus.PENDING,
            )

            result = await session.execute(query)
            old_executions = result.scalars().all()

            # Delete executions
            deleted_count = 0
            for execution in old_executions:
                await session.delete(execution)
                deleted_count += 1

            await session.commit()

            logger.info(f"Deleted {deleted_count} old workflow executions")

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }

    try:
        result = asyncio.run(_cleanup())
        return result

    except Exception as e:
        logger.error(f"Workflow execution cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.workflow.workflow_health_check",
    bind=True,
)
def workflow_health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for the workflow system.

    Verifies:
    - Active workflows can be queried
    - Workflow engine can be initialized
    - Database connections are working

    Returns:
        Dictionary with health check results
    """
    import asyncio

    logger.info("Running workflow health check")

    async def _check():
        results = {
            "status": "healthy",
            "checks": {},
        }

        # Check database connectivity
        try:
            async with async_session_maker() as session:
                # Try to query workflows
                result = await session.execute(
                    select(func.count(Workflow.id))
                )
                count = result.scalar()

                results["checks"]["database"] = {
                    "status": "ok",
                    "workflows_count": count,
                }
        except Exception as e:
            results["checks"]["database"] = {
                "status": "error",
                "error": str(e),
            }
            results["status"] = "unhealthy"

        # Check workflow engine initialization
        try:
            engine = get_workflow_engine()
            results["checks"]["engine"] = {
                "status": "ok",
            }
        except Exception as e:
            results["checks"]["engine"] = {
                "status": "error",
                "error": str(e),
            }
            results["status"] = "unhealthy"

        # Check active workflows
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Workflow).where(
                        Workflow.is_active == True
                    ).limit(1)
                )
                has_active = result.scalar_one_or_none() is not None

                results["checks"]["active_workflows"] = {
                    "status": "ok",
                    "has_active": has_active,
                }
        except Exception as e:
            results["checks"]["active_workflows"] = {
                "status": "error",
                "error": str(e),
            }

        logger.info(f"Workflow health check completed: {results['status']}")

        return results

    try:
        return asyncio.run(_check())
    except Exception as e:
        logger.error(f"Workflow health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# Import func for health check
from sqlalchemy import func


__all__ = [
    "execute_workflow_task",
    "trigger_webhook_workflow_task",
    "execute_scheduled_workflows_task",
    "batch_execute_workflows_task",
    "get_workflow_stats_task",
    "cleanup_old_executions_task",
    "workflow_health_check_task",
]
