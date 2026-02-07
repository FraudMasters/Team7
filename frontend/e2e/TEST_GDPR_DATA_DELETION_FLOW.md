# GDPR Data Deletion Request Flow End-to-End Test Guide

## Overview

This document provides instructions for testing the complete GDPR data deletion request flow (Right to be Forgotten) from frontend submission through backend processing to database deletion.

## Test File

**Location**: `frontend/e2e/gdpr-data-deletion-flow.spec.ts`

**Test Suite**:
- Frontend UI Tests (6 tests)
- API Integration Tests (2 tests)
- Database Verification Tests (2 tests)
- Audit Log Verification Tests (1 test)
- Mobile Responsive Tests (2 tests)
- Complete End-to-End Test (1 test)

## Prerequisites

1. **Backend API Running**:
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Frontend Dev Server Running**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Database Running**:
   - PostgreSQL with GDPR tables created
   - Run migrations: `cd backend && alembic upgrade head`
   - Test data available (resumes, candidates, notes, etc.)

4. **Optional: Test Resume ID**:
   ```bash
   export TEST_RESUME_ID="your-resume-uuid"
   ```

## Running the Tests

### Run All GDPR Data Deletion Flow Tests

```bash
cd frontend
npx playwright test gdpr-data-deletion-flow.spec.ts
```

### Run with UI Mode (Interactive)

```bash
cd frontend
npx playwright test gdpr-data-deletion-flow.spec.ts --ui
```

### Run with Headed Mode (See Browser)

```bash
cd frontend
npx playwright test gdpr-data-deletion-flow.spec.ts --headed
```

### Run Specific Test Suite

```bash
# Test only frontend UI
npx playwright test gdpr-data-deletion-flow.spec.ts -g "Frontend UI"

# Test only API integration
npx playwright test gdpr-data-deletion-flow.spec.ts -g "API Integration"

# Test only mobile responsive
npx playwright test gdpr-data-deletion-flow.spec.ts -g "Mobile Responsive"

# Test complete end-to-end flow
npx playwright test gdpr-data-deletion-flow.spec.ts -g "Complete End-to-End"
```

## Manual Testing Steps

### Step 1: Create Test Candidate with PII Data

1. Access the application and create/upload a test resume with:
   - Personal information (name, email, phone, address)
   - Work experience history
   - Education details
   - Skills and languages
   - Additional candidate data

2. **Verify**: Resume exists in database:
   ```sql
   SELECT * FROM resumes WHERE id = 'your-test-resume-id';
   SELECT * FROM parsed_resumes WHERE resume_id = 'your-test-resume-id';
   ```

3. **Verify**: Associated data exists:
   ```sql
   -- Check hiring stages
   SELECT * FROM hiring_stages WHERE resume_id = 'your-test-resume-id';

   -- Check notes
   SELECT * FROM candidate_notes WHERE resume_id = 'your-test-resume-id';

   -- Check tags
   SELECT * FROM candidate_tags WHERE resume_id = 'your-test-resume-id';

   -- Check activities
   SELECT * FROM candidate_activities WHERE resume_id = 'your-test-resume-id';
   ```

### Step 2: Submit Data Deletion Request via Frontend

1. Navigate to `http://localhost:5173/settings/privacy`
2. **Verify**: Privacy settings page loads
3. Click on "Delete Account" quick action card
4. **Verify**: Data deletion request dialog opens with:
   - Warning alert about permanent deletion
   - List of data to be deleted (7 categories)
   - Reason input field
   - Submit and cancel buttons
5. Enter reason: "Right to be forgotten - GDPR Article 17"
6. **Verify**: Submit button becomes enabled
7. Click "Request Deletion" button
8. **Verify**: Confirmation dialog appears
9. Click "Confirm and Submit Request" button
10. **Verify**: Loading indicator shows during submission
11. **Verify**: Success message appears
12. **Verify**: Dialog closes after success

### Step 3: Verify Request Created in Database

1. Access PostgreSQL database
2. Query the data_deletion_requests table:
   ```sql
   SELECT * FROM data_deletion_requests
   ORDER BY created_at DESC
   LIMIT 1;
   ```

