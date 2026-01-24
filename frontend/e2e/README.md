# E2E Tests with Playwright

This directory contains end-to-end tests for the Resume Analysis Platform using Playwright.

## Test Coverage

The E2E test suite (`resume-analysis.spec.ts`) covers:

### 1. Navigation & Page Rendering
- Home page loads with all elements
- Navigation between pages works
- Unknown routes redirect properly
- App bar navigation links function

### 2. Resume Upload Workflow
- Upload component displays correctly
- Drag-drop area is visible
- File format validation (PDF/DOCX only)
- File size limits shown
- Invalid file types rejected

### 3. Analysis Results Display
- Results page renders for valid IDs
- Loading states display
- Error states handled gracefully
- Navigation between upload/results works

### 4. Job Comparison Workflow
- Comparison page displays with required IDs
- Missing parameters handled correctly

### 5. Complete User Journeys
- Full workflow: Home → Upload → Results
- Job comparison flow
- Multi-page navigation

### 6. Responsive Design
- Mobile viewport (375x667)
- Tablet viewport (768x1024)
- Desktop viewport

### 7. Accessibility
- Heading hierarchy (h1, h2, h3)
- Image alt text
- Keyboard navigation
- Color contrast (basic check)

### 8. Performance
- Page load time < 3 seconds
- No memory leaks during navigation

### 9. Error Handling
- Network errors handled gracefully
- Malformed URLs handled
- Invalid resume IDs handled

### 10. Content Validation
- Correct text on all pages
- Instructions displayed properly

## Prerequisites

Before running E2E tests, ensure:

1. **Backend API is running** at `http://localhost:8000`
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Frontend dev server is running** at `http://localhost:5173`
   ```bash
   cd frontend
   npm run dev
   ```

3. **Playwright browsers are installed**
   ```bash
   npm run test:e2e:install
   ```

## Installation

First, install dependencies:
```bash
cd frontend
npm install
```

Install Playwright browsers:
```bash
npm run test:e2e:install
```

## Running Tests

### Run all E2E tests
```bash
npm run test:e2e
```

### Run tests in UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run tests in debug mode
```bash
npm run test:e2e:debug
```

### Run tests on specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run specific test file
```bash
npx playwright test resume-analysis.spec.ts
```

### Run specific test(s) by name
```bash
npx playwright test -g "should load home page"
```

## Test Results

After running tests:

- **HTML Report**: `test-results/results.html` (visual report with screenshots)
- **JSON Report**: `test-results/e2e-results.json` (machine-readable)
- **Screenshots**: `test-results/` (on failure)
- **Traces**: `test-results/traces/` (on retry)

View HTML report:
```bash
npx playwright show-report
```

## Configuration

Playwright is configured in `playwright.config.ts`:

- **Base URL**: `http://localhost:5173` (override with `BASE_URL` env var)
- **Browsers**: Chromium, Firefox, WebKit
- **Timeouts**: Default 30s, element action 10s
- **Retries**: 0 locally, 2 in CI
- **Parallelization**: Fully parallel (multi-threaded)

### Testing Different Environments

Test staging environment:
```bash
BASE_URL=https://staging.example.com npm run test:e2e
```

Test production:
```bash
BASE_URL=https://example.com npm run test:e2e
```

## Writing New Tests

When adding new E2E tests, follow this pattern:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/test-page');
  });

  test('should do something specific', async ({ page }) => {
    // Arrange: Set up test conditions
    const button = page.getByRole('button', { name: 'Submit' });

    // Act: Perform action
    await button.click();

    // Assert: Verify outcome
    await expect(page.getByText('Success')).toBeVisible();
  });
});
```

### Best Practices

1. **Use locators, not selectors**
   ```typescript
   // Good
   page.getByRole('button', { name: 'Submit' })
   page.getByText('Welcome')
   page.getByTestId('submit-button')

   // Avoid
   page.locator('.btn-submit')
   page.$('#submit')
   ```

2. **Wait for elements properly**
   ```typescript
   // Good - waits automatically
   await expect(page.getByText('Loaded')).toBeVisible();

   // Avoid - manual waits
   await page.waitForTimeout(1000);
   ```

3. **Test user behavior, not implementation**
   ```typescript
   // Good - tests what user sees
   await page.getByRole('button', { name: 'Upload' }).click();

   // Avoid - tests React internals
   await page.evaluate(() => {
     window.store.dispatch(uploadFile());
   });
   ```

4. **Use data-testid for complex selectors**
   ```tsx
   // In React component
   <button data-testid="submit-button">Submit</button>

   // In test
   await page.getByTestId('submit-button').click();
   ```

## Debugging Failed Tests

### View traces
```bash
npx playwright show-trace test-results/traces/[test-name].zip
```

### View screenshots
Check `test-results/` directory for screenshots taken on failure.

### Run in headed mode
```bash
npx playwright test --headed
```

### Run in debug mode with inspector
```bash
npx playwright test --debug
```

### Slow motion execution
```bash
npx playwright test --slow-mo=1000
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run test:e2e:install
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: test-results/
```

## Troubleshooting

### Tests fail with "Target closed"
- Backend API not running
- Frontend dev server not running
- Wrong port configured

### Tests timeout
- Increase timeout in `playwright.config.ts`
- Backend API too slow
- Network issues

### Element not found
- Wait for element to be visible
- Use `waitForSelector()` before acting
- Check if element is in iframe or shadow DOM

### Flaky tests
- Add proper waits for async operations
- Use `waitForResponse()` for API calls
- Disable parallel execution if tests interfere

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright Locator Strategies](https://playwright.dev/docs/locators)
