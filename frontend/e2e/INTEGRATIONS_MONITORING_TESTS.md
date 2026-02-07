# Integration Monitoring Dashboard Verification Tests

## Overview

This document describes the comprehensive E2E test suite for verifying that monitoring dashboards correctly display integration status, sync metrics, and error information.

## Test Location

**File**: `frontend/e2e/integrations-monitoring.spec.ts`

## Test Coverage

### 1. Integration Health Status Display

**Tests**:
- ✅ `should display integration health status for all integrations`
- ✅ `should display correct status colors and icons`
- ✅ `should display platform badges for each integration`

**Verifies**:
- Integration status badges are visible (Active, Inactive, Error, Pending)
- Status indicators use correct colors and icons:
  - Green/Success for Active status
  - Gray/Default for Inactive status
  - Red/Error for Error status
  - Yellow/Warning for Pending status
- Platform badges (Workday, Greenhouse, Lever, BambooHR, Ashby) are displayed
- Status badges contain Material-UI icons

### 2. Sync Metrics Display

**Tests**:
- ✅ `should display sync metrics in the dashboard`
- ✅ `should display last sync timestamps`
- ✅ `should display sync duration metrics`

**Verifies**:
- Last Sync column shows timestamps for recent syncs
- Sync Status column shows current sync state (in_progress, completed, failed)
- Sync duration is displayed (in seconds or human-readable format)
- Records processed counts are visible
- Sync history is accessible for detailed metrics

### 3. Recent Sync Errors Display

**Tests**:
- ✅ `should display recent sync errors when they exist`
- ✅ `should show error details for failed syncs`

**Verifies**:
- Failed syncs are highlighted with error badges
- Error messages are visible and descriptive
- Error details are accessible via click/tap
- Error information includes:
  - Error type (authentication, network, timeout, etc.)
  - Error message
  - Timestamp of failure
  - Retry options

### 4. Sync History and Details

**Tests**:
- ✅ `should allow viewing detailed sync history`
- ✅ `should show sync history with filtering options`

**Verifies**:
- Sync history dialog opens when clicking History button
- History table shows:
  - Sync timestamp
  - Sync status (pending, running, completed, failed)
  - Records processed count
  - Duration
  - Error details (if failed)
- Filter options available (by status, date range)
- Pagination for large history sets

### 5. Real-time Updates

**Tests**:
- ✅ `should auto-refresh integration status`
- ✅ `should show loading state during sync operations`

**Verifies**:
- Dashboard auto-refreshes status (if enabled)
- Manual refresh button available and functional
- Loading indicators shown during sync operations
- Status updates reflect in real-time

### 6. Integration Statistics

**Tests**:
- ✅ `should show integration statistics summary`

**Verifies**:
- Total integrations count
- Active integrations count
- ATS vs HRIS breakdown
- Recent sync success rate

### 7. Empty States

**Tests**:
- ✅ `should display helpful message when no integrations configured`
- ✅ `should display helpful message when no sync history`

**Verifies**:
- Helpful empty state message when no integrations exist
- Call-to-action button to add first integration
- Helpful message when integration has no sync history
- Clear instructions for next steps

## Running the Tests

### Prerequisites

1. Backend API server running on `http://localhost:8000`
2. Frontend dev server running on `http://localhost:5173`
3. Test data available (integrations configured)

### Run All Monitoring Tests

```bash
cd frontend
npm run test:e2e integrations-monitoring
```

### Run Specific Test Suite

```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --grep "should display integration health status"
```

### Run with UI Mode

```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --ui
```

### Run with Debugging

```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --debug
```

### Run Headed (Show Browser)

```bash
cd frontend
npx playwright test integrations-monitoring.spec.ts --headed
```

## Test Data Setup

### Option 1: Use Existing Integrations

Tests will work with integrations already configured in your development database.

### Option 2: Seed Test Data

Create test integrations via the UI or API:

```bash
# Create active Greenhouse integration
curl -X POST http://localhost:8000/api/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Active Greenhouse Integration",
    "platform": "greenhouse",
    "status": "active",
    "config": {
      "api_key": "test_key"
    }
  }'

# Create Workday integration (will show as syncing)
curl -X POST http://localhost:8000/api/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Syncing Workday Integration",
    "platform": "workday",
    "status": "active",
    "config": {
      "tenant_url": "https://wd1.myworkday.com"
    }
  }'
```

## Expected Results

### Successful Test Run

All tests should pass with:
- ✅ Integration health status visible
- ✅ Sync metrics display correctly
- ✅ Recent sync errors shown
- ✅ Sync history accessible
- ✅ Real-time updates working
- ✅ Empty states handled gracefully

### Common Issues and Solutions

#### Issue: "No integrations found" when tests expect data

**Solution**: Create test integrations using the seed scripts above or via the UI at `/integrations`.

#### Issue: "Sync history dialog doesn't open"

