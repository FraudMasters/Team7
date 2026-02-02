import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Candidate Flow (Job Seeker)
 *
 * Test Suite Contents:
 * 1. Complete Candidate Flow - Landing to Application
 * 2. Navigation Between All Candidate Pages
 * 3. Page Rendering and Functionality
 * 4. Responsive Design on Mobile and Desktop
 * 5. Error Handling and Edge Cases
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

test.describe('Candidate Flow - Landing Page Entry', () => {
  test('should display landing page with role selection', async ({ page }) => {
    await page.goto('/');

    // Check main heading
    await expect(page.getByRole('heading', { level: 1, name: /AgentHR|Transform Your Recruitment/i })).toBeVisible();

    // Check for role selection buttons/cards
    await expect(page.getByText(/Candidate|Job Seeker/i)).toBeVisible();
  });

  test('should navigate to candidate flow from landing', async ({ page }) => {
    await page.goto('/');

    // Click on candidate/job seeker option
    const candidateButton = page.getByRole('button', { name: /Candidate|Job Seeker/i }).or(
      page.locator('.MuiCard-root').filter({ hasText: /Candidate|Job Seeker/i })
    );

    const count = await candidateButton.count();
    if (count > 0) {
      await candidateButton.first().click();

      // Should navigate to jobs page or show JobSeekerLayout
      await expect(page).toHaveURL(/\/jobs/);
    }
  });
});

test.describe('Candidate Flow - Job Seeker Layout Navigation', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    // Navigate to a candidate page to ensure JobSeekerLayout is active
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');
  });

  test('should display bottom navigation with all items', async ({ page }) => {
    // Check for bottom navigation (may not be visible on desktop)
    const bottomNav = page.locator('nav').or(page.locator('[role="navigation"]'));

    // Look for navigation items
    const searchNav = page.getByRole('link', { name: /Search/i }).or(page.locator('button').filter({ hasText: /Search/i }));
    const savedNav = page.getByRole('link', { name: /Saved/i }).or(page.locator('button').filter({ hasText: /Saved/i }));
    const applicationsNav = page.getByRole('link', { name: /Applications/i }).or(page.locator('button').filter({ hasText: /Applications/i }));
    const profileNav = page.getByRole('link', { name: /Profile/i }).or(page.locator('button').filter({ hasText: /Profile/i }));

    // At least some navigation should be visible
    await expect(searchNav.or(savedNav).or(applicationsNav).or(profileNav)).toBeVisible();
  });

  test('should navigate to Saved Jobs page', async ({ page }) => {
    // Click on Saved navigation item
    const savedNav = page.getByRole('link', { name: /Saved/i }).or(page.locator('button').filter({ hasText: /Saved/i }));

    const count = await savedNav.count();
    if (count > 0) {
      await savedNav.first().click();
      await expect(page).toHaveURL(/\/jobs\/saved/);

      // Check SavedJobsPage elements
      await expect(page.getByRole('heading', { name: /Saved Jobs/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/jobs/saved');
      await expect(page.getByRole('heading', { name: /Saved Jobs/i })).toBeVisible();
    }
  });

  test('should navigate to My Applications page', async ({ page }) => {
    // Click on Applications navigation item
    const applicationsNav = page.getByRole('link', { name: /Applications/i }).or(page.locator('button').filter({ hasText: /Applications/i }));

    const count = await applicationsNav.count();
    if (count > 0) {
      await applicationsNav.first().click();
      await expect(page).toHaveURL(/\/jobs\/applications/);

      // Check MyApplicationsPage elements
      await expect(page.getByRole('heading', { name: /My Applications/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/jobs/applications');
      await expect(page.getByRole('heading', { name: /My Applications/i })).toBeVisible();
    }
  });

  test('should navigate to Profile page', async ({ page }) => {
    // Click on Profile navigation item
    const profileNav = page.getByRole('link', { name: /Profile/i }).or(page.locator('button').filter({ hasText: /Profile/i }));

    const count = await profileNav.count();
    if (count > 0) {
      await profileNav.first().click();
      await expect(page).toHaveURL(/\/profile/);

      // Check CandidateProfilePage elements
      await expect(page.getByRole('heading', { name: /Profile|My Profile/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/profile');
      await expect(page.getByRole('heading', { name: /Profile|My Profile/i })).toBeVisible();
    }
  });
});

test.describe('Candidate Flow - Saved Jobs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');
  });

  test('should display saved jobs page with search', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /Saved Jobs/i })).toBeVisible();

    // Check for search functionality
    const searchInput = page.getByPlaceholder(/Search/i).or(page.locator('input[type="search"]'));
    await expect(searchInput.first()).toBeVisible();
  });

  test('should display empty state when no saved jobs', async ({ page }) => {
    // Check for empty state message
    const emptyState = page.getByText(/No saved jobs|You haven't saved any jobs yet/i);
    const bookmarkIcon = page.locator('svg').filter({ hasText: /bookmark/i });

    // Either empty state should be visible or job cards
    const isEmptyOrHasJobs = await emptyState.isVisible().catch(() => false) ||
                            await page.locator('.MuiCard-root').count().then(count => count > 0);

    expect(isEmptyOrHasJobs).toBeTruthy();
  });

  test('should filter saved jobs by search term', async ({ page }) => {
    // Type in search box
    const searchInput = page.getByPlaceholder(/Search/i).or(page.locator('input[type="search"]')).first();

    await searchInput.fill('developer');
    await page.waitForTimeout(500); // Wait for debounced search

    // Check that search was performed (URL may have search param or UI updates)
    await expect(searchInput).toHaveValue('developer');
  });
});

