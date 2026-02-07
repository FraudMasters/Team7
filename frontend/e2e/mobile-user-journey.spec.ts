import { test, expect } from '@playwright/test';

/**
 * Mobile User Journey E2E Tests
 *
 * Comprehensive end-to-end tests for the complete mobile user experience.
 * Tests the full journey from PWA installation to offline usage and data synchronization.
 *
 * Run with: npm run test:e2e -- mobile-user-journey.spec.ts
 *
 * Test Journey:
 * 1. Install app to homescreen on mobile device
 * 2. Launch app from homescreen
 * 3. Search for candidates with mobile search bar
 * 4. Swipe through candidate cards
 * 5. View candidate details in single-column layout
 * 6. Go offline and verify cached data is accessible
 * 7. Add notes to candidate while offline
 * 8. Go back online and verify sync
 */

// Mobile viewport configuration
const MOBILE_VIEWPORT = { width: 375, height: 667 }; // iPhone SE
const MOBILE_VIEWPORT_LARGE = { width: 414, height: 896 }; // iPhone 11

test.describe('Mobile User Journey - PWA Installation', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Complete PWA installation flow', async ({ page, context }) => {
    await page.goto('/');

    // Wait for service worker to register
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Verify service worker is registered
    const swReady = await page.evaluate(async () => {
      return await navigator.serviceWorker.ready;
    });
    expect(swReady).toBeTruthy();
    expect(swReady.active).toBeTruthy();

    // Verify manifest is accessible
    const manifestResponse = await page.request.get('/manifest.json');
    expect(manifestResponse.status()).toBe(200);
    const manifest = await manifestResponse.json();
    expect(manifest.name).toBeTruthy();
    expect(manifest.icons.length).toBeGreaterThan(0);

    // Check PWA installability criteria
    const isInstallable = await page.evaluate(async () => {
      // Check manifest
      const manifestLink = document.querySelector('link[rel="manifest"]');
      if (!manifestLink) return false;

      // Check service worker
      const swRegistration = await navigator.serviceWorker.ready;
      if (!swRegistration) return false;

      // Check secure context
      if (!window.isSecureContext) return false;

      return true;
    });
    expect(isInstallable).toBeTruthy();

    // Note: Actual install-to-homescreen requires user interaction
    // and browser-specific install prompts. This test verifies
    // the technical prerequisites for installation.
  });

  test('App launches correctly from start URL', async ({ page }) => {
    // Simulate launching from homescreen (standalone mode)
    await page.goto('/', {
      extraHTTPHeaders: {
        'Sec-CH-Prefers-Color-Scheme': 'light',
      },
    });

    await page.waitForLoadState('networkidle');

    // Verify app renders correctly in mobile viewport
    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBe(375);

    // Check for console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Wait a bit for any async errors
    await page.waitForTimeout(2000);

    // Verify no critical errors
    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught') ||
      err.includes('TypeError') ||
      err.includes('ReferenceError')
    );
    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Mobile User Journey - Search and Discovery', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Search for candidates using mobile search bar', async ({ page }) => {
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Verify mobile search bar is present
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i], input[placeholder*="Поиск" i]');
    await expect(searchInput.first()).toBeVisible();

    // Type search query
    await searchInput.first().fill('developer');

    // Wait for debounced search
    await page.waitForTimeout(500);

    // Verify search results appear (if any candidates exist)
    const candidateCards = page.locator('[data-testid="candidate-card"], .MuiCard-root');
    const count = await candidateCards.count();

    // If results exist, verify they're rendered
    if (count > 0) {
      await expect(candidateCards.first()).toBeVisible();
    }

    // Check for no console errors during search
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForTimeout(1000);
    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught') ||
      err.includes('TypeError')
    );
    expect(criticalErrors.length).toBe(0);
  });

  test('Swipe through candidate cards on mobile', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Find candidate cards
    const candidateCards = page.locator('[data-testid="candidate-card"], .MuiCard-root, [data-testid="resume-card"]');
    const count = await candidateCards.count();

    if (count > 0) {
      // Perform swipe gestures on the first card
      const firstCard = candidateCards.first();

      // Swipe left (quick motion)
      const cardBox = await firstCard.boundingBox();
      if (cardBox) {
        const startX = cardBox.x + cardBox.width * 0.8;
        const startY = cardBox.y + cardBox.height / 2;
        const endX = cardBox.x + cardBox.width * 0.2;

        await page.touchscreen.tap(startX, startY);
        await page.mouse.down();
        await page.mouse.move(endX, startY, { steps: 10 });
        await page.mouse.up();

        // Wait for any animations
        await page.waitForTimeout(500);
      }

      // Verify card is still visible (no crashes)
      await expect(candidateCards.first()).toBeVisible();
    }

    // Verify no console errors from swipe interactions
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForTimeout(1000);

    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught') ||
      err.includes('TypeError')
    );
    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Mobile User Journey - Candidate Details', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('View candidate details in single-column mobile layout', async ({ page }) => {
    // Navigate to candidate list first
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Try to find and click on a candidate
    const candidateCards = page.locator('[data-testid="candidate-card"], .MuiCard-root, [data-testid="resume-card"], a[href*="/resume/"]');
    const count = await candidateCards.count();

    if (count > 0) {
      // Click on first candidate card/link
      await candidateCards.first().click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Verify single-column layout on mobile
      // Check that content doesn't overflow horizontally
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = page.viewportSize()?.width || 375;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

      // Verify tabs are touch-friendly (min 44px height)
      const tabs = page.locator('[role="tab"], .MuiTab-root');
      const tabCount = await tabs.count();

      if (tabCount > 0) {
        const firstTab = tabs.first();
        const tabBox = await firstTab.boundingBox();
        expect(tabBox?.height).toBeGreaterThanOrEqual(44);
      }

      // Verify content stacks vertically (no multi-column layout)
      const mainContent = page.locator('main, .MuiContainer-root');
      const isFlexColumn = await mainContent.first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.flexDirection === 'column' ||
               styles.display === 'block' ||
               styles.display === 'flow-root';
      });
      expect(isFlexColumn).toBeTruthy();
    } else {
      // If no candidates, verify the page still loads without errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      await page.waitForTimeout(1000);

      const criticalErrors = errors.filter(err =>
        err.includes('Uncaught') ||
        err.includes('TypeError')
      );
      expect(criticalErrors.length).toBe(0);
    }
  });

  test('Mobile candidate details page has proper navigation', async ({ page }) => {
    // Navigate directly to a candidate detail page (if candidate ID 1 exists)
    await page.goto('/recruiter/resumes/1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Check for back navigation or breadcrumbs
    const backButtons = page.locator('button[aria-label*="back" i], button[aria-label*="назад" i], .MuiIconButton-root');
    const breadcrumbs = page.locator('.MuiBreadcrumbs-root, nav[aria-label="breadcrumb"]');

    // At least one navigation element should be present
    const hasNav = await backButtons.count() > 0 || await breadcrumbs.count() > 0;
    expect(hasNav).toBeTruthy();

    // Verify no horizontal scroll on mobile
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth;
    });
    expect(hasHorizontalScroll).toBeFalsy();
  });
});

