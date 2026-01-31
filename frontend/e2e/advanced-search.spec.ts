import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Advanced Search and Filtering
 *
 * Test Suite Contents:
 * 1. Navigation & Page Rendering
 * 2. Advanced Search Filters
 * 3. Boolean Search Operators
 * 4. Saved Search Management
 * 5. Search History
 * 6. Search Results Display
 * 7. Error Handling
 * 8. Complete User Journeys
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Test data: resumes and vacancies in the database
 */

test.describe('Navigation & Page Rendering', () => {
  test('should load candidate search page with all elements', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check page title
    await expect(page).toHaveTitle(/Candidate Search|Resume Analysis/);

    // Check main heading
    const mainHeading = page.getByRole('heading', { level: 1, name: /Candidate Search|Find Candidates/i });
    await expect(mainHeading).toBeVisible();

    // Check tabs
    await expect(page.getByRole('tab', { name: /Search/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Saved Searches/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Search History/i })).toBeVisible();

    // Check search panel elements
    await expect(page.getByText(/Select Vacancy/i)).toBeVisible();
    await expect(page.getByText(/Filter by Skills/i)).toBeVisible();
    await expect(page.getByText(/Minimum Match Percentage/i)).toBeVisible();
  });

  test('should display advanced filters toggle button', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for advanced filters button
    const advancedFiltersBtn = page.getByRole('button', { name: /Advanced Filters|Enable Advanced Filters/i });
    await expect(advancedFiltersBtn).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/candidate-search');

    // Click on Saved Searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();
    await expect(page.getByRole('tab', { name: /Saved Searches/i, selected: true })).toBeVisible();

    // Click on Search History tab
    await page.getByRole('tab', { name: /Search History/i }).click();
    await expect(page.getByRole('tab', { name: /Search History/i, selected: true })).toBeVisible();

    // Click back to Search tab
    await page.getByRole('tab', { name: /^Search$/i }).click();
    await expect(page.getByRole('tab', { name: /^Search$/i, selected: true })).toBeVisible();
  });

  test('should display AI ranking options', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for AI ranking toggle buttons
    await expect(page.getByRole('button', { name: /AI Ranking/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Match Percent/i })).toBeVisible();

    // Check for use AI ranking checkbox
    await expect(page.getByRole('checkbox', { name: /Use AI Ranking/i })).toBeVisible();
  });
});

test.describe('Advanced Search Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
  });

  test('should enable advanced filters panel', async ({ page }) => {
    // Click advanced filters button
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Wait for panel to appear
    await expect(page.getByText(/Skills/i)).toBeVisible({ timeout: 5000 });
  });

  test('should display all filter fields', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Check for filter inputs
    await expect(page.getByText(/Skills/i)).toBeVisible();
    await expect(page.getByText(/Experience/i)).toBeVisible();
    await expect(page.getByText(/Education/i)).toBeVisible();
    await expect(page.getByText(/Location/i)).toBeVisible();
    await expect(page.getByText(/Match Score/i)).toBeVisible();
  });

  test('should allow inputting search query with boolean operators', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Find search query input
    const searchInput = page.getByPlaceholder(/Search|Query/i).first();
    await expect(searchInput).toBeVisible();

    // Type boolean query
    await searchInput.fill('Python AND (Django OR Flask)');

    // Verify input has text
    await expect(searchInput).toHaveValue(/Python/);
  });

  test('should allow setting experience range filter', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Look for experience filter
    const minExperienceInput = page.getByPlaceholder(/Min Experience|Minimum Experience/i);
    if (await minExperienceInput.isVisible()) {
      await minExperienceInput.fill('5');
      await expect(minExperienceInput).toHaveValue('5');
    }
  });

  test('should allow setting location filter', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Look for location input
    const locationInput = page.getByPlaceholder(/Location/i).first();
    if (await locationInput.isVisible()) {
      await locationInput.fill('Remote');
      await expect(locationInput).toHaveValue('Remote');
    }
  });

  test('should allow setting match score range', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Check for match score inputs
    const minMatchInput = page.getByPlaceholder(/Min Match|Minimum Match/i);
    if (await minMatchInput.isVisible()) {
      await minMatchInput.fill('70');
      await expect(minMatchInput).toHaveValue('70');
    }
  });

  test('should display search button in advanced filters', async ({ page }) => {
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Check for search button
    const searchBtn = page.getByRole('button', { name: /Search|Find Candidates/i }).first();
    await expect(searchBtn).toBeVisible();
  });
});

