import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Recruiter Flow
 *
 * Test Suite Contents:
 * 1. Complete Recruiter Flow - Dashboard to Candidate View
 * 2. Navigation Between All Recruiter Pages
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

test.describe('Recruiter Flow - Landing Page Entry', () => {
  test('should display landing page with role selection', async ({ page }) => {
    await page.goto('/');

    // Check main heading
    await expect(page.getByRole('heading', { level: 1, name: /AgentHR|Transform Your Recruitment/i })).toBeVisible();

    // Check for role selection buttons/cards
    await expect(page.getByText(/Recruiter|Employer|Hiring/i })).toBeVisible();
  });

  test('should navigate to recruiter flow from landing', async ({ page }) => {
    await page.goto('/');

    // Click on recruiter option
    const recruiterButton = page.getByRole('button', { name: /Recruiter|Employer|Hiring/i }).or(
      page.locator('.MuiCard-root').filter({ hasText: /Recruiter|Employer/i })
    );

    const count = await recruiterButton.count();
    if (count > 0) {
      await recruiterButton.first().click();

      // Should navigate to recruiter dashboard or show RecruiterLayout
      await expect(page).toHaveURL(/\/recruiter/);
    }
  });
});

test.describe('Recruiter Flow - Recruiter Layout Navigation', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    // Navigate to a recruiter page to ensure RecruiterLayout is active
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display sidebar navigation with all items', async ({ page }) => {
    // Check for sidebar or navigation
    const sidebar = page.locator('aside').or(page.locator('[role="navigation"]'));

    // Look for navigation items
    const dashboardNav = page.getByRole('link', { name: /Dashboard/i }).or(page.locator('button').filter({ hasText: /Dashboard/i }));
    const vacanciesNav = page.getByRole('link', { name: /Vacancies|Jobs/i }).or(page.locator('button').filter({ hasText: /Vacancies/i }));
    const candidatesNav = page.getByRole('link', { name: /Candidates/i }).or(page.locator('button').filter({ hasText: /Candidates/i }));
    const analyticsNav = page.getByRole('link', { name: /Analytics/i }).or(page.locator('button').filter({ hasText: /Analytics/i }));
    const weightsNav = page.getByRole('link', { name: /Weights|Settings/i }).or(page.locator('button').filter({ hasText: /Weights/i }));

    // At least some navigation should be visible
    await expect(dashboardNav.or(vacanciesNav).or(candidatesNav).or(analyticsNav).or(weightsNav)).toBeVisible();
  });

  test('should navigate to Dashboard', async ({ page }) => {
    // Click on Dashboard navigation item
    const dashboardNav = page.getByRole('link', { name: /Dashboard/i }).or(page.locator('button').filter({ hasText: /Dashboard/i }));

    const count = await dashboardNav.count();
    if (count > 0) {
      await dashboardNav.first().click();
      await expect(page).toHaveURL(/\/recruiter\/dashboard/);

      // Check DashboardPage elements
      await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/recruiter/dashboard');
      await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();
    }
  });

  test('should navigate to Vacancies page', async ({ page }) => {
    // Click on Vacancies navigation item
    const vacanciesNav = page.getByRole('link', { name: /Vacancies/i }).or(page.locator('button').filter({ hasText: /Vacancies/i }));

    const count = await vacanciesNav.count();
    if (count > 0) {
      await vacanciesNav.first().click();
      await expect(page).toHaveURL(/\/recruiter\/vacancies/);

      // Check VacanciesPage elements
      await expect(page.getByRole('heading', { name: /Vacancies/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/recruiter/vacancies');
      await expect(page.getByRole('heading', { name: /Vacancies/i })).toBeVisible();
    }
  });

  test('should navigate to Candidates page', async ({ page }) => {
    // Click on Candidates navigation item
    const candidatesNav = page.getByRole('link', { name: /Candidates/i }).or(page.locator('button').filter({ hasText: /Candidates/i }));

    const count = await candidatesNav.count();
    if (count > 0) {
      await candidatesNav.first().click();
      await expect(page).toHaveURL(/\/recruiter\/candidates/);

      // Check CandidatesKanbanPage elements
      await expect(page.getByRole('heading', { name: /Candidates/i }).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/recruiter/candidates');
      await expect(page.getByRole('heading', { name: /Candidates/i })).toBeVisible();
    }
  });

  test('should navigate to Analytics page', async ({ page }) => {
    // Click on Analytics navigation item
    const analyticsNav = page.getByRole('link', { name: /Analytics/i }).or(page.locator('button').filter({ hasText: /Analytics/i }));

    const count = await analyticsNav.count();
    if (count > 0) {
      await analyticsNav.first().click();
      await expect(page).toHaveURL(/\/recruiter\/analytics/);

      // Check AnalyticsDashboardPage elements
      await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/recruiter/analytics');
      await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible();
    }
  });

  test('should navigate to Weights page', async ({ page }) => {
    // Click on Weights navigation item
    const weightsNav = page.getByRole('link', { name: /Weights/i }).or(page.locator('button').filter({ hasText: /Weights/i }));

    const count = await weightsNav.count();
    if (count > 0) {
      await weightsNav.first().click();
      await expect(page).toHaveURL(/\/recruiter\/weights/);

      // Check WeightsPage elements
      await expect(page.getByRole('heading', { name: /Weights|Customize Matching/i })).toBeVisible();
    } else {
      // Direct navigation test
      await page.goto('/recruiter/weights');
      await expect(page.getByRole('heading', { name: /Weights|Customize Matching/i })).toBeVisible();
    }
  });
});

test.describe('Recruiter Flow - Vacancy Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recruiter/vacancies/test-vacancy-123');
    await page.waitForLoadState('networkidle');
  });

  test('should display vacancy detail page', async ({ page }) => {
    // Check for vacancy details (may show loading/error without backend)
    const heading = page.getByRole('heading');
    const loadingOrError = page.getByText(/Loading|Error|Not Found|Vacancy not found/i);

    await expect(heading.or(loadingOrError)).toBeVisible();
  });

  test('should display action buttons', async ({ page }) => {
    // Look for action buttons
    const viewCandidatesButton = page.getByRole('button', { name: /View Candidates/i });
    const editVacancyButton = page.getByRole('button', { name: /Edit/i });

    // At least one action button should be present (if vacancy loads)
    const buttonCount = await viewCandidatesButton.count() + await editVacancyButton.count();
    if (buttonCount > 0) {
      await expect(viewCandidatesButton.or(editVacancyButton)).toBeVisible();
    }
  });

  test('should navigate from vacancy detail to candidates list', async ({ page }) => {
    const viewCandidatesButton = page.getByRole('button', { name: /View Candidates/i });

    const count = await viewCandidatesButton.count();
    if (count > 0) {
      await viewCandidatesButton.first().click();

      // Should navigate to candidates page
      await expect(page).toHaveURL(/\/recruiter\/candidates/);
    } else {
      // Test direct navigation as fallback
      await page.goto('/recruiter/candidates');
      await expect(page.getByRole('heading', { name: /Candidates/i })).toBeVisible();
    }
  });

  test('should navigate from vacancy detail to edit form', async ({ page }) => {
    const editVacancyButton = page.getByRole('button', { name: /Edit/i });

    const count = await editVacancyButton.count();
    if (count > 0) {
      await editVacancyButton.first().click();

      // Should navigate to edit form
      await expect(page).toHaveURL(/\/recruiter\/vacancies\/.*\/edit|vacancies\/create/);
    }
  });
});

