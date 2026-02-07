# Import Failure Handling and Retry Mechanism - Verification Guide

This document provides comprehensive verification instructions for testing import failure handling and retry mechanisms in the job board aggregation system.

## Overview

The import failure handling system ensures that:
1. Invalid credentials cause graceful failures (no crashes)
2. All errors are logged in ImportLog with detailed information
3. Failed imports can be retried after fixing issues
4. Multiple failure/success attempts are properly tracked

## Architecture

### Error Flow

```
┌─────────────────┐
│ Trigger Import  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ poll_job_board Task     │
│ - Get Integration       │
│ - Check Enabled         │
│ - Initialize Client     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Fetch Applicants        │
│ (API Call)              │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────┐
│ Success │  Failure  │
└───┬───┘  └────┬─────┘
    │            │
    │            ▼
    │    ┌──────────────────┐
    │    │ Create ImportLog │
    │    │ - status=FAILED  │
    │    │ - error_message  │
    │    │ - error_details  │
    │    └──────────────────┘
    │
    ▼
┌──────────────────┐
│ Create ImportLog │
│ - status=SUCCESS │
│ - record counts  │
└──────────────────┘
```

### Error Handling Layers

1. **Client Level** (`indeed_client.py`):
   - HTTPStatusError: 401, 403, 500 errors
   - RequestError: Network failures, timeouts
   - Returns IndeedFetchResult with errors list

2. **Task Level** (`import_tasks.py`):
   - Catches client errors
   - Creates ImportLog with error details
   - Implements retry logic (max 3 retries with exponential backoff)

3. **API Level** (`job_integrations.py`):
   - Validates integration exists and is enabled
   - Returns 202 Accepted (async task execution)
   - Errors caught during task execution

## Test Files

### Automated Tests

**File**: `test_import_failure_handling.py`

Run with pytest:
```bash
pytest backend/tests/integration/test_import_failure_handling.py -v
```

Test cases:
- `test_import_with_invalid_api_key_fails_gracefully`: Verifies 401 errors don't crash
- `test_import_failure_logs_error_details`: Checks error details are captured
- `test_import_with_missing_job_id_in_config`: Tests validation errors
- `test_retry_with_fixed_credentials_succeeds`: Full failure-to-success flow
- `test_manual_trigger_with_invalid_credentials`: API trigger validation
- `test_import_with_disabled_integration_fails`: Disabled integration handling
- `test_multiple_failures_and_then_success`: Multiple retry attempts

### Manual Tests

**File**: `manual_import_failure_test.py`

Run directly:
```bash
cd backend/tests/integration
chmod +x manual_import_failure_test.py
python manual_import_failure_test.py
```

Test scenarios:
1. Invalid API Key → Graceful failure
2. Network Error → Proper error logging
3. Retry After Fixing Credentials → Success after fix
4. Missing Job ID → Configuration validation
5. Disabled Integration → Access control

## Verification Steps

### 1. Verify Invalid API Key Handling

**Objective**: Ensure invalid API keys don't crash the system.

**Steps**:

1. Create integration with invalid API key:
```sql
INSERT INTO job_board_integrations (id, name, api_endpoint, api_key, enabled, config, created_at, updated_at)
VALUES (
    'test-integration-1',
    'Test Invalid Key',
    'https://api.indeed.com/v1',
    'invalid_key_12345',
    true,
    '{"job_id": "test_job_1"}'::jsonb,
    NOW(),
    NOW()
);
```

2. Trigger import via API:
```bash
curl -X POST http://localhost:8000/api/integrations/test-integration-1/trigger-import
```

3. Check import logs:
```sql
SELECT
    id,
    status,
    error_message,
    error_details,
    records_processed,
    records_succeeded,
    created_at
FROM import_logs
WHERE job_board_id = 'test-integration-1'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Results**:
- Response: `202 Accepted` with task_id
- ImportLog exists with `status = 'failed'`
- `error_message` contains "401" or "Unauthorized"
- `records_processed = 0`, `records_succeeded = 0`
- No crash or 500 error

**Verification Query**:
```sql
-- Should have 1+ failed import log
SELECT COUNT(*) >= 1 AS has_failed_log
FROM import_logs
WHERE job_board_id = 'test-integration-1'
AND status = 'failed';
```

### 2. Verify Error Details Are Logged

**Objective**: Ensure errors are captured with sufficient detail.

**Steps**:

1. After triggering failed import, inspect log:
```sql
SELECT
    error_message,
    error_details,
    import_metadata
FROM import_logs
WHERE job_board_id = 'test-integration-1'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Results**:
- `error_message` is not NULL
- `error_details` is JSON with `errors` array
- `import_metadata` contains job_id, status_filter, etc.

**Example Output**:
```json
{
  "error_message": "HTTP error fetching applicants: 401 - Unauthorized",
  "error_details": {
    "errors": [
      "HTTP error fetching applicants: 401 - Unauthorized"
    ]
  },
  "import_metadata": {
    "job_id": "test_job_1",
    "status_filter": null,
    "from_date": null
  }
}
```

### 3. Verify Retry After Fixing Credentials

**Objective**: Ensure fixing credentials allows successful retry.

**Steps**:

1. Update API key:
```sql
UPDATE job_board_integrations
SET api_key = 'correct_api_key_here'
WHERE id = 'test-integration-1';
```

2. Trigger import again:
```bash
curl -X POST http://localhost:8000/api/integrations/test-integration-1/trigger-import
```

3. Check import logs:
```sql
SELECT
    status,
    records_processed,
    records_succeeded,
    created_at
FROM import_logs
WHERE job_board_id = 'test-integration-1'
ORDER BY created_at;
```

