# Integrations E2E Tests

## Overview

This document describes the end-to-end tests for HRIS/ATS platform integrations, which verify the complete workflow for managing external platform connections (Workday, Greenhouse, Lever, BambooHR, Ashby).

## Test File

- **Location**: `frontend/e2e/integrations.spec.ts`
- **Framework**: Playwright
- **Coverage**: Complete integration lifecycle from creation to deletion

## Test Suites

### 1. Page Navigation
- ✅ Display integrations page
- ✅ Show add integration button
- ✅ Navigate from other pages to integrations

### 2. Create Integration
- ✅ Open integration config dialog
- ✅ Display platform options (Workday, Greenhouse, Lever, BambooHR, Ashby)
- ✅ Show platform-specific credential fields
- ✅ Validate integration form fields
- ✅ Create integration with valid data

### 3. Test Connection
- ✅ Have test connection button for integrations
- ✅ Test connection successfully
- ✅ Show loading state during connection test

### 4. Trigger Sync
- ✅ Have sync button for integrations
- ✅ Trigger manual sync
- ✅ Show sync status after triggering

### 5. Sync History
- ✅ Have view history button
- ✅ Open sync history dialog
- ✅ Display sync status badges
- ✅ Show sync details in history

### 6. Edit Integration
- ✅ Have edit button for integrations
- ✅ Open edit dialog with pre-filled data
- ✅ Update integration name

### 7. Delete Integration
- ✅ Have delete button for integrations
- ✅ Show confirmation dialog before delete
- ✅ Cancel delete when cancel clicked

### 8. Complete Workflow
- ✅ Complete full integration lifecycle (create → test → sync → view history)

### 9. Mobile Responsive
- ✅ Display properly on mobile
- ✅ Show add button on mobile
- ✅ Open integration dialog on mobile

### 10. Error Handling
- ✅ Handle network errors gracefully
- ✅ Show error message for invalid credentials

### 11. Accessibility
- ✅ Have proper heading hierarchy
- ✅ Be keyboard navigable
- ✅ Have ARIA labels on buttons

## Running the Tests

### Prerequisites

1. **Backend API** running at `http://localhost:8000`
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Frontend dev server** running at `http://localhost:5173`
   ```bash
   cd frontend
   npm run dev
   ```

3. **Install Playwright browsers** (first time only)
   ```bash
   cd frontend
   npm run test:e2e:install
   ```

### Run All Tests

```bash
cd frontend
npm run test:e2e
```

### Run Tests in UI Mode

```bash
cd frontend
npm run test:e2e:ui
```

### Run Tests in Debug Mode

```bash
cd frontend
npm run test:e2e:debug
```

### Run Only Integration Tests

```bash
cd frontend
npx playwright test integrations.spec.ts
```

### Run Specific Test Suite

```bash
cd frontend
npx playwright test integrations.spec.ts --grep "Create Integration"
```

## Test Credentials

The tests use mock/test credentials defined in the test file:

```typescript
const TEST_CREDENTIALS = {
  workday: {
    api_url: 'https://wd1.workday.com',
    username: 'test@example.com',
    password: 'test-password-123',
    tenant_name: 'test_tenant',
  },
  greenhouse: {
    api_key: 'test-greenhouse-api-key',
  },
  // ... etc
};
```

**Note**: These are test credentials only. For production testing with real APIs, set environment variables:

```bash
export WORKDAY_API_URL="https://your-company.workday.com"
export WORKDAY_USERNAME="your-email@company.com"
export WORKDAY_PASSWORD="your-password"
# ... etc
```

## Expected Test Results

### With Backend Running

- ✅ All UI navigation tests pass
- ✅ Form validation works
- ✅ Integration creation succeeds (or fails gracefully with real API)
- ✅ Connection test shows loading and result
- ✅ Sync trigger queues background task
- ✅ Sync history displays records

### Without Backend (Frontend Only)

- ✅ UI navigation tests pass
- ✅ Form validation works
- ⚠️ Integration creation may fail with network errors (expected)
- ⚠️ Connection test may fail (expected)
- ⚠️ Sync operations may fail (expected)

## CI/CD Integration

The tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: npm ci

- name: Install Playwright browsers
  run: npm run test:e2e:install

- name: Start backend
  run: |
    cd backend
    uvicorn main:app &
    sleep 10

- name: Start frontend
  run: |
    cd frontend
    npm run dev &
    sleep 10

- name: Run E2E tests
  run: |
    cd frontend
    npm run test:e2e

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/playwright-report/
```

## Test Data Cleanup

Tests create integrations with names like:
- `E2E Test Integration - Workday`
- `E2E Full Workflow Test`

**Important**: Clean up test data after running tests:

```bash
# Via API
curl -X DELETE http://localhost:8000/api/integrations/{integration_id}

# Or via database
cd backend
python -c "
from database import SessionLocal
from models.integration import Integration
db = SessionLocal()
db.query(Integration).filter(Integration.name.like('E2E%')).delete(synchronize_session=False)
db.commit()
"
```

## Troubleshooting

### Tests fail with "Network error"

- Verify backend is running on port 8000
- Check CORS settings in backend
- Ensure frontend dev server is running on port 5173

### Tests timeout

- Increase timeout in playwright.config.ts
- Check if backend API is responding slowly
- Verify network connectivity

### Tests skip with "No integrations found"

- Tests gracefully skip when no integrations exist
- Create test data first, or adjust tests to create data
- Check backend database has test data

### Dialog not found

- Ensure Material-UI components are rendered
- Check for JavaScript errors in browser console
- Verify Playwright waiting long enough for async operations

## Maintenance

When adding new integration platforms:

1. Add test credentials to `TEST_CREDENTIALS`
2. Add platform-specific validation tests
3. Update expected field names in tests
4. Add platform to platform selection test
5. Run full test suite to verify

## Related Files

- `frontend/src/pages/IntegrationsPage.tsx` - Main integrations UI
- `frontend/src/components/IntegrationConfig.tsx` - Integration form
- `frontend/src/components/SyncHistory.tsx` - Sync history UI
- `frontend/src/api/integrations.ts` - API client
- `backend/api/integrations.py` - Backend endpoints
- `backend/tasks/sync_tasks.py` - Background sync tasks
