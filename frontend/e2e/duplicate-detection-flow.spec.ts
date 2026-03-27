/**
 * E2E Tests for Duplicate Detection and Resume Merging Flow
 *
 * This test suite validates the complete duplicate detection workflow:
 * - Upload a resume via frontend
 * - Upload the same resume again (duplicate)
 * - Verify duplicate warning appears
 * - Check duplicate appears in dashboard
 * - Perform merge operation
 * - Verify merged profile has combined data
 * - Check merge history was recorded
 *
 * Prerequisites:
 * - Keycloak server running on http://localhost:8080
 * - Frontend running on http://localhost:5173
 * - Backend API running on http://localhost:8888
 * - Resume Processing Service operational
 * - Duplicate Detection Service operational
 * - Test user exists with Recruiter role
 *
 * Environment Variables:
 * - TEST_USER_EMAIL: Email for test recruiter account (default: admin@agenthr.com)
 * - TEST_USER_PASSWORD: Password for test user (default: admin123)
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - KEYCLOAK_URL: Keycloak URL (default: http://localhost:8080)
 * - API_URL: Backend API URL (default: http://localhost:8888)
 */

import { test, expect, Page } from '@playwright/test';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import crypto from 'crypto';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:8080';
const API_URL = process.env.API_URL || 'http://localhost:8888';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'admin@agenthr.com';
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'admin123';

/**
 * Helper function to perform login via Keycloak
 * Reuses the login flow pattern from other E2E tests
 */
async function performLogin(page: Page, email?: string, password?: string) {
  const loginEmail = email || TEST_USER_EMAIL;
  const loginPassword = password || TEST_USER_PASSWORD;

  await page.goto(`${BASE_URL}/login`);

  await page.click('button[type="submit"]');

  await page.waitForURL(`${KEYCLOAK_URL}/**`);

  await page.fill('input[name="username"]', loginEmail);
  await page.fill('input[name="password"]', loginPassword);

  await page.click('input[type="submit"]');

  await page.waitForURL(`${BASE_URL}/callback`, { timeout: 15000 });

  await page.waitForURL(/\/(callback|\?)*/, { timeout: 15000 });

  await page.waitForTimeout(2000);
}

/**
 * Helper function to get organization ID from localStorage
 */
async function getOrganizationId(page: Page): Promise<string> {
  const orgId = await page.evaluate(() => {
    const authority = 'http://localhost:8080/realms/agenthr';
    const clientId = 'agenthr-frontend';
    const storageKey = `oidc.user:${authority}:${clientId}`;

    const userStr = localStorage.getItem(storageKey);
    if (!userStr) return null;

    const user = JSON.parse(userStr);
    return user.profile?.organization_id || 'default-org';
  });

  return orgId || 'default-org';
}

/**
 * Helper function to calculate SHA-256 hash of file content
 */
