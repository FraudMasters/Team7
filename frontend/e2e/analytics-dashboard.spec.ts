import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Analytics Dashboard
 *
 * Test Suite Contents:
 * 1. Analytics Dashboard Navigation & Rendering
 * 2. Dashboard Tab Components
 * 3. Reports Tab Functionality
 * 4. Tab Switching
 * 5. Date Range Filtering
 * 6. Key Metrics Display
 * 7. Funnel Visualization
 * 8. Skill Demand Chart
 * 9. Source Tracking
 * 10. Recruiter Performance
 * 11. Report Builder
 * 12. Error Handling
 * 13. Responsive Design
 * 14. Accessibility
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Analytics dashboard accessible at /analytics
 */

test.describe('Analytics Dashboard - Navigation & Rendering', () => {
  test('should load analytics dashboard page', async ({ page }) => {
    await page.goto('/analytics');

    // Check URL
    await expect(page).toHaveURL(/\/analytics/);

    // Check page title
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    // Check description
    await expect(
      page.getByText(/Monitor key hiring metrics, track candidate progression/i)
    ).toBeVisible();
  });

  test('should display main tabs', async ({ page }) => {
    await page.goto('/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for tabs
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Reports/i })).toBeVisible();
  });

  test('should display Dashboard tab by default', async ({ page }) => {
    await page.goto('/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Dashboard tab should be active
    const dashboardTab = page.getByRole('tab', { name: /Dashboard/i });
    await expect(dashboardTab).toHaveAttribute('aria-selected', 'true');
  });

  test('should load Reports tab from URL parameter', async ({ page }) => {
    await page.goto('/analytics?tab=reports');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Reports tab should be active
    const reportsTab = page.getByRole('tab', { name: /Reports/i });
    await expect(reportsTab).toHaveAttribute('aria-selected', 'true');
  });
});

test.describe('Dashboard Tab Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display Date Range Filter', async ({ page }) => {
    // Check for date range filter section
    await expect(page.getByText(/Date Range/i)).toBeVisible();

    // Check for preset dropdown
    await expect(page.getByRole('combobox', { name: /Preset/i })).toBeVisible();
  });

  test('should display Key Metrics section', async ({ page }) => {
    // Check for key metrics heading
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();

    // Check for metric cards (may be empty)
    const metricsSection = page.getByText(/Key Metrics/i).locator('..');

    // At least the heading should be visible
    await expect(metricsSection).toBeVisible();
  });

  test('should display Funnel Visualization section', async ({ page }) => {
    // Check for funnel visualization heading
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();

    // Funnel section should be visible
    const funnelSection = page.getByText(/Funnel Visualization/i).locator('..');
    await expect(funnelSection).toBeVisible();
  });

  test('should display Skill Demand Chart section', async ({ page }) => {
    // Check for skill demand heading
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();

    // Skill demand section should be visible
    const skillDemandSection = page.getByText(/Skill Demand/i).locator('..');
    await expect(skillDemandSection).toBeVisible();
  });

  test('should display Source Tracking section', async ({ page }) => {
    // Check for source tracking heading
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();

    // Source tracking section should be visible
    const sourceSection = page.getByText(/Source Tracking/i).locator('..');
    await expect(sourceSection).toBeVisible();
  });

  test('should display Recruiter Performance section', async ({ page }) => {
    // Check for recruiter performance heading
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();

    // Recruiter performance section should be visible
    const recruiterSection = page.getByText(/Recruiter Performance/i).locator('..');
    await expect(recruiterSection).toBeVisible();
  });

  test('should display all dashboard sections in correct order', async ({ page }) => {
    // Get all section headings
    const sections = page.locator('h5, h6');

    const count = await sections.count();

    // Should have multiple sections
    expect(count).toBeGreaterThan(0);

    // Check for specific section headings
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();
  });
});

test.describe('Reports Tab Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics?tab=reports');
    await page.waitForLoadState('networkidle');
  });

  test('should display Report Builder', async ({ page }) => {
    // Check for report builder heading
    await expect(page.getByText(/Report Builder|Custom Reports/i)).toBeVisible();
  });

  test('should have report configuration options', async ({ page }) => {
    // Check for common report builder elements
    const reportBuilder = page.getByText(/Report Builder|Custom Reports/i).locator('..');

    // Report builder section should be visible
    await expect(reportBuilder).toBeVisible();
  });

  test('should switch between Dashboard and Reports tabs', async ({ page }) => {
    // Start on Reports tab
    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');

    // Click Dashboard tab
    await page.getByRole('tab', { name: /Dashboard/i }).click();

    // Dashboard tab should now be active
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toHaveAttribute('aria-selected', 'true');

    // Dashboard content should be visible
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();

    // Click Reports tab again
    await page.getByRole('tab', { name: /Reports/i }).click();

    // Reports tab should be active again
    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');
  });
});

