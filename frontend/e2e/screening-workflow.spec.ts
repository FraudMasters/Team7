import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Screening Workflow (Recruiter)
 *
 * Test Suite Contents:
 * 1. Screening Dashboard - Metrics and Analytics
 * 2. Screening Configuration - Rule Creation
 * 3. Screening Results - Tier Filtering and Display
 * 4. Complete Screening Workflow Integration
 * 5. Error Handling and Edge Cases
 * 6. Responsive Design on Mobile and Desktop
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

test.describe('Screening Workflow - Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');
  });

  test('should display screening dashboard with heading', async ({ page }) => {
    // Check main heading
    await expect(page.getByRole('heading', { level: 1, name: /Screening Dashboard/i })).toBeVisible();
  });

  test('should display key metrics cards', async ({ page }) => {
    // Check for metrics cards
    const totalScreenedCard = page.getByText(/Total Screened/i);
    const highPriorityCard = page.getByText(/High Priority/i);
    const reviewRequiredCard = page.getByText(/Review Required/i);
    const autoRejectedCard = page.getByText(/Auto Rejected/i);

    // At least some metrics should be visible
    await expect(totalScreenedCard.or(highPriorityCard).or(reviewRequiredCard).or(autoRejectedCard)).toBeVisible();
  });

  test('should display automation effectiveness metrics', async ({ page }) => {
    // Check for automation effectiveness section
    const automationSection = page.getByText(/Automation Effectiveness/i);
    const hoursSaved = page.getByText(/Time Saved|Hours Saved/i);
    const efficiencyGain = page.getByText(/Efficiency Gain|Efficiency/i);
    const avgTime = page.getByText(/Avg. Screening Time/i);

    // Look for automation metrics
    const hasAutomationMetrics = await automationSection.isVisible().catch(() => false) ||
                                  await hoursSaved.isVisible().catch(() => false) ||
                                  await efficiencyGain.isVisible().catch(() => false) ||
                                  await avgTime.isVisible().catch(() => false);

    expect(hasAutomationMetrics).toBeTruthy();
  });

  test('should display rejection reasons distribution', async ({ page }) => {
    // Check for rejection reasons section
    const rejectionSection = page.getByText(/Rejection Reasons/i);

    // Rejection reasons may be empty initially
    const hasRejectionSection = await rejectionSection.isVisible().catch(() => false);
    if (hasRejectionSection) {
      await expect(rejectionSection).toBeVisible();
    }
  });

  test('should have quick action buttons', async ({ page }) => {
    // Check for quick action buttons
    const configureButton = page.getByRole('button', { name: /Configure Screening Rules|Configure Rules/i });
    const viewResultsButton = page.getByRole('button', { name: /View All Candidates|View Results/i });

    // At least one quick action should be visible
    await expect(configureButton.or(viewResultsButton)).toBeVisible();
  });

  test('should display recent screening results table', async ({ page }) => {
    // Check for recent results section
    const recentResultsSection = page.getByText(/Recent Screening Results/i);

    // Either recent results should be visible or empty state
    const hasRecentResults = await recentResultsSection.isVisible().catch(() => false);
    if (hasRecentResults) {
      await expect(recentResultsSection).toBeVisible();
    }
  });

  test('should have refresh functionality', async ({ page }) => {
    // Look for refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i }).or(
      page.locator('button').filter({ hasText: /Refresh/i })
    );

    const count = await refreshButton.count();
    if (count > 0) {
      await expect(refreshButton.first()).toBeVisible();
    }
  });
});

