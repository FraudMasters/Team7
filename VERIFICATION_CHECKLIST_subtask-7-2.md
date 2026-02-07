# Verification Checklist - Subtask 7-2: Data Deletion Request Flow

## Test Environment

- [ ] Backend API running on http://localhost:8000
- [ ] Frontend dev server running on http://localhost:5173
- [ ] PostgreSQL database running
- [ ] GDPR database migrations applied
- [ ] Test data available (resumes with PII)
- [ ] Playwright browsers installed

## Automated Tests

### Test Execution

- [ ] Run all tests: `./frontend/scripts/test-gdpr-data-deletion-flow.sh`
- [ ] All 6 active tests pass
- [ ] No console errors during tests
- [ ] No backend errors during tests
- [ ] Test report generated successfully

### Frontend UI Tests (6 tests)

- [ ] Test: Display deletion form on privacy settings page
- [ ] Test: Open data deletion request dialog
- [ ] Test: Display warning messages about permanent deletion
- [ ] Test: Require reason before submitting deletion request
- [ ] Test: Show confirmation dialog before submitting
- [ ] Test: Submit deletion request after confirmation

### API Integration Tests

- [ ] Test: Send deletion request to backend API
- [ ] Test: Handle API errors gracefully (skipped - needs mocking)

### Mobile Responsive Tests (2 tests)

- [ ] Test: Display deletion form correctly on mobile
- [ ] Test: Allow submitting deletion request on mobile

### Complete End-to-End Test (1 test)

- [ ] Test: Complete deletion flow from frontend to API
- [ ] All 11 steps of the flow complete successfully

## Manual Verification Steps

### Step 1: Create Test Candidate with PII Data

- [ ] Test resume created with full PII data
- [ ] Resume exists in `resumes` table
- [ ] Parsed resume exists in `parsed_resumes` table
- [ ] Hiring stages exist in `hiring_stages` table
- [ ] Notes exist in `candidate_notes` table
- [ ] Tags exist in `candidate_tags` table
- [ ] Activities exist in `candidate_activities` table
- [ ] All data properly linked via foreign keys

### Step 2: Submit Data Deletion Request via Frontend

- [ ] Navigate to /settings/privacy successfully
- [ ] Privacy settings page loads without errors
- [ ] "Delete Account" card is visible
- [ ] Clicking card opens deletion request dialog
- [ ] Dialog displays warning alert prominently
- [ ] All 7 data categories are listed:
  - [ ] Resume and CV files
  - [ ] Personal information (name, email, phone, address)
  - [ ] Hiring stage history
  - [ ] Notes and comments
  - [ ] Tags and categorizations
  - [ ] Activity history
  - [ ] All associated records
- [ ] Reason input field is present
- [ ] Submit button is disabled initially
- [ ] Submit button enables when reason is entered
- [ ] Clicking submit shows confirmation dialog
- [ ] Confirmation dialog warns about permanent action
- [ ] Confirmation button is present
- [ ] Cancel/back button is present
- [ ] Clicking confirm submits the request
- [ ] Loading indicator shows during submission
- [ ] Success message appears after submission
- [ ] Dialog closes after success
- [ ] No errors in browser console

### Step 3: Verify Request Created in Database

- [ ] Query `data_deletion_requests` table
- [ ] Deletion request record exists
- [ ] `requester_email` field is populated
- [ ] `requester_type` = 'candidate'
- [ ] `status` = 'pending'
- [ ] `notes` field contains resume_id
- [ ] `notes` field contains reason
- [ ] `created_at` timestamp is recent (within last minute)
- [ ] `verification_token` is generated (32-character URL-safe string)
- [ ] `verified_at` is NULL (not yet verified)
- [ ] `processed_at` is NULL (not yet processed)
- [ ] `rejection_reason` is NULL
- [ ] Resume data still exists (not deleted yet)

### Step 4: Process Deletion Request via API

**Choose one method:**

- [ ] **Option A**: Call processing API endpoint (if implemented)
- [ ] **Option B**: Manually update status and delete data (for testing)

**Processing Steps:**
- [ ] Update status to 'verified'
- [ ] Set `verified_at` timestamp
- [ ] Update status to 'processing'
- [ ] Set `processed_at` timestamp
- [ ] Delete related data in correct order:
  - [ ] Delete from `candidate_activities`
  - [ ] Delete from `candidate_tags`
  - [ ] Delete from `candidate_notes`
  - [ ] Delete from `hiring_stages`
  - [ ] Delete from `parsed_resumes`
  - [ ] Delete from `resumes`
- [ ] Update status to 'completed'

### Step 5: Verify All Candidate Data Deleted from Database

- [ ] Resume deleted: `SELECT * FROM resumes WHERE id = 'test-id'` returns 0 rows
- [ ] Parsed resume deleted: `SELECT * FROM parsed_resumes WHERE resume_id = 'test-id'` returns 0 rows
- [ ] Hiring stages deleted: `SELECT COUNT(*) FROM hiring_stages WHERE resume_id = 'test-id'` = 0
- [ ] Notes deleted: `SELECT COUNT(*) FROM candidate_notes WHERE resume_id = 'test-id'` = 0
- [ ] Tags deleted: `SELECT COUNT(*) FROM candidate_tags WHERE resume_id = 'test-id'` = 0
- [ ] Activities deleted: `SELECT COUNT(*) FROM candidate_activities WHERE resume_id = 'test-id'` = 0
- [ ] No orphaned records remain
- [ ] Foreign key constraints satisfied
- [ ] Cascade deletion worked correctly
- [ ] All PII completely removed from database

### Step 6: Verify Audit Log Records Deletion

