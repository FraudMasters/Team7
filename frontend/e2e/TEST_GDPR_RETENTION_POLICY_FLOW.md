# GDPR Data Retention Policy End-to-End Test Guide

## Overview

This document provides instructions for testing the complete GDPR data retention policy automation from policy creation through automated data cleanup to audit trail verification.

## Test File

**Location**: `frontend/e2e/gdpr-retention-policy-flow.spec.ts`

**Test Suites**:
- Retention Policy Management API Tests (5 tests)
- Data Creation with Different Ages (3 tests)
- Cleanup Execution Tests (3 tests)
- Data Verification Tests (3 tests)
- Audit Trail Verification Tests (2 tests)
- Mobile Responsive Tests (2 tests)
- Complete End-to-End Workflow Test (1 test)

**Total**: 19 tests

## Prerequisites

### 1. Backend API Running

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Dev Server Running

```bash
cd frontend
npm run dev
```

### 3. Database Running

- PostgreSQL with GDPR tables created
- Run migrations: `cd backend && alembic upgrade head`

### 4. Celery Worker Available (Optional)

For manual task execution:
```bash
cd backend
celery -A celery_app worker --loglevel=info
```

## Running the Tests

### Run All Retention Policy Flow Tests

```bash
cd frontend
npx playwright test gdpr-retention-policy-flow.spec.ts
```

### Run with UI Mode (Interactive)

```bash
cd frontend
npx playwright test gdpr-retention-policy-flow.spec.ts --ui
```

### Run with Headed Mode (See Browser)

```bash
cd frontend
npx playwright test gdpr-retention-policy-flow.spec.ts --headed
```

### Run Specific Test Suite

```bash
# Test only API management
npx playwright test gdpr-retention-policy-flow.spec.ts -g "API Management"

# Test only data creation
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Data Creation"

# Test only cleanup execution
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Cleanup Execution"

# Test only data verification
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Data Verification"

# Test only audit trail
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Audit Trail"

# Test only mobile responsive
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Mobile Responsive"

# Test complete end-to-end
npx playwright test gdpr-retention-policy-flow.spec.ts -g "Complete End-to-End"
```

### Run with Bash Script

```bash
cd frontend
./scripts/test-gdpr-retention-policy-flow.sh

# With options
./scripts/test-gdpr-retention-policy-flow.sh --ui
./scripts/test-gdpr-retention-policy-flow.sh --headed
./scripts/test-gdpr-retention-policy-flow.sh --grep "API Management"
```

## Manual Testing Steps

### Step 1: Create Retention Policy

**API Endpoint**: `POST /api/retention-policies/`

**Request Body**:
```json
{
  "policy_name": "30-Day Cleanup Policy",
  "entity_type": "resumes",
  "retention_days": 30,
  "action_type": "delete",
  "organization_id": null,
  "is_active": true,
  "description": "Delete resumes older than 30 days",
  "legal_basis": "legitimate_interest",
  "deletion_reason": "retention_period_expired"
}
```

**Expected Response** (201 Created):
```json
{
  "id": "uuid-here",
  "policy_name": "30-Day Cleanup Policy",
  "entity_type": "resumes",
  "retention_days": 30,
  "action_type": "delete",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Verification**:
- ✅ Policy created with specified parameters
- ✅ Policy ID returned
- ✅ Timestamps populated

### Step 2: Create Test Data with Different Ages

**Create Old Resume** (60+ days ago):

```bash
curl -X POST http://localhost:8000/api/resumes/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "old_resume_60days.pdf",
    "raw_text": "Old resume content",
    "language": "en",
    "status": "active",
    "created_at": "2024-12-06T10:00:00Z"
  }'
```

**Create Recent Resume** (within 30 days):

```bash
curl -X POST http://localhost:8000/api/resumes/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "recent_resume_10days.pdf",
    "raw_text": "Recent resume content",
    "language": "en",
    "status": "active",
    "created_at": "2025-01-25T10:00:00Z"
  }'
```

**Verification**:
- ✅ Old resume created with timestamp > 30 days ago
- ✅ Recent resume created with timestamp < 30 days ago
- ✅ Both resumes returned IDs

### Step 3: Run Retention Cleanup (Dry-Run Mode First)

**API Endpoint**: `POST /api/retention-policies/cleanup`

**Request Body** (Dry-Run):
```json
{
  "organization_id": null,
  "dry_run": true
}
```

**Expected Response** (200 OK):
```json
{
  "status": "success",
  "organization_id": null,
  "dry_run": true,
  "total_processed": 1,
  "total_succeeded": 1,
  "total_failed": 0,
  "entity_types": {
    "resumes": {
      "total_processed": 1,
      "deleted_count": 1,
      "anonymized_count": 0,
      "archived_count": 0,
      "flagged_count": 0
    }
  },
  "processing_time_ms": 123.45
}
```

**Verification**:
- ✅ Cleanup task executes successfully
- ✅ Dry-run mode reported
- ✅ Statistics by entity type returned
- ✅ Processing time recorded

**Verify Dry-Run Didn't Delete Data**:

```bash
# Check if old resume still exists
curl http://localhost:8000/api/resumes/{old_resume_id}