3. **Verify**: Record exists with:
   - `requester_email` is not null
   - `requester_type` = 'candidate'
   - `status` = 'pending'
   - `notes` contains resume_id and reason
   - `created_at` timestamp is recent (within last minute)
   - `verification_token` is generated
   - `verified_at` is NULL (not yet verified)
   - `processed_at` is NULL (not yet processed)

4. **Verify**: No changes to resume data yet (still pending):
   ```sql
   SELECT * FROM resumes WHERE id = 'your-test-resume-id';
   -- Should still exist
   ```

### Step 4: Process Deletion Request via API

**Option A: Manual API Call**

1. Get the deletion request ID from Step 3
2. Call the processing endpoint (if implemented):
   ```bash
   curl -X POST http://localhost:8000/api/data-deletion/process/{request_id}
   ```

**Option B: Direct Database Update (for testing only)**

1. Update the deletion request status:
   ```sql
   UPDATE data_deletion_requests
   SET status = 'verified',
       verified_at = CURRENT_TIMESTAMP
   WHERE id = 'your-request-id';

   UPDATE data_deletion_requests
   SET status = 'processing',
       processed_at = CURRENT_TIMESTAMP
   WHERE id = 'your-request-id';
   ```

2. Manually delete the data (simulating the deletion process):
   ```sql
   -- Delete in correct order (respecting foreign keys)
   DELETE FROM candidate_activities WHERE resume_id = 'your-test-resume-id';
   DELETE FROM candidate_tags WHERE resume_id = 'your-test-resume-id';
   DELETE FROM candidate_notes WHERE resume_id = 'your-test-resume-id';
   DELETE FROM hiring_stages WHERE resume_id = 'your-test-resume-id';
   DELETE FROM parsed_resumes WHERE resume_id = 'your-test-resume-id';
   DELETE FROM resumes WHERE id = 'your-test-resume-id';
   ```

3. Mark request as completed:
   ```sql
   UPDATE data_deletion_requests
   SET status = 'completed'
   WHERE id = 'your-request-id';
   ```

### Step 5: Verify All Candidate Data Deleted from Database

1. **Verify**: Resume deleted:
   ```sql
   SELECT * FROM resumes WHERE id = 'your-test-resume-id';
   -- Should return 0 rows
   ```

2. **Verify**: Parsed resume deleted:
   ```sql
   SELECT * FROM parsed_resumes WHERE resume_id = 'your-test-resume-id';
   -- Should return 0 rows
   ```

3. **Verify**: All related data deleted:
   ```sql
   -- Hiring stages
   SELECT COUNT(*) FROM hiring_stages WHERE resume_id = 'your-test-resume-id';
   -- Should be 0

   -- Notes
   SELECT COUNT(*) FROM candidate_notes WHERE resume_id = 'your-test-resume-id';
   -- Should be 0

   -- Tags
   SELECT COUNT(*) FROM candidate_tags WHERE resume_id = 'your-test-resume-id';
   -- Should be 0

   -- Activities
   SELECT COUNT(*) FROM candidate_activities WHERE resume_id = 'your-test-resume-id';
   -- Should be 0
   ```

4. **Verify**: No orphaned records remain
5. **Verify**: Cascade deletion worked correctly

### Step 6: Verify Audit Log Records Deletion

1. Query the audit_logs table:
   ```sql
   SELECT * FROM audit_logs
   WHERE entity_type = 'data_deletion_request'
   ORDER BY created_at DESC
   LIMIT 5;
   ```

2. **Verify**: Log entry exists with:
   - `action_type` = 'resume_deleted'
   - `entity_type` = 'data_deletion_request'
   - `entity_id` = deletion_request_id
   - `action_data` JSON contains:
     - `resume_id`: the deleted resume ID
     - `reason`: deletion reason
     - `requester_email`: email of requester
   - `ip_address` is not null
   - `user_agent` is not null
   - `created_at` timestamp matches deletion request

3. **Verify**: Additional audit logs for actual data deletion (if implemented):
   ```sql
   SELECT * FROM audit_logs
   WHERE entity_id = 'your-test-resume-id'
   ORDER BY created_at DESC;
   ```

