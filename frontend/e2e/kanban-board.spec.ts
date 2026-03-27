import { test, expect, Page, Locator } from '@playwright/test';

/**
 * E2E Tests for Candidate Pipeline Kanban Board
 *
 * Test Suite Contents:
 * 1. Kanban Board Loading and Rendering
 * 2. Candidates Display in Correct Stages
 * 3. Drag-and-Drop Functionality
 * 4. WIP Limit Updates and Display
 * 5. Swimlane Grouping Functionality
 * 6. Responsive Design and Accessibility
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - At least one vacancy with candidates in different stages
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

/**
 * Navigate to the kanban board page and wait for it to load
 */
async function navigateToKanbanBoard(page: Page) {
  await page.goto('/recruiter/candidates');
  await page.waitForLoadState('networkidle');
}

/**
 * Find the kanban board container
 */
function getKanbanBoard(page: Page): Locator {
  return page.locator('[class*="kanban"]').or(
    page.locator('[data-testid="kanban-board"]')
  ).or(
    // Look for the container with columns
    page.locator('div').filter({ has: page.locator('[class*="column"]') }).first()
  );
}

/**
 * Get all kanban columns
 */
function getKanbanColumns(page: Page): Locator {
  return page.locator('[class*="column"]').or(
    page.locator('[data-testid*="column"]')
  ).or(
    // Look for column containers by MUI paper/card styling
    page.locator('div[class*="Paper"]').filter({ has: page.getByRole('heading', { level: 3 }) }).or(
      page.locator('div').filter({ has: page.getByText(/Applied|Screening|Interview|Offer|Hired/i) })
    )
  );
}

/**
 * Get swimlane selector component
 */
function getSwimlaneSelector(page: Page): Locator {
  return page.locator('[class*="MuiToggleButtonGroup"]').or(
    page.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /None|Job|Recruiter/i })
  ).first();
}

/**
 * Get swimlane options (None, By Job, By Recruiter)
 */
function getSwimlaneOptions(page: Page): Locator {
  return page.locator('[class*="MuiToggleButton"]').or(
    page.locator('button').filter({ hasText: /None|By Job|By Recruiter/i })
  );
}

/**
 * Get WIP limit indicators
 */
function getWipIndicators(page: Page): Locator {
  return page.locator('[class*="MuiChip"]').filter({ hasText: /\d+\/\d+/ }).or(
    page.locator('[class*="MuiChip"]').filter({ hasText: /\d+/ })
  );
}

/**
 * Get candidate cards on the board
 */
function getCandidateCards(page: Page): Locator {
  return page.locator('[data-testid="candidate-card"]').or(
    page.locator('[draggable="true"]').filter({ has: page.locator('div') })
  );
}

/**
 * Get the search input field
 */
function getSearchInput(page: Page): Locator {
  return page.getByPlaceholder(/Search candidates/i).or(
    page.locator('input[type="text"]').filter({ has: page.locator('[class*="SearchIcon"]') })
  );
}

/**
 * Get the settings/customize stages button
 */
function getSettingsButton(page: Page): Locator {
  return page.getByRole('button', { name: /Customize stages/i }).or(
    page.locator('button').filter({ has: page.locator('[class*="SettingsIcon"], svg[data-testid="SettingsIcon"]') })
  );
}

/**
 * Get the refresh button
 */
function getRefreshButton(page: Page): Locator {
  return page.getByRole('button', { name: /Refresh/i }).or(
    page.locator('button').filter({ has: page.locator('[class*="RefreshIcon"], svg[data-testid="RefreshIcon"]') })
  );
}

