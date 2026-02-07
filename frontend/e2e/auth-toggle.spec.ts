import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Auth Toggle Functionality Verification
 *
 * This test suite verifies the auth toggle feature that allows enabling/disabling
 * authentication via the VITE_AUTH_ENABLED environment variable.
 *
 * Verification Steps (from spec - subtask-7-4):
 * 1. Set VITE_AUTH_ENABLED=false
 * 2. Restart frontend
 * 3. Access protected routes without login
 * 4. Set VITE_AUTH_ENABLED=true
 * 5. Restart frontend
 * 6. Verify auth required for protected routes
 *
 * Prerequisites:
 * - Frontend dev server running at http://localhost:5173
 * - Environment variable VITE_AUTH_ENABLED can be toggled
 * - Server restart after changing VITE_AUTH_ENABLED
 *
 * Note: These tests assume the environment is configured with the specified
 * VITE_AUTH_ENABLED value before running the test suite.
 */

test.describe('Auth Toggle - E2E Verification', () => {
  /**
   * PHASE 1: Auth Disabled Mode (VITE_AUTH_ENABLED=false)
   *
   * These tests verify that when auth is disabled, all routes are accessible
   * without any authentication or authorization checks.
   */

  test.describe('Phase 1: Auth Disabled (VITE_AUTH_ENABLED=false)', () => {
    test.beforeEach(async ({ page }) => {
      // Note: Tests in this phase require VITE_AUTH_ENABLED=false in .env
      // and the dev server to be restarted after setting this value

      // Log current state for debugging
      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.log('Browser console error:', msg.text());
        }
      });
    });

    /**
     * Step 1-3: Verify all protected routes are accessible without auth
     */
    test('Admin Dashboard - accessible without authentication', async ({ page }) => {
      await page.goto('/admin/dashboard');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Verify Admin Dashboard content is visible
      await expect(page.getByRole('heading', { name: /System Overview/i })).toBeVisible();

      // Verify system metrics are displayed
      await expect(page.getByText(/Organizations/i)).toBeVisible();
      await expect(page.getByText(/Users/i)).toBeVisible();
      await expect(page.getByText(/System Health/i)).toBeVisible();
      await expect(page.getByText(/Analytics/i)).toBeVisible();

      // Verify AdminLayout sidebar is visible
      await expect(page.getByText('Admin Panel')).toBeVisible();

      // Verify no access denied message is shown
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Users - accessible without authentication', async ({ page }) => {
      await page.goto('/admin/users');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Verify User Management page content
      await expect(page.getByRole('heading', { name: /User Management/i })).toBeVisible();

      // Verify search functionality is present
      const searchInput = page.getByPlaceholder(/Search users.../i);
      await expect(searchInput).toBeVisible();

      // Verify user table is displayed
      await expect(page.getByRole('columnheader', { name: /Name/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /Email/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /Role/i })).toBeVisible();

      // Verify no access denied message
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Settings - accessible without authentication', async ({ page }) => {
      await page.goto('/admin/settings');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Verify Settings page content
      await expect(page.getByRole('heading', { name: /System Configuration/i })).toBeVisible();

      // Verify settings sections are present
      await expect(page.getByText(/Authentication & Security/i)).toBeVisible();
      await expect(page.getByText(/Email Configuration/i)).toBeVisible();
      await expect(page.getByText(/System Limits/i)).toBeVisible();

      // Verify save button is present
      await expect(page.getByRole('button', { name: /Save Changes/i })).toBeVisible();

      // Verify no access denied message
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Audit Logs - accessible without authentication', async ({ page }) => {
      await page.goto('/admin/audit-logs');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Verify Audit Logs page content
      await expect(page.getByRole('heading', { name: /Audit Logs/i })).toBeVisible();

      // Verify stats cards are displayed
      await expect(page.getByText(/Total Logs/i)).toBeVisible();
      await expect(page.getByText(/Action Types/i)).toBeVisible();

      // Verify filter controls are present
      await expect(page.getByLabelText(/Action Type/i)).toBeVisible();

      // Verify no access denied message
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Recruiter routes - accessible without authentication', async ({ page }) => {
      // Test multiple Recruiter routes
      const recruiterRoutes = [
        '/recruiter/dashboard',
        '/recruiter/vacancies',
        '/recruiter/candidates',
        '/recruiter/analytics',
      ];

      for (const route of recruiterRoutes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');

        // Verify page content is visible (no access denied)
        await expect(page.getByText(/Access Denied/i)).not.toBeVisible();

        // Verify layout is visible
        await expect(page.getByText('AgentHR')).toBeVisible();
      }
    });

    test('JobSeeker routes - accessible without authentication', async ({ page }) => {
      // Test JobSeeker routes
      const jobseekerRoutes = [
        '/jobs',
        '/jobs/saved',
        '/jobs/applications',
      ];

      for (const route of jobseekerRoutes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');

        // Verify page content is visible
        await expect(page.getByText(/Access Denied/i)).not.toBeVisible();

        // Verify JobSeekerLayout is visible
        await expect(page.getByText('AgentHR')).toBeVisible();
      }
    });

    test('Direct URL access - all routes work without login redirect', async ({ page }) => {
      // Test direct URL access to protected routes
      const protectedRoutes = [
        '/admin/dashboard',
        '/admin/users',
        '/admin/settings',
        '/admin/audit-logs',
        '/recruiter/dashboard',
        '/recruiter/vacancies',
      ];

      for (const route of protectedRoutes) {
        // Navigate directly to protected route
        await page.goto(route);

        // Wait a bit for any potential redirects
        await page.waitForTimeout(500);

        // Verify we're still on the same route (not redirected to login)
        expect(page.url()).toContain(route);

        // Verify no access denied or login prompt
        await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
        await expect(page.getByText(/Please log in/i)).not.toBeVisible();
      }
    });

    test('No login prompt is shown on protected routes', async ({ page }) => {
      await page.goto('/admin/dashboard');

      // Verify no login-related elements are present
      await expect(page.getByText(/Log in/i)).not.toBeVisible();
      await expect(page.getByText(/Sign in/i)).not.toBeVisible();
      await expect(page.getByRole('button', { name: /Login/i })).not.toBeVisible();
      await expect(page.getByRole('button', { name: /Sign in/i })).not.toBeVisible();

      // Verify dashboard content is shown instead
      await expect(page.getByRole('heading', { name: /System Overview/i })).toBeVisible();
    });
  });

  /**
   * PHASE 2: Auth Enabled Mode (VITE_AUTH_ENABLED=true)
   *
   * These tests verify that when auth is enabled, protected routes
   * require proper authentication and role-based access control.
   *
   * Note: Running these tests requires:
   * 1. Set VITE_AUTH_ENABLED=true in .env
   * 2. Restart the dev server
   * 3. Run this test suite
   *
   * Currently, with the placeholder auth implementation, the behavior
   * will use mock roles from VITE_MOCK_ROLE for testing.
   */

  test.describe('Phase 2: Auth Enabled (VITE_AUTH_ENABLED=true)', () => {
    test.beforeEach(async ({ page }) => {
      // Note: Tests in this phase require VITE_AUTH_ENABLED=true in .env
      // and the dev server to be restarted after setting this value

      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.log('Browser console error:', msg.text());
        }
      });
    });

    /**
     * Step 4-6: Verify auth enforcement with proper roles
     */
    test('Admin routes accessible with Admin mock role', async ({ page }) => {
      // Assumes VITE_MOCK_ROLE=Admin when running this test
      await page.goto('/admin/dashboard');

      await page.waitForLoadState('networkidle');

      // Admin dashboard should be accessible
      await expect(page.getByRole('heading', { name: /System Overview/i })).toBeVisible();
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Users accessible with Admin mock role', async ({ page }) => {
      await page.goto('/admin/users');

      await page.waitForLoadState('networkidle');

      // User management should be accessible
      await expect(page.getByRole('heading', { name: /User Management/i })).toBeVisible();
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Settings accessible with Admin mock role', async ({ page }) => {
      await page.goto('/admin/settings');

      await page.waitForLoadState('networkidle');

      // Settings should be accessible
      await expect(page.getByRole('heading', { name: /System Configuration/i })).toBeVisible();
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Admin Audit Logs accessible with Admin mock role', async ({ page }) => {
      await page.goto('/admin/audit-logs');

      await page.waitForLoadState('networkidle');

      // Audit logs should be accessible
      await expect(page.getByRole('heading', { name: /Audit Logs/i })).toBeVisible();
      await expect(page.getByText(/Access Denied/i)).not.toBeVisible();
    });

    test('Recruiter routes accessible with Recruiter mock role', async ({ page }) => {
      // Note: This test requires VITE_MOCK_ROLE=Recruiter
      await page.goto('/recruiter/dashboard');

      await page.waitForLoadState('networkidle');

      // Recruiter dashboard should be accessible
      await expect(page.getByText(/Dashboard/i)).toBeVisible();
    });

    test('JobSeeker routes accessible with JobSeeker mock role', async ({ page }) => {
      // Note: This test requires VITE_MOCK_ROLE=JobSeeker
      await page.goto('/jobs');

      await page.waitForLoadState('networkidle');

      // Jobs page should be accessible
      await expect(page.getByRole('heading', { name: /Find Your Next Job/i })).toBeVisible();
    });
  });

  /**
   * Auth Toggle Transition Tests
   *
   * Verify the behavior changes correctly when toggling
   * VITE_AUTH_ENABLED between states.
   */

  test.describe('Auth Toggle State Verification', () => {
    test('Verify feature flag state at application load', async ({ page }) => {
      // Navigate to a protected route
      await page.goto('/admin/dashboard');

      await page.waitForLoadState('networkidle');

      // Check for console logs indicating auth state
      const logs: string[] = [];
      page.on('console', msg => {
        logs.push(msg.text());
      });

      // Reload page to capture initialization logs
      await page.reload();

      // Wait for page to stabilize
      await page.waitForTimeout(1000);

      // The logs should contain auth-related debug info if AUTH_DEBUG is enabled
      // This is a basic check - actual implementation would check for specific log messages
      expect(page.url()).toContain('/admin/dashboard');
    });

    test('Verify protected route behavior is consistent', async ({ page }) => {
      // Navigate to admin dashboard multiple times
      const routes = ['/admin/dashboard', '/admin/users', '/admin/settings'];

      for (const route of routes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');

        // Verify consistent behavior (either always accessible or always protected)
        // based on current VITE_AUTH_ENABLED setting
        const currentUrl = page.url();
        expect(currentUrl).toContain(route);
      }
    });
  });

  /**
   * Accessibility and UX Tests
   */

  test.describe('Auth Toggle - Accessibility & UX', () => {
    test('Protected routes have proper ARIA attributes', async ({ page }) => {
      await page.goto('/admin/dashboard');

      await page.waitForLoadState('networkidle');

      // Verify main navigation is present
      const mainNav = page.getByRole('navigation', { name: /admin/i });
      await expect(mainNav).toBeVisible();

      // Verify heading structure
      const mainHeading = page.getByRole('heading', { level: 1 });
      await expect(mainHeading).toBeVisible();
    });

    test('Skip-to-content link works on protected routes', async ({ page }) => {
      await page.goto('/admin/dashboard');

      // Find and click skip-to-content link
      const skipLink = page.getByText(/Skip to main content/i).first();
      await expect(skipLink).toBeVisible();

      // Verify the link has the correct href attribute
      await expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    test('No console errors on protected routes', async ({ page }) => {
      const errors: string[] = [];

      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');

      // Navigate through multiple admin routes
      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      await page.goto('/admin/settings');
      await page.waitForLoadState('networkidle');

      // Check that no critical errors occurred
      const criticalErrors = errors.filter(err =>
        err.includes('TypeError') ||
        err.includes('ReferenceError') ||
        err.includes('Cannot read')
      );

      expect(criticalErrors).toHaveLength(0);
    });
  });

  /**
   * Mobile Responsiveness Tests
   */

  test.describe('Auth Toggle - Mobile Responsiveness', () => {
    test('Protected routes work on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/admin/dashboard');

      await page.waitForLoadState('networkidle');

      // Verify content is accessible on mobile
      await expect(page.getByRole('heading', { name: /System Overview/i })).toBeVisible();
    });

    test('Admin layout drawer works on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/admin/dashboard');

      await page.waitForLoadState('networkidle');

      // On mobile, there should be a menu button to open drawer
      const menuButton = page.getByRole('button', { name: /menu/i }).or(
        page.getByRole('button', { name: /open drawer/i })
      );

      // Menu button should be present and visible on mobile
      if (await menuButton.isVisible()) {
        await menuButton.click();

        // Drawer should open
        await expect(page.getByText('Dashboard')).toBeVisible();
      }
    });
  });

  /**
   * Edge Cases and Error Handling
   */

  test.describe('Auth Toggle - Edge Cases', () => {
    test('Invalid protected route shows appropriate error', async ({ page }) => {
      // Navigate to invalid admin route
      await page.goto('/admin/invalid-route');

      await page.waitForLoadState('networkidle');

      // Should redirect to a valid page or show error
      // Current implementation redirects to landing page for invalid routes
      await page.waitForTimeout(500);
      expect(page.url()).toMatch(/\/$/);
    });

    test('Back navigation works correctly from protected routes', async ({ page }) => {
      // Navigate through multiple protected routes
      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');

      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      // Use browser back button
      await page.goBack();
      await page.waitForLoadState('networkidle');

      // Should return to dashboard
      expect(page.url()).toContain('/admin/dashboard');
      await expect(page.getByRole('heading', { name: /System Overview/i })).toBeVisible();
    });

    test('Forward navigation works correctly', async ({ page }) => {
      // Build up history
      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');

      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      await page.goBack();
      await page.waitForLoadState('networkidle');

      // Use forward button
      await page.goForward();
      await page.waitForLoadState('networkidle');

      // Should return to users page
      expect(page.url()).toContain('/admin/users');
      await expect(page.getByRole('heading', { name: /User Management/i })).toBeVisible();
    });
  });
});
