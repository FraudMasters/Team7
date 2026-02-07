# Subtask 7-1: End-to-End Consent Flow Verification Checklist

## Task Information

- **Subtask ID**: subtask-7-1
- **Description**: Test end-to-end consent flow from cookie banner to database
- **Phase**: Integration and Testing
- **Service**: all

## Files Created

1. **E2E Test File**: `frontend/e2e/gdpr-consent-flow.spec.ts`
   - 18 automated tests covering complete consent flow
   - Tests for cookie banner, privacy settings, API integration, mobile responsive, and complete end-to-end flow

2. **Test Documentation**: `frontend/e2e/TEST_GDPR_CONSENT_FLOW.md`
   - Comprehensive testing guide
   - Manual testing steps
   - Troubleshooting tips
   - Expected results

3. **Test Runner Script**: `frontend/scripts/test-gdpr-consent-flow.sh`
   - Automated test runner with options
   - UI mode, headed mode, debug mode support
   - Test filtering capabilities
   - Colored output and error handling

## Verification Steps

### Step 1: Prerequisites Check

- [ ] Backend API is running on `http://localhost:8000`
- [ ] Frontend dev server is running on `http://localhost:5173`
- [ ] PostgreSQL database is running
- [ ] GDPR database tables exist (consent_records, cookie_consent, etc.)
- [ ] Browser automation tools installed (Playwright)

### Step 2: Run Automated Tests

- [ ] Navigate to frontend directory
- [ ] Run test script: `./scripts/test-gdpr-consent-flow.sh`
- [ ] All 18 tests pass
- [ ] No errors in test output
- [ ] Test report generated successfully

### Step 3: Verify Cookie Banner Behavior

- [ ] Open browser in incognito mode
- [ ] Navigate to `http://localhost:5173`
- [ ] Cookie banner appears on first visit
- [ ] Banner displays Accept/Reject/Customize buttons
- [ ] Clicking "Accept All" hides the banner
- [ ] Consent saved to localStorage
- [ ] Reloading page does not show banner again

### Step 4: Verify Backend API Integration

- [ ] Grant consent via cookie banner or ConsentManager
- [ ] Open browser DevTools → Network tab
- [ ] POST request sent to `/api/consent/` or `/api/cookie-consent/`
- [ ] Request contains consent data (consent_type, granted, consent_text)
- [ ] Response status is 201 or 200
- [ ] No error messages in browser console

### Step 5: Verify Database Records

- [ ] Access PostgreSQL database
- [ ] Query consent_records table:
  ```sql
  SELECT * FROM consent_records ORDER BY created_at DESC LIMIT 5;
  ```
- [ ] Records exist for granted consents
- [ ] Records contain: consent_type, granted, user_id, ip_address, created_at
- [ ] No null values in required fields

### Step 6: Verify ConsentManager Component

- [ ] Navigate to `http://localhost:5173/settings/privacy`
- [ ] Privacy settings page loads successfully
- [ ] "Consent Management" tab is visible
- [ ] Click tab to open ConsentManager
- [ ] All 13 consent types are displayed
- [ ] Toggle switches work correctly
- [ ] Consent status indicators are accurate

### Step 7: Verify Consent Granting via ConsentManager

- [ ] Find a consent type that is not granted (switch is off)
- [ ] Click the toggle switch
- [ ] Switch turns on (visual feedback)
- [ ] No error messages displayed
- [ ] Check Network tab for API call
- [ ] Verify database record created

### Step 8: Verify Consent Revocation

- [ ] Find a consent type that is granted (switch is on)
- [ ] Click toggle switch to revoke
- [ ] Confirmation dialog appears
- [ ] Dialog contains warning message
- [ ] Click "Confirm" button
- [ ] Switch turns off
- [ ] Success message displayed
- [ ] Check Network tab for revocation API call
- [ ] Verify database record updated (withdrawn_at not null)

### Step 9: Verify Consent Persistence

- [ ] Grant or revoke consent
- [ ] Close browser tab
- [ ] Reopen browser and navigate to privacy settings
- [ ] Previous consent decisions are preserved
- [ ] ConsentManager shows correct consent states
- [ ] No data loss across sessions

