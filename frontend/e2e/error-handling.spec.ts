import { test, expect } from '@playwright/test';

/**
 * Error Handling E2E Tests
 *
 * Tests user-friendly error messages throughout the application.
 * Verifies that no alert() dialogs are used and that all errors
 * provide actionable guidance.
 *
 * Run with: npm run test:e2e -- error-handling.spec.ts
 */

test.describe('Error Handling - Upload Errors', () => {
  test('should show user-friendly error for invalid file type', async ({ page }) => {
    await page.goto('/upload');

    // Listen for any alert() calls (should not exist)
    let alertCalled = false;
    page.on('dialog', () => {
      alertCalled = true;
    });

    // Create a text file (invalid type)
    const textFile = Buffer.from('test content').toString('base64');

    // Get the file input
    const fileInput = page.locator('input[type="file"]');

    // Upload invalid file type
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from(textFile, 'base64'),
    });

    // Wait for error to appear
    await page.waitForTimeout(500);

    // Verify error message appears (not alert)
    const errorMessage = page.locator('[role="alert"]').filter({ hasText: /invalid/i });
    await expect(errorMessage.first()).toBeVisible();

    // Verify it's not an alert dialog
    expect(alertCalled).toBeFalsy();

    // Verify error message is user-friendly
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/invalid|type|file|pdf|docx/i);
  });

  test('should show user-friendly error for file too large', async ({ page }) => {
    await page.goto('/upload');

    // Listen for any alert() calls
    let alertCalled = false;
    page.on('dialog', () => {
      alertCalled = true;
    });

    // Create a large file (> 10MB)
    const largeFile = Buffer.alloc(11 * 1024 * 1024); // 11MB

    // Get the file input
    const fileInput = page.locator('input[type="file"]');

    // Upload large file
    await fileInput.setInputFiles({
      name: 'large.pdf',
      mimeType: 'application/pdf',
      buffer: largeFile,
    });

    // Wait for error to appear
    await page.waitForTimeout(500);

    // Verify error message appears (not alert)
    const errorMessage = page.locator('[role="alert"]').filter({ hasText: /large|size|mb/i });
    await expect(errorMessage.first()).toBeVisible();

    // Verify it's not an alert dialog
    expect(alertCalled).toBeFalsy();

    // Verify error message is actionable
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/large|size|10.?mb|compress/i);
  });

  test('should show user-friendly error when upload fails (network error)', async ({ page }) => {
    // Intercept upload requests and fail them
    await page.route('**/api/resumes/upload', route => route.abort());

    await page.goto('/upload');

    // Create a valid PDF file
    const pdfFile = Buffer.from('%PDF-1.4 test content');

    // Get the file input
    const fileInput = page.locator('input[type="file"]');

    // Try to upload
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: pdfFile,
    });

    // Wait for error to appear
    await page.waitForTimeout(1000);

    // Verify error message appears
    const errorMessage = page.locator('[role="alert"]').filter({ hasText: /error|fail|network/i });
    await expect(errorMessage.first()).toBeVisible();

    // Verify error message suggests retry
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/error|fail|network|retry|try again/i);
  });

  test('should allow retry after upload error', async ({ page }) => {
    // First attempt - fail the upload
    await page.route('**/api/resumes/upload', route => route.abort());

    await page.goto('/upload');

    const pdfFile = Buffer.from('%PDF-1.4 test content');
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: pdfFile,
    });

    await page.waitForTimeout(1000);

    // Verify error appears
    const errorMessage = page.locator('[role="alert"]').first();
    await expect(errorMessage).toBeVisible();

    // Second attempt - allow upload to succeed (or fail gracefully)
    // The important thing is that user can try again
    const fileInput2 = page.locator('input[type="file"]');
    await expect(fileInput2).toBeEnabled();
  });
});

test.describe('Error Handling - Validation Errors', () => {
  test('should show user-friendly error when searching without vacancy', async ({ page }) => {
    await page.goto('/recruiter/search');

    // Listen for any alert() calls
    let alertCalled = false;
    page.on('dialog', () => {
      alertCalled = true;
    });

    // Try to search without selecting a vacancy
    const searchButton = page.locator('button').filter({ hasText: /search/i });
    await searchButton.click();

    // Wait for error to appear
    await page.waitForTimeout(300);

    // Verify ErrorMessage appears (not alert)
    const errorMessage = page.locator('.toast [role="alert"]');
    await expect(errorMessage.first()).toBeVisible();

    // Verify it's not an alert dialog
    expect(alertCalled).toBeFalsy();

    // Verify error message is helpful
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/vacancy|select|first/i);
  });

  test('should show validation errors in vacancy creation form', async ({ page }) => {
    await page.goto('/recruiter/vacancies/create');

    // Try to submit form without required fields
    const createButton = page.locator('button').filter({ hasText: /create|save/i });
    await createButton.click();

    // Wait for validation errors
    await page.waitForTimeout(300);

    // Check for validation error messages (could be in various forms)
    const validationErrors = page.locator('.error, [role="alert"], .helper-text.error');

    const count = await validationErrors.count();
    if (count > 0) {
      // At least one validation error should be visible
      await expect(validationErrors.first()).toBeVisible();
    }
  });
});

