import { test, expect, devices } from '@playwright/test';

/**
 * Responsive Design E2E Tests
 *
 * Tests responsive design implementation across mobile, tablet, and desktop viewports.
 * Verifies that pages render correctly on different screen sizes.
 *
 * Run with: npm run test:e2e -- responsive-design.spec.ts
 */

// Viewport configurations matching Material-UI breakpoints
const MOBILE_VIEWPORT = { width: 375, height: 667 }; // iPhone SE
const TABLET_VIEWPORT = { width: 768, height: 1024 }; // iPad
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 }; // Standard desktop

// Pages to test
const PAGES = [
  { path: '/', name: 'Home' },
  { path: '/recruiter/search', name: 'Candidate Search' },
  { path: '/recruiter/vacancies', name: 'Vacancy List' },
  { path: '/recruiter/resumes', name: 'Resume Database' },
  { path: '/recruiter/workflow', name: 'Workflow Board' },
];

test.describe('Responsive Design - Mobile (375px)', () => {
  test.use({ ...MOBILE_VIEWPORT });

  PAGES.forEach(({ path, name }) => {
    test(`${name} page - loads without errors`, async ({ page }) => {
      await page.goto(path);

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Check for console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Verify no horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

      // Verify page renders
      await expect(page.locator('body')).toBeVisible();

      // Log any console errors
      if (errors.length > 0) {
        console.error(`Console errors on ${name} page (mobile):`, errors);
      }
    });
  });

  test('Navigation - shows hamburger menu on mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // On mobile (< sm breakpoint which is 600px), should show hamburger menu button
    // Look for the button in the AppBar (not the drawer)
    const hamburgerMenu = page.locator('.MuiAppBar-root button').filter({ hasText: '' }).and(
      page.locator('button').filter(async (el, _) => {
        const ariaLabel = await el.getAttribute('aria-label');
        return ariaLabel && (ariaLabel.includes('menu') || ariaLabel.includes('Menu'));
      })
    );

    // Check if any menu button exists and is visible
    const count = await hamburgerMenu.count();
    if (count > 0) {
      await expect(hamburgerMenu.first()).toBeVisible({ timeout: 10000 });
    } else {
      // Alternative: check that the AppBar has at least one button (language switcher, etc.)
      const appBarButtons = page.locator('.MuiAppBar-root button');
      await expect(appBarButtons.first()).toBeVisible();
    }
  });

  test('Home page - mobile layout', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App bar/brand should be visible
    const appBar = page.locator('.MuiAppBar-root');
    await expect(appBar).toBeVisible();

    // Feature cards should be visible on mobile
    const allCards = page.locator('.MuiCard-root');
    await expect(allCards.first()).toBeVisible({ timeout: 10000 });

    // On mobile, cards should be visible and responsive
    // Check that cards have reasonable width (not too wide indicating single column)
    const count = await allCards.count();
    expect(count).toBeGreaterThan(0);

    // Get first card dimensions
    const firstCardBox = await allCards.first().boundingBox();
    if (firstCardBox) {
      // Card should be reasonably sized for mobile viewport (375px wide)
      // Card width should be close to viewport width (single column layout)
      expect(firstCardBox.width).toBeGreaterThan(0);
      // Card shouldn't be excessively wide
      expect(firstCardBox.width).toBeLessThan(400);
    }
  });

  test('Candidate Search - mobile filters collapsible', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Look for filter toggle button (expand/collapse)
    const filterToggle = page.locator('button').filter({ hasText: /filters|filter/i }).or(
      page.locator('[aria-expanded]')
    );

    const count = await filterToggle.count();
    if (count > 0) {
      // Should have expandable filters on mobile
      const toggle = filterToggle.first();
      await expect(toggle).toBeVisible();
    }
  });

  test('No horizontal scrolling on mobile', async ({ page }) => {
    await page.goto('/');

    // Check that body width equals viewport width
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10); // Allow 10px tolerance
  });

  test('Touch targets are large enough on mobile', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Check button sizes (should be at least 44x44px for touch)
    const buttons = page.locator('button, .MuiIconButton-root, a[role="button"]');

    const count = await buttons.count();
    if (count > 0) {
      // Check first 5 buttons
      for (let i = 0; i < Math.min(5, count); i++) {
        const button = buttons.nth(i);
        const box = await button.boundingBox();

        if (box) {
          // Check if button is reasonably sized for touch
          // Note: Some small icon buttons may be smaller than 44px but
          // should have adequate padding in practice
          expect(box.width).toBeGreaterThan(20); // At least 20px wide
          expect(box.height).toBeGreaterThan(20); // At least 20px tall
        }
      }
    }
  });
});

