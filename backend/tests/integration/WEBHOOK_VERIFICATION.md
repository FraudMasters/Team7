# Webhook Endpoint Verification Guide

## Overview
This document provides step-by-step instructions for verifying the webhook endpoint implementation (subtask-6-1).

## Prerequisites

1. **Backend server running**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Database initialized**:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Tools installed**:
   - `curl` (for HTTP requests)
   - `jq` (for JSON parsing)
   - `pytest` (for automated tests)

## Verification Steps

### Step 1: Send POST Request to Webhook Endpoint

#### Test 1.1: Minimal Valid Payload
```bash
curl -X POST http://localhost:8000/api/webhooks/resume \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "candidate_name": "Jane Smith"
  }'
```

**Expected Response**:
```json
{
  "id": "uuid-here",
  "status": "pending",
  "message": "File uploaded successfully",
  "source": "test"
}
```

#### Test 1.2: Full Payload with All Fields
```bash
curl -X POST http://localhost:8000/api/webhooks/resume \
  -H "Content-Type: application/json" \
  -d '{
    "source": "indeed",
    "resume_url": "https://example.com/resumes/john_doe.pdf",
    "candidate_name": "John Doe",
    "candidate_email": "john.doe@example.com",
    "candidate_phone": "+1-555-0123-4567",
    "job_id": "job-12345",
    "metadata": {
      "external_id": "ext-67890",
      "applied_date": "2026-02-03"
    }
  }'
```

**Expected Response**:
```json
{
  "id": "uuid-here",
  "status": "pending",
  "message": "File uploaded successfully",
  "source": "indeed"
}
```

#### Test 1.3: Invalid Payload (Empty Source)
```bash
curl -X POST http://localhost:8000/api/webhooks/resume \
  -H "Content-Type: application/json" \
  -d '{
    "source": "   ",
    "candidate_name": "Test"
  }'
```

**Expected Response**: HTTP 400 Bad Request

#### Test 1.4: Missing Required Field
```bash
curl -X POST http://localhost:8000/api/webhooks/resume \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Test",
    "candidate_email": "test@example.com"
  }'
```

**Expected Response**: HTTP 422 Unprocessable Entity

### Step 2: Verify Resume is Stored in Database

Using psql:
```bash
psql -U agenthr -d agenthr -c \
  "SELECT id, filename, status, raw_text, created_at
   FROM resumes
   WHERE filename LIKE 'webhook_%'
   ORDER BY created_at DESC
   LIMIT 5;"
```

**Expected Results**:
- Resume records with filenames like `webhook_indeed_<uuid>`
- Status should be `PENDING`
- `raw_text` should contain candidate information

### Step 3: Verify Audit Log Entry

```bash
psql -U agenthr -d agenthr -c \
  "SELECT id, entity_type, action_type, action_data, created_at
   FROM audit_logs
   WHERE action_type = 'resume_uploaded'
   ORDER BY created_at DESC
   LIMIT 5;"
```

**Expected Results**:
- Audit log with `action_type = 'resume_uploaded'`
- `action_data` should contain `"webhook": true`
- `action_data` should contain the source field

### Step 4: Check Celery Task Status

**Note**: The current webhook implementation creates a Resume record in PENDING status but does NOT directly queue a Celery task for processing. This is by design - the processing task (`process_imported_resume`) is triggered separately by:

1. The `poll_job_board` Celery task (subtask-4-1)
2. Manual trigger from frontend
3. Direct API call to processing endpoint

To verify this behavior:
```bash
# Check if Celery worker is running
pgrep -f "celery.*worker"

# If running, check for queued tasks
celery -A celery_app inspect active
```

### Step 5: Check Import Log

Import logs are created by the `poll_job_board` task, not directly by the webhook. However, you can verify the import_log table structure:

```bash
psql -U agenthr -d agenthr -c \
  "\d import_logs"
```

## Automated Testing

### Run Integration Tests
```bash
cd backend
pytest tests/integration/test_job_board_import_flow.py -v
```

### Run Specific Test Class
```bash
cd backend
pytest tests/integration/test_job_board_import_flow.py::TestWebhookResumeSubmission -v
```

### Run with Coverage
```bash
cd backend
pytest tests/integration/test_job_board_import_flow.py \
  --cov=api.webhooks \
  --cov-report=html
```

## Verification Checklist

Complete each item and check the box:

- [ ] Webhook endpoint responds to POST requests
- [ ] Minimal payload (source only) is accepted
- [ ] Full payload with all fields is accepted
- [ ] Empty source field returns 400 error
- [ ] Missing source field returns 422 error
- [ ] Invalid URL format returns 422 error
- [ ] Resume record is created in database
- [ ] Resume status is set to PENDING
- [ ] Resume raw_text contains candidate information
- [ ] Audit log entry is created
- [ ] Audit log contains webhook metadata
- [ ] Integration tests pass
- [ ] No console errors or exceptions

## Expected Behavior Summary

1. **Webhook Endpoint** (`POST /api/webhooks/resume`):
   - Accepts resume submissions from external sources
   - Validates required fields
   - Returns 201 CREATED on success
   - Returns 400/422 on validation errors

2. **Database Storage**:
   - Creates Resume record with PENDING status
   - Stores candidate information in raw_text field
   - Filename follows pattern: `webhook_{source}_{uuid}`

3. **Audit Logging**:
   - Creates audit log entry
   - Tracks source, candidate info, and webhook flag
   - Records IP address and user agent

4. **Celery Integration**:
   - No immediate task queuing (by design)
   - Processing triggered separately via poll_job_board task
   - Resume remains in PENDING until processing

## Common Issues and Solutions

### Issue: Connection Refused
**Solution**: Ensure backend server is running on port 8000

### Issue: Database Connection Error
**Solution**: Verify PostgreSQL is running and credentials are correct

### Issue: Import Logs Not Created
**Solution**: This is expected - import logs are created by poll_job_board task, not webhook

### Issue: Resume Not Processed
**Solution**: Webhook only stores resume. Run poll_job_board task or trigger processing manually

## Next Steps

After verifying webhook endpoint:
1. Test manual import trigger (subtask-6-2)
2. Test duplicate detection (subtask-6-3)
3. Test import failure handling (subtask-6-4)
4. Test resume parsing automation (subtask-6-5)

## Files Created

- `backend/tests/integration/test_job_board_import_flow.py` - Integration test suite
- `backend/tests/integration/verify_webhook.sh` - Automated verification script
- `backend/tests/integration/WEBHOOK_VERIFICATION.md` - This documentation