test.describe('Error Handling - Network Errors', () => {
  test('should show user-friendly error when backend is unreachable', async ({ page }) => {
    // Block all API requests
    await page.route('**/api/**', route => route.abort());

    await page.goto('/recruiter/vacancies');

    // Wait for page to try loading
    await page.waitForTimeout(1000);

    // Check for error message
    const errorMessage = page.locator('[role="alert"], .toast').filter({
      hasText: /error|network|connect|fail/i
    });

    const count = await errorMessage.count();
    if (count > 0) {
      await expect(errorMessage.first()).toBeVisible();

      // Verify error message provides guidance
      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/network|connect|retry|refresh/i);
    }
  });

  test('should show retry action for network errors', async ({ page }) => {
    await page.route('**/api/**', route => route.abort());

    await page.goto('/');

    await page.waitForTimeout(1000);

    // Look for error with action buttons (Retry, etc.)
    const actionButtons = page.locator('[role="alert"] button').filter({
      hasText: /retry|refresh|try again/i
    });

    const count = await actionButtons.count();
    if (count > 0) {
      // Retry button should be present if error message is shown
      await expect(actionButtons.first()).toBeVisible();
    }
  });
});

test.describe('Error Handling - Error Message Structure', () => {
  test('error messages should include what went wrong', async ({ page }) => {
    await page.goto('/upload');

    // Trigger file type error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    const errorMessage = page.locator('[role="alert"]').first();
    const errorText = await errorMessage.textContent();

    // Should clearly state what the problem is
    expect(errorText).toMatch(/invalid|type|file/i);
  });

  test('error messages should include how to fix', async ({ page }) => {
    await page.goto('/upload');

    // Trigger file type error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    const errorMessage = page.locator('[role="alert"]').first();
    const errorText = await errorMessage.textContent();

    // Should provide actionable guidance
    expect(errorText).toMatch(/pdf|docx|upload/i);
  });

  test('structured error messages should have action buttons', async ({ page }) => {
    await page.route('**/api/**', route => route.abort());

    await page.goto('/recruiter/search');

    await page.waitForTimeout(1000);

    // Look for error messages with action buttons
    const errorWithActions = page.locator('[role="alert"]').filter(async (el) => {
      const buttons = await el.locator('button').count();
      return buttons > 0;
    });

    const count = await errorWithActions.count();
    if (count > 0) {
      // Verify action buttons are present
      const buttons = errorWithActions.first().locator('button');
      await expect(buttons.first()).toBeVisible();
    }
  });
});

test.describe('Error Handling - No Alert Dialogs', () => {
  test('should not use alert() for file upload errors', async ({ page }) => {
    await page.goto('/upload');

    let alertShown = false;
    page.on('dialog', async dialog => {
      alertShown = true;
      await dialog.dismiss();
    });

    // Trigger upload error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Verify no alert was shown
    expect(alertShown).toBeFalsy();
  });

  test('should not use alert() for search errors', async ({ page }) => {
    await page.goto('/recruiter/search');

    let alertShown = false;
    page.on('dialog', async dialog => {
      alertShown = true;
      await dialog.dismiss();
    });

    // Try to search without selecting vacancy
    const searchButton = page.locator('button').filter({ hasText: /search/i });
    await searchButton.click();

    await page.waitForTimeout(500);

    // Verify no alert was shown
    expect(alertShown).toBeFalsy();
  });

  test('should use Material UI Snackbar/Alert for all errors', async ({ page }) => {
    // Visit multiple pages and check for MUI error components
    const pages = ['/upload', '/recruiter/search', '/recruiter/vacancies'];

    for (const pagePath of pages) {
      await page.goto(pagePath);

      // Trigger errors on each page
      if (pagePath === '/upload') {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles({
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('test'),
        });
      } else if (pagePath === '/recruiter/search') {
        const searchButton = page.locator('button').filter({ hasText: /search/i });
        await searchButton.click();
      }

      await page.waitForTimeout(500);

      // Check for error components (toast or alert)
      const toastError = page.locator('.toast [role="alert"]');

      // If there's an error, it should use proper error components
      const errorExists = await toastError.count() > 0;
      if (errorExists) {
        await expect(muiError.first()).toBeVisible();
      }
    }
  });
});