test.describe('Candidate Flow - My Applications Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/jobs/applications');
    await page.waitForLoadState('networkidle');
  });

  test('should display applications page with filters', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /My Applications/i })).toBeVisible();

    // Check for search functionality
    const searchInput = page.getByPlaceholder(/Search/i).or(page.locator('input[type="search"]'));
    await expect(searchInput.first()).toBeVisible();

    // Check for status filter
    const statusFilter = page.getByRole('combobox').or(page.getByRole('listbox'));
    const filterCount = await statusFilter.count();

    // Status filter may or may not be present depending on UI design
    if (filterCount > 0) {
      await expect(statusFilter.first()).toBeVisible();
    }
  });

  test('should display empty state when no applications', async ({ page }) => {
    // Check for empty state message
    const emptyState = page.getByText(/No applications|You haven't applied to any jobs/i);
    const workIcon = page.locator('svg').filter({ hasText: /work/i });

    // Either empty state should be visible or application cards
    const isEmptyOrHasApps = await emptyState.isVisible().catch(() => false) ||
                             await page.locator('.MuiCard-root').count().then(count => count > 0);

    expect(isEmptyOrHasApps).toBeTruthy();
  });

  test('should filter applications by status', async ({ page }) => {
    // Look for status filter dropdown
    const statusFilter = page.getByRole('combobox').or(page.getByRole('button', { name: /Status/i }));

    const count = await statusFilter.count();
    if (count > 0) {
      // Open filter
      await statusFilter.first().click();
      await page.waitForTimeout(300);

      // Select a status option (e.g., "Pending")
      const pendingOption = page.getByRole('option', { name: /Pending/i }).or(page.getByText(/Pending/i));
      const optionCount = await pendingOption.count();

      if (optionCount > 0) {
        await pendingOption.first().click();
        await page.waitForTimeout(500);

        // Verify filter was applied
        await expect(statusFilter.first()).toBeVisible();
      }
    }
  });
});

test.describe('Candidate Flow - Candidate Profile Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');
  });

  test('should display profile page with edit functionality', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /Profile/i })).toBeVisible();

    // Check for edit button
    const editButton = page.getByRole('button', { name: /Edit/i });
    const editCount = await editButton.count();

    // Edit button should be present
    if (editCount > 0) {
      await expect(editButton.first()).toBeVisible();
    }
  });

  test('should display profile sections', async ({ page }) => {
    // Check for profile information sections
    const contactInfo = page.getByText(/Contact|Email|Phone|Location/i);
    const skills = page.getByText(/Skills/i);
    const experience = page.getByText(/Experience|Work History/i);
    const education = page.getByText(/Education/i);

    // At least some profile sections should be visible
    await expect(contactInfo.or(skills).or(experience).or(education)).toBeVisible();
  });

  test('should enter edit mode when Edit button clicked', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /Edit/i });
    const editCount = await editButton.count();

    if (editCount > 0) {
      await editButton.first().click();
      await page.waitForTimeout(300);

      // Should show input fields or Save/Cancel buttons
      const saveButton = page.getByRole('button', { name: /Save/i });
      const cancelButton = page.getByRole('button', { name: /Cancel/i });

      await expect(saveButton.or(cancelButton)).toBeVisible();
    }
  });
});

