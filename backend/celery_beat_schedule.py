"""
Celery Beat schedule configuration for automated model retraining.

This module defines the periodic task schedule for Celery Beat, including
daily and weekly automated model retraining schedules. It integrates with
the main Celery configuration to provide scheduled task execution.

Schedule Overview:
- Daily automated retraining check: Runs every day at configured time
- Weekly full model retraining: Runs once a week with more extensive training
- Concept drift monitoring: Periodic checks for performance degradation

The schedule uses Celery's crontab schedule for precise timing control
and allows configuration via environment variables.
"""
import logging
from typing import Dict, Any, Optional

from celery.schedules import crontab

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_retraining_schedule_config() -> Dict[str, Any]:
    """
    Get retraining schedule configuration from settings.

    Returns schedule configuration with defaults for:
    - daily_hour: Hour for daily retraining (default: 2 AM)
    - daily_minute: Minute for daily retraining (default: 0)
    - weekly_day: Day of week for weekly retraining (default: 6 = Sunday)
    - weekly_hour: Hour for weekly retraining (default: 3 AM)
    - weekly_minute: Minute for weekly retraining (default: 0)
    - enabled: Whether automated retraining is enabled (default: True)

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_retraining_schedule_config()
        >>> print(config['daily_hour'])
        2
    """
    return {
        "daily_hour": getattr(settings, "retraining_daily_hour", 2),
        "daily_minute": getattr(settings, "retraining_daily_minute", 0),
        "weekly_day": getattr(settings, "retraining_weekly_day", 6),  # Sunday
        "weekly_hour": getattr(settings, "retraining_weekly_hour", 3),
        "weekly_minute": getattr(settings, "retraining_weekly_minute", 0),
        "enabled": getattr(settings, "retraining_enabled", True),
        "models": getattr(settings, "retraining_models", ["skill_matching", "ranking"]),
    }


# Celery Beat schedule for automated model retraining
# This schedule is imported by celery_config.py and merged into beat_schedule
beat_schedule: Dict[str, Dict[str, Any]] = {
    # ==============================================
    # Daily Automated Retraining Schedule
    # ==============================================
    "daily-automated-retraining-skill-matching": {
        "task": "tasks.model_retraining.automated_retraining_task",
        "schedule": crontab(
            hour=get_retraining_schedule_config()["daily_hour"],
            minute=get_retraining_schedule_config()["daily_minute"],
        ),
        "args": ("skill_matching",),  # model_name
        "kwargs": {
            "days_back": 7,  # Use last 7 days of feedback for daily training
            "auto_activate": False,  # Require manual approval for daily runs
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 3600,  # Task expires if not run within 1 hour
            "queue": "learning",  # Route to learning queue
        },
    },
    "daily-automated-retraining-ranking": {
        "task": "tasks.model_retraining.automated_retraining_task",
        "schedule": crontab(
            hour=get_retraining_schedule_config()["daily_hour"],
            minute=get_retraining_schedule_config()["daily_minute"],
        ),
        "args": ("ranking",),  # model_name
        "kwargs": {
            "days_back": 7,  # Use last 7 days of feedback for daily training
            "auto_activate": False,  # Require manual approval for daily runs
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 3600,  # Task expires if not run within 1 hour
            "queue": "learning",  # Route to learning queue
        },
    },
    # ==============================================
    # Weekly Full Retraining Schedule
    # ==============================================
    "weekly-full-retraining-skill-matching": {
        "task": "tasks.model_retraining.automated_retraining_task",
        "schedule": crontab(
            day_of_week=get_retraining_schedule_config()["weekly_day"],
            hour=get_retraining_schedule_config()["weekly_hour"],
            minute=get_retraining_schedule_config()["weekly_minute"],
        ),
        "args": ("skill_matching",),  # model_name
        "kwargs": {
            "days_back": 30,  # Use last 30 days of feedback for weekly training
            "auto_activate": False,  # Require manual approval
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "learning",  # Route to learning queue
        },
    },
    "weekly-full-retraining-ranking": {
        "task": "tasks.model_retraining.automated_retraining_task",
        "schedule": crontab(
            day_of_week=get_retraining_schedule_config()["weekly_day"],
            hour=get_retraining_schedule_config()["weekly_hour"],
            minute=get_retraining_schedule_config()["weekly_minute"],
        ),
        "args": ("ranking",),  # model_name
        "kwargs": {
            "days_back": 30,  # Use last 30 days of feedback for weekly training
            "auto_activate": False,  # Require manual approval
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "learning",  # Route to learning queue
        },
    },
}


