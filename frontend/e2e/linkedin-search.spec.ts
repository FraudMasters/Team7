/**
 * LinkedIn Search E2E Tests
 *
 * Tests the LinkedIn candidate search functionality:
 * - Boolean search with filters
 * - Search results display
 * - Pagination
 * - Error handling
 */

import { test, expect, Page } from '@playwright/test';

test.describe('LinkedIn Candidate Search', () => {
  test.beforeEach(async ({ page }) => {
    // Login as recruiter with LinkedIn connected
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

  test('should display search form with all filters', async ({ page }) => {
    await page.goto('/recruiter/linkedin/search');
    
    // Check for search input
    await expect(page.getByPlaceholder(/search.*keywords/i)).toBeVisible();
    
    // Check for filter options
    await expect(page.getByLabel(/location/i)).toBeVisible();
    await expect(page.getByLabel(/skills/i)).toBeVisible();
    await expect(page.getByLabel(/title/i)).toBeVisible();
    await expect(page.getByLabel(/experience/i)).toBeVisible();
    
    // Check for search button
    await expect(page.getByRole('button', { name: /search/i })).toBeVisible();
  });

  test('should perform search and display results', async ({ page }) => {
    // Mock search API
    await page.route('**/api/linkedin/search**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: 'profile-1',
              name: 'John Doe',
              headline: 'Senior Software Engineer at Tech Corp',
              location: 'San Francisco, CA',
              skills: ['Python', 'React', 'AWS'],
              experience_years: 8,
              profile_url: 'https://linkedin.com/in/johndoe',
            },
            {
              id: 'profile-2',
              name: 'Jane Smith',
              headline: 'Full Stack Developer at Startup Inc',
              location: 'New York, NY',
              skills: ['JavaScript', 'Node.js', 'MongoDB'],
              experience_years: 5,
              profile_url: 'https://linkedin.com/in/janesmith',
            },
          ],
          total: 2,
          page: 1,
          page_size: 10,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    // Enter search keywords
    await page.getByPlaceholder(/search.*keywords/i).fill('software engineer');
    
    // Click search
    await page.getByRole('button', { name: /search/i }).click();
    
    // Wait for results
    await expect(page.getByText('John Doe')).toBeVisible();
    await expect(page.getByText('Jane Smith')).toBeVisible();
  });

  test('should support boolean search operators', async ({ page }) => {
    let capturedQuery = '';
    
    await page.route('**/api/linkedin/search**', async (route) => {
      const url = new URL(route.request().url());
      capturedQuery = url.searchParams.get('keywords') || '';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], total: 0 }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    // Test AND operator
    await page.getByPlaceholder(/search.*keywords/i).fill('Python AND Django');
    await page.getByRole('button', { name: /search/i }).click();
    await page.waitForResponse('**/api/linkedin/search**');
    expect(capturedQuery).toContain('AND');
    
    // Test OR operator
    await page.getByPlaceholder(/search.*keywords/i).fill('React OR Vue');
    await page.getByRole('button', { name: /search/i }).click();
    await page.waitForResponse('**/api/linkedin/search**');
    expect(capturedQuery).toContain('OR');
    
    // Test NOT operator
    await page.getByPlaceholder(/search.*keywords/i).fill('Java NOT JavaScript');
    await page.getByRole('button', { name: /search/i }).click();
    await page.waitForResponse('**/api/linkedin/search**');
    expect(capturedQuery).toContain('NOT');
  });

  test('should apply location filter', async ({ page }) => {
    let capturedLocation = '';
    
    await page.route('**/api/linkedin/search**', async (route) => {
      const url = new URL(route.request().url());
      capturedLocation = url.searchParams.get('location') || '';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], total: 0 }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    await page.getByPlaceholder(/search.*keywords/i).fill('developer');
    await page.getByLabel(/location/i).fill('San Francisco');
    await page.getByRole('button', { name: /search/i }).click();
    
    await page.waitForResponse('**/api/linkedin/search**');
    expect(capturedLocation).toBe('San Francisco');
  });

  test('should apply skills filter', async ({ page }) => {
    let capturedSkills = '';
    
    await page.route('**/api/linkedin/search**', async (route) => {
      const url = new URL(route.request().url());
      capturedSkills = url.searchParams.get('skills') || '';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], total: 0 }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    await page.getByPlaceholder(/search.*keywords/i).fill('engineer');
    await page.getByLabel(/skills/i).fill('Python, React');
    await page.getByRole('button', { name: /search/i }).click();
    
    await page.waitForResponse('**/api/linkedin/search**');
    expect(capturedSkills).toContain('Python');
  });

  test('should show empty state when no results', async ({ page }) => {
    await page.route('**/api/linkedin/search**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], total: 0 }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    await page.getByPlaceholder(/search.*keywords/i).fill('nonexistent skill xyz123');
    await page.getByRole('button', { name: /search/i }).click();
    
    // Should show empty state message
    await expect(page.getByText(/no.*results|no.*candidates/i)).toBeVisible();
  });

  test('should paginate through results', async ({ page }) => {
    let requestCount = 0;
    
    await page.route('**/api/linkedin/search**', async (route) => {
      requestCount++;
      const url = new URL(route.request().url());
      const pageParam = parseInt(url.searchParams.get('page') || '1');
      
      const allResults = Array.from({ length: 25 }, (_, i) => ({
        id: `profile-${i + 1}`,
        name: `Candidate ${i + 1}`,
        headline: `Developer ${i + 1}`,
        location: 'City',
        skills: ['Skill'],
        experience_years: 5,
        profile_url: `https://linkedin.com/in/candidate${i + 1}`,
      }));
      
      const pageSize = 10;
      const start = (pageParam - 1) * pageSize;
      const results = allResults.slice(start, start + pageSize);
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results,
          total: allResults.length,
          page: pageParam,
          page_size: pageSize,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    await page.getByPlaceholder(/search.*keywords/i).fill('developer');
    await page.getByRole('button', { name: /search/i }).click();
    
    // Should show first page
    await expect(page.getByText('Candidate 1')).toBeVisible();
    
    // Click next page
    const nextButton = page.getByRole('button', { name: /next/i });
    if (await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForResponse('**/api/linkedin/search**');
      
      // Should show second page
      await expect(page.getByText('Candidate 11')).toBeVisible();
    }
  });

  test('should display candidate profile details in results', async ({ page }) => {
    await page.route('**/api/linkedin/search**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: 'profile-1',
              name: 'John Doe',
              headline: 'Senior Software Engineer at Tech Corp',
              location: 'San Francisco, CA',
              skills: ['Python', 'React', 'AWS', 'Docker', 'Kubernetes'],
              experience_years: 8,
              profile_url: 'https://linkedin.com/in/johndoe',
              summary: 'Experienced software engineer with expertise in cloud technologies.',
              education: ['BS Computer Science, Stanford University'],
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    await page.getByPlaceholder(/search.*keywords/i).fill('john doe');
    await page.getByRole('button', { name: /search/i }).click();
    
    // Check displayed information
    await expect(page.getByText('John Doe')).toBeVisible();
    await expect(page.getByText('Senior Software Engineer')).toBeVisible();
    await expect(page.getByText('San Francisco, CA')).toBeVisible();
    await expect(page.getByText('Python')).toBeVisible();
    await expect(page.getByText('8')).toBeVisible(); // Experience years
  });

  test('should show rate limit warning when approaching limit', async ({ page }) => {
    await page.route('**/api/linkedin/rate-limit', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          requests_remaining: 10,
          reset_at: new Date(Date.now() + 3600000).toISOString(),
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/search');
    
    // Should show rate limit warning
    await expect(page.getByText(/10.*requests.*remaining/i)).toBeVisible();
  });
});

test.describe('LinkedIn Search - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display mobile-friendly search interface', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    await page.goto('/recruiter/linkedin/search');
    
    // Search form should be visible and usable
    await expect(page.getByPlaceholder(/search.*keywords/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /search/i })).toBeVisible();
  });
});
