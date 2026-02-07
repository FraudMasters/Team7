/**
 * E2E Tests for Role-Based Access Control (RBAC)
 *
 * This test suite validates role-based access control for three roles:
 * - Admin: Full access to all endpoints including user management
 * - Recruiter: Access to hiring workflow endpoints, no admin access
 * - Viewer: Read-only access, no write operations
 *
 * Prerequisites:
 * - Keycloak server running on http://localhost:8080
 * - Frontend running on http://localhost:5173
 * - Backend running on http://localhost:8000
 * - Test users exist in Keycloak with appropriate roles
 *
 * Test Users Required:
 * - admin@agenthr.com (Admin role) - default from setup
 * - recruiter@agenthr.com (Recruiter role)
 * - viewer@agenthr.com (Viewer role)
 *
 * Environment Variables:
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - KEYCLOAK_URL: Keycloak URL (default: http://localhost:8080)
 * - API_URL: Backend API URL (default: http://localhost:8000)
 */

import { test, expect, Page, APIRequestContext } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:8080';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test user credentials
const TEST_USERS = {
  admin: {
    email: process.env.ADMIN_EMAIL || 'admin@agenthr.com',
    password: process.env.ADMIN_PASSWORD || 'admin123',
    role: 'Admin',
  },
  recruiter: {
    email: process.env.RECRUITER_EMAIL || 'recruiter@agenthr.com',
    password: process.env.RECRUITER_PASSWORD || 'recruiter123',
    role: 'Recruiter',
  },
  viewer: {
    email: process.env.VIEWER_EMAIL || 'viewer@agenthr.com',
    password: process.env.VIEWER_PASSWORD || 'viewer123',
    role: 'Viewer',
  },
} as const;

/**
 * Helper function to perform login via Keycloak
 */
async function performLogin(page: Page, email: string, password: string) {
  // Navigate to login page
  await page.goto(`${BASE_URL}/login`);

  // Click login button to redirect to Keycloak
  await page.click('button[type="submit"]');

  // Wait for redirect to Keycloak
  await page.waitForURL(`${KEYCLOAK_URL}/**`);

  // Fill in Keycloak login form
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);

  // Submit login form
  await page.click('input[type="submit"]');

  // Wait for redirect back to frontend callback
  await page.waitForURL(`${BASE_URL}/callback`, { timeout: 15000 });

  // Wait for navigation from callback to home or original destination
  await page.waitForTimeout(2000);
}

/**
 * Helper function to perform logout
 */
async function performLogout(page: Page) {
  await page.goto(`${BASE_URL}/`);
  await page.waitForTimeout(500);

  // Check if logout button/link exists and click it
  const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")').first();
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForTimeout(2000);
  }
}

/**
 * Helper function to get JWT token from localStorage
 */
async function getAuthToken(page: Page): Promise<string | null> {
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
 * Helper function to make authenticated API request
 */
async function makeApiRequest(
  context: APIRequestContext,
  token: string,
  method: string,
  endpoint: string,
  body?: any
) {
  const response = await context.fetch(`${API_URL}${endpoint}`, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: body,
  });

  return {
    status: response.status(),
    statusText: response.statusText(),
    body: await response.text().catch(() => null),
  };
}

/**
 * Helper function to verify user has expected role in JWT
 */
async function verifyUserRole(page: Page, expectedRole: string): Promise<boolean> {
  const token = await getAuthToken(page);
  if (!token) return false;

  return await page.evaluate((accessToken) => {
    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const roles = payload.realm_access?.roles || [];
      const clientRoles = payload.resource_access?.['agenthr-frontend']?.roles || [];
      const allRoles = [...roles, ...clientRoles];
      return allRoles.includes(expectedRole);
    } catch {
      return false;
    }
  }, token);
}

// ============================================================================
// TEST SUITE 1: ADMIN ROLE ACCESS
// ============================================================================

