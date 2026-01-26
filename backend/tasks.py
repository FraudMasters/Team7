"""
Celery application for async task processing.

This module initializes the Celery application with Redis broker and provides
task definitions for long-running operations like resume analysis.
"""
import logging
from typing import Dict, Any, Optional

from celery import Celery, shared_task
from celery.result import AsyncResult

from .celery_config import get_celery_config
from .config import get_settings
from .tasks import (
    analyze_resume_async,
    batch_analyze_resumes,
    generate_scheduled_reports,
    process_all_pending_reports,
    send_feedback_notification,
    send_batch_notification,
    check_resume_against_saved_searches,
    send_search_alert_notification,
    process_pending_alerts,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery application instance
# Using 'backend.tasks' as the main module name
celery_app = Celery(
    "backend.tasks",
    config_source=get_celery_config(),
)

# Optional: Explicitly set configuration from dictionary
celery_app.conf.update(get_celery_config())

# Log startup information
logger.info("Celery application initialized")
logger.info(f"Broker URL: {settings.celery_broker_url}")
logger.info(f"Result Backend: {settings.celery_result_backend}")


@shared_task(
    name="tasks.health_check",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def health_check_task(self) -> Dict[str, Any]:
    """
    Simple health check task to verify Celery worker is functioning.

    This task performs basic checks and returns status information.
    Useful for monitoring Celery worker health and connectivity.

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing health status information

    Example:
        >>> from tasks import health_check_task
        >>> result = health_check_task.delay()
        >>> print(result.get())
        {'status': 'healthy', 'worker': 'celery@hostname'}
    """
    logger.info("Health check task executed")
    return {
        "status": "healthy",
        "worker": self.request.hostname,
        "task_id": self.request.id,
        "message": "Celery worker is operational",
    }


@shared_task(
    name="tasks.add_numbers",
    bind=True,
    max_retries=3,
)
def add_numbers_task(self, x: int, y: int) -> int:
    """
    Simple addition task for testing Celery functionality.

    This is a basic task that adds two numbers together. Useful for
    testing Celery setup, task execution, and result retrieval.

    Args:
        self: Celery task instance (bind=True)
        x: First number to add
        y: Second number to add

    Returns:
        Sum of x and y

    Raises:
        ValueError: If inputs are not integers

    Example:
        >>> from tasks import add_numbers_task
        >>> result = add_numbers_task.delay(5, 3)
        >>> print(result.get())
        8
    """
    if not isinstance(x, int) or not isinstance(y, int):
        error_msg = f"Both inputs must be integers, got {type(x)} and {type(y)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    result = x + y
    logger.info(f"Task {self.request.id}: {x} + {y} = {result}")
    return result


@shared_task(
    name="tasks.long_running_task",
    bind=True,
    max_retries=2,
)
def long_running_task(
    self,
    duration_seconds: int = 10,
    progress_updates: bool = True,
) -> Dict[str, Any]:
    """
    Simulated long-running task for testing async processing.

    This task simulates a long-running operation with optional progress
    updates. Useful for testing background task execution, monitoring,
    and progress tracking.

    Args:
        self: Celery task instance (bind=True)
        duration_seconds: How long the task should run (default: 10 seconds)
        progress_updates: Whether to send progress updates (default: True)

    Returns:
        Dictionary containing task completion status and timing information

    Example:
        >>> from tasks import long_running_task
        >>> result = long_running_task.delay(duration_seconds=5)
        >>> # Can check result.status for 'PROGRESS' updates
        >>> print(result.get())
        {'status': 'completed', 'duration': 5, 'steps': 5}
    """
    import time

    logger.info(
        f"Long-running task {self.request.id} started (duration: {duration_seconds}s)"
    )

    steps = 5
    step_duration = duration_seconds / steps

    for i in range(steps):
        # Simulate work
        time.sleep(step_duration)

        # Update progress if enabled
        if progress_updates:
            progress = {
                "current": i + 1,
                "total": steps,
                "percentage": int((i + 1) / steps * 100),
                "status": "in_progress",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id} progress: {progress['percentage']}%")

    logger.info(f"Long-running task {self.request.id} completed")

    return {
        "status": "completed",
        "task_id": self.request.id,
        "duration_seconds": duration_seconds,
        "steps_completed": steps,
        "message": "Long-running task completed successfully",
    }


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a Celery task by its ID.

    This function retrieves the current status, result, and metadata
    for a given task ID. Useful for checking task progress and results.

    Args:
        task_id: The Celery task ID to check

    Returns:
        Dictionary containing task status information:
        - task_id: The task ID
        - state: Current task state (PENDING, STARTED, SUCCESS, FAILURE, etc.)
        - result: Task result (if successful)
        - error: Error message (if failed)
        - info: Additional task metadata (for PROGRESS state)

    Example:
        >>> from tasks import get_task_status
        >>> status = get_task_status('abc-123-def')
        >>> print(status['state'])
        'SUCCESS'
    """
    result = AsyncResult(task_id, app=celery_app)

    status_info = {
        "task_id": task_id,
        "state": result.state,
    }

    if result.state == "PENDING":
        status_info["status"] = "Task is waiting to be executed"
        status_info["result"] = None

    elif result.state == "STARTED":
        status_info["status"] = "Task has been started"
        status_info["result"] = None

    elif result.state == "SUCCESS":
        status_info["status"] = "Task completed successfully"
        status_info["result"] = result.result

    elif result.state == "FAILURE":
        status_info["status"] = "Task failed"
        status_info["error"] = str(result.info)
        status_info["result"] = None

    elif result.state == "PROGRESS":
        status_info["status"] = "Task is in progress"
        status_info["result"] = None
        if isinstance(result.info, dict):
            status_info["progress"] = result.info

    else:
        status_info["status"] = f"Unknown state: {result.state}"
        status_info["result"] = result.result if result.result else None

    return status_info


def revoke_task(task_id: str, terminate: bool = False) -> Dict[str, Any]:
    """
    Cancel or terminate a running Celery task.

    This function attempts to cancel or terminate a task by its ID.
    Terminate will forcefully kill the task, while cancel will
    attempt to stop it gracefully.

    Args:
        task_id: The Celery task ID to cancel
        terminate: Whether to forcefully terminate the task (default: False)

    Returns:
        Dictionary containing cancellation status

    Example:
        >>> from tasks import revoke_task
        >>> result = revoke_task('abc-123-def', terminate=True)
        >>> print(result['status'])
        'cancelled'
    """
    celery_app.control.revoke(task_id, terminate=terminate)

    logger.info(f"Task {task_id} revoked (terminate={terminate})")

    return {
        "task_id": task_id,
        "status": "cancelled" if terminate else "revoked",
        "terminated": terminate,
    }


# Export Celery app for use by workers
__all__ = [
    "celery_app",
    "health_check_task",
    "add_numbers_task",
    "long_running_task",
    "analyze_resume_async",
    "batch_analyze_resumes",
    "generate_scheduled_reports",
    "process_all_pending_reports",
    "send_feedback_notification",
    "send_batch_notification",
    "check_resume_against_saved_searches",
    "send_search_alert_notification",
    "process_pending_alerts",
    "get_task_status",
    "revoke_task",
]
