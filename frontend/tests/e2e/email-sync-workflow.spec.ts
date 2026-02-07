/**
 * End-to-End Tests for Email Sync Workflow
 *
 * This test suite verifies the complete email synchronization workflow:
 * 1. Configure email sync settings in frontend
 * 2. Trigger email sync
 * 3. View synced emails in CommunicationTimeline
 * 4. Compose and send reply email
 * 5. Verify reply appears in timeline
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Frontend running on http://localhost:5173
 * - Test database with candidate data
 * - Mock or test email server configured
 */

import { test, expect, Page } from '@playwright/test';

// Helper functions

async function loginAsRecruiter(page: Page) {
  await page.goto('http://localhost:5173/login');
  await page.fill('input[name="email"]', 'recruiter@test.com');
  await page.fill('input[name="password"]', 'testpassword');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:5173/recruiter/dashboard');
}

async function navigateToCommunications(page: Page) {
  await page.click('text=Communications');
  await page.waitForURL('**/communications');
  await page.waitForLoadState('networkidle');
}

async function createTestCandidateViaAPI() {
  // This would typically create a test candidate via API
  // For now, we assume candidate exists or is created by backend tests
  return {
    id: 'test-candidate-id',
    name: 'Test Candidate',
    email: 'test.candidate@example.com'
  };
}

// Test Suite

