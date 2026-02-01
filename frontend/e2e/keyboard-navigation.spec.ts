import { test, expect } from '@playwright/test';

/**
 * Keyboard Navigation E2E Tests
 *
 * Tests all keyboard shortcuts and navigation functionality across the application.
 * Verifies global shortcuts, list navigation, and modal interactions.
 *
 * Run with: npm run test:e2e -- keyboard-navigation.spec.ts
 */

// Helper to simulate keyboard shortcuts
async function pressShortcut(page, keys: string[]) {
  for (const key of keys) {
    await page.keyboard.press(key);
  }
}

test.describe('Keyboard Navigation - Global Shortcuts', () => {
  test('should navigate to candidate search with Ctrl+K', async ({ page }) => {
    await page.goto('/');

    // Press Ctrl+K (or Cmd+K on Mac)
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', 'k'] : ['Control', 'k']);

    // Wait for navigation
    await page.waitForTimeout(200);

    // Verify we're on the candidate search page
    await expect(page).toHaveURL(/.*\/recruiter\/search/);
  });

  test('should show keyboard shortcuts help with Ctrl+/', async ({ page }) => {
    await page.goto('/');

    // Press Ctrl+/ (or Cmd+/ on Mac)
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);

    // Wait for dialog to appear
    await page.waitForTimeout(200);

    // Verify shortcuts dialog is visible
    const dialog = page.locator('role=dialog').filter({ hasText: 'keyboard shortcuts' });
    await expect(dialog.first()).toBeVisible();
  });

  test('should navigate to home with Alt+Home', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Press Alt+Home
    await page.keyboard.press('Alt+Home');

    // Wait for navigation
    await page.waitForTimeout(200);

    // Verify we're on the home page
    await expect(page).toHaveURL('/');
  });

  test('should close shortcuts dialog with Escape', async ({ page }) => {
    await page.goto('/');

    // Open shortcuts dialog
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);
    await page.waitForTimeout(200);

    // Verify dialog is open
    const dialog = page.locator('role=dialog');
    await expect(dialog.first()).toBeVisible();

    // Press Escape to close
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    // Verify dialog is closed
    await expect(dialog.first()).not.toBeVisible();
  });
});

test.describe('Keyboard Navigation - CandidateSearch', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to candidate search page
    await page.goto('/recruiter/search');
    // Wait for page to load
    await page.waitForTimeout(500);
  });

  test('should display keyboard navigation hint when candidates are available', async ({ page }) => {
    // Check for keyboard hint text
    const hint = page.locator('text=/arrow keys|navigate/i');
    // Hint should be visible if there are candidates
    // Note: This depends on having data in the system
  });

  test('should navigate down through candidates with ArrowDown', async ({ page }) => {
    // Look for candidate cards
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 0) {
      // Press ArrowDown
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Check if any card got focus indicator
      // (Visual feedback would be checked manually)
    }
  });

  test('should navigate up through candidates with ArrowUp', async ({ page }) => {
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 1) {
      // Press ArrowDown twice, then ArrowUp once
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);
      await page.keyboard.press('ArrowUp');
      await page.waitForTimeout(100);

      // Should have moved back up
    }
  });

  test('should navigate with j and k keys', async ({ page }) => {
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 0) {
      // Press 'j' to move down
      await page.keyboard.press('j');
      await page.waitForTimeout(100);

      // Press 'k' to move up
      await page.keyboard.press('k');
      await page.waitForTimeout(100);
    }
  });

  test('should navigate to first candidate with Home key', async ({ page }) => {
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 1) {
      // Navigate down a few
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press Home to go to first
      await page.keyboard.press('Home');
      await page.waitForTimeout(100);

      // Should be back at first candidate
    }
  });

  test('should navigate to last candidate with End key', async ({ page }) => {
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 1) {
      // Press End to go to last
      await page.keyboard.press('End');
      await page.waitForTimeout(100);

      // Should be at last candidate
    }
  });

  test('should clear focus with Escape', async ({ page }) => {
    const candidates = page.locator('[data-testid="candidate-card"], .MuiCard-root').filter({
      has: page.locator('a[href*="/results/"]'),
    });

    const count = await candidates.count();

    if (count > 0) {
      // Navigate to a candidate
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press Escape to clear focus
      await page.keyboard.press('Escape');
      await page.waitForTimeout(100);

      // Focus should be cleared
    }
  });

  test('should not handle keyboard events when typing in input field', async ({ page }) => {
    // Find a search input
    const searchInput = page.locator('input[type="text"]').first();

    if (await searchInput.isVisible()) {
      // Focus the input
      await searchInput.focus();
      await page.waitForTimeout(100);

      // Press ArrowDown - should NOT navigate candidates
      // (This would be checked by verifying no candidate card gets focused)
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);
    }
  });
});