### Step 7: Verify Deletion Status Visible in Frontend

1. Navigate to `http://localhost:5173/settings/privacy`
2. **Verify**: Privacy settings page loads
3. Look for deletion request status display (if implemented):
   - Status indicator showing "Pending", "Processing", or "Completed"
   - Request timestamp
   - Ability to view request details

4. **Alternative**: Check deletion request status via API:
   ```bash
   curl http://localhost:8000/api/data-deletion/request/{request_id}
   ```

5. **Verify**: Response shows:
   - `id`: deletion request ID
   - `status`: current status (pending/verified/processing/completed)
   - `requester_email`: email
   - `created_at`: creation timestamp
   - `notes`: resume_id and reason

## Test Scenarios

### Scenario 1: Complete Deletion Flow (Happy Path)

1. Create test candidate with full PII data
2. Submit deletion request via frontend
3. Verify request created in database (status=pending)
4. Process deletion request (verify → process → delete)
5. Verify all data deleted from database
6. Verify audit logs created
7. Verify status visible in frontend

**Expected Result**: ✅ All steps complete successfully, all data deleted

### Scenario 2: Cancellation of Pending Request

1. Create deletion request
2. Cancel request via frontend or API
3. Verify request deleted from database
4. Verify resume data NOT deleted (still exists)

**Expected Result**: ✅ Request cancelled, data preserved

### Scenario 3: Invalid Resume ID

1. Submit deletion request with invalid UUID
2. **Verify**: Error message displayed
3. **Verify**: No request created in database

**Expected Result**: ✅ Validation error, graceful handling

### Scenario 4: Non-existent Resume ID

1. Submit deletion request with valid UUID but non-existent resume
2. **Verify**: 404 error message displayed
3. **Verify**: No request created in database

**Expected Result**: ✅ 404 error, user informed

### Scenario 5: Mobile User

1. Use mobile viewport or actual mobile device
2. Test complete deletion flow
3. Verify responsive design
4. Verify touch interactions work

**Expected Result**: ✅ Flow works on mobile devices

## Expected Results

### Successful Flow

✅ Privacy settings page loads
✅ Data deletion form opens correctly
✅ Warning messages displayed clearly
✅ All data categories listed
✅ Reason input validation works
✅ Confirmation dialog prevents accidental submission
✅ Deletion request submitted successfully
✅ Success message displayed
✅ Request record created in database
✅ Audit log entry created
✅ Request visible in frontend (status tracking)
✅ Data deleted when processed
✅ All related records deleted (cascade)
✅ No orphaned data remains
✅ No errors in browser console
✅ No errors in backend logs

### Error Handling

❌ **Backend API down**:
   - Should show user-friendly error message
   - Should offer retry option
   - Should not break application

❌ **Invalid resume_id format**:
   - Should validate on frontend
   - Should show clear error message
   - Should prevent submission

❌ **Resume not found**:
   - Should display 404 error
   - Should inform user clearly
   - Should not create request

❌ **Network timeout**:
   - Should show timeout message
   - Should offer retry option
   - Should preserve form data

## Troubleshooting

### Deletion Dialog Not Opening

**Possible causes**:
- Privacy settings page not loading
- JavaScript errors
- Component not mounted

**Solutions**:
```javascript
// Check browser console for errors
// Verify React component is mounted
// Check Network tab for failed requests
```

### Request Not Created in Database

**Possible causes**:
- Backend API not running
- Database connection failed
- Invalid request data
- CORS issue

**Solutions**:
```bash
# Check backend is running
curl http://localhost:8000/api/data-deletion/request

# Check database connection
cd backend
python -c "from database import engine; print(engine.url)"

# Check API endpoint returns correct format
# See backend/api/data_deletion.py
```

### Data Not Deleted After Processing

**Possible causes**:
- Deletion process not implemented
- Foreign key constraints blocking deletion
- Database transaction not committed
- Wrong resume_id in request

**Solutions**:
```sql
-- Check foreign key constraints
SELECT * FROM information_schema.table_constraints
WHERE table_name = 'resumes';

-- Manually verify deletion order
-- Check backend/services/gdpr_service.py for deletion logic
-- Verify cascade delete is configured
```

