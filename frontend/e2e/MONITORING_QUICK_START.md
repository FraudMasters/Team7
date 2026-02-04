# Integration Monitoring Tests - Quick Start

## Overview
This test suite verifies that monitoring dashboards correctly display integration status, sync metrics, and errors.

## Files Created
1. **frontend/e2e/integrations-monitoring.spec.ts** (674 lines, 17 tests)
   - E2E tests for integration monitoring dashboard
2. **frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md** (414 lines)
   - Comprehensive documentation
3. **frontend/e2e/verify-monitoring-tests.sh** (executable)
   - Verification script for test infrastructure
4. **frontend/e2e/MONITORING_QUICK_START.md** (this file)
   - Quick reference guide

## Test Coverage Summary

### ✓ Integration Health Status (3 tests)
- Status badges visible for all integrations
- Correct colors and icons for status types
- Platform badges displayed

### ✓ Sync Metrics Display (3 tests)
- Last sync timestamps shown
- Sync duration metrics visible
- Records processed counts

### ✓ Recent Sync Errors (2 tests)
- Failed syncs highlighted with error badges
- Error details accessible via click
- Error messages descriptive

### ✓ Sync History (2 tests)
- Detailed sync history accessible
- History table shows all metrics
- Filter options available

### ✓ Real-time Updates (2 tests)
- Auto-refresh functionality
- Loading states during sync
- Manual refresh button

### ✓ Integration Statistics (1 test)
- Total integrations count
- Active integrations count
- ATS vs HRIS breakdown

### ✓ Empty States (2 tests)
- Helpful message when no integrations
- Clear CTAs for adding integrations
- Empty sync history messaging

### ✓ Platform Badges (1 test)
- Workday, Greenhouse, Lever, BambooHR, Ashby badges
- Proper colors and styling

### ✓ Duration Metrics (1 test)
- Sync duration in history or dashboard
- Human-readable format (e.g., "2m 34s")

## Running the Tests

### Prerequisites
```bash
# Backend running on port 8000
cd backend && python -m uvicorn main:app --reload

# Frontend running on port 5173
cd frontend && npm run dev
```

### Run All Monitoring Tests
```bash
cd frontend
npm run test:e2e integrations-monitoring
```

### Run with UI Mode (Recommended)
```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --ui
```

### Run Specific Test Suite
```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --grep "should display integration health"
```

### Run Headed (Show Browser)
```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --headed
```

### Run with Debugging
```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --debug
```

## Verification Checklist

After tests pass, manually verify:

- [ ] Navigate to `/integrations`
- [ ] Check status badges for each integration (Active, Inactive, Error, Pending)
- [ ] Verify platform badges show correct colors
- [ ] Click "History" button for an integration
- [ ] Verify sync history dialog shows detailed metrics
- [ ] Check "Last Sync" column has timestamps or "Never"
- [ ] Verify "Sync Status" column shows current state
- [ ] If any syncs failed, click to see error details
- [ ] Trigger a manual sync and watch status update
- [ ] Verify loading indicator appears during sync

## Expected Results

### Dashboard View
- Integration list table with status indicators
- Platform badges with proper colors
- Last sync timestamps or "Never"
- Sync status badges (Syncing, Completed, Failed)
- Action buttons (Test, Sync, History, Edit, Delete)

### Sync History Dialog
- Table of sync operations
- Date/time column
- Status badges with colors
- Records processed count
- Duration (human-readable format)
- Error details (for failed syncs)
- Filter controls (if available)

### Status Badge Colors
- **Active**: Green with checkmark icon
- **Inactive**: Gray with schedule icon
- **Error**: Red with error icon
- **Pending**: Yellow with schedule icon
- **Syncing**: Blue with spinner icon

### Empty States
- **No Integrations**: "No integrations configured" + "Add Integration" button
- **No Sync History**: "No sync history available" message

## Troubleshooting

### Tests timeout
- Increase timeout in test configuration
- Check backend API performance
- Verify database is running

### Tests fail to find elements
- Check if backend/frontend are running
- Verify integration data exists
- Check for UI changes (selectors may need updating)

### Tests flaky
- Increase wait times for async operations
- Use more specific selectors
- Check for race conditions with auto-refresh

## Success Criteria

✅ All 17 tests pass
✅ Integration health status visible
✅ Sync metrics display correctly
✅ Recent sync errors shown
✅ Manual verification checklist passes

## Related Documentation

- [INTEGRATIONS_MONITORING_TESTS.md](./INTEGRATIONS_MONITORING_TESTS.md) - Full documentation
- [INTEGRATIONS_TESTS.md](./INTEGRATIONS_TESTS.md) - Integration workflow tests
- [ERROR_HANDLING_TESTS.md](./ERROR_HANDLING_TESTS.md) - Error recovery tests
- [WEBHOOK_TESTING.md](./WEBHOOK_TESTING.md) - Webhook flow tests

## Next Steps

1. Run verification script: `./frontend/e2e/verify-monitoring-tests.sh`
2. Run the E2E tests: `cd frontend && npm run test:e2e integrations-monitoring`
3. Manually verify the dashboard at `/integrations`
4. Check CI/CD integration if needed

## Summary

- **Total Test Cases**: 17
- **Test Suites**: 3
- **Files Created**: 4
- **Lines of Code**: ~1,200
- **Coverage**: Complete integration monitoring dashboard verification

All verification steps from subtask-6-4 are now implemented and documented.
