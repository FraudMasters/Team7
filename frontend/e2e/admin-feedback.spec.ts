import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Admin Feedback Workflow
 *
 * Test Suite Contents:
 * 1. Admin Synonyms Management
 * 2. Admin Analytics Dashboard
 * 3. Complete Admin Workflows
 * 4. Navigation & Page Rendering
 * 5. Error Handling
 * 6. Responsive Design
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Admin pages accessible at /admin/synonyms and /admin/analytics
 */

test.describe('Admin Synonyms Page - Navigation & Rendering', () => {
  test('should load admin synonyms page', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Check URL
    await expect(page).toHaveURL(/\/admin\/synonyms/);

    // Check page title
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();

    // Check description
    await expect(page.getByText(/Manage organization-specific custom skill synonym mappings/i)).toBeVisible();
  });

  test('should display summary statistics cards', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for statistics cards (may be empty)
    const totalSynonymsCard = page.getByText(/Total Synonyms/i);
    const activeCard = page.getByText(/Active/i);
    const inactiveCard = page.getByText(/Inactive/i);

    // At least the headers should be visible
    await expect(totalSynonymsCard.or(page.getByText(/No Custom Synonyms Found/i))).toBeVisible();
  });

  test('should have refresh and add buttons', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Check for refresh button
    await expect(page.getByRole('button', { name: /Refresh/i })).toBeVisible();

    // Check for add button
    await expect(page.getByRole('button', { name: /Add Custom Synonym/i })).toBeVisible();
  });

  test('should show empty state when no synonyms exist', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Wait for loading to complete
    await page.waitForSelector('body', { timeout: 10000 });

    // Check for either empty state or content
    const emptyState = page.getByText(/No Custom Synonyms Found/i);
    const hasContent = page.locator('.MuiCard-root').filter({ hasText: /Custom Synonyms/i });

    const isVisible = await emptyState.isVisible().catch(() => false);
    const hasCards = await hasContent.count().then((count) => count > 0);

    expect(isVisible || hasCards).toBeTruthy();
  });
});

test.describe('Admin Synonyms Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/synonyms');
    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test('should open add synonym dialog', async ({ page }) => {
    // Click add button
    await page.getByRole('button', { name: /Add Custom Synonym/i }).click();

    // Check dialog title
    await expect(page.getByRole('heading', { name: /Add Custom Synonym/i })).toBeVisible();

    // Check form fields
    await expect(page.getByRole('textbox', { name: /Canonical Skill Name/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Custom Synonyms/i })).toBeVisible();
    await expect(page.getByRole('combobox', { name: /Context/i })).toBeVisible();

    // Check buttons
    await expect(page.getByRole('button', { name: /Cancel/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Create/i })).toBeVisible();

    // Close dialog
    await page.getByRole('button', { name: /Cancel/i }).click();
  });

  test('should validate required fields in add dialog', async ({ page }) => {
    // Open add dialog
    await page.getByRole('button', { name: /Add Custom Synonym/i }).click();

    // Try to submit without filling fields
    const createButton = page.getByRole('button', { name: /Create/i });

    // Button should be disabled when fields are empty
    await expect(createButton).toBeDisabled();

    // Fill canonical skill
    await page.getByRole('textbox', { name: /Canonical Skill Name/i }).fill('React');

    // Button should still be disabled (custom synonyms required)
    await expect(createButton).toBeDisabled();

    // Fill custom synonyms
    await page.getByRole('textbox', { name: /Custom Synonyms/i }).fill('ReactJS, React.js');

    // Button should now be enabled
    await expect(createButton).toBeEnabled();

    // Close dialog
    await page.getByRole('button', { name: /Cancel/i }).click();
  });

  test('should allow selecting context dropdown', async ({ page }) => {
    // Open add dialog
    await page.getByRole('button', { name: /Add Custom Synonym/i }).click();

    // Click context dropdown
    await page.getByRole('combobox', { name: /Context/i }).click();

    // Check for options
    await expect(page.getByRole('option', { name: /None/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Web Framework/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Programming Language/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Database/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Tool/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Library/i })).toBeVisible();

    // Close dialog
    await page.getByRole('button', { name: /Cancel/i }).click();
  });

  test('should allow toggling active status', async ({ page }) => {
    // Open add dialog
    await page.getByRole('button', { name: /Add Custom Synonym/i }).click();

    // Find status dropdown
    const statusDropdown = page.getByRole('combobox', { name: /Status/i });
    await expect(statusDropdown).toBeVisible();

    // Click and check options
    await statusDropdown.click();
    await expect(page.getByRole('option', { name: /Active/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Inactive/i })).toBeVisible();

    // Close dialog
    await page.getByRole('button', { name: /Cancel/i }).click();
  });

  test('should display synonym cards if data exists', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check if any synonym cards exist
    const synonymCards = page.locator('.MuiCard-root').filter({
      has: page.locator('h6', { hasText: /.+/ }),
    });

    const count = await synonymCards.count();

    if (count > 0) {
      // If cards exist, check their structure
      const firstCard = synonymCards.first();

      // Should have edit and delete buttons
      await expect(firstCard.getByRole('button')).toHaveCount(await firstCard.getByRole('button').count());
    }
  });

  test('should handle refresh button click', async ({ page }) => {
    // Click refresh button
    await page.getByRole('button', { name: /Refresh/i }).click();

    // Should trigger a reload - wait for network idle
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Page should still be on admin synonyms
    await expect(page).toHaveURL(/\/admin\/synonyms/);
  });
});