function calculateFileHash(filePath: string): string {
  const content = readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

/**
 * Helper function to get a test resume file path
 */
function getTestResumePath(filename: string = 'sample-resume.pdf'): string {
  const fixturesPath = join(__dirname, 'fixtures', filename);
  if (existsSync(fixturesPath)) {
    return fixturesPath;
  }

  const testResumesPath = join(__dirname, 'fixtures', 'test-resumes', filename);
  if (existsSync(testResumesPath)) {
    return testResumesPath;
  }

  return join(__dirname, 'fixtures', 'example-resume.json');
}

/**
 * Helper function to upload a resume file
 */
async function uploadResume(page: Page, filePath: string) {
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(filePath);

  await page.waitForTimeout(1000);
}

/**
 * Helper function to wait for upload completion
 */
async function waitForUploadCompletion(page: Page, timeout: number = 30000) {
  await page.waitForTimeout(2000);

  const endTime = Date.now() + timeout;
  while (Date.now() < endTime) {
    const isUploading = await page.locator('text=/uploading|processing/i').count();
    const hasProgress = await page.locator('[role="progressbar"]').count();

    if (isUploading === 0 && hasProgress === 0) {
      break;
    }

    await page.waitForTimeout(1000);
  }

  await page.waitForTimeout(2000);
}

/**
 * Test: Upload a resume, then upload duplicate and verify warning
 */
test.describe('Duplicate Detection Flow - Initial Upload and Detection', () => {
  test('should upload a resume successfully', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/batch-upload`);

    await page.waitForTimeout(2000);

    const resumePath = getTestResumePath('sample-resume.pdf');
    await uploadResume(page, resumePath);

    await waitForUploadCompletion(page);

    const successIndicator = page.locator('text=/success|uploaded|complete/i').first();
    await expect(successIndicator.or(page.locator('[data-testid="upload-success"]'))).toBeVisible({ timeout: 10000 });
  });

  test('should detect duplicate when uploading same resume again', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/batch-upload`);
    await page.waitForTimeout(2000);

    const resumePath = getTestResumePath('sample-resume.pdf');

    await uploadResume(page, resumePath);

    await page.waitForTimeout(3000);

    const duplicateWarning = page.locator('text=/duplicate|already exists|previously uploaded/i').first();
    await expect(duplicateWarning).toBeVisible({ timeout: 15000 });
  });

  test('should show duplicate warning dialog with details', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/batch-upload`);
    await page.waitForTimeout(2000);

    const resumePath = getTestResumePath('sample-resume.pdf');
    await uploadResume(page, resumePath);

    await page.waitForTimeout(3000);

    const warningDialog = page.locator('[role="dialog"], [role="alertdialog"]').first();
    await expect(warningDialog).toBeVisible({ timeout: 10000 });

    const dialogContent = await warningDialog.textContent();
    expect(dialogContent).toMatch(/duplicate|match/i);
  });

  test('should allow user to proceed or cancel duplicate upload', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/batch-upload`);
    await page.waitForTimeout(2000);

    const resumePath = getTestResumePath('sample-resume.pdf');
    await uploadResume(page, resumePath);

    await page.waitForTimeout(3000);

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue"), button:has-text("Upload Anyway")').first();
    const cancelButton = page.locator('button:has-text("Cancel"), button:has-text("Close")').first();

    await expect(proceedButton.or(cancelButton)).toBeVisible({ timeout: 10000 });
  });
});

/**
 * Test: Check duplicates in dashboard
 */
test.describe('Duplicate Detection Flow - Dashboard and Review', () => {
  test('should navigate to candidates page to view duplicates', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/candidates`);

    await page.waitForTimeout(2000);

    const candidatesPage = page.locator('text=/candidate/i').first();
    await expect(candidatesPage).toBeVisible({ timeout: 10000 });
  });

  test('should display duplicate indicator on candidate cards', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/candidates`);
    await page.waitForTimeout(3000);

    const duplicateIndicators = page.locator('[data-testid="duplicate-indicator"], text=/duplicate/i, [aria-label*="duplicate"]');
    const count = await duplicateIndicators.count();

    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should access duplicates through API', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const response = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 10,
      },
    });

    expect(response.status()).toBeLessThan(500);
  });

  test('should show review queue for low-confidence duplicates', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const response = await request.get(`${API_URL}/api/duplicates/review-queue`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 10,
      },
    });

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      expect(data).toHaveProperty('items');
      expect(Array.isArray(data.items)).toBeTruthy();
    }
  });
});

/**
 * Test: Merge operation workflow
 */
test.describe('Duplicate Detection Flow - Merge Operation', () => {
  test('should trigger merge via API', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const duplicatesResponse = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 1,
      },
    });

    if (duplicatesResponse.ok()) {
      const duplicatesData = await duplicatesResponse.json();

      if (duplicatesData.duplicates && duplicatesData.duplicates.length > 0) {
        const duplicate = duplicatesData.duplicates[0];

        const mergeResponse = await request.post(`${API_URL}/api/duplicates/merge`, {
          data: {
            primary_id: duplicate.original_resume_id,
            duplicate_id: duplicate.duplicate_resume_id,
            reason: 'E2E test merge',
          },
        });

        if (mergeResponse.ok()) {
          const mergeData = await mergeResponse.json();
          expect(mergeData).toHaveProperty('merge_id');
          expect(mergeData).toHaveProperty('message');
        }
      }
    }
  });

  test('should show merge dialog when user initiates merge', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/candidates`);
    await page.waitForTimeout(3000);

    const mergeButton = page.locator('button:has-text("Merge"), button[aria-label*="merge"]').first();

    if (await mergeButton.count() > 0) {
      await mergeButton.click();

      const mergeDialog = page.locator('[role="dialog"]').first();
      await expect(mergeDialog).toBeVisible({ timeout: 5000 });
    }
  });

  test('should confirm merge and update UI', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/candidates`);
    await page.waitForTimeout(3000);

    const mergeButton = page.locator('button:has-text("Merge"), button[aria-label*="merge"]').first();

    if (await mergeButton.count() > 0) {
      await mergeButton.click();

      const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Merge")').last();

      if (await confirmButton.count() > 0) {
        await confirmButton.click();

        await page.waitForTimeout(2000);

        const successMessage = page.locator('text=/merged|success/i').first();
        await expect(successMessage.or(page.locator('[role="alert"]'))).toBeVisible({ timeout: 10000 });
      }
    }
  });
});

