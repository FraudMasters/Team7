# Duplicate Detection Verification Guide

This guide provides instructions for verifying that duplicate detection prevents re-importing the same resume.

## Overview

The duplicate detection service (`ImportService`) prevents importing the same resume multiple times using three detection methods:

1. **Priority 1: Exact match by external_id + job_board_id** (100% confidence)
2. **Priority 2: Exact match by candidate_email** (95% confidence)
3. **Priority 3: Fuzzy match by candidate_name + job_title** (70%+ confidence)

## Test Files

### 1. Integration Tests: `test_duplicate_detection.py`

Comprehensive test suite covering all duplicate detection scenarios.

**Location:** `backend/tests/integration/test_duplicate_detection.py`

**Test Classes:**
- `TestDuplicateDetectionByExternalId` - Tests external ID detection
- `TestDuplicateDetectionByEmail` - Tests email-based detection
- `TestDuplicateDetectionByNameAndTitle` - Tests fuzzy name matching
- `TestDuplicateDetectionPriority` - Tests priority order
- `TestEndToEndDuplicatePrevention` - Tests complete flow with import logs
- `TestImportServiceErrorHandling` - Tests error handling

**Running the tests:**

```bash
cd backend
pytest tests/integration/test_duplicate_detection.py -v
```

**Expected Output:**
```
tests/integration/test_duplicate_detection.py::TestDuplicateDetectionByExternalId::test_duplicate_detected_by_external_id PASSED
tests/integration/test_duplicate_detection.py::TestDuplicateDetectionByEmail::test_duplicate_detected_by_email PASSED
...
================= 20 passed in 5.32s =================
```

### 2. Manual Test Script: `manual_duplicate_test.py`

Standalone Python script for manual verification without pytest.

**Location:** `backend/tests/integration/manual_duplicate_test.py`

**Running the script:**

```bash
cd backend
python tests/integration/manual_duplicate_test.py
```

**Expected Output:**
```
====================================================================
  DUPLICATE DETECTION MANUAL TEST
====================================================================

====================================================================
  Setting Up Test Data
====================================================================
✅ PASS - Created job board
     ID: 123e4567-e89b-12d3-a456-426614174000
✅ PASS - Created resume
     ID: 987fcdeb-51a2-43f1-a456-426614174000
✅ PASS - Created imported resume
     ID: 456789ab-cdef-1234-5678-90abcdef1234

====================================================================
  Test 1: Duplicate Detection by External ID
====================================================================
✅ PASS - Duplicate detected by external_id + job_board_id
     Type: external_id, Confidence: 1.0
✅ PASS - No duplicate with different external_id
     Correctly identified as unique resume

...
====================================================================
  Test Summary
====================================================================
✅ All tests completed!
```

## Verification Steps

### Step 1: Verify Duplicate Detection by External ID

**Scenario:** Import a resume, then attempt to import the same resume (same external_id) again.

**Expected Behavior:**
- First import: No duplicate detected → Resume imported successfully
- Second import: Duplicate detected → Import skipped with log

**Test with Python:**
```python
from services.import_service import ImportService

# First check - no duplicate
result1 = await import_service.check_duplicate(
    job_board_id="board-uuid",
    external_id="ext-12345"
)
assert result1.is_duplicate is False

# After creating imported resume, second check - duplicate found
result2 = await import_service.check_duplicate(
    job_board_id="board-uuid",
    external_id="ext-12345"  # Same external ID
)
assert result2.is_duplicate is True
assert result2.duplicate_type == "external_id"
assert result2.confidence_score == 1.0
```

**Database Verification:**
```sql
-- Check for existing import with same external_id and job board
SELECT * FROM imported_resumes
WHERE job_board_id = 'board-uuid'
  AND external_id = 'ext-12345'
  AND is_active = TRUE;
```

### Step 2: Verify Duplicate Detection by Email

**Scenario:** Import a resume from one job board, then attempt to import the same candidate (same email) from another job board.

**Expected Behavior:**
- Duplicate detected by email
- Confidence score: 0.95
- Duplicate type: "email"

**Test with Python:**
```python
# Check with email only
result = await import_service.check_duplicate(
    job_board_id="different-board-uuid",
    candidate_email="john.doe@example.com"  # Case-insensitive
)
assert result.is_duplicate is True
assert result.duplicate_type == "email"
assert result.confidence_score == 0.95
```

### Step 3: Verify Import Log Shows 'skipped - duplicate'

**Scenario:** After duplicate detection, create an import log showing the resume was skipped.

**Expected Behavior:**
- ImportLog.status = SKIPPED
- ImportLog.error_message = "skipped - duplicate"
- ImportLog.error_details contains duplicate information

**Test with Python:**
```python
from models import ImportLog, ImportJobStatus

# After duplicate check
if duplicate_result.is_duplicate:
    import_log = ImportLog(
        job_board_id=job_board_id,
        job_board_name="Indeed",
        status=ImportJobStatus.SKIPPED,
        records_processed=1,
        records_succeeded=0,
        records_failed=0,
        error_message="skipped - duplicate",
        error_details={
            "duplicate_type": duplicate_result.duplicate_type,
            "existing_resume_id": duplicate_result.existing_resume_id,
            "existing_import_id": duplicate_result.existing_import_id,
            "confidence_score": duplicate_result.confidence_score,
        },
    )
    db.add(import_log)
    await db.commit()
```

