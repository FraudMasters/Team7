# Manual Import Trigger Verification Guide

This guide provides step-by-step instructions to verify the manual import trigger functionality from the frontend.

## Overview

The manual import trigger allows users to click an "Import Now" button on job board integrations to immediately trigger the Celery import task, without waiting for the scheduled polling interval.

## Architecture

```
Frontend UI (JobIntegrationsPage)
    ↓
POST /api/integrations/{id}/trigger-import
    ↓
Backend API (job_integrations.py)
    ↓
Celery Task: poll_job_board.apply_async()
    ↓
Job Board API Client (Indeed/ZipRecruiter/Glassdoor)
    ↓
Import Log Entry Created
```

## Verification Steps

### 1. Backend API Endpoint Verification

#### Test 1.1: Health Check
```bash
curl -X GET http://localhost:8000/api/integrations/
```

Expected: JSON response with list of integrations (may be empty)

#### Test 1.2: Create Test Integration
```bash
curl -X POST http://localhost:8000/api/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Verification Test Integration",
    "api_endpoint": "https://api.indeed.com/v2",
    "api_key": "test_key_1234567890",
    "enabled": true
  }'
```

Expected:
```json
{
  "id": "uuid-here",
  "name": "Verification Test Integration",
  "api_endpoint": "https://api.indeed.com/v2",
  "api_key": "test_***7890",
  "enabled": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Test 1.3: Trigger Manual Import
```bash
curl -X POST http://localhost:8000/api/integrations/{integration_id}/trigger-import
```

Expected:
```json
{
  "task_id": "celery-task-uuid",
  "integration_id": "integration-uuid",
  "integration_name": "Verification Test Integration",
  "message": "Import task triggered successfully",
  "status": "pending"
}
```

#### Test 1.4: Verify Celery Task Received
Check Celery worker logs:
```bash
docker logs <celery-worker-container>
```

Expected to see:
```
[2024-01-01 00:00:00,000: INFO/MainProcess] Received task: tasks.import_tasks.poll_job_board[task-id]
[2024-01-01 00:00:00,100: INFO/ForkPoolWorker-1] Polling job board integration_id=uuid
```

#### Test 1.5: Check Import Logs
```bash
curl -X GET http://localhost:8000/api/integrations/logs?limit=5
```

Expected: Import log entry with status, record counts, and timestamps

### 2. Frontend UI Verification

#### Test 2.1: Navigate to Job Integrations Page
1. Open browser to `http://localhost:5173/integrations`
2. Verify page loads without errors
3. Check browser console for no errors

Expected: Job Board Integrations page displays with integrations list

#### Test 2.2: Verify "Import Now" Button
1. Locate an enabled integration card
2. Verify "Import Now" button is visible
3. Verify button is enabled (not disabled)

Expected:
- Button with sync icon and "Import Now" text
- Button is clickable
- Button disabled for disabled integrations

#### Test 2.3: Click "Import Now" Button
1. Click the "Import Now" button on an integration
2. Verify button state changes to "Importing..."
3. Wait for API response
4. Verify success snackbar appears

Expected:
- Button text changes to "Importing..." while loading
- Success message appears: "Import triggered for {name}. Task ID: {task-id}"
- Button returns to "Import Now" state

#### Test 2.4: Verify Error Handling
1. Disable an integration
2. Try clicking "Import Now" button (should be disabled)
3. Or trigger via API with disabled integration

Expected:
- Button is disabled for disabled integrations
- Error snackbar appears if API call fails

### 3. End-to-End Verification

#### Test 3.1: Full Import Flow
1. Navigate to Job Integrations page
2. Click "Import Now" on an integration
3. Note the task ID from success message
4. Check Celery worker logs for task execution
5. Check import logs in database or frontend
6. Verify new import log entry appears

#### Test 3.2: Multiple Concurrent Imports
1. Click "Import Now" on 2-3 different integrations quickly
2. Verify all requests succeed
3. Check Celery worker logs - tasks should queue and execute
4. Verify multiple import log entries created

#### Test 3.3: Import with Real Job Board (Optional)
If you have valid API credentials:
1. Create integration with real API key
2. Trigger manual import
3. Verify applicants are fetched
4. Verify ImportedResume records created
5. Verify import log shows success/failure counts

## Database Verification

### Query Import Logs
```sql
SELECT
  id,
  job_board_name,
  status,
  records_processed,
  records_succeeded,
  records_failed,
  error_message,
  started_at,
  completed_at
FROM import_logs
ORDER BY created_at DESC
LIMIT 10;
```

### Query Imported Resumes
```sql
SELECT
  ir.id,
  ir.external_id,
  ir.import_status,
  ir.candidate_name,
  ir.candidate_email,
  jbi.name as job_board_name
FROM imported_resumes ir
JOIN job_board_integrations jbi ON ir.job_board_id = jbi.id
ORDER BY ir.created_at DESC
LIMIT 10;
```

## Common Issues and Solutions

### Issue 1: "Integration not found" (404)
**Cause:** Integration ID doesn't exist or was deleted
**Solution:** Verify integration exists in database

### Issue 2: "Cannot trigger import for disabled integration" (400)
**Cause:** Integration is disabled
**Solution:** Enable the integration first via PATCH /api/integrations/{id}/toggle

### Issue 3: "Failed to trigger import task" (500)
**Cause:** Celery worker not running or not connected to Redis
**Solution:**
- Check Celery worker is running: `docker ps | grep celery`
- Check Redis connection: `docker logs <celery-container>`
- Verify Redis is accessible from Celery worker

### Issue 4: Button disabled in UI
**Cause:** Integration is disabled
**Solution:** Enable integration via UI menu (options → enable)

### Issue 5: No import log created
**Cause:** Celery task failed or job board API error
**Solution:**
- Check Celery worker logs for errors
- Verify job board API credentials are valid
- Check import_logs table for error details

## Automated Testing

Run the integration test suite:
```bash
cd backend
pytest tests/integration/test_manual_import_trigger.py -v
```

Run the manual test script:
```bash
cd backend/tests/integration
chmod +x manual_import_trigger_test.sh
./manual_import_trigger_test.sh
```

## Verification Checklist

- [ ] Backend endpoint returns 202 with task_id
- [ ] Celery task is queued and executes
- [ ] Import log entry is created
- [ ] Frontend "Import Now" button visible and functional
- [ ] Success snackbar appears with task ID
- [ ] Disabled integrations cannot trigger import
- [ ] Invalid integration IDs return 404
- [ ] Invalid UUID format returns 422
- [ ] Multiple concurrent imports work correctly
- [ ] Error handling works (network errors, server errors)

## Success Criteria

The manual import trigger is working correctly when:
1. User can click "Import Now" button on any enabled integration
2. API returns 202 Accepted with valid task_id
3. Celery worker receives and processes the task
4. Import log entry is created with appropriate status
5. UI provides user feedback (success/error messages)
6. Disabled integrations cannot trigger imports
