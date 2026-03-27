/**
 * LinkedIn Campaigns E2E Tests
 *
 * Tests the LinkedIn outreach campaign management:
 * - Campaign creation
 * - Campaign list and filtering
 * - Campaign detail view
 * - Outreach tracking
 * - Response rate analytics
 */

import { test, expect, Page } from '@playwright/test';

test.describe('LinkedIn Campaigns Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as recruiter
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
  });

  test('should display campaigns list page', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          campaigns: [
            {
              id: 'campaign-1',
              name: 'Senior Engineers Q1',
              status: 'active',
              sent_count: 50,
              response_count: 15,
              response_rate: 30.0,
              created_at: '2026-01-15T10:00:00Z',
            },
            {
              id: 'campaign-2',
              name: 'Product Managers Outreach',
              status: 'paused',
              sent_count: 25,
              response_count: 5,
              response_rate: 20.0,
              created_at: '2026-02-01T14:00:00Z',
            },
          ],
          total: 2,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns');
    
    // Should show campaigns
    await expect(page.getByText('Senior Engineers Q1')).toBeVisible();
    await expect(page.getByText('Product Managers Outreach')).toBeVisible();
    
    // Should show status badges
    await expect(page.getByText('active', { exact: false })).toBeVisible();
    await expect(page.getByText('paused', { exact: false })).toBeVisible();
  });

  test('should create new campaign', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        expect(body.name).toBeTruthy();
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'campaign-new',
            name: body.name,
            status: 'draft',
            sent_count: 0,
            response_count: 0,
            response_rate: 0,
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ campaigns: [], total: 0 }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/campaigns');
    
    // Click create button
    await page.getByRole('button', { name: /create.*campaign|new.*campaign/i }).click();
    
    // Fill campaign form
    await page.getByLabel(/campaign.*name/i).fill('Test Campaign 2026');
    await page.getByLabel(/description/i).fill('Outreach for senior developers');
    
    // Submit
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Should show success and redirect
    await expect(page.getByText(/campaign.*created/i)).toBeVisible();
  });

  test('should display campaign detail with outreach tracking', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns/campaign-1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'campaign-1',
          name: 'Senior Engineers Q1',
          status: 'active',
          sent_count: 50,
          response_count: 15,
          response_rate: 30.0,
          target_count: 100,
          description: 'Outreach to senior engineers',
          created_at: '2026-01-15T10:00:00Z',
        }),
      });
    });
    
    await page.route('**/api/linkedin/campaigns/campaign-1/outreach**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          outreach: [
            {
              id: 'outreach-1',
              candidate_name: 'John Doe',
              sent_at: '2026-01-16T09:00:00Z',
              response_status: 'responded',
              responded_at: '2026-01-17T14:30:00Z',
            },
            {
              id: 'outreach-2',
              candidate_name: 'Jane Smith',
              sent_at: '2026-01-16T10:00:00Z',
              response_status: 'pending',
              responded_at: null,
            },
            {
              id: 'outreach-3',
              candidate_name: 'Bob Johnson',
              sent_at: '2026-01-16T11:00:00Z',
              response_status: 'not_responded',
              responded_at: null,
            },
          ],
          total: 3,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns/campaign-1');
    
    // Should show campaign details
    await expect(page.getByText('Senior Engineers Q1')).toBeVisible();
    await expect(page.getByText('50')).toBeVisible(); // Sent count
    await expect(page.getByText('15')).toBeVisible(); // Response count
    await expect(page.getByText('30')).toBeVisible(); // Response rate
    
    // Should show outreach list
    await expect(page.getByText('John Doe')).toBeVisible();
    await expect(page.getByText('Jane Smith')).toBeVisible();
  });

  test('should update campaign status', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns/campaign-1', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'campaign-1',
            name: 'Test Campaign',
            status: 'paused',
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'campaign-1',
            name: 'Test Campaign',
            status: 'active',
          }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/campaigns/campaign-1');
    
    // Click pause button
    await page.getByRole('button', { name: /pause/i }).click();
    
    // Confirm
    await page.getByRole('button', { name: /confirm/i }).click();
    
    // Should show paused status
    await expect(page.getByText(/paused/i)).toBeVisible();
  });

  test('should filter campaigns by status', async ({ page }) => {
    let capturedStatus = '';
    
    await page.route('**/api/linkedin/campaigns**', async (route) => {
      const url = new URL(route.request().url());
      capturedStatus = url.searchParams.get('status') || '';
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          campaigns: [
            {
              id: 'campaign-1',
              name: 'Active Campaign',
              status: 'active',
            },
          ],
          total: 1,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns');
    
    // Filter by active
    await page.getByLabel(/status/i).selectOption('active');
    
    await page.waitForResponse('**/api/linkedin/campaigns**');
    expect(capturedStatus).toBe('active');
  });

  test('should sort campaigns by response rate', async ({ page }) => {
    let capturedSort = '';
    
    await page.route('**/api/linkedin/campaigns**', async (route) => {
      const url = new URL(route.request().url());
      capturedSort = url.searchParams.get('sort_by') || '';
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ campaigns: [], total: 0 }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns');
    
    // Sort by response rate
    await page.getByLabel(/sort/i).selectOption('response_rate');
    
    await page.waitForResponse('**/api/linkedin/campaigns**');
    expect(capturedSort).toBe('response_rate');
  });

  test('should delete campaign with confirmation', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns/campaign-delete', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'campaign-delete',
            name: 'Campaign to Delete',
            status: 'draft',
          }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/campaigns/campaign-delete');
    
    // Click delete
    await page.getByRole('button', { name: /delete/i }).click();
    
    // Confirm deletion
    await page.getByRole('button', { name: /confirm|delete/i }).click();
    
    // Should redirect to campaigns list
    await page.waitForURL(/\/linkedin\/campaigns$/);
    await expect(page.getByText(/campaign.*deleted/i)).toBeVisible();
  });

  test('should display campaign performance metrics', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns/campaign-1/analytics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sent_over_time: [
            { date: '2026-01-15', count: 10 },
            { date: '2026-01-16', count: 15 },
            { date: '2026-01-17', count: 12 },
          ],
          response_over_time: [
            { date: '2026-01-16', count: 3 },
            { date: '2026-01-17', count: 5 },
            { date: '2026-01-18', count: 4 },
          ],
          by_day_of_week: {
            monday: 12,
            tuesday: 15,
            wednesday: 10,
            thursday: 8,
            friday: 5,
          },
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns/campaign-1');
    
    // Should show analytics section
    await expect(page.getByText(/analytics|performance/i)).toBeVisible();
  });

  test('should link campaign to vacancy', async ({ page }) => {
    await page.route('**/api/vacancies**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          vacancies: [
            { id: 'vacancy-1', title: 'Senior Software Engineer' },
            { id: 'vacancy-2', title: 'Product Manager' },
          ],
          total: 2,
        }),
      });
    });
    
    await page.route('**/api/linkedin/campaigns', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'campaign-new',
            name: body.name,
            vacancy_id: body.vacancy_id,
            status: 'draft',
          }),
        });
      }
    });
    
    await page.goto('/recruiter/linkedin/campaigns');
    await page.getByRole('button', { name: /create.*campaign/i }).click();
    
    await page.getByLabel(/campaign.*name/i).fill('Linked Campaign');
    
    // Select vacancy
    await page.getByLabel(/vacancy|job/i).selectOption('vacancy-1');
    
    await page.getByRole('button', { name: /create/i }).click();
    
    await expect(page.getByText(/campaign.*created/i)).toBeVisible();
  });

  test('should show outreach response rate trends', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns/campaign-1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'campaign-1',
          name: 'Test Campaign',
          status: 'active',
          sent_count: 100,
          response_count: 30,
          response_rate: 30.0,
        }),
      });
    });
    
    await page.goto('/recruiter/linkedin/campaigns/campaign-1');
    
    // Should show response rate metric
    await expect(page.getByText('30')).toBeVisible();
    
    // Response rate should be highlighted/prominent
    const responseRateElement = page.locator('[data-testid="response-rate"], :text("30%")');
    await expect(responseRateElement.first()).toBeVisible();
  });
});

test.describe('LinkedIn Campaigns - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display mobile-friendly campaign list', async ({ page }) => {
    await page.route('**/api/linkedin/campaigns**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          campaigns: [
            { id: 'c1', name: 'Campaign 1', status: 'active', response_rate: 25 },
          ],
          total: 1,
        }),
      });
    });
    
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'recruiter@test.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/recruiter\//);
    
    await page.goto('/recruiter/linkedin/campaigns');
    
    // Should be usable on mobile
    await expect(page.getByText('Campaign 1')).toBeVisible();
    
    // Create button should be accessible
    await expect(page.getByRole('button', { name: /create|new/i })).toBeVisible();
  });
});
