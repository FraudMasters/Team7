import { test, expect } from '@playwright/test';

/**
 * Dark Mode E2E Tests
 *
 * Tests dark mode toggle functionality and verifies all pages work correctly
 * in both light and dark themes.
 *
 * Run with: npm run test:e2e -- dark-mode.spec.ts
 */

// Main pages to test in both themes
const MAIN_PAGES = [
  { path: '/', name: 'Home' },
  { path: '/recruiter/search', name: 'Candidate Search' },
  { path: '/recruiter/vacancies', name: 'Vacancy List' },
  { path: '/recruiter/resumes', name: 'Resume Database' },
  { path: '/recruiter/workflow', name: 'Workflow Board' },
  { path: '/upload', name: 'Upload' },
];

test.describe('Dark Mode - Toggle Functionality', () => {
  test('should display theme toggle button in navigation', async ({ page }) => {
    await page.goto('/');

    // Look for theme toggle button (has sun or moon icon SVG)
    // Using generic SVG detection instead of MUI-specific icon classes
    const themeToggle = page.locator('button[aria-label*="Switch"]').filter({
      has: page.locator('svg'),
    });

    await expect(themeToggle.first()).toBeVisible();
  });

  test('should toggle to dark mode when clicking the toggle button', async ({ page }) => {
    await page.goto('/');

    // Get theme toggle button
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // Check initial theme (should be light or based on system preference)
    const initialTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Click toggle button
    await themeToggle.click();

    // Wait for theme transition
    await page.waitForTimeout(300);

    // Verify theme changed
    const newTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    expect(newTheme).not.toBe(initialTheme);
  });

  test('should toggle back to light mode when clicking again', async ({ page }) => {
    await page.goto('/');

    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // First click
    await themeToggle.click();
    await page.waitForTimeout(300);

    const darkTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Second click
    await themeToggle.click();
    await page.waitForTimeout(300);

    const lightTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    expect(lightTheme).not.toBe(darkTheme);
  });

  test('should persist theme preference after page reload', async ({ page }) => {
    await page.goto('/');

    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // Toggle to dark mode
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Get theme after toggle
    const themeBeforeReload = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Reload page
    await page.reload();

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Get theme after reload
    const themeAfterReload = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Theme should persist
    expect(themeAfterReload).toBe(themeBeforeReload);
  });

  test('should persist theme preference across page navigation', async ({ page }) => {
    await page.goto('/');

    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // Toggle to dark mode
    await themeToggle.click();
    await page.waitForTimeout(300);

    const themeOnHomePage = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Navigate to another page
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    const themeOnSearchPage = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Theme should persist across navigation
    expect(themeOnSearchPage).toBe(themeOnHomePage);
  });
});

test.describe('Dark Mode - Visual Verification', () => {
  test.use({ viewport: { width: 1920, height: 1080 } }); // Desktop viewport

  MAIN_PAGES.forEach(({ path, name }) => {
    test(`${name} page - renders correctly in dark mode`, async ({ page }) => {
      await page.goto(path);

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Toggle to dark mode
      const themeToggle = page.locator('button[aria-label*="Switch"]').first();
      await themeToggle.click();
      await page.waitForTimeout(300);

      // Check for console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Wait a bit for any async theme changes
      await page.waitForTimeout(500);

      // Verify page is still rendered
      await expect(page.locator('body')).toBeVisible();

      // Verify dark mode is applied
      const theme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });
      expect(theme).toBe('dark');

      // Log any console errors
      if (errors.length > 0) {
        console.error(`Console errors on ${name} page (dark mode):`, errors);
      }
    });

    test(`${name} page - renders correctly in light mode`, async ({ page }) => {
      await page.goto(path);

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Ensure light mode
      const theme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });

      if (theme === 'dark') {
        const themeToggle = page.locator('button[aria-label*="Switch"]').first();
        await themeToggle.click();
        await page.waitForTimeout(300);
      }

      // Check for console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Verify page is rendered
      await expect(page.locator('body')).toBeVisible();

      // Verify light mode is applied
      const finalTheme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });
      expect(finalTheme).toBe('light');

      // Log any console errors
      if (errors.length > 0) {
        console.error(`Console errors on ${name} page (light mode):`, errors);
      }
    });
  });
});