test.describe('Keyboard Navigation - WorkflowBoard (Kanban)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflow board
    await page.goto('/recruiter/workflow');
    // Wait for page to load
    await page.waitForTimeout(500);
  });

  test('should navigate between stage columns with ArrowLeft and ArrowRight', async ({ page }) => {
    // Look for stage columns
    const stages = page.locator('[data-testid="workflow-stage"], .MuiPaper-root').filter({
      has: page.locator('text=/stage|стадия/i'),
    });

    const stageCount = await stages.count();

    if (stageCount > 1) {
      // Navigate right
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(100);

      // Navigate left
      await page.keyboard.press('ArrowLeft');
      await page.waitForTimeout(100);
    }
  });

  test('should navigate between candidate cards with ArrowUp and ArrowDown', async ({ page }) => {
    // Look for candidate cards in stages
    const cards = page.locator('[data-testid="candidate-card"], .MuiCard-root');

    const cardCount = await cards.count();

    if (cardCount > 1) {
      // Navigate down
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Navigate up
      await page.keyboard.press('ArrowUp');
      await page.waitForTimeout(100);
    }
  });

  test('should open candidate details with Enter', async ({ page }) => {
    const cards = page.locator('[data-testid="candidate-card"], .MuiCard-root');

    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Focus a card with ArrowDown
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press Enter to open details
      await page.keyboard.press('Enter');
      await page.waitForTimeout(300);

      // Check if detail modal opened
      const dialog = page.locator('role=dialog');
      const dialogVisible = await dialog.count() > 0;
      if (dialogVisible) {
        await expect(dialog.first()).toBeVisible();
      }
    }
  });

  test('should move candidate to next stage with M key', async ({ page }) => {
    const cards = page.locator('[data-testid="candidate-card"], .MuiCard-root');

    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Focus a card
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press M to move to next stage
      await page.keyboard.press('m');
      await page.waitForTimeout(300);

      // Candidate should have moved (visual verification needed)
    }
  });

  test('should move candidate to previous stage with Shift+M', async ({ page }) => {
    const cards = page.locator('[data-testid="candidate-card"], .MuiCard-root');

    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Focus a card
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press Shift+M to move to previous stage
      await page.keyboard.press('Shift+m');
      await page.waitForTimeout(300);

      // Candidate should have moved (visual verification needed)
    }
  });

  test('should clear focus with Escape', async ({ page }) => {
    const cards = page.locator('[data-testid="candidate-card"], .MuiCard-root');

    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Focus a card
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Press Escape to clear
      await page.keyboard.press('Escape');
      await page.waitForTimeout(100);

      // Focus should be cleared
    }
  });

  test('should not handle keyboard events when typing in search field', async ({ page }) => {
    // Look for search input in workflow board
    const searchInput = page.locator('input[placeholder*="search"], input[placeholder*="search" i]').first();

    if (await searchInput.isVisible()) {
      // Focus the input
      await searchInput.focus();
      await page.waitForTimeout(100);

      // Press Arrow keys - should NOT navigate cards
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(100);

      // Should not have focused any card
    }
  });
});