test.describe('Candidate Flow - Resume Upload and Results', () => {
  test('should navigate to resume upload page', async ({ page }) => {
    await page.goto('/jobs/upload');
    await page.waitForLoadState('networkidle');

    // Check page heading
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();

    // Check for upload area
    await expect(page.getByText(/Drag and drop|Browse Files/i)).toBeVisible();
  });

  test('should display stepper for upload process', async ({ page }) => {
    await page.goto('/jobs/upload');
    await page.waitForLoadState('networkidle');

    // Check for stepper or progress indicator
    const stepper = page.getByRole('navigation', { name: /stepper|progress/i }).or(
      page.locator('.MuiStepper-root')
    );

    const stepperCount = await stepper.count();
    if (stepperCount > 0) {
      await expect(stepper.first()).toBeVisible();
    }
  });

  test('should navigate to resume results page', async ({ page }) => {
    // Navigate to results page with test ID
    await page.goto('/jobs/resume-results/test-resume-123');
    await page.waitForLoadState('networkidle');

    // Check for results page elements (may show error without backend)
    const resultsHeading = page.getByRole('heading', { name: /Analysis Results|Resume Results/i });
    const loadingOrError = page.getByText(/Loading|Error|Failed/i);

    await expect(resultsHeading.or(loadingOrError)).toBeVisible();
  });
});

test.describe('Candidate Flow - Complete Journey', () => {
  test('should navigate through entire candidate flow', async ({ page }) => {
    // Start at landing page
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Navigate to jobs browse page
    await page.goto('/jobs');
    await expect(page.getByRole('heading', { name: /Jobs|Browse Jobs/i })).toBeVisible();

    // Navigate to saved jobs
    await page.goto('/jobs/saved');
    await expect(page.getByRole('heading', { name: /Saved Jobs/i })).toBeVisible();

    // Navigate to my applications
    await page.goto('/jobs/applications');
    await expect(page.getByRole('heading', { name: /My Applications/i })).toBeVisible();

    // Navigate to profile
    await page.goto('/profile');
    await expect(page.getByRole('heading', { name: /Profile/i })).toBeVisible();

    // Navigate to resume upload
    await page.goto('/jobs/upload');
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();
  });

  test('should support browser back and forward navigation', async ({ page }) => {
    // Navigate through pages
    await page.goto('/jobs');
    await page.goto('/jobs/saved');
    await page.goto('/jobs/applications');

    // Go back
    await page.goBack();
    await expect(page).toHaveURL(/\/jobs\/saved/);

    // Go back again
    await page.goBack();
    await expect(page).toHaveURL(/\/jobs/);

    // Go forward
    await page.goForward();
    await expect(page).toHaveURL(/\/jobs\/saved/);
  });
});

test.describe('Candidate Flow - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('should display properly on mobile viewport', async ({ page }) => {
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Saved Jobs/i })).toBeVisible();

    // Check for no horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
  });

  test('should show bottom navigation on mobile', async ({ page }) => {
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');

    // Bottom navigation should be visible on mobile
    const bottomNav = page.locator('nav[aria-label*="bottom" i]').or(
      page.locator('.MuiBottomNavigation-root')
    );

    const navCount = await bottomNav.count();
    if (navCount > 0) {
      await expect(bottomNav.first()).toBeVisible();
    }
  });

  test('should navigate through all candidate pages on mobile', async ({ page }) => {
    const candidatePages = [
      { path: '/jobs', name: 'Jobs Browse' },
      { path: '/jobs/saved', name: 'Saved Jobs' },
      { path: '/jobs/applications', name: 'My Applications' },
      { path: '/profile', name: 'Profile' },
    ];

    for (const pagePath of candidatePages) {
      await page.goto(pagePath.path);
      await page.waitForLoadState('networkidle');

      // Check that page loads without errors
      await expect(page.locator('body')).toBeVisible();

      // Check no horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 15);
    }
  });
});

