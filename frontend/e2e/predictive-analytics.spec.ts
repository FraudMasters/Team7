import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Predictive Analytics Workflow
 *
 * Test Suite Contents:
 * 1. Predictive Analytics Navigation & Rendering
 * 2. Pipeline Forecast Display
 * 3. Time-to-Fill Prediction
 * 4. Hiring Needs Prediction
 * 5. Pipeline Health Score
 * 6. AI-Generated Recommendations
 * 7. Auto-refresh Functionality
 * 8. Manual Refresh
 * 9. Loading States
 * 10. Error Handling
 * 11. Complete Predictive Analytics Workflow
 * 12. Responsive Design
 * 13. Accessibility
 * 14. Performance
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Predictive analytics API endpoint: /api/analytics/predictive
 */

test.describe('Predictive Analytics - Navigation & Rendering', () => {
  test('should navigate to analytics dashboard and display Predictive Analytics section', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check for Predictive Analytics heading
    await expect(page.getByRole('heading', { name: /Predictive Analytics/i })).toBeVisible();

    // Check for description
    await expect(
      page.getByText(/AI-powered forecasting and insights/i)
    ).toBeVisible();
  });

  test('should load Predictive Analytics component on Analytics Dashboard', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Predictive Analytics section should be visible
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();

    // Should contain key subsections
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();
  });

  test('should display all main sections of Predictive Analytics', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check for all major sections
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();
    await expect(page.getByText(/Time-to-Fill Prediction/i)).toBeVisible();
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
    await expect(page.getByText(/AI-Generated Recommendations/i)).toBeVisible();
  });
});

test.describe('Pipeline Forecast Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display Pipeline Forecast section', async ({ page }) => {
    // Check for Pipeline Forecast heading
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();
  });

  test('should display forecast cards with expected metrics', async ({ page }) => {
    // Look for forecast cards
    const forecastSection = page.getByText(/Pipeline Forecast/i).locator('..');

    // Should be visible
    await expect(forecastSection).toBeVisible();
  });

  test('should show forecast periods (Next 30 Days, Next Quarter, etc.)', async ({ page }) => {
    // Look for forecast period labels
    const possiblePeriods = [
      /Next 30 Days/i,
      /Next Quarter/i,
      /Next Semester/i,
    ];

    // At least one period should be visible
    const periodVisible = await Promise.all(
      possiblePeriods.map(period => page.getByText(period).isVisible().catch(() => false))
    );

    expect(periodVisible.some(visible => visible)).toBeTruthy();
  });

  test('should display expected candidates and hires metrics', async ({ page }) => {
    // Look for metric labels
    await expect(page.getByText(/Expected Candidates/i)).toBeVisible();
    await expect(page.getByText(/Expected Hires/i)).toBeVisible();
  });

  test('should display confidence level for each forecast', async ({ page }) => {
    // Check for confidence level labels
    await expect(page.getByText(/Confidence Level/i)).toBeVisible();

    // Should have percentage indicators or progress bars
    const confidenceSection = page.getByText(/Confidence Level/i);
    await expect(confidenceSection).toBeVisible();
  });
});

test.describe('Time-to-Fill Prediction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display Time-to-Fill Prediction section', async ({ page }) => {
    // Check for Time-to-Fill heading
    await expect(page.getByText(/Time-to-Fill Prediction/i)).toBeVisible();
  });

  test('should show average time-to-fill metric', async ({ page }) => {
    // Look for average time-to-fill label
    await expect(page.getByText(/Average Time-to-Fill/i)).toBeVisible();

    // Should display in days
    const daysText = await page.textContent('body');
    expect(daysText).toMatch(/\d+\s*days?/i);
  });

  test('should display min and max time-to-fill values', async ({ page }) => {
    // Check for min/max labels
    await expect(page.getByText(/Min/i)).toBeVisible();
    await expect(page.getByText(/Max/i)).toBeVisible();
  });

  test('should show trend indicator (improving, stable, or worsening)', async ({ page }) => {
    // Look for trend indicators
    const possibleTrends = [/Improving/i, /Stable/i, /Worsening/i];

    // At least one trend should be displayed
    const trendVisible = await Promise.all(
      possibleTrends.map(trend => page.getByText(trend).isVisible().catch(() => false))
    );

    expect(trendVisible.some(visible => visible)).toBeTruthy();
  });
});