**Expected Results**:
- First log: `status = 'failed'`
- Second log: `status = 'success'` or `completed`
- Second log has `records_succeeded > 0`
- Both logs exist (history is preserved)

### 4. Verify Network Error Handling

**Objective**: Ensure network issues don't crash the system.

**Steps**:

1. Create integration with unreachable endpoint:
```sql
INSERT INTO job_board_integrations (id, name, api_endpoint, api_key, enabled, config, created_at, updated_at)
VALUES (
    'test-network-error',
    'Test Network Error',
    'https://unreachable-domain-12345.com',
    'test_key',
    true,
    '{"job_id": "test_job_2"}'::jsonb,
    NOW(),
    NOW()
);
```

2. Trigger import and check logs:
```sql
SELECT error_message
FROM import_logs
WHERE job_board_id = 'test-network-error'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Results**:
- `error_message` contains "Connection" or "timeout" or "Request error"
- Import completes (doesn't hang indefinitely)
- System remains responsive

### 5. Verify Multiple Attempts Are Logged

**Objective**: Ensure each import attempt creates a separate log.

**Steps**:

1. Trigger import 3 times (with invalid credentials):
```bash
for i in {1..3}; do
    curl -X POST http://localhost:8000/api/integrations/test-integration-1/trigger-import
    sleep 2
done
```

2. Count logs:
```sql
SELECT COUNT(*) as total_logs
FROM import_logs
WHERE job_board_id = 'test-integration-1';
```

**Expected Results**:
- `total_logs = 3`
- Each log has distinct `created_at` timestamp
- All logs show `status = 'failed'`

### 6. Verify Disabled Integration Handling

**Objective**: Ensure disabled integrations cannot import.

**Steps**:

1. Disable integration:
```sql
UPDATE job_board_integrations
SET enabled = false
WHERE id = 'test-integration-1';
```

2. Try to trigger import:
```bash
curl -i -X POST http://localhost:8000/api/integrations/test-integration-1/trigger-import
```

**Expected Results**:
- HTTP response: `400 Bad Request`
- Response body contains "disabled"
- No Celery task is triggered
- No new import logs created

## Common Issues and Solutions

### Issue 1: Import hangs indefinitely

**Symptoms**: Import task never completes, no log created.

**Causes**:
- API endpoint is slow/unresponsive
- Missing timeout configuration

**Solutions**:
- Check IndeedClient timeout setting (default 30s)
- Verify API endpoint is reachable
- Check Celery worker logs

**Debug Query**:
```sql
-- Check for incomplete logs
SELECT * FROM import_logs
WHERE completed_at IS NULL
AND created_at < NOW() - INTERVAL '5 minutes';
```

### Issue 2: Error message is generic

**Symptoms**: `error_message` doesn't provide useful information.

**Causes**:
- Exception caught at wrong level
- Error details not propagated

**Solutions**:
- Check `error_details` JSON field for more context
- Review Celery worker logs for full stack trace
- Verify client error handling

### Issue 3: Retry doesn't work after fixing credentials

**Symptoms**: Still getting 401 errors after updating API key.

**Causes**:
- Celery worker cached old integration
- Database transaction not committed
- Wrong integration updated

**Solutions**:
- Restart Celery worker after credential changes
- Verify UPDATE affected 1 row
- Check `api_key` field in database

**Verification Query**:
```sql
SELECT name, api_key, enabled
FROM job_board_integrations
WHERE id = 'test-integration-1';
```

### Issue 4: Import logs growing too large

**Symptoms**: Too many log entries, slow queries.

**Causes**:
- Frequent failed imports
- No log cleanup strategy

**Solutions**:
- Implement log archival (move old logs to cold storage)
- Delete logs older than X days
- Add index on `created_at` for faster cleanup

**Cleanup Query** (example):
```sql
-- Delete failed logs older than 90 days
DELETE FROM import_logs
WHERE status = 'failed'
AND created_at < NOW() - INTERVAL '90 days';
```

## Verification Checklist

Complete all items to verify the feature:

### Functional Requirements
- [ ] Invalid API key causes graceful failure
- [ ] Error is logged in ImportLog with details
- [ ] Network errors don't crash the system
- [ ] Missing configuration is caught and logged
- [ ] Disabled integrations cannot import
- [ ] Retry after fixing credentials succeeds
- [ ] Multiple attempts create separate logs

### Data Integrity
- [ ] All ImportLog fields are populated correctly
- [ ] `error_details` JSON is valid
- [ ] `import_metadata` preserves request parameters
- [ ] `status` enum values are correct
- [ ] `retry_count` increments properly (if implemented)

### API Contract
- [ ] POST `/api/integrations/{id}/trigger-import` returns 202 for valid request
- [ ] Returns 400 for disabled integration
- [ ] Returns 404 for non-existent integration
- [ ] Returns 422 for invalid UUID format

### Performance
- [ ] Failed imports complete quickly (no hanging)
- [ ] Import log queries are fast with proper indexes
- [ ] Concurrent imports don't deadlock

### Security
- [ ] API keys are masked in logs
- [ ] Error messages don't leak sensitive data
- [ ] Failed imports don't expose system details

## Next Steps

After verification:

1. **Production Deployment**:
   - Set up log monitoring (alert on high failure rates)
   - Configure log retention policy
   - Document retry strategy for users

2. **Monitoring**:
   - Dashboard showing import success/failure rates
   - Alerts for repeated authentication failures
   - Track error types by frequency

3. **Enhancements**:
   - Automatic retry with exponential backoff
   - Webhook notifications for failed imports
   - Import log UI with retry button

## Contact

For questions or issues with verification, refer to:
- Test files: `test_import_failure_handling.py`, `manual_import_failure_test.py`
- Implementation: `backend/tasks/import_tasks.py`
- Client: `backend/services/job_board_clients/indeed_client.py`