**Solution**: Ensure the History button is present in the integration table and the dialog component is properly mounted.

#### Issue: "Status badges not visible"

**Solution**: Check that `data-testid="integration-status-badge"` or `.MuiChip-root` selectors match your component structure.

#### Issue: "Tests timeout waiting for elements"

**Solution**: Increase timeouts in test configuration or ensure backend API responds quickly.

## Verification Checklist

After running tests, verify the following manually:

### Integration Health Status

- [ ] Navigate to `/integrations`
- [ ] Verify each integration shows a status badge (Active, Inactive, Error, Pending)
- [ ] Check status badges use appropriate colors (green, gray, red, yellow)
- [ ] Verify status icons are visible
- [ ] Check platform badges are displayed (Workday, Greenhouse, etc.)

### Sync Metrics

- [ ] Verify "Last Sync" column shows timestamps or "Never"
- [ ] Check "Sync Status" column shows current state
- [ ] Click History button for an integration
- [ ] Verify sync history dialog opens
- [ ] Check history shows: Date/Time, Status, Records, Duration
- [ ] Verify sync duration is formatted correctly (e.g., "2m 34s" or "154s")

### Sync Errors

- [ ] If any syncs failed, verify error badge is visible
- [ ] Click on failed sync status
- [ ] Verify error details are shown
- [ ] Check error message is descriptive
- [ ] Verify retry button or action is available

### Real-time Updates

- [ ] Trigger a manual sync via the UI
- [ ] Verify sync status changes to "Syncing" or "In Progress"
- [ ] Check that loading indicator appears
- [ ] Wait for sync to complete
- [ ] Verify status updates to "Completed" or "Failed"
- [ ] Check that last sync timestamp is updated

### Empty States

- [ ] If no integrations exist, verify empty state message is shown
- [ ] Check "Add Integration" button is visible and functional
- [ ] If integration has no sync history, verify appropriate message is shown

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Monitoring Tests

on:
  pull_request:
    paths:
      - 'frontend/src/pages/IntegrationsPage.tsx'
      - 'frontend/src/components/SyncHistory.tsx'
      - 'backend/api/integrations.py'

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    services:
      backend:
        image: agenthr-backend:latest
        ports:
          - 8000:8000

      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: agenthr_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright browsers
        run: |
          cd frontend
          npx playwright install --with-deps

      - name: Seed test data
        run: |
          python scripts/seed_test_integrations.py

      - name: Run monitoring tests
        run: |
          cd frontend
          npm run test:e2e integrations-monitoring

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Test Metrics and KPIs

### Coverage Metrics

- **Integration Status Tests**: 3 tests
- **Sync Metrics Tests**: 3 tests
- **Error Display Tests**: 2 tests
- **Sync History Tests**: 2 tests
- **Real-time Updates Tests**: 2 tests
- **Statistics Tests**: 1 test
- **Empty State Tests**: 2 tests

**Total**: 15 test cases

### Success Criteria

- All tests pass: ✅ 15/15
- Test execution time: < 2 minutes
- Flaky test rate: < 5%
- Test reliability: > 95%

## Related Documentation

- [Integrations E2E Tests](./INTEGRATIONS_TESTS.md) - Complete integration workflow tests
- [Error Handling Tests](./ERROR_HANDLING_TESTS.md) - Error recovery and retry logic tests
- [Webhook Testing](./WEBHOOK_TESTING.md) - Webhook reception and processing tests
- [Manual Test Checklist](./MANUAL_TEST_CHECKLIST.md) - Manual verification checklist

## Maintenance Notes

### When to Update Tests

1. **UI Changes**: Update selectors when component structure changes
2. **New Metrics**: Add tests for new sync metrics or status indicators
3. **New Platforms**: Add platform badges and tests for new integrations
4. **Dashboard Updates**: Update tests when monitoring dashboard layout changes

### Test Best Practices

1. Use `data-testid` attributes for stable selectors
2. Wait for network idle before asserting
3. Handle both "has data" and "no data" scenarios
4. Provide helpful error messages in assertions
5. Clean up test data after tests run
6. Use page object model for common actions

### Troubleshooting

**Tests are flaky**:
- Increase wait times
- Use more specific selectors
- Check for race conditions with auto-refresh

**Tests timeout**:
- Increase Playwright timeout
- Check backend performance
- Verify network conditions

**Tests fail in CI but pass locally**:
- Check for environment differences
- Ensure test data is seeded in CI
- Verify database migrations are run
- Check for hardcoded URLs or localhost assumptions

## Support and Contact

For issues or questions about these tests:
1. Check this documentation first
2. Review test failure logs and screenshots
3. Check related documentation files
4. Consult the development team

## Changelog

### v1.0.0 (2026-02-03)
- Initial test suite created
- 15 test cases covering all monitoring aspects
- Comprehensive documentation
- CI/CD integration examples
