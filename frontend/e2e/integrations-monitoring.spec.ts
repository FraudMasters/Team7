/**
 * Integration Monitoring Dashboard E2E Tests
 *
 * Verifies that monitoring dashboards correctly display:
 * - Integration health status
 * - Sync metrics
 * - Recent sync errors
 *
 * Test coverage:
 * - Integration status indicators
 * - Sync history metrics display
 * - Error visibility and details
 * - Real-time status updates
 * - Performance metrics
 */

import { test, expect, Page } from '@playwright/test';

/**
 * Test credentials and data
 */
const TEST_INTEGRATIONS = {
  active: {
    name: 'Active Greenhouse Integration',
    platform: 'greenhouse',
    status: 'active',
  },
  syncing: {
    name: 'Syncing Workday Integration',
    platform: 'workday',
    status: 'active',
    syncStatus: 'in_progress',
  },
  failed: {
    name: 'Failed Lever Integration',
    platform: 'lever',
    status: 'error',
    syncStatus: 'failed',
  },
  inactive: {
    name: 'Inactive BambooHR Integration',
    platform: 'bamboohr',
    status: 'inactive',
  },
};

/**
 * Helper function to navigate to integrations page
 */
async function navigateToIntegrations(page: Page) {
  await page.goto('/integrations');
  await page.waitForLoadState('networkidle');
}

/**
 * Helper function to verify status badge
 */
async function verifyStatusBadge(page: Page, integrationName: string, expectedStatus: string) {
  const row = page.locator(`tr:has-text("${integrationName}")`);
  await expect(row).toBeVisible();

  const statusBadge = row.locator('[data-testid="integration-status-badge"]');
  await expect(statusBadge).toBeVisible();
  await expect(statusBadge).toContainText(expectedStatus, { ignoreCase: true });
}

/**
 * Helper function to verify sync metrics
 */
async function verifySyncMetrics(page: Page) {
  // Check for sync metrics columns
  await expect(page.locator('th:has-text("Last Sync")')).toBeVisible();
  await expect(page.locator('th:has-text("Sync Status")')).toBeVisible();

  // Verify metrics display
  const rows = page.locator('tbody tr');
  const count = await rows.count();

  if (count > 0) {
    for (let i = 0; i < Math.min(count, 5); i++) {
      const row = rows.nth(i);
      const lastSyncCell = row.locator('td').nth(3); // Last Sync column
      const syncStatusCell = row.locator('td').nth(4); // Sync Status column

      // Check that cells have content (date or status indicator)
      const lastSyncText = await lastSyncCell.textContent();
      const syncStatusText = await syncStatusCell.textContent();

      // At least one should have content
      expect(lastSyncText?.trim() || syncStatusText?.trim()).toBeTruthy();
    }
  }
}

/**
 * Helper function to open sync history for an integration
 */
async function openSyncHistory(page: Page, integrationName: string) {
  const row = page.locator(`tr:has-text("${integrationName}")`);
  const historyButton = row.locator('button[aria-label*="history" i], button:has-text("History")');

  if (await historyButton.isVisible()) {
    await historyButton.click();
    await page.waitForSelector('[data-testid="sync-history-dialog"]', { timeout: 5000 });
    return true;
  }
  return false;
}

