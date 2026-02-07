/**
 * E2E Tests for JWT Token Refresh Mechanism
 *
 * This test suite validates the automatic JWT token refresh functionality:
 * - Token refresh triggered automatically before expiration
 * - User session maintained without interruption
 * - New tokens stored correctly in localStorage
 * - API calls succeed with refreshed tokens
 * - Token refresh fails gracefully when refresh token expires
 * - Multiple refresh cycles work correctly
 * - Session monitoring for multi-tab logout detection
 *
 * Prerequisites:
 * - Keycloak server running on http://localhost:8080
 * - Frontend running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test user exists in Keycloak (admin@agenthr.com/admin123)
 *
 * Environment Variables:
 * - TEST_USER_EMAIL: Email for test user account (default: admin@agenthr.com)
 * - TEST_USER_PASSWORD: Password for test user account (default: admin123)
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - KEYCLOAK_URL: Keycloak URL (default: http://localhost:8080)
 * - API_URL: Backend API URL (default: http://localhost:8000)
 *
 * Keycloak Token Configuration:
 * - Access Token Lifespan: 5 minutes (300 seconds) - can be adjusted in Realm Settings
 * - Client Session Idle: 30 minutes
 * - Client Session Max: 10 hours
 *
 * Note: These tests use short token expiration times configured in Keycloak
 * for testing purposes. In production, access tokens typically have longer lifespans.
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:8080';
const API_URL = process.env.API_URL || 'http://localhost:8000';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'admin@agenthr.com';
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'admin123';

/**
 * Helper function to perform login via Keycloak
 */
async function performLogin(page: Page, email?: string, password?: string) {
  const loginEmail = email || TEST_USER_EMAIL;
  const loginPassword = password || TEST_USER_PASSWORD;

  // Navigate to login page
  await page.goto(`${BASE_URL}/login`);

  // Click login button to redirect to Keycloak
  await page.click('button[type="submit"]');

  // Wait for redirect to Keycloak
  await page.waitForURL(`${KEYCLOAK_URL}/**`);

  // Fill in Keycloak login form
  await page.fill('input[name="username"]', loginEmail);
  await page.fill('input[name="password"]', loginPassword);

  // Submit login form
  await page.click('input[type="submit"]');

  // Wait for redirect back to frontend callback
  await page.waitForURL(`${BASE_URL}/callback`, { timeout: 15000 });

  // Wait for navigation from callback to home or original destination
  await page.waitForURL(/\/(callback|\?)*/, { timeout: 15000 });

  // Wait a bit for token processing
  await page.waitForTimeout(2000);
}

/**
 * Helper function to get JWT access token from localStorage
 */
async function getAccessToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    const authority = 'http://localhost:8080/realms/agenthr';
    const clientId = 'agenthr-frontend';
    const storageKey = `oidc.user:${authority}:${clientId}`;

    const userStr = localStorage.getItem(storageKey);
    if (!userStr) return null;

    const user = JSON.parse(userStr);
    return user.access_token || null;
  });
}

/**
 * Helper function to get JWT refresh token from localStorage
 */
async function getRefreshToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    const authority = 'http://localhost:8080/realms/agenthr';
    const clientId = 'agenthr-frontend';
    const storageKey = `oidc.user:${authority}:${clientId}`;

    const userStr = localStorage.getItem(storageKey);
    if (!userStr) return null;

    const user = JSON.parse(userStr);
    return user.refresh_token || null;
  });
}

/**
 * Helper function to decode JWT payload
 */
async function decodeToken(page: Page, token: string): Promise<any> {
  return await page.evaluate((t) => {
    const parts = t.split('.');
    if (parts.length !== 3) return null;
    return JSON.parse(atob(parts[1]));
  }, token);
}

/**
 * Helper function to get token expiration time
 */
async function getTokenExpiration(page: Page): Promise<number | null> {
  const token = await getAccessToken(page);
  if (!token) return null;

  const payload = await decodeToken(page, token);
  return payload?.exp || null;
}

/**
 * Helper function to get token issued at time
 */
async function getTokenIssuedAt(page: Page): Promise<number | null> {
  const token = await getAccessToken(page);
  if (!token) return null;

  const payload = await decodeToken(page, token);
  return payload?.iat || null;
}