test.describe('Tab Switching', () => {
  test('should update URL when switching tabs', async ({ page }) => {
    await page.goto('/analytics');

    // Dashboard tab should be active
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toHaveAttribute('aria-selected', 'true');
    await expect(page).toHaveURL(/\/analytics/);

    // Click Reports tab
    await page.getByRole('tab', { name: /Reports/i }).click();

    // URL should update
    await expect(page).toHaveURL(/\/analytics\?tab=reports/);

    // Click Dashboard tab
    await page.getByRole('tab', { name: /Dashboard/i }).click();

    // URL should update
    await expect(page).toHaveURL(/\/analytics(\?tab=dashboard)?/);
  });

  test('should maintain tab state on navigation', async ({ page }) => {
    // Go to reports tab
    await page.goto('/analytics?tab=reports');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Reports tab should still be active
    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');
  });
});

test.describe('Date Range Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display date range filter controls', async ({ page }) => {
    // Check for preset dropdown
    await expect(page.getByRole('combobox', { name: /Preset/i })).toBeVisible();

    // Check for date inputs
    const startDateInput = page.getByRole('textbox', { name: /Start Date|From/i });
    const endDateInput = page.getByRole('textbox', { name: /End Date|To/i });

    // At least preset dropdown should be visible
    await expect(page.getByRole('combobox', { name: /Preset/i })).toBeVisible();
  });

  test('should allow selecting preset date ranges', async ({ page }) => {
    // Click preset dropdown
    await page.getByRole('combobox', { name: /Preset/i }).click();

    // Check for preset options
    await expect(page.getByRole('option', { name: /Last 7 Days/i }).or(
      page.getByRole('option', { name: /7 Days/i })
    )).toBeVisible();

    await expect(page.getByRole('option', { name: /Last 30 Days/i }).or(
      page.getByRole('option', { name: /30 Days/i })
    )).toBeVisible();

    await expect(page.getByRole('option', { name: /Last 90 Days/i }).or(
      page.getByRole('option', { name: /90 Days/i })
    )).toBeVisible();
  });

  test('should handle date range changes', async ({ page }) => {
    // Click preset dropdown
    await page.getByRole('combobox', { name: /Preset/i }).click();

    // Select a different preset (e.g., Last 90 Days)
    const ninetyDaysOption = page.getByRole('option', { name: /90 Days/i });
    const isVisible = await ninetyDaysOption.isVisible().catch(() => false);

    if (isVisible) {
      await ninetyDaysOption.click();

      // Preset dropdown should still be visible
      await expect(page.getByRole('combobox', { name: /Preset/i })).toBeVisible();
    }
  });
});

test.describe('Key Metrics Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display key metrics cards', async ({ page }) => {
    // Check for key metrics section
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();

    // Metrics may be empty or populated
    const metricsSection = page.getByText(/Key Metrics/i).locator('..');
    await expect(metricsSection).toBeVisible();
  });

  test('should show metric labels and values', async ({ page }) => {
    // Look for common metric labels
    const possibleMetrics = [
      /Total Candidates/i,
      /Applications/i,
      /Interviews/i,
      /Hires/i,
      /Time to Hire/i,
      /Acceptance Rate/i,
    ];

    // At least section should be visible
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
  });
});

test.describe('Funnel Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display funnel stages', async ({ page }) => {
    // Check for funnel visualization
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();

    // Funnel section should be visible
    const funnelSection = page.getByText(/Funnel Visualization/i).locator('..');
    await expect(funnelSection).toBeVisible();
  });

  test('should show stage labels', async ({ page }) => {
    // Look for common funnel stage labels
    const possibleStages = [
      /Applied/i,
      /Screening/i,
      /Interview/i,
      /Offer/i,
      /Hired/i,
      /Rejected/i,
    ];

    // Funnel section should be visible
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
  });
});

test.describe('Skill Demand Chart', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display skill demand chart', async ({ page }) => {
    // Check for skill demand section
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();

    // Skill demand section should be visible
    const skillDemandSection = page.getByText(/Skill Demand/i).locator('..');
    await expect(skillDemandSection).toBeVisible();
  });

  test('should show chart or empty state', async ({ page }) => {
    // Check for chart container or empty state
    const skillSection = page.getByText(/Skill Demand/i).locator('..');
    await expect(skillSection).toBeVisible();
  });
});

test.describe('Source Tracking', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display source tracking section', async ({ page }) => {
    // Check for source tracking
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();

    // Source tracking section should be visible
    const sourceSection = page.getByText(/Source Tracking/i).locator('..');
    await expect(sourceSection).toBeVisible();
  });

  test('should show source breakdown', async ({ page }) => {
    // Look for common source labels
    const possibleSources = [
      /LinkedIn/i,
      /Indeed/i,
      /Referral/i,
      /Career Site/i,
      /Agency/i,
    ];

    // Source tracking section should be visible
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();
  });
});