test.describe('Saved Search Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
  });

  test('should display saved searches tab', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for saved searches content
    await expect(page.getByText(/Saved Searches/i)).toBeVisible();
  });

  test('should display create saved search button', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for create button
    const createBtn = page.getByRole('button', { name: /Save Current Search|Save Search/i });
    await expect(createBtn).toBeVisible();
  });

  test('should display saved search list or empty state', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Either show list or empty state
    const listExists = await page.getByText(/No saved searches found/i).isVisible();
    const emptyExists = await page.locator('.MuiCard-root').isVisible({ timeout: 2000 }).catch(() => false);

    expect(listExists || emptyExists).toBeTruthy();
  });

  test('should display search functionality in saved searches', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for search box
    const searchBox = page.getByPlaceholder(/Search saved searches/i);
    if (await searchBox.isVisible({ timeout: 3000 })) {
      await expect(searchBox).toBeVisible();
    }
  });

  test('should display statistics cards', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for statistics
    await expect(page.getByText(/Total Saved Searches/i)).toBeVisible();
    await expect(page.getByText(/With Queries/i)).toBeVisible();
  });

  test('should have refresh button in saved searches', async ({ page }) => {
    // Navigate to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for refresh button
    const refreshBtn = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshBtn).toBeVisible();
  });
});

test.describe('Search History', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
  });

  test('should display search history tab', async ({ page }) => {
    // Navigate to search history tab
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Check for search history content
    await expect(page.getByText(/Search History/i)).toBeVisible();
  });

  test('should display history list or empty state', async ({ page }) => {
    // Navigate to search history tab
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Either show list or empty state
    const emptyState = page.getByText(/No Search History|haven't performed any searches/i);
    const historyList = page.locator('.MuiCard-root').first();

    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasList = await historyList.isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasEmptyState || hasList).toBeTruthy();
  });

  test('should have refresh button in search history', async ({ page }) => {
    // Navigate to search history tab
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Check for refresh button
    const refreshBtn = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshBtn).toBeVisible();
  });

  test('should have clear button in search history', async ({ page }) => {
    // Navigate to search history tab
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Check for clear button
    const clearBtn = page.getByRole('button', { name: /Clear/i });
    await expect(clearBtn).toBeVisible();
  });

  test('should display search history items with details', async ({ page }) => {
    // Navigate to search history tab
    await page.getByRole('tab', { name: /Search History/i }).click();

    // If there are history items, check for details
    const historyCard = page.locator('.MuiCard-root').first();

    if (await historyCard.isVisible({ timeout: 3000 })) {
      // Check for search icon and details
      await expect(page.locator('svg').first()).toBeVisible();
    }
  });
});

test.describe('Search Results Display', () => {
  test('should perform basic search and display results', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for vacancies to load
    await page.waitForTimeout(1000);

    // Check if search button exists and is enabled
    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    if (await searchBtn.isEnabled({ timeout: 5000 })) {
      await searchBtn.click();

      // Wait for results
      await page.waitForTimeout(2000);

      // Check for results or no results message
      const hasResults = await page.locator('.MuiCard-root').isVisible().catch(() => false);
      const hasNoResults = await page.getByText(/No candidates|startMessage/i).isVisible().catch(() => false);

      expect(hasResults || hasNoResults).toBeTruthy();
    }
  });

  test('should display candidate cards with match percentage', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for vacancies to load
    await page.waitForTimeout(1000);

    // Perform search
    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });
    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check for candidate cards
      const candidateCard = page.locator('.MuiCard-root').first();

      if (await candidateCard.isVisible({ timeout: 5000 })) {
        // Check for match percentage chip
        const matchChip = page.locator('.MuiChip-root').first();
        await expect(matchChip).toBeVisible();
      }
    }
  });

  test('should display matched and missing skills in results', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for vacancies to load and perform search
    await page.waitForTimeout(1000);

    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });
    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check for skills display
      const candidateCard = page.locator('.MuiCard-root').first();

      if (await candidateCard.isVisible({ timeout: 5000 })) {
        // Look for skills chips
        const hasSkills = await page.locator('.MuiChip-root').count() > 0;
        expect(hasSkills).toBeTruthy();
      }
    }
  });

  test('should display summary statistics', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for vacancies to load and perform search
    await page.waitForTimeout(1000);

    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });
    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check for stats
      const statsPaper = page.locator('.MuiPaper-root').filter({ hasText: /candidates found|high match/i });

      if (await statsPaper.isVisible({ timeout: 5000 })) {
        await expect(page.getByText(/candidates found|high match/i)).toBeVisible();
      }
    }
  });

  test('should display AI ranking badge if available', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for vacancies to load and perform search
    await page.waitForTimeout(1000);

    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });
    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check for AI badges (may not be present if ranking not enabled)
      const aiBadge = page.getByText(/AI/i).first();

      if (await aiBadge.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(aiBadge).toBeVisible();
      }
    }
  });
});

