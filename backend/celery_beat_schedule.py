"""
Celery Beat schedule configuration for automated model retraining, analytics reports, and search alerts.

This module defines the periodic task schedule for Celery Beat, including
daily and weekly automated model retraining schedules, analytics email
report schedules, and search alert processing schedules. It integrates with
the main Celery configuration to provide scheduled task execution.

Schedule Overview:
- Feedback volume check: Runs every 6 hours to check if feedback threshold is met
- Daily automated retraining check: Runs every day at configured time
- Weekly full model retraining: Runs once a week with more extensive training
- Concept drift monitoring: Periodic checks for performance degradation
- Daily analytics email report: Sends daily summary at configured time
- Weekly analytics email report: Sends weekly summary on configured day
- Daily search alert processing: Processes pending alerts for daily-frequency saved searches
- Weekly search alert processing: Processes pending alerts for weekly-frequency saved searches
- Scheduled report processing: Processes pending scheduled reports at configured intervals

Feedback Volume Trigger:
- Monitors accumulated feedback counts per model
- Automatically triggers retraining when threshold (default: 1000) is reached
- Can be enabled/disabled via retraining_feedback_counter_enabled setting

Analytics Email Reports:
- Daily reports: Key metrics summary sent every morning
- Weekly reports: Comprehensive analytics sent once a week
- Configurable recipients via analytics_report_default_recipients setting

Search Alert Processing:
- Daily alerts: Processes pending alerts for saved searches with daily frequency
- Weekly alerts: Processes pending alerts for saved searches with weekly frequency
- Configurable timing via alert_schedule settings

Scheduled Report Processing:
- Daily reports: Processes pending scheduled reports with daily frequency
- Weekly reports: Processes pending scheduled reports with weekly frequency
- Monthly reports: Processes pending scheduled reports with monthly frequency
- Configurable timing via scheduled_report_schedule settings

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
    - feedback_volume_threshold: Number of feedbacks to trigger retraining (default: 1000)
    - feedback_counter_enabled: Whether feedback volume triggers are enabled (default: True)

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_retraining_schedule_config()
        >>> print(config['daily_hour'])
        2
        >>> print(config['feedback_volume_threshold'])
        1000
    """
    return {
        "daily_hour": getattr(settings, "retraining_daily_hour", 2),
        "daily_minute": getattr(settings, "retraining_daily_minute", 0),
        "weekly_day": getattr(settings, "retraining_weekly_day", 6),  # Sunday
        "weekly_hour": getattr(settings, "retraining_weekly_hour", 3),
        "weekly_minute": getattr(settings, "retraining_weekly_minute", 0),
        "enabled": getattr(settings, "retraining_enabled", True),
        "models": getattr(settings, "retraining_models", ["skill_matching", "ranking"]),
        "feedback_volume_threshold": getattr(
            settings, "retraining_feedback_volume_threshold", 1000
        ),
        "feedback_counter_enabled": getattr(
            settings, "retraining_feedback_counter_enabled", True
        ),
    }


def get_analytics_report_schedule_config() -> Dict[str, Any]:
    """
    Get analytics email report schedule configuration from settings.

    Returns schedule configuration with defaults for:
    - enabled: Whether analytics email reports are enabled (default: True)
    - daily_hour: Hour for daily reports (default: 8 AM)
    - daily_minute: Minute for daily reports (default: 0)
    - weekly_day: Day of week for weekly reports (default: 1 = Monday)
    - weekly_hour: Hour for weekly reports (default: 9 AM)
    - weekly_minute: Minute for weekly reports (default: 0)
    - default_recipients: List of default email recipients

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_analytics_report_schedule_config()
        >>> print(config['daily_hour'])
        8
        >>> print(config['weekly_day'])
        1
    """
    return {
        "enabled": getattr(settings, "analytics_email_reports_enabled", True),
        "daily_hour": getattr(settings, "analytics_report_daily_hour", 8),
        "daily_minute": getattr(settings, "analytics_report_daily_minute", 0),
        "weekly_day": getattr(settings, "analytics_report_weekly_day", 1),  # Monday
        "weekly_hour": getattr(settings, "analytics_report_weekly_hour", 9),
        "weekly_minute": getattr(settings, "analytics_report_weekly_minute", 0),
        "default_recipients": getattr(
            settings, "analytics_report_default_recipients", []
        ),
    }


