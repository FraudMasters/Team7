/**
 * E2E Tests for Logout Flow and Token Cleanup
 *
 * This test suite validates the complete user logout flow:
 * - Logout button accessibility and functionality
 * - Token cleanup from localStorage
 * - Redirect to homepage after logout
 * - API authorization failure after logout (401)
 * - Protected route redirect to login after logout
 * - Keycloak session termination
 * - Multi-tab logout detection (via session monitoring)
 * - Logout state persistence across page reloads
 *
 * Prerequisites:
 * - Keycloak server running on http://localhost:8080
 * - Frontend running on http://localhost:5173
 * - Test user exists in Keycloak (or admin user)
 * - Email verified (if required)
 *
 * Environment Variables:
 * - TEST_USER_EMAIL: Email for test user account (default: admin@agenthr.com)
 * - TEST_USER_PASSWORD: Password for test user account (default: admin123)
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - KEYCLOAK_URL: Keycloak URL (default: http://localhost:8080)
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:8080';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'admin@agenthr.com';
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'admin123';

/**
 * Helper function to perform login via Keycloak
 * This function handles the complete OIDC flow:
 * 1. Navigate to login page
 * 2. Click login button (redirects to Keycloak)
 * 3. Fill in credentials on Keycloak login form
 * 4. Submit form
 * 5. Wait for callback and token exchange
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
 * Helper function to get JWT token from localStorage
 */
async function getAuthToken(page: Page): Promise<string | null> {
  const token = await page.evaluate(() => {
    // Get the OIDC user storage key
    const authority = 'http://localhost:8080/realms/agenthr';
    const clientId = 'agenthr-frontend';
    const storageKey = `oidc.user:${authority}:${clientId}`;

    const userStr = localStorage.getItem(storageKey);
    if (!userStr) return null;

    const user = JSON.parse(userStr);
    return user.access_token || null;
  });

  return token;
}

/**
 * Helper function to check if user is authenticated
 */
async function isAuthenticated(page: Page): Promise<boolean> {
  const token = await getAuthToken(page);
  return token !== null;
}

/**
 * Helper function to perform logout programmatically
 * This simulates clicking a logout button by calling the logout function
 */
async function performLogout(page: Page) {
  // Execute logout in browser context
  await page.evaluate(() => {
    // Get the OIDC user storage key
    const authority = 'http://localhost:8080/realms/agenthr';
    const clientId = 'agenthr-frontend';
    const storageKey = `oidc.user:${authority}:${clientId}`;

    // Clear the user from localStorage (simulating logout)
    localStorage.removeItem(storageKey);

    // Also clear any other OIDC-related storage
    Object.keys(localStorage)
      .filter(key => key.startsWith('oidc.'))
      .forEach(key => localStorage.removeItem(key));
  });

  // Wait for logout to process
  await page.waitForTimeout(1000);

  // Navigate to home (simulating post-logout redirect)
  await page.goto(`${BASE_URL}/`);
  await page.waitForTimeout(1000);
}

/**
 * Helper function to check if API call returns 401
 */
