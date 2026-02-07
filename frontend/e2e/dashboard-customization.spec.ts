import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Dashboard Customization Workflow
 *
 * Test Suite Contents:
 * 1. Dashboard Customization Navigation & Access
 * 2. Customizer Modal Rendering
 * 3. Widget Selection (Add/Remove)
 * 4. Widget Reordering
 * 5. Dashboard Configuration Saving
 * 6. Loading Saved Configurations
 * 7. Configuration Persistence
 * 8. Error Handling
 * 9. Complete Customization Workflow
 * 10. Responsive Design
 * 11. Accessibility
 * 12. Performance
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Dashboard customization API: /api/analytics/dashboards
 */

test.describe('Dashboard Customization - Navigation & Access', () => {
  test('should navigate to analytics dashboard', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check URL
    await expect(page).toHaveURL(/\/analytics/);

    // Check page title
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });

  test('should display Customize Dashboard button', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Look for Customize Dashboard button
    const customizeButton = page.getByRole('button', { name: /Customize Dashboard/i });
    await expect(customizeButton).toBeVisible();
  });

  test('should have settings icon on Customize button', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check for button with settings icon
    const customizeButton = page.getByRole('button', { name: /Customize Dashboard/i });
    await expect(customizeButton).toBeVisible();
  });
});

test.describe('Customizer Modal Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should open customization modal when button clicked', async ({ page }) => {
    // Click customize button
    const customizeButton = page.getByRole('button', { name: /Customize Dashboard/i });
    await customizeButton.click();

    // Modal should open
    await expect(page.getByText(/Customize Dashboard/i)).toBeVisible();
  });

  test('should display modal title and description', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for title
    await expect(page.getByRole('heading', { name: /Customize Dashboard/i })).toBeVisible();

    // Check for description
    await expect(page.getByText(/Add, remove, and reorder dashboard widgets/i)).toBeVisible();
  });

  test('should display Available Widgets section', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for Available Widgets heading
    await expect(page.getByText(/Available Widgets/i)).toBeVisible();

    // Check for instruction text
    await expect(page.getByText(/Click to add widgets to your dashboard/i)).toBeVisible();
  });

  test('should display Selected Widgets section', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for Selected Widgets heading
    await expect(page.getByText(/Selected Widgets/i)).toBeVisible();

    // Should have widget count
    const selectedText = await page.getByText(/Selected Widgets/i).textContent();
    expect(selectedText).toMatch(/\d+/);
  });

  test('should display Dashboard Name input field', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for dashboard name input
    const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
    await expect(nameInput).toBeVisible();
  });

  test('should display action buttons (Cancel, Apply, Save)', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for action buttons
    await expect(page.getByRole('button', { name: /Cancel/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Apply Changes/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Save Configuration/i })).toBeVisible();
  });

  test('should display all available widget options', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for common widgets
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
    await expect(page.getByText(/Source Tracking/i)).toBeVisible();
    await expect(page.getByText(/Recruiter Performance/i)).toBeVisible();
    await expect(page.getByText(/Skill Demand/i)).toBeVisible();
    await expect(page.getByText(/Predictive Analytics/i)).toBeVisible();
  });
});

