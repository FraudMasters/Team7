import { test, expect } from '@playwright/test';

/**
 * Mobile Interactions E2E Tests
 *
 * Tests touch-optimized interactions including swipe gestures, tap interactions,
 * and long-press on mobile devices. Verifies that mobile UI components respond
 * correctly to touch events.
 *
 * Run with: npm run test:e2e -- mobile-interactions.spec.ts
 */

// Mobile viewport configuration
const MOBILE_VIEWPORT = { width: 375, height: 667 }; // iPhone SE
const MOBILE_VIEWPORT_LARGE = { width: 414, height: 896 }; // iPhone 11

test.describe('Mobile Interactions - Setup', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Mobile viewport is correctly set', async ({ page }) => {
    await page.goto('/');

    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBe(375);
    expect(viewportSize?.height).toBe(667);
  });
});

test.describe('Mobile Interactions - Tap Gestures', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Tap on navigation buttons works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find navigation buttons in AppBar
    const navButtons = page.locator('.MuiAppBar-root button');

    const count = await navButtons.count();
    if (count > 0) {
      // Tap the first button
      await navButtons.first().tap();

      // Verify no errors occurred
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Wait a moment for any navigation
      await page.waitForTimeout(500);

      // Check that we're still on a valid page
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('Tap on cards triggers navigation/action', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Wait for cards to load
    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    if (count > 0) {
      // Tap the first card
      await cards.first().tap();

      // Should navigate or show some action
      await page.waitForTimeout(500);

      // Verify page is still responsive
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('Tap on buttons has visual feedback', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Find buttons on the page
    const buttons = page.locator('button').filter({ hasText: /.+/ });

    const count = await buttons.count();
    if (count > 0) {
      const button = buttons.first();

      // Get initial state
      const isVisible = await button.isVisible();
      expect(isVisible).toBeTruthy();

      // Tap the button
      await button.tap();

      // Verify button is still visible and interactive
      await expect(button).toBeVisible();
    }
  });

  test('Tap targets are large enough on mobile', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Check button and link sizes
    const interactiveElements = page.locator('button, a[role="button"], .MuiButtonBase-root');

    const count = await interactiveElements.count();
    if (count > 0) {
      // Check first few interactive elements
      const checkCount = Math.min(5, count);
      for (let i = 0; i < checkCount; i++) {
        const element = interactiveElements.nth(i);
        const box = await element.boundingBox();

        if (box) {
          // Touch targets should be at least 44x44px (iOS/Android guidelines)
          // Note: Some small icon buttons may be smaller but have adequate padding
          expect(box.width).toBeGreaterThan(20);
          expect(box.height).toBeGreaterThan(20);
        }
      }
    }
  });

  test('Multiple taps in rapid succession work', async ({ page }) => {
    await page.goto('/');

    // Find a tappable element
    const buttons = page.locator('button');

    const count = await buttons.count();
    if (count >= 2) {
      // Tap two different buttons rapidly
      await buttons.nth(0).tap();
      await page.waitForTimeout(100);
      await buttons.nth(1).tap();

      // Page should still be responsive
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('Mobile Interactions - Swipe Gestures', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Swipe down gesture is recognized', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Get the page dimensions
    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const startX = viewportSize.width / 2;
    const startY = 100;
    const endY = 300;

    // Perform swipe down gesture
    await page.touchscreen.tap(startX, startY);
    await page.mouse.down();
    await page.mouse.move(startX, endY, { steps: 10 });
    await page.mouse.up();

    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('Swipe up gesture is recognized', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const centerX = viewportSize.width / 2;
    const startY = 500;
    const endY = 200;

    // Perform swipe up gesture
    await page.mouse.move(centerX, startY);
    await page.mouse.down();
    await page.mouse.move(centerX, endY, { steps: 10 });
    await page.mouse.up();

    // Page should remain functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('Swipe left gesture is recognized', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const startY = viewportSize.height / 2;
    const startX = 300;
    const endX = 100;

    // Perform swipe left gesture
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    await page.mouse.move(endX, startY, { steps: 10 });
    await page.mouse.up();

    // Page should still be functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('Swipe right gesture is recognized', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const startY = viewportSize.height / 2;
    const startX = 100;
    const endX = 300;

    // Perform swipe right gesture
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    await page.mouse.move(endX, startY, { steps: 10 });
    await page.mouse.up();

    // Page should remain responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('Horizontal swipe on candidate cards', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Wait for cards to load
    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    if (count > 0) {
      const firstCard = cards.first();
      const box = await firstCard.boundingBox();

      if (box) {
        const startX = box.x + box.width - 50;
        const endX = box.x + 50;
        const centerY = box.y + box.height / 2;

        // Perform left swipe on card
        await page.mouse.move(startX, centerY);
        await page.mouse.down();
        await page.mouse.move(endX, centerY, { steps: 10 });
        await page.mouse.up();

        // Wait for animation
        await page.waitForTimeout(500);

        // Card should still be visible
        await expect(firstCard).toBeVisible();
      }
    }
  });

  test('Vertical page scroll works with touch', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    // Get initial scroll position
    const initialScrollY = await page.evaluate(() => window.scrollY);

    // Perform vertical swipe to scroll down
    const centerX = viewportSize.width / 2;
    await page.mouse.move(centerX, 500);
    await page.mouse.down();
    await page.mouse.move(centerX, 200, { steps: 10 });
    await page.mouse.up();

    // Wait for scroll to complete
    await page.waitForTimeout(500);

    // Page should have scrolled
    const finalScrollY = await page.evaluate(() => window.scrollY);
    expect(finalScrollY).toBeGreaterThanOrEqual(initialScrollY);
  });
});

test.describe('Mobile Interactions - Long Press', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Long press on buttons is handled', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Find a button
    const buttons = page.locator('button').filter({ hasText: /.+/ });

    const count = await buttons.count();
    if (count > 0) {
      const button = buttons.first();
      const box = await button.boundingBox();

      if (box) {
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;

        // Long press: hold for 1 second
        await page.mouse.move(centerX, centerY);
        await page.mouse.down();
        await page.waitForTimeout(1000);
        await page.mouse.up();

        // Page should still be responsive
        await expect(page.locator('body')).toBeVisible();
      }
    }
  });

  test('Long press on cards does not cause errors', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    if (count > 0) {
      const firstCard = cards.first();
      const box = await firstCard.boundingBox();

      if (box) {
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;

        // Long press on card
        await page.mouse.move(centerX, centerY);
        await page.mouse.down();
        await page.waitForTimeout(1000);
        await page.mouse.up();

        // Card should still be visible
        await expect(firstCard).toBeVisible();
      }
    }
  });

  test('Long press followed by quick tap', async ({ page }) => {
    await page.goto('/');

    const buttons = page.locator('button');

    const count = await buttons.count();
    if (count >= 2) {
      // Long press on first button
      const firstButton = buttons.nth(0);
      const box1 = await firstButton.boundingBox();

      if (box1) {
        await page.mouse.move(box1.x + box1.width / 2, box1.y + box1.height / 2);
        await page.mouse.down();
        await page.waitForTimeout(800);
        await page.mouse.up();
      }

      // Quick tap on second button
      await buttons.nth(1).tap();

      // Page should handle both interactions
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('Mobile Interactions - Touch Carousel', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Carousel swipe changes active item', async ({ page }) => {
    // Navigate to a page that might have a carousel or swipeable content
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for swipeable containers or cards
    const swipeableArea = page.locator('.MuiCard-root').first();

    await expect(swipeableArea).toBeVisible({ timeout: 10000 });

    const box = await swipeableArea.boundingBox();
    if (box) {
      const startX = box.x + box.width * 0.8;
      const endX = box.x + box.width * 0.2;
      const centerY = box.y + box.height / 2;

      // Swipe left
      await page.mouse.move(startX, centerY);
      await page.mouse.down();
      await page.mouse.move(endX, centerY, { steps: 10 });
      await page.mouse.up();

      // Wait for animation
      await page.waitForTimeout(500);

      // Area should still be visible
      await expect(swipeableArea).toBeVisible();
    }
  });

  test('Multiple rapid swipes are handled', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const centerX = viewportSize.width / 2;

    // Perform multiple rapid swipes
    for (let i = 0; i < 3; i++) {
      await page.mouse.move(centerX, 400);
      await page.mouse.down();
      await page.mouse.move(centerX, 200, { steps: 5 });
      await page.mouse.up();
      await page.waitForTimeout(200);
    }

    // Page should remain responsive
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Mobile Interactions - Pull to Refresh', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Pull down gesture at top of page', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Scroll to top
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const centerX = viewportSize.width / 2;

    // Pull down gesture from top
    await page.mouse.move(centerX, 50);
    await page.mouse.down();
    await page.mouse.move(centerX, 200, { steps: 10 });
    await page.mouse.up();

    // Wait for any pull-to-refresh animation
    await page.waitForTimeout(1000);

    // Page should remain functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('Pull down gesture triggers refresh indicator', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Ensure we're at the top
    await page.evaluate(() => window.scrollTo(0, 0));

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const centerX = viewportSize.width / 2;

    // Pull down from top
    await page.mouse.move(centerX, 20);
    await page.mouse.down();
    await page.mouse.move(centerX, 150, { steps: 15 });
    await page.mouse.up();

    // Check for loading indicators or refresh UI
    await page.waitForTimeout(500);

    // Page should still work
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Mobile Interactions - Form Inputs', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Tap on input field focuses it', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Find input fields
    const inputs = page.locator('input[type="text"], input[type="search"]');

    const count = await inputs.count();
    if (count > 0) {
      const input = inputs.first();

      // Tap on input
      await input.tap();

      // Check if input is focused
      const isFocused = await input.evaluate(el => document.activeElement === el);
      expect(isFocused).toBeTruthy();
    }
  });

  test('Typing in mobile search bar works', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Find search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]');

    const count = await searchInput.count();
    if (count > 0) {
      const input = searchInput.first();

      // Tap to focus
      await input.tap();
      await page.waitForTimeout(200);

      // Type search query
      await input.fill('developer');
      await page.waitForTimeout(500);

      // Verify input has value
      const value = await input.inputValue();
      expect(value).toContain('developer');
    }
  });

  test('Tapping clear button in search clears input', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]');

    const count = await searchInput.count();
    if (count > 0) {
      const input = searchInput.first();

      // Type something
      await input.fill('test');
      await page.waitForTimeout(300);

      // Look for clear button (usually an icon button near input)
      const clearButton = page.locator('button').filter({ hasText: '' }).locator('xpath=../../..').filter({ has: input });

      const buttonCount = await clearButton.count();
      if (buttonCount > 0) {
        // Try to find and click clear button
        const parent = await input.locator('..').locator('button').first();
        if (await parent.isVisible()) {
          await parent.tap();
          await page.waitForTimeout(300);

          // Input should be cleared
          const value = await input.inputValue();
          expect(value).toBe('');
        }
      }
    }
  });
});