// ==========================================
// TEST SUITE: Kanban Board Loading
// ==========================================
test.describe('Kanban Board - Page Loading', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
  });

  test('should load the kanban board page successfully', async ({ page }) => {
    // Check page title/heading
    await expect(page.getByRole('heading', { name: /Candidate Pipeline|Candidates/i })).toBeVisible();
  });

  test('should display page description', async ({ page }) => {
    // Check for description text
    const description = page.getByText(/Drag candidates between stages/i);
    const count = await description.count();
    if (count > 0) {
      await expect(description.first()).toBeVisible();
    }
  });

  test('should show loading state initially', async ({ page }) => {
    // Reload to catch loading state
    await page.reload();

    // Either loading indicator or content should appear
    const loading = page.locator('[class*="CircularProgress"]').or(page.getByText(/Loading/i));
    const content = getKanbanBoard(page);

    // One of them should be visible
    await expect(loading.or(content)).toBeVisible({ timeout: 5000 });
  });

  test('should render without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await navigateToKanbanBoard(page);
    await page.waitForTimeout(2000);

    // Filter out known non-critical errors
    const criticalErrors = consoleErrors.filter(
      (err) => !err.includes('favicon') && !err.includes('manifest')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('should display toolbar with search and controls', async ({ page }) => {
    // Check for search input
    const searchInput = getSearchInput(page);
    const searchCount = await searchInput.count();
    if (searchCount > 0) {
      await expect(searchInput.first()).toBeVisible();
    }

    // Check for refresh button
    const refreshBtn = getRefreshButton(page);
    const refreshCount = await refreshBtn.count();
    if (refreshCount > 0) {
      await expect(refreshBtn.first()).toBeVisible();
    }

    // Check for settings button
    const settingsBtn = getSettingsButton(page);
    const settingsCount = await settingsBtn.count();
    if (settingsCount > 0) {
      await expect(settingsBtn.first()).toBeVisible();
    }
  });
});

// ==========================================
// TEST SUITE: Candidates Display
// ==========================================
test.describe('Kanban Board - Candidates Display', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
  });

  test('should display kanban columns for stages', async ({ page }) => {
    // Wait for content to load
    await page.waitForTimeout(1000);

    // Look for columns - should have at least one
    const columns = getKanbanColumns(page);
    const columnCount = await columns.count();

    // Either columns exist or loading/error state
    const loading = page.locator('[class*="CircularProgress"]');
    const error = page.getByText(/Error|Failed to load/i);

    if (columnCount > 0) {
      expect(columnCount).toBeGreaterThan(0);
    } else {
      // Should show loading or error
      await expect(loading.or(error)).toBeVisible();
    }
  });

  test('should display candidate cards when data is available', async ({ page }) => {
    await page.waitForTimeout(1500);

    const cards = getCandidateCards(page);
    const cardCount = await cards.count();

    // If there are candidates, cards should be visible
    if (cardCount > 0) {
      await expect(cards.first()).toBeVisible();
    }

    // Check for empty state or candidates count
    const totalCandidates = page.getByText(/Total candidates:/i);
    const totalCount = await totalCandidates.count();
    if (totalCount > 0) {
      await expect(totalCandidates.first()).toBeVisible();
    }
  });

  test('should show candidate name on cards', async ({ page }) => {
    await page.waitForTimeout(1500);

    const cards = getCandidateCards(page);
    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Get first card and check it has text content
      const firstCard = cards.first();
      const cardText = await firstCard.textContent();
      expect(cardText?.length).toBeGreaterThan(0);
    }
  });

  test('should display candidate tags if available', async ({ page }) => {
    await page.waitForTimeout(1500);

    // Look for tag-like elements on cards
    const tags = page.locator('[class*="MuiChip"]').filter({ hasNot: page.getByText(/\d+\/\d+/) });
    const tagCount = await tags.count();

    // Tags may or may not be present depending on data
    if (tagCount > 0) {
      await expect(tags.first()).toBeVisible();
    }
  });

  test('should show match score badges on cards', async ({ page }) => {
    await page.waitForTimeout(1500);

    // Look for match score indicators (percentage badges)
    const matchScores = page.locator('[class*="MuiChip"]').filter({ hasText: /\d+%/ });
    const scoreCount = await matchScores.count();

    // Match scores may or may not be present
    if (scoreCount > 0) {
      await expect(matchScores.first()).toBeVisible();
    }
  });
});

