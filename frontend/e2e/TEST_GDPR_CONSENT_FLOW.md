# GDPR Consent Flow End-to-End Test Guide

## Overview

This document provides instructions for testing the complete GDPR consent flow from cookie banner to database.

## Test File

**Location**: `frontend/e2e/gdpr-consent-flow.spec.ts`

**Test Suite**:
- Cookie Banner Display on First Visit
- Grant Consent via Cookie Banner
- Verify Consent Saved to Backend API
- View Consent in ConsentManager
- Revoke Consent in ConsentManager
- Verify Revocation Saved to Backend
- Cookie Consent Persistence Across Sessions
- Mobile Responsive Testing

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

## Running the Tests

### Run All GDPR Consent Flow Tests

```bash
cd frontend
npx playwright test gdpr-consent-flow.spec.ts
```

### Run with UI Mode (Interactive)

```bash
cd frontend
npx playwright test gdpr-consent-flow.spec.ts --ui
```

### Run with Headed Mode (See Browser)

```bash
cd frontend
npx playwright test gdpr-consent-flow.spec.ts --headed
```

### Run Specific Test Suite

```bash
# Test only cookie banner
npx playwright test gdpr-consent-flow.spec.ts -g "Cookie Banner"

# Test only privacy settings
npx playwright test gdpr-consent-flow.spec.ts -g "Privacy Settings"

# Test only API integration
npx playwright test gdpr-consent-flow.spec.ts -g "API Integration"

# Test only mobile responsive
npx playwright test gdpr-consent-flow.spec.ts -g "Mobile Responsive"

# Test complete end-to-end flow
npx playwright test gdpr-consent-flow.spec.ts -g "Complete End-to-End"
```

## Manual Testing Steps

### Step 1: First Visit - Cookie Banner

1. Open browser in incognito mode (or clear localStorage)
2. Navigate to `http://localhost:5173`
3. **Verify**: Cookie banner appears at bottom or center of page
4. **Verify**: Banner contains:
   - Text about cookies/consent
   - "Accept All" button
   - "Reject All" button
   - "Customize" button

### Step 2: Grant Consent

1. Click "Accept All" button
2. **Verify**: Banner disappears
3. **Verify**: Check localStorage:
   ```javascript
   // Open browser console
   JSON.parse(localStorage.getItem('cookie_consent'))
   // Should return: { necessary: true, analytics: true, marketing: true }
   ```

### Step 3: Verify Backend API Call

1. Open browser DevTools → Network tab
2. Filter by "consent" or "api"
3. Grant consent via cookie banner or consent manager
4. **Verify**: POST request to `/api/consent/` or `/api/cookie-consent/`
5. **Verify**: Request body contains:
   ```json
   {
     "consent_type": "data_processing",
     "granted": true,
     "consent_text": "...",
     "consent_version": "1.0"
   }
   ```
6. **Verify**: Response status is 201 or 200

### Step 4: Verify Database Record

1. Access PostgreSQL database
2. Run query:
   ```sql
   SELECT * FROM consent_records ORDER BY created_at DESC LIMIT 1;
   ```
3. **Verify**: Record exists with:
   - `consent_type` = 'data_processing' or 'data_storing'
   - `granted` = true
   - `user_id` is not null
   - `ip_address` is not null
   - `created_at` timestamp is recent

### Step 5: View Consent in ConsentManager

1. Navigate to `http://localhost:5173/settings/privacy`
2. **Verify**: Privacy settings page loads
3. **Verify**: "Consent Management" tab is visible
4. Click on "Consent Management" tab
5. **Verify**: ConsentManager component displays:
   - List of consent types (Data Processing, Data Storage, Resume Analysis, etc.)
   - Toggle switches for each consent type
   - Status indicators (granted/not granted)
   - Summary statistics

### Step 6: Grant Additional Consent

1. Find a consent type that is not granted (switch is off)
2. Click the toggle switch
3. **Verify**: Switch turns on (visual feedback)
4. **Verify**: No error messages
5. **Verify**: Check Network tab for API call

### Step 7: Revoke Consent

1. Find a consent type that is granted (switch is on)
2. Click the toggle switch to revoke
3. **Verify**: Confirmation dialog appears with:
   - Warning message about revoking consent
   - "Confirm" or "Withdraw" button
   - "Cancel" or "Back" button
4. Click "Confirm" button
5. **Verify**: Switch turns off
6. **Verify**: Success message or notification

### Step 8: Verify Revocation in Database

1. Access PostgreSQL database
2. Run query:
   ```sql
   SELECT * FROM consent_records
   WHERE consent_type = 'data_processing'
     AND withdrawn_at IS NOT NULL
   ORDER BY created_at DESC
   LIMIT 1;
   ```
3. **Verify**: Record shows:
   - `withdrawn_at` timestamp is not null
   - `withdrawal_reason` is not null (if provided)
   - `granted` is still true (historical record preserved)

### Step 9: Verify Consent Persistence

1. Close browser tab
2. Reopen browser and navigate to `http://localhost:5173/settings/privacy`
3. **Verify**: Cookie banner does NOT appear (consent persisted)
4. **Verify**: ConsentManager shows previously granted/revoked consents
5. **Verify**: localStorage still contains consent data

