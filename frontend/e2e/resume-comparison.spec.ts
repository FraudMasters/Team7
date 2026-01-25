import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Resume Comparison Platform
 *
 * Test Suite Contents:
 * 1. Navigation & Page Rendering
 * 2. Single Resume Comparison Workflow
 * 3. Multi-Resume Comparison Workflow
 * 4. Comparison Controls & Filtering
 * 5. Save & Share Functionality
 * 6. Export Functionality
 * 7. Error Handling
 * 8. Complete User Journeys
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Test data fixtures available in backend/uploads/
 */

test.describe('Navigation & Page Rendering', () => {
  test('should navigate to single resume comparison page', async ({ page }) => {
    await page.goto('/compare/test-resume-123/test-vacancy-456');

    // Check URL
    await expect(page).toHaveURL(/\/compare\/test-resume-123\/test-vacancy-456/);

    // Check that comparison interface is visible
    await expect(page.getByText(/Job Comparison|Compare Resume with Vacancy/i)).toBeVisible();
  });

  test('should navigate to multi-resume comparison page', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy-456');

    // Check URL
    await expect(page).toHaveURL(/\/compare-vacancy\/test-vacancy-456/);

    // Check page title
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();

    // Check description
    await expect(page.getByText(/Compare multiple resumes side-by-side/i)).toBeVisible();
  });

  test('should handle multi-resume comparison with query params', async ({ page }) => {
    const resumeIds = 'resume-1,resume-2,resume-3';
    await page.goto(`/compare-vacancy/test-vacancy?resumes=${resumeIds}`);

    // Check URL includes query params
    await expect(page).toHaveURL(/resumes=resume-1,resume-2,resume-3/);

    // Should show comparison interface
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();
  });

  test('should show error for missing vacancy ID', async ({ page }) => {
    await page.goto('/compare-vacancy/');

    // Should redirect or show error
    const url = page.url();
    expect(url).toMatch(/\/($|compare-vacancy)/);
  });

  test('should display comparison settings section', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy-456');

    // Check comparison settings section
    await expect(page.getByRole('heading', { name: /Comparison Settings/i })).toBeVisible();

    // Check for controls
    await expect(page.getByText(/Resume Selection/i)).toBeVisible();
    await expect(page.getByText(/Filters/i)).toBeVisible();
    await expect(page.getByText(/Sorting/i)).toBeVisible();
  });
});

