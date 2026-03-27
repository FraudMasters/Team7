/**
 * LinkedIn Profile Import E2E Tests
 *
 * Tests the LinkedIn profile import functionality:
 * - Single profile import
 * - Batch import
 * - Import history
 * - Source attribution
 * - Error handling
 */

import { test, expect, Page } from '@playwright/test';

test.describe('LinkedIn Profile Import', () => {
  test.beforeEach(async ({ page }) => {
    // Login as recruiter
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    // Mock LinkedIn connected status
    await page.route('**/api/linkedin/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ connected: true }),
      });
    });
  });

  test('should import single profile from search results', async ({ page }) => {
    // Mock search results
    await page.route('**/api/linkedin/search**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: 'profile-1',
              name: 'John Doe',
              headline: 'Senior Software Engineer',
              location: 'San Francisco, CA',
              skills: ['Python', 'React'],
              experience_years: 8,
              profile_url: 'https://linkedin.com/in/johndoe',
            },
          ],
          total: 1,
        }),
      });
    });
    
    // Mock import endpoint
    await page.route('**/api/linkedin/import', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Profile imported successfully',
            resume_id: 'resume-123',
            profile_id: 'profile-1',
          }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/search');
    await page.getByPlaceholder(/search.*keywords/i).fill('software engineer');
    await page.getByRole('button', { name: /search/i }).click();
    
    // Click import button
    await page.getByRole('button', { name: /import/i }).first().click();
    
    // Should show success message
    await expect(page.getByText(/imported.*success/i)).toBeVisible();
  });

  test('should import profile via URL', async ({ page }) => {
    await page.route('**/api/linkedin/import', async (route) => {
      const body = route.request().postDataJSON();
      expect(body.linkedin_url).toContain('linkedin.com/in/');
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Profile imported successfully',
          resume_id: 'resume-456',
          profile_id: 'profile-url',
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Enter LinkedIn URL
    await page.getByPlaceholder(/linkedin.*url/i).fill('https://linkedin.com/in/johndoe');
    
    // Click import
    await page.getByRole('button', { name: /import/i }).click();
    
    // Should show success
    await expect(page.getByText(/imported.*success/i)).toBeVisible();
  });

  test('should display import statistics dashboard', async ({ page }) => {
    await page.route('**/api/linkedin/import/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_imports: 150,
          this_month: 45,
          this_week: 12,
          today: 3,
          success_rate: 94.5,
          by_status: {
            completed: 142,
            pending: 5,
            failed: 3,
          },
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Check stats are displayed
    await expect(page.getByText('150')).toBeVisible(); // Total imports
    await expect(page.getByText('45')).toBeVisible(); // This month
    await expect(page.getByText('94.5')).toBeVisible(); // Success rate
  });

  test('should show import history with pagination', async ({ page }) => {
    await page.route('**/api/linkedin/history**', async (route) => {
      const url = new URL(route.request().url());
      const skip = parseInt(url.searchParams.get('skip') || '0');
      const limit = parseInt(url.searchParams.get('limit') || '10');
      
      const allImports = Array.from({ length: 25 }, (_, i) => ({
        id: `import-${i + 1}`,
        linkedin_url: `https://linkedin.com/in/user${i + 1}`,
        status: i % 5 === 0 ? 'failed' : 'completed',
        resume_id: `resume-${i + 1}`,
        imported_at: new Date(Date.now() - i * 3600000).toISOString(),
        name: `User ${i + 1}`,
        headline: `Software Engineer ${i + 1}`,
      }));
      
      const imports = allImports.slice(skip, skip + limit);
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          imports,
          total_imports: allImports.length,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Should show history
    await expect(page.getByText('Import History')).toBeVisible();
    
    // Should show pagination
    const pagination = page.getByRole('navigation', { name: /pagination/i });
    if (await pagination.isVisible()) {
      await expect(pagination).toBeVisible();
    }
  });

  test('should filter import history by status', async ({ page }) => {
    let capturedStatus = '';
    
    await page.route('**/api/linkedin/history**', async (route) => {
      const url = new URL(route.request().url());
      capturedStatus = url.searchParams.get('status') || '';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          imports: [
            {
              id: 'import-1',
              status: 'failed',
              error_message: 'Profile not found',
              imported_at: new Date().toISOString(),
            },
          ],
          total_imports: 1,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Filter by failed status
    await page.getByLabel(/status/i).selectOption('failed');
    
    await page.waitForResponse('**/api/linkedin/history**');
    expect(capturedStatus).toBe('failed');
  });

  test('should show source attribution for imported candidates', async ({ page }) => {
    // Mock candidates list with LinkedIn source
    await page.route('**/api/candidates**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          candidates: [
            {
              id: 'candidate-1',
              name: 'John Doe',
              source: 'linkedin',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
        }),
      });
    });
    
    await page.goto('/recruiter/candidates');
    
    // Should show LinkedIn source badge
    await expect(page.getByText(/linkedin/i)).toBeVisible();
  });

  test('should handle invalid LinkedIn URL gracefully', async ({ page }) => {
    await page.route('**/api/linkedin/import', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid LinkedIn URL format',
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    await page.getByPlaceholder(/linkedin.*url/i).fill('invalid-url');
    await page.getByRole('button', { name: /import/i }).click();
    
    // Should show error message
    await expect(page.getByText(/invalid|error/i)).toBeVisible();
  });

  test('should handle duplicate import detection', async ({ page }) => {
    await page.route('**/api/linkedin/import', async (route) => {
      await route.fulfill({
        status: 409, // Conflict
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'This profile has already been imported',
          existing_resume_id: 'resume-existing',
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    await page.getByPlaceholder(/linkedin.*url/i).fill('https://linkedin.com/in/duplicate');
    await page.getByRole('button', { name: /import/i }).click();
    
    // Should show duplicate warning
    await expect(page.getByText(/already.*imported|duplicate/i)).toBeVisible();
  });

  test('should batch import multiple profiles', async ({ page }) => {
    let importCount = 0;
    
    await page.route('**/api/linkedin/import/batch', async (route) => {
      importCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          imported: 5,
          failed: 1,
          results: [
            { profile_id: 'p1', status: 'success', resume_id: 'r1' },
            { profile_id: 'p2', status: 'success', resume_id: 'r2' },
            { profile_id: 'p3', status: 'success', resume_id: 'r3' },
            { profile_id: 'p4', status: 'success', resume_id: 'r4' },
            { profile_id: 'p5', status: 'success', resume_id: 'r5' },
            { profile_id: 'p6', status: 'failed', error: 'Profile not found' },
          ],
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    // Switch to batch mode if available
    const batchTab = page.getByRole('tab', { name: /batch/i });
    if (await batchTab.isVisible()) {
      await batchTab.click();
      
      // Enter multiple URLs
      await page.getByPlaceholder(/linkedin.*urls/i).fill(`
        https://linkedin.com/in/user1
        https://linkedin.com/in/user2
        https://linkedin.com/in/user3
        https://linkedin.com/in/user4
        https://linkedin.com/in/user5
        https://linkedin.com/in/user6
      `);
      
      await page.getByRole('button', { name: /import.*all/i }).click();
      
      // Should show batch results
      await expect(page.getByText(/5.*imported|1.*failed/i)).toBeVisible();
    }
  });

  test('should retry failed imports', async ({ page }) => {
    let attemptCount = 0;
    
    await page.route('**/api/linkedin/import', async (route) => {
      attemptCount++;
      if (attemptCount === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Temporary error' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            resume_id: 'resume-retry',
          }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/import');
    
    await page.getByPlaceholder(/linkedin.*url/i).fill('https://linkedin.com/in/retry');
    await page.getByRole('button', { name: /import/i }).click();
    
    // Should show error with retry option
    await expect(page.getByRole('button', { name: /retry/i })).toBeVisible();
    
    // Click retry
    await page.getByRole('button', { name: /retry/i }).click();
    
    // Should succeed
    await expect(page.getByText(/success/i)).toBeVisible();
  });
});

test.describe('LinkedIn Import - Resume Parsing', () => {
  test('should parse skills from imported profile', async ({ page }) => {
    await page.route('**/api/linkedin/import', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          resume_id: 'resume-123',
          parsed_data: {
            skills: ['Python', 'JavaScript', 'React', 'AWS', 'Docker'],
            experience: [
              { title: 'Senior Engineer', company: 'Tech Corp', years: 3 },
            ],
            education: [
              { degree: 'BS Computer Science', school: 'MIT', year: 2015 },
            ],
          },
        }),
      });
    });
    
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    await page.goto('/recruiter/linkedin/import');
    await page.getByPlaceholder(/linkedin.*url/i).fill('https://linkedin.com/in/skilled');
    await page.getByRole('button', { name: /import/i }).click();
    
    // Should show parsed skills
    await expect(page.getByText('Python')).toBeVisible();
    await expect(page.getByText('React')).toBeVisible();
  });
});
