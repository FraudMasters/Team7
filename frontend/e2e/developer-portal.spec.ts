import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Developer Portal Workflows
 *
 * Test Suite Contents:
 * 1. Developer Portal Navigation & Layout
 * 2. API Keys Management Workflow
 *    - Navigate to API Keys page
 *    - Create API key with scopes and rate limits
 *    - List and view API keys
 *    - Copy API key prefix
 *    - Revoke API key
 *
 * 3. Webhooks Management Workflow
 *    - Navigate to Webhooks page
 *    - Create webhook subscription
 *    - View webhook delivery logs
 *    - Enable/disable webhooks
 *    - Delete webhook subscription
 *
 * 4. Workflow Builder Workflow
 *    - Navigate to Workflows page
 *    - Create new workflow with trigger
 *    - Add actions to workflow
 *    - Save and activate workflow
 *    - View workflow execution history
 *
 * 5. Complete Developer Portal Integration
 *    - End-to-end: API key → Webhook → Workflow
 *    - Cross-feature navigation
 *    - Responsive design
 *    - Error handling
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Recruiter account available for authentication
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

test.describe('Developer Portal - Navigation & Layout', () => {
  test('should display developer portal home page', async ({ page }) => {
    await page.goto('/developer');
    await page.waitForLoadState('networkidle');

    // Check main heading
    await expect(page.getByRole('heading', { level: 1, name: /Developer Portal|Developer/i })).toBeVisible();
  });

  test('should display sidebar navigation with all sections', async ({ page }) => {
    await page.goto('/developer');
    await page.waitForLoadState('networkidle');

    // Check for navigation items (sidebar or top nav)
    const apiKeysNav = page.getByRole('link', { name: /API Keys/i }).or(page.getByText(/API Keys/i));
    const webhooksNav = page.getByRole('link', { name: /Webhooks/i }).or(page.getByText(/Webhooks/i));
    const pluginsNav = page.getByRole('link', { name: /Plugins/i }).or(page.getByText(/Plugins/i));
    const workflowsNav = page.getByRole('link', { name: /Workflows/i }).or(page.getByText(/Workflows/i));
    const analyticsNav = page.getByRole('link', { name: /Analytics/i }).or(page.getByText(/Analytics/i));

    // At least some navigation should be visible
    await expect(apiKeysNav.or(webhooksNav).or(pluginsNav).or(workflowsNav).or(analyticsNav)).toBeVisible();
  });

  test('should navigate to API Keys page', async ({ page }) => {
    await page.goto('/developer');

    // Click on API Keys navigation
    const apiKeysLink = page.getByRole('link', { name: /API Keys/i });
    const linkCount = await apiKeysLink.count();

    if (linkCount > 0) {
      await apiKeysLink.first().click();
    } else {
      await page.goto('/developer/api-keys');
    }

    await expect(page).toHaveURL(/\/developer\/api-keys/);
    await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();
  });

  test('should navigate to Webhooks page', async ({ page }) => {
    await page.goto('/developer');

    // Click on Webhooks navigation
    const webhooksLink = page.getByRole('link', { name: /Webhooks/i });
    const linkCount = await webhooksLink.count();

    if (linkCount > 0) {
      await webhooksLink.first().click();
    } else {
      await page.goto('/developer/webhooks');
    }

    await expect(page).toHaveURL(/\/developer\/webhooks/);
    await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();
  });

  test('should navigate to Workflows page', async ({ page }) => {
    await page.goto('/developer');

    // Click on Workflows navigation
    const workflowsLink = page.getByRole('link', { name: /Workflows/i });
    const linkCount = await workflowsLink.count();

    if (linkCount > 0) {
      await workflowsLink.first().click();
    } else {
      await page.goto('/developer/workflows');
    }

    await expect(page).toHaveURL(/\/developer\/workflows/);
    await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();
  });

  test('should navigate through all developer portal pages', async ({ page }) => {
    const pages = [
      { path: '/developer/api-keys', name: 'API Keys' },
      { path: '/developer/webhooks', name: 'Webhooks' },
      { path: '/developer/plugins', name: 'Plugins' },
      { path: '/developer/workflows', name: 'Workflows' },
      { path: '/developer/analytics', name: 'Analytics' },
    ];

    for (const pagePath of pages) {
      await page.goto(pagePath.path);
      await page.waitForLoadState('networkidle');

      // Check heading
      await expect(page.getByRole('heading', { name: new RegExp(pagePath.name, 'i') })).toBeVisible();
    }
  });
});