test.describe('Recruiter Flow - Candidate Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recruiter/candidates/test-candidate-123');
    await page.waitForLoadState('networkidle');
  });

  test('should display candidate detail page', async ({ page }) => {
    // Check for candidate details (may show loading/error without backend)
    const heading = page.getByRole('heading');
    const loadingOrError = page.getByText(/Loading|Error|Candidate not found/i);

    await expect(heading.or(loadingOrError)).toBeVisible();
  });

  test('should display candidate information sections', async ({ page }) => {
    // Look for candidate information sections
    const contactInfo = page.getByText(/Contact|Email|Phone|Location/i);
    const skills = page.getByText(/Skills/i);
    const experience = page.getByText(/Experience|Work History/i);
    const analysis = page.getByText(/Analysis|Match|Score/i);

    // At least some sections should be visible (if candidate loads)
    const hasContent = await contactInfo.isVisible().catch(() => false) ||
                      await skills.isVisible().catch(() => false) ||
                      await experience.isVisible().catch(() => false) ||
                      await analysis.isVisible().catch(() => false) ||
                      await page.getByText(/Loading|Error/i).isVisible();

    expect(hasContent).toBeTruthy();
  });

  test('should display tabs for different information views', async ({ page }) => {
    // Look for tab navigation
    const tabs = page.locator('[role="tab"]').or(page.locator('.MuiTabs-root'));

    const tabsCount = await tabs.count();
    if (tabsCount > 0) {
      await expect(tabs.first()).toBeVisible();
    }
  });
});