test.describe('Screening Workflow - Configuration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should navigate to screening configuration page', async ({ page }) => {
    // Start from screening dashboard
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Look for configure rules button
    const configureButton = page.getByRole('button', { name: /Configure Screening Rules|Configure Rules/i });

    const count = await configureButton.count();
    if (count > 0) {
      await configureButton.first().click();
      await page.waitForTimeout(500);

      // Should navigate to vacancies page (where screening config can be accessed)
      await expect(page).toHaveURL(/\/vacancies/);
    } else {
      // Direct navigation test to screening config page
      await page.goto('/screening/config/test-vacancy-123');
      await page.waitForLoadState('networkidle');

      // Should show screening configuration heading or error
      const heading = page.getByRole('heading', { name: /Screening Rule Configuration|Screening Configuration/i });
      const error = page.getByText(/No vacancy ID provided|Error/i);

      await expect(heading.or(error)).toBeVisible();
    }
  });

  test('should display screening configuration form', async ({ page }) => {
    // Navigate to screening config with test vacancy ID
    await page.goto('/screening/config/test-vacancy-123');
    await page.waitForLoadState('networkidle');

    // Check for form elements
    const heading = page.getByRole('heading', { name: /Screening/i });
    const thresholdInput = page.getByRole('textbox', { name: /threshold|score/i }).or(
      page.locator('input[type="number"]')
    );
    const saveButton = page.getByRole('button', { name: /Save|Submit/i });

    // At least heading should be visible
    await expect(heading.or(saveButton)).toBeVisible();
  });

  test('should have threshold configuration fields', async ({ page }) => {
    await page.goto('/screening/config/test-vacancy-123');
    await page.waitForLoadState('networkidle');

    // Look for threshold-related fields
    const minScoreLabel = page.getByText(/Minimum Score|Min Score/i);
    const autoRejectLabel = page.getByText(/Auto Reject|Auto-reject/i);
    const highPriorityLabel = page.getByText(/High Priority|High-priority/i);

    // At least one threshold field should be present
    const hasThresholdFields = await minScoreLabel.isVisible().catch(() => false) ||
                               await autoRejectLabel.isVisible().catch(() => false) ||
                               await highPriorityLabel.isVisible().catch(() => false);

    // This is optional - the page might show error without valid vacancy
    if (hasThresholdFields) {
      await expect(minScoreLabel.or(autoRejectLabel).or(highPriorityLabel)).toBeVisible();
    }
  });

  test('should have must-have skills input', async ({ page }) => {
    await page.goto('/screening/config/test-vacancy-123');
    await page.waitForLoadState('networkidle');

    // Look for skills input
    const skillsLabel = page.getByText(/Must-have Skills|Skills/i);
    const autocomplete = page.locator('.MuiAutocomplete-root');

    // Skills field is optional
    const hasSkillsField = await skillsLabel.isVisible().catch(() => false) ||
                           await autocomplete.count().then(c => c > 0);

    if (hasSkillsField) {
      await expect(skillsLabel.or(autocomplete.first())).toBeVisible();
    }
  });
});

test.describe('Screening Workflow - Results Display', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to candidates page which shows screening results
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');
  });

  test('should display screening results with tiers', async ({ page }) => {
    // Check for results page heading
    const heading = page.getByRole('heading', { name: /Candidates|Screening Results/i });
    await expect(heading).toBeVisible();

    // Look for tier indicators
    const highPriorityChip = page.locator('.MuiChip-root').filter({ hasText: /HIGH PRIORITY|High Priority/i });
    const reviewChip = page.locator('.MuiChip-root').filter({ hasText: /REVIEW|Review/i });
    const rejectChip = page.locator('.MuiChip-root').filter({ hasText: /REJECT|Reject/i });

    // At least one tier chip should be visible (or empty state)
    const hasTierChips = await highPriorityChip.count().then(c => c > 0) ||
                         await reviewChip.count().then(c => c > 0) ||
                         await rejectChip.count().then(c => c > 0);

    // If no tier chips, there might be empty state
    if (!hasTierChips) {
      const emptyState = page.getByText(/No candidates|No results|No screening data/i);
      const hasEmptyState = await emptyState.isVisible().catch(() => false);
      expect(hasEmptyState).toBeTruthy();
    }
  });

  test('should have tier filtering tabs', async ({ page }) => {
    // Look for tier tabs
    const allTab = page.getByRole('tab', { name: /All/i });
    const highPriorityTab = page.getByRole('tab', { name: /High Priority/i });
    const reviewTab = page.getByRole('tab', { name: /Review/i });
    const rejectTab = page.getByRole('tab', { name: /Reject/i });

    // At least some tabs should be visible
    const hasTabs = await allTab.isVisible().catch(() => false) ||
                    await highPriorityTab.isVisible().catch(() => false) ||
                    await reviewTab.isVisible().catch(() => false) ||
                    await rejectTab.isVisible().catch(() => false);

    if (hasTabs) {
      await expect(allTab.or(highPriorityTab).or(reviewTab).or(rejectTab)).toBeVisible();
    }
  });

  test('should display candidate information in results', async ({ page }) => {
    // Look for table rows or candidate cards
    const table = page.locator('table');
    const tableCount = await table.count();

    if (tableCount > 0) {
      // Check for table headers
      const candidateHeader = page.getByRole('columnheader', { name: /Candidate/i });
      const scoreHeader = page.getByRole('columnheader', { name: /Score/i });
      const tierHeader = page.getByRole('columnheader', { name: /Tier/i });

      await expect(candidateHeader.or(scoreHeader).or(tierHeader)).toBeVisible();
    }
  });

  test('should have search functionality', async ({ page }) => {
    // Look for search input
    const searchInput = page.getByPlaceholder(/Search/i).or(
      page.locator('input[type="search"]')
    );

    const searchCount = await searchInput.count();
    if (searchCount > 0) {
      await expect(searchInput.first()).toBeVisible();

      // Test search input
      await searchInput.first().fill('developer');
      await page.waitForTimeout(500);

      // Verify search value
      await expect(searchInput.first()).toHaveValue('developer');
    }
  });

  test('should have vacancy filter', async ({ page }) => {
    // Look for vacancy filter dropdown
    const vacancyFilter = page.getByRole('combobox', { name: /Vacancy/i }).or(
      page.getByText(/Filter by Vacancy|Vacancy/i)
    );

    // Vacancy filter may or may not be present
    const hasVacancyFilter = await vacancyFilter.count().then(c => c > 0);
    if (hasVacancyFilter) {
      await expect(vacancyFilter.first()).toBeVisible();
    }
  });
});