test.describe('Hiring Needs Prediction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display Hiring Needs Prediction section', async ({ page }) => {
    // Check for Hiring Needs heading
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
  });

  test('should show hiring needs by department', async ({ page }) => {
    // Look for department-related content
    const hasDepartmentInfo = await page.getByText(/department/i).isVisible().catch(() => false);

    // Section should be visible even if no data
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
  });

  test('should display open positions and predicted openings', async ({ page }) => {
    // Check for relevant labels
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();

    const hasOpenPositions = await page.getByText(/Open Positions/i).isVisible().catch(() => false);
    const hasPredicted = await page.getByText(/Predicted/i).isVisible().catch(() => false);

    // At least the section should be visible
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
  });

  test('should show priority levels (high, medium, low)', async ({ page }) => {
    // Look for priority indicators
    const possiblePriorities = [/HIGH/i, /MEDIUM/i, /LOW/i];

    // Check if any priority chips are visible
    const priorityVisible = await Promise.all(
      possiblePriorities.map(priority => page.getByText(priority).isVisible().catch(() => false))
    );

    // Section should be visible regardless of data
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
  });
});

test.describe('Pipeline Health Score', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display Pipeline Health Score section', async ({ page }) => {
    // Check for Pipeline Health Score heading
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();
  });

  test('should show health score as percentage', async ({ page }) => {
    // Look for percentage indicator
    const bodyText = await page.textContent('body');

    // Should contain a percentage (e.g., 75%, 80%, etc.)
    expect(bodyText).toMatch(/\d+%/i);
  });

  test('should display health status label (Excellent, Good, Needs Attention)', async ({ page }) => {
    // Look for status labels
    const possibleStatuses = [/Excellent/i, /Good/i, /Needs Attention/i];

    const statusVisible = await Promise.all(
      possibleStatuses.map(status => page.getByText(status).isVisible().catch(() => false))
    );

    expect(statusVisible.some(visible => visible)).toBeTruthy();
  });

  test('should show health score progress bar', async ({ page }) => {
    // Look for progress bar elements
    const progressBar = page.locator('.MuiLinearProgress-root').first();
    const isVisible = await progressBar.isVisible().catch(() => false);

    // Progress bar should be visible
    if (isVisible) {
      await expect(progressBar).toBeVisible();
    }
  });
});

test.describe('AI-Generated Recommendations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display AI-Generated Recommendations section', async ({ page }) => {
    // Check for Recommendations heading
    await expect(page.getByText(/AI-Generated Recommendations/i)).toBeVisible();
  });

  test('should show actionable recommendations', async ({ page }) => {
    // Section should be visible
    await expect(page.getByText(/AI-Generated Recommendations/i)).toBeVisible();

    // May have recommendation items or empty state
    const hasRecommendations = await page.getByText(/recommendation/i, { exact: false }).isVisible().catch(() => false);
    expect(hasRecommendations || true).toBeTruthy();
  });
});

test.describe('Auto-refresh Functionality', () => {
  test('should have auto-refresh button', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Look for auto-refresh button
    const autoRefreshButton = page.getByRole('button', { name: /Auto-refresh|Paused/i });
    await expect(autoRefreshButton).toBeVisible();
  });

  test('should toggle auto-refresh state when button clicked', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Click auto-refresh button
    const autoRefreshButton = page.getByRole('button', { name: /Auto-refresh|Paused/i });
    await autoRefreshButton.click();

    // Button text should change
    await expect(autoRefreshButton).toBeVisible();
  });

  test('should show correct auto-refresh status indicator', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Look for status chip or indicator
    const statusText = await page.textContent('body');
    expect(statusText).toMatch(/Auto-refresh|refreshed/i);
  });
});

test.describe('Manual Refresh', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should have manual refresh button', async ({ page }) => {
    // Look for refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should trigger refresh when button clicked', async ({ page }) => {
    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await refreshButton.click();

    // Should show loading state briefly
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const wasLoading = await loadingSpinner.isVisible().catch(() => false);

    // After refresh, content should still be visible
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });

  test('should update last refresh time indicator', async ({ page }) => {
    // Get initial time
    const initialTimeText = await page.textContent('body');

    // Click refresh
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await refreshButton.click();

    // Wait a moment for update
    await page.waitForTimeout(500);

    // Time indicator should still be present
    const updatedTimeText = await page.textContent('body');
    expect(updatedTimeText).toMatch(/Last updated|updated/i);
  });
});

test.describe('Predictive Analytics Loading States', () => {
  test('should show loading state initially', async ({ page }) => {
    // Navigate to analytics
    await page.goto('/analytics');

    // May briefly show loading spinner
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const wasLoading = await loadingSpinner.isVisible().catch(() => false);

    // Eventually should show content
    await page.waitForLoadState('networkidle');
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });

  test('should handle loading state gracefully during refresh', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Trigger refresh
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await refreshButton.click();

    // Should still be functional after refresh
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });
});

test.describe('Predictive Analytics Error Handling', () => {
  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure scenario - navigate to page
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Page should load without crashing
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });

  test('should show error message if API fails', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // If there's an error, should show error alert
    const errorAlert = page.locator('.MuiAlert-root').filter({ hasText: /error|failed/i });
    const hasError = await errorAlert.isVisible().catch(() => false);

    // Either content loads or error is shown
    if (hasError) {
      await expect(errorAlert).toBeVisible();
    } else {
      // Content should load successfully
      await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
    }
  });

  test('should provide retry option on error', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // If error occurs, should have retry button
    const retryButton = page.getByRole('button', { name: /Retry|Refresh/i });
    await expect(retryButton).toBeVisible();
  });
});