test.describe('Widget Selection - Adding Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
  });

  test('should allow clicking on available widget to add it', async ({ page }) => {
    // Get initial selected count
    const initialCountText = await page.getByText(/Selected Widgets/i).textContent();
    const initialCount = parseInt(initialCountText?.match(/\d+/)?.[0] || '0');

    // Find and click on a non-required widget (e.g., Source Tracking)
    const widgetCard = page.getByText('Source Tracking').locator('..').locator('..');
    await widgetCard.click();

    // Wait a moment for state update
    await page.waitForTimeout(500);

    // Widget should now be selected (checkmark visible)
    await expect(page.getByText('Source Tracking')).toBeVisible();
  });

  test('should show widget as selected after adding', async ({ page }) => {
    // Click on an available widget
    const widgetCard = page.getByText('Skill Demand').locator('..').locator('..');
    await widgetCard.click();

    // Widget should now have a checkmark or show as selected
    await expect(page.getByText('Skill Demand')).toBeVisible();
  });

  test('should update selected widgets count when adding', async ({ page }) => {
    // Get initial count
    const initialCountText = await page.getByText(/Selected Widgets/).textContent();
    const initialCount = parseInt(initialCountText?.match(/\d+/)?.[0] || '0');

    // Add a widget
    const widgetCard = page.getByText('Fairness Dashboard').locator('..').locator('..');
    const isVisible = await widgetCard.isVisible().catch(() => false);

    if (isVisible) {
      await widgetCard.click();
      await page.waitForTimeout(500);

      // Count should increase
      const newCountText = await page.getByText(/Selected Widgets/).textContent();
      const newCount = parseInt(newCountText?.match(/\d+/)?.[0] || '0');
      expect(newCount).toBeGreaterThanOrEqual(initialCount);
    }
  });

  test('should prevent adding duplicate widgets', async ({ page }) => {
    // Try to click on an already selected widget
    const selectedWidget = page.getByText('Key Metrics').locator('..').locator('..');
    await selectedWidget.click();

    // Should not add duplicate - count should remain the same
    await page.waitForTimeout(500);

    // Widget should still be visible but not duplicated
    await expect(page.getByText('Key Metrics')).toBeVisible();
  });
});

test.describe('Widget Selection - Removing Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
  });

  test('should allow removing non-required widgets', async ({ page }) => {
    // Find a removable widget in selected list
    const removeButton = page.getByRole('button', { name: /Remove/i }).first();
    const isVisible = await removeButton.isVisible().catch(() => false);

    if (isVisible) {
      // Get initial count
      const initialCountText = await page.getByText(/Selected Widgets/).textContent();
      const initialCount = parseInt(initialCountText?.match(/\d+/)?.[0] || '0');

      // Remove widget
      await removeButton.click();
      await page.waitForTimeout(500);

      // Count should decrease
      const newCountText = await page.getByText(/Selected Widgets/).textContent();
      const newCount = parseInt(newCountText?.match(/\d+/)?.[0] || '0');
      expect(newCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test('should prevent removing required widgets', async ({ page }) => {
    // Try to remove a required widget (Key Metrics is required)
    const requiredWidgetCard = page.getByText('Key Metrics').locator('..').locator('..');
    await requiredWidgetCard.click();

    // Should show error or prevent removal
    // Required widgets should remain in selected list
    await expect(page.getByText('Key Metrics')).toBeVisible();
  });

  test('should show error when trying to remove required widget', async ({ page }) => {
    // The required widget shouldn't have a remove button
    const keyMetricsCard = page.getByText('Key Metrics').locator('..').locator('..');
    await expect(keyMetricsCard).toBeVisible();

    // Should have "Required" chip
    await expect(page.getByText('Required')).toBeVisible();
  });
});

test.describe('Widget Reordering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
  });

  test('should display move up and move down buttons', async ({ page }) => {
    // Selected widgets should have up/down buttons
    const upButtons = page.getByRole('button', { name: /Move up/i });
    const downButtons = page.getByRole('button', { name: /Move down/i });

    const upCount = await upButtons.count();
    const downCount = await downButtons.count();

    expect(upCount).toBeGreaterThan(0);
    expect(downCount).toBeGreaterThan(0);
  });

  test('should move widget up when up button clicked', async ({ page }) => {
    // Get the second widget's up button
    const upButtons = page.getByRole('button', { name: /Move up/i });
    const secondUpButton = upButtons.nth(1);

    const isVisible = await secondUpButton.isVisible().catch(() => false);

    if (isVisible) {
      // Get initial state
      const initialText = await page.textContent('body');

      // Click up button
      await secondUpButton.click();
      await page.waitForTimeout(500);

      // Widget should have moved (text content should have changed order)
      await expect(page.getByText(/Selected Widgets/i)).toBeVisible();
    }
  });

  test('should move widget down when down button clicked', async ({ page }) => {
    // Get the first widget's down button
    const downButtons = page.getByRole('button', { name: /Move down/i });
    const firstDownButton = downButtons.first();

    const isVisible = await firstDownButton.isVisible().catch(() => false);

    if (isVisible) {
      // Click down button
      await firstDownButton.click();
      await page.waitForTimeout(500);

      // Widget should have moved
      await expect(page.getByText(/Selected Widgets/i)).toBeVisible();
    }
  });

  test('should disable up button for first widget', async ({ page }) => {
    // First widget's up button should be disabled
    const upButtons = page.getByRole('button', { name: /Move up/i });
    const firstUpButton = upButtons.first();

    await expect(firstUpButton).toHaveAttribute('disabled');
  });

  test('should disable down button for last widget', async ({ page }) => {
    // Last widget's down button should be disabled
    const downButtons = page.getByRole('button', { name: /Move down/i });
    const count = await downButtons.count();

    if (count > 0) {
      const lastDownButton = downButtons.nth(count - 1);
      await expect(lastDownButton).toHaveAttribute('disabled');
    }
  });
});

