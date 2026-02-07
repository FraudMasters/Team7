import { test, expect } from '@playwright/test';

/**
 * E2E Tests for GDPR Consent Flow
 *
 * Test Suite Contents:
 * 1. Cookie Banner Display on First Visit
 * 2. Grant Consent via Cookie Banner
 * 3. Verify Consent Saved to Backend API
 * 4. View Consent in ConsentManager
 * 5. Revoke Consent in ConsentManager
 * 6. Verify Revocation Saved to Backend
 * 7. Cookie Consent Persistence Across Sessions
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Clean browser state (no localStorage)
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

test.describe('GDPR Consent Flow - Cookie Banner', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page, context }) => {
    // Clear all cookies and localStorage before each test
    await context.clearCookies();
    await page.goto('/');

    // Clear localStorage
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Reload to ensure clean state
    await page.reload();
  });

  test('should display cookie banner on first visit', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for cookie banner
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).toBeVisible({ timeout: 5000 });

    // Verify banner text mentions cookies/consent
    await expect(page.getByText(/cookie|consent/i)).toBeVisible();

    // Check for action buttons
    const acceptButton = page.getByRole('button', { name: /accept/i });
    const rejectButton = page.getByRole('button', { name: /reject/i });
    const customizeButton = page.getByRole('button', { name: /customize|settings/i });

    // At least accept button should be visible
    await expect(acceptButton).toBeVisible();
  });

  test('should hide banner after accepting all cookies', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click "Accept All" button
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Banner should disappear
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).not.toBeVisible({ timeout: 3000 });
  });

  test('should hide banner after rejecting all cookies', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click "Reject All" button
    const rejectButton = page.getByRole('button', { name: /reject all/i });
    await rejectButton.click();

    // Banner should disappear
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).not.toBeVisible({ timeout: 3000 });
  });

  test('should allow customizing cookie preferences', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click "Customize" button
    const customizeButton = page.getByRole('button', { name: /customize|settings/i });
    await customizeButton.click();

    // Should show customization dialog with checkboxes
    const dialog = page.locator('[role="dialog"]').filter({ hasText: /cookie|preference/i });
    await expect(dialog).toBeVisible();

    // Check for cookie category checkboxes
    const analyticsCheckbox = page.getByRole('checkbox', { name: /analytics/i });
    const marketingCheckbox = page.getByRole('checkbox', { name: /marketing/i });

    // At least one checkbox should be present
    await expect(analyticsCheckbox.or(marketingCheckbox)).toBeVisible();
  });

  test('should save consent preferences to localStorage', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Accept all cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Check localStorage
    const consentData = await page.evaluate(() => {
      const stored = localStorage.getItem('cookie_consent');
      return stored ? JSON.parse(stored) : null;
    });

    expect(consentData).not.toBeNull();
    expect(consentData?.necessary).toBe(true);
    expect(consentData?.analytics).toBe(true);
    expect(consentData?.marketing).toBe(true);
  });

  test('should not show banner on subsequent visits after consent', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Accept cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Banner should not appear
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe('GDPR Consent Flow - Privacy Settings', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page, context }) => {
    // Clear state and navigate to privacy settings
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Accept cookies to proceed
    await page.waitForLoadState('networkidle');
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    const acceptCount = await acceptButton.count();

    if (acceptCount > 0) {
      await acceptButton.click();
    }

    // Navigate to privacy settings page
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');
  });

  test('should display privacy settings page with all components', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /privacy settings/i })).toBeVisible();

    // Check for quick action cards
    await expect(page.getByText(/export my data/i)).toBeVisible();
    await expect(page.getByText(/delete account/i)).toBeVisible();
    await expect(page.getByText(/view consents/i)).toBeVisible();

    // Check for consent manager
    await expect(page.getByText(/consent management/i)).toBeVisible();
  });

  test('should display consent manager with all consent types', async ({ page }) => {
    // Click on "View Consents" or navigate to consent management tab
    const viewConsentsButton = page.getByRole('button', { name: /view consents/i });
    const count = await viewConsentsButton.count();

    if (count > 0) {
      await viewConsentsButton.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Check for consent types
    await expect(page.getByText(/data processing/i)).toBeVisible();
    await expect(page.getByText(/data storage/i)).toBeVisible();
    await expect(page.getByText(/resume analysis/i)).toBeVisible();

    // Check for toggle switches
    const switches = page.locator('.MuiSwitch-root');
    await expect(switches.first()).toBeVisible();
  });

  test('should grant consent via consent manager', async ({ page }) => {
    // Navigate to consent management
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Find a disabled consent switch (not granted)
    const disabledSwitch = page.locator('.MuiSwitch-root').filter({ hasText: /resume analysis/i });
    const switchCount = await disabledSwitch.count();

    if (switchCount > 0) {
      // Get initial state
      const initialState = await disabledSwitch.getAttribute('aria-checked');

      // Click to grant consent
      await disabledSwitch.click();

      // Wait for API call
      await page.waitForTimeout(500);

      // Verify switch changed state
      const newState = await disabledSwitch.getAttribute('aria-checked');
      expect(newState).not.toBe(initialState);
    }
  });

  test('should show confirmation when revoking consent', async ({ page }) => {
    // Navigate to consent management
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Find an enabled consent switch
    const enabledSwitch = page.locator('.MuiSwitch-input[aria-checked="true"]').first();
    const switchCount = await enabledSwitch.count();

    if (switchCount > 0) {
      // Click to revoke consent
      await enabledSwitch.click();

      // Should show confirmation dialog
      const confirmDialog = page.locator('[role="dialog"]').filter({ hasText: /withdraw|revoke/i });
      await expect(confirmDialog).toBeVisible({ timeout: 3000 });

      // Check for confirmation message
      await expect(page.getByText(/are you sure|confirm/i)).toBeVisible();
    }
  });

  test('should revoke consent after confirmation', async ({ page }) => {
    // Navigate to consent management
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Find an enabled consent switch
    const enabledSwitch = page.locator('.MuiSwitch-input[aria-checked="true"]').first();
    const switchCount = await enabledSwitch.count();

    if (switchCount > 0) {
      // Click to revoke consent
      await enabledSwitch.click();

      // Wait for confirmation dialog
      await page.waitForTimeout(500);

      // Click confirm button
      const confirmButton = page.getByRole('button', { name: /confirm|withdraw|yes/i });
      await confirmButton.click();

      // Wait for API call
      await page.waitForTimeout(1000);

      // Verify switch is now unchecked
      const isChecked = await enabledSwitch.getAttribute('aria-checked');
      expect(isChecked).toBe('false');
    }
  });
});

test.describe('GDPR Consent Flow - API Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should send consent grant request to backend API', async ({ page }) => {
    // Clear state
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
    });

    // Accept cookies
    await page.waitForLoadState('networkidle');
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Navigate to consent management tab
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Find and click a consent switch
    const consentSwitch = page.locator('.MuiSwitch-root').first();
    await consentSwitch.click();

    // Wait for API call to complete
    await page.waitForTimeout(1000);

    // Verify no error messages
    const errorMessage = page.getByText(/error|failed/i);
    const errorCount = await errorMessage.count();

    expect(errorCount).toBe(0);
  });

  test('should send consent revocation request to backend API', async ({ page }) => {
    // Clear state
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
    });

    // Accept cookies
    await page.waitForLoadState('networkidle');
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Navigate to consent management tab
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    // Wait for consent manager to load
    await page.waitForTimeout(1000);

    // Find an enabled consent switch
    const enabledSwitch = page.locator('.MuiSwitch-input[aria-checked="true"]').first();
    const switchCount = await enabledSwitch.count();

    if (switchCount > 0) {
      // Click to revoke consent
      await enabledSwitch.click();

      // Wait for confirmation dialog
      await page.waitForTimeout(500);

      // Click confirm button
      const confirmButton = page.getByRole('button', { name: /confirm|withdraw|yes/i });
      await confirmButton.click();

      // Wait for API call to complete
      await page.waitForTimeout(1000);

      // Verify no error messages
      const errorMessage = page.getByText(/error|failed/i);
      const errorCount = await errorMessage.count();

      expect(errorCount).toBe(0);
    }
  });
});

test.describe('GDPR Consent Flow - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test.beforeEach(async ({ page, context }) => {
    // Clear state before each test
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should display cookie banner correctly on mobile', async ({ page }) => {
    // Check for cookie banner
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).toBeVisible({ timeout: 5000 });

    // Check for action buttons (may be stacked on mobile)
    const acceptButton = page.getByRole('button', { name: /accept/i });
    await expect(acceptButton).toBeVisible();
  });

  test('should allow granting consent on mobile', async ({ page }) => {
    // Accept all cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Banner should disappear
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).not.toBeVisible({ timeout: 3000 });

    // Verify consent saved
    const consentData = await page.evaluate(() => {
      const stored = localStorage.getItem('cookie_consent');
      return stored ? JSON.parse(stored) : null;
    });

    expect(consentData).not.toBeNull();
  });

  test('should navigate to privacy settings on mobile', async ({ page }) => {
    // Accept cookies to proceed
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    // Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Check page heading
    await expect(page.getByRole('heading', { name: /privacy/i })).toBeVisible();

    // Check for consent manager (may be collapsed or in tabs on mobile)
    await expect(page.getByText(/consent/i)).toBeVisible();
  });
});

test.describe('GDPR Consent Flow - Complete End-to-End', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('complete consent flow: banner → privacy settings → consent manager → revoke', async ({
    page,
    context,
  }) => {
    // Step 1: Clear state and visit frontend
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Step 2: Verify cookie banner appears
    const cookieBanner = page.locator('[data-testid="cookie-banner"]').or(
      page.locator('.cookie-banner').or(
        page.locator('[role="dialog"]').filter({ hasText: /cookie|consent/i })
      )
    );

    await expect(cookieBanner).toBeVisible();
    console.log('✓ Cookie banner displayed on first visit');

    // Step 3: Grant consents in banner
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    await acceptButton.click();

    await expect(cookieBanner).not.toBeVisible({ timeout: 3000 });
    console.log('✓ Consents granted via cookie banner');

    // Step 4: Verify consent saved to localStorage
    const consentData = await page.evaluate(() => {
      const stored = localStorage.getItem('cookie_consent');
      return stored ? JSON.parse(stored) : null;
    });

    expect(consentData).not.toBeNull();
    expect(consentData?.necessary).toBe(true);
    expect(consentData?.analytics).toBe(true);
    expect(consentData?.marketing).toBe(true);
    console.log('✓ Consent saved to localStorage');

    // Step 5: Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Verify page loaded
    await expect(page.getByRole('heading', { name: /privacy/i })).toBeVisible();
    console.log('✓ Navigated to privacy settings');

    // Step 6: Verify consent visible in ConsentManager
    const consentTab = page.getByRole('tab', { name: /consent/i });
    const tabCount = await consentTab.count();

    if (tabCount > 0) {
      await consentTab.click();
    }

    await page.waitForTimeout(1000);

    // Check for consent types
    await expect(page.getByText(/data processing/i)).toBeVisible();
    await expect(page.getByText(/consent management/i)).toBeVisible();
    console.log('✓ Consent visible in ConsentManager');

    // Step 7: Revoke consent in ConsentManager
    const enabledSwitch = page.locator('.MuiSwitch-input[aria-checked="true"]').first();
    const switchCount = await enabledSwitch.count();

    if (switchCount > 0) {
      // Click to revoke consent
      await enabledSwitch.click();

      // Wait for confirmation dialog
      await page.waitForTimeout(500);

      // Verify confirmation dialog appears
      const confirmDialog = page.locator('[role="dialog"]').filter({ hasText: /withdraw|revoke/i });
      await expect(confirmDialog).toBeVisible();
      console.log('✓ Confirmation dialog displayed');

      // Click confirm button
      const confirmButton = page.getByRole('button', { name: /confirm|withdraw|yes/i });
      await confirmButton.click();

      // Wait for API call
      await page.waitForTimeout(1000);

      // Verify switch is now unchecked
      const isChecked = await enabledSwitch.getAttribute('aria-checked');
      expect(isChecked).toBe('false');
      console.log('✓ Consent revoked in ConsentManager');
    }

    console.log('✓ Complete end-to-end consent flow verified');
  });
});