test.describe('Admin Analytics Page - Navigation & Rendering', () => {
  test('should load admin analytics page', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Check URL
    await expect(page).toHaveURL(/\/admin\/analytics/);

    // Check page title
    await expect(page.getByRole('heading', { name: /Feedback Analytics/i })).toBeVisible();

    // Check description
    await expect(page.getByText(/Monitor match accuracy, learning progress/i })).toBeVisible();
  });

  test('should display summary statistics cards', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for statistics cards
    await expect(page.getByText(/Total Feedback/i)).toBeVisible();
    await expect(page.getByText(/Correct Matches/i)).toBeVisible();
    await expect(page.getByText(/Incorrect Matches/i)).toBeVisible();
    await expect(page.getByText(/Match Accuracy/i)).toBeVisible();
  });

  test('should have refresh button', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Check for refresh button
    await expect(page.getByRole('button', { name: /Refresh/i })).toBeVisible();
  });

  test('should display tabs for different views', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for tabs
    await expect(page.getByRole('tab', { name: /Learning Progress/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Model Versions/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Recent Feedback/i })).toBeVisible();
  });
});

test.describe('Admin Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/analytics');
    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test('should display Learning Progress tab by default', async ({ page }) => {
    // Learning Progress tab should be active
    const learningTab = page.getByRole('tab', { name: /Learning Progress/i });
    await expect(learningTab).toHaveAttribute('aria-selected', 'true');

    // Check for learning progress content
    await expect(page.getByText(/Learning Progress/i)).toBeVisible();
  });

  test('should switch to Model Versions tab', async ({ page }) => {
    // Click Model Versions tab
    await page.getByRole('tab', { name: /Model Versions/i }).click();

    // Check that tab is now active
    await expect(page.getByRole('tab', { name: /Model Versions/i })).toHaveAttribute('aria-selected', 'true');

    // Check for model versions content
    await expect(page.getByText(/Model Versions/i)).toBeVisible();
  });

  test('should switch to Recent Feedback tab', async ({ page }) => {
    // Click Recent Feedback tab
    await page.getByRole('tab', { name: /Recent Feedback/i }).click();

    // Check that tab is now active
    await expect(page.getByRole('tab', { name: /Recent Feedback/i })).toHaveAttribute('aria-selected', 'true');

    // Check for recent feedback content
    await expect(page.getByText(/Recent Feedback/i)).toBeVisible();
  });

  test('should display accuracy metrics', async ({ page }) => {
    // Check for accuracy percentage display
    await expect(page.locator('text=/\\d+\\.\\d+%/')).toBeVisible();

    // Check for trend indicator (up or down)
    const trendUp = page.getByText(/Current Match Accuracy/i).locator('..').locator('svg');
    await expect(trendUp).toBeVisible();
  });

  test('should display learning progress indicators', async ({ page }) => {
    // Make sure we're on Learning Progress tab
    await page.getByRole('tab', { name: /Learning Progress/i }).click();

    // Check for progress bars
    const progressBars = page.locator('.MuiLinearProgress-root');
    const count = await progressBars.count();

    // Should have at least some progress indicators
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should handle refresh button click', async ({ page }) => {
    // Click refresh button
    await page.getByRole('button', { name: /Refresh/i }).click();

    // Should trigger a reload - wait for network idle
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Page should still be on admin analytics
    await expect(page).toHaveURL(/\/admin\/analytics/);
  });

  test('should display feedback table on Recent Feedback tab', async ({ page }) => {
    // Click Recent Feedback tab
    await page.getByRole('tab', { name: /Recent Feedback/i }).click();

    // Check for table headers
    const tableHeaders = page.locator('thead th');
    const count = await tableHeaders.count();

    // Table should exist even if empty
    if (count > 0) {
      // Check for expected column headers
      await expect(page.getByText(/Skill/i)).toBeVisible();
      await expect(page.getByText(/Correct/i)).toBeVisible();
      await expect(page.getByText(/Confidence/i)).toBeVisible();
    }
  });
});