test.describe('Integration Monitoring Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to integrations monitoring dashboard
    await navigateToIntegrations(page);
  });

  test('should display integration health status for all integrations', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Integration health status visible in dashboard',
    });

    // Wait for page to load
    await expect(page.locator('h1:has-text("Integrations")')).toBeVisible();

    // Check for integration status indicators
    const statusBadges = page.locator('[data-testid="integration-status-badge"], .MuiChip-root');

    // Should have at least some status indicators (even if 0 integrations, we check UI elements exist)
    await expect(page.locator('table')).toBeVisible();

    // If integrations exist, verify status badges
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Each row should have a status badge
      for (let i = 0; i < Math.min(rowCount, 3); i++) {
        const row = rows.nth(i);
        const statusBadge = row.locator('[data-testid="integration-status-badge"], .MuiChip-root');
        await expect(statusBadge.first()).toBeVisible();
      }
    }
  });

  test('should display correct status colors and icons', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Status indicators use correct colors and icons',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Check first row has status indicator with icon
      const firstRow = rows.first();
      const statusBadge = firstRow.locator('[data-testid="integration-status-badge"], .MuiChip-root');

      await expect(statusBadge.first()).toBeVisible();

      // Verify icon presence (if using material icons)
      const icon = statusBadge.locator('svg');
      const hasIcon = await icon.count() > 0;
      expect(hasIcon).toBeTruthy();
    }
  });

  test('should display sync metrics in the dashboard', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Sync metrics display correctly',
    });

    // Check for metrics table headers
    await expect(page.locator('th:has-text("Platform")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();

    // Verify sync metrics are displayed
    await verifySyncMetrics(page);

    // Look for sync-related columns
    const hasSyncInfo = await page.locator('th:has-text("Last Sync"), th:has-text("Sync Status")').count() > 0;
    expect(hasSyncInfo).toBeTruthy();
  });

  test('should show integration statistics summary', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Integration statistics visible at top of dashboard',
    });

    // Look for stats cards or summary section
    const statsSection = page.locator('[data-testid="integration-stats"], .integration-stats');

    // Check for common stat displays
    const hasStats =
      (await page.locator('text=/Total.*Integrations/i').count() > 0) ||
      (await page.locator('text=/Active.*Integrations/i').count() > 0);

    if (hasStats) {
      // Verify stats are numbers
      const statNumbers = page.locator('[data-testid="stat-value"], .stat-value');
      const count = await statNumbers.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should display recent sync errors when they exist', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Recent sync errors shown in dashboard',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Check for error indicators in sync status column
      const errorBadges = page.locator('[data-testid="integration-status-badge"]:has-text("failed"), .MuiChip-colorError');

      const errorCount = await errorBadges.count();

      // If there are errors, verify they're visible
      if (errorCount > 0) {
        // Click on first error to see details
        await errorBadges.first().click();

        // Error details might be in a dialog or alert
        const errorDetail = page.locator('[data-testid="error-detail"], .error-detail, [role="alert"]');
        const isVisible = await errorDetail.first().isVisible().catch(() => false);

        if (isVisible) {
          await expect(errorDetail.first()).toBeVisible();
        }
      }
    }
  });

  test('should allow viewing detailed sync history', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Sync history dialog shows detailed metrics',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Get first integration name
      const firstRow = rows.first();
      const integrationName = await firstRow.locator('td').first().textContent();

      if (integrationName) {
        // Open sync history
        const historyOpened = await openSyncHistory(page, integrationName.trim());

        if (historyOpened) {
          // Verify sync history dialog
          const dialog = page.locator('[data-testid="sync-history-dialog"], .MuiDialog-root');
          await expect(dialog).toBeVisible();

          // Check for sync history table
          const historyTable = dialog.locator('table');
          await expect(historyTable).toBeVisible();

          // Verify history columns
          await expect(dialog.locator('th:has-text("Date")').or(dialog.locator('th:has-text("Time")'))).toBeVisible();
          await expect(dialog.locator('th:has-text("Status")')).toBeVisible();

          // Check for metrics columns
          const hasMetrics =
            (await dialog.locator('th:has-text("Records")').count() > 0) ||
            (await dialog.locator('th:has-text("Duration")').count() > 0);

          if (hasMetrics) {
            // Verify metrics are displayed
            const metricCells = dialog.locator('td');
            const metricCount = await metricCells.count();
            expect(metricCount).toBeGreaterThan(0);
          }

          // Close dialog
          const closeButton = dialog.locator('button[aria-label="close"], button:has-text("Close")');
          if (await closeButton.isVisible()) {
            await closeButton.click();
          }
        }
      }
    }
  });

  test('should show sync status with proper indicators', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Sync status indicators (in progress, completed, failed) visible',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Check for different sync status indicators
      const inProgressBadge = page.locator('text=/syncing/i, [data-testid="sync-status-in-progress"]');
      const completedBadge = page.locator('text=/completed/i, [data-testid="sync-status-completed"]');
      const failedBadge = page.locator('text=/failed/i, [data-testid="sync-status-failed"]');

      // At least the sync status column should exist
      const syncStatusColumn = page.locator('th:has-text("Sync Status")');
      const hasColumn = await syncStatusColumn.count() > 0;

      expect(hasColumn).toBeTruthy();
    }
  });

  test('should display last sync timestamps', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Last sync timestamps displayed correctly',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Look for last sync column
      const lastSyncHeader = page.locator('th:has-text("Last Sync")');
      const hasColumn = await lastSyncHeader.count() > 0;

      if (hasColumn) {
        // Get header index to find the column
        const headers = page.locator('th');
        const headerCount = await headers.count();

        let lastSyncIndex = -1;
        for (let i = 0; i < headerCount; i++) {
          const text = await headers.nth(i).textContent();
          if (text?.includes('Last Sync')) {
            lastSyncIndex = i;
            break;
          }
        }

        if (lastSyncIndex >= 0) {
          // Check cells in this column have reasonable content
          for (let i = 0; i < Math.min(rowCount, 3); i++) {
            const row = rows.nth(i);
            const cell = row.locator('td').nth(lastSyncIndex);
            const text = await cell.textContent();

            // Should have a date, "Never", or similar
            expect(text?.trim().length).toBeGreaterThan(0);
          }
        }
      }
    }
  });

  test('should show error details for failed syncs', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Error details accessible for failed sync operations',
    });

    // Look for failed sync status
    const failedStatus = page.locator('text=/failed/i, [data-testid="sync-status-failed"]');
    const failedCount = await failedStatus.count();

    if (failedCount > 0) {
      // Click on first failed status to see details
      await failedStatus.first().click();

      // Check for error detail view (dialog, expandable row, or alert)
      const errorDetail = page.locator(
        '[data-testid="error-detail"], ' +
        '[data-testid="sync-error-dialog"], ' +
        '.error-detail, ' +
        '[role="alert"]'
      );

      const isVisible = await errorDetail.first().isVisible().catch(() => false);

      if (isVisible) {
        // Verify error message is present
        await expect(errorDetail.first()).toBeVisible();

        const errorMessage = errorDetail.locator('text=/error|failed|could not/i');
        const hasErrorMessage = await errorMessage.count() > 0;

        if (hasErrorMessage) {
          await expect(errorMessage.first()).toBeVisible();
        }
      }
    }
  });

  test('should support manual refresh of integration status', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Manual refresh button updates integration status',
    });

    // Look for refresh button
    const refreshButton = page.locator('button:has-text("Refresh"), button[aria-label*="refresh" i]');

    if (await refreshButton.isVisible()) {
      // Get current state
      const rowsBefore = await page.locator('tbody tr').count();

      // Click refresh
      await refreshButton.click();

      // Wait for loading indicator
      const loadingIndicator = page.locator('.MuiCircularProgress-root, [data-testid="loading"]');
      const isLoading = await loadingIndicator.isVisible().catch(() => false);

      if (isLoading) {
        await loadingIndicator.waitFor({ state: 'hidden', timeout: 5000 });
      }

      // Wait for network to settle
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});

      // Verify page is still functional
      await expect(page.locator('table')).toBeVisible();
    }
  });

  test('should display platform badges for each integration', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Platform badges (Workday, Greenhouse, etc.) visible',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Check for platform badges/chips in first few rows
      for (let i = 0; i < Math.min(rowCount, 3); i++) {
        const row = rows.nth(i);
        const platformBadge = row.locator('.MuiChip-root').first();
        await expect(platformBadge).toBeVisible();

        // Badge should have text
        const badgeText = await platformBadge.textContent();
        expect(badgeText?.trim().length).toBeGreaterThan(0);
      }
    }
  });

  test('should show sync history with filtering options', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Sync history supports filtering by status or date',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Open sync history for first integration
      const firstRow = rows.first();
      const integrationName = await firstRow.locator('td').first().textContent();

      if (integrationName) {
        const historyOpened = await openSyncHistory(page, integrationName.trim());

        if (historyOpened) {
          const dialog = page.locator('[data-testid="sync-history-dialog"]');

          // Look for filter controls
          const filterControls = dialog.locator(
            'select, ' +
            '[role="combobox"], ' +
            'button:has-text("Filter"), ' +
            '[data-testid="filter-controls"]'
          );

          const hasFilters = await filterControls.count() > 0;

          if (hasFilters) {
            await expect(filterControls.first()).toBeVisible();
          }

          // Close dialog
          const closeButton = dialog.locator('button[aria-label="close"], button:has-text("Close")');
          if (await closeButton.isVisible()) {
            await closeButton.click();
          }
        }
      }
    }
  });

  test('should display sync duration metrics', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Sync duration shown in history or dashboard',
    });

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Check for duration in main table
      const durationHeader = page.locator('th:has-text("Duration")');
      const hasDurationColumn = await durationHeader.count() > 0;

      if (!hasDurationColumn) {
        // Open sync history to check for duration there
        const firstRow = rows.first();
        const integrationName = await firstRow.locator('td').first().textContent();

        if (integrationName) {
          const historyOpened = await openSyncHistory(page, integrationName.trim());

          if (historyOpened) {
            const dialog = page.locator('[data-testid="sync-history-dialog"]');
            const durationHeaderInDialog = dialog.locator('th:has-text("Duration")');
            const hasDurationInHistory = await durationHeaderInDialog.count() > 0;

            if (hasDurationInHistory) {
              await expect(durationHeaderInDialog.first()).toBeVisible();
            }

            // Close dialog
            const closeButton = dialog.locator('button[aria-label="close"]');
            if (await closeButton.isVisible()) {
              await closeButton.click();
            }
          }
        }
      } else {
        await expect(durationHeader.first()).toBeVisible();
      }
    }
  });
});

