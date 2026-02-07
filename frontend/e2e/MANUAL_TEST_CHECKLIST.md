# Manual E2E Test Checklist

## Overview

Use this checklist to manually verify the integrations end-to-end workflow. This can be used when automated tests are not available or for additional verification.

## Prerequisites

- [ ] Backend API running at http://localhost:8000
- [ ] Frontend running at http://localhost:5173
- [ ] Database accessible and migrations applied
- [ ] Celery worker running (for background sync tasks)

## Test Environment Setup

### 1. Start Services

```bash
# Terminal 1: Backend API
cd backend
uvicorn main:app --reload

# Terminal 2: Celery Worker
cd backend
celery -A celery_app worker -l info

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 2. Open Browser

Navigate to: http://localhost:5173

---

## Test Scenario 1: Navigate to Integrations Page

### Steps

1. [ ] Login to the application (if required)
2. [ ] Navigate to Settings → Integrations
   - OR go directly to http://localhost:5173/integrations
3. [ ] Verify page loads without errors
4. [ ] Check browser console for errors (F12 → Console)

### Expected Results

- [ ] Page heading "Integrations" or "Integration Management" is visible
- [ ] "Add Integration" button is visible
- [ ] Integration list is visible OR "No integrations" empty state is shown
- [ ] No console errors
- [ ] Page is responsive on different screen sizes

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Notes:
```

---

## Test Scenario 2: Add New Workday Integration

### Steps

1. [ ] Click "Add Integration" button
2. [ ] Verify config dialog opens
3. [ ] Fill in integration details:
   - Name: `Test Workday Integration`
   - Platform: `Workday`
   - API URL: `https://wd1.workday.com` (or test URL)
   - Username: `test@example.com`
   - Password: `test-password-123`
   - Tenant Name: `test_tenant`
4. [ ] Enable sync toggle (optional)
5. [ ] Set sync interval to `60` minutes (optional)
6. [ ] Click "Save" button

### Expected Results

- [ ] Dialog opens with form fields
- [ ] Platform dropdown shows all options (Workday, Greenhouse, Lever, BambooHR, Ashby)
- [ ] Selecting Workday shows Workday-specific fields
- [ ] Form validation prevents empty required fields
- [ ] Save button is disabled while saving
- [ ] Success message appears OR error message with clear details
- [ ] Integration appears in the list after successful creation

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Integration ID: _______________

Notes:
```

---

## Test Scenario 3: Test Connection

### Steps

1. [ ] Locate the newly created integration in the list
2. [ ] Click "Test Connection" button
3. [ ] Wait for connection test to complete (2-10 seconds)

### Expected Results

- [ ] "Test Connection" button is visible and enabled
- [ ] Loading indicator appears during test
- [ ] Success message appears: "Connection successful" OR
- [ ] Error message appears with details: "Connection failed: [reason]"
- [ ] No unhandled errors in browser console

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Connection Status: ⬜ Success / ⬜ Failed (Expected if test credentials)

Response Time: _____ seconds

Notes:
```

---

## Test Scenario 4: Trigger Manual Sync

### Steps

1. [ ] Locate the integration in the list
2. [ ] Click "Sync Now" or "Trigger Sync" button
3. [ ] Wait for sync to trigger (1-3 seconds)
4. [ ] Check Celery worker terminal for task logs

### Expected Results

- [ ] "Sync Now" button is visible and enabled
- [ ] Clicking button shows confirmation or immediate loading state
- [ ] Success message: "Sync triggered successfully"
- [ ] Celery worker logs show task received: `tasks.sync_tasks.sync_integration_task`
- [ ] Sync task appears with correct integration_id
- [ ] Integration status changes to "Syncing" or shows sync indicator

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Sync Task ID: _______________

Celery Logs:
[Task received in worker terminal]

Notes:
```

---

## Test Scenario 5: View Sync History

### Steps

1. [ ] Locate the integration in the list
2. [ ] Click "View History" or "History" button
3. [ ] Verify sync history dialog opens
4. [ ] Check sync records displayed

### Expected Results

- [ ] "View History" button is visible and enabled
- [ ] History dialog/modal opens
- [ ] Table shows sync records with columns:
  - [ ] Sync Type (full/incremental)
  - [ ] Status (completed/failed/running)
  - [ ] Start Time
  - [ ] Duration
  - [ ] Records Processed
  - [ ] Records Successful
  - [ ] Records Failed
- [ ] Status badges have correct colors:
  - Completed: Green/Success
  - Failed: Red/Error
  - Running: Blue/Info
- [ ] Failed syncs show error message on click
- [ ] Date formatting is readable

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Number of sync records: _____

Most recent sync:
- Type: _____
- Status: _____
- Records processed: _____
- Duration: _____ seconds

Notes:
```

---

## Test Scenario 6: Edit Integration

### Steps

1. [ ] Click "Edit" button on the integration
2. [ ] Verify edit dialog opens with pre-filled data
3. [ ] Change integration name to `Updated Test Workday Integration`
4. [ ] Click "Save"

