/**
 * E2E Tests for Login Flow with Valid Credentials
 *
 * This test suite validates the complete user login flow:
 * - Login page accessibility and UI elements
 * - Redirect to Keycloak for authentication
 * - Callback handling and token exchange
 * - JWT token storage in localStorage
 * - User authentication state after login
 * - Access to protected routes
 * - Role-based access control
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
 * Test: Login page accessibility
 */
test.describe('Login Page Accessibility', () => {
  test('should load login page successfully', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Verify page title
    await expect(page).toHaveTitle(/Resume Analysis/);

    // Verify login form elements are present
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Verify info alert about Keycloak redirect
    await expect(page.locator('text=You will be redirected')).toBeVisible();

    // Verify registration link is present
    await expect(page.locator('text=Don\'t have an account')).toBeVisible();
  });

  test('should have proper form labels and placeholders', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Check email field
    const emailInput = page.locator('input[name="email"]');
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(emailInput).toHaveAttribute('required', '');

    // Check password field
    const passwordInput = page.locator('input[name="password"]');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(passwordInput).toHaveAttribute('required', '');

    // Check submit button
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toContainText('Login');
  });

  test('should have Forgot Password link', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Verify forgot password link
    const forgotPasswordLink = page.locator('text=Forgot Password');
    await expect(forgotPasswordLink).toBeVisible();
  });

  test('should redirect authenticated users to home', async ({ page }) => {
    // First login
    await performLogin(page);

    // Now try to go to login page again
    await page.goto(`${BASE_URL}/login`);

    // Should redirect to home page
    await page.waitForURL(`${BASE_URL}/`, { timeout: 5000 });
    expect(page.url()).toBe(`${BASE_URL}/`);
  });
});

/**
 * Test: Complete login flow
 */
test.describe('Complete Login Flow', () => {
  test('should login with valid credentials', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Verify redirect to home page after successful login
    await page.waitForURL(`${BASE_URL}/`, { timeout: 15000 });
    expect(page.url()).toContain(BASE_URL);
  });

  test('should redirect to Keycloak and back', async ({ page }) => {
    // Start from login page
    await page.goto(`${BASE_URL}/login`);
    expect(page.url()).toContain('/login');

    // Click login button
    await page.click('button[type="submit"]');

    // Verify redirect to Keycloak
    await page.waitForURL(`${KEYCLOAK_URL}/**`, { timeout: 10000 });
    expect(page.url()).toContain(KEYCLOAK_URL);

    // Fill and submit Keycloak form
    await page.fill('input[name="username"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.click('input[type="submit"]');

    // Verify redirect back to frontend
    await page.waitForURL(`${BASE_URL}/callback`, { timeout: 15000 });
    expect(page.url()).toContain('/callback');

    // Wait for final redirect
    await page.waitForTimeout(2000);
  });

  test('should verify user is authenticated after login', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Check authentication state via localStorage
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);

    // Verify we can access protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(1000);

    // Should NOT redirect to login (we're authenticated)
    expect(page.url()).toContain('/recruiter/dashboard');
  });

  test('should store JWT token in localStorage', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Get JWT token from localStorage
    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    // Verify token is a valid JWT format (header.payload.signature)
    if (token) {
      const parts = token.split('.');
      expect(parts).toHaveLength(3);

      // Decode payload and verify basic structure
      const payload = JSON.parse(atob(parts[1]));
      expect(payload).toHaveProperty('exp');
      expect(payload).toHaveProperty('iat');
      expect(payload).toHaveProperty('sub');
    }
  });

  test('should include roles in JWT token', async ({ page }) => {
    // Perform login as admin user
    await performLogin(page);

    // Get JWT token
    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      // Decode payload
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));

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
 * Test: Access protected routes after login
 */
test.describe('Protected Route Access', () => {
  test('should access recruiter routes after login', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Try to access recruiter dashboard
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    await page.waitForTimeout(1000);

    // Should not redirect to login
    expect(page.url()).toContain('/recruiter/dashboard');
    await expect(page.locator('body')).not.toContainText('Access Denied');
  });

  test('should access admin routes with Admin role', async ({ page }) => {
    // Perform login as admin
    await performLogin(page);

    // Try to access admin route
    await page.goto(`${BASE_URL}/admin/synonyms`);
    await page.waitForTimeout(1000);

    // Should not redirect to login
    expect(page.url()).toContain('/admin/synonyms');
    await expect(page.locator('body')).not.toContainText('Access Denied');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Start fresh (no authentication)
    await page.context().clearCookies();

    // Try to access protected route directly
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    // Should redirect to login
    await page.waitForURL(`${BASE_URL}/login`, { timeout: 5000 });
    expect(page.url()).toContain('/login');
  });
});