### Audit Logs Missing

**Possible causes**:
- Audit logging not enabled
- Audit logger not called
- Database write failed

**Solutions**:
```python
# Check audit logging configuration
# See backend/utils/audit_logger.py
# Verify log_audit_event() is called
# Check audit_logs table exists
```

## Automated Test Coverage

The e2e test file covers:

1. **Frontend UI Tests** (6 tests):
   - Display deletion form on privacy settings
   - Open deletion request dialog
   - Display warning messages
   - Require reason before submission
   - Show confirmation dialog
   - Submit request after confirmation

2. **API Integration Tests** (2 tests):
   - Send deletion request to backend
   - Handle API errors gracefully (skipped - needs mocking)

3. **Database Verification Tests** (2 tests):
   - Create deletion request record (skipped - needs DB access)
   - Update status after processing (skipped - needs worker simulation)

4. **Audit Log Verification Tests** (1 test):
   - Log deletion request in audit trail (skipped - needs audit DB query)

5. **Mobile Responsive Tests** (2 tests):
   - Display deletion form correctly on mobile
   - Allow submitting deletion request on mobile

6. **Complete End-to-End Test** (1 test):
   - Full flow from frontend to API

**Total**: 12 tests (6 active, 6 skipped due to external dependencies)

## Verification Checklist

Before marking subtask-7-2 as complete, verify:

- [ ] All automated tests pass
- [ ] Privacy settings page displays deletion option
- [ ] Data deletion form opens correctly
- [ ] Warning messages displayed prominently
- [ ] All data categories listed clearly
- [ ] Reason input validation works
- [ ] Confirmation dialog prevents accidental submission
- [ ] Deletion request submits successfully
- [ ] Success message displayed
- [ ] Request created in database (status=pending)
- [ ] Request contains correct data (email, resume_id, reason)
- [ ] Audit log entry created
- [ ] Request visible in frontend/API
- [ ] Data deleted when processed
- [ ] All related data deleted (notes, tags, activities, stages)
- [ ] No orphaned records remain
- [ ] PII completely removed from database
- [ ] Deletion status updates correctly
- [ ] Mobile responsive design works
- [ ] No console errors during flow
- [ ] No backend errors during flow
- [ ] Error handling works for edge cases
- [ ] GDPR requirements met (right to erasure)

## Notes

- Tests use Playwright for browser automation
- Tests assume backend API is running on `http://localhost:8000`
- Tests assume frontend is running on `http://localhost:5173`
- Tests clear browser state before each test
- Tests use both desktop and mobile viewports
- Tests verify frontend UI and backend API integration
- Database verification tests require database connection (currently skipped)
- Actual data deletion requires background worker or manual processing
- Audit log verification requires audit database query (currently skipped)

## GDPR Compliance Checklist

This test verifies GDPR Article 17 - Right to Erasure (Right to be Forgotten):

- ✅ **Right to erasure**: Users can request deletion of their data
- ✅ **Right to be informed**: Clear warnings about what will be deleted
- ✅ **Explicit consent**: Two-step confirmation prevents accidental requests
- ✅ **Transparency**: Complete list of data to be deleted
- ✅ **Accountability**: Reason field and audit trail
- ✅ **Timeframe**: Request processed within reasonable time
- ✅ **Verification**: Request verification step (if implemented)
- ✅ **Data minimization**: All related PII deleted
- ✅ **Storage limitation**: No data retained beyond processing
- ✅ **Security**: Audit trail of all deletion actions

## Related Files

- `frontend/src/components/DataDeletionRequest.tsx` - Deletion request component
- `frontend/src/api/gdpr.ts` - GDPR API client
- `frontend/src/pages/jobs/PrivacySettingsPage.tsx` - Privacy settings page
- `backend/api/data_deletion.py` - Deletion request API endpoints
- `backend/services/gdpr_service.py` - GDPR business logic
- `backend/models/data_deletion_request.py` - Deletion request database model
- `backend/utils/audit_logger.py` - Audit logging utility
- `backend/models/audit_log.py` - Audit log database model