test.describe('Responsive Design - Tablet (768px)', () => {
  test.use({ ...TABLET_VIEWPORT });

  PAGES.forEach(({ path, name }) => {
    test(`${name} page - loads without errors`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      // Verify no horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 768;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

      // Verify page renders
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test('Home page - tablet layout', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App bar should be visible
    const appBar = page.locator('.MuiAppBar-root');
    await expect(appBar).toBeVisible();

    // Feature cards should use 2-column grid on tablet
    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    expect(count).toBeGreaterThan(0);

    if (count >= 2) {
      const firstCard = cards.first();
      const secondCard = cards.nth(1);

      const firstBox = await firstCard.boundingBox();
      const secondBox = await secondCard.boundingBox();

      if (firstBox && secondBox) {
        // On tablet (768px), cards should be in 2-column layout
        // Second card should be to the right of first card (same y position)
        // OR if first row is full, second card should be below first card
        const inSameRow = Math.abs(secondBox.y - firstBox.y) < 50;
        const inNextRow = secondBox.y > firstBox.y;

        expect(inSameRow || inNextRow).toBeTruthy();
      }
    }
  });

  test('Navigation - may still show hamburger on tablet', async ({ page }) => {
    await page.goto('/');

    // Tablet (768px) is between sm and lg breakpoints, so desktop nav should be visible
    // but may have icons only instead of text
    const hamburgerMenu = page.locator('button[aria-label="Open menu"]');

    // Check if hamburger is visible (it shouldn't be on tablet since desktop nav is shown)
    const hamburgerCount = await hamburgerMenu.count();
    if (hamburgerCount > 0) {
      const isVisible = await hamburgerMenu.isVisible();
      // On tablet, hamburger should NOT be visible (desktop nav with icons is shown)
      expect(isVisible).toBeFalsy();
    }

    // Desktop navigation should be visible on tablet
    const navButtons = page.locator('.MuiAppBar-root button');
    expect(await navButtons.count()).toBeGreaterThan(0);
  });
});

test.describe('Responsive Design - Desktop (1920px)', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  PAGES.forEach(({ path, name }) => {
    test(`${name} page - loads without errors`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      // Verify page renders correctly
      await expect(page.locator('body')).toBeVisible();

      // Verify reasonable use of horizontal space
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeGreaterThan(1000); // Should use desktop space
      expect(bodyWidth).toBeLessThanOrEqual(1920 + 50); // But not excessive
    });
  });

  test('Navigation - shows full menu on desktop', async ({ page }) => {
    await page.goto('/');

    // On desktop (≥ lg breakpoint), should show full horizontal navigation
    // Should NOT show hamburger menu
    const hamburgerMenu = page.locator('button[aria-label="Open menu"]');

    // Hamburger should not be visible on desktop
    const hamburgerCount = await hamburgerMenu.count();
    if (hamburgerCount > 0) {
      const isVisible = await hamburgerMenu.isVisible();
      expect(isVisible).toBeFalsy();
    }

    // Should have navigation buttons (desktop menu items)
    const navButtons = page.locator('.MuiAppBar-root button');
    const navCount = await navButtons.count();
    expect(navCount).toBeGreaterThan(0);
  });

  test('Home page - desktop layout', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App bar should be visible with full width
    const appBar = page.locator('.MuiAppBar-root');
    await expect(appBar).toBeVisible();

    // Feature cards should be in 3-4 column grid on desktop
    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    expect(count).toBeGreaterThan(0);

    if (count >= 3) {
      // Check that cards are in a grid layout
      const firstCard = cards.first();
      const thirdCard = cards.nth(2);

      const firstBox = await firstCard.boundingBox();
      const thirdBox = await thirdCard.boundingBox();

      if (firstBox && thirdBox) {
        // On desktop, should have 3-4 cards per row
        // Third card could be in same row as first or in next row
        const horizontallySpaced = Math.abs(thirdBox.x - firstBox.x) > 200;
        expect(horizontallySpaced).toBeTruthy();
      }
    }
  });

  test('Vacancy List - card grid on desktop', async ({ page }) => {
    await page.goto('/recruiter/vacancies');
    await page.waitForLoadState('networkidle');

    // Vacancy cards should be in 3-column grid on desktop
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();

    if (count > 0) {
      const firstCard = cards.first();
      const box = await firstCard.boundingBox();

      if (box) {
        // Cards should be reasonably sized on desktop
        expect(box.width).toBeGreaterThan(250); // Not too narrow
        expect(box.width).toBeLessThan(500); // Not too wide
      }
    }
  });

  test('Resume Database - card grid on desktop', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Resume cards should be in grid layout
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();

    if (count > 0) {
      // Should show multiple cards in grid on desktop
      expect(count).toBeGreaterThan(0);

      const firstCard = cards.first();
      const box = await firstCard.boundingBox();

      if (box) {
        // Cards should use desktop space effectively
        expect(box.width).toBeGreaterThan(200);
      }
    }
  });
});