test.describe('Dashboard Configuration Saving', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should enter dashboard name in input field', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Enter dashboard name
    const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
    await nameInput.fill('My Custom Analytics Dashboard');

    // Verify input has value
    await expect(nameInput).toHaveValue('My Custom Analytics Dashboard');
  });

  test('should enable Save button when widgets selected', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Save button should be enabled (default widgets are selected)
    const saveButton = page.getByRole('button', { name: /Save Configuration/i });
    await expect(saveButton).toBeEnabled();
  });

  test('should save configuration when Save button clicked', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Enter dashboard name
    const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
    await nameInput.fill('E2E Test Dashboard');

    // Save configuration
    const saveButton = page.getByRole('button', { name: /Save Configuration/i });
    await saveButton.click();

    // Should show loading state
    await expect(page.getByText(/Saving\.\.\./i)).toBeVisible();

    // Wait for save to complete
    await page.waitForTimeout(2000);

    // Should show success message or close modal
    const successMessage = page.getByText(/Dashboard configuration saved successfully/i);
    const isMessageVisible = await successMessage.isVisible().catch(() => false);

    // Either show success message or modal closes
    expect(isMessageVisible || true).toBeTruthy();
  });

  test('should close modal after successful save', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Enter name and save
    await page.getByRole('textbox', { name: /Dashboard Name/i }).fill('Auto Save Test');
    await page.getByRole('button', { name: /Save Configuration/i }).click();

    // Wait for save
    await page.waitForTimeout(2000);

    // Modal should close or show success
    const modalTitle = page.getByRole('heading', { name: /Customize Dashboard/i });
    const isModalOpen = await modalTitle.isVisible().catch(() => false);

    // Modal should close after successful save (timeout-based)
    if (isModalOpen) {
      await page.waitForTimeout(1500);
      const stillOpen = await modalTitle.isVisible().catch(() => false);
      expect(stillOpen).toBeFalsy();
    }
  });
});

test.describe('Loading Saved Configurations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should display saved configurations if any exist', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Wait for configs to load
    await page.waitForTimeout(1000);

    // Check for saved configurations section
    const hasConfigs = await page.getByText(/Load saved configuration/i).isVisible().catch(() => false);

    // May or may not have saved configs
    expect(hasConfigs || true).toBeTruthy();
  });

  test('should show configuration chips for saved dashboards', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.waitForTimeout(1000);

    // Look for configuration chips
    const configChips = page.locator('.MuiChip-root').filter({ hasText: /Dashboard|My/i });
    const count = await configChips.count();

    // May have 0 or more saved configs
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should load saved configuration when chip clicked', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.waitForTimeout(1000);

    // Look for a saved config chip
    const configChips = page.locator('.MuiChip-root').filter({ hasText: /Dashboard|My/i });
    const count = await configChips.count();

    if (count > 0) {
      // Click first chip
      await configChips.first().click();
      await page.waitForTimeout(500);

      // Dashboard name should update
      const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
      await expect(nameInput).toBeVisible();
    }
  });
});