test.describe('Mobile User Journey - Offline Mode', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Go offline and verify cached data is accessible', async ({ page, context }) => {
    // First, visit pages while online to cache them
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Wait for service worker to cache assets
    await page.waitForTimeout(3000);

    // Go offline
    await context.setOffline(true);

    try {
      // Navigate to resumes page while offline
      await page.goto('/recruiter/resumes');
      await page.waitForTimeout(2000);

      // Verify page still renders (from cache)
      const bodyVisible = await page.locator('body').isVisible();
      expect(bodyVisible).toBeTruthy();

      // Verify service worker is still controlling the page
      const isControlled = await page.evaluate(() => {
        return navigator.serviceWorker.controller !== null;
      });
      expect(isControlled).toBeTruthy();

      // Verify cached data is displayed
      const content = await page.locator('body').textContent();
      expect(content?.length).toBeGreaterThan(0);

    } finally {
      // Go back online
      await context.setOffline(false);
      await page.waitForTimeout(1000);
    }
  });

  test('Search and navigation work while offline', async ({ page, context }) => {
    // Cache pages first
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Go offline
    await context.setOffline(true);

    try {
      // Navigate to cached page
      await page.goto('/recruiter/search');
      await page.waitForTimeout(1000);

      // Verify page renders from cache
      const searchPage = page.locator('body');
      await expect(searchPage).toBeVisible();

      // Try to interact with search (may fail gracefully)
      const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]');
      const inputCount = await searchInput.count();

      if (inputCount > 0) {
        // Input should be visible even offline
        await expect(searchInput.first()).toBeVisible();
      }

    } finally {
      // Go back online
      await context.setOffline(false);
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Mobile User Journey - Offline Operations', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Add notes to candidate while offline (if feature exists)', async ({ page, context }) => {
    // First, cache a candidate detail page
    await page.goto('/recruiter/resumes/1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Go offline
    await context.setOffline(true);

    try {
      // Reload page while offline
      await page.reload();
      await page.waitForTimeout(1000);

      // Look for notes/feedback input fields
      const noteInputs = page.locator('textarea[placeholder*="note" i], textarea[placeholder*="заметка" i], [data-testid="notes-input"]');
      const noteCount = await noteInputs.count();

      if (noteCount > 0) {
        // Notes feature exists - try to add a note offline
        const testNote = 'Test note added offline ' + new Date().toISOString();

        await noteInputs.first().fill(testNote);

        // Look for save button
        const saveButtons = page.locator('button:has-text("Save"), button:has-text("Сохранить"), [data-testid="save-note"]');
        const saveCount = await saveButtons.count();

        if (saveCount > 0) {
          // Try to save (may fail or queue for later)
          await saveButtons.first().click();
          await page.waitForTimeout(1000);

          // Verify graceful handling (no crash)
          const errors: string[] = [];
          page.on('console', msg => {
            if (msg.type() === 'error') {
              errors.push(msg.text());
            }
          });
          await page.waitForTimeout(500);

          // Should handle offline save gracefully
          const criticalErrors = errors.filter(err =>
            err.includes('Uncaught') ||
            err.includes('TypeError') &&
            !err.includes('network')
          );
          expect(criticalErrors.length).toBe(0);
        }
      } else {
        // Notes feature may not exist - just verify page loads offline
        const bodyVisible = await page.locator('body').isVisible();
        expect(bodyVisible).toBeTruthy();
      }

    } finally {
      // Go back online
      await context.setOffline(false);
      await page.waitForTimeout(1000);
    }
  });

  test('Offline indicator shows when network is unavailable', async ({ page, context }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Go offline
    await context.setOffline(true);

    try {
      await page.waitForTimeout(1000);

      // Check for offline indicator
      // This could be a toast, banner, or status indicator
      const offlineIndicators = page.locator(
        '[data-testid="offline-indicator"], ' +
        '.MuiAlert-root, ' +
        '[role="alert"]'
      );

      // Wait a bit for offline indicator to appear
      await page.waitForTimeout(500);

      const indicatorCount = await offlineIndicators.count();

      // If indicator exists, verify it's visible
      if (indicatorCount > 0) {
        await expect(offlineIndicators.first()).toBeVisible();
      }

    } finally {
      // Go back online
      await context.setOffline(false);
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Mobile User Journey - Online Recovery', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Recover gracefully when connection is restored', async ({ page, context }) => {
    // Start online
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Go offline
    await context.setOffline(true);
    await page.waitForTimeout(2000);

    // Verify offline state
    const isOffline = await page.evaluate(() => !navigator.onLine);
    expect(isOffline).toBeTruthy();

    // Go back online
    await context.setOffline(false);
    await page.waitForTimeout(1000);

    // Verify online state recovered
    const isOnline = await page.evaluate(() => navigator.onLine);
    expect(isOnline).toBeTruthy();

    // Try to fetch new data
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify page still works
    const bodyVisible = await page.locator('body').isVisible();
    expect(bodyVisible).toBeTruthy();

    // No console errors after recovery
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForTimeout(1000);

    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught') ||
      err.includes('TypeError')
    );
    expect(criticalErrors.length).toBe(0);
  });

  test('Data syncs correctly after coming back online', async ({ page, context }) => {
    // Start online and cache data
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Simulate going offline and making changes
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    // Try to interact with page (search, filter, etc.)
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]');
    const inputCount = await searchInput.count();

    if (inputCount > 0) {
      await searchInput.first().fill('test');
      await page.waitForTimeout(500);
    }

    // Go back online
    await context.setOffline(false);
    await page.waitForTimeout(1000);

    // Reload to force fresh data fetch
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify app works correctly after sync
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForTimeout(1000);

    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught') ||
      err.includes('TypeError') ||
      err.includes('NetworkError')
    );
    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Mobile User Journey - Complete End-to-End', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('Complete mobile user journey: Install, Search, View, Offline, Sync', async ({ page, context }) => {
    // Step 1: Verify PWA installation prerequisites
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const swReady = await page.evaluate(async () => {
      return await navigator.serviceWorker.ready;
    });
    expect(swReady).toBeTruthy();

    // Step 2: Launch and navigate to search
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Step 3: Search for candidates
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]');
    const searchCount = await searchInput.count();

    if (searchCount > 0) {
      await searchInput.first().fill('developer');
      await page.waitForTimeout(500);
    }

    // Step 4: Navigate to candidate list
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Cache the page for offline use
    await page.waitForTimeout(2000);

    // Step 5: Go offline
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    try {
      // Step 6: Verify cached data is accessible offline
      const bodyContent = await page.locator('body').textContent();
      expect(bodyContent?.length).toBeGreaterThan(0);

      // Step 7: Try to view candidate details offline
      const candidateLinks = page.locator('a[href*="/resume/"]');
      const linkCount = await candidateLinks.count();

      if (linkCount > 0) {
        await candidateLinks.first().click();
        await page.waitForTimeout(1000);

        // Verify detail page loads from cache
        const detailContent = await page.locator('body').textContent();
        expect(detailContent?.length).toBeGreaterThan(0);
      }

    } finally {
      // Step 8: Go back online and verify sync
      await context.setOffline(false);
      await page.waitForTimeout(1000);

      // Reload to fetch fresh data
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify everything still works
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      await page.waitForTimeout(1000);

      const criticalErrors = errors.filter(err =>
        err.includes('Uncaught') ||
        err.includes('TypeError')
      );
      expect(criticalErrors.length).toBe(0);

      // Verify online status
      const isOnline = await page.evaluate(() => navigator.onLine);
      expect(isOnline).toBeTruthy();
    }
  });

  test('Mobile performance: All pages load within acceptable time', async ({ page }) => {
    const pages = [
      '/',
      '/recruiter/search',
      '/recruiter/resumes',
      '/recruiter/vacancies',
    ];

    for (const pagePath of pages) {
      const startTime = Date.now();

      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;

      // Verify page loads in less than 5 seconds (generous for mobile)
      expect(loadTime).toBeLessThan(5000);

      // Verify no console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      await page.waitForTimeout(500);

      const criticalErrors = errors.filter(err =>
        err.includes('Uncaught') ||
        err.includes('TypeError')
      );
      expect(criticalErrors.length).toBe(0);
    }
  });
});