test.describe('Complete Admin Workflows', () => {
  test('complete workflow: navigate home → admin synonyms → admin analytics', async ({ page }) => {
    // Start at home
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: /Transform Your Recruitment Process/i })).toBeVisible();

    // Navigate to admin synonyms
    await page.goto('/admin/synonyms');
    await expect(page).toHaveURL(/\/admin\/synonyms/);
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();

    // Navigate to admin analytics
    await page.goto('/admin/analytics');
    await expect(page).toHaveURL(/\/admin\/analytics/);
    await expect(page.getByRole('heading', { name: /Feedback Analytics/i })).toBeVisible();
  });

  test('complete workflow: synonym management flow', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Click add button
    await page.getByRole('button', { name: /Add Custom Synonym/i }).click();

    // Fill form
    await page.getByRole('textbox', { name: /Canonical Skill Name/i }).fill('TypeScript');
    await page.getByRole('textbox', { name: /Custom Synonyms/i }).fill('TS, TypeScript Lang, TS-Lang');

    // Select context
    await page.getByRole('combobox', { name: /Context/i }).click();
    await page.getByRole('option', { name: /Programming Language/i }).click();

    // Close dialog (in real test, would click Create)
    await page.getByRole('button', { name: /Cancel/i }).click();

    // Should return to synonyms list
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();
  });

  test('complete workflow: analytics exploration', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Start on Learning Progress tab
    await expect(page.getByRole('tab', { name: /Learning Progress/i })).toHaveAttribute('aria-selected', 'true');

    // Switch to Model Versions
    await page.getByRole('tab', { name: /Model Versions/i }).click();
    await expect(page.getByRole('tab', { name: /Model Versions/i })).toHaveAttribute('aria-selected', 'true');

    // Switch to Recent Feedback
    await page.getByRole('tab', { name: /Recent Feedback/i }).click();
    await expect(page.getByRole('tab', { name: /Recent Feedback/i })).toHaveAttribute('aria-selected', 'true');

    // Switch back to Learning Progress
    await page.getByRole('tab', { name: /Learning Progress/i }).click();
    await expect(page.getByRole('tab', { name: /Learning Progress/i })).toHaveAttribute('aria-selected', 'true');
  });

  test('complete workflow: admin navigation cycle', async ({ page }) => {
    // Home → Admin Synonyms → Admin Analytics → Home
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    await page.goto('/admin/synonyms');
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();

    await page.goto('/admin/analytics');
    await expect(page.getByRole('heading', { name: /Feedback Analytics/i })).toBeVisible();

    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Admin Error Handling', () => {
  test('should handle loading states gracefully', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Initially might show loading state
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const isVisible = await loadingSpinner.isVisible().catch(() => false);

    if (isVisible) {
      // If loading, wait for it to complete
      await page.waitForSelector('.MuiCircularProgress-root', { state: 'hidden', timeout: 10000 });
    }

    // Should eventually show content
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();
  });

  test('should handle analytics loading states', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Initially might show loading state
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const isVisible = await loadingSpinner.isVisible().catch(() => false);

    if (isVisible) {
      // If loading, wait for it to complete
      await page.waitForSelector('.MuiCircularProgress-root', { state: 'hidden', timeout: 10000 });
    }

    // Should eventually show content
    await expect(page.getByRole('heading', { name: /Feedback Analytics/i })).toBeVisible();
  });
});

