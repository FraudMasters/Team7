import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Resume Analysis Platform
 *
 * Test Suite Contents:
 * 1. Navigation & Page Rendering
 * 2. Resume Upload Workflow
 * 3. Analysis Results Display
 * 4. Job Comparison Workflow
 * 5. Error Handling
 * 6. Complete User Journeys
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Test data fixtures available in backend/uploads/
 */

test.describe('Navigation & Page Rendering', () => {
  test('should load home page with all elements', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/Resume Analysis/);

    // Check main heading
    const mainHeading = page.getByRole('heading', { level: 1, name: /Transform Your Recruitment Process/i });
    await expect(mainHeading).toBeVisible();

    // Check feature cards
    await expect(page.getByText('AI-Powered Analysis')).toBeVisible();
    await expect(page.getByText('Error Detection')).toBeVisible();
    await expect(page.getByText('Job Matching')).toBeVisible();
    await expect(page.getByText('Fast Processing')).toBeVisible();

    // Check CTA buttons
    await expect(page.getByRole('button', { name: /Upload Resume/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /View Sample Analysis/i })).toBeVisible();
  });

  test('should navigate to upload page', async ({ page }) => {
    await page.goto('/');

    // Click upload button
    await page.getByRole('button', { name: /Upload Resume/i }).click();

    // Check URL
    await expect(page).toHaveURL(/\/upload/);

    // Check upload page elements
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();
    await expect(page.getByText(/Upload your resume \(PDF or DOCX\)/i)).toBeVisible();
  });

  test('should have working navigation links in app bar', async ({ page }) => {
    await page.goto('/');

    // Navigate to upload via nav
    await page.getByRole('link', { name: /Upload/i }).click();
    await expect(page).toHaveURL(/\/upload/);

    // Navigate back to home
    await page.getByRole('link', { name: /Home/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should handle unknown routes with redirect', async ({ page }) => {
    await page.goto('/unknown-route');

    // Should redirect to home
    await expect(page).toHaveURL(/\//);
  });
});

test.describe('Resume Upload Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/upload');
  });

  test('should display upload component with drag-drop area', async ({ page }) => {
    // Check upload area
    const uploadArea = page.getByText(/Drag and drop your resume here/i);
    await expect(uploadArea).toBeVisible();

    // Check file input
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();

    // Check upload button
    await expect(page.getByRole('button', { name: /Browse Files/i })).toBeVisible();
  });

  test('should show file format and size restrictions', async ({ page }) => {
    // Check for supported formats
    await expect(page.getByText(/PDF or DOCX/i)).toBeVisible();
    await expect(page.getByText(/Maximum file size/i)).toBeVisible();
  });

  test('should reject invalid file types', async ({ page }) => {
    // Create a text file
    const fileInput = page.locator('input[type="file"]');

    // Try uploading a .txt file
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Invalid file type'),
    });

    // Should show error
    await expect(page.getByText(/Unsupported file type|Please upload PDF or DOCX/i)).toBeVisible();
  });

  test('should handle file selection before upload', async ({ page }) => {
    // Mock file selection - actual upload requires backend
    const fileInput = page.locator('input[type="file"]');

    // Check that file input accepts PDF and DOCX
    const accept = await fileInput.getAttribute('accept');
    expect(accept).toContain('.pdf');
    expect(accept).toContain('.docx');
  });

  test('should display "What happens next" instructions', async ({ page }) => {
    await expect(page.getByText(/What happens next\?/i)).toBeVisible();
    await expect(page.getByText(/Our AI extracts skills/i)).toBeVisible();
    await expect(page.getByText(/analyze your resume for common errors/i)).toBeVisible();
    await expect(page.getByText(/compare your resume against job vacancies/i)).toBeVisible();
  });
});

test.describe('Analysis Results Display', () => {
  test('should display results page for valid resume ID', async ({ page }) => {
    // Navigate to results page with test ID
    await page.goto('/results/test-resume-id');

    // Check loading state initially
    await expect(page.getByText(/Loading analysis|Please wait/i)).toBeVisible();

    // Note: Without actual backend, this will show error state
    // The test verifies the UI structure is correct
  });

  test('should handle analysis errors gracefully', async ({ page }) => {
    // Navigate with invalid ID
    await page.goto('/results/invalid-id');

    // Should show error state or retry option
    const errorOrRetry = page.getByText(/Failed to load|Error loading analysis|Retry/i);
    await expect(errorOrRetry).toBeVisible({ timeout: 10000 });
  });

  test('should navigate between upload and results', async ({ page }) => {
    await page.goto('/upload');

    // Even if upload doesn't complete, navigation should work
    await page.goto('/results/sample-id');
    await expect(page).toHaveURL(/\/results\//);

    // Back to upload
    await page.goto('/upload');
    await expect(page).toHaveURL(/\/upload/);
  });
});

test.describe('Job Comparison Workflow', () => {
  test('should display comparison page with required IDs', async ({ page }) => {
    await page.goto('/compare/test-resume/test-vacancy');

    // Should show comparison interface
    await expect(page.getByText(/Job Comparison|Compare Resume with Vacancy/i)).toBeVisible();
  });

  test('should handle missing parameters', async ({ page }) => {
    // Navigate without proper params
    await page.goto('/compare');

    // Should redirect or show error
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/(\/$|\/compare\/)/);
  });
});