def get_alert_schedule_config() -> Dict[str, Any]:
    """
    Get search alert processing schedule configuration from settings.

    Returns schedule configuration with defaults for:
    - enabled: Whether search alerts are enabled (default: True)
    - daily_hour: Hour for daily alert processing (default: 6 AM)
    - daily_minute: Minute for daily alert processing (default: 0)
    - weekly_day: Day of week for weekly alert processing (default: 0 = Sunday)
    - weekly_hour: Hour for weekly alert processing (default: 7 AM)
    - weekly_minute: Minute for weekly alert processing (default: 0)
    - batch_size: Number of alerts to process in one batch (default: 100)

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_alert_schedule_config()
        >>> print(config['daily_hour'])
        6
        >>> print(config['weekly_day'])
        0
    """
    return {
        "enabled": getattr(settings, "search_alerts_enabled", True),
        "daily_hour": getattr(settings, "search_alert_daily_hour", 6),
        "daily_minute": getattr(settings, "search_alert_daily_minute", 0),
        "weekly_day": getattr(settings, "search_alert_weekly_day", 0),  # Sunday
        "weekly_hour": getattr(settings, "search_alert_weekly_hour", 7),
        "weekly_minute": getattr(settings, "search_alert_weekly_minute", 0),
        "batch_size": getattr(settings, "search_alert_batch_size", 100),
    }


def get_elasticsearch_indexing_config() -> Dict[str, Any]:
    """
    Get Elasticsearch bulk indexing schedule configuration from settings.

    Returns schedule configuration with defaults for:
    - enabled: Whether scheduled bulk indexing is enabled (default: False)
    - hour: Hour for indexing (default: 3 AM)
    - minute: Minute for indexing (default: 0)
    - day_of_week: Day of week for indexing (default: 0 = Sunday)
    - batch_size: Number of resumes to index per batch (default: 100)

    Note: Bulk indexing is typically a one-time or manually triggered operation.
    Enable scheduled indexing only if you need periodic re-indexing.

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_elasticsearch_indexing_config()
        >>> print(config['enabled'])
        False
        >>> print(config['batch_size'])
        100
    """
    return {
        "enabled": getattr(settings, "elasticsearch_bulk_indexing_enabled", False),
        "hour": getattr(settings, "elasticsearch_indexing_hour", 3),
        "minute": getattr(settings, "elasticsearch_indexing_minute", 0),
        "day_of_week": getattr(settings, "elasticsearch_indexing_day", 0),  # Sunday
        "batch_size": getattr(settings, "elasticsearch_indexing_batch_size", 100),
    }


def get_scheduled_report_config() -> Dict[str, Any]:
    """
    Get scheduled report processing configuration from settings.

    Returns schedule configuration with defaults for:
    - enabled: Whether scheduled reports are enabled (default: True)
    - daily_hour: Hour for daily report processing (default: 7 AM)
    - daily_minute: Minute for daily report processing (default: 0)
    - weekly_day: Day of week for weekly report processing (default: 1 = Monday)
    - weekly_hour: Hour for weekly report processing (default: 8 AM)
    - weekly_minute: Minute for weekly report processing (default: 0)
    - monthly_day: Day of month for monthly report processing (default: 1)
    - monthly_hour: Hour for monthly report processing (default: 9 AM)
    - monthly_minute: Minute for monthly report processing (default: 0)
    - batch_size: Number of reports to process in one batch (default: 50)

    Returns:
        Dictionary containing schedule configuration

    Example:
        >>> config = get_scheduled_report_config()
        >>> print(config['daily_hour'])
        7
        >>> print(config['weekly_day'])
        1
    """
    return {
        "enabled": getattr(settings, "scheduled_reports_enabled", True),
        "daily_hour": getattr(settings, "scheduled_report_daily_hour", 7),
        "daily_minute": getattr(settings, "scheduled_report_daily_minute", 0),
        "weekly_day": getattr(settings, "scheduled_report_weekly_day", 1),  # Monday
        "weekly_hour": getattr(settings, "scheduled_report_weekly_hour", 8),
        "weekly_minute": getattr(settings, "scheduled_report_weekly_minute", 0),
        "monthly_day": getattr(settings, "scheduled_report_monthly_day", 1),  # 1st of month
        "monthly_hour": getattr(settings, "scheduled_report_monthly_hour", 9),
        "monthly_minute": getattr(settings, "scheduled_report_monthly_minute", 0),
        "batch_size": getattr(settings, "scheduled_report_batch_size", 50),
    }