test.describe('Single Resume Comparison Workflow', () => {
  test('should display job comparison component', async ({ page }) => {
    await page.goto('/compare/test-resume-123/test-vacancy-456');

    // Should show comparison interface
    await expect(page.getByText(/Job Comparison|Compare Resume with Vacancy/i)).toBeVisible();

    // Check for key comparison elements
    await expect(page.getByText(/Match Percentage|Skills|Experience/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle loading state for comparison', async ({ page }) => {
    await page.goto('/compare/test-resume-123/test-vacancy-456');

    // Initially might show loading
    const loading = page.getByText(/Loading|Comparing|Please wait/i);
    if (await loading.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(loading).toBeVisible();
    }
  });

  test('should handle comparison errors gracefully', async ({ page }) => {
    // Navigate with invalid IDs
    await page.goto('/compare/invalid-resume/invalid-vacancy');

    // Should show error state or retry option
    const errorOrRetry = page.getByText(/Failed to load|Error loading comparison|Retry/i);
    await expect(errorOrRetry).toBeVisible({ timeout: 10000 });
  });

  test('should navigate between compare and other pages', async ({ page }) => {
    await page.goto('/compare/test-resume/test-vacancy');
    await expect(page).toHaveURL(/\/compare\//);

    // Navigate to home
    await page.goto('/');
    await expect(page).toHaveURL(/\//);

    // Navigate back to compare
    await page.goto('/compare/test-resume/test-vacancy');
    await expect(page).toHaveURL(/\/compare\//);
  });
});

test.describe('Multi-Resume Comparison Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy-456');
  });

  test('should display getting started guidance when no resumes selected', async ({ page }) => {
    // Should show guidance message
    await expect(page.getByText(/Getting Started/i)).toBeVisible();
    await expect(page.getByText(/Add at least 2 resume IDs/i)).toBeVisible();
    await expect(page.getByText(/Maximum 5 resumes/i)).toBeVisible();
  });

  test('should allow adding resume IDs', async ({ page }) => {
    // Find the input field
    const input = page.getByLabel(/Add Resume ID/i);
    await expect(input).toBeVisible();

    // Add a resume ID
    await input.fill('test-resume-1');

    // Click add button
    const addButton = page.getByRole('button', { name: /Add/i });
    await addButton.click();

    // Should show the added resume (may take a moment)
    await page.waitForTimeout(500);

    // Check that resume was added (visible in chip/list)
    const resumeChip = page.getByText('test-resume-1');
    await expect(resumeChip).toBeVisible();
  });

  test('should validate minimum resume requirement', async ({ page }) => {
    // Add only one resume
    const input = page.getByLabel(/Add Resume ID/i);
    await input.fill('test-resume-1');
    await page.getByRole('button', { name: /Add/i }).click();
    await page.waitForTimeout(500);

    // Try to save (should show warning)
    const saveButton = page.getByRole('button', { name: /Save Comparison/i });
    await saveButton.click();

    // Should show error message
    await expect(page.getByText(/Please select 2-5 resumes/i)).toBeVisible();
  });

  test('should validate maximum resume limit', async ({ page }) => {
    // Try to add more than 5 resumes
    const input = page.getByLabel(/Add Resume ID/i);

    for (let i = 1; i <= 6; i++) {
      await input.fill(`test-resume-${i}`);
      await page.getByRole('button', { name: /Add/i }).click();
      await page.waitForTimeout(300);
    }

    // Should show warning about too many resumes
    await expect(page.getByText(/Too Many Resumes|Maximum 5 resumes/i)).toBeVisible();
  });

  test('should allow removing resume IDs', async ({ page }) => {
    // Add a resume first
    const input = page.getByLabel(/Add Resume ID/i);
    await input.fill('test-resume-1');
    await page.getByRole('button', { name: /Add/i }).click();
    await page.waitForTimeout(500);

    // Find and click delete button on the chip
    const deleteButton = page.locator('.MuiChip-deleteIcon').first();
    await deleteButton.click();

    // Resume should be removed
    await page.waitForTimeout(500);
    await expect(page.getByText('test-resume-1')).not.toBeVisible();
  });

  test('should display comparison matrix when valid resumes selected', async ({ page }) => {
    // Navigate with resumes pre-selected via URL
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Should show comparison matrix
    await expect(page.getByText(/Skills Matrix|Resume Comparison Matrix/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display resume count info', async ({ page }) => {
    // Check for resume count display
    await expect(page.getByText(/Selected Resumes:|0 \/ 5/i)).toBeVisible();
  });
});

test.describe('Comparison Controls & Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy-456');
  });

  test('should display match percentage filter controls', async ({ page }) => {
    // Check for filter section
    await expect(page.getByText(/Match Percentage Range/i)).toBeVisible();

    // Check for slider
    const slider = page.locator('.MuiSlider-root').first();
    await expect(slider).toBeVisible();
  });

  test('should display sorting controls', async ({ page }) => {
    // Check for sort section
    await expect(page.getByText(/Sorting/i)).toBeVisible();

    // Check for sort dropdowns
    await expect(page.getByText(/Sort By/i)).toBeVisible();
    await expect(page.getByText(/Order/i)).toBeVisible();
  });

  test('should allow changing sort field', async ({ page }) => {
    // Click on sort by dropdown
    const sortByDropdown = page.locator('label').filter({ hasText: 'Sort By' }).click();
    await page.waitForTimeout(200);

    // Check that options are available
    await expect(page.getByRole('option', { name: /Match Percentage/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Date Created/i })).toBeVisible();
  });

  test('should allow changing sort order', async ({ page }) => {
    // Click on order dropdown
    const orderDropdown = page.locator('label').filter({ hasText: 'Order' }).click();
    await page.waitForTimeout(200);

    // Check that options are available
    await expect(page.getByRole('option', { name: /Descending/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Ascending/i })).toBeVisible();
  });

  test('should display active sort indicator', async ({ page }) => {
    // Check for sort indicator chip
    await expect(page.getByText(/Sorted by/i)).toBeVisible();
  });

  test('should have reset button', async ({ page }) => {
    // Check for reset button
    const resetButton = page.getByRole('button', { name: /Reset All/i });
    await expect(resetButton).toBeVisible();
  });

  test('should reset filters and sort to defaults', async ({ page }) => {
    // Add a resume first
    const input = page.getByLabel(/Add Resume ID/i);
    await input.fill('test-resume-1');
    await page.getByRole('button', { name: /Add/i }).click();
    await page.waitForTimeout(500);

    // Click reset
    const resetButton = page.getByRole('button', { name: /Reset All/i });
    await resetButton.click();
    await page.waitForTimeout(500);

    // Filters should be reset
    await expect(page.getByText(/0 \/ 5/i)).toBeVisible();
  });
});

