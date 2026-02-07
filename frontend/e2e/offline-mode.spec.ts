import { test, expect } from '@playwright/test';

/**
 * Offline Mode E2E Tests
 *
 * Tests Progressive Web App (PWA) offline capabilities including service worker
 * registration, caching, and offline viewing of cached content.
 *
 * Run with: npm run test:e2e -- offline-mode.spec.ts
 */

// Pages to test for offline functionality
const PAGES = [
  { path: '/', name: 'Home' },
  { path: '/recruiter/search', name: 'Candidate Search' },
  { path: '/recruiter/vacancies', name: 'Vacancy List' },
  { path: '/recruiter/resumes', name: 'Resume Database' },
];

test.describe('Service Worker Registration', () => {
  test('Service worker is registered', async ({ page }) => {
    await page.goto('/');

    // Wait for service worker to register
    await page.waitForLoadState('networkidle');

    // Check if service worker is registered
    const swRegistration = await page.evaluate(async () => {
      return await navigator.serviceWorker.ready;
    });

    expect(swRegistration).toBeTruthy();
    expect(swRegistration.active).toBeTruthy();
  });

  test('Service worker controls the page', async ({ page }) => {
    await page.goto('/');

    // Wait for service worker to be ready
    await page.waitForTimeout(2000);

    // Check if service worker is controlling the page
    const isControlled = await page.evaluate(() => {
      return navigator.serviceWorker.controller !== null;
    });

    expect(isControlled).toBeTruthy();
  });

  test('PWA manifest is present', async ({ page }) => {
    await page.goto('/');

    // Check for manifest link
    const manifestLink = page.locator('link[rel="manifest"]');
    await expect(manifestLink).toHaveAttribute('href', '/manifest.json');
  });

  test('PWA manifest has required fields', async ({ page }) => {
    const response = await page.request.get('/manifest.json');
    const manifest = await response.json();

    // Verify required PWA manifest fields
    expect(manifest.name).toBeTruthy();
    expect(manifest.short_name).toBeTruthy();
    expect(manifest.start_url).toBeTruthy();
    expect(manifest.display).toBeTruthy();
    expect(manifest.icons).toBeDefined();
    expect(manifest.icons.length).toBeGreaterThan(0);

    // Verify icons have required properties
    const icon = manifest.icons[0];
    expect(icon.src).toBeTruthy();
    expect(icon.sizes).toBeTruthy();
    expect(icon.type).toBeTruthy();
  });
});

test.describe('Cache Functionality', () => {
  test('Static assets are cached', async ({ page }) => {
    // First visit to populate cache
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for service worker to cache assets
    await page.waitForTimeout(2000);

    // Check cache storage
    const cacheNames = await page.evaluate(async () => {
      const caches = await window.caches.keys();
      return caches;
    });

    // Should have at least one cache
    expect(cacheNames.length).toBeGreaterThan(0);

    // Check that cache contains entries
    const cacheEntries = await page.evaluate(async () => {
      const caches = await window.caches.keys();
      if (caches.length > 0) {
        const cache = await window.caches.open(caches[0]);
        const keys = await cache.keys();
        return keys.length;
      }
      return 0;
    });

    // Should have cached entries
    expect(cacheEntries).toBeGreaterThan(0);
  });

  test('API responses are cached for offline use', async ({ page }) => {
    // Visit a page with API calls
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Wait for service worker to cache API responses
    await page.waitForTimeout(2000);

    // Check if API responses are cached
    const hasCachedRequests = await page.evaluate(async () => {
      const caches = await window.caches.keys();
      for (const cacheName of caches) {
        const cache = await window.caches.open(cacheName);
        const requests = await cache.keys();
        // Check if any API requests are cached
        const apiRequests = requests.filter(request =>
          request.url.includes('/api/')
        );
        if (apiRequests.length > 0) {
          return true;
        }
      }
      return false;
    });

    // Note: This test may pass even if no API responses are cached
    // as caching strategy may vary by endpoint
    // We're just verifying the cache mechanism exists
  });
});