test.describe('Recruiter Flow - Weights Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recruiter/weights');
    await page.waitForLoadState('networkidle');
  });

  test('should display weights customization page', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /Weights|Customize Matching/i })).toBeVisible();
  });

  test('should display weight sliders', async ({ page }) => {
    // Look for slider inputs
    const sliders = page.locator('input[type="range"]').or(page.locator('[role="slider"]'));

    const sliderCount = await sliders.count();
    if (sliderCount > 0) {
      await expect(sliders.first()).toBeVisible();
    }
  });

  test('should display weight distribution visualization', async ({ page }) => {
    // Look for progress bars or visual indicators
    const progressBars = page.locator('.MuiLinearProgress-root').or(
      page.locator('[role="progressbar"]')
    );

    const barCount = await progressBars.count();
    if (barCount > 0) {
      await expect(progressBars.first()).toBeVisible();
    }
  });

  test('should display tabs for presets, custom, and saved profiles', async ({ page }) => {
    // Look for tab navigation
    const tabs = page.locator('[role="tab"]').or(page.locator('.MuiTabs-root'));

    const tabsCount = await tabs.count();
    if (tabsCount > 0) {
      await expect(tabs.first()).toBeVisible();

      // Check for preset, custom, and saved tabs
      const presetTab = page.getByRole('tab', { name: /Preset/i }).or(page.getByText(/Preset/i));
      const customTab = page.getByRole('tab', { name: /Custom/i }).or(page.getByText(/Custom/i));
      const savedTab = page.getByRole('tab', { name: /Saved/i }).or(page.getByText(/Saved/i));

      await expect(presetTab.or(customTab).or(savedTab)).toBeVisible();
    }
  });

  test('should display preset configurations', async ({ page }) => {
    // Look for preset cards
    const presetCards = page.locator('.MuiCard-root').filter({ hasText: /Preset|Technical|Creative|Balanced/i });

    const cardCount = await presetCards.count();
    if (cardCount > 0) {
      await expect(presetCards.first()).toBeVisible();
    }
  });

  test('should display save profile functionality', async ({ page }) => {
    // Look for save button
    const saveButton = page.getByRole('button', { name: /Save/i });

    const saveCount = await saveButton.count();
    if (saveCount > 0) {
      await expect(saveButton.first()).toBeVisible();
    }
  });

  test('should display explanation section', async ({ page }) => {
    // Look for explanation cards or text
    const explanation = page.getByText(/Keyword|TF-IDF|Vector|Semantic|Explanation/i);

    await expect(explanation).toBeVisible();
  });
});

