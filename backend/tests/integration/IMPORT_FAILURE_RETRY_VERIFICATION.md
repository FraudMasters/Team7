# Import Failure Handling and Retry Mechanism - Verification Guide

## Overview

This document provides comprehensive verification procedures for the import failure handling and retry mechanism implemented for the Job Board Aggregation and Auto-Import feature.

## Feature Description

The import failure handling and retry mechanism ensures:

1. **Graceful Failure**: Imports that fail (e.g., invalid credentials, network errors) are logged with detailed error information
2. **Error Tracking**: All failures are recorded in the `import_logs` table with error messages, error details, and timestamps
3. **Retry Capability**: Failed or partially completed imports can be retried via the UI or API
4. **Retry Limits**: Maximum of 5 retry attempts to prevent infinite loops
5. **Status Tracking**: Import logs track retry counts and status changes throughout the retry workflow

## Architecture

### Components

1. **Backend API Endpoint**: `POST /api/integrations/logs/{log_id}/retry`
2. **Frontend Component**: `ImportLogsTable.tsx` with retry button
3. **Celery Task**: `poll_job_board` with built-in retry logic
4. **Database Models**: `ImportLog` with `retry_count` field

### Workflow

```
Import Triggered
       ↓
   Fails?  →  No → Success
       ↓
     Yes
       ↓
Create ImportLog (status=FAILED)
       ↓
Error logged (error_message, error_details)
       ↓
User clicks "Retry" button
       ↓
POST /api/integrations/logs/{id}/retry
       ↓
Validate:
  - Log exists
  - Status is FAILED or PARTIAL
  - Retry count < 5
  - Integration is enabled
       ↓
Increment retry_count
Update status to IN_PROGRESS
       ↓
Trigger new poll_job_board task
       ↓
Return 202 with new task_id
```

## Verification Methods

### Method 1: Automated Integration Tests (pytest)

**File**: `backend/tests/integration/test_import_failure_retry.py`

Run the full test suite:

```bash
cd backend
pytest tests/integration/test_import_failure_retry.py -v
```

**Test Classes**:

1. **TestImportFailureHandling**
   - `test_import_with_invalid_credentials_fails_gracefully`
   - `test_import_error_is_logged_with_details`

2. **TestImportRetryMechanism**
   - `test_retry_failed_import_successfully`
   - `test_retry_partial_import`
   - `test_cannot_retry_successful_import`
   - `test_cannot_retry_nonexistent_log`
   - `test_retry_updates_import_log_status`
   - `test_multiple_retries_increment_count`
   - `test_retry_respects_max_retry_limit`
   - `test_retry_disabled_integration_fails`
   - `test_retry_with_deleted_integration_fails`

3. **TestRetryEndToEnd**
   - `test_complete_retry_workflow`

**Expected Output**:
```
tests/integration/test_import_failure_retry.py::TestImportFailureHandling::test_import_with_invalid_credentials_fails_gracefully PASSED
tests/integration/test_import_failure_retry.py::TestImportFailureHandling::test_import_error_is_logged_with_details PASSED
...
======================== 13 passed in 45.23s ========================
```

### Method 2: Manual Python Test Script

**File**: `backend/tests/integration/manual_import_retry_test.py`

Standalone test script that doesn't require pytest:

```bash
cd backend/tests/integration
python manual_import_retry_test.py
```

**Tests Included**:
1. Test 1: Invalid Credentials Fail Gracefully
2. Test 2: Retry Failed Import
3. Test 3: Cannot Retry Successful Import
4. Test 4: Retry Limit Enforced
5. Test 5: Disabled Integration Cannot Retry

**Expected Output**:
```
======================================================================
          TEST 1: Invalid Credentials Fail Gracefully
======================================================================

ℹ Creating integration with invalid API key...
✓ Integration created with invalid credentials
ℹ Triggering import with invalid credentials...
✓ Import log found with status: failed
✓ Import log shows FAILED status ✓
✓ Error message logged: Authentication failed: Invalid API key...
✓ Timestamps present (started_at, completed_at)
✓ TEST 1 PASSED: Invalid credentials failed gracefully

...
======================================================================
                         TEST SUMMARY
======================================================================

PASSED: Test 1: Invalid Credentials Fail Gracefully
PASSED: Test 2: Retry Failed Import
PASSED: Test 3: Cannot Retry Successful Import
PASSED: Test 4: Retry Limit Enforced
PASSED: Test 5: Disabled Integration Cannot Retry

Total: 5/5 tests passed

ALL TESTS PASSED! ✓
```