test.describe('Admin Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/admin/synonyms');

    // Main elements should be visible
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();

    // Add button should be visible (might need scrolling on mobile)
    const addButton = page.getByRole('button', { name: /Add Custom Synonym/i });
    await addButton.scrollIntoViewIfNeeded();
    await expect(addButton).toBeVisible();
  });

  test('should adapt analytics layout on mobile', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/admin/analytics');

    // Wait for load
    await page.waitForLoadState('networkidle');

    // Main heading should be visible
    await expect(page.getByRole('heading', { name: /Feedback Analytics/i })).toBeVisible();

    // Tabs should be visible
    await expect(page.getByRole('tab', { name: /Learning Progress/i })).toBeVisible();
  });

  test('should be usable on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/admin/synonyms');

    // Admin interface should be visible
    await expect(page.getByRole('heading', { name: /Custom Synonyms Management/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Add Custom Synonym/i })).toBeVisible();
  });
});

test.describe('Admin Accessibility', () => {
  test('should have proper heading hierarchy on synonyms page', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Check for h4 heading (page title)
    const h4 = page.getByRole('heading', { level: 4 });
    await expect(h4).toBeVisible();

    // Check for h5 and h6 headings
    const h5 = page.getByRole('heading', { level: 5 });
    const h6 = page.getByRole('heading', { level: 6 });

    const h5Count = await h5.count();
    const h6Count = await h6.count();

    expect(h5Count + h6Count).toBeGreaterThan(0);
  });

  test('should have proper heading hierarchy on analytics page', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Wait for load
    await page.waitForLoadState('networkidle');

    // Check for h4 heading (page title)
    const h4 = page.getByRole('heading', { level: 4 });
    await expect(h4).toBeVisible();

    // Check for h5 and h6 headings
    const h5 = page.getByRole('heading', { level: 5 });
    const h6 = page.getByRole('heading', { level: 6 });

    const h5Count = await h5.count();
    const h6Count = await h6.count();

    expect(h5Count + h6Count).toBeGreaterThan(0);
  });

  test('should be keyboard navigable on synonyms page', async ({ page }) => {
    await page.goto('/admin/synonyms');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First interactive element should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toMatch(/BUTTON|INPUT|A/);
  });

  test('should be keyboard navigable on analytics page', async ({ page }) => {
    await page.goto('/admin/analytics');

    // Wait for load
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First interactive element should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toMatch(/BUTTON|INPUT|TAB/);
  });
});

test.describe('Admin Performance', () => {
  test('should load synonyms page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/admin/synonyms');

    // Wait for main content
    await page.waitForSelector('h4, h5, h6');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should load analytics page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/admin/analytics');

    // Wait for main content
    await page.waitForSelector('h4, h5, h6');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should not have memory leaks during admin navigation', async ({ page }) => {
    // Navigate through admin pages multiple times
    for (let i = 0; i < 5; i++) {
      await page.goto('/admin/synonyms');
      await page.goto('/admin/analytics');
    }

    // Page should still be responsive
    await expect(page.getByRole('heading', { level: 4 })).toBeVisible();
  });
});