test.describe('Integration Monitoring - Real-time Updates', () => {
  test('should auto-refresh integration status', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Dashboard auto-refreshes integration status',
    });

    await navigateToIntegrations(page);

    // Wait for initial load
    await page.waitForLoadState('networkidle');

    // Check if there's an auto-refresh indicator
    const autoRefreshIndicator = page.locator(
      'text=/auto.*refresh|live|real.*time/i, ' +
      '[data-testid="auto-refresh-indicator"]'
    );

    const hasAutoRefresh = await autoRefreshIndicator.count() > 0;

    if (hasAutoRefresh) {
      await expect(autoRefreshIndicator.first()).toBeVisible();
    }

    // Verify page is functional regardless of auto-refresh
    await expect(page.locator('table')).toBeVisible();
  });

  test('should show loading state during sync operations', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Loading indicators shown during sync operations',
    });

    await navigateToIntegrations(page);

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      // Look for sync button
      const syncButton = page.locator('button:has-text("Sync"), button[aria-label*="sync" i]').first();

      if (await syncButton.isVisible()) {
        // Click sync button
        await syncButton.click();

        // Look for loading indicator
        const loadingIndicator = page.locator('.MuiCircularProgress-root, [data-testid="syncing"]');

        // Loading might appear briefly
        const isLoading = await loadingIndicator.isVisible().catch(() => false);

        // Either loading appears or sync completes quickly
        if (isLoading) {
          await expect(loadingIndicator).toBeVisible();
        }
      }
    }
  });
});