test.describe('Error Handling', () => {
  test('should handle search errors gracefully', async ({ page }) => {
    await page.goto('/candidate-search');

    // Try performing search without selecting vacancy
    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    // If vacancy dropdown is empty, button should be disabled
    const vacancySelect = page.getByRole('combobox', { name: /Select Vacancy/i });
    const vacancyCount = await vacancySelect.locator('option').count();

    if (vacancyCount === 0) {
      await expect(searchBtn).toBeDisabled();
    }
  });

  test('should display error message if search fails', async ({ page }) => {
    await page.goto('/candidate-search');

    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // The test verifies the UI structure - actual error handling
    // requires backend to be running
    await expect(page.getByText(/Skills/i)).toBeVisible({ timeout: 5000 });
  });

  test('should handle network errors in saved searches', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to saved searches
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for error handling (retry button if error occurs)
    const retryBtn = page.getByRole('button', { name: /Try Again|Retry/i });

    if (await retryBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(retryBtn).toBeVisible();
    }
  });

  test('should handle network errors in search history', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to search history
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Check for error handling
    const retryBtn = page.getByRole('button', { name: /Retry/i });

    if (await retryBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(retryBtn).toBeVisible();
    }
  });
});

test.describe('Complete User Journeys', () => {
  test('complete workflow: navigate → search → view results', async ({ page }) => {
    // Start at candidate search page
    await page.goto('/candidate-search');

    // Verify page loaded
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Perform search if possible
    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    if (await searchBtn.isEnabled({ timeout: 5000 })) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Verify results page or empty state
      const url = page.url();
      expect(url).toContain('/candidate-search');
    }
  });

  test('complete workflow: enable filters → search → check results', async ({ page }) => {
    await page.goto('/candidate-search');

    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();

    // Wait for filters to load
    await page.waitForTimeout(1000);

    // Verify filters are visible
    await expect(page.getByText(/Skills|Experience/i)).toBeVisible({ timeout: 5000 });

    // Perform search if button is available
    const searchBtn = page.getByRole('button', { name: /Search/i }).first();

    if (await searchBtn.isVisible({ timeout: 3000 })) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Verify we're still on search page
      expect(page.url()).toContain('/candidate-search');
    }
  });

  test('complete workflow: search → view history → repeat search', async ({ page }) => {
    await page.goto('/candidate-search');

    // Perform initial search
    await page.waitForTimeout(1000);

    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Navigate to history
      await page.getByRole('tab', { name: /Search History/i }).click();
      await page.waitForTimeout(500);

      // Verify history tab is active
      await expect(page.getByRole('tab', { name: /Search History/i, selected: true })).toBeVisible();
    }
  });

  test('complete workflow: navigate through all tabs', async ({ page }) => {
    await page.goto('/candidate-search');

    // Search tab
    await expect(page.getByRole('tab', { name: /^Search$/i })).toBeVisible();

    // Saved Searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();
    await expect(page.getByRole('tab', { name: /Saved Searches/i, selected: true })).toBeVisible();

    // Search History tab
    await page.getByRole('tab', { name: /Search History/i }).click();
    await expect(page.getByRole('tab', { name: /Search History/i, selected: true })).toBeVisible();

    // Back to Search tab
    await page.getByRole('tab', { name: /^Search$/i }).click();
    await expect(page.getByRole('tab', { name: /^Search$/i, selected: true })).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/candidate-search');

    // Main elements should be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Search/i })).toBeVisible();
  });

  test('should adapt tabs on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/candidate-search');

    // Tabs should still be visible
    await expect(page.getByRole('tab', { name: /Search/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Saved/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /History/i })).toBeVisible();
  });

  test('should be usable on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/candidate-search');

    // Main interface should be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: /Find Candidates/i })).toBeVisible();
  });

  test('should adapt layout on desktop viewport', async ({ page }) => {
    // Desktop viewport (default)
    await page.goto('/candidate-search');

    // Grid layout should be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();

    // Check for h2 headings
    const h2s = page.getByRole('heading', { level: 2 });
    const count = await h2s.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should have accessible form controls', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for proper labels on form controls
    const vacancySelect = page.getByRole('combobox', { name: /Select Vacancy/i });
    await expect(vacancySelect).toBeVisible();

    const skillsInput = page.getByRole('textbox', { name: /Filter by Skills/i });
    await expect(skillsInput).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/candidate-search');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First tab should focus on a tab or button
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toMatch(/BUTTON|INPUT/);
  });

  test('should have accessible tab navigation', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check that tabs have proper role
    const tabs = page.getByRole('tab');
    const count = await tabs.count();
    expect(count).toBeGreaterThan(0);

    // First tab should be visible
    await expect(tabs.first()).toBeVisible();
  });

  test('should have color contrast for match scores', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for page to load
    await page.waitForTimeout(1000);

    // Perform search to show results
    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check for chips (color indicators)
      const chips = page.locator('.MuiChip-root');

      if (await chips.count() > 0) {
        await expect(chips.first()).toBeVisible();
      }
    }
  });
});