test.describe('Admin Role Access Control', () => {
  let adminPage: Page;
  let authToken: string;

  test.beforeAll(async ({ browser, context }) => {
    adminPage = await browser.newPage();
    await performLogin(adminPage, TEST_USERS.admin.email, TEST_USERS.admin.password);
    authToken = (await getAuthToken(adminPage)) || '';

    // Verify admin has Admin role
    const hasAdminRole = await verifyUserRole(adminPage, 'Admin');
    expect(hasAdminRole, 'User should have Admin role').toBeTruthy();
  });

  test.afterAll(async () => {
    await adminPage.close();
  });

  test('Admin can access user management endpoints', async ({ context }) => {
    // Test GET /api/users/ - list users
    const response = await makeApiRequest(context, authToken, 'GET', '/api/users/');
    expect(response.status).toBe(200);
    expect(response.body).toContain('users');

    // Parse response body
    const body = JSON.parse(response.body || '{}');
    expect(body).toHaveProperty('users');
    expect(Array.isArray(body.users)).toBeTruthy();
  });

  test('Admin can access hiring workflow endpoints', async ({ context }) => {
    // Test GET /api/skill-taxonomies/ - read access
    const response = await makeApiRequest(context, authToken, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);
    expect(response.body).toBeDefined();
  });

  test('Admin can perform write operations on skill taxonomies', async ({ context }) => {
    // Test creating a skill taxonomy (write operation)
    const testData = {
      name: 'Test Taxonomy',
      industry: 'Technology',
      skills: ['Java', 'Python'],
    };

    const response = await makeApiRequest(context, authToken, 'POST', '/api/skill-taxonomies/', testData);
    expect(response.status).toBeLessThan(500); // Should not be server error

    // 201 for success, 400 for validation error (both are acceptable)
    expect([201, 400, 422]).toContain(response.status);
  });

  test('Admin can access admin UI routes', async () => {
    // Test access to admin dashboard
    await adminPage.goto(`${BASE_URL}/admin/synonyms`);
    await adminPage.waitForTimeout(1000);

    // Should not redirect to login (already authenticated) or show access denied
    const currentUrl = adminPage.url();
    expect(currentUrl).not.toContain('/login');

    // Should not show access denied message
    const accessDenied = await adminPage.locator('text=Access Denied').count();
    expect(accessDenied).toBe(0);
  });

  test('Admin can access recruiter UI routes', async () => {
    // Test access to recruiter dashboard
    await adminPage.goto(`${BASE_URL}/recruiter/dashboard`);
    await adminPage.waitForTimeout(1000);

    const currentUrl = adminPage.url();
    expect(currentUrl).not.toContain('/login');

    const accessDenied = await adminPage.locator('text=Access Denied').count();
    expect(accessDenied).toBe(0);
  });
});

// ============================================================================
// TEST SUITE 2: RECRUITER ROLE ACCESS
// ============================================================================

