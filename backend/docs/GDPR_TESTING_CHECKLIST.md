# GDPR Testing Checklist

**Version:** 1.0
**Last Updated:** 2026-02-03
**Purpose:** Comprehensive testing procedures for GDPR compliance verification

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Consent Management Tests](#consent-management-tests)
3. [Right to Access Tests](#right-to-access-tests)
4. [Right to Rectification Tests](#right-to-rectification-tests)
5. [Right to Erasure Tests](#right-to-erasure-tests)
6. [Right to Restrict Processing Tests](#right-to-restrict-processing-tests)
7. [Right to Data Portability Tests](#right-to-data-portability-tests)
8. [Right to Object Tests](#right-to-object-tests)
9. [Automated Decision Making Tests](#automated-decision-making-tests)
10. [Data Retention Tests](#data-retention-tests)
11. [Security Testing](#security-testing)
12. [Audit Trail Testing](#audit-trail-testing)
13. [Performance Testing](#performance-testing)

---

## Testing Overview

### Testing Strategy

The GDPR compliance testing strategy covers **3 layers** of verification:

1. **Automated Tests (E2E):** Playwright browser automation
   - 68 E2E tests covering all GDPR features
   - Browser-based UI testing
   - API integration verification
   - Mobile responsive testing

2. **Manual Verification:** Human testing procedures
   - UI/UX validation
   - Legal text review
   - Edge case handling
   - Error message verification

3. **Security Audits:** Third-party security assessment
   - Penetration testing
   - Code review for PII handling
   - Infrastructure security scan
   - Compliance audit

---

### Test Environment Setup

**Prerequisites:**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -c "from database import engine; print('DB ready')"

# Frontend
cd frontend
npm install
npm run build

# Start services
# Terminal 1: Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Celery Worker
cd backend && celery -A celery_app worker --loglevel=info

# Terminal 4: Celery Beat (Scheduler)
cd backend && celery -A celery_app beat --loglevel=info
```

**Test Data:**
- Test resumes with realistic PII (synthetic data only)
- Test user accounts (candidate, recruiter, admin)
- Test organization with multiple users
- Sample job vacancies for matching

---

### Running Tests

**E2E Tests (Playwright):**
```bash
cd frontend

# Run all GDPR tests
npx playwright test e2e/gdpr-*

# Run specific test suite
npx playwright test e2e/gdpr-consent-flow.spec.ts
npx playwright test e2e/gdpr-data-deletion-flow.spec.ts
npx playwright test e2e/gdpr-data-export-flow.spec.ts
npx playwright test e2e/gdpr-retention-policy-flow.spec.ts

# Run with UI
npx playwright test e2e/gdpr-consent-flow.spec.ts --ui

# Run in debug mode
npx playwright test e2e/gdpr-consent-flow.spec.ts --debug

# Run headed (show browser)
npx playwright test e2e/gdpr-consent-flow.spec.ts --headed
```

**Manual Testing:**
```bash
# Use test scripts
cd frontend
bash scripts/test-gdpr-consent-flow.sh --ui
bash scripts/test-gdpr-data-deletion-flow.sh --ui
bash scripts/test-gdpr-data-export-flow.sh --ui
bash scripts/test-gdpr-retention-policy-flow.sh --ui
```

---

## Consent Management Tests

### Test Suite: Consent Flow

**File:** `frontend/e2e/gdpr-consent-flow.spec.ts`
**Total Tests:** 18
**Test Categories:** Cookie Banner, Privacy Settings, API Integration, Mobile, E2E

---

### Test 1.1: Cookie Banner Display

**Objective:** Verify GDPR-compliant cookie banner appears on first visit

**Steps:**
1. Open browser in incognito mode (clear cookies)
2. Navigate to `http://localhost:5173/`
3. Verify cookie banner is visible
4. Check banner elements:
   - Privacy policy link
   - Accept button
   - Reject button
   - Customize button
5. Verify banner is fixed at bottom
6. Verify page content is scrollable behind banner

**Expected Results:**
- ✅ Cookie banner displays on first visit
- ✅ All required buttons present
- ✅ Privacy policy link works
- ✅ Banner positioning is correct (bottom fixed)
- ✅ No console errors

**Verification Commands:**
```javascript
// Browser console
document.querySelector('[data-testid="cookie-banner"]').should.exist
document.querySelector('[data-testid="accept-cookies"]').should.exist
document.querySelector('[data-testid="customize-cookies"]').should.exist
```

**Database Verification:**
```sql
-- No consent should exist yet
SELECT COUNT(*) FROM consent_records WHERE user_id = 'test-user-id';
-- Expected: 0
```

---

### Test 1.2: Grant All Consents

**Objective:** Verify user can grant all consents via cookie banner

**Steps:**
1. Open cookie banner (first visit)
2. Click "Accept All" button
3. Verify banner disappears
4. Navigate to `/settings/privacy`
5. Open ConsentManager component
6. Verify all consent types show "Granted"

**Expected Results:**
- ✅ Banner accepts all consents
- ✅ Banner disappears after acceptance
- ✅ All 13 consent types granted
- ✅ Consent records created in database
- ✅ IP address and user agent captured

**API Verification:**
```bash
curl -X GET http://localhost:8000/api/consent/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.consents | length'
# Expected: 13

curl -X GET http://localhost:8000/api/consent/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.consents[] | select(.granted == true) | .consent_type'
# Expected: All 13 types listed
```

**Database Verification:**
```sql
SELECT consent_type, granted, ip_address, user_agent, created_at
FROM consent_records
WHERE user_id = 'test-user-id'
ORDER BY created_at DESC;
-- Expected: 13 records, all granted=true, IP/user_agent populated
```

---

### Test 1.3: Grant Partial Consents (Customize)

**Objective:** Verify granular consent control

**Steps:**
1. Open cookie banner (first visit)
2. Click "Customize" button
3. Verify customization dialog opens
4. Select only essential cookies:
   - ✅ Essential cookies
   - ❌ Analytics cookies
   - ❌ Marketing cookies
5. Click "Save Preferences"
6. Navigate to `/settings/privacy`
7. Verify consent state in ConsentManager

**Expected Results:**
- ✅ Customization dialog opens
- ✅ Consent categories displayed clearly
- ✅ Can individually toggle each category
- ✅ Only selected consents granted
- ✅ Unselected consents not granted

**Database Verification:**
```sql
SELECT consent_type, granted
FROM consent_records
WHERE user_id = 'test-user-id'
AND consent_type IN ('essential_cookies', 'analytics', 'marketing_cookies');
-- Expected:
-- essential_cookies: true
-- analytics: false
-- marketing_cookies: false
```

---

### Test 1.4: Reject All Consents

**Objective:** Verify user can reject all optional consents

**Steps:**
1. Open cookie banner (first visit)
2. Click "Reject All" button
3. Verify banner disappears
4. Navigate to `/settings/privacy`
5. Verify only essential consents granted

**Expected Results:**
- ✅ Essential consents granted (required for operation)
- ✅ All optional consents rejected
- ✅ Banner does not reappear on refresh
- ✅ Consent persists in localStorage

**Database Verification:**
```sql
SELECT consent_type, granted
FROM consent_records
WHERE user_id = 'test-user-id';
-- Expected: Only essential consents granted
```

---

### Test 1.5: Consent Persistence

**Objective:** Verify consent persists across sessions

**Steps:**
1. Grant consents (accept all)
2. Close browser
3. Reopen browser and navigate to app
4. Verify cookie banner does NOT appear
5. Navigate to `/settings/privacy`
6. Verify previous consents still active

**Expected Results:**
- ✅ Banner does not reappear
- ✅ Consents persisted in localStorage
- ✅ Consents persisted in database
- ✅ User not prompted again

**Browser Console:**
```javascript
// Check localStorage
localStorage.getItem('cookieConsent')
// Expected: {"hasConsented":true,"analytics":true,"marketing":true,...}
```

---

### Test 1.6: Withdraw Consent

**Objective:** Verify user can withdraw previously granted consent

**Steps:**
1. Grant all consents
2. Navigate to `/settings/privacy`
3. Open ConsentManager
4. Find "Analytics" consent
5. Toggle switch to OFF
6. Verify withdrawal confirmation dialog appears
7. Confirm withdrawal
8. Verify consent status changes to "Withdrawn"

**Expected Results:**
- ✅ ConsentManager shows current consent states
- ✅ Toggle switches work
- ✅ Withdrawal confirmation dialog appears
- ✅ Consent status updated to withdrawn
- ✅ `withdrawn_at` timestamp set
- ✅ Audit log entry created

**API Verification:**
```bash
curl -X POST http://localhost:8000/api/consent/withdraw \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consent_type": "analytics",
    "reason": "No longer want analytics tracking"
  }'
# Expected: 200 OK
```

**Database Verification:**
```sql
SELECT consent_type, granted, withdrawn_at, withdrawal_reason
FROM consent_records
WHERE user_id = 'test-user-id'
AND consent_type = 'analytics';
-- Expected: granted=false, withdrawn_at IS NOT NULL
```

**Audit Log Verification:**
```sql
SELECT action_type, target_id, action_data
FROM audit_logs
WHERE actor_id = 'test-user-id'
AND action_type = 'consent_withdrawn'
ORDER BY created_at DESC
LIMIT 1;
-- Expected: action_data contains consent_type and reason
```

---

### Test 1.7: Consent Version Tracking

**Objective:** Verify consent text and version are tracked

**Steps:**
1. Grant a consent (e.g., data_processing)
2. Query database for consent record
3. Verify `consent_text` field contains exact legal text
4. Verify `consent_version` field contains policy version

**Expected Results:**
- ✅ Consent text is stored verbatim
- ✅ Consent version tracked
- ✅ IP address captured
- ✅ User agent captured

**Database Verification:**
```sql
SELECT
    consent_type,
    consent_text,
    consent_version,
    ip_address,
    user_agent,
    created_at
FROM consent_records
WHERE user_id = 'test-user-id'
AND consent_type = 'data_processing';
-- Expected: All fields populated
```

---

### Test 1.8: Re-grant Withdrawn Consent

**Objective:** Verify user can re-grant previously withdrawn consent

**Steps:**
1. Withdraw a consent (e.g., analytics)
2. Navigate to `/settings/privacy`
3. Open ConsentManager
4. Find withdrawn consent
5. Toggle switch back to ON
6. Verify new consent record created
7. Verify old record still shows withdrawn

**Expected Results:**
- ✅ New consent record created
- ✅ New record has `granted=true`, `withdrawn_at=NULL`
- ✅ Old record preserved for audit trail
- ✅ Consent status shows "Granted"

**Database Verification:**
```sql
SELECT id, consent_type, granted, withdrawn_at, created_at
FROM consent_records
WHERE user_id = 'test-user-id'
AND consent_type = 'analytics'
ORDER BY created_at;
-- Expected: 2 records (1 withdrawn, 1 active)
```

---

### Test 1.9: Consent Required for Processing

**Objective:** Verify processing is blocked without required consent

**Steps:**
1. Create new user (no consents)
2. Withdraw `ai_analysis` consent
3. Attempt to analyze resume:
   ```bash
   POST /api/resumes/analyze
   ```
4. Verify request is rejected with 403 Forbidden
5. Verify error message mentions missing consent

**Expected Results:**
- ✅ API returns 403 Forbidden
- ✅ Error message: "AI analysis consent required"
- ✅ No processing occurs
- ✅ Audit log shows denied access

**API Verification:**
```bash
curl -X POST http://localhost:8000/api/resumes/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "test-resume-id"}'
# Expected: 403 Forbidden
# Expected: {"detail": "AI analysis consent required"}
```

---

### Test 1.10: Mobile Responsive Cookie Banner

**Objective:** Verify cookie banner works on mobile devices

**Steps:**
1. Set viewport to 375x667 (iPhone)
2. Navigate to app
3. Verify cookie banner displays correctly
4. Verify buttons are tappable
5. Verify text is readable
6. Test accepting and rejecting

**Expected Results:**
- ✅ Banner fits on mobile screen
- ✅ Buttons are tappable (minimum 44x44px)
- ✅ Text is readable (no horizontal scroll)
- ✅ Accept/reject work correctly

**Playwright Test:**
```typescript
test('cookie banner mobile responsive', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:5173/');
  await expect(page.locator('[data-testid="cookie-banner"]')).toBeVisible();
  await page.click('[data-testid="accept-cookies"]');
  await expect(page.locator('[data-testid="cookie-banner"]')).toBeHidden();
});
```

---

## Right to Access Tests

### Test Suite: Data Export (Right to Portability)

**File:** `frontend/e2e/gdpr-data-export-flow.spec.ts`
**Total Tests:** 19
**Test Categories:** Frontend UI, API Integration, File Download, Mobile, E2E

---

### Test 2.1: JSON Data Export

**Objective:** Verify user can export all personal data as JSON

**Steps:**
1. Create test candidate with full data:
   - Resume uploaded
   - Parsed resume (all fields)
   - Hiring stages
   - Notes and tags
   - Activities
   - Consent records
2. Navigate to `/settings/privacy`
3. Click "Export Data" quick action
4. Select "JSON" format
5. Click "Export"
6. Wait for download to complete
7. Open downloaded JSON file
8. Verify structure and completeness

**Expected Results:**
- ✅ Export dialog opens
- ✅ JSON format option available
- ✅ Export starts immediately
- ✅ Progress indicator shows
- ✅ File downloads automatically
- ✅ JSON is valid (parseable)
- ✅ All PII fields included
- ✅ All related records included

**API Verification:**
```bash
curl -X GET "http://localhost:8000/api/data-export/resume/$RESUME_ID?format=json" \
  -H "Authorization: Bearer $TOKEN" \
  -o export.json

# Verify JSON is valid
jq '.' export.json > /dev/null
echo $?
# Expected: 0 (valid JSON)

# Verify structure
jq '.export_timestamp, .resume_id, .format' export.json
# Expected: All fields populated

jq '.total_records' export.json
# Expected: > 0
```

**JSON Structure Verification:**
```json
{
  "export_timestamp": "2026-02-03T12:00:00Z",
  "resume_id": "uuid",
  "filename": "resume.pdf",
  "format": "json",
  "total_records": 45,
  "resume": {
    "id": "uuid",
    "filename": "resume.pdf",
    "created_at": "2026-01-15T10:30:00Z"
  },
  "parsed_resume": {
    "email": "user@example.com",     // PII
    "phone": "+1-234-567-8900",      // PII
    "name": "John Smith",            // PII
    "location": "San Francisco, CA", // PII
    "skills": [...],
    "work_experience": [...],
    "education": [...]
  },
  "hiring_stages": [...],
  "activities": [...],
  "notes": [...],
  "tags": [...],
  "consents": [...]
}
```

---

### Test 2.2: CSV Data Export

**Objective:** Verify user can export data as CSV

**Steps:**
1. Create test candidate with full data
2. Navigate to `/settings/privacy`
3. Click "Export Data"
4. Select "CSV" format
5. Click "Export"
6. Wait for download
7. Open CSV file in spreadsheet software
8. Verify data integrity

**Expected Results:**
- ✅ CSV format option available
- ✅ File downloads as .csv
- ✅ CSV is properly formatted
- ✅ All data rows present
- ✅ Headers are correct
- ✅ No data corruption

**API Verification:**
```bash
curl -X GET "http://localhost:8000/api/data-export/resume/$RESUME_ID?format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  -o export.csv

# Verify CSV format
file export.csv
# Expected: ASCII text, with very long lines

# Count rows (excluding header)
wc -l export.csv
# Expected: > 1 (at least 1 data row)
```

**CSV Structure Verification:**
```csv
record_type,resume_id,email,phone,name,location,skill,stage,note
parsed_resume,uuid,user@example.com,+1-234-567-8900,John Smith,San Francisco,CA,Python,,
hiring_stage,uuid,,,,,,,,screening,
candidate_note,uuid,,,,,,,,,Promising candidate
```

---

### Test 2.3: Export Contains All PII

**Objective:** Verify export includes all personal data categories

**Checklist:**
- [ ] Contact info (email, phone, location)
- [ ] Identification (name, age)
- [ ] Professional (position, skills, experience, education)
- [ ] Pipeline (hiring stages)
- [ ] Activities (stage changes, notes)
- [ ] Tags (organizational labels)
- [ ] Consents (consent records)
- [ ] Metadata (timestamps)

**JSON Path Verification:**
```bash
# Check all required fields exist
jq '.parsed_resume | has("email", "phone", "name", "location")' export.json
# Expected: true

jq '.parsed_resume | has("skills", "work_experience", "education")' export.json
# Expected: true

jq '.hiring_stages | length > 0' export.json
# Expected: true
```

---

### Test 2.4: Export Data Accuracy

**Objective:** Verify exported data matches database data

**Steps:**
1. Query database for candidate data
2. Export data via API
3. Compare exported data to database records
4. Verify no missing or corrupted data

**Database Verification:**
```sql
-- Get candidate data
SELECT
    r.id,
    r.filename,
    pr.parsed_data->>'email' as email,
    pr.parsed_data->>'name' as name
FROM resumes r
LEFT JOIN parsed_resumes pr ON pr.resume_id = r.id
WHERE r.id = 'test-resume-id';
```

**Comparison Script:**
```python
import json
import psycopg2

# Query database
conn = psycopg2.connect("dbname=agenthr")
cur = conn.cursor()
cur.execute("SELECT parsed_data FROM parsed_resumes WHERE resume_id = %s", (resume_id,))
db_data = cur.fetchone()[0]

# Load export
with open('export.json') as f:
    export_data = json.load(f)

# Compare
assert db_data['email'] == export_data['parsed_resume']['email']
assert db_data['name'] == export_data['parsed_resume']['name']
print("✅ Data accuracy verified")
```

---

### Test 2.5: Export Error Handling

**Objective:** Verify graceful error handling for export failures

**Steps:**
1. Attempt to export non-existent resume
2. Verify API returns 404
3. Attempt to export without authentication
4. Verify API returns 401
5. Attempt to export other user's data
6. Verify API returns 403

**Expected Results:**
- ✅ 404 for non-existent resume
- ✅ 401 for missing auth token
- ✅ 403 for cross-user access attempt
- ✅ Descriptive error messages

**API Verification:**
```bash
# Test 404
curl -X GET "http://localhost:8000/api/data-export/resume/nonexistent-id" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 404 Not Found

# Test 401
curl -X GET "http://localhost:8000/api/data-export/resume/$RESUME_ID"
# Expected: 401 Unauthorized

# Test 403 (user A trying to export user B's data)
curl -X GET "http://localhost:8000/api/data-export/resume/$OTHER_USER_RESUME_ID" \
  -H "Authorization: Bearer $USER_A_TOKEN"
# Expected: 403 Forbidden
```

---

## Right to Erasure Tests

### Test Suite: Data Deletion (Right to be Forgotten)

**File:** `frontend/e2e/gdpr-data-deletion-flow.spec.ts`
**Total Tests:** 12
**Test Categories:** Frontend UI, API Integration, Database, Mobile, E2E

---

### Test 3.1: Create Deletion Request

**Objective:** Verify user can submit data deletion request

**Steps:**
1. Create test candidate with full data
2. Navigate to `/settings/privacy`
3. Click "Delete Account" quick action
4. Read warning message
5. Enter email address
6. Select reason from dropdown
7. Confirm request
8. Verify success message

**Expected Results:**
- ✅ Deletion form opens
- ✅ Warning message displayed
- ✅ Email validation works
- ✅ Reason dropdown works
- ✅ Confirmation required
- ✅ Request submitted successfully
- ✅ Success message shown

**API Verification:**
```bash
curl -X POST http://localhost:8000/api/data-deletion/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "test-resume-id",
    "requester_email": "user@example.com",
    "reason": "Right to be forgotten"
  }'
# Expected: 201 Created
# Expected: {"id": "...", "status": "pending"}
```

**Database Verification:**
```sql
SELECT
    id,
    requester_email,
    status,
    created_at
FROM data_deletion_requests
WHERE requester_email = 'user@example.com'
ORDER BY created_at DESC
LIMIT 1;
-- Expected: status = 'pending'
```

---

### Test 3.2: Email Verification

**Objective:** Verify deletion request requires email verification

**Steps:**
1. Submit deletion request
2. Check email inbox (test email service)
3. Find verification email
4. Click verification link/token
5. Verify request status changes to `VERIFIED`

**Expected Results:**
- ✅ Verification email sent
- ✅ Email contains verification link
- ✅ Link works and verifies request
- ✅ Status changes from `PENDING` to `VERIFIED`

**API Verification:**
```bash
# Simulate email verification
curl -X POST http://localhost:8000/api/data-deletion/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "verification-token-from-email"
  }'
# Expected: 200 OK
# Expected: {"status": "verified"}
```

**Database Verification:**
```sql
SELECT status, verified_at
FROM data_deletion_requests
WHERE id = 'deletion-request-id';
-- Expected: status = 'verified', verified_at IS NOT NULL
```

---

### Test 3.3: Process Deletion Request

**Objective:** Verify deletion request can be processed

**Steps:**
1. Verify deletion request (status = VERIFIED)
2. Call process API endpoint
3. Verify status changes to PROCESSING
4. Wait for processing to complete
5. Verify status changes to COMPLETED
6. Verify all data deleted from database

**Expected Results:**
- ✅ Request can be processed
- ✅ Status transitions: VERIFIED → PROCESSING → COMPLETED
- ✅ All data deleted from database
- ✅ File deleted from storage
- ✅ Audit log created

**API Verification:**
```bash
# Process deletion request
curl -X POST http://localhost:8000/api/data-deletion/process \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "deletion-request-id"}'
# Expected: 200 OK
```

**Database Verification:**
```sql
-- Verify resume deleted
SELECT COUNT(*) FROM resumes WHERE id = 'deleted-resume-id';
-- Expected: 0

-- Verify cascade deletion
SELECT COUNT(*) FROM parsed_resumes WHERE resume_id = 'deleted-resume-id';
-- Expected: 0

SELECT COUNT(*) FROM hiring_stages WHERE resume_id = 'deleted-resume-id';
-- Expected: 0

SELECT COUNT(*) FROM candidate_notes WHERE resume_id = 'deleted-resume-id';
-- Expected: 0
```

**Audit Log Verification:**
```sql
SELECT
    action_type,
    target_id,
    action_data
FROM audit_logs
WHERE action_type = 'deletion_request_processed'
AND target_id = 'deleted-resume-id'
ORDER BY created_at DESC
LIMIT 1;
-- Expected: action_data contains list of deleted entities
```

---

### Test 3.4: Deletion Request Rejection

**Objective:** Verify deletion request can be rejected (legal hold)

**Steps:**
1. Create deletion request for hired candidate
2. Attempt to process deletion
3. Verify request is rejected
4. Verify rejection reason provided
5. Verify data NOT deleted

**Expected Results:**
- ✅ Request rejected when legal obligation exists
- ✅ Rejection reason documented
- ✅ Data remains in database
- ✅ Status = REJECTED

**API Verification:**
```bash
curl -X POST http://localhost:8000/api/data-deletion/process \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "deletion-request-id",
    "rejection_reason": "Legal obligation to retain hired candidate data"
  }'
# Expected: 200 OK
# Expected: {"status": "rejected"}
```

**Database Verification:**
```sql
SELECT status, rejection_reason
FROM data_deletion_requests
WHERE id = 'deletion-request-id';
-- Expected: status = 'rejected', rejection_reason IS NOT NULL

-- Verify data NOT deleted
SELECT COUNT(*) FROM resumes WHERE id = 'hired-candidate-id';
-- Expected: 1 (still exists)
```

---

### Test 3.5: Cancel Pending Deletion Request

**Objective:** Verify user can cancel pending deletion request

**Steps:**
1. Submit deletion request
2. Do NOT verify via email
3. Call cancel API endpoint
4. Verify request is cancelled/deleted
5. Verify data NOT deleted

**Expected Results:**
- ✅ Pending requests can be cancelled
- ✅ Request record deleted
- ✅ Data remains intact
- ✅ No audit log for deletion

**API Verification:**
```bash
curl -X DELETE http://localhost:8000/api/data-deletion/request/request-id \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204 No Content
```

**Database Verification:**
```sql
SELECT COUNT(*) FROM data_deletion_requests WHERE id = 'request-id';
-- Expected: 0 (deleted)

-- Verify data still exists
SELECT COUNT(*) FROM resumes WHERE id = 'resume-id';
-- Expected: 1
```

---

## Data Retention Tests

### Test Suite: Retention Policy Automation

**File:** `frontend/e2e/gdpr-retention-policy-flow.spec.ts`
**Total Tests:** 19
**Test Categories:** Policy Management, Data Creation, Cleanup, Verification, Mobile, E2E

---

### Test 4.1: Create Retention Policy

**Objective:** Verify organization can create custom retention policy

**Steps:**
1. Navigate to retention policy settings
2. Click "Add Policy"
3. Select entity type (e.g., RESUME)
4. Set retention days (e.g., 30)
5. Select action type (e.g., DELETE)
6. Save policy
7. Verify policy created in database

**Expected Results:**
- ✅ Policy creation form works
- ✅ Entity type dropdown populated
- ✅ Retention days validation works
- ✅ Action type selection works
- ✅ Policy saved to database
- ✅ Policy appears in policy list

**API Verification:**
```bash
curl -X POST http://localhost:8000/api/retention-policies/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "resume",
    "retention_days": 30,
    "action_type": "delete",
    "policy_name": "30-Day Resume Retention"
  }'
# Expected: 201 Created
```

**Database Verification:**
```sql
SELECT
    entity_type,
    retention_days,
    action_type,
    is_active
FROM data_retention_policies
WHERE policy_name = '30-Day Resume Retention';
-- Expected: All fields match request
```

---

### Test 4.2: Automated Cleanup Execution

**Objective:** Verify Celery task automatically deletes expired data

**Steps:**
1. Create retention policy (30 days)
2. Create old resume (created_date > 30 days ago)
3. Create recent resume (created_date < 30 days ago)
4. Manually trigger cleanup task:
   ```bash
   cd backend
   celery -A celery_app call tasks.retention_cleanup.cleanup_expired_data
   ```
5. Verify old resume deleted
6. Verify recent resume preserved
7. Verify audit log entry created

**Expected Results:**
- ✅ Cleanup task executes successfully
- ✅ Old data deleted (action = DELETE)
- ✅ Recent data preserved
- ✅ Cleanup statistics returned
- ✅ Audit log entry created

**Manual Task Trigger:**
```bash
# Dry-run mode (test without deleting)
curl -X POST http://localhost:8000/api/retention-policies/cleanup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
# Expected: 200 OK
# Expected: {"deleted_count": 1, "preserved_count": 1}

# Actual cleanup
curl -X POST http://localhost:8000/api/retention-policies/cleanup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
# Expected: 200 OK
```

**Database Verification:**
```sql
-- Verify old resume deleted
SELECT COUNT(*) FROM resumes WHERE id = 'old-resume-id';
-- Expected: 0

-- Verify recent resume preserved
SELECT COUNT(*) FROM resumes WHERE id = 'recent-resume-id';
-- Expected: 1

-- Verify audit log
SELECT COUNT(*) FROM audit_logs WHERE action_type = 'retention_cleanup';
-- Expected: > 0
```

---

### Test 4.3: Retention Action - Anonymize

**Objective:** Verify ANONYMIZE action removes PII but keeps aggregates

**Steps:**
1. Create retention policy with action = ANONYMIZE
2. Create old resume with PII
3. Run cleanup task
4. Verify parsed_resume PII fields redacted
5. Verify resume record preserved (for analytics)

**Expected Results:**
- ✅ PII fields redacted (email, phone, name)
- ✅ Aggregate data preserved (skills counts, trends)
- ✅ Record still exists in database
- ✅ Audit log notes anonymization

**Database Verification:**
```sql
SELECT
    pr.parsed_data->>'email' as email,
    pr.parsed_data->>'name' as name,
    pr.parsed_data->>'phone' as phone
FROM parsed_resumes pr
WHERE pr.resume_id = 'old-resume-id';
-- Expected: All PII fields = "[REDACTED]" or NULL

-- But record still exists
SELECT COUNT(*) FROM parsed_resumes WHERE resume_id = 'old-resume-id';
-- Expected: 1
```

---

### Test 4.4: Retention Action - Archive

**Objective:** Verify ARCHIVE action moves data to cold storage

**Steps:**
1. Create retention policy with action = ARCHIVE
2. Create old resume
3. Run cleanup task
4. Verify data moved to archive storage
5. Verify data marked as archived

**Expected Results:**
- ✅ Data compressed and moved
- ✅ Archive location recorded
- ✅ Data marked as archived (flag)
- ✅ Normal access blocked
- ✅ DPO can still access

**Database Verification:**
```sql
-- Check archive flag
SELECT is_archived, archive_location
FROM resumes
WHERE id = 'old-resume-id';
-- Expected: is_archived = true, archive_location IS NOT NULL
```

---

### Test 4.5: Policy Priority (Organization vs Global)

**Objective:** Verify organization policies override global policies

**Steps:**
1. Create global policy: 365 days retention
2. Create organization policy: 30 days retention
3. Create resume in that organization (31 days old)
4. Run cleanup task
5. Verify resume deleted (follows shorter org policy)

**Expected Results:**
- ✅ Organization policy takes precedence
- ✅ Shorter retention period wins
- ✅ Global policy used as default
- ✅ Policy priority correctly calculated

**Database Verification:**
```sql
-- Verify deletion followed org policy (30 days)
SELECT COUNT(*) FROM resumes WHERE id = 'org-resume-id' AND created_at < NOW() - INTERVAL '30 days';
-- Expected: 0 (deleted by org policy)
```

---

## Security Testing

### Test Suite: Security and Access Control

---

### Test 5.1: PII Not in Logs

**Objective:** Verify no PII in application logs

**Steps:**
1. Upload resume with PII
2. Parse resume (triggers logging)
3. Search application logs for email/phone
4. Verify no PII found

**Expected Results:**
- ✅ No email addresses in logs
- ✅ No phone numbers in logs
- ✅ No names in logs (unless aggregated)
- ✅ Only user IDs and entity IDs logged

**Log Verification:**
```bash
# Check backend logs
cd backend
grep -r "user@example.com" . --include="*.log"
# Expected: No results

grep -r "john@example.com" /var/log/agenthr/
# Expected: No results

# Verify only IDs logged
grep "resume_id" /var/log/agenthr/app.log | head -5
# Expected: resume_id=uuid (no PII)
```

---

### Test 5.2: PII Not in Error Messages

**Objective:** Verify PII not exposed in error responses

**Steps:**
1. Intentionally trigger validation error
2. Check error response
3. Verify no PII in error details

**Expected Results:**
- ✅ Generic error messages
- ✅ Only field names mentioned (not values)
- ✅ No PII in stack traces

**API Verification:**
```bash
# Trigger validation error
curl -X POST http://localhost:8000/api/consent/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consent_type": "invalid_type",
    "user_email": "user@example.com"
  }'
# Expected: 422 Validation Error
# Expected: Error mentions "consent_type" but NOT the email
```

---

### Test 5.3: Encryption at Rest

**Objective:** Verify database encryption enabled

**Steps:**
1. Check database connection string
2. Verify SSL mode required
3. Check file storage encryption
4. Verify backup encryption

**Expected Results:**
- ✅ Database connection uses `sslmode=require`
- ✅ File storage uses AES-256 encryption
- ✅ Backups encrypted

**Configuration Verification:**
```bash
# Check database URL
grep DATABASE_URL backend/.env
# Expected: postgresql://...?sslmode=require

# Check file encryption
ls -la /data/uploads/resume.pdf
# Expected: Encrypted file system (check mount options)

# Check backup encryption
file /backups/agenthr_backup.sql.gz
# Expected: Encrypted backup
```

---

### Test 5.4: Encryption in Transit

**Objective:** Verify TLS/HTTPS enforced

**Steps:**
1. Check API base URL
2. Verify HTTPS required
3. Check TLS version
4. Verify cipher suites

**Expected Results:**
- ✅ API uses HTTPS only (production)
- ✅ TLS 1.2 minimum required
- ✅ Strong cipher suites
- ✅ HTTP requests redirect to HTTPS

**Security Scan:**
```bash
# Test TLS configuration
nmap --script ssl-enum-ciphers -p 443 api.agenthr.com

# Check certificate
openssl s_client -connect api.agenthr.com:443 -servername api.agenthr.com
# Expected: Valid certificate, TLS 1.2 or 1.3
```

---

### Test 5.5: Access Control (Authorization)

**Objective:** Verify users can only access their own data

**Steps:**
1. Create user A with resume
2. Create user B with different resume
3. User A attempts to access user B's resume
4. Verify access denied (403)

**Expected Results:**
- ✅ Cross-user access blocked
- ✅ Cross-organization access blocked
- ✅ Role-based access enforced
- ✅ API returns 403 Forbidden

**API Verification:**
```bash
# User A tries to access User B's resume
RESUME_B_ID="user-b-resume-id"
TOKEN_A="user-a-jwt-token"

curl -X GET "http://localhost:8000/api/resumes/$RESUME_B_ID" \
  -H "Authorization: Bearer $TOKEN_A"
# Expected: 403 Forbidden
# Expected: {"detail": "Access denied"}
```

---

### Test 5.6: SQL Injection Prevention

**Objective:** Verify ORM prevents SQL injection

**Steps:**
1. Attempt SQL injection in search parameter
2. Verify query sanitized
3. Verify no SQL errors
4. Verify no unexpected data returned

**Expected Results:**
- ✅ Input sanitized
- ✅ No SQL errors
- ✅ Parameterized queries used
- ✅ SQLAlchemy ORM protects against injection

**API Verification:**
```bash
# Attempt SQL injection
curl -X POST http://localhost:8000/api/search/candidates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "John OR 1=1; DROP TABLE resumes; --"
  }'
# Expected: 200 OK (search executed safely)
# Expected: No SQL errors
# Expected: No data deleted
```

---

## Audit Trail Testing

### Test Suite: Audit Logging

---

### Test 6.1: Consent Events Logged

**Objective:** Verify consent events create audit log entries

**Steps:**
1. Grant consent
2. Check audit_logs table
3. Verify entry created
4. Verify entry contains all required fields

**Expected Results:**
- ✅ Consent granted event logged
- ✅ Consent withdrawn event logged
- ✅ Event contains: actor_id, action_type, target_id, timestamp
- ✅ IP address and user agent captured

**Database Verification:**
```sql
SELECT
    action_type,
    actor_id,
    target_id,
    action_data,
    ip_address,
    user_agent,
    created_at
FROM audit_logs
WHERE action_type IN ('consent_granted', 'consent_withdrawn')
ORDER BY created_at DESC
LIMIT 5;
-- Expected: All fields populated, timestamps recent
```

---

### Test 6.2: Data Access Events Logged

**Objective:** Verify data access creates audit log entries

**Steps:**
1. Access candidate resume via API
2. Check audit_logs table
3. Verify `resume_viewed` event logged
4. Verify actor and target IDs correct

**Expected Results:**
- ✅ Resume access logged
- ✅ Data export logged
- ✅ Search operations logged
- ✅ Who accessed what data recorded

**Database Verification:**
```sql
SELECT
    action_type,
    actor_id,
    target_id,
    action_data,
    created_at
FROM audit_logs
WHERE action_type = 'resume_viewed'
AND target_id = 'test-resume-id'
ORDER BY created_at DESC;
-- Expected: Records exist, actor_id = user who accessed
```

---

### Test 6.3: Data Deletion Events Logged

**Objective:** Verify deletion events create comprehensive audit log

**Steps:**
1. Submit deletion request
2. Process deletion request
3. Check audit_logs table
4. Verify both request and processing logged
5. Verify deleted data listed in action_data

**Expected Results:**
- ✅ Deletion request created event logged
- ✅ Deletion request processed event logged
- ✅ List of deleted entities in action_data
- ✅ Timestamps accurate
- ✅ Actor (admin) logged

**Database Verification:**
```sql
SELECT
    action_type,
    target_id,
    action_data,
    created_at
FROM audit_logs
WHERE action_type = 'deletion_request_processed'
AND target_id = 'deleted-resume-id';
-- Expected: action_data contains JSON array of deleted entities
```

---

### Test 6.4: Audit Log Retention

**Objective:** Verify audit logs retained for 7 years

**Steps:**
1. Check audit log retention policy
2. Verify old logs not deleted
3. Verify logs queryable after years

**Expected Results:**
- ✅ Audit logs excluded from normal cleanup
- ✅ 7-year retention configured
- ✅ Logs archived after 7 years (not deleted)
- ✅ Legal requirement met

**Database Verification:**
```sql
-- Check retention policy for audit logs
SELECT entity_type, retention_days, action_type
FROM data_retention_policies
WHERE entity_type = 'audit_logs';
-- Expected: retention_days = 2555 (7 years)
-- Expected: action_type = 'ARCHIVE' (not DELETE)
```

---

## Performance Testing

### Test Suite: GDPR Feature Performance

---

### Test 7.1: Export Performance

**Objective:** Verify data export completes within acceptable time

**Steps:**
1. Create candidate with maximum data (100 activities, 50 notes, etc.)
2. Trigger data export
3. Measure time to complete
4. Verify file size reasonable

**Expected Results:**
- ✅ Export completes < 30 seconds
- ✅ File size < 10MB (JSON) or < 5MB (CSV)
- ✅ Memory usage acceptable
- ✅ No timeout errors

**Performance Test:**
```bash
time curl -X GET "http://localhost:8000/api/data-export/resume/$RESUME_ID?format=json" \
  -H "Authorization: Bearer $TOKEN" \
  -o export.json

# Expected: real < 30s
ls -lh export.json
# Expected: < 10MB
```

---

### Test 7.2: Deletion Performance

**Objective:** Verify data deletion completes within acceptable time

**Steps:**
1. Create candidate with maximum related data
2. Submit deletion request
3. Process deletion
4. Measure time to complete

**Expected Results:**
- ✅ Deletion completes < 60 seconds
- ✅ All cascade deletes complete
- ✅ File storage cleanup complete
- ✅ No orphaned records

**Performance Test:**
```bash
time curl -X POST http://localhost:8000/api/data-deletion/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "deletion-request-id"}'

# Expected: real < 60s
```

---

### Test 7.3: Cleanup Task Performance

**Objective:** Verify retention cleanup task performs efficiently

**Steps:**
1. Create 10,000 old resumes (expired)
2. Create 10,000 recent resumes (not expired)
3. Run cleanup task
4. Measure time to complete

**Expected Results:**
- ✅ Cleanup completes < 5 minutes
- ✅ Only expired data deleted
- ✅ Recent data preserved
- ✅ No database locks

**Performance Test:**
```bash
# Trigger cleanup for large dataset
time celery -A celery_app call tasks.retention_cleanup.cleanup_expired_data

# Expected: < 5 minutes for 20k records
```

---

## Testing Checklist Summary

### Test Coverage

| Feature | E2E Tests | API Tests | Manual Tests | Total |
|---------|-----------|-----------|--------------|-------|
| Consent Management | 10 | 5 | 3 | 18 |
| Right to Access | 7 | 4 | 3 | 14 |
| Right to Erasure | 6 | 3 | 3 | 12 |
| Data Retention | 8 | 4 | 2 | 14 |
| Security | 6 | 6 | 2 | 14 |
| Audit Trail | 4 | 4 | 0 | 8 |
| Performance | 3 | 0 | 0 | 3 |
| **TOTAL** | **44** | **26** | **13** | **83** |

---

### Pre-Release Testing Checklist

Before releasing GDPR features to production:

- [ ] All 83 tests pass (100% pass rate)
- [ ] E2E tests run on CI/CD pipeline
- [ ] Security scan completed (no high/critical issues)
- [ ] Performance benchmarks met
- [ ] Legal review of consent text completed
- [ ] DPA review and approval obtained
- [ ] Audit log review completed
- [ ] Incident response procedure tested
- [ ] Data backup/restore tested
- [ ] Disaster recovery tested
- [ ] User acceptance testing (UAT) completed
- [ ] Documentation reviewed and approved

---

### Post-Release Monitoring

After releasing GDPR features:

- [ ] Monitor audit logs for anomalies
- [ ] Track consent grant/withdrawal rates
- [ ] Monitor data export request volume
- [ ] Monitor deletion request processing time
- [ ] Review cleanup task execution logs
- [ ] Track API error rates
- [ ] Monitor performance metrics
- [ ] Review user feedback on privacy controls
- [ ] Conduct quarterly compliance review
- [ ] Annual DPO audit

---

## Test Execution Commands

### Run All Tests

```bash
# E2E tests (Playwright)
cd frontend
npx playwright test e2e/gdpr-*

# With coverage
npx playwright test e2e/gdpr-* --reporter=html

# Specific test suites
npx playwright test e2e/gdpr-consent-flow.spec.ts
npx playwright test e2e/gdpr-data-deletion-flow.spec.ts
npx playwright test e2e/gdpr-data-export-flow.spec.ts
npx playwright test e2e/gdpr-retention-policy-flow.spec.ts
```

### Manual Testing Scripts

```bash
# Use provided test scripts
cd frontend

# Test consent flow
bash scripts/test-gdpr-consent-flow.sh --ui

# Test data deletion
bash scripts/test-gdpr-data-deletion-flow.sh --ui

# Test data export
bash scripts/test-gdpr-data-export-flow.sh --ui

# Test retention policies
bash scripts/test-gdpr-retention-policy-flow.sh --ui
```

### Database Verification Queries

```sql
-- Consent records
SELECT COUNT(*) FROM consent_records WHERE granted = true;

-- Deletion requests
SELECT status, COUNT(*) FROM data_deletion_requests GROUP BY status;

-- Retention policies
SELECT entity_type, retention_days, action_type FROM data_retention_policies WHERE is_active = true;

-- Audit logs (last 24 hours)
SELECT action_type, COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours' GROUP BY action_type;
```

---

**Document Owner:** QA Lead
**Review Frequency:** Each release
**Last Updated:** 2026-02-03
**Next Review:** Before next production release

For questions about testing procedures, contact: qa@agenthr.com