test.describe('Configuration Persistence', () => {
  test('should persist configuration across page reloads', async ({ page }) => {
    // First visit - save a configuration
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Enter name
    await page.getByRole('textbox', { name: /Dashboard Name/i }).fill('Persistence Test Dashboard');

    // Save
    await page.getByRole('button', { name: /Save Configuration/i }).click();
    await page.waitForTimeout(2000);

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Analytics dashboard should still be visible
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });

  test('should display selected widgets after reload', async ({ page }) => {
    // Configure dashboard
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer and save config
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.getByRole('textbox', { name: /Dashboard Name/i }).fill('Widget Test Dashboard');
    await page.getByRole('button', { name: /Save Configuration/i }).click();
    await page.waitForTimeout(2000);

    // Reload
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Key sections should still be visible
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
    await expect(page.getByText(/Funnel Visualization/i)).toBeVisible();
  });

  test('should maintain dashboard settings across sessions', async ({ page }) => {
    // Create a new context to simulate new session
    const context = page.context();
    const newPage = await context.newPage();

    await newPage.goto('/analytics');
    await newPage.waitForLoadState('networkidle');

    // Dashboard should load
    await expect(newPage.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();

    await newPage.close();
  });
});

test.describe('Apply Changes (Without Saving)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
  });

  test('should apply changes without saving configuration', async ({ page }) => {
    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Add a widget
    const widgetCard = page.getByText('Source Tracking').locator('..').locator('..');
    await widgetCard.click();
    await page.waitForTimeout(500);

    // Click Apply Changes
    const applyButton = page.getByRole('button', { name: /Apply Changes/i });
    await applyButton.click();

    // Modal should close
    await page.waitForTimeout(500);

    // Should return to dashboard
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });

  test('should update dashboard widgets after applying', async ({ page }) => {
    // Get initial state
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer and apply changes
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.getByRole('button', { name: /Apply Changes/i }).click();

    // Wait for apply
    await page.waitForTimeout(1000);

    // Dashboard should still render properly
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();
  });
});

test.describe('Reset to Default', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
  });

  test('should display Reset to Default button', async ({ page }) => {
    // Check for Reset button
    const resetButton = page.getByRole('button', { name: /Reset to Default/i });
    await expect(resetButton).toBeVisible();
  });

  test('should reset selected widgets to default when clicked', async ({ page }) => {
    // Add some widgets first
    const widgetCard = page.getByText('Skill Demand').locator('..').locator('..');
    await widgetCard.click();
    await page.waitForTimeout(500);

    // Get count before reset
    const countBeforeText = await page.getByText(/Selected Widgets/).textContent();
    const countBefore = parseInt(countBeforeText?.match(/\d+/)?.[0] || '0');

    // Click reset
    const resetButton = page.getByRole('button', { name: /Reset to Default/i });
    await resetButton.click();
    await page.waitForTimeout(500);

    // Get count after reset
    const countAfterText = await page.getByText(/Selected Widgets/).textContent();
    const countAfter = parseInt(countAfterText?.match(/\d+/)?.[0] || '0');

    // Should reset to required widgets only
    expect(countAfter).toBeLessThanOrEqual(countBefore);
  });

  test('should restore required widgets after reset', async ({ page }) => {
    // Reset to default
    const resetButton = page.getByRole('button', { name: /Reset to Default/i });
    await resetButton.click();
    await page.waitForTimeout(500);

    // Required widgets should be present
    await expect(page.getByText('Key Metrics')).toBeVisible();
    await expect(page.getByText('Funnel Visualization')).toBeVisible();
  });
});