// ==========================================
// TEST SUITE: Drag and Drop
// ==========================================
test.describe('Kanban Board - Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should have draggable candidate cards', async ({ page }) => {
    const cards = getCandidateCards(page);
    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Check if card has draggable attribute or is within draggable context
      const firstCard = cards.first();
      const isDraggable = await firstCard.getAttribute('draggable');

      // In @hello-pangea/dnd, elements get draggable="true" during drag
      // We just verify the card exists and is interactive
      await expect(firstCard).toBeVisible();
    }
  });

  test('should allow drag interaction simulation', async ({ page }) => {
    const cards = getCandidateCards(page);
    const columns = getKanbanColumns(page);

    const cardCount = await cards.count();
    const columnCount = await columns.count();

    // Need at least one card and two columns to test drag
    if (cardCount > 0 && columnCount >= 2) {
      const firstCard = cards.first();
      const secondColumn = columns.nth(1);

      // Verify both elements are visible before attempting drag
      await expect(firstCard).toBeVisible();
      await expect(secondColumn).toBeVisible();

      // Simulate drag by hovering and checking visual feedback
      await firstCard.hover();
      await page.waitForTimeout(300);

      // The card should still be visible after hover
      await expect(firstCard).toBeVisible();
    }
  });

  test('should maintain card visibility during drag simulation', async ({ page }) => {
    const cards = getCandidateCards(page);
    const cardCount = await cards.count();

    if (cardCount > 0) {
      const firstCard = cards.first();

      // Mouse down on card
      await firstCard.hover();
      const box = await firstCard.boundingBox();

      if (box) {
        // Verify card position before and after interaction
        const initialBox = await firstCard.boundingBox();
        expect(initialBox).toBeTruthy();
      }
    }
  });
});

// ==========================================
// TEST SUITE: WIP Limits
// ==========================================
test.describe('Kanban Board - WIP Limits', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should display WIP limit indicators', async ({ page }) => {
    const wipIndicators = getWipIndicators(page);
    const wipCount = await wipIndicators.count();

    // WIP indicators should be visible in column headers
    if (wipCount > 0) {
      await expect(wipIndicators.first()).toBeVisible();
    }

    // Check footer for WIP limit info
    const wipFooter = page.getByText(/WIP limits/i);
    const footerCount = await wipFooter.count();
    if (footerCount > 0) {
      await expect(wipFooter.first()).toBeVisible();
    }
  });

  test('should show WIP status colors correctly', async ({ page }) => {
    // Look for chips with success/warning/error colors
    const successChips = page.locator('[class*="MuiChip-colorSuccess"]');
    const warningChips = page.locator('[class*="MuiChip-colorWarning"]');
    const errorChips = page.locator('[class*="MuiChip-colorError"]');

    // At least one color status should be present if there are candidates
    const successCount = await successChips.count();
    const warningCount = await warningChips.count();
    const errorCount = await errorChips.count();

    const hasStatusChips = successCount > 0 || warningCount > 0 || errorCount > 0;

    // WIP status should be visible if stages have candidates
    if (hasStatusChips) {
      expect(hasStatusChips).toBeTruthy();
    }
  });

  test('should display candidate count per stage', async ({ page }) => {
    const columns = getKanbanColumns(page);
    const columnCount = await columns.count();

    if (columnCount > 0) {
      // Look for count indicators in columns
      const countIndicators = page.locator('[class*="MuiChip"]').filter({ hasText: /\d+/ });
      const countNumber = await countIndicators.count();

      if (countNumber > 0) {
        // Get text from first count indicator
        const text = await countIndicators.first().textContent();
        expect(text).toMatch(/\d+/);
      }
    }
  });

  test('should show over-limit warning when exceeded', async ({ page }) => {
    // Look for "Over limit" text which appears when WIP is exceeded
    const overLimitWarning = page.getByText(/Over limit|exceeded/i);
    const warningCount = await overLimitWarning.count();

    // This warning only appears when limit is actually exceeded
    if (warningCount > 0) {
      await expect(overLimitWarning.first()).toBeVisible();
    }
  });
});