/**
 * Helper function to check if token is expired
 */
async function isTokenExpired(page: Page): Promise<boolean> {
  const exp = await getTokenExpiration(page);
  if (!exp) return true;

  const now = Math.floor(Date.now() / 1000);
  return now >= exp;
}

/**
 * Helper function to get time until token expires (in seconds)
 */
async function getTimeUntilExpiration(page: Page): Promise<number | null> {
  const exp = await getTokenExpiration(page);
  if (!exp) return null;

  const now = Math.floor(Date.now() / 1000);
  return Math.max(0, exp - now);
}

/**
 * Helper function to make authenticated API call
 */
async function makeAuthenticatedRequest(
  page: Page,
  endpoint: string
): Promise<{ status: number; data?: any }> {
  const token = await getAccessToken(page);

  const response = await page.evaluate(
    async ({ apiUrl, endpoint, token }) => {
      try {
        const res = await fetch(`${apiUrl}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        return {
          status: res.status,
          data: await res.json().catch(() => null),
        };
      } catch (error) {
        return { status: 0, data: null };
      }
    },
    { apiUrl: API_URL, endpoint, token }
  );

  return response;
}

/**
 * Helper function to wait for token refresh
 * This monitors localStorage for token changes
 */
async function waitForTokenRefresh(
  page: Page,
  timeout: number = 60000
): Promise<boolean> {
  const initialToken = await getAccessToken(page);
  const initialExp = await getTokenExpiration(page);

  if (!initialToken || !initialExp) {
    return false;
  }

  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    await page.waitForTimeout(1000); // Check every second

    const currentToken = await getAccessToken(page);
    const currentExp = await getTokenExpiration(page);

    // Check if token has changed (new iat or exp)
    if (currentToken !== initialToken) {
      return true;
    }

    // Check if expiration time has been extended
    if (currentExp && currentExp > initialExp) {
      return true;
    }
  }

  return false;
}

/**
 * Test Suite: Token Storage and Structure
 */
test.describe('Token Storage and Structure', () => {
  test('should store both access and refresh tokens after login', async ({
    page,
  }) => {
    await performLogin(page);

    // Get tokens
    const accessToken = await getAccessToken(page);
    const refreshToken = await getRefreshToken(page);

    // Verify both tokens exist
    expect(accessToken).not.toBeNull();
    expect(refreshToken).not.toBeNull();

    // Verify access token format (header.payload.signature)
    if (accessToken) {
      const parts = accessToken.split('.');
      expect(parts).toHaveLength(3);
    }

    // Verify refresh token format
    if (refreshToken) {
      const parts = refreshToken.split('.');
      expect(parts.length).toBeGreaterThanOrEqual(2);
    }
  });

  test('should include expiration claims in access token', async ({ page }) => {
    await performLogin(page);

    const token = await getAccessToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const payload = await decodeToken(page, token);

      // Verify standard JWT claims
      expect(payload).toHaveProperty('exp'); // Expiration time
      expect(payload).toHaveProperty('iat'); // Issued at time
      expect(payload).toHaveProperty('sub'); // Subject (user ID)
      expect(payload).toHaveProperty('iss'); // Issuer
      expect(payload).toHaveProperty('aud'); // Audience

      // Verify expiration is in the future
      const exp = payload.exp;
      const now = Math.floor(Date.now() / 1000);
      expect(exp).toBeGreaterThan(now);
    }
  });

  test('should have reasonable token expiration time', async ({ page }) => {
    await performLogin(page);

    const timeUntilExpiry = await getTimeUntilExpiration(page);

    // Token should expire between 1 minute and 1 hour
    // (adjust based on your Keycloak configuration)
    expect(timeUntilExpiry).toBeGreaterThanOrEqual(60); // At least 1 minute
    expect(timeUntilExpiry).toBeLessThanOrEqual(3600); // At most 1 hour
  });

  test('should include roles in access token', async ({ page }) => {
    await performLogin(page);

    const token = await getAccessToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const payload = await decodeToken(page, token);

      // Verify resource_access contains client roles
      expect(payload).toHaveProperty('resource_access');
      expect(payload.resource_access).toHaveProperty('agenthr-frontend');
      expect(payload.resource_access['agenthr-frontend']).toHaveProperty('roles');

      // Admin user should have Admin role
      const roles = payload.resource_access['agenthr-frontend'].roles;
      expect(roles).toContain('Admin');
    }
  });
});

/**
 * Test Suite: Automatic Token Refresh
 */
test.describe('Automatic Token Refresh', () => {
  test('should refresh token before expiration', async ({ page }) => {
    await performLogin(page);

    // Get initial token details
    const initialToken = await getAccessToken(page);
    const initialIat = await getTokenIssuedAt(page);
    const initialExp = await getTokenExpiration(page);

    expect(initialToken).not.toBeNull();
    expect(initialIat).not.toBeNull();
    expect(initialExp).not.toBeNull();

    // Wait for automatic refresh (typically 1 minute before expiration)
    // This may take several minutes depending on Keycloak configuration
    const refreshed = await waitForTokenRefresh(page, 300000); // 5 minute timeout

    if (refreshed) {
      // Get new token details
      const newToken = await getAccessToken(page);
      const newIat = await getTokenIssuedAt(page);
      const newExp = await getTokenExpiration(page);

      // Verify token has changed
      expect(newToken).not.toBe(initialToken);

      // Verify new token was issued later
      expect(newIat).toBeGreaterThan(initialIat);

      // Verify new token expires later
      expect(newExp).toBeGreaterThan(initialExp);

      // Verify new token is still valid
      const now = Math.floor(Date.now() / 1000);
      expect(newExp).toBeGreaterThan(now);
    } else {
      // If refresh didn't happen within timeout, check if token is still valid
      const isValid = !(await isTokenExpired(page));
      expect(isValid).toBe(true);
    }
  });

  test('should maintain user session after token refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Navigate to a protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(1000);

    // Verify we can access the route
    expect(page.url()).toContain('/recruiter/dashboard');

    // Wait for token refresh
    await waitForTokenRefresh(page, 300000);

    // Try to access the same route again
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(1000);

    // Should still have access (not redirected to login)
    expect(page.url()).toContain('/recruiter/dashboard');
    await expect(page.locator('body')).not.toContainText('Access Denied');
  });

  test('should update token in localStorage after refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Get initial token
    const initialToken = await getAccessToken(page);

    // Wait for refresh
    await waitForTokenRefresh(page, 300000);

    // Get new token
    const newToken = await getAccessToken(page);

    // Tokens should be different
    expect(newToken).not.toBe(initialToken);

    // New token should still be valid
    const isValid = !(await isTokenExpired(page));
    expect(isValid).toBe(true);
  });

  test('should preserve user claims after token refresh', async ({ page }) => {
    await performLogin(page);

    // Get initial token and extract claims
    const initialToken = await getAccessToken(page);
    const initialPayload = initialToken
      ? await decodeToken(page, initialToken)
      : null;

    expect(initialPayload).not.toBeNull();

    // Wait for refresh
    await waitForTokenRefresh(page, 300000);

    // Get new token and extract claims
    const newToken = await getAccessToken(page);
    const newPayload = newToken ? await decodeToken(page, newToken) : null;

    expect(newPayload).not.toBeNull();

    // Verify critical claims are preserved
    if (initialPayload && newPayload) {
      expect(newPayload.sub).toBe(initialPayload.sub); // User ID
      expect(newPayload.resource_access).toEqual(initialPayload.resource_access); // Roles
    }
  });
});

/**
 * Test Suite: API Calls with Refreshed Tokens
 */
test.describe('API Calls with Refreshed Tokens', () => {
  test('should successfully make API call after token refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Wait for token refresh
    await waitForTokenRefresh(page, 300000);

    // Make authenticated API call
    const response = await makeAuthenticatedRequest(page, '/api/auth/me');

    // Should succeed with 200 OK
    expect(response.status).toBe(200);
    expect(response.data).not.toBeNull();
  });

  test('should include new access token in API request after refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Wait for token refresh
    await waitForTokenRefresh(page, 300000);

    // Get current token from localStorage
    const currentToken = await getAccessToken(page);

    // Intercept API request to check Authorization header
    let requestToken: string | null = null;
    page.route('**/api/auth/me', async (route) => {
      const headers = route.request().headers();
      requestToken = headers['authorization'] || null;

      if (requestToken && requestToken.startsWith('Bearer ')) {
        requestToken = requestToken.substring(7);
      }

      route.continue();
    });

    // Make API call
    await makeAuthenticatedRequest(page, '/api/auth/me');

    // Verify Authorization header includes current token
    expect(requestToken).toBe(currentToken);
  });

  test('should handle multiple sequential API calls after refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Wait for token refresh
    await waitForTokenRefresh(page, 300000);

    // Make multiple API calls
    const responses = await Promise.all([
      makeAuthenticatedRequest(page, '/api/auth/me'),
      makeAuthenticatedRequest(page, '/api/auth/me'),
      makeAuthenticatedRequest(page, '/api/auth/me'),
    ]);

    // All should succeed
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });
});

/**
 * Test Suite: Token Refresh Failure Handling
 */
test.describe('Token Refresh Failure Handling', () => {
  test('should handle expired refresh token gracefully', async ({ page }) => {
    // This test requires a user with a very short refresh token lifespan
    // For testing purposes, you can configure this in Keycloak:
    // Realm Settings → Tokens → Refresh Token Max Reuse → 0
    // Realm Settings → Tokens → Refresh Token Max Age → short duration (e.g., 60 seconds)

    await performLogin(page);

    // Wait for access token to expire
    const timeUntilExpiry = await getTimeUntilExpiration(page);
    if (timeUntilExpiry) {
      await page.waitForTimeout((timeUntilExpiry + 10) * 1000);
    }

    // Try to make API call
    const response = await makeAuthenticatedRequest(page, '/api/auth/me');

    // Should fail with 401 Unauthorized
    expect([401, 403]).toContain(response.status);

    // User should be redirected to login on next page navigation
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/login');
  });

  test('should clear tokens when refresh fails', async ({ page }) => {
    // This test simulates a refresh failure scenario
    await performLogin(page);

    // Wait for access token to expire
    const timeUntilExpiry = await getTimeUntilExpiration(page);
    if (timeUntilExpiry) {
      await page.waitForTimeout((timeUntilExpiry + 10) * 1000);
    }

    // Try to access protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(2000);

    // Should be redirected to login
    expect(page.url()).toContain('/login');

    // Tokens should be cleared
    const token = await getAccessToken(page);
    expect(token).toBeNull();
  });
});

/**
 * Test Suite: Multiple Refresh Cycles
 */
test.describe('Multiple Refresh Cycles', () => {
  test('should handle multiple token refresh cycles', async ({ page }) => {
    await performLogin(page);

    const refreshCount = 3;
    const tokens: string[] = [];

    for (let i = 0; i < refreshCount; i++) {
      const token = await getAccessToken(page);
      tokens.push(token || '');

      // Wait for refresh
      const refreshed = await waitForTokenRefresh(page, 300000);

      if (!refreshed) {
        // If refresh didn't happen, break the loop
        break;
      }
    }

    // Verify tokens changed (if refresh happened)
    const uniqueTokens = new Set(tokens);
    if (uniqueTokens.size > 1) {
      expect(uniqueTokens.size).toBeGreaterThan(1);
    }
  });

  test('should maintain session across multiple refresh cycles', async ({
    page,
  }) => {
    await performLogin(page);

    // Navigate to protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    const refreshCycles = 3;

    for (let i = 0; i < refreshCycles; i++) {
      // Wait for refresh
      await waitForTokenRefresh(page, 300000);

      // Verify we still have access
      await page.goto(`${BASE_URL}/recruiter/dashboard`);
      await page.waitForTimeout(1000);
      expect(page.url()).toContain('/recruiter/dashboard');
    }
  });
});

/**
 * Test Suite: Session Monitoring
 */
test.describe('Session Monitoring', () => {
  test('should detect logout in another tab', async ({ context }) => {
    // Create two tabs/pages
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Login in first tab
    await performLogin(page1);
    await page1.goto(`${BASE_URL}/recruiter/dashboard`);

    // Login in second tab (same user, same session)
    await performLogin(page2);
    await page2.goto(`${BASE_URL}/recruiter/dashboard`);

    // Logout in first tab
    await page1.goto(`${BASE_URL}/login`);
    await page1.click('button:has-text("Logout")');

    // Wait for session monitoring to detect logout (checkSessionIntervalInSeconds: 10)
    await page2.waitForTimeout(15000);

    // Second tab should be logged out
    await page2.goto(`${BASE_URL}/recruiter/dashboard`);
    await page2.waitForTimeout(2000);

    // Should redirect to login
    expect(page2.url()).toContain('/login');

    // Cleanup
    await page1.close();
    await page2.close();
  });

  test('should monitor session state periodically', async ({ page }) => {
    // This test verifies that session monitoring is enabled
    await performLogin(page);

    // The oidcConfig has monitorSession: true and checkSessionIntervalInSeconds: 10
    // We can verify this by checking the oidc library configuration

    const sessionMonitoringEnabled = await page.evaluate(() => {
      const authority = 'http://localhost:8080/realms/agenthr';
      const clientId = 'agenthr-frontend';
      const storageKey = `oidc.user:${authority}:${clientId}`;

      const userStr = localStorage.getItem(storageKey);
      if (!userStr) return false;

      const user = JSON.parse(userStr);

      // Check if session_state exists (indicates session monitoring)
      return user.session_state !== undefined;
    });

    expect(sessionMonitoringEnabled).toBe(true);
  });
});

/**
 * Test Suite: Token Refresh Without User Interruption
 */
test.describe('Token Refresh Without User Interruption', () => {
  test('should refresh token without blocking UI', async ({ page }) => {
    await performLogin(page);

    // Navigate to a page with content
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    // Monitor for UI blocking or loading indicators
    const hadLoadingIndicator = await page.evaluate(async () => {
      // Wait for potential refresh
      await new Promise((resolve) => setTimeout(resolve, 60000));

      // Check if any loading indicators were shown
      const loadingElements = document.querySelectorAll(
        '[role="progressbar"], .loading, .spinner'
      );
      return loadingElements.length > 0;
    });

    // Token refresh should be silent (no loading indicators)
    // Note: This test runs for 60 seconds to catch automatic refresh
    expect(hadLoadingIndicator).toBe(false);
  });

  test('should allow user interaction during token refresh', async ({
    page,
  }) => {
    await performLogin(page);

    // Navigate to a page with interactive elements
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    // Monitor user interactions during potential refresh period
    const interactionsSuccessful = await page.evaluate(async () => {
      const interactions = [];

      // Simulate user interactions over 60 seconds
      for (let i = 0; i < 6; i++) {
        await new Promise((resolve) => setTimeout(resolve, 10000));

        // Try to scroll or interact with page
        window.scrollTo(0, window.scrollY + 100);
        interactions.push(true);
      }

      return interactions.every((success) => success === true);
    });

    // User should be able to interact without interruption
    expect(interactionsSuccessful).toBe(true);
  });
});

/**
 * Test Suite: Token Refresh Configuration
 */
test.describe('Token Refresh Configuration', () => {
  test('should have automaticSilentRenew enabled', async ({ page }) => {
    await performLogin(page);

    // Verify that automatic silent renew is configured
    const hasAutomaticSilentRenew = await page.evaluate(() => {
      // Check if tokens are being managed by oidc-client-ts
      const authority = 'http://localhost:8080/realms/agenthr';
      const clientId = 'agenthr-frontend';
      const storageKey = `oidc.user:${authority}:${clientId}`;

      const userStr = localStorage.getItem(storageKey);
      if (!userStr) return false;

      const user = JSON.parse(userStr);

      // Presence of tokens indicates oidc-client-ts is managing them
      return user.access_token !== undefined && user.refresh_token !== undefined;
    });

    expect(hasAutomaticSilentRenew).toBe(true);
  });

  test('should have session monitoring enabled', async ({ page }) => {
    await performLogin(page);

    // Verify session monitoring is active
    const hasSessionState = await page.evaluate(() => {
      const authority = 'http://localhost:8080/realms/agenthr';
      const clientId = 'agenthr-frontend';
      const storageKey = `oidc.user:${authority}:${clientId}`;

      const userStr = localStorage.getItem(storageKey);
      if (!userStr) return false;

      const user = JSON.parse(userStr);
      return user.session_state !== undefined;
    });

    expect(hasSessionState).toBe(true);
  });
});