# Expected: 200 OK with resume data
```

### Step 4: Run Actual Retention Cleanup

**Request Body** (Actual Cleanup):
```json
{
  "organization_id": null,
  "dry_run": false
}
```

**Expected Response**:
```json
{
  "status": "success",
  "organization_id": null,
  "dry_run": false,
  "total_processed": 1,
  "total_succeeded": 1,
  "total_failed": 0,
  "entity_types": {
    "resumes": {
      "total_processed": 1,
      "deleted_count": 1,
      "anonymized_count": 0,
      "archived_count": 0,
      "flagged_count": 0
    }
  },
  "processing_time_ms": 234.56
}
```

**Verification**:
- ✅ Cleanup task executes successfully
- ✅ Dry-run flag is false
- ✅ Old data processed and deleted

### Step 5: Verify Old Data Deleted

```bash
# Check if old resume exists
curl http://localhost:8000/api/resumes/{old_resume_id}

# Expected: 404 Not Found
```

**Verification**:
- ✅ Old resume (60 days) returns 404
- ✅ Resume no longer in database
- ✅ Associated records deleted (cascade)

### Step 6: Verify Recent Data Preserved

```bash
# Check if recent resume exists
curl http://localhost:8000/api/resumes/{recent_resume_id}

# Expected: 200 OK with resume data
```

**Verification**:
- ✅ Recent resume (10 days) returns 200
- ✅ Resume data intact
- ✅ All fields present

### Step 7: Verify Cleanup Logged to Audit Trail

**API Endpoint**: `GET /api/audit-logs/?entity_type=retention_cleanup&limit=100`

**Expected Response**:
```json
{
  "total_count": 1,
  "logs": [
    {
      "id": "uuid-here",
      "action": "retention_cleanup",
      "entity_type": "retention_cleanup",
      "entity_id": null,
      "user_id": null,
      "organization_id": null,
      "changes": {
        "before": null,
        "after": {
          "total_deleted": 1,
          "entity_types": ["resumes"]
        }
      },
      "ip_address": null,
      "user_agent": "Celery/1.0",
      "created_at": "2025-02-03T10:30:00Z"
    }
  ]
}
```

**Verification**:
- ✅ Audit log entry created for cleanup
- ✅ Action is "retention_cleanup"
- ✅ Entity type is "retention_cleanup"
- ✅ Changes record deleted count
- ✅ Timestamp recorded
- ✅ User agent shows system task

### Step 8: Verify Policy Details in Audit Log

**Check audit log details**:

```bash
curl http://localhost:8000/api/audit-logs/?entity_type=retention_cleanup&limit=50
```

**Expected in audit log details**:
```json
{
  "details": {
    "policy_id": "policy-uuid",
    "policy_name": "30-Day Cleanup Policy",
    "retention_days": 30,
    "entity_type": "resumes",
    "action_type": "delete"
  }
}
```

**Verification**:
- ✅ Policy ID recorded
- ✅ Policy name recorded
- ✅ Retention period recorded
- ✅ Entity type and action recorded

## Test Coverage

### API Tests (5 tests)

1. **Create retention policy** - POST /api/retention-policies/
2. **List active policies** - GET /api/retention-policies/
3. **Update retention policy** - PUT /api/retention-policies/{id}
4. **Delete retention policy** - DELETE /api/retention-policies/{id}
5. **Validate policy parameters** - Invalid entity type, negative days, etc.

### Data Creation Tests (3 tests)

1. **Create old test resume** - Resume with created_date 60+ days ago
2. **Create recent test resume** - Resume with created_date within 30 days
3. **Verify timestamps** - Multiple resumes with different ages

### Cleanup Execution Tests (3 tests)

1. **Execute cleanup task** - Run retention cleanup
2. **Dry-run mode** - Test without actual deletion
3. **Statistics reporting** - Verify cleanup statistics by entity type

### Data Verification Tests (3 tests)

1. **Delete old resumes** - Verify resumes > 30 days deleted
2. **Preserve recent resumes** - Verify resumes < 30 days preserved
3. **Mixed age handling** - Test with multiple resumes of different ages

### Audit Trail Tests (2 tests)

1. **Log cleanup to audit trail** - Verify cleanup action logged
2. **Include policy details** - Verify policy details in audit log

### Mobile Responsive Tests (2 tests)

1. **Display on mobile** - UI loads correctly on mobile viewport
2. **Responsive layout** - 375px width viewport test

### End-to-End Test (1 test)

Complete workflow from policy creation → data creation → cleanup → verification

## Verification Checklist

### ✅ Retention Policy Creation
- [ ] Policy created via API
- [ ] Policy parameters validated
- [ ] Policy returned with ID
- [ ] Policy marked as active

### ✅ Test Data Creation
- [ ] Old resumes created (60+ days)
- [ ] Recent resumes created (< 30 days)
- [ ] Timestamps set correctly
- [ ] Both resume types returned IDs

### ✅ Cleanup Execution
- [ ] Dry-run mode works correctly
- [ ] Dry-run doesn't delete data
- [ ] Actual cleanup task executes
- [ ] Statistics returned correctly

### ✅ Data Deletion Verification
- [ ] Old resumes deleted (404 response)
- [ ] Recent resumes preserved (200 response)
- [ ] Mixed ages handled correctly
- [ ] Cascade deletion works (related records)

### ✅ Audit Trail Verification
- [ ] Cleanup logged to audit trail
- [ ] Action is "retention_cleanup"
- [ ] Policy details included
- [ ] Timestamps recorded
- [ ] Deletion count accurate

### ✅ Mobile Responsive
- [ ] UI loads on mobile viewport
- [ ] No console errors
- [ ] Responsive layout works
- [ ] Touch interactions work

## Troubleshooting

### Issue: Cleanup task doesn't execute

**Solution**:
1. Check Celery worker is running: `celery -A celery_app worker --loglevel=info`
2. Check task is registered: `celery -A celery_app inspect registered`
3. Check task queue: `celery -A celery_app inspect active`

### Issue: Old data not deleted

**Solution**:
1. Verify retention policy is active
2. Check retention_days value is correct
3. Verify resume created_at timestamp is old enough
4. Check entity_type matches (resumes, candidate_data, etc.)

### Issue: Recent data deleted incorrectly

**Solution**:
1. Verify created_at timestamp is recent
2. Check retention_days calculation
3. Review policy configuration
4. Check for multiple conflicting policies

### Issue: Audit logs not created

**Solution**:
1. Verify audit log table exists
2. Check RetentionService.delete_entity() is calling audit logger
3. Verify database connection for audit writes
4. Check for audit log write errors

### Issue: Tests fail with connection errors

**Solution**:
1. Verify backend API is running on port 8000
2. Check frontend is running on port 5173
3. Verify database is running and accessible
4. Check network connectivity

## Expected Output

### Successful Test Run

```
Running 19 tests using 1 worker