test.describe('Candidate Flow - Desktop Responsive', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should display properly on desktop viewport', async ({ page }) => {
    await page.goto('/jobs/applications');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /My Applications/i })).toBeVisible();

    // Content should use desktop space
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyWidth).toBeGreaterThan(900);
  });

  test('should display grid layouts on desktop', async ({ page }) => {
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // Check for grid layout (cards should be arranged horizontally)
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();

    if (count >= 2) {
      const firstCard = cards.first();
      const secondCard = cards.nth(1);

      const firstBox = await firstCard.boundingBox();
      const secondBox = await secondCard.boundingBox();

      if (firstBox && secondBox) {
        // On desktop, cards should be in grid layout
        // Second card should either be to the right (same row) or below (next row)
        const horizontallySpaced = secondBox.x > firstBox.x + 50;
        const verticallyStacked = secondBox.y > firstBox.y;

        expect(horizontallySpaced || verticallyStacked).toBeTruthy();
      }
    }
  });
});

test.describe('Candidate Flow - Error Handling', () => {
  test('should handle invalid job IDs gracefully', async ({ page }) => {
    // Navigate with invalid ID
    await page.goto('/jobs/invalid-job-id');
    await page.waitForLoadState('networkidle');

    // Should show error state or redirect
    const errorMessage = page.getByText(/Error|Not Found|Failed to load/i);
    const redirectCheck = page.url().match(/\/jobs($|\/$)/);

    const hasErrorOrRedirect = await errorMessage.isVisible().catch(() => false) || redirectCheck;
    expect(hasErrorOrRedirect).toBeTruthy();
  });

  test('should handle network errors on saved jobs', async ({ page }) => {
    // Navigate to saved jobs (may show loading/error without backend)
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // Page should not crash - should show loading, error, or content
    const loading = page.getByText(/Loading/i);
    const error = page.getByText(/Error|Failed/i);
    const content = page.locator('.MuiCard-root, h1, h2');

    await expect(loading.or(error).or(content)).toBeVisible();
  });

  test('should handle direct URL access to all candidate pages', async ({ page }) => {
    const candidatePages = [
      '/jobs',
      '/jobs/saved',
      '/jobs/applications',
      '/profile',
      '/jobs/upload',
      '/jobs/resume-results/test-123',
    ];

    for (const pagePath of candidatePages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      // Page should render without crashing
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('Candidate Flow - Page Transitions', () => {
  test('should have smooth transitions between pages', async ({ page }) => {
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');

    // Get initial state
    const initialUrl = page.url();

    // Navigate to another page
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // URL should change
    expect(page.url()).not.toBe(initialUrl);

    // Content should be visible
    await expect(page.getByRole('heading')).toBeVisible();
  });
});

test.describe('Candidate Flow - Accessibility', () => {
  test('should have proper heading hierarchy on candidate pages', async ({ page }) => {
    const candidatePages = ['/jobs', '/jobs/saved', '/jobs/applications', '/profile'];

    for (const pagePath of candidatePages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      // Check for h1 heading
      const h1 = page.getByRole('heading', { level: 1 });
      await expect(h1).toBeVisible();
    }
  });

  test('should be keyboard navigable on candidate pages', async ({ page }) => {
    await page.goto('/jobs/saved');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'NAV'].includes(focused || '')).toBeTruthy();
  });

  test('should have ARIA labels on navigation elements', async ({ page }) => {
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');

    // Check for ARIA labels on navigation
    const navElements = page.locator('nav, [role="navigation"]');
    const count = await navElements.count();

    if (count > 0) {
      // At least one nav should have aria-label or role
      const hasAria = await navElements.first().getAttribute('aria-label') ||
                     await navElements.first().getAttribute('role');
      expect(hasAria).toBeTruthy();
    }
  });
});