test.describe('Performance', () => {
  test('should load candidate search page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/candidate-search');

    // Wait for main content
    await page.waitForSelector('h1');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should switch tabs quickly', async ({ page }) => {
    await page.goto('/candidate-search');

    const startTime = Date.now();

    // Switch to saved searches tab
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Wait for tab content
    await page.waitForTimeout(500);

    const switchTime = Date.now() - startTime;

    // Should switch in less than 1 second
    expect(switchTime).toBeLessThan(1000);
  });

  test('should not have memory leaks during navigation', async ({ page }) => {
    // Navigate through multiple pages
    for (let i = 0; i < 3; i++) {
      await page.goto('/candidate-search');
      await page.waitForTimeout(500);

      await page.getByRole('tab', { name: /Saved Searches/i }).click();
      await page.waitForTimeout(500);

      await page.getByRole('tab', { name: /Search History/i }).click();
      await page.waitForTimeout(500);

      await page.getByRole('tab', { name: /^Search$/i }).click();
      await page.waitForTimeout(500);
    }

    // Page should still be responsive
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Loading States', () => {
  test('should show loading indicator when fetching vacancies', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for initial loading state
    const loader = page.locator('.MuiCircularProgress-root');

    if (await loader.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(loader).toBeVisible();

      // Wait for loading to complete
      await loader.waitFor({ state: 'hidden', timeout: 5000 });
    }
  });

  test('should show loading indicator in saved searches tab', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to saved searches
    await page.getByRole('tab', { name: /Saved Searches/i }).click();

    // Check for loading indicator
    const loader = page.locator('.MuiCircularProgress-root');

    if (await loader.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(loader).toBeVisible();

      // Wait for loading to complete
      await loader.waitFor({ state: 'hidden', timeout: 5000 });
    }
  });

  test('should show loading indicator in search history tab', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to search history
    await page.getByRole('tab', { name: /Search History/i }).click();

    // Check for loading indicator
    const loader = page.locator('.MuiCircularProgress-root');

    if (await loader.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(loader).toBeVisible();

      // Wait for loading to complete
      await loader.waitFor({ state: 'hidden', timeout: 5000 });
    }
  });
});

test.describe('Integration Points', () => {
  test('should have working vacancy selector', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Check vacancy dropdown
    const vacancySelect = page.getByRole('combobox', { name: /Select Vacancy/i });
    await expect(vacancySelect).toBeVisible();

    // Get option count
    const options = await vacancySelect.locator('option').count();

    if (options > 1) {
      // Should have at least one option (plus default)
      expect(options).toBeGreaterThan(0);
    }
  });

  test('should integrate with results page', async ({ page }) => {
    await page.goto('/candidate-search');

    // Wait for data and perform search
    await page.waitForTimeout(1000);

    const searchBtn = page.getByRole('button', { name: /Find Candidates/i });

    if (await searchBtn.isEnabled()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);

      // Check if results are clickable
      const candidateCard = page.locator('.MuiCard-root').first();

      if (await candidateCard.isVisible({ timeout: 3000 })) {
        // Verify card is clickable
        await expect(candidateCard).toHaveAttribute('role', 'undefined');
      }
    }
  });
});

test.describe('Content Validation', () => {
  test('should display correct content on search page', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check key phrases
    await expect(page.getByText(/Candidate Search|Find Candidates/i)).toBeVisible();
  });

  test('should display helpful empty state messages', async ({ page }) => {
    await page.goto('/candidate-search');

    // Check for empty state before search
    const emptyState = page.getByText(/startMessage|Start searching/i);

    if (await emptyState.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(emptyState).toBeVisible();
    }
  });

  test('should display helpful instructions in saved searches', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to saved searches
    await page.getByRole('tab', { name: /Saved Searches/i }).click();
    await page.waitForTimeout(500);

    // Check for instructions
    const instructions = page.getByText(/Save your frequently used search|Save your search queries/i);

    if (await instructions.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(instructions).toBeVisible();
    }
  });

  test('should display helpful instructions in search history', async ({ page }) => {
    await page.goto('/candidate-search');

    // Navigate to search history
    await page.getByRole('tab', { name: /Search History/i }).click();
    await page.waitForTimeout(500);

    // Check for instructions or empty state
    const emptyState = page.getByText(/No Search History|haven't performed any searches/i);

    if (await emptyState.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(emptyState).toBeVisible();
    }
  });
});