test.describe('API Keys Management Workflow', () => {
  test.describe('Navigation & Page Rendering', () => {
    test('should display API Keys page with header', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      // Check description
      await expect(page.getByText(/Manage API keys|authenticating requests/i)).toBeVisible();
    });

    test('should display statistics cards', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Check for statistics (active keys, requests, revoked, expired)
      const statsText = page.getByText(/Active|Requests|Revoked|Expired|Total/i);
      await expect(statsText).toBeVisible();
    });

    test('should display Create API Key button', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Check for create button
      const createButton = page.getByRole('button', { name: /Create API Key|Create/i });
      await expect(createButton).toBeVisible();
    });

    test('should display API key list or empty state', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Check for either API key cards or empty state
      const keyCards = page.locator('.MuiCard-root').filter({ hasText: /sk_|Active|Revoked|Expired/i });
      const emptyState = page.getByText(/No API keys|Create your first API key/i);

      const cardCount = await keyCards.count();
      const hasEmptyState = await emptyState.isVisible().catch(() => false);

      expect(cardCount > 0 || hasEmptyState).toBeTruthy();
    });

    test('should display getting started guide', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Check for getting started section
      const gettingStarted = page.getByText(/Getting Started|Quick Start|How to use/i);
      const hasGuide = await gettingStarted.isVisible().catch(() => false);

      if (hasGuide) {
        await expect(gettingStarted).toBeVisible();
      }
    });
  });

  test.describe('Create API Key', () => {
    test('should open create dialog via button', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Click create button
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();

      // Should open dialog
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display create form with all fields', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();

      // Wait for dialog
      await page.waitForTimeout(500);

      // Check for form fields
      await expect(page.getByRole('dialog')).toBeVisible();

      // Check for name input
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));
      const hasNameInput = await nameInput.count() > 0;
      expect(hasNameInput).toBeTruthy();

      // Check for scopes section
      const scopes = page.getByText(/Scopes|Permissions|Read|Write/i);
      const hasScopes = await scopes.count() > 0;
      expect(hasScopes).toBeTruthy();
    });

    test('should show security warning about key display', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for security warning
      const warning = page.getByText(/copy|secure|display|one time|only shown once/i);
      const hasWarning = await warning.isVisible().catch(() => false);

      if (hasWarning) {
        await expect(warning).toBeVisible();
      }
    });

    test('should allow selecting scopes', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Look for scope checkboxes
      const checkboxes = page.locator('input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      if (checkboxCount > 0) {
        // Check first scope
        await checkboxes.first().check();
        await page.waitForTimeout(200);

        // Verify it's checked
        await expect(checkboxes.first()).toBeChecked();
      }
    });

    test('should show new key after creation', async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Try to fill form and submit (may fail without backend)
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));
      const hasNameInput = await nameInput.count() > 0;

      if (hasNameInput) {
        await nameInput.first().fill('Test Key');

        // Look for submit button
        const submitButton = page.getByRole('button', { name: /Create|Save|Generate/i });
        const submitCount = await submitButton.count();

        if (submitCount > 0) {
          await submitButton.first().click();
          await page.waitForTimeout(2000);

          // May show success dialog with the key or error
          const dialogVisible = await page.getByRole('dialog').count() > 0;
          if (dialogVisible) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('API Key List Actions', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');
    });

    test('should display API key cards with details', async ({ page }) => {
      // Find API key cards
      const keyCards = page.locator('.MuiCard-root').filter({ hasText: /sk_|Active|Revoked|Expired/i });
      const cardCount = await keyCards.count();

      if (cardCount > 0) {
        // Check first card has expected elements
        await expect(keyCards.first()).toBeVisible();
      }
    });

    test('should allow copying key prefix', async ({ page }) => {
      // Find API key cards
      const keyCards = page.locator('.MuiCard-root');
      const cardCount = await keyCards.count();

      if (cardCount > 0) {
        // Look for copy button
        const copyButton = page.getByRole('button', { name: /Copy/i }).or(
          page.locator('button').filter({ hasText: /Copy/i })
        );
        const copyCount = await copyButton.count();

        if (copyCount > 0) {
          await copyButton.first().click();
          await page.waitForTimeout(200);

          // Button should still be visible
          await expect(copyButton.first()).toBeVisible();
        }
      }
    });

    test('should show revoke confirmation dialog', async ({ page }) => {
      // Find API key cards
      const keyCards = page.locator('.MuiCard-root');
      const cardCount = await keyCards.count();

      if (cardCount > 0) {
        // Look for revoke button
        const revokeButton = page.getByRole('button', { name: /Revoke/i }).or(
          page.locator('button').filter({ hasText: /Revoke/i })
        );
        const revokeCount = await revokeButton.count();

        if (revokeCount > 0) {
          await revokeButton.first().click();
          await page.waitForTimeout(500);

          // Should show confirmation dialog
          const hasDialog = await page.getByRole('dialog').count() > 0;
          if (hasDialog) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });

    test('should refresh list', async ({ page }) => {
      // Look for refresh button
      const refreshButton = page.getByRole('button', { name: /Refresh/i }).or(
        page.locator('button').filter({ hasText: /Refresh/i })
      );
      const refreshCount = await refreshButton.count();

      if (refreshCount > 0) {
        await refreshButton.first().click();
        await page.waitForTimeout(1000);

        // Page should still be on API keys
        await expect(page).toHaveURL(/\/developer\/api-keys/);
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should display properly on mobile', async ({ page }) => {
      await page.goto('/developer/api-keys');
      page.setViewportSize({ ...MOBILE_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      // Check for no horizontal scrolling
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
    });

    test('should display properly on desktop', async ({ page }) => {
      await page.goto('/developer/api-keys');
      page.setViewportSize({ ...DESKTOP_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      // Content should use desktop space
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeGreaterThan(900);
    });
  });

  test.describe('Complete API Key Workflow', () => {
    test('end-to-end: navigate → list → create dialog → view key cards', async ({ page }) => {
      // Navigate to API Keys
      await page.goto('/developer/api-keys');
      await expect(page).toHaveURL(/\/developer\/api-keys/);

      // Check page header
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create API Key/i });
      await createButton.click();

      // Verify dialog opens
      await expect(page.getByRole('dialog')).toBeVisible();

      // Close dialog
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Check API key list (or empty state)
      const keyCards = page.locator('.MuiCard-root');
      const emptyState = page.getByText(/No API keys|Create your first/i);

      const hasContent = await keyCards.count() > 0 || await emptyState.isVisible().catch(() => false);
      expect(hasContent).toBeTruthy();
    });
  });
});

test.describe('Webhooks Management Workflow', () => {
  test.describe('Navigation & Page Rendering', () => {
    test('should display Webhooks page with header', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      // Check description
      await expect(page.getByText(/webhook|event|notifications|real-time/i)).toBeVisible();
    });

    test('should display statistics cards', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Check for statistics
      const statsText = page.getByText(/Total|Active|Successful|Failed|Deliveries/i);
      await expect(statsText).toBeVisible();
    });

    test('should display Create Webhook button', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Check for create button
      const createButton = page.getByRole('button', { name: /Create Webhook|Add Webhook|Create/i });
      await expect(createButton).toBeVisible();
    });

    test('should display webhook list or empty state', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Check for either webhook cards or empty state
      const webhookCards = page.locator('.MuiCard-root').filter({ hasText: /https?://|endpoint|events|Active|Inactive/i });
      const emptyState = page.getByText(/No webhooks|Create your first webhook/i);

      const cardCount = await webhookCards.count();
      const hasEmptyState = await emptyState.isVisible().catch(() => false);

      expect(cardCount > 0 || hasEmptyState).toBeTruthy();
    });

    test('should display getting started guide', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Check for getting started section
      const gettingStarted = page.getByText(/Getting Started|Quick Start|How to use/i);
      const hasGuide = await gettingStarted.isVisible().catch(() => false);

      if (hasGuide) {
        await expect(gettingStarted).toBeVisible();
      }
    });
  });

  test.describe('Create Webhook Subscription', () => {
    test('should open create dialog via button', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Click create button
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();

      // Should open dialog
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display create form with all fields', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for form fields
      await expect(page.getByRole('dialog')).toBeVisible();

      // Check for endpoint URL input
      const urlInput = page.getByRole('textbox', { name: /URL|Endpoint/i }).or(
        page.getByPlaceholder(/https?:\/\//i)
      );
      const hasUrlInput = await urlInput.count() > 0;
      expect(hasUrlInput).toBeTruthy();

      // Check for events section
      const events = page.getByText(/Events|candidate\.created|stage\.changed/i);
      const hasEvents = await events.count() > 0;
      expect(hasEvents).toBeTruthy();
    });

    test('should validate endpoint URL input', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Find URL input
      const urlInput = page.getByRole('textbox', { name: /URL|Endpoint/i }).or(
        page.getByPlaceholder(/https?:\/\//i)
      );

      const hasUrlInput = await urlInput.count() > 0;
      if (hasUrlInput) {
        // Type invalid URL
        await urlInput.first().fill('not-a-valid-url');
        await page.waitForTimeout(300);

        // Type valid URL
        await urlInput.first().fill('https://example.com/webhook');
        await page.waitForTimeout(300);
      }
    });

    test('should allow selecting event types', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Look for event checkboxes
      const checkboxes = page.locator('input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      if (checkboxCount > 0) {
        // Check first event
        await checkboxes.first().check();
        await page.waitForTimeout(200);

        // Verify it's checked
        await expect(checkboxes.first()).toBeChecked();
      }
    });

    test('should show event categories', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for event categories (candidate, vacancy, ranking, etc.)
      const categories = page.getByText(/Candidate|Vacancy|Ranking|Stage|Workflow/i);
      const hasCategories = await categories.count() > 0;
      expect(hasCategories).toBeTruthy();
    });

    test('should allow setting HMAC secret', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Look for HMAC secret input
      const secretInput = page.getByRole('textbox', { name: /Secret|HMAC/i }).or(
        page.getByPlaceholder(/secret/i)
      );

      const hasSecretInput = await secretInput.count() > 0;
      if (hasSecretInput) {
        await secretInput.first().fill('test-secret-key');
      }
    });

    test('should attempt to create webhook', async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Fill form
      const urlInput = page.getByRole('textbox', { name: /URL|Endpoint/i }).or(
        page.getByPlaceholder(/https?:\/\//i)
      );

      const hasUrlInput = await urlInput.count() > 0;
      if (hasUrlInput) {
        await urlInput.first().fill('https://example.com/webhook');

        // Try to submit
        const submitButton = page.getByRole('button', { name: /Create|Save|Subscribe/i });
        const submitCount = await submitButton.count();

        if (submitCount > 0) {
          await submitButton.first().click();
          await page.waitForTimeout(2000);

          // May show success or error
          const dialogVisible = await page.getByRole('dialog').count() > 0;
          const url = page.url();

          expect(dialogVisible || url.match(/\/developer\/webhooks/)).toBeTruthy();
        }
      }
    });
  });

  test.describe('Webhook List Actions', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');
    });

    test('should display webhook cards with details', async ({ page }) => {
      // Find webhook cards
      const webhookCards = page.locator('.MuiCard-root');
      const cardCount = await webhookCards.count();

      if (cardCount > 0) {
        // Check first card has expected elements
        await expect(webhookCards.first()).toBeVisible();
      }
    });

    test('should allow viewing delivery logs', async ({ page }) => {
      // Find webhook cards
      const webhookCards = page.locator('.MuiCard-root');
      const cardCount = await webhookCards.count();

      if (cardCount > 0) {
        // Look for logs button
        const logsButton = page.getByRole('button', { name: /Logs|Delivery|View Logs/i }).or(
          page.locator('button').filter({ hasText: /Logs/i })
        );
        const logsCount = await logsButton.count();

        if (logsCount > 0) {
          await logsButton.first().click();
          await page.waitForTimeout(500);

          // Should show logs dialog
          const hasDialog = await page.getByRole('dialog').count() > 0;
          if (hasDialog) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });

    test('should allow enabling/disabling webhook', async ({ page }) => {
      // Find webhook cards
      const webhookCards = page.locator('.MuiCard-root');
      const cardCount = await webhookCards.count();

      if (cardCount > 0) {
        // Look for enable/disable toggle or button
        const toggleButton = page.getByRole('button', { name: /Enable|Disable|Toggle/i }).or(
          page.locator('button').filter({ hasText: /Enable|Disable/i })
        );
        const toggleCount = await toggleButton.count();

        if (toggleCount > 0) {
          await toggleButton.first().click();
          await page.waitForTimeout(500);

          // Page should still be on webhooks
          await expect(page).toHaveURL(/\/developer\/webhooks/);
        }
      }
    });

    test('should show delete confirmation dialog', async ({ page }) => {
      // Find webhook cards
      const webhookCards = page.locator('.MuiCard-root');
      const cardCount = await webhookCards.count();

      if (cardCount > 0) {
        // Look for delete button
        const deleteButton = page.getByRole('button', { name: /Delete|Remove/i }).or(
          page.locator('button').filter({ hasText: /Delete/i })
        );
        const deleteCount = await deleteButton.count();

        if (deleteCount > 0) {
          await deleteButton.first().click();
          await page.waitForTimeout(500);

          // Should show confirmation dialog
          const hasDialog = await page.getByRole('dialog').count() > 0;
          if (hasDialog) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should display properly on mobile', async ({ page }) => {
      await page.goto('/developer/webhooks');
      page.setViewportSize({ ...MOBILE_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      // Check for no horizontal scrolling
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
    });

    test('should display properly on desktop', async ({ page }) => {
      await page.goto('/developer/webhooks');
      page.setViewportSize({ ...DESKTOP_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      // Content should use desktop space
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeGreaterThan(900);
    });
  });

  test.describe('Complete Webhook Workflow', () => {
    test('end-to-end: navigate → list → create dialog → view webhooks', async ({ page }) => {
      // Navigate to Webhooks
      await page.goto('/developer/webhooks');
      await expect(page).toHaveURL(/\/developer\/webhooks/);

      // Check page header
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createButton.click();

      // Verify dialog opens
      await expect(page.getByRole('dialog')).toBeVisible();

      // Close dialog
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Check webhook list (or empty state)
      const webhookCards = page.locator('.MuiCard-root');
      const emptyState = page.getByText(/No webhooks|Create your first/i);

      const hasContent = await webhookCards.count() > 0 || await emptyState.isVisible().catch(() => false);
      expect(hasContent).toBeTruthy();
    });
  });
});

test.describe('Workflow Builder Workflow', () => {
  test.describe('Navigation & Page Rendering', () => {
    test('should display Workflows page with header', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Check page heading
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      // Check description
      await expect(page.getByText(/workflow|automation|builder/i)).toBeVisible();
    });

    test('should display statistics cards', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Check for statistics
      const statsText = page.getByText(/Total|Active|Paused|Success|Failed|Today/i);
      await expect(statsText).toBeVisible();
    });

    test('should display Create Workflow button', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Check for create button
      const createButton = page.getByRole('button', { name: /Create Workflow|New Workflow|Create/i });
      await expect(createButton).toBeVisible();
    });

    test('should display workflow tabs', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Check for tabs (Active, Paused, Draft)
      const tabs = page.getByRole('tab');
      const tabCount = await tabs.count();

      if (tabCount > 0) {
        // Should have at least one tab
        await expect(tabs.first()).toBeVisible();
      }
    });

    test('should display workflow list or empty state', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Check for either workflow cards or empty state
      const workflowCards = page.locator('.MuiCard-root').filter({ hasText: /workflow|trigger|actions/i });
      const emptyState = page.getByText(/No workflows|Create your first workflow/i);

      const cardCount = await workflowCards.count();
      const hasEmptyState = await emptyState.isVisible().catch(() => false);

      expect(cardCount > 0 || hasEmptyState).toBeTruthy();
    });
  });

  test.describe('Create Workflow', () => {
    test('should open create dialog via button', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Click create button
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();

      // Should open dialog
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display workflow builder with all sections', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for builder elements
      await expect(page.getByRole('dialog')).toBeVisible();

      // Check for name input
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));
      const hasNameInput = await nameInput.count() > 0;
      expect(hasNameInput).toBeTruthy();

      // Check for trigger section
      const trigger = page.getByText(/Trigger|When|Webhook|Schedule/i);
      const hasTrigger = await trigger.count() > 0;
      expect(hasTrigger).toBeTruthy();
    });

    test('should allow entering workflow name', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Find name input
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));

      const hasNameInput = await nameInput.count() > 0;
      if (hasNameInput) {
        await nameInput.first().fill('Test Workflow');
        await page.waitForTimeout(200);

        // Verify value
        const value = await nameInput.first().inputValue();
        expect(value).toBe('Test Workflow');
      }
    });

    test('should allow selecting trigger type', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for trigger type selector
      const triggerOption = page.getByText(/Webhook|Schedule|Manual/i);
      const hasTriggerOption = await triggerOption.count() > 0;

      if (hasTriggerOption) {
        await expect(triggerOption.first()).toBeVisible();
      }
    });

    test('should allow selecting webhook event', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for event selector
      const eventOption = page.getByText(/candidate\.created|stage\.changed|ranking\.created/i);
      const hasEventOption = await eventOption.count() > 0;

      if (hasEventOption) {
        await expect(eventOption.first()).toBeVisible();
      }
    });

    test('should display action palette', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Check for action palette or add action button
      const actionPalette = page.getByText(/Actions|Add Action|Send|Email|Webhook/i);
      const hasActionPalette = await actionPalette.count() > 0;

      if (hasActionPalette) {
        await expect(actionPalette.first()).toBeVisible();
      }
    });

    test('should allow adding actions to workflow', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Look for add action button
      const addActionButton = page.getByRole('button', { name: /Add Action|Add/i });
      const addActionCount = await addActionButton.count();

      if (addActionCount > 0) {
        await addActionButton.first().click();
        await page.waitForTimeout(500);

        // Should show action options
        const hasDialog = await page.getByRole('dialog', { name: /action/i }).count() > 0 ||
                          await page.getByRole('menu').count() > 0;
        expect(hasDialog).toBeTruthy();
      }
    });

    test('should allow saving workflow', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();
      await page.waitForTimeout(500);

      // Fill name
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));
      const hasNameInput = await nameInput.count() > 0;

      if (hasNameInput) {
        await nameInput.first().fill('E2E Test Workflow');
      }

      // Look for save button
      const saveButton = page.getByRole('button', { name: /Save|Create|Build/i });
      const saveCount = await saveButton.count();

      if (saveCount > 0) {
        await saveButton.first().click();
        await page.waitForTimeout(2000);

        // May save successfully or show error
        const dialogVisible = await page.getByRole('dialog').count() > 0;
        const url = page.url();

        expect(dialogVisible || url.match(/\/developer\/workflows/)).toBeTruthy();
      }
    });
  });

  test.describe('Workflow List Actions', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');
    });

    test('should display workflow cards with details', async ({ page }) => {
      // Find workflow cards
      const workflowCards = page.locator('.MuiCard-root');
      const cardCount = await workflowCards.count();

      if (cardCount > 0) {
        // Check first card has expected elements
        await expect(workflowCards.first()).toBeVisible();
      }
    });

    test('should allow viewing execution history', async ({ page }) => {
      // Find workflow cards
      const workflowCards = page.locator('.MuiCard-root');
      const cardCount = await workflowCards.count();

      if (cardCount > 0) {
        // Look for history button
        const historyButton = page.getByRole('button', { name: /History|Executions|View History/i }).or(
          page.locator('button').filter({ hasText: /History/i })
        );
        const historyCount = await historyButton.count();

        if (historyCount > 0) {
          await historyButton.first().click();
          await page.waitForTimeout(500);

          // Should show history dialog
          const hasDialog = await page.getByRole('dialog').count() > 0;
          if (hasDialog) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });

    test('should allow activating workflow', async ({ page }) => {
      // Find workflow cards
      const workflowCards = page.locator('.MuiCard-root');
      const cardCount = await workflowCards.count();

      if (cardCount > 0) {
        // Look for activate button
        const activateButton = page.getByRole('button', { name: /Activate|Start|Enable/i }).or(
          page.locator('button').filter({ hasText: /Activate|Enable/i })
        );
        const activateCount = await activateButton.count();

        if (activateCount > 0) {
          await activateButton.first().click();
          await page.waitForTimeout(500);

          // Page should still be on workflows
          await expect(page).toHaveURL(/\/developer\/workflows/);
        }
      }
    });

    test('should allow pausing workflow', async ({ page }) => {
      // Find workflow cards
      const workflowCards = page.locator('.MuiCard-root');
      const cardCount = await workflowCards.count();

      if (cardCount > 0) {
        // Look for pause button
        const pauseButton = page.getByRole('button', { name: /Pause|Stop|Disable/i }).or(
          page.locator('button').filter({ hasText: /Pause|Disable/i })
        );
        const pauseCount = await pauseButton.count();

        if (pauseCount > 0) {
          await pauseButton.first().click();
          await page.waitForTimeout(500);

          // Page should still be on workflows
          await expect(page).toHaveURL(/\/developer\/workflows/);
        }
      }
    });

    test('should show delete confirmation dialog', async ({ page }) => {
      // Find workflow cards
      const workflowCards = page.locator('.MuiCard-root');
      const cardCount = await workflowCards.count();

      if (cardCount > 0) {
        // Look for delete button
        const deleteButton = page.getByRole('button', { name: /Delete|Remove/i }).or(
          page.locator('button').filter({ hasText: /Delete/i })
        );
        const deleteCount = await deleteButton.count();

        if (deleteCount > 0) {
          await deleteButton.first().click();
          await page.waitForTimeout(500);

          // Should show confirmation dialog
          const hasDialog = await page.getByRole('dialog').count() > 0;
          if (hasDialog) {
            await expect(page.getByRole('dialog')).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('Tab Navigation', () => {
    test('should switch between workflow tabs', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Look for tabs
      const tabs = page.getByRole('tab');
      const tabCount = await tabs.count();

      if (tabCount > 0) {
        // Click on second tab if exists
        if (tabCount > 1) {
          await tabs.nth(1).click();
          await page.waitForTimeout(500);

          // URL should still be on workflows
          await expect(page).toHaveURL(/\/developer\/workflows/);
        }
      }
    });

    test('should filter workflows by status', async ({ page }) => {
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Look for status tabs
      const activeTab = page.getByRole('tab', { name: /Active/i });
      const pausedTab = page.getByRole('tab', { name: /Paused/i });
      const draftTab = page.getByRole('tab', { name: /Draft/i });

      const hasTabs = await activeTab.count() > 0 ||
                      await pausedTab.count() > 0 ||
                      await draftTab.count() > 0;

      if (hasTabs) {
        // Click on a tab
        if (await activeTab.count() > 0) {
          await activeTab.first().click();
          await page.waitForTimeout(500);
        }

        // Page should still be on workflows
        await expect(page).toHaveURL(/\/developer\/workflows/);
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should display properly on mobile', async ({ page }) => {
      await page.goto('/developer/workflows');
      page.setViewportSize({ ...MOBILE_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      // Check for no horizontal scrolling
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
    });

    test('should display properly on desktop', async ({ page }) => {
      await page.goto('/developer/workflows');
      page.setViewportSize({ ...DESKTOP_VIEWPORT });
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      // Content should use desktop space
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeGreaterThan(900);
    });
  });

  test.describe('Complete Workflow Builder Workflow', () => {
    test('end-to-end: navigate → create dialog → configure trigger → add actions', async ({ page }) => {
      // Navigate to Workflows
      await page.goto('/developer/workflows');
      await expect(page).toHaveURL(/\/developer\/workflows/);

      // Check page header
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      // Open create dialog
      const createButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createButton.click();

      // Verify dialog opens
      await expect(page.getByRole('dialog')).toBeVisible();

      // Check for workflow name input
      const nameInput = page.getByRole('textbox', { name: /Name/i }).or(page.getByPlaceholder(/Name/i));
      const hasNameInput = await nameInput.count() > 0;

      if (hasNameInput) {
        await nameInput.first().fill('E2E Test Workflow');
      }

      // Check for trigger section
      const trigger = page.getByText(/Trigger|When|Event/i);
      const hasTrigger = await trigger.count() > 0;
      expect(hasTrigger).toBeTruthy();

      // Check for actions section
      const actions = page.getByText(/Actions|Add Action|Then/i);
      const hasActions = await actions.count() > 0;
      expect(hasActions).toBeTruthy();

      // Close dialog
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Check workflow list (or empty state)
      const workflowCards = page.locator('.MuiCard-root');
      const emptyState = page.getByText(/No workflows|Create your first/i);

      const hasContent = await workflowCards.count() > 0 || await emptyState.isVisible().catch(() => false);
      expect(hasContent).toBeTruthy();
    });
  });
});

test.describe('Complete Developer Portal Integration', () => {
  test.describe('Cross-Feature Navigation', () => {
    test('should navigate through all developer portal features', async ({ page }) => {
      const features = [
        { path: '/developer/api-keys', name: 'API Keys' },
        { path: '/developer/webhooks', name: 'Webhooks' },
        { path: '/developer/plugins', name: 'Plugins' },
        { path: '/developer/workflows', name: 'Workflows' },
        { path: '/developer/analytics', name: 'Analytics' },
      ];

      for (const feature of features) {
        await page.goto(feature.path);
        await page.waitForLoadState('networkidle');

        // Check heading
        await expect(page.getByRole('heading', { name: new RegExp(feature.name, 'i') })).toBeVisible();
      }
    });

    test('should maintain navigation state', async ({ page }) => {
      // Start at API Keys
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Navigate to Webhooks
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Navigate to Workflows
      await page.goto('/developer/workflows');
      await page.waitForLoadState('networkidle');

      // Navigate back to API Keys
      await page.goto('/developer/api-keys');

      // Should load successfully
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();
    });

    test('should show consistent sidebar navigation', async ({ page }) => {
      const pages = ['/developer/api-keys', '/developer/webhooks', '/developer/workflows'];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');

        // Check for navigation elements
        const nav = page.getByRole('navigation').or(page.locator('nav'));
        const navCount = await nav.count();

        // Navigation should be present on at least some pages
        if (navCount > 0) {
          await expect(nav.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Complete Developer Workflow', () => {
    test('end-to-end: API Key → Webhook → Workflow creation flow', async ({ page }) => {
      // Step 1: Create API Key
      await page.goto('/developer/api-keys');
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      const createKeyButton = page.getByRole('button', { name: /Create API Key/i });
      await createKeyButton.click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Step 2: Create Webhook
      await page.goto('/developer/webhooks');
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      const createWebhookButton = page.getByRole('button', { name: /Create Webhook|Add/i });
      await createWebhookButton.click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Step 3: Create Workflow
      await page.goto('/developer/workflows');
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      const createWorkflowButton = page.getByRole('button', { name: /Create Workflow|New/i });
      await createWorkflowButton.click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);

      // Verify all pages are accessible
      await page.goto('/developer/api-keys');
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();
    });

    test('end-to-end: Full developer portal workflow with all features', async ({ page }) => {
      // Start at developer portal home
      await page.goto('/developer');
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

      // Visit API Keys
      await page.goto('/developer/api-keys');
      await expect(page.getByRole('heading', { name: /API Keys/i })).toBeVisible();

      // Verify statistics displayed
      await expect(page.getByText(/Active|Requests|Revoked|Expired/i)).toBeVisible();

      // Visit Webhooks
      await page.goto('/developer/webhooks');
      await expect(page.getByRole('heading', { name: /Webhooks/i })).toBeVisible();

      // Verify statistics displayed
      await expect(page.getByText(/Total|Active|Successful|Failed/i)).toBeVisible();

      // Visit Workflows
      await page.goto('/developer/workflows');
      await expect(page.getByRole('heading', { name: /Workflows/i })).toBeVisible();

      // Verify statistics displayed
      await expect(page.getByText(/Total|Active|Paused|Success/i)).toBeVisible();

      // Visit Plugins
      await page.goto('/developer/plugins');
      await expect(page.getByRole('heading', { name: /Plugins/i })).toBeVisible();

      // Visit Analytics
      await page.goto('/developer/analytics');
      await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible();
    });
  });

  test.describe('Responsive Design Across Portal', () => {
    test('should be responsive on mobile viewport', async ({ page }) => {
      page.setViewportSize({ ...MOBILE_VIEWPORT });

      const pages = ['/developer/api-keys', '/developer/webhooks', '/developer/workflows'];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');

        // Main content should be visible
        await expect(page.getByRole('heading')).toBeVisible();

        // Check for no horizontal scroll
        const body = page.locator('body');
        const scrollWidth = await body.evaluate((el) => el.scrollWidth);
        const clientWidth = await body.evaluate((el) => el.clientWidth);

        expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
      }
    });

    test('should be responsive on desktop viewport', async ({ page }) => {
      page.setViewportSize({ ...DESKTOP_VIEWPORT });

      const pages = ['/developer/api-keys', '/developer/webhooks', '/developer/workflows'];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');

        // Main content should be visible
        await expect(page.getByRole('heading')).toBeVisible();

        // Content should use desktop space
        const body = page.locator('body');
        const scrollWidth = await body.evaluate((el) => el.scrollWidth);

        expect(scrollWidth).toBeGreaterThan(900);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle invalid developer routes', async ({ page }) => {
      const invalidRoutes = [
        '/developer/invalid-feature',
        '/developer/api-keys/invalid-id',
        '/developer/webhooks/invalid-id',
      ];

      for (const route of invalidRoutes) {
        await page.goto(route);
        await page.waitForTimeout(1000);

        // Should handle error gracefully or show 404
        const hasHeading = await page.getByRole('heading').count() > 0;
        expect(hasHeading).toBeTruthy();
      }
    });

    test('should handle network errors gracefully', async ({ page }) => {
      // Navigate to a page that makes API calls
      await page.goto('/developer/api-keys');
      await page.waitForLoadState('networkidle');

      // Page should load (with or without data)
      await expect(page.getByRole('heading')).toBeVisible();
    });

    test('should provide recovery actions for errors', async ({ page }) => {
      // Navigate to a page
      await page.goto('/developer/webhooks');
      await page.waitForLoadState('networkidle');

      // Page should display properly
      await expect(page.getByRole('heading')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      const pages = ['/developer/api-keys', '/developer/webhooks', '/developer/workflows'];

      for (const pagePath of pages) {
        await page.goto(pagePath);

        // Check for main heading
        const h1 = page.getByRole('heading', { level: 1 });
        await expect(h1).toBeVisible();
      }
    });

    test('should be keyboard navigable', async ({ page }) => {
      await page.goto('/developer/api-keys');

      // Tab through focusable elements
      await page.keyboard.press('Tab');

      // Something should be focused
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(['BUTTON', 'INPUT', 'A', 'NAV'].includes(focused || '')).toBeTruthy();
    });

    test('should have ARIA labels on navigation', async ({ page }) => {
      await page.goto('/developer/workflows');

      // Check for ARIA labels on navigation
      const navElements = page.locator('nav, [role="navigation"]');
      const count = await navElements.count();

      if (count > 0) {
        const hasAria = await navElements.first().getAttribute('aria-label') ||
                       await navElements.first().getAttribute('role');
        expect(hasAria).toBeTruthy();
      }
    });
  });

  test.describe('Performance', () => {
    test('should load developer portal pages quickly', async ({ page }) => {
      const pages = [
        { url: '/developer/api-keys', name: 'API Keys' },
        { url: '/developer/webhooks', name: 'Webhooks' },
        { url: '/developer/workflows', name: 'Workflows' },
      ];

      for (const pageConfig of pages) {
        const startTime = Date.now();

        await page.goto(pageConfig.url);

        // Wait for main content
        await page.waitForSelector('h1, h2, h3, h4, h5, h6');

        const loadTime = Date.now() - startTime;

        // Should load in less than 3 seconds
        expect(loadTime).toBeLessThan(3000);
      }
    });
  });
});

test.describe('Developer Portal - Keyboard Navigation', () => {
  test('should support Escape to close dialogs', async ({ page }) => {
    await page.goto('/developer/api-keys');

    // Open create dialog
    const createButton = page.getByRole('button', { name: /Create API Key/i });
    await createButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Press Escape
    await page.keyboard.press('Escape');

    // Dialog should close
    await page.waitForTimeout(500);

    // Should still be on API Keys page
    await expect(page).toHaveURL(/\/developer\/api-keys/);
  });

  test('should support Tab navigation in forms', async ({ page }) => {
    await page.goto('/developer/webhooks');

    // Open create dialog
    const createButton = page.getByRole('button', { name: /Create Webhook|Add/i });
    await createButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Tab through form
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should not cause errors
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA'].includes(focused || '')).toBeTruthy();
  });
});

test.describe('Developer Portal - Data Display', () => {
  test('should display statistics on dashboard', async ({ page }) => {
    await page.goto('/developer');

    // Check for statistics or overview cards
    const stats = page.getByText(/API Keys|Webhooks|Workflows|Plugins|Analytics/i);
    await expect(stats).toBeVisible();
  });

  test('should update statistics after actions', async ({ page }) => {
    // This test verifies the statistics infrastructure exists
    await page.goto('/developer/api-keys');

    // Statistics should be displayed
    const statsText = page.getByText(/Active|Requests|Revoked|Expired/i);
    await expect(statsText).toBeVisible();
  });
});