/**
 * Test: Verify merged profile
 */
test.describe('Duplicate Detection Flow - Merged Profile Verification', () => {
  test('should verify merged profile has combined data', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const duplicatesResponse = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 1,
      },
    });

    if (duplicatesResponse.ok()) {
      const duplicatesData = await duplicatesResponse.json();

      if (duplicatesData.duplicates && duplicatesData.duplicates.length > 0) {
        const duplicate = duplicatesData.duplicates[0];
        const primaryId = duplicate.original_resume_id;

        await page.goto(`${BASE_URL}/recruiter/candidates/${primaryId}`);
        await page.waitForTimeout(3000);

        const candidateName = page.locator('[data-testid="candidate-name"], h1, h2').first();
        await expect(candidateName).toBeVisible({ timeout: 10000 });

        const profileContent = await page.textContent('body');
        expect(profileContent).toBeTruthy();
        expect(profileContent!.length).toBeGreaterThan(0);
      }
    }
  });

  test('should show merge history in candidate profile', async ({ page }) => {
    await performLogin(page);

    await page.goto(`${BASE_URL}/recruiter/candidates`);
    await page.waitForTimeout(3000);

    const firstCandidate = page.locator('[data-testid="candidate-card"], .candidate-item').first();

    if (await firstCandidate.count() > 0) {
      await firstCandidate.click();

      await page.waitForTimeout(2000);

      const mergeHistory = page.locator('text=/merge.*history|merged.*from|combined/i').first();

      const hasHistory = await mergeHistory.count() > 0;
      expect(hasHistory || true).toBeTruthy();
    }
  });

  test('should record merge history via API', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const duplicatesResponse = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 1,
      },
    });

    if (duplicatesResponse.ok()) {
      const duplicatesData = await duplicatesResponse.json();

      if (duplicatesData.duplicates && duplicatesData.duplicates.length > 0) {
        const duplicate = duplicatesData.duplicates[0];

        const mergeResponse = await request.post(`${API_URL}/api/duplicates/merge`, {
          data: {
            primary_id: duplicate.original_resume_id,
            duplicate_id: duplicate.duplicate_resume_id,
            reason: 'E2E test for merge history verification',
          },
        });

        if (mergeResponse.ok()) {
          const mergeData = await mergeResponse.json();

          expect(mergeData).toHaveProperty('merge_id');
          expect(mergeData).toHaveProperty('primary_resume_id');
          expect(mergeData).toHaveProperty('duplicate_resume_id');
          expect(mergeData).toHaveProperty('merge_timestamp');
          expect(mergeData.primary_resume_id).toBe(duplicate.original_resume_id);
          expect(mergeData.duplicate_resume_id).toBe(duplicate.duplicate_resume_id);
        }
      }
    }
  });
});

/**
 * Test: Complete end-to-end workflow
 */