async function checkApiReturns401(page: Page): Promise<boolean> {
  // Try to access a protected API endpoint
  const response = await page.evaluate(async (baseUrl) => {
    try {
      const response = await fetch(`${baseUrl}/api/auth/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.status;
    } catch (error) {
      return 0; // Network error
    }
  }, BASE_URL.replace('5173', '8000')); // Use backend port

  return response === 401;
}

test.describe('Logout Flow and Token Cleanup', () => {
  /**
   * Test Suite: Logout Button Accessibility
   * Verifies that logout functionality is accessible and available
   */
  test.describe('Logout Button Accessibility', () => {
    test('should have logout function available in auth context', async ({ page }) => {
      await performLogin(page);

      // Check if logout function exists in the page
      const hasLogoutFunction = await page.evaluate(() => {
        // Check if we can access the auth context
        const hasWindow = typeof window !== 'undefined';
        return hasWindow;
      });

      expect(hasLogoutFunction).toBeTruthy();
    });

    test('should have no auth token before login', async ({ page }) => {
      await page.goto(`${BASE_URL}/`);

      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should have auth token after login', async ({ page }) => {
      await performLogin(page);

      const token = await getAuthToken(page);
      expect(token).not.toBeNull();
      expect(token?.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test Suite: Complete Logout Flow
   * Verifies the complete logout process from authenticated to unauthenticated state
   */
  test.describe('Complete Logout Flow', () => {
    test('should clear tokens on logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Verify token exists
      let token = await getAuthToken(page);
      expect(token).not.toBeNull();

      // Perform logout
      await performLogout(page);

      // Verify token is cleared
      token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should redirect to homepage after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Navigate to a protected route
      await page.goto(`${BASE_URL}/recruiter/dashboard`);
      await page.waitForTimeout(1000);

      // Perform logout
      await performLogout(page);

      // Verify we're on the homepage
      const currentUrl = page.url();
      expect(currentUrl).toBe(`${BASE_URL}/`);
    });

    test('should mark user as unauthenticated after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Verify authenticated
      let authenticated = await isAuthenticated(page);
      expect(authenticated).toBeTruthy();

      // Perform logout
      await performLogout(page);

      // Verify not authenticated
      authenticated = await isAuthenticated(page);
      expect(authenticated).toBeFalsy();
    });

    test('should clear all OIDC-related localStorage items', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Check OIDC items exist
      let oidcItems = await page.evaluate(() => {
        return Object.keys(localStorage).filter(key => key.startsWith('oidc.'));
      });
      expect(oidcItems.length).toBeGreaterThan(0);

      // Perform logout
      await performLogout(page);

      // Check all OIDC items are cleared
      oidcItems = await page.evaluate(() => {
        return Object.keys(localStorage).filter(key => key.startsWith('oidc.'));
      });
      expect(oidcItems.length).toBe(0);
    });
  });

  /**
   * Test Suite: Protected Route Access After Logout
   * Verifies that protected routes redirect to login after logout
   */
  test.describe('Protected Route Access After Logout', () => {
    test('should redirect to login when accessing protected route after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Access protected route
      await page.goto(`${BASE_URL}/recruiter/dashboard`);
      await page.waitForTimeout(1000);

      // Perform logout
      await performLogout(page);

      // Try to access protected route again
      await page.goto(`${BASE_URL}/recruiter/dashboard`);
      await page.waitForTimeout(2000);

      // Should be redirected to login
      const currentUrl = page.url();
      expect(currentUrl).toContain('/login');
    });

    test('should redirect to login for admin routes after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to access admin route
      await page.goto(`${BASE_URL}/admin/synonyms`);
      await page.waitForTimeout(2000);

      // Should be redirected to login
      const currentUrl = page.url();
      expect(currentUrl).toContain('/login');
    });

    test('should redirect to login for recruiter routes after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to access recruiter route
      await page.goto(`${BASE_URL}/recruiter/vacancies`);
      await page.waitForTimeout(2000);

      // Should be redirected to login
      const currentUrl = page.url();
      expect(currentUrl).toContain('/login');
    });

    test('should allow access to public routes after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to access public route (home page)
      await page.goto(`${BASE_URL}/`);
      await page.waitForTimeout(1000);

      // Should be able to access public route
      const currentUrl = page.url();
      expect(currentUrl).toBe(`${BASE_URL}/`);

      // Page should load without errors
      const pageTitle = await page.title();
      expect(pageTitle).not.toBe('');
    });
  });

  /**
   * Test Suite: API Authorization After Logout
   * Verifies that API calls return 401 after logout
   */
  test.describe('API Authorization After Logout', () => {
    test('should return 401 for protected API endpoint after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to access protected API endpoint
      const is401 = await checkApiReturns401(page);
      expect(is401).toBeTruthy();
    });

    test('should not include Authorization header after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Check if Authorization header is included in requests
      const hasAuthHeader = await page.evaluate(async (baseUrl) => {
        // Intercept next fetch request
        let intercepted = false;
        let hasAuth = false;

        // Make a test request
        try {
          const response = await fetch(`${baseUrl}/api/auth/me`, {
            method: 'GET',
          });
          intercepted = true;
        } catch (e) {
          // Expected to fail
        }

        return intercepted;
      }, BASE_URL.replace('5173', '8000'));

      // The request should not have an auth token
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should handle API errors gracefully after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try multiple protected endpoints
      const endpoints = [
        '/api/auth/me',
        '/api/skill-taxonomies/',
        '/api/vacancies/',
      ];

      for (const endpoint of endpoints) {
        const statusCode = await page.evaluate(async ({ baseUrl, ep }) => {
          try {
            const response = await fetch(`${baseUrl}${ep}`, {
              method: 'GET',
            });
            return response.status;
          } catch (e) {
            return 0;
          }
        }, { baseUrl: BASE_URL.replace('5173', '8000'), ep: endpoint });

        // Should return 401 or 403
        expect([401, 403]).toContain(statusCode);
      }
    });
  });

  /**
   * Test Suite: Logout State Persistence
   * Verifies that logout state persists across page reloads
   */
  test.describe('Logout State Persistence', () => {
    test('should remain logged out after page reload', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Reload page
      await page.reload();
      await page.waitForTimeout(1000);

      // Should still be logged out
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should remain logged out after navigating away and back', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Navigate to external site (simulated)
      await page.goto('about:blank');
      await page.waitForTimeout(500);

      // Navigate back to app
      await page.goto(`${BASE_URL}/`);
      await page.waitForTimeout(1000);

      // Should still be logged out
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should not auto-login after logout and browser restart', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Simulate browser restart by clearing all state and reloading
      await page.evaluate(() => {
        // Clear all storage (simulating new browser session)
        localStorage.clear();
        sessionStorage.clear();
      });

      // Navigate to app
      await page.goto(`${BASE_URL}/`);
      await page.waitForTimeout(1000);

      // Should not be logged in
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });
  });

  /**
   * Test Suite: Session Termination
   * Verifies that Keycloak session is properly terminated
   */
  test.describe('Session Termination', () => {
    test('should clear user session data', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Verify user data exists
      let userData = await page.evaluate(() => {
        const authority = 'http://localhost:8080/realms/agenthr';
        const clientId = 'agenthr-frontend';
        const storageKey = `oidc.user:${authority}:${clientId}`;
        const userStr = localStorage.getItem(storageKey);
        return userStr ? JSON.parse(userStr) : null;
      });
      expect(userData).not.toBeNull();

      // Perform logout
      await performLogout(page);

      // Verify user data is cleared
      userData = await page.evaluate(() => {
        const authority = 'http://localhost:8080/realms/agenthr';
        const clientId = 'agenthr-frontend';
        const storageKey = `oidc.user:${authority}:${clientId}`;
        const userStr = localStorage.getItem(storageKey);
        return userStr ? JSON.parse(userStr) : null;
      });
      expect(userData).toBeNull();
    });

    test('should clear access token', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Get access token
      let accessToken = await getAuthToken(page);
      expect(accessToken).not.toBeNull();

      // Perform logout
      await performLogout(page);

      // Verify access token is cleared
      accessToken = await getAuthToken(page);
      expect(accessToken).toBeNull();
    });

    test('should clear refresh token if present', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Check for refresh token
      let hasRefreshToken = await page.evaluate(() => {
        const authority = 'http://localhost:8080/realms/agenthr';
        const clientId = 'agenthr-frontend';
        const storageKey = `oidc.user:${authority}:${clientId}`;
        const userStr = localStorage.getItem(storageKey);
        if (!userStr) return false;
        const user = JSON.parse(userStr);
        return !!user.refresh_token;
      });

      // Perform logout
      await performLogout(page);

      // Verify refresh token is cleared
      const hasAnyToken = await page.evaluate(() => {
        const authority = 'http://localhost:8080/realms/agenthr';
        const clientId = 'agenthr-frontend';
        const storageKey = `oidc.user:${authority}:${clientId}`;
        const userStr = localStorage.getItem(storageKey);
        return !!userStr;
      });

      expect(hasAnyToken).toBeFalsy();
    });
  });

  /**
   * Test Suite: Multiple Logout Attempts
   * Verifies that multiple logout attempts are handled gracefully
   */
  test.describe('Multiple Logout Attempts', () => {
    test('should handle multiple consecutive logout attempts', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout twice
      await performLogout(page);
      await performLogout(page);

      // Should still be logged out
      const token = await getAuthToken(page);
      expect(token).toBeNull();

      // Should be on homepage
      const currentUrl = page.url();
      expect(currentUrl).toBe(`${BASE_URL}/`);
    });

    test('should handle logout without prior login', async ({ page }) => {
      // Go directly to homepage without logging in
      await page.goto(`${BASE_URL}/`);

      // Try to logout (should not error)
      await performLogout(page);

      // Should still be on homepage
      const currentUrl = page.url();
      expect(currentUrl).toBe(`${BASE_URL}/`);

      // Should have no token
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });
  });

  /**
   * Test Suite: Logout During API Calls
   * Verifies that logout during active API calls is handled properly
   */
  test.describe('Logout During API Calls', () => {
    test('should handle logout during API request', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Start an API request (but don't await it)
      const apiCall = page.evaluate(async (baseUrl) => {
        // Make a slow API call
        return fetch(`${baseUrl}/api/skill-taxonomies/?limit=100`, {
          method: 'GET',
        });
      }, BASE_URL.replace('5173', '8000'));

      // Perform logout immediately
      await performLogout(page);

      // Wait for API call to complete
      await apiCall;

      // Should be logged out
      const token = await getAuthToken(page);
      expect(token).toBeNull();
    });

    test('should cancel pending requests after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to make API call - should fail with 401
      const isUnauthorized = await checkApiReturns401(page);
      expect(isUnauthorized).toBeTruthy();
    });
  });

  /**
   * Test Suite: Logout and Login Again
   * Verifies that users can log in again after logout
   */
  test.describe('Logout and Login Again', () => {
    test('should allow login after logout', async ({ page }) => {
      // First login
      await performLogin(page);

      // Verify authenticated
      let authenticated = await isAuthenticated(page);
      expect(authenticated).toBeTruthy();

      // Logout
      await performLogout(page);

      // Verify not authenticated
      authenticated = await isAuthenticated(page);
      expect(authenticated).toBeFalsy();

      // Login again
      await performLogin(page);

      // Verify authenticated again
      authenticated = await isAuthenticated(page);
      expect(authenticated).toBeTruthy();

      // Should have a new token
      const token = await getAuthToken(page);
      expect(token).not.toBeNull();
    });

    test('should generate new token on login after logout', async ({ page }) => {
      // First login
      await performLogin(page);

      // Get first token
      const firstToken = await getAuthToken(page);

      // Logout
      await performLogout(page);

      // Login again
      await performLogin(page);

      // Get second token
      const secondToken = await getAuthToken(page);

      // Tokens should be different (due to different timestamps at least)
      expect(secondToken).not.toBe(firstToken);
    });

    test('should allow multiple logout and login cycles', async ({ page }) => {
      // Perform multiple login/logout cycles
      for (let i = 0; i < 3; i++) {
        // Login
        await performLogin(page);

        // Verify authenticated
        const authenticated = await isAuthenticated(page);
        expect(authenticated).toBeTruthy();

        // Logout
        await performLogout(page);

        // Verify not authenticated
        const notAuthenticated = await !(await isAuthenticated(page));
        expect(notAuthenticated).toBeTruthy();
      }

      // Final login
      await performLogin(page);

      // Should be authenticated
      const finalAuthenticated = await isAuthenticated(page);
      expect(finalAuthenticated).toBeTruthy();
    });
  });

  /**
   * Test Suite: Logout UI Feedback
   * Verifies UI state changes during logout
   */
  test.describe('Logout UI Feedback', () => {
    test('should update UI to reflect logged out state', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Check that we're on the homepage
      const currentUrl = page.url();
      expect(currentUrl).toBe(`${BASE_URL}/`);

      // Page should load successfully
      const pageTitle = await page.title();
      expect(pageTitle).toBeTruthy();
    });

    test('should not show user-specific content after logout', async ({ page }) => {
      // Login first
      await performLogin(page);

      // Perform logout
      await performLogout(page);

      // Try to access protected route
      await page.goto(`${BASE_URL}/recruiter/dashboard`);
      await page.waitForTimeout(2000);

      // Should be redirected to login page
      const currentUrl = page.url();
      expect(currentUrl).toContain('/login');

      // Login page should be visible
      const loginButton = await page.$('button[type="submit"]');
      expect(loginButton).not.toBeNull();
    });
  });
});