## Test Scenarios

### Scenario 1: New User Complete Flow

1. Clear all browser data
2. Visit site for first time
3. See cookie banner
4. Accept all cookies
5. Navigate to privacy settings
6. View consent manager
7. Grant additional consent
8. Revoke one consent
9. Verify all changes in database

### Scenario 2: Returning User

1. Visit site (with existing consent)
2. Cookie banner should NOT appear
3. Navigate to privacy settings
4. Modify existing consents
5. Verify changes persist across sessions

### Scenario 3: Mobile User

1. Use mobile viewport or actual mobile device
2. Test complete flow
3. Verify responsive design
4. Verify touch interactions work

### Scenario 4: Custom Cookie Preferences

1. On first visit, click "Customize" instead of "Accept All"
2. Select specific cookie categories
3. Save preferences
4. Verify only selected categories are enabled

## Expected Results

### Successful Flow

✅ Cookie banner appears on first visit
✅ Banner disappears after consent decision
✅ Consent saved to localStorage
✅ Consent sent to backend API
✅ Consent record created in database
✅ Consent visible in ConsentManager
✅ Can grant new consents via ConsentManager
✅ Can revoke existing consents with confirmation
✅ Revocation sent to backend API
✅ Revocation recorded in database (withdrawn_at timestamp)
✅ Consent persists across sessions
✅ No errors in browser console
✅ No errors in backend logs

### Error Handling

❌ Backend API down:
   - Should show user-friendly error message
   - Should not break application
   - Should retry or offer manual retry

❌ Invalid consent data:
   - Should validate before sending
   - Should show clear error message
   - Should not crash application

❌ Network timeout:
   - Should show timeout message
   - Should offer retry option
   - Should preserve UI state

## Troubleshooting

### Cookie Banner Not Appearing

**Possible causes**:
- localStorage already has consent data
- Banner component not mounted
- CSS hiding banner

**Solutions**:
```javascript
// Clear localStorage
localStorage.clear();
// Reload page
location.reload();
```

### Consent Not Saving to Database

**Possible causes**:
- Backend API not running
- Database connection failed
- Invalid request data
- CORS issue

**Solutions**:
```bash
# Check backend is running
curl http://localhost:8000/api/consent/

# Check database connection
cd backend
python -c "from database import engine; print(engine.url)"

# Check CORS configuration
# See backend/main.py CORS middleware
```

### ConsentManager Not Showing Consents

**Possible causes**:
- API call failing
- User not authenticated (if auth required)
- Response format mismatch

**Solutions**:
```javascript
// Check browser console for errors
// Check Network tab for API response
// Verify API endpoint returns correct format
```

## Automated Test Coverage

The e2e test file covers:

1. **Cookie Banner Tests** (6 tests):
   - Display on first visit
   - Hide after accepting
   - Hide after rejecting
   - Customization dialog
   - localStorage persistence
   - No banner on repeat visit

2. **Privacy Settings Tests** (6 tests):
   - Privacy settings page display
   - Consent manager visibility
   - Grant consent
   - Revoke consent confirmation
   - Revoke consent action

3. **API Integration Tests** (2 tests):
   - Consent grant API call
   - Consent revocation API call

4. **Mobile Responsive Tests** (3 tests):
   - Cookie banner on mobile
   - Grant consent on mobile
   - Privacy settings on mobile

5. **Complete End-to-End Test** (1 test):
   - Full flow from banner to revocation

**Total**: 18 automated tests

## Verification Checklist

Before marking subtask-7-1 as complete, verify:

- [ ] All automated tests pass
- [ ] Cookie banner displays on first visit
- [ ] Consent can be granted via banner
- [ ] Consent saves to localStorage
- [ ] Consent sent to backend API
- [ ] Consent record created in database
- [ ] ConsentManager displays consents correctly
- [ ] Can grant additional consents via ConsentManager
- [ ] Can revoke consents via ConsentManager
- [ ] Revocation confirmation dialog appears
- [ ] Revocation sent to backend API
- [ ] Revocation recorded in database (withdrawn_at)
- [ ] Consent persists across browser sessions
- [ ] Flow works on mobile devices
- [ ] No console errors during flow
- [ ] No backend errors during flow

## Notes

- Tests use Playwright for browser automation
- Tests assume backend API is running on `http://localhost:8000`
- Tests assume frontend is running on `http://localhost:5173`
- Tests clear browser state before each test
- Tests use both desktop and mobile viewports
- Tests verify both frontend UI and backend API integration

## Related Files

- `frontend/src/components/CookieBanner.tsx` - Cookie banner component
- `frontend/src/components/ConsentManager.tsx` - Consent management component
- `frontend/src/contexts/CookieContext.tsx` - Cookie consent context
- `frontend/src/api/gdpr.ts` - GDPR API client
- `backend/api/consent.py` - Consent API endpoints
- `backend/api/cookie_consent.py` - Cookie consent API endpoints
- `backend/services/gdpr_service.py` - GDPR business logic
- `backend/models/consent_record.py` - Consent database model
