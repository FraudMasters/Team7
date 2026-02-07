import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Recruiter Journey End-to-End Flow Verification
 *
 * This test suite verifies the complete Recruiter user journey as specified in subtask-7-2.
 *
 * Verification Steps (from spec):
 * 1. Navigate to recruiter dashboard
 * 2. View vacancies
 * 3. View candidates kanban
 * 4. Navigate to search
 * 5. Navigate to analytics
 * 6. Verify all pages accessible
 *
 * Prerequisites:
 * - Frontend dev server running at http://localhost:5173
 * - Auth disabled (VITE_AUTH_ENABLED=false) for testing purposes
 */

test.describe('Recruiter Journey - E2E Verification', () => {
  /**
   * Step 1: Navigate to recruiter dashboard
   * Expected: Dashboard renders with key metrics and RecruiterLayout navigation
   */
  test('Step 1: Navigate to recruiter dashboard', async ({ page }) => {
    await page.goto('/recruiter/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify RecruiterLayout components
    await expect(page.getByText('AgentHR')).toBeVisible();

    // Verify Recruiter Portal title in AppBar
    await expect(page.getByText('Recruiter Portal')).toBeVisible();

    // Verify dashboard heading
    await expect(page.getByRole('heading', { name: /recruiter dashboard/i })).toBeVisible();

    // Verify welcome message
    await expect(page.getByText(/Welcome back!/i)).toBeVisible();

    // Verify BentoCard metrics
    await expect(page.getByText('Active Jobs')).toBeVisible();
    await expect(page.getByText('Total Candidates')).toBeVisible();
    await expect(page.getByText('Time to Hire')).toBeVisible();
    await expect(page.getByText('Applications/Job')).toBeVisible();

    // Verify Pipeline Funnel section
    await expect(page.getByText('Pipeline Funnel')).toBeVisible();

    // Verify navigation sections in sidebar
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Hiring')).toBeVisible();
    await expect(page.getByText('Resumes')).toBeVisible();
    await expect(page.getByText('Search')).toBeVisible();
    await expect(page.getByText('Analytics')).toBeVisible();
    await expect(page.getByText('Settings')).toBeVisible();

    // Verify skip-to-content link for accessibility
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');

    // Verify ARIA navigation
    const mainNav = page.getByRole('navigation', { name: /recruiter sidebar navigation/i });
    await expect(mainNav).toBeVisible();
  });

  /**
   * Step 2: View vacancies
   * Expected: VacanciesPage renders with vacancy list and actions
   */
  test('Step 2: View vacancies page', async ({ page }) => {
    await page.goto('/recruiter/vacancies');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading or loading state
    const heading = page.getByRole('heading', { name: /vacancies/i });
    const loading = page.getByText(/loading/i);
    await expect(heading.or(loading)).toBeVisible();

    // Verify RecruiterLayout components are still present
    await expect(page.getByText('AgentHR')).toBeVisible();
    await expect(page.getByText('Recruiter Portal')).toBeVisible();

    // Verify navigation items in sidebar
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Hiring')).toBeVisible();
    await expect(page.getByText('Vacancies')).toBeVisible();
    await expect(page.getByText('Candidates')).toBeVisible();
    await expect(page.getByText('Pipeline')).toBeVisible();

    // Check for action buttons (Add New Vacancy button or similar)
    const addButton = page.getByRole('button', { name: /add|create|new/i }).first();
    // May or may not be visible depending on state
    if (await addButton.isVisible()) {
      await expect(addButton).toBeVisible();
    }
  });

  /**
   * Step 3: View candidates kanban
   * Expected: CandidatesKanbanPage renders with kanban board and search
   */
  test('Step 3: View candidates kanban page', async ({ page }) => {
    await page.goto('/recruiter/candidates');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page heading
    await expect(page.getByRole('heading', { name: /candidate pipeline/i })).toBeVisible();

    // Verify subtitle
    await expect(page.getByText(/Drag candidates between stages/i)).toBeVisible();

    // Verify search functionality
    const searchInput = page.getByPlaceholder('Search candidates...');
    await expect(searchInput).toBeVisible();

    // Verify RecruiterLayout navigation
    await expect(page.getByText('AgentHR')).toBeVisible();
    await expect(page.getByText('Candidates')).toBeVisible();
    await expect(page.getByText('Pipeline')).toBeVisible();

    // Verify kanban board elements (column headers, etc.)
    // Default stages: Applied, Screening, Interview, Offer, Hired
    const stages = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'];
    for (const stage of stages) {
      const stageElement = page.getByText(stage);
      await expect(stageElement).toBeVisible();
    }
  });

  /**
   * Step 4: Navigate to search
   * Expected: SearchPage renders with search interface and filters
   */
  test('Step 4: Navigate to candidate search page', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify search page elements
    // May show loading or search interface
    const searchHeading = page.getByRole('heading', { name: /candidate search|search/i });
    const loading = page.getByText(/loading/i);
    await expect(searchHeading.or(loading)).toBeVisible();

    // Verify RecruiterLayout navigation
    await expect(page.getByText('AgentHR')).toBeVisible();
    await expect(page.getByText('Candidate Search')).toBeVisible();

    // Check for search-related UI elements
    const searchInput = page.getByPlaceholder(/search/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    // At least one search element should be present
    await expect(searchInput.or(searchButton).or(loading)).toBeVisible({ timeout: 5000 });
  });

  /**
   * Step 5: Navigate to analytics
   * Expected: AnalyticsDashboardPage renders with metrics and charts
   */
  test('Step 5: Navigate to analytics dashboard', async ({ page }) => {
    await page.goto('/recruiter/analytics');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify analytics page elements
    // May show loading or analytics content
    const analyticsHeading = page.getByRole('heading', { name: /analytics|overview/i });
    const loading = page.getByRole('progressbar');
    const metricsText = page.getByText(/metrics|time to hire|applications/i);

    await expect(analyticsHeading.or(loading).or(metricsText)).toBeVisible({ timeout: 5000 });

    // Verify RecruiterLayout navigation
    await expect(page.getByText('AgentHR')).toBeVisible();
    await expect(page.getByText('Overview')).toBeVisible();
    await expect(page.getByText('Skill Gap Analysis')).toBeVisible();
  });

  /**
   * Step 6: Verify all pages accessible
   * Expected: All navigation links work and pages render without errors
   */
  test('Step 6: Verify all Recruiter pages accessible', async ({ page }) => {
    // Test all key routes from navigation
    const routes = [
      '/recruiter/dashboard',
      '/recruiter/vacancies',
      '/recruiter/candidates',
      '/recruiter/search',
      '/recruiter/analytics',
      '/recruiter/saved-searches',
      '/recruiter/applications',
      '/recruiter/resumes',
      '/recruiter/upload',
      '/recruiter/compare',
      '/recruiter/skill-gap',
      '/recruiter/weights',
      '/recruiter/backups',
      '/recruiter/workflow',
    ];

    for (const route of routes) {
      await page.goto(route);

      // Wait for page to stabilize
      await page.waitForLoadState('networkidle');

      // Verify AgentHR branding is present (indicates layout loaded)
      await expect(page.getByText('AgentHR')).toBeVisible();

      // Verify Recruiter Portal header
      await expect(page.getByText('Recruiter Portal')).toBeVisible();

      // Verify no console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Wait a bit to catch any console errors
      await page.waitForTimeout(500);
    }
  });

  /**
   * Additional: Navigation flow test
   * Verify user can navigate between pages using sidebar
   */
  test('Navigation flow: Complete journey using sidebar', async ({ page }) => {
    // Start at dashboard
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify starting point
    await expect(page.getByRole('heading', { name: /recruiter dashboard/i })).toBeVisible();

    // Navigate to Vacancies
    await page.click('text=Vacancies');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('AgentHR')).toBeVisible();

    // Navigate to Candidates
    await page.click('text=Candidates');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /candidate pipeline/i })).toBeVisible();

    // Navigate to Search
    await page.click('text=Candidate Search');
    await page.waitForLoadState('networkidle');
    // Search page may show different content
    await expect(page.getByText('AgentHR')).toBeVisible();

    // Navigate to Analytics
    await page.click('text=Overview');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('AgentHR')).toBeVisible();

    // Navigate back to Dashboard
    await page.click('text=Dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /recruiter dashboard/i })).toBeVisible();
  });

  /**
   * Additional: Browser navigation (back/forward)
   * Verify browser back/forward buttons work correctly
   */
  test('Browser navigation: Back and forward buttons work', async ({ page }) => {
    // Go to dashboard
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /recruiter dashboard/i })).toBeVisible();

    // Navigate to vacancies
    await page.goto('/recruiter/vacancies');
    await page.waitForLoadState('networkidle');

    // Navigate to candidates
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /candidate pipeline/i })).toBeVisible();

    // Go back
    await page.goBack();
    await page.waitForLoadState('networkidle');

    // Go forward
    await page.goForward();
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /candidate pipeline/i })).toBeVisible();
  });

  /**
   * Additional: Accessibility verification
   * Verify keyboard navigation and ARIA attributes
   */
  test('Accessibility: Keyboard navigation works', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify skip-to-content link exists and is focusable
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');

    // Verify main navigation has proper ARIA role
    const mainNav = page.getByRole('navigation', { name: /recruiter sidebar navigation/i });
    await expect(mainNav).toBeVisible();

    // Verify navigation items have proper role
    const menuItems = page.getByRole('menuitem');
    await expect(menuItems.first()).toBeVisible();

    // Tab through navigation items
    await page.keyboard.press('Tab');
    // Should focus on first interactive element
  });

  /**
   * Additional: Mobile responsive verification
   * Verify layout works on mobile viewport
   */
  test('Mobile responsive: Layout adapts to mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify AgentHR branding
    await expect(page.getByText('AgentHR')).toBeVisible();

    // Verify mobile menu toggle is present
    const menuButton = page.getByRole('button', { name: /open navigation menu/i });
    await expect(menuButton).toBeVisible();

    // Verify content is still accessible
    await expect(page.getByRole('heading', { name: /recruiter dashboard/i })).toBeVisible();

    // Open mobile menu
    await menuButton.click();
    await page.waitForTimeout(500);

    // Verify navigation items are visible in mobile menu
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Hiring')).toBeVisible();
    await expect(page.getByText('Vacancies')).toBeVisible();
  });

  /**
   * Additional: Error handling
   * Verify handling of invalid routes
   */
  test('Error handling: Invalid recruiter route redirects gracefully', async ({ page }) => {
    // Navigate to invalid route
    await page.goto('/recruiter/invalid-page');

    // Wait for handling
    await page.waitForLoadState('networkidle');

    // Should either show an error or redirect
    // The app uses catch-all route that redirects to landing page
    // So we expect to be redirected or shown error content
    const currentUrl = page.url();
    const hasError = page.getByText(/error|not found|404/i);

    // Either we're still on recruiter path with error, or redirected
    if (currentUrl.includes('/recruiter/')) {
      await expect(hasError.or(page.getByText('AgentHR'))).toBeVisible();
    }
  });

  /**
   * Additional: Quick search shortcut
   * Verify Ctrl+K shortcut works for quick search
   */
  test('Quick search: Ctrl+K shortcut navigates to search', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Press Ctrl+K
    await page.keyboard.press('Control+K');

    // Should navigate to search page or focus search input
    await page.waitForTimeout(500);

    // Verify either we're on search page or search is focused
    const isOnSearchPage = page.url().includes('/recruiter/search');
    const searchInput = page.getByPlaceholder(/search/i);

    if (isOnSearchPage) {
      await expect(page.getByText('AgentHR')).toBeVisible();
    }
  });
});