### Method 3: API-Level Testing with curl

**File**: `backend/tests/integration/verify_import_retry.sh`

Bash script that tests the actual HTTP endpoints:

```bash
cd backend/tests/integration
chmod +x verify_import_retry.sh
./verify_import_retry.sh
```

**What It Tests**:
1. Server health check
2. Create integration with invalid credentials
3. Trigger import (will fail)
4. Check import logs for failure entry
5. Get specific import log details
6. Filter logs by status
7. Retry failed import
8. Verify disabled integrations cannot retry
9. Cleanup test data

**Expected Output**:
```
======================================================================
  Import Failure Handling and Retry Verification
======================================================================

✓ Server is running

======================================================================
  Creating Test Integration
======================================================================

✓ Integration created: 123e4567-e89b-12d3-a456-426614174000

...
======================================================================
  TEST SUMMARY
======================================================================

Tests Passed: 8
Tests Failed: 0
Total Tests:  8

ALL TESTS PASSED! ✓
```

### Method 4: End-to-End Browser Testing

**Prerequisites**:
- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- Worker (Celery) running

**Steps**:

1. **Navigate to Job Integrations Page**
   ```
   http://localhost:5173/recruiter/integrations
   ```

2. **Create Integration with Invalid Credentials**
   - Click "Add Integration" button
   - Enter name: "Test Indeed Integration"
   - Enter API endpoint: "https://api.indeed.com/v2"
   - Enter invalid API key: "invalid_bad_key"
   - Enter job ID in config: `{"job_id": "test-123"}`
   - Click "Save"

3. **Trigger Import**
   - Find the integration card
   - Click "Import Now" button
   - Button should show "Importing..." briefly

4. **Check Import Logs**
   - Scroll down to "Import Logs" section
   - Filter by status: "Failed"
   - Verify failed import is visible
   - Click expand arrow to see error details
   - Verify error message is displayed
   - Verify error details JSON is shown

5. **Fix Credentials**
   - Click edit icon on integration card
   - Update API key to valid credentials
   - Click "Save"

6. **Retry Failed Import**
   - In Import Logs table, find the failed import
   - Click the retry (circular arrow) icon in the Actions column
   - Button should show loading spinner
   - Success message should appear: "Import retry initiated successfully"

7. **Verify Retry**
   - Import log status should change to "IN_PROGRESS"
   - Retry count should be incremented to 1
   - New task should be created (check Celery logs)

8. **Verify Retry Cannot Be Done on Successful Imports**
   - Filter by status: "Success"
   - Verify retry button is not visible for successful imports

9. **Verify Retry Limit**
   - Retry the same import 4 more times (total 5)
   - On the 6th attempt, retry button should be disabled
   - Or API should return error: "Maximum retries exceeded"

## Database Verification

### SQL Queries

**Check import logs with errors**:
```sql
SELECT
    id,
    job_board_name,
    status,
    error_message,
    retry_count,
    created_at
FROM import_logs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

**Check retry distribution**:
```sql
SELECT
    retry_count,
    COUNT(*) as count
FROM import_logs
WHERE status != 'in_progress'
GROUP BY retry_count
ORDER BY retry_count;
```

**View failed imports by job board**:
```sql
SELECT
    job_board_name,
    COUNT(*) as failed_count,
    AVG(records_failed) as avg_failed_records
