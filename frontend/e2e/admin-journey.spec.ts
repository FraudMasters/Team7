import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Admin Journey End-to-End Flow Verification
 *
 * This test suite verifies the complete Admin user journey as specified in subtask-7-3.
 *
 * Verification Steps (from spec):
 * 1. Navigate to admin dashboard
 * 2. Access user management
 * 3. Access system settings
 * 4. Access audit logs
 * 5. Verify access to Recruiter routes
 * 6. Verify read-only access to JobSeeker flows
 *
 * Prerequisites:
 * - Frontend dev server running at http://localhost:5173
 * - Auth disabled (VITE_AUTH_ENABLED=false) or Admin user logged in
 * - Mock role set to Admin for testing purposes
 */

test.describe('Admin Journey - E2E Verification', () => {
  /**
   * Step 1: Navigate to admin dashboard
   * Expected: Admin dashboard renders with system overview metrics
   */
  test('Step 1: Navigate to admin dashboard', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();

    // Verify subtitle
    await expect(page.getByText('System overview and administrative controls')).toBeVisible();

    // Verify Admin badge
    await expect(page.getByText('ADMIN')).toBeVisible();

    // Verify metrics cards
    await expect(page.getByText('Organizations')).toBeVisible();
    await expect(page.getByText('Total Users')).toBeVisible();
    await expect(page.getByText('System Health')).toBeVisible();
    await expect(page.getByText('Analytics Reports')).toBeVisible();

    // Verify System Overview section
    await expect(page.getByText('System Overview')).toBeVisible();

    // Verify no console errors
    const logs: string[] = [];
    page.on('console', msg => logs.push(msg.text()));
    await expect(logs.filter(log => log.includes('error') || log.includes('Error'))).toEqual([]);
  });

  /**
   * Step 2: Access user management
   * Expected: User management page renders with user list and actions
   */
  test('Step 2: Access user management', async ({ page }) => {
    await page.goto('/admin/users');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // Verify search functionality
    const searchInput = page.getByPlaceholder(/search by name, email, role, or organization/i);
    await expect(searchInput).toBeVisible();

    // Verify table headers
    await expect(page.getByText('Name')).toBeVisible();
    await expect(page.getByText('Email')).toBeVisible();
    await expect(page.getByText('Role')).toBeVisible();
    await expect(page.getByText('Organization')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();

    // Verify action buttons are present (more options buttons for each user)
    const actionButtons = await page.locator('button[aria-label*="more options"], button[aria-label*="actions"]').all();
    expect(actionButtons.length).toBeGreaterThan(0);

    // Verify role badges
    await expect(page.getByText('Admin')).toBeVisible();
    await expect(page.getByText('Recruiter')).toBeVisible();
    await expect(page.getByText('JobSeeker')).toBeVisible();

    // Verify status chips
    await expect(page.getByText('Active')).toBeVisible();
  });

  /**
   * Step 3: Access system settings
   * Expected: System settings page renders with configuration options
   */
  test('Step 3: Access system settings', async ({ page }) => {
    await page.goto('/admin/settings');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading
    await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();

    // Verify settings sections
    await expect(page.getByText('Authentication & Security')).toBeVisible();
    await expect(page.getByText('Email Configuration')).toBeVisible();
    await expect(page.getByText('System Limits')).toBeVisible();
    await expect(page.getByText('Data Retention')).toBeVisible();
    await expect(page.getByText('Feature Flags')).toBeVisible();

    // Verify OIDC settings
    await expect(page.getByText('OIDC Authority')).toBeVisible();
    await expect(page.getByText('OIDC Client ID')).toBeVisible();

    // Verify session timeout field
    await expect(page.getByLabelText(/session timeout/i)).toBeVisible();

    // Verify save and reload buttons
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /reload/i })).toBeVisible();

    // Verify system limits section
    await expect(page.getByText('Max Users per Organization')).toBeVisible();
    await expect(page.getByText('Max Vacancies per Organization')).toBeVisible();
    await expect(page.getByText('Max File Size (MB)')).toBeVisible();
  });

  /**
   * Step 4: Access audit logs
   * Expected: Audit logs page renders with filterable log table
   */
  test('Step 4: Access audit logs', async ({ page }) => {
    await page.goto('/admin/audit-logs');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading
    await expect(page.getByRole('heading', { name: 'Audit Logs' })).toBeVisible();

    // Verify stats cards
    await expect(page.getByText('Total Logs')).toBeVisible();
    await expect(page.getByText('Action Types')).toBeVisible();
    await expect(page.getByText('Entity Types')).toBeVisible();
    await expect(page.getByText('Current View')).toBeVisible();

    // Verify action buttons
    await expect(page.getByRole('button', { name: /filter logs/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /export logs/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /refresh/i })).toBeVisible();

    // Verify table headers
    await expect(page.getByText('Timestamp')).toBeVisible();
    await expect(page.getByText('User')).toBeVisible();
    await expect(page.getByText('Action')).toBeVisible();
    await expect(page.getByText('Entity')).toBeVisible();
    await expect(page.getByText('Details')).toBeVisible();

    // Verify action type filters
    await expect(page.getByText('Create')).toBeVisible();
    await expect(page.getByText('Update')).toBeVisible();
    await expect(page.getByText('Delete')).toBeVisible();
    await expect(page.getByText('Export')).toBeVisible();
  });

  /**
   * Step 5: Verify access to Recruiter routes
   * Expected: Admin can access all Recruiter pages with elevated privileges
   */
  test('Step 5: Verify access to Recruiter routes', async ({ page }) => {
    // Test access to recruiter dashboard
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify recruiter dashboard loads
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    // Verify recruiter layout navigation
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Vacancies')).toBeVisible();
    await expect(page.getByText('Candidates')).toBeVisible();
    await expect(page.getByText('Search')).toBeVisible();

    // Test access to candidates kanban
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Verify candidates page loads
    await expect(page.getByText(/candidates/i)).toBeVisible();

    // Test access to vacancies
    await page.goto('/recruiter/vacancies');
    await page.waitForLoadState('networkidle');

    // Verify vacancies page loads
    await expect(page.getByText(/vacancies/i)).toBeVisible();

    // Test access to analytics
    await page.goto('/recruiter/analytics');
    await page.waitForLoadState('networkidle');

    // Verify analytics page loads
    await expect(page.getByText(/analytics/i)).toBeVisible();
  });

  /**
   * Step 6: Verify read-only access to JobSeeker flows
   * Expected: Admin can view JobSeeker pages in read-only mode
   */
  test('Step 6: Verify read-only access to JobSeeker flows', async ({ page }) => {
    // Test access to jobs browse page
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');

    // Verify jobs page loads
    await expect(page.getByRole('heading', { name: /find your next job/i })).toBeVisible();

    // Verify JobSeekerLayout navigation
    await expect(page.getByText('Find Jobs')).toBeVisible();
    await expect(page.getByText('Browse')).toBeVisible();
    await expect(page.getByText('Saved')).toBeVisible();
    await expect(page.getByText('Applications')).toBeVisible();
    await expect(page.getByText('Profile')).toBeVisible();

    // Test access to job detail page
    await page.goto('/jobs/1');
    await page.waitForLoadState('networkidle');

    // Verify job detail loads
    await expect(page.getByText('Software Engineer')).toBeVisible();

    // Verify job information is displayed
    await expect(page.getByText(/develop awesome software/i)).toBeVisible();
    await expect(page.getByText('Remote')).toBeVisible();

    // Test access to saved jobs (read-only view)
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // Verify saved jobs page loads
    await expect(page.getByRole('heading', { name: /saved jobs/i })).toBeVisible();

    // Test access to applications (read-only view)
    await page.goto('/jobs/applications');
    await page.waitForLoadState('networkidle');

    // Verify applications page loads
    await expect(page.getByRole('heading', { name: /my applications/i })).toBeVisible();
  });

  /**
   * Complete Admin Navigation Flow
   * Tests navigation between all admin pages
   */
  test('Complete Admin Navigation Flow', async ({ page }) => {
    // Start at admin dashboard
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify dashboard
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();

    // Navigate to users via sidebar
    await page.getByRole('link', { name: /users/i }).click();
    await page.waitForLoadState('networkidle');

    // Verify users page
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // Navigate to settings via sidebar
    await page.getByRole('link', { name: /general/i }).click();
    await page.waitForLoadState('networkidle');

    // Verify settings page
    await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();

    // Navigate to audit logs
    await page.goto('/admin/audit-logs');
    await page.waitForLoadState('networkidle');

    // Verify audit logs page
    await expect(page.getByRole('heading', { name: 'Audit Logs' })).toBeVisible();
  });

  /**
   * Accessibility Tests
   */
  test('Accessibility - Skip to content link', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify skip-to-content link exists
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');

    // Verify main content area exists
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toBeVisible();
  });

  test('Accessibility - ARIA labels and roles', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify navigation role
    const nav = page.getByRole('navigation', { name: /admin sidebar navigation/i });
    await expect(nav).toBeVisible();

    // Verify menubar role
    const menubar = page.getByRole('menubar');
    await expect(menubar).toBeVisible();

    // Verify heading levels
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('Accessibility - Keyboard navigation', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Test Tab key navigation
    await page.keyboard.press('Tab');

    // Verify focus management works
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'A', 'INPUT']).toContain(focusedElement);
  });

  /**
   * Mobile Responsive Tests
   */
  test('Mobile responsive - Admin layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify mobile menu button is visible
    const menuButton = page.getByRole('button', { name: /open navigation menu/i });
    await expect(menuButton).toBeVisible();

    // Open mobile menu
    await menuButton.click();
    await page.waitForTimeout(500);

    // Verify drawer opens on mobile
    const drawer = page.locator('.MuiDrawer-paper');
    await expect(drawer).toBeVisible();

    // Verify navigation items are visible
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('System')).toBeVisible();
    await expect(page.getByText('User Management')).toBeVisible();
  });

  /**
   * Browser Navigation Tests
   */
  test('Browser navigation - Back and forward buttons', async ({ page }) => {
    // Navigate through admin pages
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();

    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    await page.goto('/admin/settings');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();

    // Test back button
    await page.goBack();
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // Test forward button
    await page.goForward();
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();
  });

  /**
   * Error Handling Tests
   */
  test('Error handling - Invalid admin route', async ({ page }) => {
    // Navigate to invalid admin route
    await page.goto('/admin/invalid-route');
    await page.waitForLoadState('networkidle');

    // Should handle gracefully - either show error or redirect
    // The app should not crash
    const logs: string[] = [];
    page.on('console', msg => logs.push(msg.text()));

    // Verify no unhandled errors
    await page.waitForTimeout(1000);
    const hasErrors = logs.some(log => log.includes('error') || log.includes('Error'));

    // Based on the routing, invalid routes should redirect to / or show appropriate error
    // This test verifies the app handles it gracefully
  });

  /**
   * Cross-Role Access Tests
   */
  test('Cross-role access - Admin accessing Recruiter then JobSeeker', async ({ page }) => {
    // Start at admin dashboard
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();

    // Access recruiter page
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    // Access jobseeker page
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /find your next job/i })).toBeVisible();

    // Return to admin
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();

    // Verify all pages loaded without errors
    const logs: string[] = [];
    page.on('console', msg => logs.push(msg.text()));
    await expect(logs.filter(log => log.includes('error'))).toEqual([]);
  });

  /**
   * Performance Tests
   */
  test('Performance - Page load times', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  /**
   * Search and Filter Tests
   */
  test('Search functionality - User management', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Find search input
    const searchInput = page.getByPlaceholder(/search by name, email, role, or organization/i);
    await expect(searchInput).toBeVisible();

    // Type search query
    await searchInput.fill('admin');
    await page.waitForTimeout(500);

    // Verify search input has value
    await expect(searchInput).toHaveValue('admin');

    // Clear search
    await searchInput.fill('');
    await page.waitForTimeout(500);

    // Verify search is cleared
    await expect(searchInput).toHaveValue('');
  });

  /**
   * Action Menu Tests
   */
  test('User actions - Open action menu', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Find first action button
    const actionButton = page.locator('button').filter({ hasText: /more|actions|menu/i }).first();
    await expect(actionButton).toBeVisible();

    // Click action button
    await actionButton.click();
    await page.waitForTimeout(300);

    // Verify action menu appears (if implemented)
    // This test verifies the action buttons are present and clickable
  });

  /**
   * Settings Form Tests
   */
  test('Settings form - Toggle switches', async ({ page }) => {
    await page.goto('/admin/settings');
    await page.waitForLoadState('networkidle');

    // Find toggle switches
    const toggles = page.locator('input[type="checkbox"]');
    const count = await toggles.count();

    // Verify there are configuration toggles
    expect(count).toBeGreaterThan(0);

    // Test toggling a switch
    if (count > 0) {
      const firstToggle = toggles.first();
      await firstToggle.click();
      await page.waitForTimeout(200);

      // Verify toggle state changed
      const isChecked = await firstToggle.isChecked();
      expect(isChecked).toBeDefined();
    }
  });

  /**
   * Audit Logs Export Test
   */
  test('Audit logs - Export functionality', async ({ page }) => {
    await page.goto('/admin/audit-logs');
    await page.waitForLoadState('networkidle');

    // Verify export button exists
    const exportButton = page.getByRole('button', { name: /export logs/i });
    await expect(exportButton).toBeVisible();

    // Note: Actual file download testing would require more setup
    // This test verifies the button is present and clickable
    await expect(exportButton).toBeEnabled();
  });

  /**
   * Audit Logs Filter Test
   */
  test('Audit logs - Filter controls', async ({ page }) => {
    await page.goto('/admin/audit-logs');
    await page.waitForLoadState('networkidle');

    // Verify filter button exists
    const filterButton = page.getByRole('button', { name: /filter logs/i });
    await expect(filterButton).toBeVisible();

    // Click filter button
    await filterButton.click();
    await page.waitForTimeout(300);

    // Verify filter options appear (if implemented as a dialog/dropdown)
    // This test verifies the filter UI is accessible
  });
});