def get_beat_schedule(enabled_only: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Get the Celery Beat schedule for automated retraining.

    This function returns the beat schedule dictionary, optionally filtered
    to include only enabled tasks based on configuration settings.

    Args:
        enabled_only: If True, only return enabled scheduled tasks (default: True)

    Returns:
        Dictionary mapping task names to their schedule configurations

    Example:
        >>> from celery_beat_schedule import get_beat_schedule
        >>> schedule = get_beat_schedule()
        >>> for name, config in schedule.items():
        ...     print(f"{name}: {config['task']}")
    """
    config = get_retraining_schedule_config()

    if not config["enabled"] and enabled_only:
        logger.info("Automated retraining is disabled in settings")
        return {}

    logger.info(
        f"Retrieving beat schedule: {len(beat_schedule)} tasks, "
        f"enabled={config['enabled']}, models={config['models']}"
    )

    if enabled_only:
        # Filter to only include tasks for configured models
        filtered_schedule = {}
        for task_name, task_config in beat_schedule.items():
            # Extract model name from task name or args
            model_name = None
            if task_config.get("args"):
                model_name = task_config["args"][0] if task_config["args"] else None

            # Include task if model is in configured list
            if model_name and model_name in config["models"]:
                filtered_schedule[task_name] = task_config
            elif not model_name:
                # Include tasks without specific model (e.g., monitoring)
                filtered_schedule[task_name] = task_config

        return filtered_schedule

    return beat_schedule


def add_scheduled_task(
    task_name: str,
    task_path: str,
    schedule: Any,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Dynamically add a new scheduled task to the beat schedule.

    This function allows runtime modification of the Celery Beat schedule,
    useful for adding or updating scheduled tasks without restarting.

    Args:
        task_name: Unique identifier for the scheduled task
        task_path: Full task path (e.g., 'tasks.model_retraining.automated_retraining_task')
        schedule: Celery schedule object (crontab, int seconds, or schedule)
        args: Positional arguments to pass to the task
        kwargs: Keyword arguments to pass to the task
        options: Additional Celery task options

    Example:
        >>> from celery.schedules import crontab
        >>> add_scheduled_task(
        ...     'daily-custom-retraining',
        ...     'tasks.model_retraining.automated_retraining_task',
        ...     crontab(hour=1, minute=0),
        ...     args=('custom_model',),
        ...     kwargs={'days_back': 14}
        ... )
    """
    if kwargs is None:
        kwargs = {}
    if options is None:
        options = {}

    beat_schedule[task_name] = {
        "task": task_path,
        "schedule": schedule,
        "args": args,
        "kwargs": kwargs,
        "options": options,
    }

    logger.info(f"Added scheduled task '{task_name}' to beat schedule")


def remove_scheduled_task(task_name: str) -> bool:
    """
    Remove a scheduled task from the beat schedule.

    Args:
        task_name: Name of the task to remove

    Returns:
        True if task was removed, False if not found

    Example:
        >>> removed = remove_scheduled_task('daily-custom-retraining')
        >>> print(removed)
        True
    """
    if task_name in beat_schedule:
        del beat_schedule[task_name]
        logger.info(f"Removed scheduled task '{task_name}' from beat schedule")
        return True
    logger.warning(f"Scheduled task '{task_name}' not found in beat schedule")
    return False


def list_scheduled_tasks() -> Dict[str, Dict[str, Any]]:
    """
    List all currently scheduled tasks with their configurations.

    Returns:
        Dictionary mapping task names to their schedule information

    Example:
        >>> tasks = list_scheduled_tasks()
        >>> for name, info in tasks.items():
        ...     print(f"{name}: {info['schedule']}")
    """
    return beat_schedule.copy()


# Log schedule configuration on import
schedule_config = get_retraining_schedule_config()
logger.info(
    f"Celery Beat schedule loaded: "
    f"daily at {schedule_config['daily_hour']:02d}:{schedule_config['daily_minute']:02d}, "
    f"weekly on day {schedule_config['weekly_day']} at "
    f"{schedule_config['weekly_hour']:02d}:{schedule_config['weekly_minute']:02d}, "
    f"enabled={schedule_config['enabled']}"
)


# Export schedule and utility functions
__all__ = [
    "beat_schedule",
    "get_beat_schedule",
    "get_retraining_schedule_config",
    "add_scheduled_task",
    "remove_scheduled_task",
    "list_scheduled_tasks",
]