### Expected Results

- [ ] "Edit" button is visible
- [ ] Edit dialog opens
- [ ] All fields are pre-populated with current values
- [ ] Credentials are masked (passwords shown as ••••••)
- [ ] Updating name works
- [ ] Success message appears
- [ ] Updated name appears in integration list

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Notes:
```

---

## Test Scenario 7: Delete Integration

### Steps

1. [ ] Click "Delete" button on the integration
2. [ ] Verify confirmation dialog appears
3. [ ] Read confirmation message
4. [ ] Click "Cancel" to cancel deletion
5. [ ] Click "Delete" again
6. [ ] Click "Confirm" to confirm deletion

### Expected Results

- [ ] "Delete" button is visible (may need to click actions menu first)
- [ ] Confirmation dialog appears with warning message
- [ ] Cancel closes dialog without deleting
- [ ] Confirm deletes the integration
- [ ] Integration disappears from the list
- [ ] Success message appears: "Integration deleted"

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Notes:
```

---

## Test Scenario 8: Error Handling - Invalid Credentials

### Steps

1. [ ] Create new integration with invalid credentials:
   - Platform: `Workday`
   - API URL: `invalid-url`
   - Username: `invalid`
   - Password: `invalid`
2. [ ] Click "Test Connection"
3. [ ] Note the error message

### Expected Results

- [ ] Connection test fails gracefully
- [ ] Clear error message shown: "Connection failed: [specific error]"
- [ ] No unhandled exceptions or console errors
- [ ] User can retry or edit credentials
- [ ] Integration is not created OR created but with error status

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Error Message: _______________

Notes:
```

---

## Test Scenario 9: Verify Data Sync (with Mock Data)

### Steps

1. [ ] Trigger sync for integration
2. [ ] Check Celery worker logs
3. [ ] Query database for synced candidates/employees (if applicable)

### Check Database

```bash
# Backend terminal
cd backend
python

# Check for synced candidates
from database import SessionLocal
from models.candidate import Candidate

db = SessionLocal()
candidates = db.query(Candidate).filter(Candidate.source == 'workday').all()
print(f"Found {len(candidates)} synced candidates")
for c in candidates[:5]:
    print(f"- {c.first_name} {c.last_name} ({c.email})
```

### Expected Results

- [ ] Celery worker processes sync task
- [ ] Sync log entry created in database
- [ ] If successful: candidates/employees appear in database
- [ ] Sync status updates to "completed"
- [ ] Records processed count is > 0

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Sync Log Entry:
- Sync ID: _______________
- Status: _____
- Records processed: _____
- Records successful: _____
- Records failed: _____

Notes:
```

---

## Test Scenario 10: Mobile Responsiveness

### Steps

1. [ ] Open browser DevTools (F12)
2. [ ] Enable device emulation (Ctrl+Shift+M / Cmd+Shift+M)
3. [ ] Select mobile device (iPhone 12, Galaxy S20, etc.)
4. [ ] Navigate through all integration screens

### Expected Results

- [ ] Integrations page is readable on mobile
- [ ] Add Integration button is accessible
- [ ] Integration config dialog fits on screen (scrollable if needed)
- [ ] Forms are usable (touch targets large enough)
- [ ] Sync history table scrolls horizontally if needed
- [ ] No horizontal overflow on page body
- [ ] Navigation works on mobile

### Actual Results

```
Status: ⬜ Pass / ⬜ Fail

Viewport tested: _______________

Issues found:
```

---

## Cleanup After Testing

### Delete Test Integrations

```bash
# Via curl
curl -X GET http://localhost:8000/api/integrations/ | jq '.integrations[] | select(.name | contains("Test")) | .id' | xargs -I {} curl -X DELETE http://localhost:8000/api/integrations/{}

# Or via Python
cd backend
python -c "
from database import SessionLocal
from models.integration import Integration

db = SessionLocal()
test_integrations = db.query(Integration).filter(
    Integration.name.like('%Test%')
).all()

for integration in test_integrations:
    print(f'Deleting: {integration.name} ({integration.id})
    db.delete(integration)

db.commit()
print(f'Deleted {len(test_integrations)} test integrations')
"
```

### Clear Sync Logs

```bash
cd backend
python -c "
from database import SessionLocal
from models.sync_log import SyncLog

db = SessionLocal()
db.query(SyncLog).delete()
db.commit()
print('Cleared sync logs')
"
```

---

## Summary

### Tests Passed: _____ / 10

### Overall Status: ⬜ Pass / ⬜ Fail

### Issues Found

1.
2.
3.

### Recommendations

-
-

---

## Additional Notes

Use this section to document any findings, bugs, or improvements discovered during manual testing.

```
Tester: _______________
Date: _______________
Environment: [ ] Development [ ] Staging [ ] Production
Backend Version: _______________
Frontend Version: _______________
```