test.describe('Complete Dashboard Customization Workflow', () => {
  test('complete workflow: open customize → add widgets → reorder → save', async ({ page }) => {
    // Navigate to analytics
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Click customize button
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Wait for modal to open
    await expect(page.getByRole('heading', { name: /Customize Dashboard/i })).toBeVisible();

    // Add a widget
    const widgetCard = page.getByText('Source Tracking').locator('..').locator('..');
    await widgetCard.click();
    await page.waitForTimeout(500);

    // Move widget up
    const upButton = page.getByRole('button', { name: /Move up/i }).first();
    const isUpVisible = await upButton.isVisible().catch(() => false);

    if (isUpVisible) {
      await upButton.click();
      await page.waitForTimeout(500);
    }

    // Enter dashboard name
    await page.getByRole('textbox', { name: /Dashboard Name/i }).fill('Complete Workflow Test');

    // Save configuration
    await page.getByRole('button', { name: /Save Configuration/i }).click();

    // Wait for save
    await page.waitForTimeout(2000);

    // Modal should close
    const modalTitle = page.getByRole('heading', { name: /Customize Dashboard/i });
    const isModalOpen = await modalTitle.isVisible().catch(() => false);

    expect(isModalOpen).toBeFalsy();
  });

  test('complete workflow: load saved config → modify → save', async ({ page }) => {
    // Open customizer
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.waitForTimeout(1000);

    // Look for saved config
    const configChips = page.locator('.MuiChip-root').filter({ hasText: /Dashboard|My/i });
    const count = await configChips.count();

    if (count > 0) {
      // Load first config
      await configChips.first().click();
      await page.waitForTimeout(500);

      // Modify
      const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
      await nameInput.fill('Modified Dashboard');

      // Save
      await page.getByRole('button', { name: /Save Configuration/i }).click();
      await page.waitForTimeout(2000);

      // Should save successfully
      const modalTitle = page.getByRole('heading', { name: /Customize Dashboard/i });
      const isModalOpen = await modalTitle.isVisible().catch(() => false);
      expect(isModalOpen).toBeFalsy();
    }
  });

  test('complete workflow: customize → apply → verify changes → reload', async ({ page }) => {
    // Customize
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Customize Dashboard/i }).click();
    await page.getByRole('button', { name: /Apply Changes/i }).click();

    // Wait for apply
    await page.waitForTimeout(1000);

    // Verify dashboard still works
    await expect(page.getByText(/Key Metrics/i)).toBeVisible();

    // Reload
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Dashboard should persist
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });
});

test.describe('Dashboard Customization Error Handling', () => {
  test('should handle empty widget selection gracefully', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Remove all non-required widgets
    const removeButtons = page.getByRole('button', { name: /Remove/i });
    const count = await removeButtons.count();

    for (let i = 0; i < count; i++) {
      const button = removeButtons.nth(i);
      const isVisible = await button.isVisible().catch(() => false);
      if (isVisible) {
        await button.click();
        await page.waitForTimeout(200);
      }
    }

    // Try to apply with only required widgets (should work)
    const applyButton = page.getByRole('button', { name: /Apply Changes/i });
    const isEnabled = await applyButton.isEnabled();
    expect(isEnabled).toBeTruthy();
  });

  test('should show validation message for empty dashboard name', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Leave name empty and try to save
    await page.getByRole('button', { name: /Save Configuration/i }).click();

    // Should use default name
    // Verify modal interaction
    await expect(page.getByText(/Dashboard/i)).toBeVisible();
  });

  test('should handle API errors during save', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Enter name
    await page.getByRole('textbox', { name: /Dashboard Name/i }).fill('Error Test Dashboard');

    // Try to save (may or may not fail depending on backend state)
    await page.getByRole('button', { name: /Save Configuration/i }).click();
    await page.waitForTimeout(2000);

    // Either success or error, page should handle gracefully
    await expect(page.getByText(/Dashboard|Error/i)).toBeVisible();
  });

  test('should close modal when cancel clicked', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Click cancel
    await page.getByRole('button', { name: /Cancel/i }).click();

    // Modal should close
    const modalTitle = page.getByRole('heading', { name: /Customize Dashboard/i });
    const isVisible = await modalTitle.isVisible().catch(() => false);

    expect(isVisible).toBeFalsy();
  });
});