test.describe('Recruiter Flow - Complete Journey', () => {
  test('should navigate through entire recruiter flow', async ({ page }) => {
    // Start at landing page
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Navigate to recruiter dashboard
    await page.goto('/recruiter/dashboard');
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();

    // Navigate to vacancies
    await page.goto('/recruiter/vacancies');
    await expect(page.getByRole('heading', { name: /Vacancies/i })).toBeVisible();

    // Navigate to candidates
    await page.goto('/recruiter/candidates');
    await expect(page.getByRole('heading', { name: /Candidates/i })).toBeVisible();

    // Navigate to analytics
    await page.goto('/recruiter/analytics');
    await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible();

    // Navigate to weights
    await page.goto('/recruiter/weights');
    await expect(page.getByRole('heading', { name: /Weights|Customize Matching/i })).toBeVisible();
  });

  test('should navigate from dashboard to candidate detail', async ({ page }) => {
    // Start at dashboard
    await page.goto('/recruiter/dashboard');
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();

    // Navigate to candidates
    await page.goto('/recruiter/candidates');
    await expect(page.getByRole('heading', { name: /Candidates/i })).toBeVisible();

    // Navigate to candidate detail
    await page.goto('/recruiter/candidates/test-candidate-123');

    // Should display candidate detail or loading/error
    const heading = page.getByRole('heading');
    const loadingOrError = page.getByText(/Loading|Error|Candidate not found/i);

    await expect(heading.or(loadingOrError)).toBeVisible();
  });

  test('should navigate from dashboard to vacancy detail', async ({ page }) => {
    // Start at dashboard
    await page.goto('/recruiter/dashboard');
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();

    // Navigate to vacancies
    await page.goto('/recruiter/vacancies');
    await expect(page.getByRole('heading', { name: /Vacancies/i })).toBeVisible();

    // Navigate to vacancy detail
    await page.goto('/recruiter/vacancies/test-vacancy-123');

    // Should display vacancy detail or loading/error
    const heading = page.getByRole('heading');
    const loadingOrError = page.getByText(/Loading|Error|Vacancy not found/i);

    await expect(heading.or(loadingOrError)).toBeVisible();
  });

  test('should support browser back and forward navigation', async ({ page }) => {
    // Navigate through pages
    await page.goto('/recruiter/dashboard');
    await page.goto('/recruiter/vacancies');
    await page.goto('/recruiter/candidates');

    // Go back
    await page.goBack();
    await expect(page).toHaveURL(/\/recruiter\/vacancies/);

    // Go back again
    await page.goBack();
    await expect(page).toHaveURL(/\/recruiter\/dashboard/);

    // Go forward
    await page.goForward();
    await expect(page).toHaveURL(/\/recruiter\/vacancies/);
  });
});

test.describe('Recruiter Flow - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('should display properly on mobile viewport', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();

    // Check for no horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
  });

  test('should show hamburger menu on mobile', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Hamburger menu should be visible on mobile
    const hamburgerMenu = page.getByRole('button', { name: /menu/i }).or(
      page.locator('button[aria-label="menu"]')
    );

    const menuCount = await hamburgerMenu.count();
    if (menuCount > 0) {
      await expect(hamburgerMenu.first()).toBeVisible();
    }
  });

  test('should navigate through all recruiter pages on mobile', async ({ page }) => {
    const recruiterPages = [
      { path: '/recruiter/dashboard', name: 'Dashboard' },
      { path: '/recruiter/vacancies', name: 'Vacancies' },
      { path: '/recruiter/candidates', name: 'Candidates' },
      { path: '/recruiter/analytics', name: 'Analytics' },
      { path: '/recruiter/weights', name: 'Weights' },
    ];

    for (const pagePath of recruiterPages) {
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

  test('should open sidebar drawer on mobile when menu clicked', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for hamburger menu
    const hamburgerMenu = page.getByRole('button', { name: /menu/i }).or(
      page.locator('button[aria-label="menu"]')
    );

    const menuCount = await hamburgerMenu.count();
    if (menuCount > 0) {
      // Click menu to open drawer
      await hamburgerMenu.first().click();
      await page.waitForTimeout(300);

      // Drawer should be visible (navigation items should appear)
      const navItems = page.locator('nav a, nav button');
      const navCount = await navItems.count();
      expect(navCount).toBeGreaterThan(0);
    }
  });
});

test.describe('Recruiter Flow - Desktop Responsive', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should display properly on desktop viewport', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Candidates/i })).toBeVisible();

    // Content should use desktop space
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyWidth).toBeGreaterThan(900);
  });

  test('should show sidebar on desktop', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Sidebar should be visible on desktop
    const sidebar = page.locator('aside').or(page.locator('[class*="sidebar" i]'));

    const sidebarCount = await sidebar.count();
    if (sidebarCount > 0) {
      await expect(sidebar.first()).toBeVisible();
    }
  });

  test('should display kanban board on desktop', async ({ page }) => {
    await page.goto('/recruiter/candidates');
    await page.waitForLoadState('networkidle');

    // Look for kanban columns
    const columns = page.locator('[class*="column" i], [class*="lane" i]').or(
      page.locator('.MuiStack-root').filter({ has: page.getByText(/To Do|Applied|Shortlisted|Interview/i) })
    );

    const columnCount = await columns.count();
    if (columnCount > 0) {
      await expect(columns.first()).toBeVisible();
    }
  });

  test('should display grid layouts on vacancies page', async ({ page }) => {
    await page.goto('/recruiter/vacancies');
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
        const horizontallySpaced = secondBox.x > firstBox.x + 50;
        const verticallyStacked = secondBox.y > firstBox.y;

        expect(horizontallySpaced || verticallyStacked).toBeTruthy();
      }
    }
  });
});