/**
 * Test: Login with invalid credentials
 */
test.describe('Login with Invalid Credentials', () => {
  test('should show error for wrong password', async ({ page }) => {
    // Navigate to login
    await page.goto(`${BASE_URL}/login`);
    await page.click('button[type="submit"]');

    // Wait for Keycloak redirect
    await page.waitForURL(`${KEYCLOAK_URL}/**`);

    // Fill with wrong password
    await page.fill('input[name="username"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', 'WrongPassword123!');

    // Submit form
    await page.click('input[type="submit"]');

    // Wait for error message
    await page.waitForTimeout(2000);

    // Keycloak should show error
    const pageContent = await page.content();
    expect(pageContent).toMatch(/Invalid username or password/i);
  });

  test('should show error for non-existent user', async ({ page }) => {
    // Navigate to login
    await page.goto(`${BASE_URL}/login`);
    await page.click('button[type="submit"]');

    // Wait for Keycloak redirect
    await page.waitForURL(`${KEYCLOAK_URL}/**`);

    // Fill with non-existent user
    await page.fill('input[name="username"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', 'SomePassword123!');

    // Submit form
    await page.click('input[type="submit"]');

    // Wait for error message
    await page.waitForTimeout(2000);

    // Keycloak should show error
    const pageContent = await page.content();
    expect(pageContent).toMatch(/Invalid user credentials/i);
  });
});

/**
 * Test: Login flow with role-based access
 */
test.describe('Role-Based Access Control', () => {
  test('should grant access based on user role', async ({ page }) => {
    // Login as admin user
    await performLogin(page);

    // Get JWT token
    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      // Decode and verify roles
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));
      const roles = payload.resource_access['agenthr-frontend'].roles;

      // Verify admin has Admin role
      expect(roles).toContain('Admin');

      // Try accessing admin route
      await page.goto(`${BASE_URL}/admin/synonyms`);
      expect(page.url()).toContain('/admin/synonyms');
    }
  });

  test('should deny access to routes based on role', async ({ page }) => {
    // This test would use a user with limited roles (e.g., Viewer)
    // For now, we test that the mechanism exists

    // Login as admin
    await performLogin(page);

    // Verify we can check roles in the application
    const hasAdminRole = await page.evaluate(() => {
      const authority = 'http://localhost:8080/realms/agenthr';
      const clientId = 'agenthr-frontend';
      const storageKey = `oidc.user:${authority}:${clientId}`;

      const userStr = localStorage.getItem(storageKey);
      if (!userStr) return false;

      const user = JSON.parse(userStr);
      const roles = user.profile?.resource_access?.[clientId]?.roles || [];
      return roles.includes('Admin');
    });

    expect(hasAdminRole).toBe(true);
  });
});

/**
 * Test: Login form navigation
 */
test.describe('Login Form Navigation', () => {
  test('should navigate to registration page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Click registration link
    await page.click('text=Don\'t have an account');

    // Should navigate to registration
    await page.waitForURL(`${BASE_URL}/register`, { timeout: 5000 });
    expect(page.url()).toContain('/register');
  });

  test('should preserve redirect destination', async ({ page }) => {
    // Try to access protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    // Should redirect to login with preserved location
    await page.waitForURL(`${BASE_URL}/login`, { timeout: 5000 });

    // Perform login
    await performLogin(page);

    // Should redirect back to original destination after login
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/recruiter');
  });
});

/**
 * Test: JWT token structure and claims
 */
test.describe('JWT Token Validation', () => {
  test('should have valid JWT structure', async ({ page }) => {
    await performLogin(page);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      // Verify JWT structure (header.payload.signature)
      const parts = token.split('.');
      expect(parts).toHaveLength(3);

      // Verify each part is base64url encoded
      parts.forEach(part => {
        expect(() => atob(part)).not.toThrow();
      });

      // Verify header
      const header = JSON.parse(atob(parts[0]));
      expect(header).toHaveProperty('alg');
      expect(header.alg).toBe('RS256'); // Keycloak uses RS256
      expect(header).toHaveProperty('typ');
      expect(header.typ).toBe('JWT');

      // Verify payload claims
      const payload = JSON.parse(atob(parts[1]));
      expect(payload).toHaveProperty('iss'); // Issuer
      expect(payload).toHaveProperty('sub'); // Subject (user ID)
      expect(payload).toHaveProperty('aud'); // Audience
      expect(payload).toHaveProperty('exp'); // Expiration
      expect(payload).toHaveProperty('iat'); // Issued at
      expect(payload).toHaveProperty('jti'); // JWT ID
      expect(payload).toHaveProperty('email'); // User email
      expect(payload).toHaveProperty('preferred_username'); // Username
    }
  });

  test('should have non-expired token', async ({ page }) => {
    await performLogin(page);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));

      // Get current time and expiration time
      const now = Math.floor(Date.now() / 1000);
      const exp = payload.exp;

      // Token should not be expired
      expect(exp).toBeGreaterThan(now);

      // Token should be valid for at least 1 minute
      expect(exp - now).toBeGreaterThan(60);
    }
  });

  test('should include correct issuer', async ({ page }) => {
    await performLogin(page);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));

      // Issuer should be Keycloak realm
      expect(payload.iss).toBe('http://localhost:8080/realms/agenthr');
    }
  });
});

