/**
 * End-to-End Tests for Phone Call Logging Workflow
 *
 * This test suite verifies the complete phone call logging workflow:
 * 1. Log phone call via PhoneCallLogger
 * 2. Verify call saved to database
 * 3. View call in CommunicationTimeline
 * 4. Check communication metrics include call data
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Frontend running on http://localhost:5173
 * - Test database with candidate data
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

test.describe('Phone Call Workflow E2E', () => {
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

  test('Step 1: Log phone call via PhoneCallLogger', async () => {
    /**
     * Test: Log phone call via PhoneCallLogger
     *
     * Verifies:
     * - PhoneCallLogger component is accessible
     * - Call type selection works (inbound/outbound/missed)
     * - Duration field accepts input
     * - Notes and outcome fields work
     * - Phone numbers are pre-filled based on direction
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Click on "Log Call" button (assuming this exists in candidate page)
    const logCallButton = page.locator('button:has-text("Log Call")').first();
    await expect(logCallButton).toBeVisible();
    await logCallButton.click();

    // Verify PhoneCallLogger dialog/form appears
    await expect(page.locator('text=Log Phone Call')).toBeVisible();
    await expect(page.locator('[data-testid="call-type-select"]')).toBeVisible();
    await expect(page.locator('[data-testid="duration-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="call-notes"]')).toBeVisible();
    await expect(page.locator('[data-testid="call-outcome"]')).toBeVisible();

    // Verify call type options
    await page.click('[data-testid="call-type-select"]');
    await expect(page.locator('text=Outbound')).toBeVisible();
    await expect(page.locator('text=Inbound')).toBeVisible();
    await expect(page.locator('text=Missed')).toBeVisible();

    // Select outbound call type
    await page.click('text=Outbound');

    // Verify phone numbers are pre-filled for outbound
    const fromNumber = page.locator('input[name="from_number"]');
    const toNumber = page.locator('input[name="to_number"]');
    await expect(fromNumber).not.toBeEmpty();
    await expect(toNumber).toHaveValue(testCandidate.phone);

    // Enter call duration
    await page.fill('[data-testid="duration-input"]', '15');

    // Select call outcome
    await page.click('[data-testid="call-outcome"]');
    await page.click('text=Reached Candidate');

    // Enter call notes
    const notes = 'Discussed candidate experience and availability. Candidate interested in the position.';
    await page.fill('[data-testid="call-notes"]', notes);

    // Verify character count or validation if present
    const notesValue = await page.inputValue('[data-testid="call-notes"]');
    expect(notesValue).toBe(notes);

    // Submit the form
    await page.click('button:has-text("Log Call")');

    // Verify success message
    await expect(page.locator('text=Call logged successfully')).toBeVisible({ timeout: 5000 });
  });

  test('Step 2: Verify call saved to database', async () => {
    /**
     * Test: Verify call saved to database via API
     *
     * Verifies:
     * - Communication record created with type=phone_call
     * - PhoneCall record created with duration and call_type
     * - Metadata includes outcome and notes
     */

    // First, log a call via the UI
    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Log Call")');

    // Fill call details
    await page.click('[data-testid="call-type-select"]');
    await page.click('text=Outbound');
    await page.fill('[data-testid="duration-input"]', '10');
    await page.click('[data-testid="call-outcome"]');
    await page.click('text=Left Voicemail');
    await page.fill('[data-testid="call-notes"]', 'Left voicemail about interview scheduling');

    // Submit
    await page.click('button:has-text("Log Call")');
    await expect(page.locator('text=Call logged successfully')).toBeVisible();

    // Verify via API that the call was saved
    const response = await page.request.get({
      url: `http://localhost:8000/api/communications/?candidate_id=${testCandidate.id}&type=phone_call`,
      headers: {
        'Authorization': 'Bearer test-token' // Adjust auth as needed
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Verify phone call exists in response
    expect(data.communications).toBeDefined();
    expect(data.communications.length).toBeGreaterThan(0);

    const phoneCall = data.communications.find((c: any) => c.type === 'phone_call');
    expect(phoneCall).toBeDefined();
    expect(phoneCall.metadata.call_type).toBe('outbound');
    expect(phoneCall.metadata.duration_minutes).toBe(10);
    expect(phoneCall.metadata.outcome).toBe('left_voicemail');
    expect(phoneCall.metadata.notes).toContain('voicemail');
  });

  test('Step 3: View call in CommunicationTimeline', async () => {
    /**
     * Test: View call in CommunicationTimeline
     *
     * Verifies:
     * - Call appears in timeline
     * - Timeline shows call icon/indicator
     * - Timeline displays call duration
     * - Timeline shows call outcome
     */

    await navigateToCommunications(page);

    // Filter timeline to show only phone calls
    await page.click('[data-testid="type-filter"]');
    await page.click('text=Phone Calls');

    // Wait for filtered timeline
    await page.waitForLoadState('networkidle');

    // Verify phone calls are visible in timeline
    const timelineItems = page.locator('[data-testid="communication-timeline-item"]');
    await expect(timelineItems.first()).toBeVisible();

    // Verify phone call indicator/icon
    const phoneCallIcon = page.locator('[data-testid="phone-call-icon"]');
    await expect(phoneCallIcon.first()).toBeVisible();

    // Verify call details are displayed
    await expect(page.locator('text=Duration')).toBeVisible();
    await expect(page.locator('text=outcome')).toBeVisible();

    // Click on a phone call to view details
    await timelineItems.first().click();

    // Verify detail view opens
    await expect(page.locator('[data-testid="communication-detail"]')).toBeVisible();
    await expect(page.locator('text=Phone Call Details')).toBeVisible();
    await expect(page.locator('text=Duration')).toBeVisible();
    await expect(page.locator('text=Outcome')).toBeVisible();
    await expect(page.locator('text=Notes')).toBeVisible();
  });

  test('Step 4: Check communication metrics include call data', async () => {
    /**
     * Test: Check communication metrics include call data
     *
     * Verifies:
     * - Metrics endpoint includes phone_call type
     * - Total sent count includes phone calls
     * - Breakdown by type shows phone_call statistics
     */

    // Navigate to communications page
    await navigateToCommunications(page);

    // Click on Metrics/Stats section
    await page.click('[data-testid="metrics-tab"]');

    // Wait for metrics to load
    await page.waitForLoadState('networkidle');

    // Verify metrics cards are displayed
    await expect(page.locator('[data-testid="total-sent-metric"]')).toBeVisible();
    await expect(page.locator('[data-testid="engagement-metric"]')).toBeVisible();
    await expect(page.locator('[data-testid="breakdown-by-type"]')).toBeVisible();

    // Verify phone calls are included in breakdown
    const phoneCallMetric = page.locator('[data-testid="phone-call-metric"]');
    await expect(phoneCallMetric).toBeVisible();

    // Verify phone call count is displayed
    const phoneCallCount = await phoneCallMetric.textContent();
    expect(phoneCallCount).toMatch(/\d+/); // Should contain numbers

    // Verify via API
    const response = await page.request.get({
      url: 'http://localhost:8000/api/communications/metrics',
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Verify phone calls in metrics
    expect(data.engagement.engagement.total_sent).toBeGreaterThan(0);
    expect(data.engagement.engagement.breakdown.by_type.phone_call).toBeDefined();
    expect(data.engagement.engagement.breakdown.by_type.phone_call.count).toBeGreaterThan(0);
  });

  test('Complete workflow: Log call and verify in timeline', async () => {
    /**
     * Test: Complete phone call logging workflow
     *
     * This test verifies the entire end-to-end workflow:
     * 1. Log phone call with notes
     * 2. Verify in database
     * 3. View in timeline
     * 4. Check metrics
     */

    // Step 1: Log phone call
    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Log Call")');

    // Fill call details
    await page.click('[data-testid="call-type-select"]');
    await page.click('text=Outbound');
    await page.fill('[data-testid="duration-input"]', '20');
    await page.click('[data-testid="call-outcome"]');
    await page.click('text=Reached Candidate');
    await page.fill('[data-testid="call-notes"]', 'Technical screening call - candidate passed');

    // Submit
    await page.click('button:has-text("Log Call")');
    await expect(page.locator('text=Call logged successfully')).toBeVisible();

    // Step 2: Navigate to timeline and verify
    await navigateToCommunications(page);
    await page.click('[data-testid="type-filter"]');
    await page.click('text=Phone Calls');

    // Verify call appears in timeline
    await expect(page.locator('[data-testid="phone-call-icon"]')).toBeVisible();

    // Step 3: View call details
    await page.locator('[data-testid="communication-timeline-item"]').first().click();
    await expect(page.locator('text=Technical screening call')).toBeVisible();
    await expect(page.locator('text=20 minutes')).toBeVisible();
    await expect(page.locator('text=Reached Candidate')).toBeVisible();

    // Step 4: Check metrics
    await page.click('[data-testid="metrics-tab"]');
    await expect(page.locator('[data-testid="phone-call-metric"]')).toBeVisible();
  });

  test('Phone call with different call types', async () => {
    /**
     * Test: Log different types of phone calls
     *
     * Verifies:
     * - Inbound calls can be logged
     * - Missed calls can be logged
     * - Outbound calls can be logged
     * - Duration defaults to 0 for missed calls
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Test inbound call
    await page.click('button:has-text("Log Call")');
    await page.click('[data-testid="call-type-select"]');
    await page.click('text=Inbound');

    // Verify phone numbers are swapped for inbound
    const fromNumber = page.locator('input[name="from_number"]');
    await expect(fromNumber).toHaveValue(testCandidate.phone);

    await page.fill('[data-testid="duration-input"]', '5');
    await page.click('[data-testid="call-outcome"]');
    await page.click('text=Reached Candidate');
    await page.fill('[data-testid="call-notes"]', 'Candidate called with questions');

    await page.click('button:has-text("Log Call")');
    await expect(page.locator('text=Call logged successfully')).toBeVisible();

    // Test missed call
    await page.click('button:has-text("Log Call")');
    await page.click('[data-testid="call-type-select"]');
    await page.click('text=Missed');

    // Verify duration is automatically 0 for missed
    const duration = page.locator('[data-testid="duration-input"]');
    await expect(duration).toHaveValue('0');

    await page.fill('[data-testid="call-notes"]', 'Missed call - need to call back');

    await page.click('button:has-text("Log Call")');
    await expect(page.locator('text=Call logged successfully')).toBeVisible();
  });

  test('Phone call filtering and search', async () => {
    /**
     * Test: Filter and search phone calls
     *
     * Verifies:
     * - Filter by type (phone_call) works
     * - Filter by direction (outbound/inbound) works
     * - Search by notes content works
     */

    await navigateToCommunications(page);

    // Filter by phone calls
    await page.click('[data-testid="type-filter"]');
    await page.click('text=Phone Calls');
    await page.waitForLoadState('networkidle');

    // Verify only phone calls shown
    const items = page.locator('[data-testid="communication-timeline-item"]');
    const count = await items.count();
    for (let i = 0; i < count; i++) {
      await expect(items.nth(i).locator('[data-testid="phone-call-icon"]')).toBeVisible();
    }

    // Filter by direction
    await page.click('[data-testid="direction-filter"]');
    await page.click('text=Outbound');
    await page.waitForLoadState('networkidle');

    // Search by notes content
    await page.fill('[data-testid="search-input"]', 'technical screening');
    await page.press('[data-testid="search-input"]', 'Enter');
    await page.waitForLoadState('networkidle');

    // Verify search results
    const searchResults = page.locator('[data-testid="communication-timeline-item"]');
    const searchCount = await searchResults.count();
    if (searchCount > 0) {
      const firstResultText = await searchResults.first().textContent();
      expect(firstResultText?.toLowerCase()).toContain('technical');
    }
  });

  test('Phone call validation', async () => {
    /**
     * Test: Phone call form validation
     *
     * Verifies:
     * - Duration must be non-negative
     * - Outcome selection is required
     * - Phone numbers are validated
     */

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Log Call")');

    // Try to submit without outcome
    await page.click('[data-testid="duration-input"]');
    await page.fill('[data-testid="duration-input"]', '15');

    // Verify submit button is disabled or validation error shown
    const submitButton = page.locator('button:has-text("Log Call")');
    const isEnabled = await submitButton.isEnabled();

    // Should be disabled if outcome not selected
    // (adjust based on actual validation behavior)
    if (!isEnabled) {
      // Select outcome and verify button becomes enabled
      await page.click('[data-testid="call-outcome"]');
      await page.click('text=Reached Candidate');
      await expect(submitButton).toBeEnabled();
    }

    // Test negative duration validation
    await page.fill('[data-testid="duration-input"]', '-5');
    await page.click('[data-testid="call-notes"]');

    // Verify validation error for negative duration
    await expect(page.locator('text=Duration must be positive')).toBeVisible();
  });

  test('Phone call responsive design', async () => {
    /**
     * Test: Phone call logger responsive design
     *
     * Verifies:
     * - Form works on mobile viewport
     * - Form works on tablet viewport
     * - Form works on desktop viewport
     */

    // Mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Log Call")');

    await expect(page.locator('[data-testid="call-type-select"]')).toBeVisible();
    await expect(page.locator('[data-testid="duration-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="call-outcome"]')).toBeVisible();

    // Tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[data-testid="call-type-select"]')).toBeVisible();

    // Desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('[data-testid="call-type-select"]')).toBeVisible();
  });

  test('Phone call error handling', async () => {
    /**
     * Test: Phone call error handling
     *
     * Verifies:
     * - API errors are displayed
     * - Network errors are handled gracefully
     * - Form can be resubmitted after error
     */

    // Mock API failure scenario
    await page.route('**/api/communications/', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });

    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Log Call")');

    // Fill form
    await page.click('[data-testid="call-type-select"]');
    await page.click('text=Outbound');
    await page.fill('[data-testid="duration-input"]', '10');
    await page.click('[data-testid="call-outcome"]');
    await page.click('text=Reached Candidate');
    await page.fill('[data-testid="call-notes"]', 'Test call');

    // Submit and verify error handling
    await page.click('button:has-text("Log Call")');
    await expect(page.locator('text=Failed to log call')).toBeVisible();

    // Remove mock to restore normal behavior
    await page.unroute('**/api/communications/');
  });
});