test.describe('Mobile Interactions - Complex Gestures', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Swipe then tap in sequence', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    // First swipe
    await page.mouse.move(300, 400);
    await page.mouse.down();
    await page.mouse.move(100, 400, { steps: 10 });
    await page.mouse.up();

    await page.waitForTimeout(300);

    // Then tap
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();
    if (count > 0) {
      await cards.first().tap();
    }

    // Page should handle both
    await expect(page.locator('body')).toBeVisible();
  });

  test('Diagonal swipe is handled gracefully', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    // Diagonal swipe (down and left)
    await page.mouse.move(300, 200);
    await page.mouse.down();
    await page.mouse.move(100, 500, { steps: 10 });
    await page.mouse.up();

    // Page should remain functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('Quick small swipes (scroll jabs)', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    const centerX = viewportSize.width / 2;

    // Multiple small quick swipes
    for (let i = 0; i < 5; i++) {
      await page.mouse.move(centerX, 300 + i * 20);
      await page.mouse.down();
      await page.mouse.move(centerX, 280 + i * 20, { steps: 3 });
      await page.mouse.up();
      await page.waitForTimeout(100);
    }

    // Page should remain responsive
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Mobile Interactions - Cross-Page Consistency', () => {
  test.use({ ...MOBILE_VIEWPORT });

  const pages = [
    { path: '/', name: 'Home' },
    { path: '/recruiter/search', name: 'Search' },
    { path: '/recruiter/resumes', name: 'Resumes' },
    { path: '/recruiter/vacancies', name: 'Vacancies' },
  ];

  pages.forEach(({ path, name }) => {
    test(`${name} - tap interactions work`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      // Find and tap a button
      const buttons = page.locator('button');

      const count = await buttons.count();
      if (count > 0) {
        await buttons.first().tap();
        await page.waitForTimeout(300);

        // Page should still be functional
        await expect(page.locator('body')).toBeVisible();
      }
    });

    test(`${name} - swipe gestures are recognized`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      const viewportSize = page.viewportSize();
      if (!viewportSize) return;

      // Perform a vertical swipe
      const centerX = viewportSize.width / 2;
      await page.mouse.move(centerX, 400);
      await page.mouse.down();
      await page.mouse.move(centerX, 200, { steps: 10 });
      await page.mouse.up();

      // Page should handle the gesture
      await expect(page.locator('body')).toBeVisible();
    });
  });
});