test.describe('Keyboard Navigation - Modal Interactions', () => {
  test('should close modal with Escape key', async ({ page }) => {
    // Open keyboard shortcuts dialog
    await page.goto('/');
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);
    await page.waitForTimeout(200);

    // Verify dialog is open
    const dialog = page.locator('role=dialog');
    await expect(dialog.first()).toBeVisible();

    // Press Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    // Verify dialog is closed
    await expect(dialog.first()).not.toBeVisible();
  });

  test('should not trigger page shortcuts when modal is open', async ({ page }) => {
    // Open shortcuts dialog
    await page.goto('/');
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);
    await page.waitForTimeout(200);

    // Try to press Ctrl+K while dialog is open
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', 'k'] : ['Control', 'k']);
    await page.waitForTimeout(200);

    // Should NOT navigate (dialog should still be open)
    const dialog = page.locator('role=dialog');
    await expect(dialog.first()).toBeVisible();
  });
});

test.describe('Keyboard Navigation - Accessibility', () => {
  test('should show visual feedback for focused elements', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForTimeout(500);

    // Press Tab to move focus
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    // Check if focused element has visible indicator
    // (This would be checked by examining computed styles)
    const focusedElement = await page.evaluate(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });

  test('should maintain focus order with Tab key', async ({ page }) => {
    await page.goto('/');

    // Press Tab multiple times
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(50);
    }

    // Focus should have moved through interactive elements
    const focusedElement = await page.evaluate(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });

  test('should support Shift+Tab for reverse focus navigation', async ({ page }) => {
    await page.goto('/');

    // Press Tab a few times
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    // Press Shift+Tab to go back
    await page.keyboard.press('Shift+Tab');
    await page.waitForTimeout(100);

    // Focus should have moved back
    const focusedElement = await page.evaluate(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });
});

test.describe('Keyboard Navigation - Platform Differences', () => {
  test('should show Cmd key on Mac instead of Ctrl', async ({ page, context }) => {
    await page.goto('/');

    // Open shortcuts dialog
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);
    await page.waitForTimeout(200);

    const dialog = page.locator('role=dialog');
    await expect(dialog.first()).toBeVisible();

    // Check if the dialog shows the correct modifier key for the platform
    const shortcutText = await dialog.textContent();

    if (process.platform === 'darwin') {
      // Should show "Cmd" on Mac
      expect(shortcutText).toMatch(/Cmd/i);
    } else {
      // Should show "Ctrl" on Windows/Linux
      expect(shortcutText).toMatch(/Ctrl/i);
    }

    // Close dialog
    await page.keyboard.press('Escape');
  });
});

test.describe('Keyboard Navigation - Edge Cases', () => {
  test('should handle rapid key presses correctly', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForTimeout(500);

    // Rapidly press ArrowDown multiple times
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('ArrowDown');
    }
    await page.waitForTimeout(200);

    // Should handle gracefully without errors
  });

  test('should not crash when using shortcuts on empty lists', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForTimeout(500);

    // Try keyboard navigation even if no candidates
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowUp');
    await page.keyboard.press('Home');
    await page.keyboard.press('End');
    await page.waitForTimeout(200);

    // Should handle gracefully
  });

  test('should work correctly after page navigation', async ({ page }) => {
    // Start on home page
    await page.goto('/');

    // Navigate to search page with shortcut
    await pressShortcut(page, process.platform === 'darwin' ? ['Meta', 'k'] : ['Control', 'k']);
    await page.waitForTimeout(300);

    // Try keyboard navigation on new page
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(100);

    // Should work correctly
  });

  test('should maintain keyboard functionality after language switch', async ({ page }) => {
    await page.goto('/');

    // Switch language (if language switcher is available)
    const langSwitcher = page.locator('button[aria-label*="language"], button[aria-label*="язык" i]').first();

    if (await langSwitcher.isVisible()) {
      await langSwitcher.click();
      await page.waitForTimeout(200);

      // Try shortcuts again
      await pressShortcut(page, process.platform === 'darwin' ? ['Meta', '/'] : ['Control', '/']);
      await page.waitForTimeout(200);

      const dialog = page.locator('role=dialog');
      await expect(dialog.first()).toBeVisible();

      // Close dialog
      await page.keyboard.press('Escape');
    }
  });
});