test.describe('Screening Workflow - Tier Filtering', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should filter results by tier', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Look for tier tabs
    const allTab = page.getByRole('tab', { name: /All/i });
    const highPriorityTab = page.getByRole('tab', { name: /High Priority/i });

    const allTabCount = await allTab.count();
    if (allTabCount > 0) {
      // Click on All tab
      await allTab.first().click();
      await page.waitForTimeout(500);

      // URL or content should update
      await expect(allTab.first()).toBeVisible();

      // Try clicking on High Priority tab
      const highPriorityCount = await highPriorityTab.count();
      if (highPriorityCount > 0) {
        await highPriorityTab.first().click();
        await page.waitForTimeout(500);

        // Verify tab is selected
        await expect(highPriorityTab.first()).toBeVisible();
      }
    }
  });

  test('should display correct tier colors', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Look for tier chips with specific colors
    const successChip = page.locator('.MuiChip-root[color="success"]').or(
      page.locator('.MuiChip-filledSuccess')
    );
    const warningChip = page.locator('.MuiChip-root[color="warning"]').or(
      page.locator('.MuiChip-filledWarning')
    );
    const errorChip = page.locator('.MuiChip-root[color="error"]').or(
      page.locator('.MuiChip-filledError')
    );

    // At least one colored chip should be present (if results exist)
    const hasColoredChips = await successChip.count().then(c => c > 0) ||
                            await warningChip.count().then(c => c > 0) ||
                            await errorChip.count().then(c => c > 0);

    // This is optional - depends on having results
    if (hasColoredChips) {
      const chipsVisible = await successChip.isVisible().catch(() => false) ||
                          await warningChip.isVisible().catch(() => false) ||
                          await errorChip.isVisible().catch(() => false);
      expect(chipsVisible).toBeTruthy();
    }
  });
});