- [ ] Query `audit_logs` table for deletion events
- [ ] Audit log entry exists for deletion request creation
- [ ] `action_type` = 'resume_deleted'
- [ ] `entity_type` = 'data_deletion_request'
- [ ] `entity_id` matches deletion request ID
- [ ] `action_data` JSON contains:
  - [ ] `resume_id`: the deleted resume ID
  - [ ] `reason`: deletion reason text
  - [ ] `requester_email`: email from request
- [ ] `ip_address` is captured
- [ ] `user_agent` is captured
- [ ] `created_at` timestamp matches request creation
- [ ] Additional audit logs for data deletion (if implemented)

### Step 7: Verify Deletion Status Visible in Frontend

- [ ] Navigate to /settings/privacy
- [ ] Deletion request status is visible (if implemented)
- [ ] Status shows correct value (pending/processing/completed)
- [ ] Request timestamp is visible
- [ ] Request details accessible (if implemented)
- [ ] **Alternative**: Check status via API:
  - [ ] GET `/api/data-deletion/request/{request_id}` returns correct status
  - [ ] Response contains all expected fields
  - [ ] `id` matches deletion request ID
  - [ ] `status` matches database status
  - [ ] `requester_email` matches
  - [ ] `created_at` timestamp correct
  - [ ] `notes` contain resume_id and reason

## GDPR Compliance Verification

### Right to Erasure (Article 17)

- [ ] Users can request deletion of their data
- [ ] Request mechanism is easily accessible
- [ ] Clear information about what will be deleted
- [ ] Confirmation prevents accidental requests
- [ ] Data is actually deleted when processed
- [ ] All related PII is deleted
- [ ] No unnecessary data retention
- [ ] Deletion happens within reasonable timeframe

### Transparency and Accountability

- [ ] Clear warnings about permanent deletion
- [ ] Complete list of data to be deleted
- [ ] Reason field for accountability
- [ ] Audit trail of all deletion actions
- [ ] IP address and user agent tracking
- [ ] Timestamps for all actions
- [ ] Request status tracking

### Data Minimization

- [ ] All related data deleted (cascade)
- [ ] No orphaned records
- [ ] No partial deletion
- [ ] Complete erasure of PII

## Error Handling Verification

### Invalid Input

- [ ] Invalid resume_id UUID shows validation error
- [ ] Empty reason shows validation error
- [ ] No request created for invalid input
- [ ] Error messages are user-friendly

### Not Found

- [ ] Non-existent resume_id shows 404 error
- [ ] Clear error message displayed
- [ ] No request created in database
- [ ] Graceful error handling

### Backend Errors

- [ ] API timeout shows timeout message
- [ ] Database errors show user-friendly message
- [ ] Network errors handled gracefully
- [ ] Retry option available
- [ ] Form data preserved on error

## Mobile Responsive Verification

- [ ] Deletion form renders correctly on mobile
- [ ] All UI elements accessible
- [ ] Touch interactions work smoothly
- [ ] No horizontal scrolling
- [ ] Text is readable
- [ ] Buttons are easily tappable
- [ ] Dialog fits on small screens
- [ ] Complete flow works on mobile

## Code Quality Verification

- [ ] No console errors during tests
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Code follows existing patterns
- [ ] Proper error handling in place
- [ ] No debug console.log statements
- [ ] No hardcoded values (except test IDs)
- [ ] Proper type definitions
- [ ] Component follows React best practices

## Documentation Verification

- [ ] Test documentation created (TEST_GDPR_DATA_DELETION_FLOW.md)
- [ ] Manual testing steps documented
- [ ] API endpoints documented
- [ ] Database schema documented
- [ ] GDPR compliance notes included
- [ ] Troubleshooting guide included
- [ ] Test runner script created and executable

## Integration Verification

### Frontend Integration

- [ ] DataDeletionRequest component works correctly
- [ ] PrivacySettingsPage integrates component
- [ ] Navigation works smoothly
- [ ] State management correct
- [ ] Error handling works
- [ ] Success feedback displayed

### Backend Integration

- [ ] API endpoint `/api/data-deletion/request` works
- [ ] Database operations successful
- [ ] Audit logging works
- [ ] Error responses correct
- [ ] Status codes correct (201, 404, 422, 500)

### API Client Integration

- [ ] gdprClient.createDataDeletionRequest() works
- [ ] Request format correct
- [ ] Response handling correct
- [ ] Error transformation works
- [ ] Type definitions match

## Performance Verification

- [ ] Dialog opens quickly (< 500ms)
- [ ] API response time reasonable (< 2s)
- [ ] No memory leaks during flow
- [ ] No unnecessary re-renders
- [ ] Smooth animations
- [ ] Loading indicators display properly

## Security Verification

- [ ] No PII exposed in console logs
- [ ] No PII in error messages
- [ ] Proper authentication checks (if applicable)
- [ ] Authorization checks (if applicable)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper input sanitization)
- [ ] CSRF protection (if applicable)

## Final Checklist

Before marking subtask-7-2 as complete:

- [ ] All automated tests pass (6/6 active tests)
- [ ] Manual verification steps completed
- [ ] Database deletion verified
- [ ] Audit logs verified
- [ ] Frontend status display verified
- [ ] GDPR compliance confirmed
- [ ] Error handling tested
- [ ] Mobile responsive verified
- [ ] Documentation complete
- [ ] Code quality verified
- [ ] Security verified
- [ ] No known bugs or issues
- [ ] Implementation plan updated

## Sign-off

**Tester**: ______________________

**Date**: ______________________

**Results**:
- [ ] PASSED - All verification steps completed successfully
- [ ] PASSED WITH NOTES - Minor issues documented, not blocking
- [ ] FAILED - Critical issues found, needs fixes

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Approval**: ______________________