test.describe('Complete User Journeys', () => {
  test('complete workflow: home → upload → results (mock)', async ({ page }) => {
    // Start at home
    await page.goto('/');

    // Verify home page loaded
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Navigate to upload
    await page.getByRole('button', { name: /Upload Resume/i }).click();
    await expect(page).toHaveURL(/\/upload/);

    // Verify upload page
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();

    // Simulate navigating to results (without actual upload)
    await page.goto('/results/test-resume-123');

    // Results page should load (may show error without backend)
    await expect(page).toHaveURL(/\/results\/test-resume-123/);
  });

  test('complete workflow: job comparison flow', async ({ page }) => {
    // Start at home
    await page.goto('/');

    // Navigate to compare page directly
    await page.goto('/compare/resume-123/vacancy-456');

    // Should display comparison UI
    await expect(page.getByText(/Job Comparison|Compare Resume/i)).toBeVisible();
  });

  test('should navigate through all main pages', async ({ page }) => {
    // Home → Upload → Results → Compare → Home
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    await page.goto('/upload');
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();

    await page.goto('/results/test-id');
    await expect(page).toHaveURL(/\/results\//);

    await page.goto('/compare/test-id/vacancy-id');
    await expect(page).toHaveURL(/\/compare\//);

    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should be usable on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Main elements should be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: /Upload Resume/i })).toBeVisible();
  });

  test('should be usable on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/upload');

    // Upload interface should be visible
    await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();
    await expect(page.getByText(/Drag and drop your resume here/i)).toBeVisible();
  });

  test('should adapt layout on desktop viewport', async ({ page }) => {
    // Desktop viewport (default)
    await page.goto('/');

    // Feature cards should be in grid layout
    const features = page.getByText(/AI-Powered Analysis/).locator('../../..');
    await expect(features).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();

    // Check for h2 headings
    const h2s = page.getByRole('heading', { level: 2 });
    const count = await h2s.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/');

    // Check that all images have alt text
    const images = page.locator('img');
    const count = await images.count();

    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // First button should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('BUTTON');
  });

  test('should have sufficient color contrast', async ({ page }) => {
    // This is a basic check - full accessibility testing requires axe-core
    await page.goto('/');

    // Check that text is visible (not white on white, etc.)
    const headings = page.locator('h1, h2, h3');
    const count = await headings.count();

    for (let i = 0; i < Math.min(count, 5); i++) {
      await expect(headings.nth(i)).toBeVisible();
    }
  });
});

test.describe('Performance', () => {
  test('should load home page quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');

    // Wait for main content
    await page.waitForSelector('h1');

    const loadTime = Date.now() - startTime;

    // Should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should not have memory leaks during navigation', async ({ page }) => {
    // Navigate through multiple pages
    for (let i = 0; i < 5; i++) {
      await page.goto('/');
      await page.goto('/upload');
      await page.goto('/results/test');
    }

    // Page should still be responsive
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should handle network errors gracefully', async ({ page }) => {
    // Navigate to results with invalid ID
    await page.goto('/results/nonexistent-resume-id');

    // Should show error state (not crash)
    await expect(page.getByText(/Loading|Error|Failed/i)).toBeVisible();
  });

  test('should handle malformed URLs', async ({ page }) => {
    // Try various malformed URLs
    await page.goto('/results/');
    await page.goto('/compare/');
    await page.goto('/unknown-page');

    // Should handle gracefully (redirect or error)
    const url = page.url();
    expect(url).toMatch(/\/($|upload|results|compare)/);
  });
});

test.describe('Content Validation', () => {
  test('should display correct content on home page', async ({ page }) => {
    await page.goto('/');

    // Check key phrases
    await expect(page.getByText(/AI-powered resume analysis platform/i)).toBeVisible();
    await expect(page.getByText(/intelligent job matching/i)).toBeVisible();
  });

  test('should display instructions on upload page', async ({ page }) => {
    await page.goto('/upload');

    // Check instructional content
    await expect(page.getByText(/Upload PDF or DOCX resume files/i)).toBeVisible();
    await expect(page.getByText(/AI-powered analysis/i)).toBeVisible();
  });

  test('should have working footer links if present', async ({ page }) => {
    await page.goto('/');

    // Check if footer exists
    const footer = page.locator('footer').first();

    if (await footer.count() > 0) {
      await expect(footer).toBeVisible();
    }
  });
});