✓ Retention Policy Management (5)
  ✓ should create retention policy successfully
  ✓ should list active retention policies
  ✓ should update retention policy
  ✓ should delete retention policy
  ✓ should validate retention policy parameters

✓ Data Creation (3)
  ✓ should create old test resume (60+ days ago)
  ✓ should create recent test resume (within 30 days)
  ✓ should verify created resumes have correct timestamps

✓ Cleanup Execution (3)
  ✓ should execute retention cleanup task
  ✓ should run cleanup in dry-run mode
  ✓ should report cleanup statistics by entity type

✓ Data Verification (3)
  ✓ should delete old resumes exceeding retention period
  ✓ should preserve recent resumes within retention period
  ✓ should handle mixed age resumes correctly

✓ Audit Trail (2)
  ✓ should log retention cleanup to audit trail
  ✓ should include policy details in audit log

✓ Mobile Responsive (2)
  ✓ should display retention policies on mobile
  ✓ should be responsive on small screens

✓ Complete End-to-End (1)
  ✓ complete retention policy workflow

19 passed (12.3s)
```

## GDPR Requirements Verified

✅ **Storage Limitation** - Data automatically deleted after retention period
✅ **Data Minimization** - Only necessary data retained
✅ **Right to Erasure** - Automated cleanup supports right to be forgotten
✅ **Accountability** - Complete audit trail of cleanup operations
✅ **Transparency** - Retention policies documented and tracked
✅ **Data Protection by Design** - Automatic cleanup prevents data accumulation

## Next Steps

1. ✅ Run all retention policy flow tests
2. ✅ Verify automated cleanup works correctly
3. ✅ Review audit trail completeness
4. ✅ Test with different entity types (analytics, match results, etc.)
5. ✅ Update implementation plan: mark subtask-7-4 as completed
6. ✅ Proceed to subtask-7-5: Privacy by design verification