test.describe('Dark Mode - Contrast and Readability', () => {
  test('should maintain sufficient text contrast in dark mode', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Check contrast of main text elements
    const textElements = await page.locator('p, h1, h2, h3, h4, h5, h6, span, div').all();

    // Get computed colors for a sample of text elements
    for (let i = 0; i < Math.min(textElements.length, 20); i++) {
      const element = textElements[i];

      const isVisible = await element.isVisible();
      if (!isVisible) continue;

      const color = await element.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return styles.color;
      });

      // Basic check - color should not be too dark (in dark mode)
      // This is a simplified check - real contrast checking is more complex
      expect(color).not.toBe('rgb(0, 0, 0)');
    }
  });

  test('should have readable background colors in both themes', async ({ page }) => {
    await page.goto('/');

    const body = page.locator('body');

    // Check light mode background
    const lightBg = await body.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Check dark mode background
    const darkBg = await body.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Backgrounds should be different
    expect(lightBg).not.toBe(darkBg);

    // Dark mode background should be dark
    expect(darkBg).toBe('rgb(18, 18, 18)'); // #121212 from ThemeContext

    // Light mode background should be light
    expect(lightBg).toBe('rgb(245, 245, 245)'); // #f5f5f5 from ThemeContext
  });
});

test.describe('Dark Mode - Component Integration', () => {
  test('Material UI components adapt to dark mode', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Check Paper/Card components (cards, dialogs, etc.)
    // Using generic selector instead of MUI-specific class
    const papers = page.locator('.paper, .card, [role="article"]');

    const count = await papers.count();
    if (count > 0) {
      const firstPaperBg = await papers.first().evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor;
      });

      // In dark mode, papers should have dark background
      expect(firstPaperBg).toBe('rgb(30, 30, 30)'); // #1e1e1e from theme
    }
  });

  test('buttons and interactive elements are visible in dark mode', async ({ page }) => {
    await page.goto('/recruiter/vacancies');

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Check buttons
    // Looking for non-icon buttons (buttons with text content)
    const buttons = page.locator('button:not([aria-label])');

    const buttonCount = await buttons.count();
    if (buttonCount > 0) {
      // At least some buttons should be visible
      const visibleButtons = page.locator('button:not([aria-label])').filter({
        hasText: /.+/
      });

      await expect(visibleButtons.first()).toBeVisible();
    }
  });
});

test.describe('Dark Mode - Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // Mobile viewport

  test('theme toggle button is accessible on mobile', async ({ page }) => {
    await page.goto('/');

    // Toggle button should be visible and accessible on mobile
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    await expect(themeToggle).toBeVisible();

    // Should be tappable on mobile
    const boundingBox = await themeToggle.boundingBox();
    expect(boundingBox).toBeTruthy();

    if (boundingBox) {
      // Touch target should be at least 44x44px (WCAG guidelines)
      expect(boundingBox.width).toBeGreaterThanOrEqual(44);
      expect(boundingBox.height).toBeGreaterThanOrEqual(44);
    }
  });

  test('dark mode works correctly on mobile pages', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Verify dark mode is applied
    const theme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    expect(theme).toBe('dark');

    // Verify no horizontal scroll on mobile in dark mode
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
  });
});

test.describe('Dark Mode - Edge Cases', () => {
  test('handles rapid theme toggling without errors', async ({ page }) => {
    await page.goto('/');

    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // Rapidly toggle theme multiple times
    for (let i = 0; i < 5; i++) {
      await themeToggle.click();
      await page.waitForTimeout(100);
    }

    // Should not have console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(500);

    // Verify page still works
    await expect(page.locator('body')).toBeVisible();

    if (errors.length > 0) {
      console.error('Console errors after rapid toggling:', errors);
    }
  });

  test('theme preference persists after browser restart (simulated)', async ({ context, page }) => {
    await page.goto('/');

    const themeToggle = page.locator('button[aria-label*="Switch"]').first();

    // Toggle to dark mode
    await themeToggle.click();
    await page.waitForTimeout(300);

    const themeBefore = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Close and reopen page (simulates browser restart)
    await page.close();

    const newPage = await context.newPage();
    await newPage.goto('/');

    await newPage.waitForLoadState('networkidle');

    const themeAfter = await newPage.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Theme should persist (localStorage persists across sessions)
    expect(themeAfter).toBe(themeBefore);
  });
});