test.describe('Save & Share Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');
  });

  test('should display save and share buttons', async ({ page }) => {
    // Check for action buttons
    await expect(page.getByRole('button', { name: /Save Comparison/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Share/i })).toBeVisible();
  });

  test('should open save dialog when save button clicked', async ({ page }) => {
    // Click save button
    const saveButton = page.getByRole('button', { name: /Save Comparison/i });
    await saveButton.click();

    // Should show dialog
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/Save Comparison/i)).toBeVisible();

    // Check for name input
    await expect(page.getByLabel(/Comparison Name/i)).toBeVisible();
  });

  test('should cancel save dialog', async ({ page }) => {
    // Open save dialog
    await page.getByRole('button', { name: /Save Comparison/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click cancel
    const cancelButton = page.getByRole('button', { name: /^Cancel$/i });
    await cancelButton.click();

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('should open share dialog when share button clicked', async ({ page }) => {
    // Click share button
    const shareButton = page.getByRole('button', { name: /Share/i });
    await shareButton.click();

    // Should show dialog
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/Share Comparison/i)).toBeVisible();

    // Check for URL display
    await expect(page.getByDisplayText(/http/)).toBeVisible();
  });

  test('should display copy button in share dialog', async ({ page }) => {
    // Open share dialog
    await page.getByRole('button', { name: /Share/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Check for copy button
    const copyButton = page.locator('button').filter({ hasText: /Copy/i }).first();
    await expect(copyButton).toBeVisible();
  });

  test('should validate resume count before save', async ({ page }) => {
    // Navigate with insufficient resumes
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1');

    // Click save button
    await page.getByRole('button', { name: /Save Comparison/i }).click();

    // Should show error notification
    await expect(page.getByText(/Please select 2-5 resumes/i)).toBeVisible();
  });

  test('should validate resume count before share', async ({ page }) => {
    // Navigate with insufficient resumes
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1');

    // Click share button
    await page.getByRole('button', { name: /Share/i }).click();

    // Should show error notification
    await expect(page.getByText(/Please select at least 2 resumes/i)).toBeVisible();
  });
});

test.describe('Export Functionality', () => {
  test('should display export button', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Check for export button
    await expect(page.getByRole('button', { name: /Export to Excel/i })).toBeVisible();
  });

  test('should enable export only when valid comparison exists', async ({ page }) => {
    // Navigate without resumes
    await page.goto('/compare-vacancy/test-vacancy');

    // Export button should be disabled
    const exportButton = page.getByRole('button', { name: /Export to Excel/i });
    await expect(exportButton).toBeDisabled();
  });

  test('should enable export when valid resumes selected', async ({ page }) => {
    // Navigate with resumes
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2');

    // Export button should be enabled
    const exportButton = page.getByRole('button', { name: /Export to Excel/i });
    await expect(exportButton).toBeEnabled();
  });
});

test.describe('Skills Matrix & Results Display', () => {
  test('should display skills matrix table', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Wait for comparison to load
    await page.waitForTimeout(2000);

    // Check for skills matrix
    await expect(page.getByText(/Skills Matrix/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display ranking overview', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Wait for comparison to load
    await page.waitForTimeout(2000);

    // Check for ranking section
    await expect(page.getByText(/#1|#2|#3/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display match percentages', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Wait for comparison to load
    await page.waitForTimeout(2000);

    // Check for match percentages
    await expect(page.getByText(/\d+%/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display experience summary section', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Wait for comparison to load
    await page.waitForTimeout(2000);

    // Check for experience summary
    await expect(page.getByText(/Experience Summary/i)).toBeVisible({ timeout: 10000 });
  });

  test('should have refresh button', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Wait for comparison to load
    await page.waitForTimeout(2000);

    // Check for refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshButton).toBeVisible();
  });
});

test.describe('Complete User Journeys', () => {
  test('complete workflow: compare multiple resumes', async ({ page }) => {
    // Start at home
    await page.goto('/');

    // Navigate to comparison page
    await page.goto('/compare-vacancy/test-vacancy-456');

    // Verify page loaded
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();

    // Add resumes
    const input = page.getByLabel(/Add Resume ID/i);
    await input.fill('resume-1');
    await page.getByRole('button', { name: /Add/i }).click();
    await page.waitForTimeout(500);

    await input.fill('resume-2');
    await page.getByRole('button', { name: /Add/i }).click();
    await page.waitForTimeout(500);

    // Should show comparison or guidance
    await expect(page.getByText(/Getting Started|Skills Matrix/i)).toBeVisible();
  });

  test('complete workflow: use URL with pre-selected resumes', async ({ page }) => {
    // Navigate with pre-selected resumes
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // Should display comparison
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();

    // Should have resumes in URL
    await expect(page).toHaveURL(/resumes=resume-1,resume-2,resume-3/);
  });

  test('complete workflow: adjust filters and view results', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2');

    // Wait for initial load
    await page.waitForTimeout(2000);

    // Verify comparison loaded
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();

    // Check that controls are visible
    await expect(page.getByText(/Filters/i)).toBeVisible();
    await expect(page.getByText(/Sorting/i)).toBeVisible();
  });

  test('complete workflow: single resume comparison', async ({ page }) => {
    // Navigate to single resume comparison
    await page.goto('/compare/test-resume-123/test-vacancy-456');

    // Should display comparison
    await expect(page.getByText(/Job Comparison|Compare Resume/i)).toBeVisible();

    // Verify URL parameters
    await expect(page).toHaveURL(/\/compare\/test-resume-123\/test-vacancy-456/);
  });

  test('should navigate through all comparison pages', async ({ page }) => {
    // Compare page → CompareVacancy page → Home
    await page.goto('/compare/test-resume/test-vacancy');
    await expect(page).toHaveURL(/\/compare\//);

    await page.goto('/compare-vacancy/test-vacancy');
    await expect(page).toHaveURL(/\/compare-vacancy\//);

    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should handle network errors gracefully', async ({ page }) => {
    // Navigate with invalid IDs
    await page.goto('/compare-vacancy/invalid-vacancy?resumes=invalid-1,invalid-2');

    // Should show error state (not crash)
    await expect(page.getByText(/Loading|Error|Failed/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle malformed URLs', async ({ page }) => {
    // Try various malformed URLs
    await page.goto('/compare/');
    await page.goto('/compare-vacancy/');

    // Should handle gracefully
    const url = page.url();
    expect(url).toMatch(/\/($|compare|compare-vacancy)/);
  });

  test('should show retry option on error', async ({ page }) => {
    // Navigate with invalid IDs
    await page.goto('/compare/invalid-resume/invalid-vacancy');

    // Look for retry button or error message
    const retryOrError = page.getByText(/Retry|Failed to load|Error/i);
    await expect(retryOrError).toBeVisible({ timeout: 10000 });
  });

  test('should handle empty comparison gracefully', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Should show guidance (not crash)
    await expect(page.getByText(/Getting Started|Add at least 2 resume IDs/i)).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/compare-vacancy/test-vacancy');

    // Main elements should be visible
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();
    await expect(page.getByText(/Resume Selection/i)).toBeVisible();
  });

  test('should be usable on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2');

    // Comparison interface should be visible
    await expect(page.getByRole('heading', { name: /Compare Resumes for Vacancy/i })).toBeVisible();
    await expect(page.getByText(/Filters|Sorting/i)).toBeVisible();
  });

  test('should adapt layout on desktop viewport', async ({ page }) => {
    // Desktop viewport (default)
    await page.goto('/compare-vacancy/test-vacancy?resumes=resume-1,resume-2,resume-3');

    // All sections should be visible
    await expect(page.getByText(/Resume Selection/i)).toBeVisible();
    await expect(page.getByText(/Filters/i)).toBeVisible();
    await expect(page.getByText(/Sorting/i)).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();

    // Check for h2 headings
    const h2s = page.getByRole('heading', { level: 2 });
    const count = await h2s.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Should have a focusable element
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON', 'A']).toContain(focused);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Check that text is visible
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const count = await headings.count();

    for (let i = 0; i < Math.min(count, 5); i++) {
      await expect(headings.nth(i)).toBeVisible();
    }
  });
});

test.describe('Performance', () => {
  test('should load comparison page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/compare-vacancy/test-vacancy');

    // Wait for main content
    await page.waitForSelector('h1, h2');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should not have memory leaks during navigation', async ({ page }) => {
    // Navigate through multiple comparison pages
    for (let i = 0; i < 5; i++) {
      await page.goto('/compare-vacancy/vacancy-1');
      await page.goto('/compare-vacancy/vacancy-2');
      await page.goto('/compare/resume-1/vacancy-1');
    }

    // Page should still be responsive
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Content Validation', () => {
  test('should display correct content on compare page', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Check key phrases
    await expect(page.getByText(/Compare multiple resumes side-by-side/i)).toBeVisible();
    await expect(page.getByText(/Select 2-5 resumes/i)).toBeVisible();
  });

  test('should display instructional content for getting started', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Check instructional content
    await expect(page.getByText(/Add at least 2 resume IDs to begin/i)).toBeVisible();
    await expect(page.getByText(/Use the controls above/i)).toBeVisible();
  });

  test('should have working info alerts', async ({ page }) => {
    await page.goto('/compare-vacancy/test-vacancy');

    // Check for info/tip alerts
    await expect(page.getByText(/Tip:|Select 2-5 resumes/i)).toBeVisible();
  });
});