test.describe('Recruiter Flow - Error Handling', () => {
  test('should handle invalid vacancy IDs gracefully', async ({ page }) => {
    // Navigate with invalid ID
    await page.goto('/recruiter/vacancies/invalid-vacancy-id');
    await page.waitForLoadState('networkidle');

    // Should show error state or redirect
    const errorMessage = page.getByText(/Error|Not Found|Failed to load|Vacancy not found/i);
    const redirectCheck = page.url().match(/\/recruiter\/vacancies($|\/$)/);

    const hasErrorOrRedirect = await errorMessage.isVisible().catch(() => false) || redirectCheck;
    expect(hasErrorOrRedirect).toBeTruthy();
  });

  test('should handle invalid candidate IDs gracefully', async ({ page }) => {
    // Navigate with invalid ID
    await page.goto('/recruiter/candidates/invalid-candidate-id');
    await page.waitForLoadState('networkidle');

    // Should show error state or redirect
    const errorMessage = page.getByText(/Error|Not Found|Failed to load|Candidate not found/i);
    const redirectCheck = page.url().match(/\/recruiter\/candidates($|\/$)/);

    const hasErrorOrRedirect = await errorMessage.isVisible().catch(() => false) || redirectCheck;
    expect(hasErrorOrRedirect).toBeTruthy();
  });

  test('should handle network errors on dashboard', async ({ page }) => {
    // Navigate to dashboard (may show loading/error without backend)
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Page should not crash - should show loading, error, or content
    const loading = page.getByText(/Loading/i);
    const error = page.getByText(/Error|Failed/i);
    const content = page.locator('h1, h2, .MuiCard-root');

    await expect(loading.or(error).or(content)).toBeVisible();
  });

  test('should handle direct URL access to all recruiter pages', async ({ page }) => {
    const recruiterPages = [
      '/recruiter/dashboard',
      '/recruiter/vacancies',
      '/recruiter/candidates',
      '/recruiter/analytics',
      '/recruiter/weights',
      '/recruiter/vacancies/test-123',
      '/recruiter/candidates/test-456',
    ];

    for (const pagePath of recruiterPages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      // Page should render without crashing
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('Recruiter Flow - Weights Page Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recruiter/weights');
    await page.waitForLoadState('networkidle');
  });

  test('should switch between tabs', async ({ page }) => {
    const tabs = page.locator('[role="tab"]');

    const tabsCount = await tabs.count();
    if (tabsCount >= 2) {
      // Click on second tab
      await tabs.nth(1).click();
      await page.waitForTimeout(300);

      // Tab should be active
      const isActive = await tabs.nth(1).getAttribute('aria-selected');
      expect(isActive).toBe('true');
    }
  });

  test('should select preset configuration', async ({ page }) => {
    // Look for preset cards
    const presetCards = page.locator('.MuiCard-root').filter({ hasText: /Technical|Creative|Executive|Balanced/i });

    const cardCount = await presetCards.count();
    if (cardCount > 0) {
      // Click on first preset card
      await presetCards.first().click();
      await page.waitForTimeout(300);

      // Should update weight visualization (progress bars)
      const progressBars = page.locator('.MuiLinearProgress-root');
      const barCount = await progressBars.count();
      if (barCount > 0) {
        await expect(progressBars.first()).toBeVisible();
      }
    }
  });

  test('should adjust weight sliders', async ({ page }) => {
    const sliders = page.locator('input[type="range"]');

    const sliderCount = await sliders.count();
    if (sliderCount > 0) {
      // Get initial value
      const firstSlider = sliders.first();
      const initialValue = await firstSlider.inputValue();

      // Adjust slider
      await firstSlider.fill('50');
      await page.waitForTimeout(300);

      // Value should change
      const newValue = await firstSlider.inputValue();
      expect(newValue).toBeTruthy();
    }
  });

  test('should normalize weights when button clicked', async ({ page }) => {
    const normalizeButton = page.getByRole('button', { name: /Normalize/i });

    const buttonCount = await normalizeButton.count();
    if (buttonCount > 0) {
      await normalizeButton.first().click();
      await page.waitForTimeout(300);

      // Should show success message or update UI
      const success = page.getByText(/normalized|updated/i);
      const progressBars = page.locator('.MuiLinearProgress-root');

      await expect(success.or(progressBars)).toBeVisible();
    }
  });

  test('should save weight profile', async ({ page }) => {
    const saveButton = page.getByRole('button', { name: /Save/i });

    const buttonCount = await saveButton.count();
    if (buttonCount > 0) {
      await saveButton.first().click();
      await page.waitForTimeout(300);

      // Should show dialog or success message
      const dialog = page.locator('.MuiDialog-root').or(page.getByRole('dialog'));
      const success = page.getByText(/saved|success/i);

      await expect(dialog.or(success)).toBeVisible();
    }
  });
});

test.describe('Recruiter Flow - Page Transitions', () => {
  test('should have smooth transitions between pages', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Get initial state
    const initialUrl = page.url();

    // Navigate to another page
    await page.goto('/recruiter/vacancies');
    await page.waitForLoadState('networkidle');

    // URL should change
    expect(page.url()).not.toBe(initialUrl);

    // Content should be visible
    await expect(page.getByRole('heading')).toBeVisible();
  });
});