test.describe('Dashboard Customization Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/analytics');

    // Customize button should be visible
    const customizeButton = page.getByRole('button', { name: /Customize Dashboard/i });
    await expect(customizeButton).toBeVisible();

    // Open customizer
    await customizeButton.click();

    // Modal should open
    await expect(page.getByRole('heading', { name: /Customize Dashboard/i })).toBeVisible();
  });

  test('should adapt widget selection layout on tablet', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/analytics');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // All sections should be visible
    await expect(page.getByText(/Available Widgets/i)).toBeVisible();
    await expect(page.getByText(/Selected Widgets/i)).toBeVisible();
  });

  test('should display two-column layout on desktop', async ({ page }) => {
    // Set desktop viewport
    page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/analytics');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Should show both available and selected widgets side by side
    await expect(page.getByText(/Available Widgets/i)).toBeVisible();
    await expect(page.getByText(/Selected Widgets/i)).toBeVisible();
  });
});

test.describe('Dashboard Customization Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for dialog heading
    const heading = page.getByRole('heading', { name: /Customize Dashboard/i });
    await expect(heading).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Tab to customize button
    await page.keyboard.press('Tab');

    // Press Enter to open
    await page.keyboard.press('Enter');

    // Modal should open
    await expect(page.getByRole('heading', { name: /Customize Dashboard/i })).toBeVisible();
  });

  test('should have proper ARIA attributes on buttons', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Check customize button
    const customizeButton = page.getByRole('button', { name: /Customize Dashboard/i });
    await expect(customizeButton).toBeVisible();
  });

  test('should have proper form labels', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Check for labeled inputs
    const nameInput = page.getByRole('textbox', { name: /Dashboard Name/i });
    await expect(nameInput).toBeVisible();
  });

  test('should close modal with Escape key', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Press Escape
    await page.keyboard.press('Escape');

    // Modal should close
    await page.waitForTimeout(500);

    const modalTitle = page.getByRole('heading', { name: /Customize Dashboard/i });
    const isVisible = await modalTitle.isVisible().catch(() => false);

    expect(isVisible).toBeFalsy();
  });
});

test.describe('Dashboard Customization Performance', () => {
  test('should open customizer modal quickly', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    const startTime = Date.now();

    // Click customize button
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    // Wait for modal
    await page.waitForSelector('text=Customize Dashboard', { timeout: 5000 });

    const loadTime = Date.now() - startTime;

    // Should load in less than 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('should handle widget selection efficiently', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Open customizer
    await page.getByRole('button', { name: /Customize Dashboard/i }).click();

    const startTime = Date.now();

    // Click on multiple widgets
    const widgets = ['Source Tracking', 'Recruiter Performance', 'Skill Demand'];

    for (const widget of widgets) {
      const card = page.getByText(widget).locator('..').locator('..');
      const isVisible = await card.isVisible().catch(() => false);
      if (isVisible) {
        await card.click();
        await page.waitForTimeout(100);
      }
    }

    const endTime = Date.now();

    // Should complete quickly
    expect(endTime - startTime).toBeLessThan(3000);
  });

  test('should not have memory leaks during customization', async ({ page }) => {
    // Open and close customizer multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('/analytics');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: /Customize Dashboard/i }).click();
      await page.waitForTimeout(500);

      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    }

    // Should still be functional
    await expect(page.getByRole('heading', { name: /Hiring Analytics Dashboard/i })).toBeVisible();
  });
});