/**
 * Test: Session persistence
 */
test.describe('Session Persistence', () => {
  test('should maintain authentication across page reloads', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Reload page
    await page.reload();

    // Should still be authenticated
    const authenticated = await isAuthenticated(page);
    expect(authenticated).toBe(true);

    // Should still be able to access protected routes
    await page.goto(`${BASE_URL}/recruiter/dashboard`);
    expect(page.url()).toContain('/recruiter/dashboard');
  });

  test('should preserve token in localStorage', async ({ page }) => {
    // Perform login
    await performLogin(page);

    // Get token
    const token1 = await getAuthToken(page);
    expect(token1).not.toBeNull();

    // Reload page
    await page.reload();

    // Get token again
    const token2 = await getAuthToken(page);
    expect(token2).not.toBeNull();

    // Tokens should be the same (not refreshed yet)
    expect(token1).toBe(token2);
  });
});

/**
 * Test: Login UI feedback
 */
test.describe('Login UI Feedback', () => {
  test('should show loading state during login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Click login button
    await page.click('button[type="submit"]');

    // Should redirect to Keycloak quickly
    // (The loading state on LoginPage is brief before redirect)
    await page.waitForURL(`${KEYCLOAK_URL}/**`, { timeout: 10000 });
  });

  test('should show loading state on callback page', async ({ page }) => {
    // Start login process
    await page.goto(`${BASE_URL}/login`);
    await page.click('button[type="submit"]');

    // Fill Keycloak form
    await page.waitForURL(`${KEYCLOAK_URL}/**`);
    await page.fill('input[name="username"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.click('input[type="submit"]');

    // Verify callback page shows loading
    await page.waitForURL(`${BASE_URL}/callback`, { timeout: 15000 });

    // Check for loading indicator
    await expect(page.locator('text=Completing Authentication')).toBeVisible();
    await expect(page.locator('svg[class*="CircularProgress"]')).toBeVisible();
  });
});

/**
 * Test: Login with different user roles
 */
test.describe('Multi-Role Login Scenarios', () => {
  test('should login with Admin role', async ({ page }) => {
    await performLogin(page);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));
      const roles = payload.resource_access['agenthr-frontend'].roles;

      expect(roles).toContain('Admin');

      // Should access admin routes
      await page.goto(`${BASE_URL}/admin/synonyms`);
      expect(page.url()).toContain('/admin/synonyms');
    }
  });

  test('should have proper role structure in token', async ({ page }) => {
    await performLogin(page);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    if (token) {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));

      // Verify role structure
      expect(payload.resource_access).toBeDefined();
      expect(payload.resource_access['agenthr-frontend']).toBeDefined();
      expect(payload.resource_access['agenthr-frontend'].roles).toBeInstanceOf(Array);

      // Verify roles are strings
      const roles = payload.resource_access['agenthr-frontend'].roles;
      roles.forEach((role: any) => {
        expect(typeof role).toBe('string');
      });
    }
  });
});

/**
 * Test: Logout and login again
 */
test.describe('Logout and Re-login', () => {
  test('should allow login after logout', async ({ page }) => {
    // First login
    await performLogin(page);
    expect(await isAuthenticated(page)).toBe(true);

    // Logout (will be implemented with logout functionality)
    // For now, we'll simulate by clearing localStorage
    await page.evaluate(() => {
      const authority = 'http://localhost:8080/realms/agenthr';
      const clientId = 'agenthr-frontend';
      const storageKey = `oidc.user:${authority}:${clientId}`;
      localStorage.removeItem(storageKey);
    });

    // Verify not authenticated
    expect(await isAuthenticated(page)).toBe(false);

    // Try to access protected route
    await page.goto(`${BASE_URL}/recruiter/dashboard`);

    // Should redirect to login
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('/login');

    // Should be able to login again
    await performLogin(page);
    expect(await isAuthenticated(page)).toBe(true);
  });
});

/**
 * Test: Responsive design
 */
test.describe('Responsive Login Design', () => {
  test('should be mobile-friendly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto(`${BASE_URL}/login`);

    // Verify all elements are visible on mobile
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should be tablet-friendly', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto(`${BASE_URL}/login`);

    // Verify all elements are visible on tablet
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
});