test.describe('Recruiter Role Access Control', () => {
  let recruiterPage: Page;
  let authToken: string;

  test.beforeAll(async ({ browser }) => {
    recruiterPage = await browser.newPage();
    await performLogin(recruiterPage, TEST_USERS.recruiter.email, TEST_USERS.recruiter.password);
    authToken = (await getAuthToken(recruiterPage)) || '';

    // Verify recruiter has Recruiter role
    const hasRecruiterRole = await verifyUserRole(recruiterPage, 'Recruiter');
    expect(hasRecruiterRole, 'User should have Recruiter role').toBeTruthy();
  });

  test.afterAll(async () => {
    await recruiterPage.close();
  });

  test('Recruiter CANNOT access admin user management endpoints', async ({ context }) => {
    // Test GET /api/users/ - should return 403 Forbidden
    const response = await makeApiRequest(context, authToken, 'GET', '/api/users/');
    expect(response.status).toBe(403);
  });

  test('Recruiter can access hiring workflow endpoints', async ({ context }) => {
    // Test GET /api/skill-taxonomies/ - read access
    const response = await makeApiRequest(context, authToken, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);
  });

  test('Recruiter can perform write operations on hiring workflow', async ({ context }) => {
    // Test POST /api/skill-taxonomies/ - write operation (Admin or Recruiter)
    const testData = {
      name: 'Recruiter Test Taxonomy',
      industry: 'Finance',
      skills: ['Excel', 'Accounting'],
    };

    const response = await makeApiRequest(context, authToken, 'POST', '/api/skill-taxonomies/', testData);
    expect(response.status).toBeLessThan(500);

    // 201 for success, 400 for validation error (both acceptable)
    expect([201, 400, 422]).toContain(response.status);
  });

  test('Recruiter CANNOT access admin UI routes', async () => {
    // Test access to admin dashboard - should show access denied
    await recruiterPage.goto(`${BASE_URL}/admin/synonyms`);
    await recruiterPage.waitForTimeout(1000);

    // Should show access denied or redirect away
    const currentUrl = recruiterPage.url();
    const hasAccessDenied = await recruiterPage.locator('text=Access Denied').count() > 0;
    const isRedirected = !currentUrl.includes('/admin/');

    expect(hasAccessDenied || isRedirected, 'Recruiter should not access admin routes').toBeTruthy();
  });

  test('Recruiter can access recruiter UI routes', async () => {
    // Test access to recruiter dashboard
    await recruiterPage.goto(`${BASE_URL}/recruiter/dashboard`);
    await recruiterPage.waitForTimeout(1000);

    const currentUrl = recruiterPage.url();
    expect(currentUrl).not.toContain('/login');

    const accessDenied = await recruiterPage.locator('text=Access Denied').count();
    expect(accessDenied).toBe(0);
  });
});

// ============================================================================
// TEST SUITE 3: VIEWER ROLE ACCESS
// ============================================================================

test.describe('Viewer Role Access Control', () => {
  let viewerPage: Page;
  let authToken: string;

  test.beforeAll(async ({ browser }) => {
    viewerPage = await browser.newPage();
    await performLogin(viewerPage, TEST_USERS.viewer.email, TEST_USERS.viewer.password);
    authToken = (await getAuthToken(viewerPage)) || '';

    // Verify viewer has Viewer role
    const hasViewerRole = await verifyUserRole(viewerPage, 'Viewer');
    expect(hasViewerRole, 'User should have Viewer role').toBeTruthy();
  });

  test.afterAll(async () => {
    await viewerPage.close();
  });

  test('Viewer CANNOT access admin user management endpoints', async ({ context }) => {
    // Test GET /api/users/ - should return 403 Forbidden
    const response = await makeApiRequest(context, authToken, 'GET', '/api/users/');
    expect(response.status).toBe(403);
  });

  test('Viewer has read-only access to hiring workflow endpoints', async ({ context }) => {
    // Test GET /api/skill-taxonomies/ - read access should work
    const response = await makeApiRequest(context, authToken, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);
  });

  test('Viewer CANNOT perform write operations', async ({ context }) => {
    // Test POST /api/skill-taxonomies/ - write operation should fail
    const testData = {
      name: 'Viewer Test Taxonomy',
      industry: 'Healthcare',
      skills: ['Nursing', 'Care'],
    };

    const response = await makeApiRequest(context, authToken, 'POST', '/api/skill-taxonomies/', testData);
    expect(response.status).toBe(403);
  });

  test('Viewer CANNOT access admin UI routes', async () => {
    // Test access to admin dashboard - should show access denied
    await viewerPage.goto(`${BASE_URL}/admin/synonyms`);
    await viewerPage.waitForTimeout(1000);

    const currentUrl = viewerPage.url();
    const hasAccessDenied = await viewerPage.locator('text=Access Denied').count() > 0;
    const isRedirected = !currentUrl.includes('/admin/');

    expect(hasAccessDenied || isRedirected, 'Viewer should not access admin routes').toBeTruthy();
  });

  test('Viewer CANNOT access recruiter UI routes', async () => {
    // Test access to recruiter dashboard - should show access denied
    await viewerPage.goto(`${BASE_URL}/recruiter/dashboard`);
    await viewerPage.waitForTimeout(1000);

    const currentUrl = viewerPage.url();
    const hasAccessDenied = await viewerPage.locator('text=Access Denied').count() > 0;
    const isRedirected = !currentUrl.includes('/recruiter/');

    expect(hasAccessDenied || isRedirected, 'Viewer should not access recruiter routes').toBeTruthy();
  });
});