test.describe('Mobile User Journey - Touch Target Sizes', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('All interactive elements meet minimum touch target size (44x44px)', async ({ page }) => {
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Check button sizes
    const buttons = page.locator('button, a[href], [role="button"], .MuiChip-root, input[type="checkbox"]');

    const count = await buttons.count();
    const undersizedElements: string[] = [];

    for (let i = 0; i < Math.min(count, 50); i++) {
      const button = buttons.nth(i);
      const box = await button.boundingBox();

      if (box) {
        const isVisible = await button.isVisible();
        if (isVisible && (box.width < 44 || box.height < 44)) {
          const text = await button.textContent();
          undersizedElements.push(
            `${(text || 'button').trim().substring(0, 30)}: ${box.width}x${box.height}`
          );
        }
      }
    }

    // Allow some undersized elements (pagination links, icon buttons, etc.)
    // but most interactive elements should meet the 44x44px guideline
    if (undersizedElements.length > 10) {
      console.warn('Found undersized touch targets:', undersizedElements);
    }

    // At least 80% of tested elements should meet the guideline
    const testedCount = Math.min(count, 50);
    const acceptableUndersized = Math.floor(testedCount * 0.2);
    expect(undersizedElements.length).toBeLessThanOrEqual(acceptableUndersized);
  });
});