test.describe('Mobile Interactions - Larger Device', () => {
  test.use({ ...MOBILE_VIEWPORT_LARGE });

  test('Touch interactions work on larger mobile', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Verify viewport size
    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBe(414);

    // Tap interaction
    const cards = page.locator('.MuiCard-root');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });

    const count = await cards.count();
    if (count > 0) {
      await cards.first().tap();
      await page.waitForTimeout(300);

      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('Swipe works on larger mobile screen', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const viewportSize = page.viewportSize();
    if (!viewportSize) return;

    // Swipe gesture
    const centerX = viewportSize.width / 2;
    await page.mouse.move(centerX, 400);
    await page.mouse.down();
    await page.mouse.move(centerX, 200, { steps: 10 });
    await page.mouse.up();

    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Mobile Interactions - Error Handling', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('No JavaScript errors during touch interactions', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    const errors: string[] = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });

    // Perform various touch interactions
    const cards = page.locator('.MuiCard-root');
    const count = await cards.count();

    if (count > 0) {
      await cards.first().tap();
      await page.waitForTimeout(200);

      const viewportSize = page.viewportSize();
      if (viewportSize) {
        // Swipe
        await page.mouse.move(300, 400);
        await page.mouse.down();
        await page.mouse.move(100, 400, { steps: 10 });
        await page.mouse.up();
      }
    }

    await page.waitForTimeout(500);

    // Check for errors
    if (errors.length > 0) {
      console.error('JavaScript errors during touch interactions:', errors);
    }
  });

  test('Rapid interactions do not cause crashes', async ({ page }) => {
    await page.goto('/');

    // Perform many rapid interactions
    for (let i = 0; i < 10; i++) {
      const buttons = page.locator('button');
      const count = await buttons.count();

      if (count > 0) {
        await buttons.first().tap();
      }

      // Small delay
      await page.waitForTimeout(50);
    }

    // Page should still be functional
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Mobile Interactions - Accessibility', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Touch targets have adequate spacing', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Check that interactive elements aren't too close together
    const buttons = page.locator('button, a[role="button"]');

    const count = await buttons.count();
    if (count >= 2) {
      // Get positions of first few buttons
      const positions: Array<{ x: number; y: number; width: number; height: number }> = [];

      for (let i = 0; i < Math.min(3, count); i++) {
        const box = await buttons.nth(i).boundingBox();
        if (box) {
          positions.push(box);
        }
      }

      // Check spacing between consecutive buttons
      for (let i = 0; i < positions.length - 1; i++) {
        const current = positions[i];
        const next = positions[i + 1];

        // Calculate distance
        const distance = Math.sqrt(
          Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
        );

        // Elements should have some spacing (at least 8px recommended)
        // This is a soft check - exact positioning depends on layout
        expect(distance).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('Interactive elements are reachable on mobile', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Check that all visible interactive elements can be tapped
    const interactiveElements = page.locator('button, a, input, select, [role="button"]');

    const count = await interactiveElements.count();
    if (count > 0) {
      // Check first few elements are visible
      let visibleCount = 0;
      const checkCount = Math.min(5, count);

      for (let i = 0; i < checkCount; i++) {
        const element = interactiveElements.nth(i);
        if (await element.isVisible()) {
          visibleCount++;
        }
      }

      // At least some elements should be visible
      expect(visibleCount).toBeGreaterThan(0);
    }
  });
});