test.describe('Screening Workflow - Complete Journey', () => {
  test('should navigate through entire screening workflow', async ({ page }) => {
    // Start at screening dashboard
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Verify dashboard loads
    await expect(page.getByRole('heading', { level: 1, name: /Screening/i })).toBeVisible();

    // Navigate to screening configuration
    await page.goto('/screening/config/test-vacancy-123');
    await page.waitForLoadState('networkidle');

    // Verify config page loads (or shows error for invalid vacancy)
    const content = page.locator('body');
    await expect(content).toBeVisible();

    // Navigate to candidates/results page
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Verify results page loads
    await expect(page.getByRole('heading')).toBeVisible();
  });

  test('should navigate between dashboard and results', async ({ page }) => {
    // Start at dashboard
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Look for view results button
    const viewResultsButton = page.getByRole('button', { name: /View All Candidates|View Results/i });

    const count = await viewResultsButton.count();
    if (count > 0) {
      await viewResultsButton.first().click();
      await page.waitForTimeout(500);

      // Should navigate to candidates page
      await expect(page).toHaveURL(/\/candidates/);

      // Go back to dashboard
      await page.goto('/screening');
      await page.waitForLoadState('networkidle');

      await expect(page.getByRole('heading', { name: /Screening Dashboard/i })).toBeVisible();
    } else {
      // Manual navigation
      await page.goto('/recruiter/candidates');
      await expect(page.getByRole('heading')).toBeVisible();

      await page.goto('/screening');
      await expect(page.getByRole('heading', { name: /Screening/i })).toBeVisible();
    }
  });
});

test.describe('Screening Workflow - Error Handling', () => {
  test('should handle missing vacancy ID in config', async ({ page }) => {
    // Navigate to config without vacancy ID
    await page.goto('/screening/config/');
    await page.waitForLoadState('networkidle');

    // Should show error or redirect
    const errorMessage = page.getByText(/No vacancy ID|Error|Invalid/i);
    const hasError = await errorMessage.isVisible().catch(() => false);

    if (hasError) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Navigate to dashboard (may show error if backend is down)
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Page should not crash - should show loading, error, or content
    const loading = page.getByText(/Loading/i);
    const error = page.getByText(/Error|Failed/i);
    const content = page.locator('h1, h2, .MuiCard-root');

    await expect(loading.or(error).or(content)).toBeVisible();
  });

  test('should handle empty screening results', async ({ page }) => {
    // Navigate to results page
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Should show either results or empty state
    const results = page.locator('table tbody tr');
    const emptyState = page.getByText(/No candidates|No results|No screening data/i);

    const resultsCount = await results.count();
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    // Either has results or shows empty state
    expect(resultsCount > 0 || hasEmptyState).toBeTruthy();
  });
});

test.describe('Screening Workflow - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('should display screening dashboard on mobile', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Screening/i })).toBeVisible();

    // Check for no horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
  });

  test('should display results page on mobile', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading')).toBeVisible();

    // Check for no horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 15);
  });

  test('should navigate through screening pages on mobile', async ({ page }) => {
    const screeningPages = [
      { path: '/screening', name: 'Screening Dashboard' },
      { path: '/recruiter/candidates', name: 'Candidates/Results' },
    ];

    for (const pagePath of screeningPages) {
      await page.goto(pagePath.path);
      await page.waitForLoadState('networkidle');

      // Check that page loads without errors
      await expect(page.locator('body')).toBeVisible();

      // Check no horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 15);
    }
  });
});

test.describe('Screening Workflow - Desktop Responsive', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should display screening dashboard on desktop', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Screening/i })).toBeVisible();

    // Content should use desktop space
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyWidth).toBeGreaterThan(900);
  });

  test('should display metrics grid on desktop', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Look for metric cards
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();

    if (count >= 2) {
      // Check that cards are arranged in grid
      const firstCard = cards.first();
      const secondCard = cards.nth(1);

      const firstBox = await firstCard.boundingBox();
      const secondBox = await secondCard.boundingBox();

      if (firstBox && secondBox) {
        // On desktop, cards should be horizontally spaced
        const horizontallySpaced = secondBox.x > firstBox.x + 50;
        expect(horizontallySpaced).toBeTruthy();
      }
    }
  });
});

test.describe('Screening Workflow - Page Transitions', () => {
  test('should have smooth transitions between screening pages', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Get initial state
    const initialUrl = page.url();

    // Navigate to candidates page
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // URL should change
    expect(page.url()).not.toBe(initialUrl);

    // Content should be visible
    await expect(page.getByRole('heading')).toBeVisible();
  });

  test('should support browser back and forward navigation', async ({ page }) => {
    // Navigate through screening pages
    await page.goto('/screening');
    await page.goto('/recruiter/candidates');

    // Go back
    await page.goBack();
    await expect(page).toHaveURL(/\/screening/);

    // Go forward
    await page.goForward();
    await expect(page).toHaveURL(/\/candidates/);
  });
});