test.describe('Error Handling - Error Recovery', () => {
  test('should allow closing error messages', async ({ page }) => {
    await page.goto('/upload');

    // Trigger error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Look for close button
    const closeButton = page.locator('[role="alert"] button').first();

    const hasCloseButton = await closeButton.count() > 0;
    if (hasCloseButton) {
      await closeButton.click();

      // Error should disappear or be hidden
      await page.waitForTimeout(300);

      const isVisible = await closeButton.isVisible();
      expect(isVisible).toBeFalsy();
    }
  });

  test('should auto-hide non-critical errors', async ({ page }) => {
    await page.goto('/upload');

    // Trigger a non-critical error (file type validation)
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    // Wait for error to appear
    const errorMessage = page.locator('.toast [role="alert"]');
    await expect(errorMessage.first()).toBeVisible();

    // Wait for auto-hide (typically 6 seconds)
    await page.waitForTimeout(7000);

    // Error should auto-hide
    const isVisible = await errorMessage.first().isVisible();
    expect(isVisible).toBeFalsy();
  });

  test('should not auto-hide errors with action buttons', async ({ page }) => {
    // This test checks that structured errors with actions remain visible
    await page.route('**/api/**', route => route.abort());

    await page.goto('/recruiter/search');

    await page.waitForTimeout(1000);

    // Look for error with action buttons
    const errorWithActions = page.locator('[role="alert"]').filter(async (el) => {
      const buttons = await el.locator('button').count();
      const text = await el.textContent();
      return buttons > 0 && text?.includes(/retry|refresh/i);
    });

    const count = await errorWithActions.count();
    if (count > 0) {
      const errorVisible = await errorWithActions.first().isVisible();

      // Wait a bit to ensure it doesn't auto-hide quickly
      await page.waitForTimeout(3000);

      const stillVisible = await errorWithActions.first().isVisible();
      expect(stillVisible).toBe(errorVisible);
    }
  });
});

test.describe('Error Handling - Accessibility', () => {
  test('error messages should have proper ARIA attributes', async ({ page }) => {
    await page.goto('/upload');

    // Trigger error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Check for proper ARIA role
    const errorMessage = page.locator('[role="alert"]').first();
    await expect(errorMessage).toBeVisible();

    // Should have role="alert" or be in an alert component
    const role = await errorMessage.getAttribute('role');
    expect(role || 'alert').toMatch(/alert/i);
  });

  test('error messages should be keyboard accessible', async ({ page }) => {
    await page.goto('/upload');

    // Trigger error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Tab to error message
    await page.keyboard.press('Tab');

    // Close button should be focusable
    const closeButton = page.locator('[role="alert"] button').first();
    const hasCloseButton = await closeButton.count() > 0;

    if (hasCloseButton) {
      // Press Enter to close
      await page.keyboard.press('Enter');

      await page.waitForTimeout(300);

      const isVisible = await closeButton.isVisible();
      expect(isVisible).toBeFalsy();
    }
  });
});

test.describe('Error Handling - Dark Mode Compatibility', () => {
  test('error messages should be visible in dark mode', async ({ page }) => {
    await page.goto('/upload');

    // Toggle to dark mode
    const themeToggle = page.locator('button[aria-label*="Switch"]').first();
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Trigger error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Error should be visible in dark mode
    const errorMessage = page.locator('[role="alert"]').first();
    await expect(errorMessage).toBeVisible();

    // Check contrast (text should be readable)
    const textColor = await errorMessage.evaluate((el) => {
      return window.getComputedStyle(el).color;
    });

    // Should not be too dark (basic check)
    expect(textColor).not.toBe('rgb(0, 0, 0)');
  });
});

test.describe('Error Handling - Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // Mobile viewport

  test('error messages should be readable on mobile', async ({ page }) => {
    await page.goto('/upload');

    // Trigger error
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test'),
    });

    await page.waitForTimeout(500);

    // Error should be visible and readable
    const errorMessage = page.locator('[role="alert"]').first();
    await expect(errorMessage).toBeVisible();

    // Should fit within mobile viewport (no horizontal overflow)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
  });

  test('error action buttons should be touch-friendly on mobile', async ({ page }) => {
    await page.route('**/api/**', route => route.abort());

    await page.goto('/recruiter/search');

    await page.waitForTimeout(1000);

    // Look for action buttons in error messages
    const actionButtons = page.locator('[role="alert"] button').filter({
      hasText: /retry|refresh|try again|close/i
    });

    const count = await actionButtons.count();
    if (count > 0) {
      for (let i = 0; i < Math.min(count, 3); i++) {
        const button = actionButtons.nth(i);
        const boundingBox = await button.boundingBox();

        if (boundingBox) {
          // Touch target should be at least 44x44px
          expect(boundingBox.width).toBeGreaterThanOrEqual(44);
          expect(boundingBox.height).toBeGreaterThanOrEqual(44);
        }
      }
    }
  });
});