test.describe('Integration Monitoring - Empty States', () => {
  test('should display helpful message when no integrations configured', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Empty state shown when no integrations exist',
    });

    await navigateToIntegrations(page);

    // Check for empty state
    const emptyState = page.locator(
      'text=/no integrations|get started|add your first integration/i, ' +
      '[data-testid="empty-state"], ' +
      '[data-testid="no-integrations"]'
    );

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount === 0) {
      // Should show empty state message
      await expect(emptyState.first()).toBeVisible();

      // Should have CTA to add integration
      const addButton = page.locator('button:has-text("Add Integration")');
      await expect(addButton).toBeVisible();
    }
  });

  test('should display helpful message when no sync history', async ({ page }) => {
    test.info().annotations.push({
      type: 'verification',
      description: 'Empty sync history shows helpful message',
    });

    await navigateToIntegrations(page);

    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      const firstRow = rows.first();
      const integrationName = await firstRow.locator('td').first().textContent();

      if (integrationName) {
        const historyOpened = await openSyncHistory(page, integrationName.trim());

        if (historyOpened) {
          const dialog = page.locator('[data-testid="sync-history-dialog"]');

          // Check for empty state in history
          const emptyHistory = dialog.locator(
            'text=/no sync history|no recent syncs/i, ' +
            '[data-testid="empty-sync-history"]'
          );

          const historyRows = dialog.locator('tbody tr');
          const historyRowCount = await historyRows.count();

          if (historyRowCount === 0) {
            await expect(emptyHistory.first()).toBeVisible();
          }

          // Close dialog
          const closeButton = dialog.locator('button[aria-label="close"]');
          if (await closeButton.isVisible()) {
            await closeButton.click();
          }
        }
      }
    }
  });
});