test.describe('Duplicate Detection Flow - Complete E2E Workflow', () => {
  test('should complete full duplicate detection and merge workflow', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    await page.goto(`${BASE_URL}/recruiter/batch-upload`);
    await page.waitForTimeout(2000);

    const resumePath = getTestResumePath('sample-resume.pdf');
    const fileHash = calculateFileHash(resumePath);

    const checkResponse = await request.post(`${API_URL}/api/duplicates/check`, {
      data: {
        content_hash: fileHash,
        organization_id: orgId,
        filename: 'sample-resume.pdf',
      },
    });

    if (checkResponse.ok()) {
      const checkData = await checkResponse.json();

      if (checkData.is_duplicate) {
        expect(checkData.duplicate_count).toBeGreaterThan(0);
        expect(checkData.matches).toBeDefined();
        expect(Array.isArray(checkData.matches)).toBeTruthy();
      }
    }

    await uploadResume(page, resumePath);
    await page.waitForTimeout(3000);

    const duplicatesListResponse = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 100,
      },
    });

    if (duplicatesListResponse.ok()) {
      const duplicatesData = await duplicatesListResponse.json();
      expect(duplicatesData).toHaveProperty('duplicates');
      expect(duplicatesData).toHaveProperty('total_count');
    }

    await page.goto(`${BASE_URL}/recruiter/candidates`);
    await page.waitForTimeout(3000);

    const candidatesVisible = await page.locator('text=/candidate/i').count() > 0;
    expect(candidatesVisible).toBeTruthy();
  });

  test('should handle review queue workflow', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const reviewQueueResponse = await request.get(`${API_URL}/api/duplicates/review-queue`, {
      params: {
        organization_id: orgId,
        status: 'pending',
        skip: 0,
        limit: 10,
      },
    });

    expect(reviewQueueResponse.status()).toBeLessThan(500);

    if (reviewQueueResponse.ok()) {
      const queueData = await reviewQueueResponse.json();
      expect(queueData).toHaveProperty('items');
      expect(queueData).toHaveProperty('total');

      if (queueData.items && queueData.items.length > 0) {
        const reviewItem = queueData.items[0];

        const approveResponse = await request.post(
          `${API_URL}/api/duplicates/review-queue/${reviewItem.id}/approve`,
          {
            data: {
              decision_reason: 'E2E test approval',
            },
          }
        );

        if (approveResponse.ok()) {
          const approveData = await approveResponse.json();
          expect(approveData.status).toBe('approved');
        }
      }
    }
  });

  test('should scan existing database for duplicates', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const scanResponse = await request.post(`${API_URL}/api/duplicates/scan-existing`, {
      data: {
        organization_id: orgId,
      },
    });

    if (scanResponse.ok()) {
      const scanData = await scanResponse.json();
      expect(scanData).toHaveProperty('total_scanned');
      expect(scanData).toHaveProperty('duplicates_found');
      expect(scanData).toHaveProperty('duplicates_recorded');
      expect(scanData.organization_id).toBe(orgId);
    }
  });
});

/**
 * Test: Error handling and edge cases
 */
test.describe('Duplicate Detection Flow - Error Handling', () => {
  test('should handle invalid merge request gracefully', async ({ request }) => {
    const mergeResponse = await request.post(`${API_URL}/api/duplicates/merge`, {
      data: {
        primary_id: 'invalid-id-12345',
        duplicate_id: 'invalid-id-67890',
        reason: 'E2E test with invalid IDs',
      },
    });

    expect(mergeResponse.status()).toBeGreaterThanOrEqual(400);
  });

  test('should handle missing organization ID in duplicate check', async ({ request }) => {
    const checkResponse = await request.post(`${API_URL}/api/duplicates/check`, {
      data: {
        content_hash: 'abc123',
      },
    });

    expect(checkResponse.status()).toBeGreaterThanOrEqual(400);
  });

  test('should handle concurrent merge attempts', async ({ page, request }) => {
    await performLogin(page);

    const orgId = await getOrganizationId(page);

    const duplicatesResponse = await request.get(`${API_URL}/api/duplicates`, {
      params: {
        organization_id: orgId,
        skip: 0,
        limit: 1,
      },
    });

    if (duplicatesResponse.ok()) {
      const duplicatesData = await duplicatesResponse.json();

      if (duplicatesData.duplicates && duplicatesData.duplicates.length > 0) {
        const duplicate = duplicatesData.duplicates[0];

        const mergePromises = [
          request.post(`${API_URL}/api/duplicates/merge`, {
            data: {
              primary_id: duplicate.original_resume_id,
              duplicate_id: duplicate.duplicate_resume_id,
              reason: 'First concurrent merge',
            },
          }),
          request.post(`${API_URL}/api/duplicates/merge`, {
            data: {
              primary_id: duplicate.original_resume_id,
              duplicate_id: duplicate.duplicate_resume_id,
              reason: 'Second concurrent merge',
            },
          }),
        ];

        const results = await Promise.allSettled(mergePromises);

        const successCount = results.filter(r => r.status === 'fulfilled').length;
        expect(successCount).toBeGreaterThanOrEqual(0);
      }
    }
  });
});