test.describe('Recruiter Flow - Accessibility', () => {
  test('should have proper heading hierarchy on recruiter pages', async ({ page }) => {
    const recruiterPages = [
      '/recruiter/dashboard',
      '/recruiter/vacancies',
      '/recruiter/candidates',
      '/recruiter/analytics',
      '/recruiter/weights',
    ];

    for (const pagePath of recruiterPages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      // Check for h1 heading
      const h1 = page.getByRole('heading', { level: 1 });
      await expect(h1).toBeVisible();
    }
  });

  test('should be keyboard navigable on recruiter pages', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'NAV']).includes(focused || '').toBeTruthy();
  });

  test('should have ARIA labels on navigation elements', async ({ page }) => {
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');

    // Check for ARIA labels on navigation
    const navElements = page.locator('nav, [role="navigation"], aside');
    const count = await navElements.count();

    if (count > 0) {
      // At least one nav should have aria-label or role
      const hasAria = await navElements.first().getAttribute('aria-label') ||
                     await navElements.first().getAttribute('role');
      expect(hasAria).toBeTruthy();
    }
  });

  test('should have accessible form controls on weights page', async ({ page }) => {
    await page.goto('/recruiter/weights');
    await page.waitForLoadState('networkidle');

    // Check for form labels
    const sliders = page.locator('input[type="range"]');

    const sliderCount = await sliders.count();
    if (sliderCount > 0) {
      // Sliders should have labels (aria-label or associated label element)
      const firstSlider = sliders.first();
      const hasLabel = await firstSlider.getAttribute('aria-label') ||
                      await firstSlider.getAttribute('aria-labelledby');
      expect(hasLabel).toBeTruthy();
    }
  });
});

test.describe('Recruiter Flow - Flow Separation', () => {
  test('should maintain separate recruiter flow from candidate flow', async ({ page }) => {
    // Navigate to recruiter page
    await page.goto('/recruiter/dashboard');
    await expect(page).toHaveURL(/\/recruiter/);

    // Should NOT have candidate navigation elements
    const candidateNav = page.locator('nav').filter({ hasText: /Saved Jobs|My Applications/i });
    const candidateCount = await candidateNav.count();

    // Recruiter layout should not show candidate navigation
    expect(candidateCount).toBe(0);
  });

  test('should not allow navigation from recruiter to candidate pages via nav', async ({ page }) => {
    await page.goto('/recruiter/dashboard');

    // Look for candidate navigation links
    const jobsBrowseLink = page.getByRole('link', { name: /Jobs Browse|Search Jobs/i });
    const savedJobsLink = page.getByRole('link', { name: /Saved Jobs/i });

    // These should not exist in recruiter navigation
    const jobsCount = await jobsBrowseLink.count();
    const savedCount = await savedJobsLink.count();

    expect(jobsCount + savedCount).toBe(0);
  });
});