FROM import_logs
WHERE status = 'failed'
GROUP BY job_board_name;
```

## Common Issues and Solutions

### Issue 1: "Import log not found" when retrying

**Cause**: Import log ID is invalid or log was deleted

**Solution**:
- Verify the import log ID exists in database
- Check that the log hasn't been cleaned up

### Issue 2: "Cannot retry import with status 'completed'"

**Cause**: Attempting to retry a successful import

**Solution**:
- Only failed or partial imports can be retried
- Create a new import instead

### Issue 3: "Maximum retries exceeded"

**Cause**: Import has been retried 5 times already

**Solution**:
- Review why the import keeps failing
- Fix the root cause (credentials, API endpoint, etc.)
- Create a new integration instead of retrying

### Issue 4: "Integration is disabled"

**Cause**: Job board integration is disabled

**Solution**:
- Enable the integration before retrying
- Use the toggle endpoint: `PATCH /api/integrations/{id}/toggle`

### Issue 5: Task triggered but import log not updated

**Cause**: Celery worker not running or task failed silently

**Solution**:
- Check Celery worker is running: `celery -A backend.celery_app worker -l info`
- Check Celery logs for errors
- Verify Redis connection

## Verification Checklist

### Backend Functionality

- [ ] Retry endpoint exists: `POST /api/integrations/logs/{log_id}/retry`
- [ ] Returns 404 for non-existent logs
- [ ] Returns 400 for non-retryable statuses (completed, skipped)
- [ ] Returns 400 when retry limit (5) exceeded
- [ ] Returns 400 when integration is disabled
- [ ] Returns 400 when integration deleted
- [ ] Returns 202 with task_id on successful retry
- [ ] Increments retry_count in import log
- [ ] Updates import log status to IN_PROGRESS
- [ ] Clears previous error_message
- [ ] Triggers new poll_job_board Celery task

### Frontend Functionality

- [ ] Import logs table displays failed imports
- [ ] Retry button only visible for failed/partial imports
- [ ] Retry button shows loading state
- [ ] Success/error messages displayed via Snackbar
- [ ] Error details expandable in log rows
- [ ] Retry count displayed in log details
- [ ] Refresh button reloads logs

### Error Handling

- [ ] Invalid credentials logged with error message
- [ ] Network errors logged properly
- [ ] API errors captured in error_details
- [ ] Timestamps recorded (started_at, completed_at)
- [ ] Import metadata preserved for retry
- [ ] Multiple retry attempts tracked correctly

### Edge Cases

- [ ] Cannot retry successful imports
- [ ] Cannot retry skipped imports
- [ ] Cannot retry beyond max limit
- [ ] Cannot retry disabled integrations
- [ ] Cannot retry with deleted integration
- [ ] Retry preserves original import parameters

## Production Readiness

### Monitoring

Monitor these metrics in production:

1. **Import Failure Rate**
   ```sql
   SELECT
       COUNT(CASE WHEN status = 'failed' THEN 1 END) * 100.0 / COUNT(*) as failure_rate
   FROM import_logs
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```

2. **Retry Distribution**
   ```sql
   SELECT
       retry_count,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
   FROM import_logs
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY retry_count
   ORDER BY retry_count;
   ```

3. **Common Errors**
   ```sql
   SELECT
       error_message,
       COUNT(*) as occurrences
   FROM import_logs
   WHERE status = 'failed'
     AND created_at > NOW() - INTERVAL '24 hours'
   GROUP BY error_message
   ORDER BY occurrences DESC
   LIMIT 10;
   ```

### Alerts

Set up alerts for:
- High failure rate (> 50% in last hour)
- Many imports at retry limit (> 10 in last hour)
- Disabled integrations with failed imports
- Repeated authentication failures

## Next Steps

After verification:

1. **Integration Testing**: Complete subtask-6-5 (Resume parsing auto-runs on imported resumes)
2. **Performance Testing**: Load test retry endpoint under high concurrency
3. **Security Review**: Ensure API keys masked in logs
4. **Documentation**: Update user-facing docs with retry instructions
5. **Monitoring**: Set up production monitoring and alerts

## Contact

For questions or issues during verification, refer to:
- Implementation Plan: `.auto-claude/specs/067-job-board-aggregation-and-auto-import/implementation_plan.json`
- Build Progress: `.auto-claude/specs/067-job-board-aggregation-and-auto-import/build-progress.txt`
- Context: `.auto-claude/specs/067-job-board-aggregation-and-auto-import/context.json`