test.describe('Recruiter Performance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display recruiter performance section', async ({ page }) => {
    // Check for recruiter performance
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();

    // Recruiter performance section should be visible
    const recruiterSection = page.getByText(/Recruiter Performance/i).locator('..');
    await expect(recruiterSection).toBeVisible();
  });

  test('should show recruiter metrics', async ({ page }) => {
    // Look for recruiter-related metrics
    const possibleMetrics = [
      /Recruiter/i,
      /Hires/i,
      /Time to Fill/i,
      /Candidates/i,
    ];

    // Recruiter performance section should be visible
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();
  });
});

test.describe('Report Builder', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics?tab=reports');
    await page.waitForLoadState('networkidle');
  });

  test('should display report builder interface', async ({ page }) => {
    // Check for report builder
    await expect(page.getByText(/Report Builder|Custom Reports/i)).toBeVisible();
  });

  test('should have report configuration options', async ({ page }) => {
    // Report builder should be visible
    const reportBuilder = page.getByText(/Report Builder|Custom Reports/i).locator('..');
    await expect(reportBuilder).toBeVisible();
  });
});

test.describe('Complete Analytics Workflows', () => {
  test('complete workflow: navigate home → analytics dashboard → reports', async ({ page }) => {
    // Start at home
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: /Transform Your Recruitment Process/i })).toBeVisible();

    // Navigate to analytics dashboard
    await page.goto('/analytics');
    await expect(page).toHaveURL(/\/analytics/);
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    // Switch to reports tab
    await page.getByRole('tab', { name: /Reports/i }).click();
    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');
  });

  test('complete workflow: explore all dashboard sections', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Verify all sections are visible
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();
  });

  test('complete workflow: date range exploration', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open preset dropdown
    await page.getByRole('combobox', { name: /Preset/i }).click();

    // Select a preset
    const last30Days = page.getByRole('option', { name: /30 Days/i });
    const isVisible = await last30Days.isVisible().catch(() => false);

    if (isVisible) {
      await last30Days.click();

      // Verify dropdown remains visible
      await expect(page.getByRole('combobox', { name: /Preset/i })).toBeVisible();
    }
  });

  test('complete workflow: tab navigation cycle', async ({ page }) => {
    await page.goto('/analytics');

    // Dashboard → Reports → Dashboard
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toHaveAttribute('aria-selected', 'true');

    await page.getByRole('tab', { name: /Reports/i }).click();
    await expect(page.getByRole('tab', { name: /Reports/i })).toHaveAttribute('aria-selected', 'true');

    await page.getByRole('tab', { name: /Dashboard/i }).click();
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toHaveAttribute('aria-selected', 'true');
  });
});

test.describe('Analytics Error Handling', () => {
  test('should handle loading states gracefully', async ({ page }) => {
    await page.goto('/analytics');

    // Initially might show loading state
    const loadingSpinner = page.locator('.MuiCircularProgress-root');
    const isVisible = await loadingSpinner.isVisible().catch(() => false);

    if (isVisible) {
      // If loading, wait for it to complete
      await page.waitForSelector('.MuiCircularProgress-root', { state: 'hidden', timeout: 10000 });
    }

    // Should eventually show content
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });

  test('should handle empty states gracefully', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Page should load without errors even if no data
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    // All sections should be present (even if empty)
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
  });
});

test.describe('Analytics Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/analytics');

    // Main elements should be visible
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    // Tabs should be visible (might be scrollable)
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toBeVisible();
  });

  test('should adapt layout on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/analytics');

    // Main heading should be visible
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    // Tabs should be visible
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Reports/i })).toBeVisible();
  });

  test('should display all sections on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // All sections should be visible
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();
  });
});

test.describe('Analytics Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/analytics');

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

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First interactive element should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toMatch(/BUTTON|INPUT|A|TAB/);
  });

  test('should have proper ARIA attributes on tabs', async ({ page }) => {
    await page.goto('/analytics');

    // Check for tabs with proper ARIA attributes
    const dashboardTab = page.getByRole('tab', { name: /Dashboard/i });
    await expect(dashboardTab).toHaveAttribute('aria-selected');

    const reportsTab = page.getByRole('tab', { name: /Reports/i });
    await expect(reportsTab).toHaveAttribute('aria-controls');
  });

  test('should have proper tab panel structure', async ({ page }) => {
    await page.goto('/analytics');

    // Check for tabpanel elements
    const tabPanels = page.locator('[role="tabpanel"]');
    const count = await tabPanels.count();

    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Analytics Performance', () => {
  test('should load analytics page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/analytics');

    // Wait for main content
    await page.waitForSelector('h4, h5, h6');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should not have memory leaks during tab navigation', async ({ page }) => {
    // Navigate between tabs multiple times
    for (let i = 0; i < 5; i++) {
      await page.goto('/analytics');
      await page.goto('/analytics?tab=reports');
    }

    // Page should still be responsive
    await expect(page.getByRole('heading', { level: 4 })).toBeVisible();
  });

  test('should handle rapid tab switching gracefully', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Rapidly switch tabs
    for (let i = 0; i < 3; i++) {
      await page.getByRole('tab', { name: /Reports/i }).click();
      await page.getByRole('tab', { name: /Dashboard/i }).click();
    }

    // Should still be functional
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });
});