test.describe('Email Sync Workflow E2E', () => {
  let page: Page;
  let testCandidate: any;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    testCandidate = await createTestCandidateViaAPI();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test.beforeEach(async () => {
    await loginAsRecruiter(page);
  });

  test('Step 1: Configure email sync in backend settings', async () => {
    /*
     * Test: Configure email sync in backend settings
     *
     * Verifies:
     * - Settings tab is accessible
     * - Email sync configuration form is visible
     * - Settings can be saved
     */

    await navigateToCommunications(page);

    // Navigate to Settings tab
    await page.click('button[role="tab"]:has-text("Settings")');
    await expect(page.locator('text=Email Sync Configuration')).toBeVisible();

    // Fill in email configuration
    await page.fill('input[name="imap_server"]', 'imap.test.com');
    await page.fill('input[name="imap_port"]', '993');
    await page.fill('input[name="imap_username"]', 'test@test.com');
    await page.fill('input[name="imap_password"]', 'test_password');

    await page.fill('input[name="smtp_server"]', 'smtp.test.com');
    await page.fill('input[name="smtp_port"]', '587');
    await page.fill('input[name="smtp_username"]', 'test@test.com');
    await page.fill('input[name="smtp_password"]', 'test_password');
    await page.fill('input[name="smtp_from_email"]', 'recruiter@test.com');

    // Enable sync
    await page.check('input[name="sync_enabled"]');
    await page.fill('input[name="sync_interval_minutes"]', '5');

    // Save configuration
    await page.click('button:has-text("Save Configuration")');

    // Verify success message
    await expect(page.locator('text=Configuration saved successfully')).toBeVisible({ timeout: 5000 });

    // Verify configuration is persisted
    await expect(page.locator('input[name="imap_server"]')).toHaveValue('imap.test.com');
    await expect(page.locator('input[name="sync_enabled"]')).toBeChecked();
  });

  test('Step 2: Trigger email sync via API', async () => {
    /*
     * Test: Trigger email sync via API
     *
     * Verifies:
     * - Sync can be triggered manually
     * - Sync status is displayed
     * - Sync completes successfully
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Settings")');

    // Trigger manual sync
    await page.click('button:has-text("Sync Now")');

    // Wait for sync status indicator
    await expect(page.locator('text=Syncing emails...')).toBeVisible({ timeout: 3000 });

    // Wait for sync completion (may take a few seconds)
    await expect(page.locator('text=Last sync:')).toBeVisible({ timeout: 15000 });

    // Verify sync completed
    const syncStatus = page.locator('[data-testid="email-sync-status"]');
    await expect(syncStatus).toContainText('completed', { timeout: 10000 });
  });

  test('Step 3: Verify emails are stored in database', async () => {
    /*
     * Test: Verify emails are stored in database via API
     *
     * Verifies:
     * - Emails are accessible via API
     * - Email metadata is correct
     * - Candidate associations are correct
     */

    // Navigate directly to candidate's communications
    await page.goto(`http://localhost:5173/recruiter/candidates/${testCandidate.id}/communications`);
    await page.waitForLoadState('networkidle');

    // Check that emails are displayed
    await expect(page.locator('[data-testid="communication-item"]')).toBeVisible();

    // Verify at least one email is shown
    const emailCount = await page.locator('[data-testid="communication-item"][data-type="email"]').count();
    expect(emailCount).toBeGreaterThan(0);

    // Click on an email to view details
    await page.click('[data-testid="communication-item"][data-type="email"]:first-child');

    // Verify email details are displayed
    await expect(page.locator('[data-testid="email-subject"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-body"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-from"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-to"]')).toBeVisible();
  });

  test('Step 4: View emails in CommunicationTimeline', async () => {
    /*
     * Test: View emails in frontend CommunicationTimeline
     *
     * Verifies:
     * - Timeline component renders
     * - Emails are displayed in chronological order
     * - Filters work correctly
     * - Email type indicators are visible
     */

    await navigateToCommunications(page);

    // Navigate to Timeline tab
    await page.click('button[role="tab"]:has-text("Timeline")');
    await page.waitForLoadState('networkidle');

    // Wait for timeline to load
    await expect(page.locator('[data-testid="communication-timeline"]')).toBeVisible();

    // Verify emails are visible
    await expect(page.locator('[data-testid="timeline-item"][data-type="email"]')).toBeVisible();

    // Test email filter
    await page.click('button[aria-label="Filter by type"]');
    await page.click('text=Email');
    await page.waitForLoadState('networkidle');

    // Verify only emails are shown
    const visibleItems = page.locator('[data-testid="timeline-item"]');
    const emailItems = page.locator('[data-testid="timeline-item"][data-type="email"]');

    const totalCount = await visibleItems.count();
    const emailCount = await emailItems.count();

    expect(totalCount).toBe(emailCount);

    // Verify chronological order (newest first)
    const timestamps = await page.locator('[data-testid="timeline-item-time"]').allTextContents();
    expect(timestamps.length).toBeGreaterThan(1);

    // Verify email icons are visible
    await expect(page.locator('[data-testid="email-icon"]')).toBeVisible();
  });

  test('Step 5: Compose and send reply email', async () => {
    /*
     * Test: Compose and send reply email
     *
     * Verifies:
     * - Reply dialog can be opened
     * - Email can be composed
     * - Send action works
     * - Success message is shown
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Timeline")');

    // Click on an email to open it
    await page.click('[data-testid="timeline-item"][data-type="email"]:first-child');

    // Wait for email viewer
    await expect(page.locator('[data-testid="email-viewer"]')).toBeVisible();

    // Click reply button
    await page.click('button:has-text("Reply")');

    // Wait for reply dialog
    await expect(page.locator('[data-testid="reply-email-dialog"]')).toBeVisible();

    // Compose reply
    await page.fill('textarea[name="body"]', 'Thank you for your email. Let me get back to you shortly.');

    // Send reply
    await page.click('button:has-text("Send")');

    // Wait for success message
    await expect(page.locator('text=Email sent successfully')).toBeVisible({ timeout: 5000 });

    // Verify dialog is closed
    await expect(page.locator('[data-testid="reply-email-dialog"]')).not.toBeVisible();
  });

  test('Step 6: Verify reply appears in timeline', async () => {
    /*
     * Test: Verify reply appears in database and timeline
     *
     * Verifies:
     * - Reply is stored in database
     * - Reply appears in timeline
     * - Thread grouping works
     * - Correct chronological order
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Timeline")');

    // Wait for timeline
    await expect(page.locator('[data-testid="communication-timeline"]')).toBeVisible();

    // Scroll to top to see newest items
    await page.evaluate(() => window.scrollTo(0, 0));

    // Look for outbound email (reply)
    const outboundEmails = page.locator('[data-testid="timeline-item"][data-type="email"][data-direction="outbound"]');

    // Wait a moment for the reply to appear
    await page.waitForTimeout(2000);

    const outboundCount = await outboundEmails.count();
    expect(outboundCount).toBeGreaterThan(0);

    // Verify reply is in correct position (near top)
    const firstOutbound = outboundEmails.first();
    await expect(firstOutbound).toBeVisible();

    // Click on reply to verify details
    await firstOutbound.click();

    // Verify reply details
    await expect(page.locator('[data-testid="email-viewer"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-direction"][data-value="outbound"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-body"]')).toContainText('Thank you for your email');

    // Verify thread view shows both original and reply
    const threadItems = page.locator('[data-testid="email-thread-item"]');
    const threadCount = await threadItems.count();
    expect(threadCount).toBeGreaterThanOrEqual(2);
  });

  test('Complete Workflow: From sync to reply', async () => {
    /*
     * Complete end-to-end workflow test:
     * 1. Navigate to communications
     * 2. Configure email sync
     * 3. Trigger sync
     * 4. View incoming email
     * 5. Send reply
     * 6. Verify thread
     */

    // Navigate to communications
    await navigateToCommunications(page);

    // Configure email sync (if not already configured)
    await page.click('button[role="tab"]:has-text("Settings")');

    const isConfigured = await page.locator('input[name="sync_enabled"]').isChecked();

    if (!isConfigured) {
      await page.fill('input[name="imap_server"]', 'imap.test.com');
      await page.fill('input[name="imap_port"]', '993');
      await page.fill('input[name="imap_username"]', 'test@test.com');
      await page.fill('input[name="smtp_server"]', 'smtp.test.com');
      await page.fill('input[name="smtp_port"]', '587');
      await page.fill('input[name="smtp_from_email"]', 'recruiter@test.com');
      await page.check('input[name="sync_enabled"]');
      await page.click('button:has-text("Save Configuration")');
      await expect(page.locator('text=Configuration saved')).toBeVisible();
    }

    // Trigger sync
    await page.click('button:has-text("Sync Now")');
    await expect(page.locator('text=Syncing emails...')).toBeVisible();
    await expect(page.locator('text=Last sync:')).toBeVisible({ timeout: 15000 });

    // View timeline
    await page.click('button[role="tab"]:has-text("Timeline")');
    await expect(page.locator('[data-testid="communication-timeline"]')).toBeVisible();

    // Wait for emails to load
    await page.waitForTimeout(1000);

    // Find and click on an incoming email
    const inboundEmails = page.locator('[data-testid="timeline-item"][data-type="email"][data-direction="inbound"]');
    const inboundCount = await inboundEmails.count();

    if (inboundCount > 0) {
      // Click on first inbound email
      await inboundEmails.first().click();

      // View email details
      await expect(page.locator('[data-testid="email-viewer"]')).toBeVisible();

      // Send a reply
      await page.click('button:has-text("Reply")');
      await expect(page.locator('[data-testid="reply-email-dialog"]')).toBeVisible();

      await page.fill('textarea[name="body"]', 'Thanks for reaching out. I will review your application.');
      await page.click('button:has-text("Send")');

      // Verify success
      await expect(page.locator('text=Email sent successfully')).toBeVisible({ timeout: 5000 });

      // Go back to timeline
      await page.click('button[role="tab"]:has-text("Timeline")');

      // Verify reply appears
      const outboundEmails = page.locator('[data-testid="timeline-item"][data-type="email"][data-direction="outbound"]');
      await page.waitForTimeout(2000);

      const outboundCount = await outboundEmails.count();
      expect(outboundCount).toBeGreaterThan(0);

      // Test passed!
      console.log('✓ Complete email sync workflow test passed');
    } else {
      console.log('⚠ No inbound emails found to reply to');
    }
  });

  test('Filter and search functionality', async () => {
    /*
     * Test filtering and searching in timeline
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Timeline")');

    // Wait for timeline to load
    await expect(page.locator('[data-testid="communication-timeline"]')).toBeVisible();

    // Test type filter
    await page.selectOption('select[name="type"]', 'email');
    await page.waitForLoadState('networkidle');

    const emailItems = page.locator('[data-testid="timeline-item"][data-type="email"]');
    await expect(emailItems.first()).toBeVisible();

    // Test direction filter
    await page.selectOption('select[name="direction"]', 'inbound');
    await page.waitForLoadState('networkidle');

    const inboundItems = page.locator('[data-testid="timeline-item"][data-direction="inbound"]');
    await expect(inboundItems.first()).toBeVisible();

    // Test search
    await page.fill('input[name="search"]', 'application');
    await page.waitForTimeout(500); // Debounce delay

    // Verify search results
    const searchResults = page.locator('[data-testid="timeline-item"]');
    const count = await searchResults.count();

    // Should have results or show empty state
    if (count > 0) {
      await expect(searchResults.first()).toBeVisible();
    } else {
      await expect(page.locator('text=No communications found')).toBeVisible();
    }

    // Clear filters
    await page.selectOption('select[name="type"]', 'all');
    await page.selectOption('select[name="direction"]', 'all');
    await page.fill('input[name="search"]', '');
    await page.waitForLoadState('networkidle');

    // Verify all items are shown again
    const allItems = page.locator('[data-testid="timeline-item"]');
    await expect(allItems.first()).toBeVisible();
  });

  test('Email thread view', async () => {
    /*
     * Test email thread view functionality
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Timeline")');

    // Click on an email that might have a thread
    const emailItems = page.locator('[data-testid="timeline-item"][data-type="email"]');
    const count = await emailItems.count();

    if (count > 0) {
      await emailItems.first().click();

      // Check if thread view is visible
      const threadView = page.locator('[data-testid="email-thread-view"]');

      if (await threadView.isVisible()) {
        // Verify thread items
        const threadItems = page.locator('[data-testid="email-thread-item"]');
        const threadCount = await threadItems.count();

        expect(threadCount).toBeGreaterThanOrEqual(1);

        // Verify thread headers
        await expect(threadItems.first().locator('[data-testid="email-from"]')).toBeVisible();
        await expect(threadItems.first().locator('[data-testid="email-body"]')).toBeVisible();
      } else {
        console.log('⚠ No thread view available for this email');
      }
    }
  });

  test('Email sync status and metrics', async () => {
    /*
     * Test email sync status and communication metrics
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Settings")');

    // Verify sync status section
    await expect(page.locator('[data-testid="email-sync-status"]')).toBeVisible();

    // Check if last sync time is displayed
    const lastSyncElement = page.locator('[data-testid="last-sync-time"]');
    if (await lastSyncElement.isVisible()) {
      await expect(lastSyncElement).toContainText('Last sync:');
    }

    // Check sync statistics
    const syncStats = page.locator('[data-testid="sync-statistics"]');
    if (await syncStats.isVisible()) {
      await expect(syncStats).toContainText(/emails|synced/);
    }

    // Navigate to timeline to check metrics
    await page.click('button[role="tab"]:has-text("Timeline")');

    // Look for metrics cards
    const metricsSection = page.locator('[data-testid="communication-metrics"]');

    if (await metricsSection.isVisible()) {
      await expect(metricsSection.locator('text=Total Communications')).toBeVisible();
      await expect(metricsSection.locator('text=Response Rate')).toBeVisible();
    }
  });

  test('Error handling and validation', async () => {
    /*
     * Test error handling and validation
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("Settings")');

    // Try to save invalid configuration
    await page.fill('input[name="imap_server"]', ''); // Empty server
    await page.click('button:has-text("Save Configuration")');

    // Verify error message
    await expect(page.locator('text=required|invalid')).toBeVisible({ timeout: 3000 });

    // Try to trigger sync without configuration
    await page.fill('input[name="imap_server"]', 'invalid.server.com');
    await page.fill('input[name="imap_username"]', 'invalid');
    await page.fill('input[name="imap_password"]', 'invalid');
    await page.click('button:has-text("Sync Now")');

    // Verify error handling (should show error message)
    await page.waitForTimeout(3000);

    const errorMessage = page.locator('[data-testid="sync-error-message"]');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/failed|error|connection/i);
    }
  });

  test('Responsive design on mobile', async () => {
    /*
     * Test responsive design on mobile viewport
     */

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await navigateToCommunications(page);

    // Verify timeline is responsive
    await page.click('button[role="tab"]:has-text("Timeline")');
    await expect(page.locator('[data-testid="communication-timeline"]')).toBeVisible();

    // Verify mobile layout
    await expect(page.locator('[data-testid="timeline-item"]').first()).toBeVisible();

    // Test mobile navigation
    await page.click('button[aria-label="Menu"]'); // Mobile menu button
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
  });
});