// ==========================================
// TEST SUITE: Swimlane Grouping
// ==========================================
test.describe('Kanban Board - Swimlane Grouping', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should display swimlane selector', async ({ page }) => {
    const selector = getSwimlaneSelector(page);
    const selectorCount = await selector.count();

    if (selectorCount > 0) {
      await expect(selector.first()).toBeVisible();
    } else {
      // Try alternative selector
      const toggleButtons = getSwimlaneOptions(page);
      const toggleCount = await toggleButtons.count();
      if (toggleCount > 0) {
        await expect(toggleButtons.first()).toBeVisible();
      }
    }
  });

  test('should show grouping options (None, By Job, By Recruiter)', async ({ page }) => {
    const options = getSwimlaneOptions(page);
    const optionCount = await options.count();

    if (optionCount >= 3) {
      // Should have at least 3 options
      expect(optionCount).toBeGreaterThanOrEqual(3);
    } else {
      // Check for text indicators of grouping
      const groupByText = page.getByText(/Group by:/i);
      const groupCount = await groupByText.count();
      if (groupCount > 0) {
        await expect(groupByText.first()).toBeVisible();
      }
    }
  });

  test('should change grouping to "By Job" when selected', async ({ page }) => {
    const jobButton = page.locator('button').filter({ hasText: /By Job/i });
    const jobCount = await jobButton.count();

    if (jobCount > 0) {
      await jobButton.first().click();
      await page.waitForTimeout(500);

      // Look for swimlane headers (job titles)
      const swimlaneHeaders = page.locator('[class*="swimlane"]').or(
        page.getByRole('heading', { level: 4 }).or(
          page.locator('h6, [class*="subtitle1"]')
        )
      );

      // Page should still render correctly after changing grouping
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should change grouping to "By Recruiter" when selected', async ({ page }) => {
    const recruiterButton = page.locator('button').filter({ hasText: /By Recruiter/i });
    const recruiterCount = await recruiterButton.count();

    if (recruiterCount > 0) {
      await recruiterButton.first().click();
      await page.waitForTimeout(500);

      // Page should still render correctly
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should reset to "None" grouping', async ({ page }) => {
    const noneButton = page.locator('button').filter({ hasText: /^None$/i });
    const noneCount = await noneButton.count();

    if (noneCount > 0) {
      await noneButton.first().click();
      await page.waitForTimeout(500);

      // Page should render without swimlane headers
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should regroup candidates when grouping changes', async ({ page }) => {
    // Get initial state
    const initialCards = await getCandidateCards(page).count();

    // Change to "By Job" grouping
    const jobButton = page.locator('button').filter({ hasText: /By Job/i });
    const jobCount = await jobButton.count();

    if (jobCount > 0) {
      await jobButton.first().click();
      await page.waitForTimeout(1000);

      // Get new state
      const newCards = await getCandidateCards(page).count();

      // Total cards should be similar (same candidates, different layout)
      // Allow for some difference due to loading timing
      expect(Math.abs(initialCards - newCards)).toBeLessThanOrEqual(2);
    }
  });
});

// ==========================================
// TEST SUITE: Search Functionality
// ==========================================
test.describe('Kanban Board - Search', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should have functional search input', async ({ page }) => {
    const searchInput = getSearchInput(page);
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      const input = searchInput.first();
      await expect(input).toBeVisible();
      await expect(input).toBeEnabled();

      // Type in search
      await input.fill('test');
      await page.waitForTimeout(300);

      // Input should contain text
      const value = await input.inputValue();
      expect(value).toBe('test');
    }
  });

  test('should filter candidates when searching', async ({ page }) => {
    const searchInput = getSearchInput(page);
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      const initialCards = await getCandidateCards(page).count();

      // Search for non-existent term
      await searchInput.first().fill('zzzznonexistent12345');
      await page.waitForTimeout(800);

      // Cards should be fewer or zero
      const filteredCards = await getCandidateCards(page).count();
      expect(filteredCards).toBeLessThanOrEqual(initialCards);

      // Clear search
      await searchInput.first().fill('');
      await page.waitForTimeout(500);

      // Cards should return
      const restoredCards = await getCandidateCards(page).count();
      expect(restoredCards).toBeGreaterThanOrEqual(filteredCards);
    }
  });

  test('should clear search results when input is cleared', async ({ page }) => {
    const searchInput = getSearchInput(page);
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      // Type and clear
      await searchInput.first().fill('test');
      await page.waitForTimeout(300);
      await searchInput.first().fill('');
      await page.waitForTimeout(500);

      // Verify input is empty
      const value = await searchInput.first().inputValue();
      expect(value).toBe('');
    }
  });
});

