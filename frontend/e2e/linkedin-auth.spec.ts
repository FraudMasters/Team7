/**
 * LinkedIn Authentication E2E Tests
 *
 * Tests the OAuth 2.0 authentication flow for LinkedIn integration:
 * - Authorization URL generation
 * - OAuth callback processing
 * - Token management
 * - Error handling
 */

import { test, expect, Page } from '@playwright/test';

test.describe('LinkedIn Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as recruiter
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
  });

  test('should display LinkedIn auth button when not connected', async ({ page }) => {
    await page.goto('/recruiter/linkedin/import');
    
    // Should show connect button
    const connectButton = page.getByRole('button', { name: /connect.*linkedin/i });
    await expect(connectButton).toBeVisible();
  });

  test('should generate OAuth URL when connect button clicked', async ({ page, context }) => {
    await page.goto('/recruiter/linkedin/import');
    
    // Click connect button
    const connectButton = page.getByRole('button', { name: /connect.*linkedin/i });
    
    // Listen for popup or redirect
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      connectButton.click(),
    ]);
    
    // Should redirect to LinkedIn OAuth
    expect(newPage.url()).toContain('linkedin.com/oauth');
    expect(newPage.url()).toContain('response_type=code');
    expect(newPage.url()).toContain('client_id=');
    expect(newPage.url()).toContain('redirect_uri=');
    expect(newPage.url()).toContain('state=');
  });

  test('should handle OAuth callback successfully', async ({ page }) => {
    // Mock the callback endpoint
    await page.route('**/api/linkedin/auth/callback**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'LinkedIn account connected successfully',
          access_token: 'mock_token_123',
          expires_in: 3600,
        }),
      });
    });
    
    // Navigate to callback URL
    await page.goto('/recruiter/linkedin/import?code=test_code&state=test_state');
    
    // Should show success message
    await expect(page.getByText(/connected.*success/i)).toBeVisible();
  });

  test('should handle OAuth error gracefully', async ({ page }) => {
    await page.route('**/api/linkedin/auth/callback**', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          message: 'Invalid state parameter',
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import?code=test_code&state=invalid_state');
    
    // Should show error message
    await expect(page.getByText(/error|failed/i)).toBeVisible();
  });

  test('should show connected status after successful auth', async ({ page }) => {
    // Mock auth status
    await page.route('**/api/linkedin/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          connected: true,
          expires_at: new Date(Date.now() + 3600000).toISOString(),
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Should show connected status
    await expect(page.getByText(/connected/i)).toBeVisible();
  });

  test('should allow disconnecting LinkedIn account', async ({ page }) => {
    // Mock connected status
    await page.route('**/api/linkedin/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          connected: true,
          expires_at: new Date(Date.now() + 3600000).toISOString(),
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Click disconnect button
    const disconnectButton = page.getByRole('button', { name: /disconnect/i });
    if (await disconnectButton.isVisible()) {
      await disconnectButton.click();
      
      // Confirm disconnect
      await page.getByRole('button', { name: /confirm/i }).click();
      
      // Should show disconnected
      await expect(page.getByRole('button', { name: /connect.*linkedin/i })).toBeVisible();
    }
  });
});

test.describe('LinkedIn Auth - Error Scenarios', () => {
  test('should handle rate limit exceeded', async ({ page }) => {
    await page.route('**/api/linkedin/**', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'LinkedIn API rate limit exceeded. Please try again later.',
        }),
      });
    });
    
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    await page.goto('/recruiter/linkedin/import');
    
    // Should show rate limit message
    await expect(page.getByText(/rate limit/i)).toBeVisible();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    await page.route('**/api/linkedin/**', async (route) => {
      await route.abort('failed');
    });
    
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    await page.goto('/recruiter/linkedin/import');
    
    // Should show error state
    await expect(page.getByText(/error|failed|try again/i)).toBeVisible();
  });
});