### Step 10: Mobile Responsive Testing

- [ ] Open browser DevTools and enable mobile emulation
- [ ] Set viewport to mobile size (e.g., 375x667)
- [ ] Refresh page
- [ ] Cookie banner displays correctly on mobile
- [ ] Privacy settings page is responsive
- [ ] ConsentManager is usable on mobile
- [ ] All buttons and switches are tappable
- [ ] No layout issues or horizontal scrolling

## Expected Results

### Success Criteria

✅ All 18 automated tests pass
✅ Cookie banner displays on first visit
✅ Banner hides after consent decision
✅ Consent saved to localStorage
✅ Consent sent to backend API
✅ Consent record created in database
✅ Consent visible in ConsentManager
✅ Can grant new consents via ConsentManager
✅ Can revoke existing consents with confirmation
✅ Revocation sent to backend API
✅ Revocation recorded in database
✅ Consent persists across sessions
✅ Works correctly on mobile devices
✅ No console errors
✅ No backend errors

### Error Handling

❌ Backend API down:
   - User-friendly error message displayed
   - Application continues to function
   - Manual retry option available

❌ Network timeout:
   - Timeout message shown
   - Retry option available
   - UI state preserved

❌ Invalid data:
   - Validation before API call
   - Clear error message
   - No application crash

## Test Results

### Automated Test Results

- **Total Tests**: 18
- **Passed**: _____
- **Failed**: _____
- **Skipped**: _____
- **Duration**: _____
- **Test Report**: `playwright-report/index.html`

### Manual Verification Results

- [ ] Cookie banner: PASSED / FAILED
- [ ] Consent granting: PASSED / FAILED
- [ ] Backend API: PASSED / FAILED
- [ ] Database records: PASSED / FAILED
- [ ] ConsentManager: PASSED / FAILED
- [ ] Consent revocation: PASSED / FAILED
- [ ] Data persistence: PASSED / FAILED
- [ ] Mobile responsive: PASSED / FAILED

### Overall Status

- [ ] **PASSED** - All verification steps completed successfully
- [ ] **FAILED** - Some verification steps failed (see notes below)

### Notes

_(Document any issues, errors, or observations during testing)_

## Next Steps

If verification is successful:

1. ✅ Mark subtask-7-1 as completed in implementation_plan.json
2. ✅ Commit changes with message:
   ```
   git add .
   git commit -m "auto-claude: subtask-7-1 - Test end-to-end consent flow from cookie banner to database"
   ```
3. ✅ Update build-progress.txt with test results
4. ✅ Proceed to next subtask (subtask-7-2: Test data deletion request flow)

If verification failed:

1. ❌ Document issues in notes section
2. ❌ Fix identified issues
3. ❌ Re-run verification
4. ❅ Do not commit until all tests pass

## Troubleshooting

### Cookie Banner Not Appearing

**Solution**:
```javascript
// Clear localStorage
localStorage.clear();
// Reload page
location.reload();
```

### Tests Failing

**Common causes**:
- Backend API not running
- Frontend dev server not running
- Database migrations not applied
- Browser not installed or not in Playwright path

**Solutions**:
```bash
# Check backend
curl http://localhost:8000/api/consent/

# Check frontend
curl http://localhost:5173

# Run migrations
cd backend && alembic upgrade head

# Install Playwright browsers
npx playwright install chromium
```

### Database Issues

**Check database connection**:
```bash
cd backend
python -c "from database import engine; print(engine.url)"
```

**Check tables exist**:
```sql
\dt consent_records
\dt cookie_consent
```

## References

- Test File: `frontend/e2e/gdpr-consent-flow.spec.ts`
- Test Documentation: `frontend/e2e/TEST_GDPR_CONSENT_FLOW.md`
- Test Runner: `frontend/scripts/test-gdpr-consent-flow.sh`
- Implementation Plan: `.auto-claude/specs/072-gdpr-and-data-privacy-compliance/implementation_plan.json`

---

**Verification Completed By**: _______________
**Date**: _______________
**Status**: ✅ PASSED / ❌ FAILED