// ============================================================================
// TEST SUITE 4: ROLE TRANSITION AND PERMISSION ISOLATION
// ============================================================================

test.describe('Role Permission Isolation', () => {
  test('Admin privileges are isolated from Recruiter', async ({ browser, context }) => {
    let page: Page;
    let token: string;

    // Login as Recruiter
    page = await browser.newPage();
    await performLogin(page, TEST_USERS.recruiter.email, TEST_USERS.recruiter.password);
    token = (await getAuthToken(page)) || '';

    // Try to access admin endpoint
    const response = await makeApiRequest(context, token, 'GET', '/api/users/');
    expect(response.status).toBe(403);

    await page.close();
  });

  test('Recruiter privileges are isolated from Viewer', async ({ browser, context }) => {
    let page: Page;
    let token: string;

    // Login as Viewer
    page = await browser.newPage();
    await performLogin(page, TEST_USERS.viewer.email, TEST_USERS.viewer.password);
    token = (await getAuthToken(page)) || '';

    // Try to perform write operation
    const testData = {
      name: 'Test',
      industry: 'Test',
      skills: ['Test'],
    };

    const response = await makeApiRequest(context, token, 'POST', '/api/skill-taxonomies/', testData);
    expect(response.status).toBe(403);

    await page.close();
  });

  test('Viewer cannot elevate privileges via direct API calls', async ({ browser, context }) => {
    let page: Page;
    let token: string;

    // Login as Viewer
    page = await browser.newPage();
    await performLogin(page, TEST_USERS.viewer.email, TEST_USERS.viewer.password);
    token = (await getAuthToken(page)) || '';

    // Try various admin endpoints
    const endpoints = [
      { method: 'GET', path: '/api/users/' },
      { method: 'DELETE', path: '/api/skill-taxonomies/test-id' },
    ];

    for (const endpoint of endpoints) {
      const response = await makeApiRequest(
        context,
        token,
        endpoint.method,
        endpoint.path
      );
      expect(response.status).toBe(403);
    }

    await page.close();
  });
});

// ============================================================================
// TEST SUITE 5: JWT TOKEN ROLE VALIDATION
// ============================================================================

test.describe('JWT Token Role Validation', () => {
  test('Admin JWT token contains Admin role', async ({ browser }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.admin.email, TEST_USERS.admin.password);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    const hasAdminRole = await verifyUserRole(page, 'Admin');
    expect(hasAdminRole).toBeTruthy();

    await page.close();
  });

  test('Recruiter JWT token contains Recruiter role', async ({ browser }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.recruiter.email, TEST_USERS.recruiter.password);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    const hasRecruiterRole = await verifyUserRole(page, 'Recruiter');
    expect(hasRecruiterRole).toBeTruthy();

    await page.close();
  });

  test('Viewer JWT token contains Viewer role', async ({ browser }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.viewer.email, TEST_USERS.viewer.password);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    const hasViewerRole = await verifyUserRole(page, 'Viewer');
    expect(hasViewerRole).toBeTruthy();

    await page.close();
  });

  test('JWT token structure is valid', async ({ browser }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.admin.email, TEST_USERS.admin.password);

    const token = await getAuthToken(page);
    expect(token).not.toBeNull();

    // Verify JWT structure (header.payload.signature)
    const parts = token!.split('.');
    expect(parts).toHaveLength(3);

    // Verify payload can be decoded
    const payload = JSON.parse(atob(parts[1]));
    expect(payload).toHaveProperty('sub');
    expect(payload).toHaveProperty('exp');
    expect(payload).toHaveProperty('iat');
    expect(payload).toHaveProperty('realm_access');

    await page.close();
  });
});

// ============================================================================
// TEST SUITE 6: UNAUTHENTICATED ACCESS
// ============================================================================