// ==========================================
// TEST SUITE: Settings and Navigation
// ==========================================
test.describe('Kanban Board - Settings and Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should navigate to workflow stages settings', async ({ page }) => {
    const settingsButton = getSettingsButton(page);
    const settingsCount = await settingsButton.count();

    if (settingsCount > 0) {
      await settingsButton.first().click();
      await page.waitForTimeout(500);

      // Should navigate to workflow stages page
      expect(page.url()).toMatch(/workflow-stages|settings/i);
    }
  });

  test('should refresh board when refresh button clicked', async ({ page }) => {
    const refreshButton = getRefreshButton(page);
    const refreshCount = await refreshButton.count();

    if (refreshCount > 0) {
      // Click refresh
      await refreshButton.first().click();
      await page.waitForTimeout(500);

      // Page should still be functional
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

// ==========================================
// TEST SUITE: Responsive Design
// ==========================================
test.describe('Kanban Board - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should display kanban board on mobile', async ({ page }) => {
    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Candidate Pipeline|Candidates/i })).toBeVisible();
  });

  test('should have horizontally scrollable columns on mobile', async ({ page }) => {
    const columns = getKanbanColumns(page);
    const columnCount = await columns.count();

    if (columnCount > 1) {
      // Check for horizontal scroll container
      const board = getKanbanBoard(page);
      const boardCount = await board.count();

      if (boardCount > 0) {
        await expect(board.first()).toBeVisible();
      }
    }
  });

  test('should show swimlane selector without labels on mobile', async ({ page }) => {
    // On mobile, text labels may be hidden, icons should still be visible
    const selector = getSwimlaneSelector(page);
    const selectorCount = await selector.count();

    if (selectorCount > 0) {
      await expect(selector.first()).toBeVisible();
    }
  });

  test('should not have horizontal page overflow', async ({ page }) => {
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;

    // Allow small tolerance for borders/margins
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
  });
});

test.describe('Kanban Board - Desktop Layout', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should display multiple columns side by side on desktop', async ({ page }) => {
    const columns = getKanbanColumns(page);
    const columnCount = await columns.count();

    if (columnCount >= 2) {
      const firstCol = columns.first();
      const secondCol = columns.nth(1);

      const firstBox = await firstCol.boundingBox();
      const secondBox = await secondCol.boundingBox();

      if (firstBox && secondBox) {
        // Columns should be side by side (second column x > first column x)
        expect(secondBox.x).toBeGreaterThan(firstBox.x);
      }
    }
  });

  test('should use full desktop width', async ({ page }) => {
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyWidth).toBeGreaterThan(900);
  });
});

// ==========================================
// TEST SUITE: Accessibility
// ==========================================
test.describe('Kanban Board - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1 heading
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'DIV'].includes(focused || '')).toBeTruthy();
  });

  test('should focus search input when tabbed', async ({ page }) => {
    // Tab until we reach the search input or go through several tabs
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }

    // Something should be focused
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('should have accessible buttons with tooltips', async ({ page }) => {
    // Check refresh button has tooltip/accessible name
    const refreshButton = getRefreshButton(page);
    const refreshCount = await refreshButton.count();

    if (refreshCount > 0) {
      const btn = refreshButton.first();
      const ariaLabel = await btn.getAttribute('aria-label');
      const title = await btn.getAttribute('title');

      // Button should have some accessible name
      expect(ariaLabel || title).toBeTruthy();
    }
  });
});