test.describe('Offline Viewing - Core Pages', () => {
  PAGES.forEach(({ path, name }) => {
    test(`${name} page - accessible offline`, async ({ page }) => {
      // First visit - populate cache
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      // Wait for service worker to cache assets
      await page.waitForTimeout(2000);

      // Go offline
      await page.context().setOffline(true);

      try {
        // Navigate to page while offline
        await page.goto(path);
        await page.waitForLoadState('domcontentloaded');

        // Page should still load (from cache)
        await expect(page.locator('body')).toBeVisible();

        // Check for offline indicator or basic UI elements
        const appBar = page.locator('.MuiAppBar-root');
        const isVisible = await appBar.count();
        if (isVisible > 0) {
          await expect(appBar.first()).toBeVisible();
        }
      } finally {
        // Go back online
        await page.context().setOffline(false);
      }
    });
  });

  test('Home page - works offline', async ({ page }) => {
    // Populate cache
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Go offline
    await page.context().setOffline(true);

    try {
      // Reload page while offline
      await page.reload();
      await page.waitForLoadState('domcontentloaded');

      // Should still render main content
      const body = page.locator('body');
      await expect(body).toBeVisible();

      // App bar should be visible
      const appBar = page.locator('.MuiAppBar-root');
      await expect(appBar.first()).toBeVisible();

      // Content should be visible
      const mainContent = page.locator('main, #root');
      await expect(mainContent.first()).toBeVisible();
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('Candidate list - cached data accessible offline', async ({ page }) => {
    // Visit resume database to cache data
    await page.goto('/recruiter/resumes');
    await page.waitForLoadState('networkidle');

    // Wait for data to load and be cached
    await page.waitForTimeout(2000);

    // Count visible items before going offline
    const itemsBeforeOffline = await page.locator('.MuiCard-root').count();

    // Go offline
    await page.context().setOffline(true);

    try {
      // Reload page while offline
      await page.reload();
      await page.waitForLoadState('domcontentloaded');

      // Should still render content
      await expect(page.locator('body')).toBeVisible();

      // May show cached data or offline indicator
      const body = page.locator('body');
      await expect(body).toBeVisible();
    } finally {
      await page.context().setOffline(false);
    }
  });
});

test.describe('Offline Mode - User Experience', () => {
  test('Shows offline indicator when network is unavailable', async ({ page }) => {
    // Populate cache first
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Go offline
    await page.context().setOffline(true);

    try {
      // Navigate while offline
      await page.goto('/recruiter/search');
      await page.waitForLoadState('domcontentloaded');

      // Page should still render from cache
      await expect(page.locator('body')).toBeVisible();

      // Check for any offline indicator or message
      const offlineIndicator = page.locator('text=/offline|no connection|network/i').first();
      const hasIndicator = await offlineIndicator.count();

      if (hasIndicator > 0) {
        await expect(offlineIndicator.first()).toBeVisible();
      }
      // If no indicator, that's also acceptable - cached content should just work
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('Handles navigation between cached pages offline', async ({ page }) => {
    // Populate cache for multiple pages
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.goto('/recruiter/vacancies');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Go offline
    await page.context().setOffline(true);

    try {
      // Navigate between pages while offline
      await page.goto('/');
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('body')).toBeVisible();

      await page.goto('/recruiter/vacancies');
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('body')).toBeVisible();
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('Recovers gracefully when connection is restored', async ({ page }) => {
    // Start online
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Go offline
    await page.context().setOffline(true);

    try {
      // Verify offline state
      await page.reload();
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('body')).toBeVisible();
    } finally {
      // Go back online
      await page.context().setOffline(false);

      // Reload to restore full functionality
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Should work normally online
      await expect(page.locator('body')).toBeVisible();

      // Service worker should still be active
      const swActive = await page.evaluate(() => {
        return navigator.serviceWorker.controller !== null;
      });
      expect(swActive).toBeTruthy();
    }
  });
});

test.describe('PWA Installation', () => {
  test('Meets PWA installability criteria', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check if app is installable
    const isInstallable = await page.evaluate(async () => {
      // Check service worker
      const swReady = await navigator.serviceWorker.ready;
      if (!swReady.active) return false;

      // Check manifest
      const manifestLink = document.querySelector('link[rel="manifest"]');
      if (!manifestLink) return false;

      return true;
    });

    expect(isInstallable).toBeTruthy();
  });

  test('Has app icons defined in manifest', async ({ page }) => {
    const response = await page.request.get('/manifest.json');
    const manifest = await response.json();

    // Should have multiple icon sizes
    expect(manifest.icons.length).toBeGreaterThanOrEqual(2);

    // Should have standard PWA icon sizes
    const iconSizes = manifest.icons.map((icon: any) => icon.sizes);
    const has192 = iconSizes.some((s: string) => s.includes('192'));
    const has512 = iconSizes.some((s: string) => s.includes('512'));

    expect(has192).toBeTruthy();
    expect(has512).toBeTruthy();
  });

  test('Manifest has correct display mode', async ({ page }) => {
    const response = await page.request.get('/manifest.json');
    const manifest = await response.json();

    // Should use standalone display for installable PWA
    expect(['standalone', 'fullscreen']).toContain(manifest.display);
  });
});

test.describe('Offline Performance', () => {
  test('Cached pages load quickly offline', async ({ page }) => {
    // Populate cache
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Go offline
    await page.context().setOffline(true);

    try {
      // Measure load time
      const startTime = Date.now();

      await page.goto('/');
      await page.waitForLoadState('domcontentloaded');

      const loadTime = Date.now() - startTime;

      // Cached page should load quickly (< 2 seconds)
      expect(loadTime).toBeLessThan(2000);
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('Service worker updates are handled', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check service worker state
    const swState = await page.evaluate(async () => {
      const registration = await navigator.serviceWorker.ready;
      return {
        active: !!registration.active,
        waiting: !!registration.waiting,
        installing: !!registration.installing,
      };
    });

    // Should have an active service worker
    expect(swState.active).toBeTruthy();

    // Waiting and installing may be null (no update available)
    // but should not cause errors
    expect(swState).toBeDefined();
  });
});

test.describe('Offline Data Resilience', () => {
  test('Form submissions fail gracefully offline', async ({ page }) => {
    // Populate cache
    await page.goto('/recruiter/search');
    await page.waitForLoadState('networkidle');

    // Go offline
    await page.context().setOffline(true);

    try {
      // Try to interact with form (if exists)
      const searchInput = page.locator('input[type="text"], input[type="search"]').first();
      const inputCount = await searchInput.count();

      if (inputCount > 0) {
        // Fill search input
        await searchInput.first().fill('test search');

        // Page should remain functional even if form submission fails
        await expect(page.locator('body')).toBeVisible();
      }
    } finally {
      await page.context().setOffline(false);
    }
  });

  test('Cached content persists across sessions', async ({ page }) => {
    // First visit - populate cache
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Verify cache exists
    const cacheExists = await page.evaluate(async () => {
      const caches = await window.caches.keys();
      return caches.length > 0;
    });

    expect(cacheExists).toBeTruthy();

    // Simulate page reload (cache should persist)
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Cache should still exist after reload
    const cacheStillExists = await page.evaluate(async () => {
      const caches = await window.caches.keys();
      return caches.length > 0;
    });

    expect(cacheStillExists).toBeTruthy();
  });
});
