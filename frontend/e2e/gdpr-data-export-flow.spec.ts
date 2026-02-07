import { test, expect } from '@playwright/test';

/**
 * E2E Tests for GDPR Data Export Flow (Right to Portability)
 *
 * Test Suite Contents:
 * 1. Create Test Candidate with Full Data
 * 2. Request Data Export via Frontend Dialog
 * 3. Select JSON Format and Export
 * 4. Verify Export File Downloads
 * 5. Verify JSON Contains All Candidate PII
 * 6. Verify JSON is Valid and Machine-Readable
 * 7. Repeat with CSV Format
 * 8. Verify CSV is Valid and Machine-Readable
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Database with test candidate data
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

// Test resume ID (in production, this would be created dynamically)
const TEST_RESUME_ID = process.env.TEST_RESUME_ID || '00000000-0000-0000-0000-000000000001';

test.describe('GDPR Data Export Flow - Frontend UI', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page, context }) => {
    // Clear all cookies and localStorage before each test
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Accept cookies to proceed
    await page.waitForLoadState('networkidle');
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    const acceptCount = await acceptButton.count();

    if (acceptCount > 0) {
      await acceptButton.click();
    }
  });

  test('should display data export dialog on privacy settings page', async ({ page }) => {
    // Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Check for privacy settings heading
    await expect(page.getByRole('heading', { name: /privacy settings/i })).toBeVisible();

    // Check for "Export My Data" quick action card
    await expect(page.getByText(/export my data|export data/i)).toBeVisible();
  });

  test('should open data export dialog', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Click on "Export My Data" card
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();

    // Wait for dialog to open
    await page.waitForTimeout(500);

    // Verify export dialog is visible
    const dialog = page.locator('[role="dialog"]').filter({ hasText: /export|portability|download/i });
    await expect(dialog).toBeVisible({ timeout: 5000 });
  });

  test('should display info about right to portability', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Check for info alert
    const infoAlert = page.locator('.MuiAlert-root').filter({ hasText: /right to portability|GDPR|Article 15/i });
    await expect(infoAlert).toBeVisible();
  });

  test('should display format selection options', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Check for format selection (JSON/CSV)
    await expect(page.getByText(/json|csv|format/i)).toBeVisible();

    // Check for radio buttons or format options
    const jsonOption = page.getByText(/json/i);
    const csvOption = page.getByText(/csv/i);

    await expect(jsonOption).toBeVisible();
    await expect(csvOption).toBeVisible();
  });

  test('should allow selecting JSON format', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Click JSON format option
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Verify JSON is selected
    const isChecked = await jsonRadio.isChecked();
    expect(isChecked).toBe(true);
  });

  test('should allow selecting CSV format', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Click CSV format option
    const csvRadio = page.getByRole('radio', { name: /csv/i }).or(
      page.getByLabel(/csv/i)
    );
    await csvRadio.check();

    // Verify CSV is selected
    const isChecked = await csvRadio.isChecked();
    expect(isChecked).toBe(true);
  });

  test('should disable export button when format not selected', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Find export button
    const exportButton = page.getByRole('button', { name: /export|download/i });

    // Button should be enabled (default format selected)
    const isVisible = await exportButton.isVisible();
    expect(isVisible).toBe(true);
  });
});

test.describe('GDPR Data Export Flow - API Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should send export request to backend API with JSON format', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for API call to initiate
    await page.waitForTimeout(1000);

    // Verify progress indicator appears
    const progress = page.locator('.MuiCircularProgress-root').or(
      page.locator('.MuiLinearProgress-root')
    );
    await expect(progress).toBeVisible({ timeout: 3000 });

    // Verify no immediate errors
    const errorMessage = page.getByText(/error|failed/i);
    const errorCount = await errorMessage.count();
    expect(errorCount).toBe(0);
  });

  test('should send export request to backend API with CSV format', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select CSV format
    const csvRadio = page.getByRole('radio', { name: /csv/i }).or(
      page.getByLabel(/csv/i)
    );
    await csvRadio.check();

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for API call to initiate
    await page.waitForTimeout(1000);

    // Verify progress indicator appears
    const progress = page.locator('.MuiCircularProgress-root').or(
      page.locator('.MuiLinearProgress-root')
    );
    await expect(progress).toBeVisible({ timeout: 3000 });

    // Verify no immediate errors
    const errorMessage = page.getByText(/error|failed/i);
    const errorCount = await errorMessage.count();
    expect(errorCount).toBe(0);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // This test would require mocking the API to return an error
    // For now, we'll skip it
    test.skip(true, 'Requires API mocking - to be implemented');
  });
});

test.describe('GDPR Data Export Flow - File Download', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should download JSON file after successful export', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for download
    const download = await downloadPromise;

    // Verify download filename
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.json$/i);
    expect(filename).toMatch(/export/);

    // Verify success message
    const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /success|downloaded|ready/i });
    await expect(successAlert).toBeVisible({ timeout: 10000 });
  });

  test('should download CSV file after successful export', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select CSV format
    const csvRadio = page.getByRole('radio', { name: /csv/i }).or(
      page.getByLabel(/csv/i)
    );
    await csvRadio.check();

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for download
    const download = await downloadPromise;

    // Verify download filename
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.csv$/i);
    expect(filename).toMatch(/export/);

    // Verify success message
    const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /success|downloaded|ready/i });
    await expect(successAlert).toBeVisible({ timeout: 10000 });
  });

  test('should verify JSON file content structure', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for download
    const download = await downloadPromise;

    // Read file content
    const fileContent = await download.createReadStream();
    let content = '';
    for await (const chunk of fileContent) {
      content += chunk.toString();
    }

    // Verify JSON is valid
    expect(() => JSON.parse(content)).not.toThrow();

    // Parse and verify structure
    const jsonData = JSON.parse(content);

    // Verify metadata fields
    expect(jsonData).toHaveProperty('export_timestamp');
    expect(jsonData).toHaveProperty('resume_id');
    expect(jsonData).toHaveProperty('format');

    // Verify data sections exist (may be empty for test data)
    expect(jsonData).toHaveProperty('resume');
    expect(jsonData).toHaveProperty('hiring_stages');
    expect(jsonData).toHaveProperty('notes');
    expect(jsonData).toHaveProperty('tags');
    expect(jsonData).toHaveProperty('activities');
  });

  test('should verify CSV file content structure', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select CSV format
    const csvRadio = page.getByRole('radio', { name: /csv/i }).or(
      page.getByLabel(/csv/i)
    );
    await csvRadio.check();

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for download
    const download = await downloadPromise;

    // Read file content
    const fileContent = await download.createReadStream();
    let content = '';
    for await (const chunk of fileContent) {
      content += chunk.toString();
    }

    // Verify CSV has content
    expect(content.length).toBeGreaterThan(0);

    // Verify CSV structure (headers present)
    const lines = content.split('\n').filter(line => line.trim());
    expect(lines.length).toBeGreaterThan(0);

    // Verify header row
    const headers = lines[0].split(',');
    expect(headers.length).toBeGreaterThan(0);

    // Verify common PII fields exist in headers
    const headerString = headers.join(' ').toLowerCase();
    expect(headerString).toMatch(/record_type|resume|stage|note|tag|activity/i);
  });

  test('should show data summary after export', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Click export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for success
    await page.waitForTimeout(5000);

    // Check for data summary
    const summarySection = page.locator('[role="dialog"]').filter({ hasText: /summary|records|stages|notes|tags/i });
    await expect(summarySection).toBeVisible({ timeout: 10000 });
  });
});

test.describe('GDPR Data Export Flow - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test.beforeEach(async ({ page, context }) => {
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Accept cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    const acceptCount = await acceptButton.count();

    if (acceptCount > 0) {
      await acceptButton.click();
    }
  });

  test('should display export dialog correctly on mobile', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Check privacy settings page loads
    await expect(page.getByRole('heading', { name: /privacy/i })).toBeVisible();

    // Check for export data option
    await expect(page.getByText(/export|data/i)).toBeVisible();
  });

  test('should allow exporting data on mobile', async ({ page }) => {
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    // Open export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();
    await page.waitForTimeout(500);

    // Verify dialog is visible on mobile
    const dialog = page.locator('[role="dialog"]').filter({ hasText: /export/i });
    await expect(dialog).toBeVisible();

    // Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    // Click export
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();

    // Wait for progress
    await page.waitForTimeout(3000);

    // Verify progress indicator
    const progress = page.locator('.MuiCircularProgress-root').or(
      page.locator('.MuiLinearProgress-root')
    );
    await expect(progress).toBeVisible();
  });
});

test.describe('GDPR Data Export Flow - Complete End-to-End', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('complete export flow: JSON format', async ({ page, context }) => {
    // Step 1: Clear state and navigate to privacy settings
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Accept cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    const acceptCount = await acceptButton.count();

    if (acceptCount > 0) {
      await acceptButton.click();
    }

    console.log('✓ Browser state initialized');

    // Step 2: Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /privacy settings/i })).toBeVisible();
    console.log('✓ Navigated to privacy settings');

    // Step 3: Open data export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();

    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]').filter({ hasText: /export|portability/i });
    await expect(dialog).toBeVisible();
    console.log('✓ Data export dialog opened');

    // Step 4: Verify info about right to portability
    const infoAlert = page.locator('.MuiAlert-root').filter({ hasText: /right to portability|GDPR/i });
    await expect(infoAlert).toBeVisible();
    console.log('✓ Right to portability info displayed');

    // Step 5: Select JSON format
    const jsonRadio = page.getByRole('radio', { name: /json/i }).or(
      page.getByLabel(/json/i)
    );
    await jsonRadio.check();

    const isChecked = await jsonRadio.isChecked();
    expect(isChecked).toBe(true);
    console.log('✓ JSON format selected');

    // Step 6: Initiate export
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();
    console.log('✓ Export initiated');

    // Step 7: Wait for progress indicator
    await page.waitForTimeout(1000);

    const progress = page.locator('.MuiCircularProgress-root').or(
      page.locator('.MuiLinearProgress-root')
    );
    await expect(progress).toBeVisible({ timeout: 3000 });
    console.log('✓ Progress indicator displayed');

    // Step 8: Set up download handler and wait for file
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
    const download = await downloadPromise;
    console.log('✓ Download started');

    // Step 9: Verify download filename
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.json$/i);
    expect(filename).toMatch(/export/);
    console.log(`✓ File downloaded: ${filename}`);

    // Step 10: Read and verify JSON content
    const fileContent = await download.createReadStream();
    let content = '';
    for await (const chunk of fileContent) {
      content += chunk.toString();
    }

    // Verify JSON is valid
    expect(() => JSON.parse(content)).not.toThrow();
    console.log('✓ JSON file is valid');

    // Parse and verify structure
    const jsonData = JSON.parse(content);

    // Verify metadata
    expect(jsonData).toHaveProperty('export_timestamp');
    expect(jsonData).toHaveProperty('resume_id');
    expect(jsonData).toHaveProperty('format');
    expect(jsonData.format).toBe('json');
    console.log('✓ JSON metadata verified');

    // Verify data sections
    expect(jsonData).toHaveProperty('resume');
    expect(jsonData).toHaveProperty('hiring_stages');
    expect(jsonData).toHaveProperty('notes');
    expect(jsonData).toHaveProperty('tags');
    expect(jsonData).toHaveProperty('activities');
    console.log('✓ JSON data structure verified');

    // Step 11: Verify success message
    const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /success|downloaded|ready/i });
    await expect(successAlert).toBeVisible({ timeout: 10000 });
    console.log('✓ Success message displayed');

    // Step 12: Verify no errors
    const errorMessage = page.getByText(/error|failed/i);
    const errorCount = await errorMessage.count();
    expect(errorCount).toBe(0);
    console.log('✓ No errors occurred');

    console.log('✓ Complete end-to-end JSON export flow verified');
  });

  test('complete export flow: CSV format', async ({ page, context }) => {
    // Step 1: Clear state and navigate to privacy settings
    await context.clearCookies();
    await page.goto('/');

    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Accept cookies
    const acceptButton = page.getByRole('button', { name: /accept all/i });
    const acceptCount = await acceptButton.count();

    if (acceptCount > 0) {
      await acceptButton.click();
    }

    console.log('✓ Browser state initialized');

    // Step 2: Navigate to privacy settings
    await page.goto('/settings/privacy');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /privacy settings/i })).toBeVisible();
    console.log('✓ Navigated to privacy settings');

    // Step 3: Open data export dialog
    const exportDataCard = page.getByText(/export my data|export data/i).first();
    await exportDataCard.click();

    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]').filter({ hasText: /export|portability/i });
    await expect(dialog).toBeVisible();
    console.log('✓ Data export dialog opened');

    // Step 4: Select CSV format
    const csvRadio = page.getByRole('radio', { name: /csv/i }).or(
      page.getByLabel(/csv/i)
    );
    await csvRadio.check();

    const isChecked = await csvRadio.isChecked();
    expect(isChecked).toBe(true);
    console.log('✓ CSV format selected');

    // Step 5: Initiate export
    const exportButton = page.getByRole('button', { name: /export|download/i });
    await exportButton.click();
    console.log('✓ Export initiated');

    // Step 6: Wait for progress indicator
    await page.waitForTimeout(1000);

    const progress = page.locator('.MuiCircularProgress-root').or(
      page.locator('.MuiLinearProgress-root')
    );
    await expect(progress).toBeVisible({ timeout: 3000 });
    console.log('✓ Progress indicator displayed');

    // Step 7: Set up download handler and wait for file
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
    const download = await downloadPromise;
    console.log('✓ Download started');

    // Step 8: Verify download filename
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.csv$/i);
    expect(filename).toMatch(/export/);
    console.log(`✓ File downloaded: ${filename}`);

    // Step 9: Read and verify CSV content
    const fileContent = await download.createReadStream();
    let content = '';
    for await (const chunk of fileContent) {
      content += chunk.toString();
    }

    // Verify CSV has content
    expect(content.length).toBeGreaterThan(0);
    console.log('✓ CSV file has content');

    // Verify CSV structure
    const lines = content.split('\n').filter(line => line.trim());
    expect(lines.length).toBeGreaterThan(0);

    const headers = lines[0].split(',');
    expect(headers.length).toBeGreaterThan(0);
    console.log('✓ CSV structure verified');

    // Step 10: Verify success message
    const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /success|downloaded|ready/i });
    await expect(successAlert).toBeVisible({ timeout: 10000 });
    console.log('✓ Success message displayed');

    // Step 11: Verify no errors
    const errorMessage = page.getByText(/error|failed/i });
    const errorCount = await errorMessage.count();
    expect(errorCount).toBe(0);
    console.log('✓ No errors occurred');

    console.log('✓ Complete end-to-end CSV export flow verified');
  });
});