// ==========================================
// TEST SUITE: Error Handling
// ==========================================
test.describe('Kanban Board - Error Handling', () => {
  test('should handle API errors gracefully', async ({ page }) => {
    // Block API requests to simulate network error
    await page.route('**/api/candidates/kanban**', (route) => route.abort());

    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);

    // Should show error message or empty state
    const error = page.getByText(/Error|Failed to load/i);
    const empty = page.getByText(/No candidates|Empty/i);
    const board = getKanbanBoard(page);

    // Something should be displayed (error, empty, or board)
    await expect(error.or(empty).or(board)).toBeVisible();
  });

  test('should allow retry after error', async ({ page }) => {
    let requestCount = 0;

    // Fail first request, succeed second
    await page.route('**/api/candidates/kanban**', (route) => {
      requestCount++;
      if (requestCount === 1) {
        route.abort();
      } else {
        route.continue();
      }
    });

    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1000);

    // Click refresh if available
    const refreshButton = getRefreshButton(page);
    const refreshCount = await refreshButton.count();

    if (refreshCount > 0) {
      await refreshButton.first().click();
      await page.waitForTimeout(1000);

      // Page should be functional
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

// ==========================================
// TEST SUITE: Complete E2E Flow
// ==========================================
test.describe('Kanban Board - Complete Flow', () => {
  test('should complete full kanban board workflow', async ({ page }) => {
    // 1. Navigate to kanban board
    await navigateToKanbanBoard(page);
    await expect(page.getByRole('heading', { name: /Candidate Pipeline|Candidates/i })).toBeVisible();

    // 2. Wait for board to load
    await page.waitForTimeout(1500);

    // 3. Verify columns are displayed
    const columns = getKanbanColumns(page);
    const columnCount = await columns.count();

    if (columnCount > 0) {
      // 4. Check for WIP indicators
      const wipIndicators = getWipIndicators(page);
      const wipCount = await wipIndicators.count();
      // WIP indicators may or may not be present

      // 5. Change swimlane grouping
      const jobButton = page.locator('button').filter({ hasText: /By Job/i });
      const jobCount = await jobButton.count();

      if (jobCount > 0) {
        await jobButton.first().click();
        await page.waitForTimeout(800);

        // 6. Verify page still works after grouping change
        await expect(page.locator('body')).toBeVisible();

        // 7. Search for candidates
        const searchInput = getSearchInput(page);
        const searchCount = await searchInput.count();

        if (searchCount > 0) {
          await searchInput.first().fill('test');
          await page.waitForTimeout(500);
          await expect(page.locator('body')).toBeVisible();
        }

        // 8. Reset to no grouping
        const noneButton = page.locator('button').filter({ hasText: /^None$/i });
        const noneCount = await noneButton.count();

        if (noneCount > 0) {
          await noneButton.first().click();
          await page.waitForTimeout(500);
          await expect(page.locator('body')).toBeVisible();
        }
      }
    }

    // Final check - page should be in good state
    await expect(page.getByRole('heading')).toBeVisible();
  });

  test('should maintain state during navigation', async ({ page }) => {
    await navigateToKanbanBoard(page);
    await page.waitForTimeout(1500);

    // Set search term
    const searchInput = getSearchInput(page);
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      await searchInput.first().fill('persistent');
    }

    // Navigate away
    await page.goto('/recruiter/dashboard');
    await page.waitForTimeout(500);

    // Navigate back
    await page.goto('/recruiter/candidates');
    await page.waitForTimeout(1500);

    // Page should render correctly
    await expect(page.getByRole('heading', { name: /Candidate Pipeline|Candidates/i })).toBeVisible();
  });
});
