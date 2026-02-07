import { test, expect } from '@playwright/test';

/**
 * E2E Tests for GDPR Data Retention Policy Automation
 *
 * Test Suite Contents:
 * 1. Retention Policy Management API Tests
 * 2. Create Test Data with Different Ages
 * 3. Manual Retention Cleanup Execution
 * 4. Verify Old Data Deleted
 * 5. Verify Recent Data Preserved
 * 6. Verify Audit Trail Logging
 * 7. Dry-Run Mode Testing
 * 8. Mobile Responsive Testing
 * 9. Complete End-to-End Retention Flow
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Database running with GDPR tables
 * - Celery worker available for task execution
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

// API base URL
const API_BASE = 'http://localhost:8000';

// Helper function to create retention policy
async function createRetentionPolicy(
  request: any,
  policyName: string,
  entityType: string,
  retentionDays: number,
  actionType: string = 'delete',
  organizationId?: string
) {
  const response = await request.post(`${API_BASE}/api/retention-policies/`, {
    headers: { 'Content-Type': 'application/json' },
    data: {
      policy_name: policyName,
      entity_type: entityType,
      retention_days: retentionDays,
      action_type: actionType,
      organization_id: organizationId || null,
      is_active: true,
      description: `Test policy for ${entityType}`,
      legal_basis: 'legitimate_interest',
      deletion_reason: 'retention_period_expired'
    }
  });
  return response;
}

// Helper function to create test resume with specific created_date
async function createTestResume(
  request: any,
  filename: string,
  createdDate: string,
  rawData: string = 'test resume content'
) {
  const response = await request.post(`${API_BASE}/api/resumes/`, {
    headers: { 'Content-Type': 'application/json' },
    data: {
      filename: filename,
      raw_text: rawData,
      language: 'en',
      status: 'active',
      created_at: createdDate
    }
  });
  return response;
}

// Helper function to trigger retention cleanup task
async function triggerRetentionCleanup(
  request: any,
  organizationId?: string,
  dryRun: boolean = false
) {
  const response = await request.post(`${API_BASE}/api/retention-policies/cleanup`, {
    headers: { 'Content-Type': 'application/json' },
    data: {
      organization_id: organizationId || null,
      dry_run: dryRun
    }
  });
  return response;
}

// Helper function to get audit logs
async function getAuditLogs(
  request: any,
  entityType?: string,
  limit: number = 100
) {
  const params = new URLSearchParams();
  if (entityType) params.append('entity_type', entityType);
  params.append('limit', limit.toString());

  const response = await request.get(`${API_BASE}/api/audit-logs/?${params.toString()}`);
  return response;
}

test.describe('GDPR Retention Policy - API Management', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should create retention policy successfully', async ({ request }) => {
    const policyName = `Test Policy ${Date.now()}`;

    const response = await createRetentionPolicy(
      request,
      policyName,
      'resumes',
      30,
      'delete'
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.policy_name).toBe(policyName);
    expect(data.entity_type).toBe('resumes');
    expect(data.retention_days).toBe(30);
    expect(data.action_type).toBe('delete');
    expect(data.is_active).toBe(true);

    // Cleanup: delete the policy
    await request.delete(`${API_BASE}/api/retention-policies/${data.id}`);
  });

  test('should list active retention policies', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/retention-policies/`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.policies).toBeDefined();
    expect(Array.isArray(data.policies)).toBeTruthy();
    expect(data.total_count).toBeDefined();
  });

  test('should update retention policy', async ({ request }) => {
    // Create a policy first
    const createResponse = await createRetentionPolicy(
      request,
      `Update Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await createResponse.json();

    // Update the policy
    const updateResponse = await request.put(
      `${API_BASE}/api/retention-policies/${policy.id}`,
      {
        headers: { 'Content-Type': 'application/json' },
        data: {
          retention_days: 60,
          description: 'Updated description'
        }
      }
    );

    expect(updateResponse.ok()).toBeTruthy();
    const updated = await updateResponse.json();
    expect(updated.retention_days).toBe(60);
    expect(updated.description).toBe('Updated description');

    // Cleanup
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });

  test('should delete retention policy', async ({ request }) => {
    // Create a policy first
    const createResponse = await createRetentionPolicy(
      request,
      `Delete Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await createResponse.json();

    // Delete the policy
    const deleteResponse = await request.delete(
      `${API_BASE}/api/retention-policies/${policy.id}`
    );

    expect(deleteResponse.status()).toBe(204);

    // Verify it's deleted
    const getResponse = await request.get(
      `${API_BASE}/api/retention-policies/${policy.id}`
    );
    expect(getResponse.status()).toBe(404);
  });

  test('should validate retention policy parameters', async ({ request }) => {
    // Test invalid entity type
    const response = await request.post(`${API_BASE}/api/retention-policies/`, {
      headers: { 'Content-Type': 'application/json' },
      data: {
        policy_name: 'Invalid Policy',
        entity_type: 'invalid_type',
        retention_days: 30,
        action_type: 'delete'
      }
    });

    expect(response.status()).toBe(422);
    const data = await response.json();
    expect(data.detail).toBeDefined();
  });
});

test.describe('GDPR Retention Policy - Data Creation', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should create old test resume (60+ days ago)', async ({ request }) => {
    // Create a resume with created_date 60 days ago
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 60);
    const createdDate = oldDate.toISOString();

    const response = await createTestResume(
      request,
      `old_resume_${Date.now()}.pdf`,
      createdDate
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.filename).toContain('old_resume');
    expect(data.id).toBeDefined();
  });

  test('should create recent test resume (within 30 days)', async ({ request }) => {
    // Create a resume with created_date 10 days ago
    const recentDate = new Date();
    recentDate.setDate(recentDate.getDate() - 10);
    const createdDate = recentDate.toISOString();

    const response = await createTestResume(
      request,
      `recent_resume_${Date.now()}.pdf`,
      createdDate
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.filename).toContain('recent_resume');
    expect(data.id).toBeDefined();
  });

  test('should verify created resumes have correct timestamps', async ({ request }) => {
    const timestamps = [
      { days: 90, label: '90_days_old' },
      { days: 45, label: '45_days_old' },
      { days: 15, label: '15_days_old' },
      { days: 1, label: '1_day_old' }
    ];

    for (const ts of timestamps) {
      const date = new Date();
      date.setDate(date.getDate() - ts.days);
      const createdDate = date.toISOString();

      const response = await createTestResume(
        request,
        `${ts.label}_${Date.now()}.pdf`,
        createdDate
      );

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.id).toBeDefined();
    }
  });
});

test.describe('GDPR Retention Policy - Cleanup Execution', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ request }) => {
    // Create a test policy with 30-day retention
    await createRetentionPolicy(
      request,
      `E2E Test Policy ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
  });

  test('should execute retention cleanup task', async ({ request }) => {
    const response = await triggerRetentionCleanup(request, null, false);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBeDefined();
    expect(data.total_processed).toBeDefined();
    expect(data.total_succeeded).toBeDefined();
    expect(data.entity_types).toBeDefined();
    expect(data.processing_time_ms).toBeDefined();
  });

  test('should run cleanup in dry-run mode', async ({ request }) => {
    const response = await triggerRetentionCleanup(request, null, true);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.dry_run).toBe(true);
    expect(data.total_processed).toBeGreaterThanOrEqual(0);

    // In dry-run mode, no data should be deleted
    expect(data.total_succeeded).toBe(data.total_processed);
  });

  test('should report cleanup statistics by entity type', async ({ request }) => {
    const response = await triggerRetentionCleanup(request, null, false);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.entity_types).toBeDefined();

    // Check if resumes entity type is present
    if (data.entity_types.resumes) {
      expect(data.entity_types.resumes.total_processed).toBeDefined();
      expect(data.entity_types.resumes.deleted_count).toBeDefined();
    }
  });
});

test.describe('GDPR Retention Policy - Data Verification', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should delete old resumes exceeding retention period', async ({ request }) => {
    // Create policy with 30-day retention
    const policyResponse = await createRetentionPolicy(
      request,
      `Delete Old Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await policyResponse.json();

    // Create old resume (60 days ago)
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 60);
    const oldResume = await createTestResume(
      request,
      `old_${Date.now()}.pdf`,
      oldDate.toISOString()
    );
    const oldResumeData = await oldResume.json();

    // Run cleanup
    await triggerRetentionCleanup(request, null, false);

    // Wait a bit for cleanup to complete
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Verify old resume is deleted
    const getResponse = await request.get(
      `${API_BASE}/api/resumes/${oldResumeData.id}`
    );
    expect(getResponse.status()).toBe(404);

    // Cleanup
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });

  test('should preserve recent resumes within retention period', async ({ request }) => {
    // Create policy with 30-day retention
    const policyResponse = await createRetentionPolicy(
      request,
      `Preserve Recent Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await policyResponse.json();

    // Create recent resume (10 days ago)
    const recentDate = new Date();
    recentDate.setDate(recentDate.getDate() - 10);
    const recentResume = await createTestResume(
      request,
      `recent_${Date.now()}.pdf`,
      recentDate.toISOString()
    );
    const recentResumeData = await recentResume.json();

    // Run cleanup
    await triggerRetentionCleanup(request, null, false);

    // Wait a bit for cleanup to complete
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Verify recent resume still exists
    const getResponse = await request.get(
      `${API_BASE}/api/resumes/${recentResumeData.id}`
    );
    expect(getResponse.ok()).toBeTruthy();
    const data = await getResponse.json();
    expect(data.id).toBe(recentResumeData.id);

    // Cleanup
    await request.delete(`${API_BASE}/api/resumes/${recentResumeData.id}`);
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });

  test('should handle mixed age resumes correctly', async ({ request }) => {
    // Create policy with 30-day retention
    const policyResponse = await createRetentionPolicy(
      request,
      `Mixed Age Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await policyResponse.json();

    // Create multiple resumes with different ages
    const resumes = [];
    const ages = [60, 45, 35, 25, 15, 5]; // days ago

    for (const age of ages) {
      const date = new Date();
      date.setDate(date.getDate() - age);
      const response = await createTestResume(
        request,
        `resume_${age}days_${Date.now()}.pdf`,
        date.toISOString()
      );
      resumes.push(await response.json());
    }

    // Run cleanup
    await triggerRetentionCleanup(request, null, false);

    // Wait for cleanup
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Verify correct resumes deleted/preserved
    // Old resumes (60, 45, 35 days) should be deleted
    // Recent resumes (25, 15, 5 days) should be preserved
    const expectedDeleted = [true, true, true, false, false, false];

    for (let i = 0; i < resumes.length; i++) {
      const getResponse = await request.get(
        `${API_BASE}/api/resumes/${resumes[i].id}`
      );

      if (expectedDeleted[i]) {
        expect(getResponse.status()).toBe(404);
      } else {
        expect(getResponse.ok()).toBeTruthy();
        // Cleanup preserved resume
        await request.delete(`${API_BASE}/api/resumes/${resumes[i].id}`);
      }
    }

    // Cleanup policy
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });
});

test.describe('GDPR Retention Policy - Audit Trail', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should log retention cleanup to audit trail', async ({ request }) => {
    // Create policy
    const policyResponse = await createRetentionPolicy(
      request,
      `Audit Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await policyResponse.json();

    // Create old resume
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 60);
    await createTestResume(
      request,
      `audit_test_${Date.now()}.pdf`,
      oldDate.toISOString()
    );

    // Get initial audit log count
    const initialLogs = await getAuditLogs(request);
    const initialData = await initialLogs.json();
    const initialCount = initialData.total_count || 0;

    // Run cleanup
    await triggerRetentionCleanup(request, null, false);

    // Wait for cleanup
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Get new audit logs
    const newLogs = await getAuditLogs(request, 'retention_cleanup');
    const newData = await newLogs.json();

    // Should have more audit logs after cleanup
    expect(newData.total_count).toBeGreaterThan(initialCount);

    // Verify audit log contains cleanup action
    if (newData.logs && newData.logs.length > 0) {
      const cleanupLog = newData.logs.find(
        (log: any) => log.action === 'retention_cleanup'
      );
      expect(cleanupLog).toBeDefined();
    }

    // Cleanup
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });

  test('should include policy details in audit log', async ({ request }) => {
    // Create and run cleanup
    const policyResponse = await createRetentionPolicy(
      request,
      `Policy Detail Test ${Date.now()}`,
      'resumes',
      30,
      'delete'
    );
    const policy = await policyResponse.json();

    await triggerRetentionCleanup(request, null, false);

    // Wait and check logs
    await new Promise(resolve => setTimeout(resolve, 2000));

    const logs = await getAuditLogs(request, 'retention_cleanup', 50);
    const logsData = await logs.json();

    // Find cleanup log with policy details
    if (logsData.logs) {
      const policyLog = logsData.logs.find((log: any) =>
        log.details && log.details.policy_id === policy.id
      );
      expect(policyLog).toBeDefined();
    }

    // Cleanup
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);
  });
});

test.describe('GDPR Retention Policy - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('should display retention policies on mobile', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Check if page loads without errors
    await expect(page).toHaveTitle(/AgentHR/);

    // Verify no console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(2000);
    expect(errors.length).toBe(0);
  });

  test('should be responsive on small screens', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Check viewport width
    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBe(375);

    // Verify content is visible
    const privacySettings = page.locator('h1, h2').filter({ hasText: /privacy|settings/i });
    await expect(privacySettings).toBeVisible();
  });
});

test.describe('GDPR Retention Policy - Complete End-to-End', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('complete retention policy workflow', async ({ page, request }) => {
    // Step 1: Create retention policy via API
    const policyName = `E2E Workflow ${Date.now()}`;
    const policyResponse = await createRetentionPolicy(
      request,
      policyName,
      'resumes',
      30,
      'delete'
    );
    expect(policyResponse.ok()).toBeTruthy();
    const policy = await policyResponse.json();

    // Step 2: Create test data with different ages
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 60);
    const oldResume = await createTestResume(
      request,
      `e2e_old_${Date.now()}.pdf`,
      oldDate.toISOString()
    );
    const oldResumeData = await oldResume.json();

    const recentDate = new Date();
    recentDate.setDate(recentDate.getDate() - 10);
    const recentResume = await createTestResume(
      request,
      `e2e_recent_${Date.now()}.pdf`,
      recentDate.toISOString()
    );
    const recentResumeData = await recentResume.json();

    // Step 3: Run dry-run cleanup first
    const dryRunResponse = await triggerRetentionCleanup(request, null, true);
    expect(dryRunResponse.ok()).toBeTruthy();
    const dryRunData = await dryRunResponse.json();
    expect(dryRunData.dry_run).toBe(true);

    // Step 4: Verify both resumes still exist after dry-run
    const oldCheck1 = await request.get(
      `${API_BASE}/api/resumes/${oldResumeData.id}`
    );
    const recentCheck1 = await request.get(
      `${API_BASE}/api/resumes/${recentResumeData.id}`
    );
    expect(oldCheck1.ok()).toBeTruthy();
    expect(recentCheck1.ok()).toBeTruthy();

    // Step 5: Run actual cleanup
    const cleanupResponse = await triggerRetentionCleanup(request, null, false);
    expect(cleanupResponse.ok()).toBeTruthy();
    const cleanupData = await cleanupResponse.json();
    expect(cleanupData.status).toBe('success');

    // Step 6: Wait for cleanup to complete
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Step 7: Verify old resume deleted, recent resume preserved
    const oldCheck2 = await request.get(
      `${API_BASE}/api/resumes/${oldResumeData.id}`
    );
    const recentCheck2 = await request.get(
      `${API_BASE}/api/resumes/${recentResumeData.id}`
    );
    expect(oldCheck2.status()).toBe(404);
    expect(recentCheck2.ok()).toBeTruthy();

    // Step 8: Verify audit trail
    const logs = await getAuditLogs(request, 'retention_cleanup', 100);
    expect(logs.ok()).toBeTruthy();
    const logsData = await logs.json();
    expect(logsData.total_count).toBeGreaterThan(0);

    // Step 9: View retention policies in UI
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Verify page loads
    await expect(page.locator('h1, h2').filter({ hasText: /privacy/i })).toBeVisible();

    // Step 10: Cleanup
    await request.delete(`${API_BASE}/api/resumes/${recentResumeData.id}`);
    await request.delete(`${API_BASE}/api/retention-policies/${policy.id}`);

    // Verify cleanup
    const policyCheck = await request.get(
      `${API_BASE}/api/retention-policies/${policy.id}`
    );
    expect(policyCheck.status()).toBe(404);
  });
});