**Database Verification:**
```sql
-- Query import logs for skipped duplicates
SELECT
    id,
    job_board_name,
    status,
    error_message,
    error_details->>'duplicate_type' as duplicate_type,
    error_details->>'confidence_score' as confidence,
    created_at
FROM import_logs
WHERE status = 'SKIPPED'
  AND error_message = 'skipped - duplicate'
ORDER BY created_at DESC
LIMIT 10;
```

### Step 4: Verify Multiple Import Attempts

**Scenario:** Attempt to import the same resume 3 times.

**Expected Behavior:**
- 3 separate ImportLog entries with SKIPPED status
- Each log has retry attempt metadata
- Original ImportedResume is not modified

**Database Verification:**
```sql
-- Check multiple skip attempts for same resume
SELECT
    il.id,
    il.status,
    il.error_message,
    il.import_metadata->>'retry_attempt' as attempt,
    il.created_at
FROM import_logs il
WHERE il.job_board_id = 'board-uuid'
  AND il.import_metadata->>'external_id' = 'ext-12345'
ORDER BY il.created_at;

-- Expected: 3 rows with attempt numbers 1, 2, 3
```

## End-to-End Verification

### Complete Import Flow with Duplicate Prevention

1. **First Import:**
```sql
-- Create ImportedResume record
INSERT INTO imported_resumes (
    resume_id,
    job_board_id,
    external_id,
    import_status,
    candidate_email,
    is_active
) VALUES (
    'resume-uuid',
    'board-uuid',
    'ext-12345',
    'COMPLETED',
    'john@example.com',
    TRUE
);

-- Create success log
INSERT INTO import_logs (
    job_board_id,
    status,
    records_processed,
    records_succeeded
) VALUES (
    'board-uuid',
    'SUCCESS',
    1,
    1
);
```

2. **Second Import (Duplicate Detected):**
```python
# Check for duplicate
result = await import_service.check_duplicate(
    job_board_id='board-uuid',
    external_id='ext-12345'
)
# Result: is_duplicate=True, duplicate_type='external_id'

# Create skipped log
import_log = ImportLog(
    job_board_id='board-uuid',
    status=ImportJobStatus.SKIPPED,
    error_message='skipped - duplicate',
    error_details={
        'duplicate_type': 'external_id',
        'existing_resume_id': 'resume-uuid',
        'confidence_score': 1.0
    }
)
```

3. **Verify Database State:**
```sql
-- Should have 2 logs (1 SUCCESS, 1 SKIPPED)
-- Should have 1 ImportedResume (not duplicated)
SELECT COUNT(*) FROM import_logs WHERE job_board_id = 'board-uuid';
-- Result: 2

SELECT COUNT(*) FROM imported_resumes WHERE external_id = 'ext-12345';
-- Result: 1 (no duplicate created)
```

## Common Issues and Solutions

### Issue 1: Duplicate Not Detected

**Symptom:** Same resume imported multiple times.

**Possible Causes:**
- `is_active` flag set to FALSE on existing import
- Different `external_id` values (job board issue)
- Case sensitivity issues with email

**Solutions:**
```sql
-- Check if existing import is active
SELECT is_active FROM imported_resumes
WHERE job_board_id = 'board-uuid' AND external_id = 'ext-12345';

-- Update if needed
UPDATE imported_resumes SET is_active = TRUE WHERE id = 'import-id';
```

### Issue 2: False Positives

**Symptom:** Different candidates flagged as duplicates.

**Possible Causes:**
- Email addresses are the same (shared accounts)
- Similar names with common job titles

**Solutions:**
- Use external_id for more reliable matching
- Adjust confidence threshold in `_check_by_name_and_title`
- Add additional matching criteria (phone number, etc.)

### Issue 3: Import Logs Not Created

**Symptom:** No SKIPPED logs when duplicates are detected.

**Possible Causes:**
- Import task not calling `check_duplicate`
- ImportLog creation code missing in import flow
- Database transaction not committed

**Solutions:**
```python
# Ensure import flow creates logs when duplicates detected
duplicate_result = await import_service.check_duplicate(...)
if duplicate_result.is_duplicate:
    import_log = ImportLog(
        status=ImportJobStatus.SKIPPED,
        error_message="skipped - duplicate",
        ...
    )
    db.add(import_log)
    await db.commit()  # Don't forget to commit!
```

## Verification Checklist

- [ ] Run `test_duplicate_detection.py` - all tests pass
- [ ] Run `manual_duplicate_test.py` - all tests pass
- [ ] Verify duplicate detection by external_id works
- [ ] Verify duplicate detection by email works
- [ ] Verify duplicate detection by name/title works
- [ ] Verify import logs show 'skipped - duplicate'
- [ ] Verify multiple import attempts create multiple logs
- [ ] Verify no duplicate ImportedResume records created
- [ ] Test with real job board integration (if available)
- [ ] Verify cleanup test data works

## Next Steps

After verification:

1. **Integrate with poll_job_board task:**
   - Add `check_duplicate` call in `import_tasks.py`
   - Create SKIPPED logs when duplicates detected
   - Update task results to include skipped count

2. **Add frontend UI feedback:**
   - Show skipped count in import logs table
   - Display reason for skipped imports
   - Allow users to view existing duplicate resume

3. **Monitor production:**
   - Track duplicate detection rates
   - Monitor false positive/negative rates
   - Adjust confidence thresholds as needed

## Additional Resources

- ImportService implementation: `backend/services/import_service.py`
- ImportedResume model: `backend/models/imported_resume.py`
- ImportLog model: `backend/models/import_log.py`
- Import tasks: `backend/tasks/import_tasks.py`
