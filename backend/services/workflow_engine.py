"""
Workflow execution engine for no-code/low-code automation

This module provides the core workflow execution functionality including:
- Action execution for various action types
- Conditional logic and branching
- Error handling and recovery
- Progress tracking and logging
- Integration with external services
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse

import httpx

from config import get_settings
from database import async_session_maker
from models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowTriggerType,
    ExecutionStatus,
    ActionType,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class WorkflowExecutionError(Exception):
    """Base exception for workflow execution errors"""

    pass


class ActionExecutionError(WorkflowExecutionError):
    """Exception for action-specific errors"""

    def __init__(self, message: str, action_type: str, action_data: Dict[str, Any]):
        super().__init__(message)
        self.action_type = action_type
        self.action_data = action_data


class WorkflowEngine:
    """
    Engine for executing workflow automations.

    This engine processes workflow definitions, executes actions in sequence,
    handles conditional logic, and tracks execution progress and results.
    """

    # Action type handlers registry
    _action_handlers: Dict[ActionType, Callable] = {}

    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize workflow engine.

        Args:
            session: Optional database session. If not provided, creates a new one.
        """
        self._session = session
        self._own_session = session is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._own_session:
            self._session = async_session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_session and self._session:
            await self.session.close()

    @property
    def session(self) -> AsyncSession:
        """Get the database session, creating one if needed."""
        if self._session is None:
            self._session = async_session_maker()
            self._own_session = True
        return self._session

    @classmethod
    def register_handler(cls, action_type: ActionType, handler: Callable):
        """
        Register a custom action handler.

        Args:
            action_type: The action type to handle
            handler: Async function that takes (engine, action_data, context)
        """
        cls._action_handlers[action_type] = handler
        logger.info(f"Registered action handler for: {action_type}")

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_type: WorkflowTriggerType,
        trigger_data: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow and track the execution.

        Args:
            workflow_id: UUID of the workflow to execute
            trigger_type: Type of trigger that initiated execution
            trigger_data: Data from the trigger event
            input_data: Additional input data for the workflow

        Returns:
            Dictionary with execution result

        Raises:
            WorkflowExecutionError: If workflow execution fails
        """
        # Fetch workflow
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            raise WorkflowExecutionError(f"Workflow not found: {workflow_id}")

        # Check if workflow is active
        if not workflow.is_active:
            raise WorkflowExecutionError(f"Workflow is not active: {workflow_id}")

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            input_data=input_data,
            status=ExecutionStatus.PENDING,
        )
        self.session.add(execution)
        await self.session.commit()

        logger.info(
            f"Starting workflow execution: {workflow.name} ({execution.id})"
        )

        try:
            # Mark execution as started
            execution.start()
            await self.session.commit()

            # Build execution context
            context = {
                "workflow": workflow,
                "execution": execution,
                "trigger": {
                    "type": trigger_type,
                    "data": trigger_data or {},
                },
                "input": input_data or {},
                "output": {},
                "variables": {},
                "errors": [],
            }

            # Execute actions
            action_results = []
            for i, action in enumerate(workflow.actions):
                logger.debug(
                    f"Executing action {i + 1}/{len(workflow.actions)}: "
                    f"{action.get('type', 'unknown')}"
                )

                try:
                    result = await self._execute_action(action, context)
                    action_results.append({
                        "index": i,
                        "action": action,
                        "status": "success",
                        "result": result,
                    })

                    # Check for conditional flow control
                    if result.get("_stop", False):
                        logger.info(f"Workflow stopped at action {i + 1}")
                        break

                except Exception as e:
                    logger.error(f"Action {i + 1} failed: {e}", exc_info=True)
                    action_results.append({
                        "index": i,
                        "action": action,
                        "status": "failed",
                        "error": str(e),
                    })

                    # Determine if we should continue or stop
                    if action.get("continue_on_error", False):
                        context["errors"].append({
                            "action_index": i,
                            "action_type": action.get("type"),
                            "error": str(e),
                        })
                    else:
                        raise ActionExecutionError(
                            f"Action failed: {str(e)}",
                            action.get("type", "unknown"),
                            action
                        ) from e

            # Mark execution as completed
            execution.complete(output_data=context.get("output"))
            execution.action_results = action_results
            await self.session.commit()

            # Update workflow stats
            workflow.record_execution(success=True)
            await self.session.commit()

            logger.info(
                f"Workflow execution completed: {workflow.name} ({execution.id}) "
                f"in {execution.duration_seconds}s"
            )

            return {
                "status": "success",
                "execution_id": str(execution.id),
                "workflow_id": str(workflow.id),
                "output": context.get("output"),
                "duration_seconds": execution.duration_seconds,
                "actions_executed": len(action_results),
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Mark execution as failed
            execution.fail(error_message=str(e))
            execution.action_results = action_results if action_results else None
            await self.session.commit()

            # Update workflow stats
            workflow.record_execution(success=False)
            await self.session.commit()

            raise WorkflowExecutionError(
                f"Workflow execution failed: {str(e)}"
            ) from e

    async def _execute_action(
        self, action: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow action.

        Args:
            action: Action definition with type and params
            context: Execution context

        Returns:
            Action result dictionary

        Raises:
            ActionExecutionError: If action execution fails
        """
        action_type = action.get("type")
        if not action_type:
            raise ActionExecutionError("Missing action type", "unknown", action)

        # Handle conditional actions
        if action_type == ActionType.CONDITIONAL:
            return await self._execute_conditional(action, context)

        # Check if action has a condition
        condition = action.get("condition")
        if condition:
            if not await self._evaluate_condition(condition, context):
                logger.debug(f"Action condition not met, skipping: {action_type}")
                return {"_skipped": True, "reason": "condition_not_met"}

        # Get action parameters
        params = action.get("params", {})

        # Resolve any variable references in params
        resolved_params = await self._resolve_variables(params, context)

        # Execute the action
        if action_type == ActionType.SEND_EMAIL:
            return await self._send_email(resolved_params, context)
        elif action_type == ActionType.SEND_WEBHOOK:
            return await self._send_webhook(resolved_params, context)
        elif action_type == ActionType.SEND_SLACK:
            return await self._send_slack(resolved_params, context)
        elif action_type == ActionType.ADD_TAG:
            return await self._add_tag(resolved_params, context)
        elif action_type == ActionType.REMOVE_TAG:
            return await self._remove_tag(resolved_params, context)
        elif action_type == ActionType.ADD_NOTE:
            return await self._add_note(resolved_params, context)
        elif action_type == ActionType.MOVE_STAGE:
            return await self._move_stage(resolved_params, context)
        elif action_type == ActionType.ASSIGN_RECRUITER:
            return await self._assign_recruiter(resolved_params, context)
        elif action_type == ActionType.UPDATE_FIELD:
            return await self._update_field(resolved_params, context)
        elif action_type == ActionType.CREATE_ENTITY:
            return await self._create_entity(resolved_params, context)
        elif action_type == ActionType.DELETE_ENTITY:
            return await self._delete_entity(resolved_params, context)
        elif action_type == ActionType.TRACK_EVENT:
            return await self._track_event(resolved_params, context)
        elif action_type == ActionType.GENERATE_REPORT:
            return await self._generate_report(resolved_params, context)
        elif action_type == ActionType.EXECUTE_FUNCTION:
            return await self._execute_function(resolved_params, context)
        elif action_type == ActionType.RUN_PLUGIN:
            return await self._run_plugin(resolved_params, context)
        elif action_type == ActionType.LOG:
            return await self._log_action(resolved_params, context)
        elif action_type == ActionType.DELAY:
            return await self._delay_action(resolved_params, context)
        elif action_type in self._action_handlers:
            # Custom handler
            handler = self._action_handlers[action_type]
            return await handler(self, action, context)
        else:
            raise ActionExecutionError(
                f"Unknown action type: {action_type}",
                action_type,
                action
            )

    async def _execute_conditional(
        self, action: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a conditional action (if/else logic).

        Args:
            action: Conditional action definition
            context: Execution context

        Returns:
            Action result dictionary
        """
        condition = action.get("condition")
        if not condition:
            raise ActionExecutionError(
                "Conditional action missing condition",
                ActionType.CONDITIONAL,
                action
            )

        # Evaluate the condition
        condition_met = await self._evaluate_condition(condition, context)

        # Execute the appropriate branch
        if condition_met:
            then_actions = action.get("then", [])
            logger.debug(f"Executing 'then' branch with {len(then_actions)} actions")
            for then_action in then_actions:
                await self._execute_action(then_action, context)
            return {"_branch": "then", "condition_met": True}
        else:
            else_actions = action.get("else", [])
            logger.debug(f"Executing 'else' branch with {len(else_actions)} actions")
            for else_action in else_actions:
                await self._execute_action(else_action, context)
            return {"_branch": "else", "condition_met": False}

    async def _evaluate_condition(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition expression.

        Args:
            condition: Condition definition with operator and values
            context: Execution context

        Returns:
            True if condition is met, False otherwise
        """
        operator = condition.get("operator")
        field = condition.get("field")
        value = condition.get("value")

        # Resolve field value from context
        field_value = await self._get_context_value(field, context)

        # Perform comparison
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return value in str(field_value) if field_value else False
        elif operator == "not_contains":
            return value not in str(field_value) if field_value else True
        elif operator == "greater_than":
            try:
                return float(field_value) > float(value)
            except (TypeError, ValueError):
                return False
        elif operator == "less_than":
            try:
                return float(field_value) < float(value)
            except (TypeError, ValueError):
                return False
        elif operator == "exists":
            return field_value is not None
        elif operator == "not_exists":
            return field_value is None
        elif operator == "in":
            return field_value in value if isinstance(value, list) else False
        elif operator == "not_in":
            return field_value not in value if isinstance(value, list) else True
        else:
            logger.warning(f"Unknown condition operator: {operator}")
            return False

    async def _resolve_variables(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve variable references in parameters.

        Supports syntax like {{trigger.data.candidate_id}} to reference context values.

        Args:
            params: Parameters with potential variable references
            context: Execution context

        Returns:
            Parameters with resolved values
        """
        if isinstance(params, dict):
            resolved = {}
            for key, value in params.items():
                resolved[key] = await self._resolve_variables(value, context)
            return resolved
        elif isinstance(params, list):
            return [await self._resolve_variables(item, context) for item in params]
        elif isinstance(params, str):
            # Check for variable references like {{path.to.value}}
            import re

            pattern = r"\{\{([^}]+)\}\}"

            def replace_var(match):
                path = match.group(1).strip()
                try:
                    return str(await self._get_context_value(path, context))
                except (KeyError, AttributeError, TypeError):
                    return match.group(0)  # Keep original if not found

            return re.sub(pattern, replace_var, params)
        else:
            return params

    async def _get_context_value(
        self, path: str, context: Dict[str, Any]
    ) -> Any:
        """
        Get a value from the context using a dot-notation path.

        Args:
            path: Dot-notation path (e.g., 'trigger.data.candidate_id')
            context: Execution context

        Returns:
            The value at the path

        Raises:
            KeyError: If path is not found
        """
        parts = path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                raise KeyError(f"Path not found: {path}")

            if value is None:
                break

        return value

    # Action handlers

    async def _send_email(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send an email notification."""
        # In a full implementation, this would integrate with an email service
        logger.info(
            f"Sending email to {params.get('to')}: "
            f"{params.get('subject', 'No subject')}"
        )
        context["output"]["email_sent"] = True
        return {"email_sent": True, "to": params.get("to")}

    async def _send_webhook(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a webhook to an external URL."""
        url = params.get("url")
        if not url:
            raise ActionExecutionError("Missing URL for webhook", ActionType.SEND_WEBHOOK, params)

        method = params.get("method", "POST").upper()
        headers = params.get("headers", {})
        body = params.get("body", {})

        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ActionExecutionError(f"Invalid URL: {url}", ActionType.SEND_WEBHOOK, params)

        logger.info(f"Sending webhook to {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=body)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=body)
                else:
                    response = await client.post(url, headers=headers, json=body)

                response.raise_for_status()

                logger.info(f"Webhook sent successfully: {url} - {response.status_code}")

                context["output"]["webhook_sent"] = True
                return {
                    "webhook_sent": True,
                    "url": url,
                    "status_code": response.status_code,
                }

        except httpx.HTTPError as e:
            raise ActionExecutionError(
                f"Webhook failed: {str(e)}",
                ActionType.SEND_WEBHOOK,
                params
            ) from e

    async def _send_slack(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a Slack message."""
        webhook_url = params.get("webhook_url")
        message = params.get("message", "")

        if not webhook_url:
            raise ActionExecutionError("Missing webhook_url for Slack", ActionType.SEND_SLACK, params)

        logger.info(f"Sending Slack message: {message[:50]}...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json={"text": message},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                context["output"]["slack_sent"] = True
                return {"slack_sent": True}

        except httpx.HTTPError as e:
            raise ActionExecutionError(
                f"Slack webhook failed: {str(e)}",
                ActionType.SEND_SLACK,
                params
            ) from e

    async def _add_tag(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a tag to an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        tag = params.get("tag")

        logger.info(f"Adding tag '{tag}' to {entity_type}:{entity_id}")

        # In a full implementation, this would update the database
        context["output"]["tag_added"] = True
        return {"tag_added": True, "tag": tag}

    async def _remove_tag(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Remove a tag from an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        tag = params.get("tag")

        logger.info(f"Removing tag '{tag}' from {entity_type}:{entity_id}")

        context["output"]["tag_removed"] = True
        return {"tag_removed": True, "tag": tag}

    async def _add_note(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a note to an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        note = params.get("note")

        logger.info(f"Adding note to {entity_type}:{entity_id}")

        context["output"]["note_added"] = True
        return {"note_added": True, "note_length": len(note) if note else 0}

    async def _move_stage(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Move an entity to a different stage."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        stage = params.get("stage")

        logger.info(f"Moving {entity_type}:{entity_id} to stage '{stage}'")

        context["output"]["stage_changed"] = True
        return {"stage_changed": True, "stage": stage}

    async def _assign_recruiter(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assign a recruiter to an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        recruiter_id = params.get("recruiter_id")

        logger.info(f"Assigning recruiter {recruiter_id} to {entity_type}:{entity_id}")

        context["output"]["recruiter_assigned"] = True
        return {"recruiter_assigned": True, "recruiter_id": recruiter_id}

    async def _update_field(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a field on an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        field = params.get("field")
        value = params.get("value")

        logger.info(f"Updating {entity_type}:{entity_id}.{field} = {value}")

        context["output"]["field_updated"] = True
        return {"field_updated": True, "field": field}

    async def _create_entity(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new entity."""
        entity_type = params.get("entity_type")
        data = params.get("data", {})

        logger.info(f"Creating {entity_type}: {data}")

        context["output"]["entity_created"] = True
        return {"entity_created": True, "entity_type": entity_type}

    async def _delete_entity(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete an entity."""
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")

        logger.info(f"Deleting {entity_type}:{entity_id}")

        context["output"]["entity_deleted"] = True
        return {"entity_deleted": True, "entity_type": entity_type}

    async def _track_event(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track an analytics event."""
        event_name = params.get("event_name")
        event_data = params.get("data", {})

        logger.info(f"Tracking analytics event: {event_name}")

        context["output"]["event_tracked"] = True
        return {"event_tracked": True, "event_name": event_name}

    async def _generate_report(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a report."""
        report_type = params.get("report_type")
        report_params = params.get("params", {})

        logger.info(f"Generating report: {report_type}")

        # In a full implementation, this would trigger report generation
        context["output"]["report_generated"] = True
        return {"report_generated": True, "report_type": report_type}

    async def _execute_function(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a custom serverless function."""
        function_name = params.get("function_name")
        function_params = params.get("params", {})

        logger.info(f"Executing function: {function_name}")

        # In a full implementation, this would call a serverless function
        context["output"]["function_executed"] = True
        return {"function_executed": True, "function_name": function_name}

    async def _run_plugin(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a plugin action."""
        plugin_id = params.get("plugin_id")
        action = params.get("action")
        action_params = params.get("params", {})

        logger.info(f"Running plugin: {plugin_id}.{action}")

        # In a full implementation, this would execute the plugin
        context["output"]["plugin_run"] = True
        return {"plugin_run": True, "plugin_id": plugin_id}

    async def _log_action(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log a message during workflow execution."""
        message = params.get("message", "")
        level = params.get("level", "info").upper()

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[Workflow] {message}")

        return {"logged": True, "message": message}

    async def _delay_action(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delay execution for a specified time."""
        delay_seconds = params.get("seconds", 0)

        if delay_seconds > 0:
            logger.info(f"Delaying execution for {delay_seconds} seconds")
            await asyncio.sleep(delay_seconds)

        return {"delayed": True, "seconds": delay_seconds}

    async def _get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Fetch a workflow by ID."""
        result = await self.session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def get_workflow_stats(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """
        Get execution statistics for a workflow.

        Args:
            workflow_id: UUID of the workflow

        Returns:
            Dictionary with workflow statistics
        """
        from sqlalchemy import select, func
        from datetime import timedelta

        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            raise WorkflowExecutionError(f"Workflow not found: {workflow_id}")

        # Get execution stats
        result = await self.session.execute(
            select(
                func.count(WorkflowExecution.id).label("total"),
                func.sum(
                    func.cast(
                        WorkflowExecution.status == ExecutionStatus.COMPLETED,
                        type_=int
                    )
                ).label("completed_count"),
                func.sum(
                    func.cast(
                        WorkflowExecution.status == ExecutionStatus.FAILED,
                        type_=int
                    )
                ).label("failed_count"),
                func.avg(WorkflowExecution.duration_seconds).label("avg_duration"),
            ).where(WorkflowExecution.workflow_id == workflow_id)
        )
        stats = result.one()

        # Get recent executions (last 24 hours)
        day_ago = datetime.utcnow() - timedelta(days=1)
        result = await self.session.execute(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.created_at >= day_ago,
            )
        )
        recent_count = result.scalar()

        return {
            "workflow_id": str(workflow_id),
            "workflow_name": workflow.name,
            "status": workflow.status,
            "is_active": workflow.is_active,
            "total_executions": workflow.execution_count,
            "successful_executions": workflow.success_count,
            "failed_executions": workflow.failure_count,
            "success_rate_percent": round(workflow.success_rate, 2),
            "executions_in_db": stats.total or 0,
            "completed_in_db": stats.completed_count or 0,
            "failed_in_db": stats.failed_count or 0,
            "avg_duration_seconds": round(stats.avg_duration or 0, 2),
            "executions_last_24h": recent_count or 0,
            "last_executed_at": workflow.last_executed_at.isoformat()
            if workflow.last_executed_at
            else None,
        }


def get_workflow_engine() -> WorkflowEngine:
    """Get a workflow engine instance."""
    return WorkflowEngine()


__all__ = [
    "WorkflowEngine",
    "get_workflow_engine",
    "WorkflowExecutionError",
    "ActionExecutionError",
]