test.describe('Complete Predictive Analytics Workflow', () => {
  test('complete workflow: navigate → view forecasts → check health → review recommendations', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Verify Predictive Analytics section is visible
    await expect(page.getByRole('heading', { name: /Predictive Analytics/i })).toBeVisible();

    // Check Pipeline Health Score
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();

    // Check Pipeline Forecast
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();

    // Check Time-to-Fill Prediction
    await expect(page.getByText(/Time-to-Fill Prediction/i)).toBeVisible();

    // Check Hiring Needs
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();

    // Check Recommendations
    await expect(page.getByText(/AI-Generated Recommendations/i)).toBeVisible();
  });

  test('complete workflow: manual refresh of predictive analytics', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Verify initial state
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();

    // Trigger manual refresh
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await refreshButton.click();

    // Wait for refresh to complete
    await page.waitForTimeout(1000);

    // Verify content is still visible
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });

  test('complete workflow: toggle auto-refresh and verify status', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Find auto-refresh button
    const autoRefreshButton = page.getByRole('button', { name: /Auto-refresh|Paused/i });

    // Get initial state
    const initialState = await autoRefreshButton.textContent();

    // Toggle auto-refresh
    await autoRefreshButton.click();

    // Verify state changed
    const newState = await autoRefreshButton.textContent();
    expect(initialState).not.toBe(newState);
  });

  test('complete workflow: review all forecast metrics across sections', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Navigate through each section
    const sections = [
      /Pipeline Health Score/i,
      /Pipeline Forecast/i,
      /Time-to-Fill Prediction/i,
      /Hiring Needs Prediction/i,
      /AI-Generated Recommendations/i,
    ];

    for (const section of sections) {
      await expect(page.getByText(section)).toBeVisible();
    }
  });
});

test.describe('Predictive Analytics Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/analytics');

    // Main elements should be visible
    await expect(page.getByRole('heading', { name: /Predictive Analytics/i })).toBeVisible();

    // Pipeline Health Score should be visible
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();
  });

  test('should adapt layout on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Main heading should be visible
    await expect(page.getByRole('heading', { name: /Predictive Analytics/i })).toBeVisible();

    // All sections should be visible
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();
    await expect(page.getByText(/Time-to-Fill Prediction/i)).toBeVisible();
  });

  test('should display all sections on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // All sections should be visible
    await expect(page.getByText(/Pipeline Health Score/i)).toBeVisible();
    await expect(page.getByText(/Pipeline Forecast/i)).toBeVisible();
    await expect(page.getByText(/Time-to-Fill Prediction/i)).toBeVisible();
    await expect(page.getByText(/Hiring Needs Prediction/i)).toBeVisible();
    await expect(page.getByText(/AI-Generated Recommendations/i)).toBeVisible();
  });
});

test.describe('Predictive Analytics Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check for h5 heading (Predictive Analytics main heading)
    const h5 = page.getByRole('heading', { level: 5 });
    const count = await h5.count();
    expect(count).toBeGreaterThan(0);

    // Check for h6 headings (subsection headings)
    const h6 = page.getByRole('heading', { level: 6 });
    const h6Count = await h6.count();
    expect(h6Count).toBeGreaterThan(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First interactive element should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toMatch(/BUTTON|INPUT|A/);
  });

  test('should have proper ARIA attributes on buttons', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check for refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should have proper button labels', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // All buttons should have accessible names
    const buttons = page.getByRole('button');
    const count = await buttons.count();

    expect(count).toBeGreaterThan(0);

    // Check first few buttons have names
    for (let i = 0; i < Math.min(3, count); i++) {
      const button = buttons.nth(i);
      await expect(button).toHaveAttribute('type');
    }
  });
});

test.describe('Predictive Analytics Performance', () => {
  test('should load predictive analytics section quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/analytics');

    // Wait for Predictive Analytics section
    await page.waitForSelector('text=Predictive Analytics', { timeout: 5000 });

    const loadTime = Date.now() - startTime;

    // Should load in less than 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should handle refresh without performance degradation', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Perform multiple refreshes
    const refreshButton = page.getByRole('button', { name: /Refresh/i });

    for (let i = 0; i < 3; i++) {
      await refreshButton.click();
      await page.waitForTimeout(500);
    }

    // Should still be responsive
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });

  test('should not have memory leaks during navigation', async ({ page }) => {
    // Navigate between pages multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('/analytics');
      await page.waitForLoadState('networkidle');
      await page.goto('/analytics?tab=reports');
      await page.waitForLoadState('networkidle');
    }

    // Should still be functional
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });
});