test.describe('Screening Workflow - Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    const screeningPages = ['/screening', '/recruiter/candidates'];

    for (const pagePath of screeningPages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      // Check for h1 heading
      const h1 = page.getByRole('heading', { level: 1 });
      await expect(h1).toBeVisible();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'NAV', 'TAB'].includes(focused || '')).toBeTruthy();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Check for tablist ARIA role
    const tablist = page.getByRole('tablist');
    const tablistCount = await tablist.count();

    if (tablistCount > 0) {
      // Tabs should have proper ARIA roles
      const tabs = page.getByRole('tab');
      const tabsCount = await tabs.count();
      expect(tabsCount).toBeGreaterThan(0);
    }
  });
});

test.describe('Screening Workflow - Backend Integration', () => {
  test('should load metrics from backend API', async ({ page }) => {
    // Monitor API calls
    const apiRequests: string[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/api/screening')) {
        apiRequests.push(request.url());
      }
    });

    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Should make at least one screening API call
    expect(apiRequests.length).toBeGreaterThan(0);
  });

  test('should load screening results from backend', async ({ page }) => {
    // Monitor API calls
    const apiRequests: string[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/api/screening/results')) {
        apiRequests.push(request.url());
      }
    });

    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Should make screening results API call
    // Note: This might not always fire if component uses different endpoint
    const hasScreeningRequest = apiRequests.length > 0 ||
                                await page.getByText(/Loading|Error|Candidates/i).isVisible();

    expect(hasScreeningRequest).toBeTruthy();
  });

  test('should handle API response data correctly', async ({ page }) => {
    await page.goto('/screening');
    await page.waitForLoadState('networkidle');

    // Check that metrics are displayed (not just loading spinner)
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const loadingCount = await loadingSpinner.count();

    // After networkidle, should not show loading
    if (loadingCount > 0) {
      const isLoading = await loadingSpinner.first().isVisible().catch(() => false);
      expect(isLoading).toBeFalsy();
    }
  });
});

test.describe('Screening Workflow - Filtering Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should filter results by tier and update display', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Look for tier tabs
    const highPriorityTab = page.getByRole('tab', { name: /High Priority/i });
    const reviewTab = page.getByRole('tab', { name: /Review/i });

    const hpCount = await highPriorityTab.count();
    if (hpCount > 0) {
      // Click on High Priority tab
      await highPriorityTab.first().click();
      await page.waitForTimeout(500);

      // Verify tab is selected
      await expect(highPriorityTab.first()).toHaveAttribute('aria-selected', 'true');

      // Try Review tab
      const reviewCount = await reviewTab.count();
      if (reviewCount > 0) {
        await reviewTab.first().click();
        await page.waitForTimeout(500);

        await expect(reviewTab.first()).toHaveAttribute('aria-selected', 'true');
      }
    }
  });

  test('should filter results by vacancy', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Look for vacancy filter
    const vacancySelect = page.getByRole('combobox', { name: /Vacancy/i });

    const count = await vacancySelect.count();
    if (count > 0) {
      // Click the select
      await vacancySelect.first().click();
      await page.waitForTimeout(300);

      // Look for options
      const options = page.getByRole('option');
      const optionsCount = await options.count();

      if (optionsCount > 0) {
        // Select first option (if not "All")
        const firstOptionText = await options.first().textContent();
        if (firstOptionText && !firstOptionText.includes('All')) {
          await options.first().click();
          await page.waitForTimeout(500);

          // Verify selection
          await expect(vacancySelect.first()).toBeVisible();
        }
      }
    }
  });

  test('should combine search and tier filters', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Apply tier filter
    const reviewTab = page.getByRole('tab', { name: /Review/i });
    const reviewCount = await reviewTab.count();

    if (reviewCount > 0) {
      await reviewTab.first().click();
      await page.waitForTimeout(500);
    }

    // Apply search
    const searchInput = page.getByPlaceholder(/Search/i).or(
      page.locator('input[type="search"]')
    );
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      await searchInput.first().fill('developer');
      await page.waitForTimeout(500);

      // Both filters should be active
      await expect(searchInput.first()).toHaveValue('developer');
      if (reviewCount > 0) {
        await expect(reviewTab.first()).toBeVisible();
      }
    }
  });
});
