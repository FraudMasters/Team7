"""
Celery tasks module for async processing.

This module provides Celery task definitions for long-running operations
like resume analysis, job matching, batch processing, ML learning tasks,
report generation, and automated backups.
"""
from .analysis_task import analyze_resume_async, batch_analyze_resumes
from .learning_tasks import (
    aggregate_feedback_and_generate_synonyms,
    review_and_activate_synonyms,
    periodic_feedback_aggregation,
    retrain_skill_matching_model,
)
from .report_generation import (
    generate_scheduled_reports,
    process_all_pending_reports,
)
from .backup_tasks import (
    daily_backup_task,
    create_backup_task,
    cleanup_old_backups_task,
    upload_to_s3_task,
    verify_backup_integrity_task,
    restore_from_backup_task,
    sync_all_to_s3_task,
    backup_health_check_task,
)

__all__ = [
    "analyze_resume_async",
    "batch_analyze_resumes",
    "aggregate_feedback_and_generate_synonyms",
    "review_and_activate_synonyms",
    "periodic_feedback_aggregation",
    "retrain_skill_matching_model",
    "generate_scheduled_reports",
    "process_all_pending_reports",
    "daily_backup_task",
    "create_backup_task",
    "cleanup_old_backups_task",
    "upload_to_s3_task",
    "verify_backup_integrity_task",
    "restore_from_backup_task",
    "sync_all_to_s3_task",
    "backup_health_check_task",
]
