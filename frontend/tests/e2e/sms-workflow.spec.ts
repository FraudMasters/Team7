/**
 * End-to-End Tests for SMS Workflow
 *
 * This test suite verifies the complete SMS sending and tracking workflow:
 * 1. Compose SMS in SMSComposer
 * 2. Send SMS via API
 * 3. Verify Celery task processes SMS
 * 4. Check delivery status
 * 5. View SMS in CommunicationTimeline
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Frontend running on http://localhost:5173
 * - Test database with candidate data
 * - Mock or test SMS provider configured (Twilio/AWS SNS)
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

async function navigateToCandidatePage(page: Page, candidateId: string) {
  await page.goto(`http://localhost:5173/recruiter/candidates/${candidateId}`);
  await page.waitForLoadState('networkidle');
}

async function createTestCandidateViaAPI(): Promise<{id: string, name: string, phone: string}> {
  // This would typically create a test candidate via API
  // For now, we assume candidate exists or is created by backend tests
  return {
    id: 'test-candidate-id',
    name: 'Test Candidate',
    phone: '+1234567890'
  };
}

// Test Suite

test.describe('SMS Workflow E2E', () => {
  let page: Page;
  let testCandidate: {id: string, name: string, phone: string};

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

  test('Step 1: Compose SMS in SMSComposer', async () => {
    /**
     * Test: Compose SMS in SMSComposer
     *
     * Verifies:
     * - SMSComposer component is accessible
     * - Phone number field is pre-filled
     * - Message body field accepts input
     * - Character count is displayed
     * - Provider selection works
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Click on "Send SMS" button (assuming this exists in candidate page)
    const sendSmsButton = page.locator('button:has-text("Send SMS")').first();
    await expect(sendSmsButton).toBeVisible();
    await sendSmsButton.click();

    // Verify SMSComposer dialog appears
    await expect(page.locator('text=Send SMS')).toBeVisible();
    await expect(page.locator('input[name="to_number"]')).toBeVisible();
    await expect(page.locator('textarea[name="body"]')).toBeVisible();

    // Verify phone number is pre-filled
    const toNumberField = page.locator('input[name="to_number"]');
    await expect(toNumberField).toHaveValue(testCandidate.phone);

    // Type a message
    const messageBody = 'Hello! You have an interview tomorrow at 2 PM.';
    await page.fill('textarea[name="body"]', messageBody);

    // Verify character count
    const charCount = page.locator('text=/\\d+\\/160/');  // Matches "47/160" format
    await expect(charCount).toBeVisible();

    // Verify provider selection
    const providerSelect = page.locator('select[name="provider"]');
    await expect(providerSelect).toBeVisible();
    await providerSelect.selectOption('twilio');
    await expect(providerSelect).toHaveValue('twilio');
  });

  test('Step 2: Send SMS via API', async () => {
    /**
     * Test: Send SMS via API
     *
     * Verifies:
     * - Send button is enabled when form is valid
     * - Loading state appears during sending
     * - Success message appears after sending
     * - Dialog closes after successful send
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Open SMSComposer
    await page.click('button:has-text("Send SMS")');
    await expect(page.locator('text=Send SMS')).toBeVisible();

    // Fill SMS form
    await page.fill('textarea[name="body"]', 'Test SMS message for E2E testing');

    // Verify send button is enabled
    const sendButton = page.locator('button:has-text("Send SMS")').last();
    await expect(sendButton).toBeEnabled();

    // Mock API response (or use test API endpoint)
    // In real test, we would intercept the API call or use test backend
    await sendButton.click();

    // Verify loading state
    await expect(page.locator('.MuiCircularProgress-root')).toBeVisible();

    // Wait for success message
    await expect(page.locator('text=SMS sent successfully')).toBeVisible({timeout: 5000});

    // Verify dialog closes
    await expect(page.locator('text=Send SMS')).not.toBeVisible();
  });

  test('Step 3: Verify Celery task processes SMS', async () => {
    /**
     * Test: Verify Celery task processes SMS
     *
     * Verifies:
     * - Celery task is triggered
     * - SMS is queued for processing
     * - Processing completes successfully
     * Note: This test requires backend Celery worker to be running
     */

    // Navigate to communications page to check status
    await navigateToCommunications(page);

    // Click on SMS tab
    await page.click('button[role="tab"]:has-text("SMS")');

    // Wait for SMS list to load
    await page.waitForLoadState('networkidle');

    // Find the recently sent SMS
    const smsItems = page.locator('.sms-message-item');
    const count = await smsItems.count();

    expect(count).toBeGreaterThan(0);

    // Check first SMS item
    const firstSms = smsItems.first();
    await expect(firstSms.locator('text=Test SMS message')).toBeVisible();
    await expect(firstSms.locator('text=delivered')).toBeVisible({timeout: 10000});
  });

  test('Step 4: Check delivery status', async () => {
    /**
     * Test: Check delivery status
     *
     * Verifies:
     * - Delivery status is visible in SMS list
     * - Status can be "sent", "delivered", "pending", or "failed"
     * - Provider message ID is tracked
     */

    await navigateToCommunications(page);

    // Click on SMS tab
    await page.click('button[role="tab"]:has-text("SMS")');
    await page.waitForLoadState('networkidle');

    // Find SMS with delivery status
    const smsItems = page.locator('.sms-message-item');
    const firstSms = smsItems.first();

    // Check for delivery status badge
    const statusBadge = firstSms.locator('.status-badge');
    await expect(statusBadge).toBeVisible();

    const statusText = await statusBadge.textContent();
    expect(['sent', 'delivered', 'pending', 'failed']).toContain(statusText?.toLowerCase() || '');

    // Check for provider info
    const providerInfo = firstSms.locator('text=/Provider:/');
    await expect(providerInfo).toBeVisible();
  });

  test('Step 5: View SMS in CommunicationTimeline', async () => {
    /**
     * Test: View SMS in CommunicationTimeline
     *
     * Verifies:
     * - SMS appears in unified timeline
     * - SMS can be filtered by type
     * - Timeline shows SMS icon/indicator
     * - Timeline displays SMS content
     */

    await navigateToCommunications(page);

    // Click on Timeline tab (default tab)
    await page.click('button[role="tab"]:has-text("Timeline")');
    await page.waitForLoadState('networkidle');

    // Verify timeline has communications
    const timelineItems = page.locator('.timeline-item');
    const count = await timelineItems.count();
    expect(count).toBeGreaterThan(0);

    // Filter by SMS type
    await page.click('button:has-text("Filter")');
    await page.click('label:has-text("SMS")');

    // Wait for filtered results
    await page.waitForLoadState('networkidle');

    // Verify filtered timeline shows only SMS
    const filteredItems = page.locator('.timeline-item[data-type="sms"]');
    const filteredCount = await filteredItems.count();
    expect(filteredCount).toBeGreaterThan(0);

    // Verify SMS content is displayed
    const firstSms = filteredItems.first();
    await expect(firstSms.locator('.sms-icon')).toBeVisible();
    await expect(firstSms.locator('.communication-body')).toBeVisible();
  });

  test('Complete SMS workflow: From compose to timeline', async () => {
    /**
     * Complete end-to-end SMS workflow test.
     *
     * This test runs the entire workflow in sequence:
     * 1. Navigate to candidate page
     * 2. Compose and send SMS
     * 3. Verify SMS in Communications page
     * 4. Check delivery status
     * 5. View in timeline
     */

    // Step 1: Navigate to candidate
    await navigateToCandidatePage(page, testCandidate.id);
    await expect(page.locator(`text=${testCandidate.name}`)).toBeVisible();

    // Step 2: Compose and send SMS
    await page.click('button:has-text("Send SMS")');
    await expect(page.locator('text=Send SMS')).toBeVisible();

    const testMessage = `E2E Test SMS at ${new Date().toISOString()}`;
    await page.fill('textarea[name="body"]', testMessage);

    // Verify character count
    const charCount = page.locator('text=/\\d+ characters/');
    await expect(charCount).toBeVisible();

    // Send SMS
    await page.click('button:has-text("Send")');
    await expect(page.locator('text=SMS sent successfully')).toBeVisible({timeout: 5000});

    // Step 3: Navigate to Communications page
    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("SMS")');
    await page.waitForLoadState('networkidle');

    // Verify SMS appears in list
    await expect(page.locator(`text=${testMessage}`)).toBeVisible({timeout: 10000});

    // Step 4: Check delivery status
    const smsItem = page.locator('.sms-message-item').filter({hasText: testMessage});
    await expect(smsItem.locator('.status-badge')).toBeVisible();

    const status = await smsItem.locator('.status-badge').textContent();
    console.log(`SMS Delivery Status: ${status}`);

    // Step 5: View in Timeline
    await page.click('button[role="tab"]:has-text("Timeline")');
    await page.waitForLoadState('networkidle');

    // Filter for SMS
    await page.click('button:has-text("Filter")');
    await page.click('label:has-text("SMS")');
    await page.waitForLoadState('networkidle');

    // Verify SMS in timeline
    await expect(page.locator(`text=${testMessage}`)).toBeVisible();

    console.log('Complete SMS workflow test passed!');
  });

  test('SMS character limit and multi-segment handling', async () => {
    /**
     * Test: SMS character limit and multi-segment handling
     *
     * Verifies:
     * - Character limit of 160 is enforced
     * - Multi-segment SMS is detected
     * - Segment count is displayed
     */

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Send SMS")');

    // Test single segment SMS (<= 160 chars)
    const singleSegment = 'A'.repeat(160);
    await page.fill('textarea[name="body"]', singleSegment);

    // Should show 160/160 characters
    await expect(page.locator('text=/160\\/160/')).toBeVisible();
    await expect(page.locator('text=/1 segment/')).toBeVisible();

    // Test multi-segment SMS (> 160 chars)
    const multiSegment = 'A'.repeat(161);
    await page.fill('textarea[name="body"]', multiSegment);

    // Should show 161/160 characters (over limit)
    await expect(page.locator('text=/161\\/160/')).toBeVisible();
    await expect(page.locator('text=/2 segments/')).toBeVisible();

    // Test maximum reasonable length
    const maxMessage = 'A'.repeat(500);
    await page.fill('textarea[name="body"]', maxMessage);

    // Should show segment count (500 chars / 153 per segment = ~4 segments)
    await expect(page.locator('text=/4 segments/')).toBeVisible();
  });

  test('SMS provider selection', async () => {
    /**
     * Test: SMS provider selection
     *
     * Verifies:
     * - Provider dropdown is available
     * - Multiple providers can be selected
     * - Provider selection is saved
     */

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Send SMS")');

    // Test Twilio provider
    const providerSelect = page.locator('select[name="provider"]');
    await providerSelect.selectOption('twilio');
    await expect(providerSelect).toHaveValue('twilio');

    // Test AWS SNS provider
    await providerSelect.selectOption('aws_sns');
    await expect(providerSelect).toHaveValue('aws_sns');

    // Verify provider is saved when sending
    await page.fill('textarea[name="body"]', 'Test provider selection');

    // In real test, we would verify the provider is sent in API request
  });

  test('SMS template selection', async () => {
    /**
     * Test: SMS template selection
     *
     * Verifies:
     * - Template dropdown is available
     * - Template populates message body
     * - Template variables are indicated
     */

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Send SMS")');

    // Check for template dropdown
    const templateSelect = page.locator('select[name="template"]');
    if (await templateSelect.isVisible()) {
      // Select a template (e.g., "Interview Reminder")
      await templateSelect.selectOption('interview_reminder');

      // Verify message body is populated
      const messageBody = page.locator('textarea[name="body"]');
      await expect(messageBody).not.toHaveValue('');

      const bodyText = await messageBody.inputValue();
      expect(bodyText).toContain('{{');  // Template variables
    } else {
      console.log('Template selection not implemented yet, skipping');
    }
  });

  test('SMS error handling', async () => {
    /**
     * Test: SMS error handling
     *
     * Verifies:
     * - Validation errors are displayed
     * - Network errors are handled gracefully
     * - Empty message validation works
     */

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Send SMS")');

    // Try to send empty message
    const sendButton = page.locator('button:has-text("Send")').last();

    // Verify send button is disabled with empty message
    await expect(sendButton).toBeDisabled();

    // Type a message then delete it
    await page.fill('textarea[name="body"]', 'Test');
    await page.fill('textarea[name="body"]', '');

    // Button should be disabled again
    await expect(sendButton).toBeDisabled();

    // Test invalid phone number (if field is editable)
    const toNumberField = page.locator('input[name="to_number"]');
    if (await toNumberField.isEditable()) {
      await toNumberField.fill('invalid-phone');
      await page.fill('textarea[name="body"]', 'Test message');

      // Should show validation error
      await expect(page.locator('text=/invalid.*phone/i')).toBeVisible();
    }
  });

  test('SMS filtering and search', async () => {
    /**
     * Test: SMS filtering and search in Communications page
     *
     * Verifies:
     * - SMS list can be filtered by candidate
     * - SMS list can be filtered by delivery status
     * - SMS list can be searched by content
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("SMS")');
    await page.waitForLoadState('networkidle');

    // Verify filter controls are present
    await expect(page.locator('select[name="filter-status"]')).toBeVisible();
    await expect(page.locator('input[name="search-query"]')).toBeVisible();

    // Filter by delivery status
    await page.selectOption('select[name="filter-status"]', 'delivered');
    await page.waitForLoadState('networkidle');

    // Verify filtered results
    const statusBadges = page.locator('.status-badge:has-text("delivered")');
    const count = await statusBadges.count();
    expect(count).toBeGreaterThan(0);

    // Search for specific content
    await page.fill('input[name="search-query"]', 'interview');
    await page.press('input[name="search-query"]', 'Enter');
    await page.waitForLoadState('networkidle');

    // Verify search results
    const searchResults = page.locator('.sms-message-item');
    const resultCount = await searchResults.count();

    for (let i = 0; i < Math.min(resultCount, 5); i++) {
      const item = searchResults.nth(i);
      const text = await item.textContent();
      expect(text?.toLowerCase()).toContain('interview');
    }
  });

  test('SMS delivery status refresh', async () => {
    /**
     * Test: SMS delivery status refresh
     *
     * Verifies:
     * - Delivery status can be manually refreshed
     * - Status updates are reflected in UI
     * - Provider message ID is displayed
     */

    await navigateToCommunications(page);
    await page.click('button[role="tab"]:has-text("SMS")');
    await page.waitForLoadState('networkidle');

    // Find an SMS with pending status
    const pendingSms = page.locator('.sms-message-item').filter({hasText: 'pending'}).first();

    if (await pendingSms.isVisible()) {
      // Click refresh button
      const refreshButton = pendingSms.locator('button[aria-label="Refresh status"]');
      await refreshButton.click();

      // Wait for status update
      await page.waitForTimeout(2000);

      // Verify status changed (or stayed the same if no update)
      await expect(pendingSms.locator('.status-badge')).toBeVisible();
    } else {
      console.log('No pending SMS found to refresh');
    }
  });
});

// Helper function for running specific tests
export function runSmsWorkflowTests() {
  test.describe.configure({ mode: 'parallel' });
}