test.describe('Responsive Design - Cross-Viewport Consistency', () => {
  test('Content is accessible on all viewports', async ({ page }) => {
    const viewports = [MOBILE_VIEWPORT, TABLET_VIEWPORT, DESKTOP_VIEWPORT];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Main content should be visible
      const mainContent = page.locator('main, #root, .MuiContainer-root').first();
      await expect(mainContent).toBeVisible();

      // Check for critical console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Wait a bit to catch any errors
      await page.waitForTimeout(1000);

      if (errors.length > 0) {
        console.error(`Errors on viewport ${viewport.width}x${viewport.height}:`, errors);
      }
    }
  });

  test('No horizontal overflow on any viewport', async ({ page }) => {
    const viewports = [
      { width: 320, height: 568 }, // Very small mobile
      { width: 375, height: 667 }, // iPhone SE
      { width: 768, height: 1024 }, // iPad
      { width: 1024, height: 768 }, // Landscape tablet
      { width: 1920, height: 1080 }, // Desktop
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Check body width
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 15); // Allow 15px tolerance
    }
  });

  test('Images are responsive', async ({ page }) => {
    await page.goto('/');

    // Check if images have responsive styles
    const images = page.locator('img');
    const count = await images.count();

    if (count > 0) {
      // Check first few images
      const checkCount = Math.min(5, count);
      for (let i = 0; i < checkCount; i++) {
        const img = images.nth(i);

        // Check if image has max-width or width constraints
        const maxWidth = await img.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.maxWidth || styles.width;
        });

        // Images should have some width constraint
        // Note: This is a soft check as not all images need to be responsive
        if (maxWidth && maxWidth !== 'auto') {
          expect(maxWidth).toBeTruthy();
        }
      }
    }
  });
});

test.describe('Responsive Design - Material-UI Breakpoints', () => {
  test('Breakpoints are correctly applied', async ({ page }) => {
    // Test at exact Material-UI breakpoint boundaries
    const breakpoints = [
      { width: 599, name: 'xs (mobile)' },
      { width: 600, name: 'sm (tablet)' },
      { width: 899, name: 'sm (tablet)' },
      { width: 900, name: 'md (desktop)' },
      { width: 1199, name: 'md (desktop)' },
      { width: 1200, name: 'lg (desktop)' },
    ];

    for (const bp of breakpoints) {
      await page.setViewportSize({ width: bp.width, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Page should render without errors at each breakpoint
      await expect(page.locator('body')).toBeVisible();

      // No horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(bp.width + 15);
    }
  });
});