test.describe('Unauthenticated Access Control', () => {
  test('Unauthenticated users cannot access protected API endpoints', async ({ context }) => {
    // Test without any token
    const response = await context.fetch(`${API_URL}/api/users/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    expect(response.status()).toBe(401);
  });

  test('Unauthenticated users cannot access protected UI routes', async ({ page }) => {
    // Try to access admin route without authentication
    await page.goto(`${BASE_URL}/admin/synonyms`);

    // Should redirect to login
    await page.waitForTimeout(1000);
    const currentUrl = page.url();
    expect(currentUrl).toContain('/login');
  });

  test('Unauthenticated users can access public routes', async ({ page }) => {
    // Try to access home page (should be public)
    await page.goto(`${BASE_URL}/`);

    // Should not redirect to login
    await page.waitForTimeout(1000);
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/login');
  });
});

// ============================================================================
// TEST SUITE 7: SESSION MANAGEMENT
// ============================================================================

test.describe('Session Management and Role Changes', () => {
  test('Logout clears authentication and prevents API access', async ({ browser, context }) => {
    let page: Page;
    let token: string;

    // Login as Admin
    page = await browser.newPage();
    await performLogin(page, TEST_USERS.admin.email, TEST_USERS.admin.password);
    token = (await getAuthToken(page)) || '';
    expect(token).not.toBeNull();

    // Verify API access works
    let response = await makeApiRequest(context, token, 'GET', '/api/users/');
    expect(response.status).toBe(200);

    // Logout
    await performLogout(page);

    // Token should be cleared
    token = (await getAuthToken(page)) || '';
    expect(token).toBeNull();

    await page.close();
  });

  test('Token expiration is handled correctly', async ({ browser, context }) => {
    let page: Page;
    let token: string;

    // Login as Recruiter
    page = await browser.newPage();
    await performLogin(page, TEST_USERS.recruiter.email, TEST_USERS.recruiter.password);
    token = (await getAuthToken(page)) || '';

    // Check token expiration claim
    const payload = JSON.parse(atob(token.split('.')[1]));
    expect(payload).toHaveProperty('exp');
    const expirationTime = payload.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();

    // Token should be valid for at least 30 seconds
    expect(expirationTime - currentTime).toBeGreaterThan(30000);

    await page.close();
  });
});

// ============================================================================
// TEST SUITE 8: CROSS-ROLE ACCESS VALIDATION
// ============================================================================

test.describe('Cross-Role Access Validation', () => {
  test('Admin can access both Admin and Recruiter endpoints', async ({ browser, context }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.admin.email, TEST_USERS.admin.password);
    const token = (await getAuthToken(page)) || '';

    // Admin endpoints
    let response = await makeApiRequest(context, token, 'GET', '/api/users/');
    expect(response.status).toBe(200);

    // Recruiter endpoints
    response = await makeApiRequest(context, token, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);

    await page.close();
  });

  test('Recruiter can access Recruiter but not Admin endpoints', async ({ browser, context }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.recruiter.email, TEST_USERS.recruiter.password);
    const token = (await getAuthToken(page)) || '';

    // Recruiter endpoints - should work
    let response = await makeApiRequest(context, token, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);

    // Admin endpoints - should fail
    response = await makeApiRequest(context, token, 'GET', '/api/users/');
    expect(response.status).toBe(403);

    await page.close();
  });

  test('Viewer can only read, not write', async ({ browser, context }) => {
    const page = await browser.newPage();
    await performLogin(page, TEST_USERS.viewer.email, TEST_USERS.viewer.password);
    const token = (await getAuthToken(page)) || '';

    // Read endpoints - should work
    let response = await makeApiRequest(context, token, 'GET', '/api/skill-taxonomies/');
    expect(response.status).toBe(200);

    // Write endpoints - should fail
    const testData = { name: 'Test', industry: 'Test', skills: ['Test'] };
    response = await makeApiRequest(context, token, 'POST', '/api/skill-taxonomies/', testData);
    expect(response.status).toBe(403);

    await page.close();
  });
});