# Celery Beat schedule for automated model retraining
# This schedule is imported by celery_config.py and merged into beat_schedule
beat_schedule: Dict[str, Dict[str, Any]] = {
    # ==============================================
    # Feedback Volume Trigger Schedule
    # ==============================================
    "feedback-volume-check-skill-matching": {
        "task": "tasks.model_retraining.check_feedback_volume_task",
        "schedule": crontab(
            hour="*/6",  # Check every 6 hours
            minute=15,
        ),
        "args": ("skill_matching",),  # model_name
        "kwargs": {
            "feedback_threshold": get_retraining_schedule_config()[
                "feedback_volume_threshold"
            ],
            "auto_trigger": True,  # Automatically trigger retraining if threshold met
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 21600,  # Task expires if not run within 6 hours
            "queue": "learning",  # Route to learning queue
        },
    },
    "feedback-volume-check-ranking": {
        "task": "tasks.model_retraining.check_feedback_volume_task",
        "schedule": crontab(
            hour="*/6",  # Check every 6 hours
            minute=30,
        ),
        "args": ("ranking",),  # model_name
        "kwargs": {
            "feedback_threshold": get_retraining_schedule_config()[
                "feedback_volume_threshold"
            ],
            "auto_trigger": True,  # Automatically trigger retraining if threshold met
            "notify": True,  # Send notifications
        },
        "options": {
            "expires": 21600,  # Task expires if not run within 6 hours
            "queue": "learning",  # Route to learning queue
        },
    },
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
    # ==============================================
    # Analytics Email Reports Schedule
    # ==============================================
    "daily-analytics-email-report": {
        "task": "tasks.analytics_email_reports.send_analytics_report",
        "schedule": crontab(
            hour=get_analytics_report_schedule_config()["daily_hour"],
            minute=get_analytics_report_schedule_config()["daily_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "report_type": "daily",  # Daily report type
        },
        "options": {
            "expires": 3600,  # Task expires if not run within 1 hour
            "queue": "default",  # Use default queue for email tasks
        },
    },
    "weekly-analytics-email-report": {
        "task": "tasks.analytics_email_reports.send_analytics_report",
        "schedule": crontab(
            day_of_week=get_analytics_report_schedule_config()["weekly_day"],
            hour=get_analytics_report_schedule_config()["weekly_hour"],
            minute=get_analytics_report_schedule_config()["weekly_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "report_type": "weekly",  # Weekly report type
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "default",  # Use default queue for email tasks
        },
    },
    # ==============================================
    # Search Alert Processing Schedule
    # ==============================================
    "daily-search-alert-processing": {
        "task": "tasks.search_alerts.process_pending_alerts",
        "schedule": crontab(
            hour=get_alert_schedule_config()["daily_hour"],
            minute=get_alert_schedule_config()["daily_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "batch_size": get_alert_schedule_config()["batch_size"],
        },
        "options": {
            "expires": 3600,  # Task expires if not run within 1 hour
            "queue": "default",  # Use default queue for alert tasks
        },
    },
    "weekly-search-alert-processing": {
        "task": "tasks.search_alerts.process_pending_alerts",
        "schedule": crontab(
            day_of_week=get_alert_schedule_config()["weekly_day"],
            hour=get_alert_schedule_config()["weekly_hour"],
            minute=get_alert_schedule_config()["weekly_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "batch_size": get_alert_schedule_config()["batch_size"],
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "default",  # Use default queue for alert tasks
        },
    },
    # ==============================================
    # Elasticsearch Bulk Indexing Schedule
    # ==============================================
    "elasticsearch-bulk-index-resumes": {
        "task": "tasks.elasticsearch_indexing.bulk_index_resumes",
        "schedule": crontab(
            day_of_week=get_elasticsearch_indexing_config()["day_of_week"],
            hour=get_elasticsearch_indexing_config()["hour"],
            minute=get_elasticsearch_indexing_config()["minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "batch_size": get_elasticsearch_indexing_config()["batch_size"],
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "default",  # Use default queue for indexing tasks
        },
    },
    # ==============================================
    # Scheduled Report Processing Schedule
    # ==============================================
    "daily-scheduled-report-processing": {
        "task": "tasks.scheduled_reports.process_scheduled_reports",
        "schedule": crontab(
            hour=get_scheduled_report_config()["daily_hour"],
            minute=get_scheduled_report_config()["daily_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "frequency": "daily",  # Process daily frequency reports
            "batch_size": get_scheduled_report_config()["batch_size"],
        },
        "options": {
            "expires": 3600,  # Task expires if not run within 1 hour
            "queue": "default",  # Use default queue for report tasks
        },
    },
    "weekly-scheduled-report-processing": {
        "task": "tasks.scheduled_reports.process_scheduled_reports",
        "schedule": crontab(
            day_of_week=get_scheduled_report_config()["weekly_day"],
            hour=get_scheduled_report_config()["weekly_hour"],
            minute=get_scheduled_report_config()["weekly_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "frequency": "weekly",  # Process weekly frequency reports
            "batch_size": get_scheduled_report_config()["batch_size"],
        },
        "options": {
            "expires": 7200,  # Task expires if not run within 2 hours
            "queue": "default",  # Use default queue for report tasks
        },
    },
    "monthly-scheduled-report-processing": {
        "task": "tasks.scheduled_reports.process_scheduled_reports",
        "schedule": crontab(
            day_of_month=get_scheduled_report_config()["monthly_day"],
            hour=get_scheduled_report_config()["monthly_hour"],
            minute=get_scheduled_report_config()["monthly_minute"],
        ),
        "args": (),  # No positional args
        "kwargs": {
            "frequency": "monthly",  # Process monthly frequency reports
            "batch_size": get_scheduled_report_config()["batch_size"],
        },
        "options": {
            "expires": 14400,  # Task expires if not run within 4 hours
            "queue": "default",  # Use default queue for report tasks
        },
    },
}


def get_beat_schedule(enabled_only: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Get the Celery Beat schedule for automated retraining, analytics reports, and search alerts.

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
    analytics_config = get_analytics_report_schedule_config()
    alert_config = get_alert_schedule_config()
    elasticsearch_config = get_elasticsearch_indexing_config()
    scheduled_report_config = get_scheduled_report_config()

    if not config["enabled"] and enabled_only:
        logger.info("Automated retraining is disabled in settings")

    if not analytics_config["enabled"] and enabled_only:
        logger.info("Analytics email reports are disabled in settings")

    if not alert_config["enabled"] and enabled_only:
        logger.info("Search alerts are disabled in settings")

    if not elasticsearch_config["enabled"] and enabled_only:
        logger.info("Elasticsearch bulk indexing is disabled in settings")

    if not scheduled_report_config["enabled"] and enabled_only:
        logger.info("Scheduled reports are disabled in settings")

    # If all are disabled and we only want enabled tasks, return empty
    if (
        not config["enabled"]
        and not analytics_config["enabled"]
        and not alert_config["enabled"]
        and not elasticsearch_config["enabled"]
        and not scheduled_report_config["enabled"]
        and enabled_only
    ):
        return {}

    logger.info(
        f"Retrieving beat schedule: {len(beat_schedule)} tasks, "
        f"retraining_enabled={config['enabled']}, models={config['models']}, "
        f"analytics_reports_enabled={analytics_config['enabled']}, "
        f"search_alerts_enabled={alert_config['enabled']}, "
        f"elasticsearch_indexing_enabled={elasticsearch_config['enabled']}, "
        f"scheduled_reports_enabled={scheduled_report_config['enabled']}"
    )

    if enabled_only:
        # Filter to only include enabled tasks
        filtered_schedule = {}
        for task_name, task_config in beat_schedule.items():
            # Skip feedback volume tasks if counter is disabled
            if "feedback-volume-check" in task_name:
                if not config.get("feedback_counter_enabled", True):
                    continue

            # Skip retraining tasks if retraining is disabled
            if "retraining" in task_name:
                if not config["enabled"]:
                    continue

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
                continue

            # Skip analytics email report tasks if analytics reports are disabled
            if "analytics-email-report" in task_name:
                if not analytics_config["enabled"]:
                    continue

            # Skip search alert tasks if alerts are disabled
            if "search-alert" in task_name:
                if not alert_config["enabled"]:
                    continue

            # Skip elasticsearch indexing tasks if indexing is disabled
            if "elasticsearch" in task_name:
                if not elasticsearch_config["enabled"]:
                    continue

            # Skip scheduled report tasks if scheduled reports are disabled
            if "scheduled-report" in task_name:
                if not scheduled_report_config["enabled"]:
                    continue

            # Include other tasks
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
analytics_config = get_analytics_report_schedule_config()
alert_config = get_alert_schedule_config()
scheduled_report_config = get_scheduled_report_config()
logger.info(
    f"Celery Beat schedule loaded: "
    f"daily at {schedule_config['daily_hour']:02d}:{schedule_config['daily_minute']:02d}, "
    f"weekly on day {schedule_config['weekly_day']} at "
    f"{schedule_config['weekly_hour']:02d}:{schedule_config['weekly_minute']:02d}, "
    f"feedback_threshold={schedule_config['feedback_volume_threshold']}, "
    f"feedback_counter_enabled={schedule_config['feedback_counter_enabled']}, "
    f"retraining_enabled={schedule_config['enabled']}, "
    f"analytics_reports_enabled={analytics_config['enabled']}, "
    f"analytics_daily_at={analytics_config['daily_hour']:02d}:{analytics_config['daily_minute']:02d}, "
    f"analytics_weekly_on_day_{analytics_config['weekly_day']}_at_{analytics_config['weekly_hour']:02d}:{analytics_config['weekly_minute']:02d}, "
    f"search_alerts_enabled={alert_config['enabled']}, "
    f"search_alert_daily_at={alert_config['daily_hour']:02d}:{alert_config['daily_minute']:02d}, "
    f"search_alert_weekly_on_day_{alert_config['weekly_day']}_at_{alert_config['weekly_hour']:02d}:{alert_config['weekly_minute']:02d}, "
    f"scheduled_reports_enabled={scheduled_report_config['enabled']}, "
    f"scheduled_report_daily_at={scheduled_report_config['daily_hour']:02d}:{scheduled_report_config['daily_minute']:02d}, "
    f"scheduled_report_weekly_on_day_{scheduled_report_config['weekly_day']}_at_{scheduled_report_config['weekly_hour']:02d}:{scheduled_report_config['weekly_minute']:02d}, "
    f"scheduled_report_monthly_on_day_{scheduled_report_config['monthly_day']}_at_{scheduled_report_config['monthly_hour']:02d}:{scheduled_report_config['monthly_minute']:02d}"
)


# Export schedule and utility functions
__all__ = [
    "beat_schedule",
    "CELERYBEAT_SCHEDULE",  # Legacy alias for Celery config compatibility
    "get_beat_schedule",
    "get_retraining_schedule_config",
    "get_analytics_report_schedule_config",
    "get_alert_schedule_config",
    "get_scheduled_report_config",
    "add_scheduled_task",
    "remove_scheduled_task",
    "list_scheduled_tasks",
]

# Legacy alias for Celery config compatibility
CELERYBEAT_SCHEDULE = beat_schedule
