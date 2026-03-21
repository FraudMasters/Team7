# Background Tasks Documentation

This document provides comprehensive documentation for all Celery background tasks in the AgentHR backend system. These tasks handle asynchronous operations including resume analysis, report generation, backup operations, ML model management, cache warming, and system maintenance.

## Table of Contents

- [Overview](#overview)
- [Task Categories](#task-categories)
- [Resume Analysis Tasks](#resume-analysis-tasks)
- [Report Generation Tasks](#report-generation-tasks)
- [ML Model Tasks](#ml-model-tasks)
- [Cache Management Tasks](#cache-management-tasks)
- [Learning & Improvement Tasks](#learning--improvement-tasks)
- [Backup & Maintenance Tasks](#backup--maintenance-tasks)
- [Email Notification Tasks](#email-notification-tasks)
- [Health Check Tasks](#health-check-tasks)
- [System Monitoring Tasks](#system-monitoring-tasks)
- [Task Execution](#task-execution)
- [Monitoring & Debugging](#monitoring--debugging)

---

## Overview

AgentHR uses **Celery** with **Redis** as a message broker for asynchronous task processing. Background tasks are used for:

- **Long-running operations** (resume analysis, model training)
- **Scheduled operations** (backups, cleanup, reports)
- **Periodic maintenance** (cache warming, log cleanup)
- **Batch processing** (bulk analysis, notifications)

### Configuration

- **Broker**: Redis (configured via `CELERY_BROKER_URL`)
- **Result Backend**: Redis (configured via `CELERY_RESULT_BACKEND`)
- **Worker Concurrency**: Configurable via `CELERY_WORKER_CONCURRENCY`
- **Task Time Limits**: Per-task limits to prevent hanging

### Key Concepts

- **@shared_task**: Decorator that registers a function as a Celery task
- **Task Binding**: `bind=True` provides access to `self` (task instance)
- **Retry Logic**: Automatic retry with exponential backoff on failure
- **Progress Updates**: `self.update_state()` for real-time progress tracking
- **Soft Time Limits**: Graceful handling of long-running tasks

---

## Task Categories

| Category | Description | Task Count |
|----------|-------------|------------|
| **Resume Analysis** | Async resume parsing and analysis | 2 |
| **Report Generation** | Scheduled and on-demand reports | 2 |
| **ML Model Management** | Model preloading and health checks | 2 |
| **Cache Management** | Cache warming and data preloading | 2 |
| **Learning & Improvement** | Feedback aggregation and model retraining | 4 |
| **Backup & Maintenance** | Database/file backups and cleanup | 8 |
| **Email Notifications** | Feedback and batch notifications | 2 |
| **Health Checks** | System health and monitoring | 3 |
| **Search Alerts** | Saved search matching | 1 |
| **Audit & Cleanup** | Log cleanup and retention | 1 |
| **Performance Monitoring** | System performance tracking | 1 |
| **Fairness Monitoring** | Bias detection and alerts | 1 |
| **Analytics Precomputation** | Pre-computed analytics data | 1 |

**Total**: 30+ documented tasks

---

## Resume Analysis Tasks

### `analyze_resume_async`

Asynchronously analyze a single resume with progress tracking.

**Task Name**: `tasks.analysis_task.analyze_resume_async`

**Parameters**:
- `resume_id` (str): Unique identifier of the resume to analyze
- `check_grammar` (bool, optional): Perform grammar checking (default: True)
- `extract_experience` (bool, optional): Calculate total experience (default: True)
- `detect_errors` (bool, optional): Detect resume errors (default: True)

**Returns**:
```python
{
    "resume_id": "uuid",
    "status": "completed",
    "language": "en",
    "keywords": {...},
    "entities": {...},
    "grammar": {...},
    "experience": {...},
    "errors": {...},
    "processing_time_ms": 1234.56
}
```

**Example Usage**:
```python
from tasks import analyze_resume_async

# Trigger async analysis
task = analyze_resume_async.delay(
    resume_id="abc-123",
    check_grammar=True,
    extract_experience=True
)

# Check status
status = task.status  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE

# Get result when ready
result = task.get(timeout=60)
```

**Progress States**:
1. `finding_resume` - Locating resume file
2. `analyzing` - Performing ML analysis
3. `complete` - Analysis finished

**Retry Configuration**:
- Max retries: 2
- Retry delay: 60 seconds

---

### `batch_analyze_resumes`

Asynchronously analyze multiple resumes in batch.

**Task Name**: `tasks.analysis_task.batch_analyze_resumes`

**Parameters**:
- `resume_ids` (List[str]): List of resume identifiers to analyze
- `check_grammar` (bool, optional): Perform grammar checking (default: True)
- `extract_experience` (bool, optional): Calculate experience (default: True)

**Returns**:
```python
{
    "total_resumes": 10,
    "successful": 9,
    "failed": 1,
    "results": [
        {"resume_id": "...", "status": "completed", ...},
        {"resume_id": "...", "status": "failed", "error": "..."}
    ]
}
```

**Example Usage**:
```python
from tasks import batch_analyze_resumes

resume_ids = ["resume-1", "resume-2", "resume-3"]
task = batch_analyze_resumes.delay(
    resume_ids=resume_ids,
    check_grammar=True
)

result = task.get(timeout=300)
print(f"Processed {result['successful']}/{result['total_resumes']} resumes")
```

**Progress Updates**: Real-time progress for each resume in the batch.

---

## Report Generation Tasks

### `generate_scheduled_report`

Generate and deliver a scheduled report with multiple formats.

**Task Name**: `tasks.report_generation.generate_scheduled_report`

**Parameters**:
- `scheduled_report_id` (str): UUID of the scheduled report to generate

**Workflow Steps**:
1. Load scheduled report configuration from database
2. Calculate date range based on schedule (daily/weekly/monthly)
3. Query analytics data based on report filters
4. Format report in requested formats (PDF, CSV, etc.)
5. Deliver report via configured method (email, S3, etc.)
6. Update last_run timestamp

**Returns**:
```python
{
    "scheduled_report_id": "uuid",
    "status": "completed",
    "formats_generated": ["pdf", "csv"],
    "delivery_method": "email",
    "recipients_count": 3,
    "delivery_successful": true,
    "processing_time_ms": 5432.10
}
```

**Example Usage**:
```python
from tasks.report_generation import generate_scheduled_report

task = generate_scheduled_report.delay("report-uuid-123")
result = task.get(timeout=120)

if result['status'] == 'completed':
    print(f"Report sent to {result['recipients_count']} recipients")
```

**Supported Formats**:
- PDF (via reportlab/weasyprint)
- CSV (via pandas/csv module)
- JSON (default)

**Delivery Methods**:
- Email (SMTP/SendGrid/AWS SES)
- S3 storage
- Webhook callback

---

### `process_all_pending_reports`

Periodic task to process all pending scheduled reports.

**Task Name**: `tasks.report_generation.process_all_pending_reports`

**Schedule**: Typically run every hour by Celery Beat

**Workflow**:
1. Query all active scheduled reports where `next_run_at <= now`
2. For each pending report, trigger `generate_scheduled_report` task
3. Update `next_run_at` based on schedule configuration
4. Return summary of processed reports

**Returns**:
```python
{
    "total_reports_found": 5,
    "reports_triggered": 4,
    "reports_skipped": 1,
    "processing_time_ms": 1234.56,
    "status": "completed"
}
```

**Celery Beat Configuration**:
```python
CELERY_BEAT_SCHEDULE = {
    'process-pending-reports': {
        'task': 'tasks.report_generation.process_all_pending_reports',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

---

## ML Model Tasks

### `preload_ml_models`

Preload ML models into memory on worker startup to reduce first-request latency.

**Task Name**: `tasks.model_preloading.preload_ml_models`

**Trigger**: Automatically executed via `worker_ready` signal when Celery worker starts

**Models Loaded**:
- Hugging Face NER models (English, Russian)
- Zero-shot classification model (BART-large-mnli)
- LanguageTool instances (en-US, en-GB, ru-RU)

**Returns**:
```python
{
    "status": "completed",
    "models_loaded": [
        "NER English",
        "NER Russian",
        "Zero-shot classification",
        "LanguageTool en-US",
        "LanguageTool en-GB",
        "LanguageTool ru-RU"
    ],
    "models_failed": [],
    "total_load_time_ms": 4532.10,
    "total_models": 6,
    "successful": 6,
    "failed": 0
}
```

**Benefits**:
- Reduced latency for first analysis request
- Predictable worker performance
- Early detection of model loading issues

---

### `health_check_with_models`

Health check that verifies ML models are loaded and ready.

**Task Name**: `tasks.model_preloading.health_check_with_models`

**Returns**:
```python
{
    "status": "healthy",  # or "degraded", "unhealthy"
    "worker": "celery@hostname",
    "task_id": "uuid",
    "models_status": {
        "ner_loaded": True,
        "zero_shot_loaded": True,
        "language_tools_loaded": True
    },
    "message": "All models loaded and ready"
}
```

**Use Cases**:
- Monitoring worker health
- Readiness probes for Kubernetes
- Detecting model loading issues

---

## Cache Management Tasks

### `warm_frequently_accessed_data`

Warm cache with frequently accessed data (candidates, vacancies, taxonomy).

**Task Name**: `tasks.cache_warming.warm_frequently_accessed_data`

**Parameters**:
- `candidate_limit` (int, optional): Max candidates to warm (default: 100)
- `vacancy_limit` (int, optional): Max vacancies to warm (default: 50)
- `ttl` (int, optional): Time-to-live for cache entries (default: 3600s)

**Workflow**:
1. Retrieve frequently accessed candidates (recent activity)
2. Retrieve frequently accessed vacancies
3. Retrieve complete skill taxonomy
4. Warm candidate cache
5. Warm vacancy cache
6. Warm taxonomy cache

**Returns**:
```python
{
    "candidates_warmed": 95,
    "vacancies_warmed": 48,
    "taxonomy_warmed": True,
    "candidate_cache_hits": 5,
    "vacancy_cache_hits": 2,
    "total_cache_hits": 7,
    "errors": 0,
    "total_warming_time_ms": 1234.56,
    "status": "completed",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example Usage**:
```python
from tasks.cache_warming import warm_frequently_accessed_data

task = warm_frequently_accessed_data.delay(
    candidate_limit=200,
    vacancy_limit=100,
    ttl=7200  # 2 hours
)
result = task.get()
```

---

### `periodic_cache_warming`

Periodic task to automatically warm the cache.

**Task Name**: `tasks.cache_warming.periodic_cache_warming`

**Schedule**: Every 30 minutes (configurable)

**Celery Beat Configuration**:
```python
CELERY_BEAT_SCHEDULE = {
    'cache-warming': {
        'task': 'tasks.cache_warming.periodic_cache_warming',
        'schedule': crontab(minute='*/30'),
    },
}
```

---

## Learning & Improvement Tasks

### `aggregate_feedback_and_generate_synonyms`

Aggregate recruiter feedback and generate new synonym candidates.

**Task Name**: `tasks.learning_tasks.aggregate_feedback_and_generate_synonyms`

**Purpose**: Process recruiter corrections to identify skill synonym patterns and generate improvement candidates.

**Parameters**:
- `organization_id` (str, optional): Filter feedback by organization
- `days_back` (int, optional): Look back period in days (default: 30)
- `mark_processed` (bool, optional): Mark feedback as processed (default: True)

**Workflow**:
1. Query unprocessed feedback entries from database
2. Aggregate corrections to find synonym patterns
3. Calculate confidence scores for each synonym
4. Generate high-confidence synonym candidates
5. Mark feedback as processed (optional)

**Returns**:
```python
{
    "total_feedback": 150,
    "unprocessed_count": 45,
    "corrections_found": 12,
    "candidates_generated": 8,
    "candidates": [
        {
            "canonical_skill": "react",
            "custom_synonyms": ["reactjs", "react.js"],
            "confidence": 0.92,
            "correction_count": 15
        }
    ],
    "processed_count": 45,
    "processing_time_ms": 2345.67,
    "status": "completed"
}
```

**Thresholds**:
- `MIN_CORRECTION_THRESHOLD = 3`: Minimum corrections before suggesting
- `MIN_SYNONYM_CONFIDENCE = 0.7`: Minimum confidence for candidates

**Example Usage**:
```python
from tasks.learning_tasks import aggregate_feedback_and_generate_synonyms

task = aggregate_feedback_and_generate_synonyms.delay(
    organization_id="org-123",
    days_back=30
)
result = task.get()
```

---

### `review_and_activate_synonyms`

Review and activate synonym candidates based on confidence thresholds.

**Task Name**: `tasks.learning_tasks.review_and_activate_synonyms`

**Parameters**:
- `candidate_ids` (List[str]): List of candidate IDs to review
- `auto_activate_threshold` (float, optional): Confidence threshold for auto-activation (default: 0.9)

**Returns**:
```python
{
    "total_candidates": 10,
    "auto_activated": 7,
    "manual_review": 2,
    "rejected": 1,
    "processing_time_ms": 543.21,
    "status": "completed"
}
```

**Activation Logic**:
- **Confidence >= 0.9**: Auto-activate
- **Confidence 0.7-0.9**: Flag for manual review
- **Confidence < 0.7**: Reject

---

### `periodic_feedback_aggregation`

Scheduled task to aggregate feedback and generate synonyms.

**Task Name**: `tasks.learning_tasks.periodic_feedback_aggregation`

**Schedule**: Daily at 2 AM

**Celery Beat Configuration**:
```python
CELERY_BEAT_SCHEDULE = {
    'daily-feedback-aggregation': {
        'task': 'tasks.learning_tasks.periodic_feedback_aggregation',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

### `retrain_skill_matching_model`

Retrain the skill matching model based on accumulated feedback.

**Task Name**: `tasks.learning_tasks.retrain_skill_matching_model`

**Purpose**: Create new model versions from feedback data, evaluate performance, and optionally auto-activate.

**Parameters**:
- `model_name` (str, optional): Name of model to retrain (default: "skill_matching")
- `days_back` (int, optional): Days of feedback to use (default: 30)
- `min_feedback_count` (int, optional): Minimum samples required (default: 50)
- `auto_activate` (bool, optional): Auto-activate if threshold met (default: False)
- `performance_threshold` (float, optional): Min score for activation (default: 0.85)

**Workflow**:
1. Query feedback data from specified time period
2. Validate minimum feedback count
3. Extract training features
4. Aggregate corrections for synonym updates
5. Generate and save synonym candidates
6. Create new MLModelVersion entry
7. Evaluate performance on validation set
8. Optionally activate if performance threshold met

**Returns**:
```python
{
    "training_samples": 150,
    "new_version_id": "uuid-123",
    "new_version": "1.2.0",
    "performance_score": 0.92,
    "is_active": False,
    "is_experiment": True,
    "improvement_over_baseline": 0.17,
    "synonyms_generated": 12,
    "corrections_aggregated": 8,
    "processing_time_ms": 12345.67,
    "status": "completed"
}
```

**Example Usage**:
```python
from tasks.learning_tasks import retrain_skill_matching_model

task = retrain_skill_matching_model.delay(
    model_name="skill_matching",
    days_back=30,
    auto_activate=True,
    performance_threshold=0.85
)
result = task.get(timeout=600)  # 10 minute timeout
```

**Model Versioning**:
- Each retraining creates a new version (e.g., 1.0.0 → 1.1.0)
- Only one version can be active per model name
- Previous versions are retained for rollback

---

## Backup & Maintenance Tasks

### `daily_backup_task`

Scheduled daily full backup of database, files, and models.

**Task Name**: `tasks.backup.daily_backup`

**Schedule**: Daily at 2 AM (configurable)

**Workflow**:
1. Create full backup with timestamp
2. Compress backup files
3. Calculate checksums
4. Trigger S3 upload (if enabled)
5. Send notification on failure

**Returns**:
```python
{
    "status": "success",
    "backup_name": "daily_20240115_020000",
    "backup_path": "/data/backups/daily_20240115_020000.tar.gz",
    "size_bytes": 1234567890,
    "elapsed_seconds": 45.6
}
```

**Celery Beat Configuration**:
```python
CELERY_BEAT_SCHEDULE = {
    'daily-backup': {
        'task': 'tasks.backup.daily_backup',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

### `create_backup_task`

Create a backup of specified type on-demand.

**Task Name**: `tasks.backup.create_backup`

**Parameters**:
- `backup_type` (str): Type of backup - "database", "files", "models", "full"
- `name` (str, optional): Custom backup name
- `is_incremental` (bool, optional): Create incremental backup (default: False)
- `upload_to_s3` (bool, optional): Upload to S3 after creation (default: False)

**Example Usage**:
```python
from tasks.backup import create_backup_task

# Create database backup
task = create_backup_task.delay(
    backup_type="database",
    name="manual_db_backup",
    upload_to_s3=True
)
result = task.get()
```

**Returns**:
```python
{
    "status": "success",
    "backup_type": "database",
    "backup_path": "/data/backups/manual_db_backup.tar.gz",
    "size_bytes": 123456789,
    "checksum": "abc123def456...",
    "elapsed_seconds": 12.3
}
```

---

### `cleanup_old_backups_task`

Clean up old backups based on retention policy.

**Task Name**: `tasks.backup.cleanup_old_backups`

**Parameters**:
- `retention_days` (int, optional): Days to retain backups (default: 30 from config)

**Returns**:
```python
{
    "status": "success",
    "deleted_count": 15,
    "deleted_paths": [
        "/data/backups/old_backup_1.tar.gz",
        "/data/backups/old_backup_2.tar.gz"
    ],
    "retention_days": 30
}
```

**Schedule**: Typically run daily after backup

---

### `upload_to_s3_task`

Upload a backup to S3-compatible storage.

**Task Name**: `tasks.backup.upload_to_s3`

**Parameters**:
- `backup_path` (str): Path to the backup file
- `backup_name` (str, optional): Name for the S3 object

**Configuration**: Uses environment variables:
- `BACKUP_S3_ENABLED`: Enable/disable S3 uploads
- `BACKUP_S3_BUCKET`: S3 bucket name
- `BACKUP_S3_ENDPOINT`: S3 endpoint URL
- `BACKUP_S3_ACCESS_KEY`: Access key
- `BACKUP_S3_SECRET_KEY`: Secret key
- `BACKUP_S3_REGION`: AWS region (default: us-east-1)

**Returns**:
```python
{
    "status": "success",
    "s3_key": "backups/daily_20240115_020000.tar.gz",
    "bucket": "agenthr-backups",
    "size_bytes": 1234567890
}
```

---

### `verify_backup_integrity_task`

Verify the integrity of a backup file using checksums.

**Task Name**: `tasks.backup.verify_integrity`

**Parameters**:
- `backup_path` (str): Path to the backup file
- `expected_checksum` (str, optional): Expected SHA256 checksum

**Returns**:
```python
{
    "valid": True,
    "checksum": "abc123def456...",
    "algorithm": "sha256",
    "size_bytes": 1234567890
}
```

---

### `restore_from_backup_task`

Restore from a backup file.

**Task Name**: `tasks.backup.restore_from_backup`

**Parameters**:
- `backup_path` (str): Path to the backup file
- `backup_type` (str): Type of restore - "full", "database", "files", "models"
- `create_backup_before` (bool, optional): Create pre-restore backup (default: True)

**Returns**:
```python
{
    "status": "success",
    "backup_path": "/data/backups/backup.tar.gz",
    "elapsed_seconds": 23.4
}
```

---

### `sync_all_to_s3_task`

Sync all local backups to S3 storage.

**Task Name**: `tasks.backup.sync_all_to_s3`

**Returns**:
```python
{
    "status": "success",
    "uploaded_count": 5,
    "skipped_count": 10,
    "uploaded": [
        "/data/backups/backup1.tar.gz",
        "/data/backups/backup2.tar.gz"
    ]
}
```

---

### `backup_health_check_task`

Health check for the backup system.

**Task Name**: `tasks.backup.health_check`

**Checks**:
- Backup directories are accessible
- Required tools are available (pg_dump, psql, gzip)
- Disk space is sufficient

**Returns**:
```python
{
    "status": "healthy",  # or "warning", "unhealthy"
    "checks": {
        "directories": {"status": "ok"},
        "pg_dump": {"status": "ok", "path": "/usr/bin/pg_dump"},
        "disk_space": {"status": "ok", "message": "15.2GB free"}
    }
}
```

---

## Email Notification Tasks

### `send_feedback_notification`

Send candidate feedback via email to recruiters.

**Task Name**: `tasks.email_task.send_feedback_notification`

**Parameters**:
- `feedback_id` (str): UUID of the candidate feedback
- `recipient_email` (str): Email address of recipient
- `candidate_name` (str): Name of the candidate
- `feedback_data` (Dict[str, Any]): Feedback details including scores, recommendations, etc.

**Returns**:
```python
{
    "feedback_id": "uuid-123",
    "status": "sent",
    "recipient": "recruiter@example.com",
    "sent_at": 1705314000.123,
    "processing_time_ms": 234.56
}
```

**Example Usage**:
```python
from tasks.email_task import send_feedback_notification

task = send_feedback_notification.delay(
    feedback_id="feedback-123",
    recipient_email="recruiter@example.com",
    candidate_name="John Doe",
    feedback_data={
        "match_score": 85,
        "skills_feedback": {...},
        "recommendations": ["..."]
    }
)
result = task.get()
```

**Retry Logic**:
- Max retries: 3
- Retry delay: 60 seconds (exponential backoff)

---

### `send_batch_notification`

Send batch notifications to multiple recipients.

**Task Name**: `tasks.email_task.send_batch_notification`

**Parameters**:
- `batch_type` (str): Type of notification - "batch_analysis", "system_alert", etc.
- `recipient_emails` (List[str]): List of email addresses
- `notification_data` (Dict[str, Any]): Notification content

**Returns**:
```python
{
    "batch_type": "batch_analysis",
    "status": "sent",  # or "partial", "failed"
    "total_recipients": 10,
    "successful_sends": 9,
    "failed_sends": 1,
    "errors": ["Failed to send to user@example.com: ..."],
    "processing_time_ms": 1234.56
}
```

---

## Health Check Tasks

### `health_check_task`

Simple health check to verify Celery worker is functioning.

**Task Name**: `tasks.health_check`

**Returns**:
```python
{
    "status": "healthy",
    "worker": "celery@hostname",
    "task_id": "uuid-123",
    "message": "Celery worker is operational"
}
```

**Use Cases**:
- Liveness probes for Kubernetes
- Monitoring worker availability
- Testing Celery connectivity

---

### `add_numbers_task`

Simple addition task for testing Celery functionality.

**Task Name**: `tasks.add_numbers`

**Parameters**:
- `x` (int): First number
- `y` (int): Second number

**Returns**: `int` - Sum of x and y

**Example Usage**:
```python
from tasks import add_numbers_task

task = add_numbers_task.delay(5, 3)
result = task.get()  # Returns 8
```

**Use Cases**:
- Testing Celery setup
- Verifying task execution
- End-to-end testing

---

### `long_running_task`

Simulated long-running task for testing async processing.

**Task Name**: `tasks.long_running_task`

**Parameters**:
- `duration_seconds` (int, optional): How long the task should run (default: 10)
- `progress_updates` (bool, optional): Send progress updates (default: True)

**Returns**:
```python
{
    "status": "completed",
    "task_id": "uuid-123",
    "duration_seconds": 10,
    "steps_completed": 5,
    "message": "Long-running task completed successfully"
}
```

**Progress Updates**: Updates progress every 2 seconds (5 steps total).

---

## System Monitoring Tasks

### `check_resume_against_saved_searches`

Check a new resume against all saved searches and create alerts for matches.

**Task Name**: `tasks.search_alerts.check_resume_against_saved_searches`

**Parameters**:
- `resume_id` (str): UUID of the newly uploaded resume
- `resume_data` (Dict[str, Any]): Resume information including skills, experience, location, etc.

**Workflow**:
1. Retrieve all saved searches from database
2. Compare resume data against each search's criteria
3. Create SearchAlert records for matching searches
4. Trigger notification tasks for each alert

**Returns**:
```python
{
    "resume_id": "uuid-123",
    "status": "completed",
    "total_searches_checked": 50,
    "matches_found": 3,
    "alerts_created": 3,
    "processing_time_ms": 1234.56,
    "match_details": [
        {
            "search_id": "search-1",
            "match_score": 0.85,
            "matched_criteria": ["skills", "location"]
        }
    ]
}
```

---

### `cleanup_old_audit_logs_task`

Clean up old audit logs based on retention policy.

**Task Name**: `tasks.audit_cleanup.cleanup_old_audit_logs`

**Parameters**:
- `retention_days` (int, optional): Days to retain logs (default: from config)

**Returns**:
```python
{
    "status": "success",
    "deleted_count": 1523,
    "retention_days": 90,
    "cutoff_date": "2023-10-17T10:30:00Z",
    "processing_time_ms": 2345.67
}
```

**Schedule**: Typically run weekly

---

## Additional Task Modules

### Performance Monitoring Tasks
- **File**: `tasks/performance_monitoring.py`
- **Tasks**: Metrics collection, anomaly detection, performance alerts

### Fairness Monitoring Tasks
- **File**: `tasks/fairness_monitoring.py`
- **Tasks**: Bias detection, fairness metrics calculation, alert generation

### Analytics Precomputation Tasks
- **File**: `tasks/analytics_precomputation.py`
- **Tasks**: Pre-compute common analytics queries, materialized view refresh

---

## Task Execution

### Running Tasks Manually

```python
# Import task
from tasks import analyze_resume_async

# Execute task asynchronously
result = analyze_resume_async.delay(resume_id="abc-123")

# Check task status
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

# Get result (blocking)
result_data = result.get(timeout=60)

# Check task ID
print(result.id)  # UUID of the task
```

### Applying Tasks (Eager Mode)

For testing/debugging, you can run tasks synchronously:

```python
from tasks import analyze_resume_async

# Run task synchronously in current thread
result = analyze_resume_async.apply(args=["abc-123"]).get()
```

### Task Options

```python
# Custom retry configuration
task = some_task.retry(
    exc=Exception,
    countdown=60,
    max_retries=3
)

# Task with countdown
task = some_task.apply_async(
    args=['arg1', 'arg2'],
    countdown=10  # Delay execution by 10 seconds
)

# Task with ETA (specific time)
task = some_task.apply_async(
    args=['arg1', 'arg2'],
    eta=datetime(2024, 1, 15, 10, 30, 0)
)
```

---

## Monitoring & Debugging

### Checking Task Status

```python
from celery_app import get_task_status

status = get_task_status(task_id="abc-123")
print(status)
# {
#     "task_id": "abc-123",
#     "state": "SUCCESS",
#     "status": "Task completed successfully",
#     "result": {...}
# }
```

### Task States

| State | Description |
|-------|-------------|
| `PENDING` | Task waiting to be executed |
| `STARTED` | Task has been started |
| `PROGRESS` | Task is in progress (with meta) |
| `SUCCESS` | Task completed successfully |
| `FAILURE` | Task failed |
| `RETRY` | Task is being retried |
| `REVOKED` | Task was revoked |

### Revoking Tasks

```python
from celery_app import revoke_task

# Cancel task gracefully
revoke_task(task_id="abc-123", terminate=False)

# Forcefully terminate task
revoke_task(task_id="abc-123", terminate=True)
```

### Viewing Worker Logs

```bash
# View Celery worker logs
tail -f /var/log/celery/worker.log

# View specific task logs
grep "task_id=abc-123" /var/log/celery/worker.log
```

### Flower (Web Monitoring)

Flower is a web-based tool for monitoring and administrating Celery clusters:

```bash
# Install flower
pip install flower

# Start flower
celery -A backend.celery_app flower

# Access at http://localhost:5555
```

**Features**:
- Real-time task monitoring
- Worker status and health
- Task progress tracking
- Task retry and revocation
- Broker and backend monitoring

---

## Celery Beat Schedule

All scheduled tasks are configured in `celery_config.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Daily backup at 2 AM
    'daily-backup': {
        'task': 'tasks.backup.daily_backup',
        'schedule': crontab(hour=2, minute=0),
    },

    # Process pending reports every hour
    'process-pending-reports': {
        'task': 'tasks.report_generation.process_all_pending_reports',
        'schedule': crontab(minute=0),
    },

    # Cache warming every 30 minutes
    'cache-warming': {
        'task': 'tasks.cache_warming.periodic_cache_warming',
        'schedule': crontab(minute='*/30'),
    },

    # Feedback aggregation daily at 2 AM
    'daily-feedback-aggregation': {
        'task': 'tasks.learning_tasks.periodic_feedback_aggregation',
        'schedule': crontab(hour=2, minute=0),
    },

    # Audit log cleanup weekly on Sunday at 3 AM
    'audit-log-cleanup': {
        'task': 'tasks.audit_cleanup.cleanup_old_audit_logs_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
}
```

---

## Best Practices

### Task Design

1. **Keep tasks idempotent**: Tasks should be safe to retry
2. **Use atomic operations**: All-or-nothing database operations
3. **Handle failures gracefully**: Proper error handling and logging
4. **Set appropriate timeouts**: Prevent hanging tasks
5. **Provide progress updates**: For long-running tasks

### Error Handling

```python
@shared_task(
    name="tasks.my_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def my_task(self, param1):
    try:
        # Task logic
        result = do_something(param1)
        return result
    except SoftTimeLimitExceeded:
        logger.error("Task timed out")
        raise  # Will retry
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### Performance Optimization

1. **Use batch operations**: Process multiple items in one task
2. **Minimize database queries**: Use joins and select_related
3. **Cache frequently accessed data**: Use Redis caching
4. **Use bulk operations**: Bulk create/update/delete
5. **Parallelize independent tasks**: Use `group()` and `chain()`

### Task Signatures

```python
from celery import chain, group, chord

# Chain: Execute tasks sequentially
workflow = chain(
    task1.s(arg1),
    task2.s(arg2),
    task3.s(arg3)
)
workflow.delay()

# Group: Execute tasks in parallel
workflow = group([
    task1.s(arg1),
    task2.s(arg2),
    task3.s(arg3)
])
workflow.delay()

# Chord: Group + callback
workflow = chord([
    task1.s(arg1),
    task2.s(arg2),
    task3.s(arg3)
], callback_task.s())
workflow.delay()
```

---

## Troubleshooting

### Common Issues

**Task not executing**:
- Check if worker is running: `celery -A backend.celery_app inspect active`
- Check broker connectivity: `redis-cli ping`
- Check task registration: `celery -A backend.celery_app inspect registered`

**Task hanging indefinitely**:
- Check task timeout configuration
- Check for deadlocks in database operations
- Review logs for errors

**High memory usage**:
- Monitor worker memory: `celery -A backend.celery_app inspect stats`
- Restart workers periodically
- Use task time limits

**Tasks not retrying**:
- Check `max_retries` configuration
- Ensure exception is retryable (not `MaxRetriesExceededError`)
- Check retry delay configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Run Celery worker with verbose logging:

```bash
celery -A backend.celery_app worker --loglevel=debug
```

---

## References

- **Celery Documentation**: https://docs.celeryproject.org/
- **Celery Beat**: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
- **Flower**: https://flower.readthedocs.io/
- **Redis as Broker**: https://docs.celeryproject.org/en/stable/userguide/configuration.html#broker-settings

---

## Quick Reference

### Starting Celery Workers

```bash
# Start worker with default concurrency
celery -A backend.celery_app worker

# Start worker with specific concurrency
celery -A backend.celery_app worker --concurrency=4

# Start worker with log level
celery -A backend.celery_app worker --loglevel=info

# Start beat scheduler
celery -A backend.celery_app beat

# Start worker and beat together
celery -A backend.celery_app worker --beat
```

### Common Commands

```bash
# Check registered tasks
celery -A backend.celery_app inspect registered

# Check active tasks
celery -A backend.celery_app inspect active

# Check worker stats
celery -A backend.celery_app inspect stats

# Purge all tasks (use with caution)
celery -A backend.celery_app purge

# Show task execution info
celery -A backend.celery_app report
```

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
**Maintainer**: AgentHR Development Team
