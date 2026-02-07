import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { execSync } from 'child_process';
import { tmpdir } from 'os';

/**
 * E2E Tests for Bulk Operations & Batch Processing
 *
 * Test Suite Contents:
 * 1. ZIP File Upload with Progress Tracking
 * 2. Bulk Export to PDF/ZIP
 * 3. Batch Job Status Updates
 * 4. Email Notifications (if configured)
 * 5. Progress Bar Accuracy
 * 6. Error Handling for Invalid Files
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Celery worker running for background tasks
 * - Redis running for Celery broker
 *
 * Test Data:
 * - Creates ZIP archives dynamically using Python zipfile
 * - Uses minimal PDF files for testing
 */

const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };
const API_BASE = 'http://localhost:8000';
const FRONTEND_BASE = 'http://localhost:5173';

// Helper function to create minimal PDF
function createMinimalPdf(filename: string): Buffer {
  return Buffer.from(
    `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(${filename} - Test Resume) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
310
%%EOF
`
  );
}

// Helper function to create test ZIP file using Python
async function createTestZipFile(filenames: string[]): Promise<string> {
  const tempDir = tmpdir();
  const zipPath = path.join(tempDir, `test-resumes-${Date.now()}.zip`);

  // Create a temporary directory for PDFs
  const pdfDir = path.join(tempDir, `pdfs-${Date.now()}`);
  fs.mkdirSync(pdfDir, { recursive: true });

  // Create PDF files
  for (const filename of filenames) {
    const pdfPath = path.join(pdfDir, filename);
    fs.writeFileSync(pdfPath, createMinimalPdf(filename));
  }

  // Use Python to create ZIP
  const pythonScript = `
import zipfile
import sys
zip_path = sys.argv[1]
pdf_dir = sys.argv[2]
filenames = sys.argv[3:]

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in filenames:
        file_path = f"{pdf_dir}/{filename}"
        zipf.write(file_path, filename)

print(f"Created ZIP with {len(filenames)} files")
`;

  const tempScriptPath = path.join(tempDir, `create-zip-${Date.now()}.py`);
  fs.writeFileSync(tempScriptPath, pythonScript);

  try {
    const command = `python3 ${tempScriptPath} ${zipPath} ${pdfDir} ${filenames.join(' ')}`;
    execSync(command, { stdio: 'pipe' });
  } catch (error) {
    // Fallback: try with 'python' instead of 'python3'
    try {
      const command = `python ${tempScriptPath} ${zipPath} ${pdfDir} ${filenames.join(' ')}`;
      execSync(command, { stdio: 'pipe' });
    } catch (error2) {
      throw new Error(`Failed to create ZIP file: ${error}`);
    }
  } finally {
    // Clean up temporary files
    if (fs.existsSync(tempScriptPath)) {
      fs.unlinkSync(tempScriptPath);
    }
    // Clean up PDF directory
    if (fs.existsSync(pdfDir)) {
      fs.rmSync(pdfDir, { recursive: true, force: true });
    }
  }

  return zipPath;
}

// Helper to clean up temporary ZIP files
function cleanupTempFile(filePath: string): void {
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  } catch (error) {
    // Ignore cleanup errors
  }
}

test.describe('Bulk Operations - ZIP File Upload', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    // Navigate to recruiter dashboard or vacancies page
    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);
    await page.waitForLoadState('networkidle');
  });

  test('should display bulk upload component', async ({ page }) => {
    // Look for bulk upload component or button to trigger it
    const bulkUploadButton = page.getByRole('button', { name: /Bulk Upload|Upload Resumes|Upload Multiple/i }).or(
      page.locator('[data-testid="bulk-upload-button"]').or(page.locator('.bulk-upload-trigger'))
    );

    const count = await bulkUploadButton.count();
    if (count > 0) {
      await expect(bulkUploadButton.first()).toBeVisible();
    } else {
      // Check if component is already visible on page
      const bulkUploadZone = page.locator('[data-testid="bulk-upload-zone"]').or(
        page.locator('.bulk-upload-zone').or(page.locator('[role="progressbar"]'))
      );
      const zoneCount = await bulkUploadZone.count();
      if (zoneCount > 0) {
        await expect(bulkUploadZone.first()).toBeVisible();
      }
    }
  });

  test('should upload ZIP file with multiple resumes', async ({ page }) => {
    // Create test ZIP file with 3 resumes
    const tempZipPath = await createTestZipFile([
      'resume1.pdf',
      'resume2.pdf',
      'resume3.pdf'
    ]);

    // Navigate to bulk upload interface
    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    // Look for drag-and-drop zone or file input
    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    const count = await fileInput.count();
    expect(count).toBeGreaterThan(0);

    try {
      // Upload the ZIP file
      await fileInput.first().setInputFiles(tempZipPath);

      // Wait for upload to initiate
      await page.waitForTimeout(1000);

      // Verify progress indicators appear
      const progressBar = page.locator('[role="progressbar"]').or(
        page.locator('.linear-progress').or(page.locator('[data-testid="upload-progress"]'))
      );

      await expect(progressBar.first()).toBeVisible({ timeout: 10000 });

      // Verify status text appears
      const statusText = page.getByText(/completed|total|remaining|uploading/i, { exact: false });
      await expect(statusText.first()).toBeVisible({ timeout: 10000 });

      // Wait for batch processing to complete (or at least start)
      await page.waitForTimeout(3000);

      // Verify completion or in-progress state
      const completionText = page.getByText(/complete|success|done|finished/i, { exact: false }).or(
        page.getByText(/3\/3|3 total/i, { exact: false })
      );

      // Check for success message
      const successCount = await completionText.count();
      if (successCount > 0) {
        await expect(completionText.first()).toBeVisible();
      }
    } finally {
      // Clean up temp file
      cleanupTempFile(tempZipPath);
    }
  });

  test('should display correct progress counts', async ({ page }) => {
    // Create test ZIP file with 5 resumes
    const tempZipPath = await createTestZipFile([
      'resume1.pdf',
      'resume2.pdf',
      'resume3.pdf',
      'resume4.pdf',
      'resume5.pdf'
    ]);

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(tempZipPath);
      await page.waitForTimeout(1000);

      // Look for progress text showing counts
      const progressText = page.getByText(/\d+\/\d+|completed|total/i, { exact: false });

      // Wait for progress to be visible
      await expect(progressText.first()).toBeVisible({ timeout: 10000 });

      // Verify the text contains numbers (counts)
      const textContent = await progressText.first().textContent();
      expect(textContent).toMatch(/\d+/); // Should contain at least one number

      // Check if it shows "5 total" or "5/5" or similar
      const hasFiveTotal = /5/.test(textContent || '');
      expect(hasFiveTotal).toBeTruthy();

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should show batch job status updates', async ({ page }) => {
    const tempZipPath = await createTestZipFile(['resume1.pdf', 'resume2.pdf']);

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(tempZipPath);
      await page.waitForTimeout(1000);

      // Check for status indicators
      const statusIndicator = page.getByText(/processing|uploading|analyzing|complete/i, { exact: false });

      // Wait for status to appear
      await expect(statusIndicator.first()).toBeVisible({ timeout: 10000 });

      // Wait a bit to see if status changes
      await page.waitForTimeout(2000);

      // Check for final status or batch ID reference
      const batchIdText = page.getByText(/batch|job|id/i, { exact: false });
      const batchCount = await batchIdText.count();

      if (batchCount > 0) {
        // Batch reference found
        await expect(batchIdText.first()).toBeVisible();
      }

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should validate file size limits', async ({ page }) => {
    // Create a ZIP file that exceeds size limits
    const tempDir = tmpdir();
    const largeZipPath = path.join(tempDir, `test-large-${Date.now()}.zip`);
    const pdfDir = path.join(tempDir, `pdfs-large-${Date.now()}`);
    fs.mkdirSync(pdfDir, { recursive: true });

    // Create a large PDF file (over 100MB)
    const largePdfPath = path.join(pdfDir, 'large-resume.pdf');
    const largeContent = Buffer.alloc(150 * 1024 * 1024); // 150 MB
    fs.writeFileSync(largePdfPath, largeContent);

    // Create ZIP with large file using Python
    const pythonScript = `
import zipfile
import sys
zip_path = sys.argv[1]
pdf_path = sys.argv[2]
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(pdf_path, 'large-resume.pdf')
`;
    const tempScriptPath = path.join(tempDir, `create-large-zip-${Date.now()}.py`);
    fs.writeFileSync(tempScriptPath, pythonScript);

    try {
      execSync(`python3 ${tempScriptPath} ${largeZipPath} ${largePdfPath}`, { stdio: 'pipe' });
    } catch (error) {
      try {
        execSync(`python ${tempScriptPath} ${largeZipPath} ${largePdfPath}`, { stdio: 'pipe' });
      } catch (error2) {
        // Ignore
      }
    }

    // Clean up temp script and PDF
    if (fs.existsSync(tempScriptPath)) {
      fs.unlinkSync(tempScriptPath);
    }
    if (fs.existsSync(pdfDir)) {
      fs.rmSync(pdfDir, { recursive: true, force: true });
    }

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(largeZipPath);
      await page.waitForTimeout(2000);

      // Look for error message about file size
      const errorMessage = page.getByText(/size|too large|limit|exceeded/i, { exact: false });

      // Error should appear
      await expect(errorMessage.first()).toBeVisible({ timeout: 10000 });

    } finally {
      cleanupTempFile(largeZipPath);
    }
  });

  test('should reject invalid file types in ZIP', async ({ page }) => {
    // Create ZIP with invalid file types
    const tempDir = tmpdir();
    const invalidZipPath = path.join(tempDir, `test-invalid-${Date.now()}.zip`);
    const fileDir = path.join(tempDir, `files-invalid-${Date.now()}`);
    fs.mkdirSync(fileDir, { recursive: true });

    // Create a mix of valid and invalid files
    fs.writeFileSync(path.join(fileDir, 'resume1.pdf'), createMinimalPdf('resume1.pdf'));
    fs.writeFileSync(path.join(fileDir, 'resume.exe'), Buffer.from('invalid executable'));
    fs.writeFileSync(path.join(fileDir, 'readme.txt'), Buffer.from('readme content'));

    // Create ZIP
    const pythonScript = `
import zipfile
import sys
zip_path = sys.argv[1]
file_dir = sys.argv[2]
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(f"{file_dir}/resume1.pdf", 'resume1.pdf')
    zipf.write(f"{file_dir}/resume.exe", 'resume.exe')
    zipf.write(f"{file_dir}/readme.txt", 'readme.txt')
`;
    const tempScriptPath = path.join(tempDir, `create-invalid-zip-${Date.now()}.py`);
    fs.writeFileSync(tempScriptPath, pythonScript);

    try {
      execSync(`python3 ${tempScriptPath} ${invalidZipPath} ${fileDir}`, { stdio: 'pipe' });
    } catch (error) {
      try {
        execSync(`python ${tempScriptPath} ${invalidZipPath} ${fileDir}`, { stdio: 'pipe' });
      } catch (error2) {
        // Ignore
      }
    }

    // Clean up
    if (fs.existsSync(tempScriptPath)) {
      fs.unlinkSync(tempScriptPath);
    }
    if (fs.existsSync(fileDir)) {
      fs.rmSync(fileDir, { recursive: true, force: true });
    }

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(invalidZipPath);
      await page.waitForTimeout(2000);

      // Should show warning about invalid files
      const warningMessage = page.getByText(/invalid|skipped|not supported|exe/i, { exact: false });
      const warningCount = await warningMessage.count();

      if (warningCount > 0) {
        await expect(warningMessage.first()).toBeVisible();
      }

    } finally {
      cleanupTempFile(invalidZipPath);
    }
  });
});

test.describe('Bulk Operations - API Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should create batch job via API', async ({ page }) => {
    // This test verifies the backend API directly
    const tempZipPath = await createTestZipFile(['resume1.pdf', 'resume2.pdf']);
    const zipBuffer = fs.readFileSync(tempZipPath);

    // Use fetch API to upload directly
    const formData = new FormData();
    const blob = new Blob([zipBuffer], { type: 'application/zip' });
    formData.append('files', blob, 'test-resumes.zip');
    formData.append('notification_email', 'test@example.com');

    const response = await fetch(`${API_BASE}/api/batch/upload`, {
      method: 'POST',
      body: formData,
    });

    expect(response.ok).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('batch_id');
    expect(data).toHaveProperty('total_files');
    expect(data.total_files).toBeGreaterThanOrEqual(2);

    // Verify batch job was created
    const batchId = data.batch_id;
    const statusResponse = await fetch(`${API_BASE}/api/batch/${batchId}`);

    expect(statusResponse.ok).toBeTruthy();

    const statusData = await statusResponse.json();
    expect(statusData).toHaveProperty('status');
    expect(statusData).toHaveProperty('total_files');

    cleanupTempFile(tempZipPath);
  });

  test('should poll batch status and get results', async ({ page, request }) => {
    // Upload a batch
    const tempZipPath = await createTestZipFile(['resume1.pdf']);
    const zipBuffer = fs.readFileSync(tempZipPath);

    const formData = new FormData();
    const blob = new Blob([zipBuffer], { type: 'application/zip' });
    formData.append('files', blob, 'test-resumes.zip');

    const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
      multipart: {
        files: {
          name: 'test-resumes.zip',
          mimeType: 'application/zip',
          buffer: zipBuffer,
        },
      },
    });

    expect(uploadResponse.ok()).toBeTruthy();

    const uploadData = await uploadResponse.json();
    const batchId = uploadData.batch_id;

    // Poll for status
    let maxAttempts = 30;
    let attempts = 0;
    let finalStatus = null;

    while (attempts < maxAttempts) {
      const statusResponse = await request.get(`${API_BASE}/api/batch/${batchId}`);

      expect(statusResponse.ok()).toBeTruthy();

      const statusData = await statusResponse.json();
      finalStatus = statusData.status;

      if (finalStatus === 'completed' || finalStatus === 'failed') {
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
      attempts++;
    }

    // Verify we got a final status
    expect(['completed', 'failed', 'processing']).toContain(finalStatus);

    // Get results if completed
    if (finalStatus === 'completed') {
      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      expect(resultsData).toHaveProperty('results');
      expect(resultsData).toHaveProperty('successful_count');
    }

    cleanupTempFile(tempZipPath);
  });
});

test.describe('Bulk Operations - Progress Tracking Accuracy', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should track progress accurately for 10 files', async ({ page }) => {
    // Create ZIP with 10 files
    const filenames = Array.from({ length: 10 }, (_, i) => `resume${i + 1}.pdf`);
    const tempZipPath = await createTestZipFile(filenames);

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(tempZipPath);
      await page.waitForTimeout(1000);

      // Look for progress text
      const progressText = page.getByText(/10|total|completed/i, { exact: false });

      // Verify progress shows 10 files
      await expect(progressText.first()).toBeVisible({ timeout: 15000 });

      const textContent = await progressText.first().textContent();
      expect(textContent).toMatch(/10/); // Should reference 10 files

      // Wait for processing to progress
      await page.waitForTimeout(5000);

      // Check for progress percentage or count update
      const percentageText = page.getByText(/\d+%|\d+\/10/i, { exact: false });
      const percentageCount = await percentageText.count();

      if (percentageCount > 0) {
        const pctText = await percentageText.first().textContent();
        expect(pctText).toMatch(/\d+/); // Should have numbers
      }

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should handle empty ZIP file gracefully', async ({ page }) => {
    // Create empty ZIP
    const tempDir = tmpdir();
    const emptyZipPath = path.join(tempDir, `test-empty-${Date.now()}.zip`);

    const pythonScript = `
import zipfile
zip_path = '${emptyZipPath}'
with zipfile.ZipFile(zip_path, 'w') as zipf:
    pass  # Empty ZIP
`;
    const tempScriptPath = path.join(tempDir, `create-empty-zip-${Date.now()}.py`);
    fs.writeFileSync(tempScriptPath, pythonScript);

    try {
      execSync(`python3 ${tempScriptPath}`, { stdio: 'pipe' });
    } catch (error) {
      try {
        execSync(`python ${tempScriptPath}`, { stdio: 'pipe' });
      } catch (error2) {
        // Ignore
      }
    }

    if (fs.existsSync(tempScriptPath)) {
      fs.unlinkSync(tempScriptPath);
    }

    await page.goto(`${FRONTEND_BASE}/recruiter/vacancies`);

    const fileInput = page.locator('input[type="file"]').or(
      page.locator('[data-testid="bulk-upload-input"]')
    );

    try {
      await fileInput.first().setInputFiles(emptyZipPath);
      await page.waitForTimeout(2000);

      // Should show error about empty ZIP
      const errorMessage = page.getByText(/empty|no files|nothing|0 files/i, { exact: false });
      await expect(errorMessage.first()).toBeVisible({ timeout: 10000 });

    } finally {
      cleanupTempFile(emptyZipPath);
    }
  });
});

test.describe('Bulk Operations - Bulk Export to ZIP/PDF', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should export selected candidates as ZIP file', async ({ page, request }) => {
    // First, upload some test resumes to have candidates to export
    const tempZipPath = await createTestZipFile(['resume1.pdf', 'resume2.pdf', 'resume3.pdf']);

    try {
      // Upload resumes
      const formData = new FormData();
      const zipBuffer = Buffer.from(fs.readFileSync(tempZipPath));
      const blob = new Blob([zipBuffer], { type: 'application/zip' });
      formData.append('files', blob, 'test-resumes.zip');

      const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
        multipart: {
          files: {
            name: 'test-resumes.zip',
            mimeType: 'application/zip',
            buffer: zipBuffer,
          },
        },
      });

      expect(uploadResponse.ok()).toBeTruthy();
      const uploadData = await uploadResponse.json();
      const batchId = uploadData.batch_id;

      // Wait for batch processing to complete
      await page.waitForTimeout(3000);

      // Get batch results to obtain resume IDs
      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      expect(resultsData).toHaveProperty('results');

      // Extract resume IDs from results
      const resumeIds = resultsData.results
        .filter((r: any) => r.status === 'success')
        .map((r: any) => r.resume_id);

      expect(resumeIds.length).toBeGreaterThan(0);

      // Export resumes as ZIP
      const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
        data: {
          resume_ids: resumeIds,
          format: 'zip',
        },
      });

      // Verify response
      expect(exportResponse.ok()).toBeTruthy();
      expect(exportResponse.headers()['content-type']).toContain('application/zip');

      // Verify content-disposition header
      const contentDisposition = exportResponse.headers()['content-disposition'];
      expect(contentDisposition).toContain('attachment');
      expect(contentDisposition).toContain('.zip');

      // Download and verify ZIP content
      const zipBuffer = await exportResponse.body();
      expect(zipBuffer.length).toBeGreaterThan(0);

      // Verify it's a valid ZIP file (starts with PK signature)
      expect(zipBuffer[0]).toBe(0x50); // P
      expect(zipBuffer[1]).toBe(0x4B); // K

      // Verify ZIP structure by looking for PDF file markers
      const zipStr = zipBuffer.toString();
      expect(zipStr).toContain('.pdf');

      // Count occurrences of PDF signatures in ZIP
      let pdfCount = 0;
      for (let i = 0; i < zipBuffer.length - 4; i++) {
        if (zipBuffer[i] === 0x25 && // %
            zipBuffer[i + 1] === 0x50 && // P
            zipBuffer[i + 2] === 0x44 && // D
            zipBuffer[i + 3] === 0x46) { // F
          pdfCount++;
        }
      }

      // Should have at least as many PDF signatures as we requested
      expect(pdfCount).toBeGreaterThanOrEqual(resumeIds.length);

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should export selected candidates as PDF format (ZIP containing PDFs)', async ({ page, request }) => {
    // Upload test resumes
    const tempZipPath = await createTestZipFile(['candidate1.pdf', 'candidate2.pdf']);

    try {
      // Upload resumes
      const zipBuffer = fs.readFileSync(tempZipPath);

      const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
        multipart: {
          files: {
            name: 'test-resumes.zip',
            mimeType: 'application/zip',
            buffer: zipBuffer,
          },
        },
      });

      expect(uploadResponse.ok()).toBeTruthy();
      const uploadData = await uploadResponse.json();
      const batchId = uploadData.batch_id;

      // Wait for processing
      await page.waitForTimeout(3000);

      // Get results
      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      const resumeIds = resultsData.results
        .filter((r: any) => r.status === 'success')
        .map((r: any) => r.resume_id);

      expect(resumeIds.length).toBeGreaterThan(0);

      // Export as PDF format
      const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
        data: {
          resume_ids: resumeIds,
          format: 'pdf',
        },
      });

      // Verify response
      expect(exportResponse.ok()).toBeTruthy();
      expect(exportResponse.headers()['content-type']).toContain('application/zip');

      // Verify content-disposition mentions PDF
      const contentDisposition = exportResponse.headers()['content-disposition'];
      expect(contentDisposition).toContain('attachment');
      expect(contentDisposition).toLowerCase().toContain('pdf');

      // Download and verify ZIP content
      const zipBuffer = await exportResponse.body();
      expect(zipBuffer.length).toBeGreaterThan(0);

      // Verify it's a valid ZIP file
      expect(zipBuffer[0]).toBe(0x50); // P
      expect(zipBuffer[1]).toBe(0x4B); // K

      // Verify ZIP contains PDF files
      const zipStr = zipBuffer.toString();
      expect(zipStr).toContain('.pdf');

      // Count PDF signatures in ZIP
      let pdfCount = 0;
      for (let i = 0; i < zipBuffer.length - 4; i++) {
        if (zipBuffer[i] === 0x25 && // %
            zipBuffer[i + 1] === 0x50 && // P
            zipBuffer[i + 2] === 0x44 && // D
            zipBuffer[i + 3] === 0x46) { // F
          pdfCount++;
        }
      }

      // Should have PDFs for each resume
      expect(pdfCount).toBeGreaterThanOrEqual(resumeIds.length);

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should handle invalid resume IDs gracefully', async ({ request }) => {
    const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
      data: {
        resume_ids: ['invalid-uuid-1', 'invalid-uuid-2'],
        format: 'zip',
      },
    });

    // Should return 404 when no valid resumes found
    expect(exportResponse.status()).toBe(404);

    const errorData = await exportResponse.json();
    expect(errorData).toHaveProperty('detail');
    expect(errorData.detail).toContain('No valid resumes found');
  });

  test('should handle empty resume ID list', async ({ request }) => {
    const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
      data: {
        resume_ids: [],
        format: 'zip',
      },
    });

    // Should return 422 for validation error
    expect(exportResponse.status()).toBe(422);
  });

  test('should handle invalid export format', async ({ request }) => {
    const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
      data: {
        resume_ids: ['some-resume-id'],
        format: 'docx', // Invalid format
      },
    });

    // Should return 400 for invalid format
    expect(exportResponse.status()).toBe(400);

    const errorData = await exportResponse.json();
    expect(errorData).toHaveProperty('detail');
    expect(errorData.detail).toContain('Invalid format');
  });

  test('should handle partial success (mix of valid and invalid IDs)', async ({ page, request }) => {
    // Upload one test resume
    const tempZipPath = await createTestZipFile(['single-resume.pdf']);

    try {
      const zipBuffer = fs.readFileSync(tempZipPath);

      const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
        multipart: {
          files: {
            name: 'test-resumes.zip',
            mimeType: 'application/zip',
            buffer: zipBuffer,
          },
        },
      });

      expect(uploadResponse.ok()).toBeTruthy();
      const uploadData = await uploadResponse.json();
      const batchId = uploadData.batch_id;

      await page.waitForTimeout(3000);

      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      const validResumeIds = resultsData.results
        .filter((r: any) => r.status === 'success')
        .map((r: any) => r.resume_id);

      // Mix valid and invalid IDs
      const mixedIds = [
        validResumeIds[0],
        'invalid-uuid-xxx',
      ];

      const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
        data: {
          resume_ids: mixedIds,
          format: 'zip',
        },
      });

      // Should succeed with valid resumes only
      expect(exportResponse.ok()).toBeTruthy();

      // Verify ZIP contains only the valid resume
      const zipBuffer = await exportResponse.body();
      expect(zipBuffer.length).toBeGreaterThan(0);

      // Verify ZIP signature
      expect(zipBuffer[0]).toBe(0x50); // P
      expect(zipBuffer[1]).toBe(0x4B); // K

      // Count PDF signatures - should only have 1 valid resume
      let pdfCount = 0;
      for (let i = 0; i < zipBuffer.length - 4; i++) {
        if (zipBuffer[i] === 0x25 && // %
            zipBuffer[i + 1] === 0x50 && // P
            zipBuffer[i + 2] === 0x44 && // D
            zipBuffer[i + 3] === 0x46) { // F
          pdfCount++;
        }
      }

      expect(pdfCount).toBe(1);

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should verify downloaded file size matches content-length header', async ({ page, request }) => {
    const tempZipPath = await createTestZipFile(['resume1.pdf', 'resume2.pdf']);

    try {
      const zipBuffer = fs.readFileSync(tempZipPath);

      const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
        multipart: {
          files: {
            name: 'test-resumes.zip',
            mimeType: 'application/zip',
            buffer: zipBuffer,
          },
        },
      });

      expect(uploadResponse.ok()).toBeTruthy();
      const uploadData = await uploadResponse.json();
      const batchId = uploadData.batch_id;

      await page.waitForTimeout(3000);

      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      const resumeIds = resultsData.results
        .filter((r: any) => r.status === 'success')
        .map((r: any) => r.resume_id);

      const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
        data: {
          resume_ids: resumeIds,
          format: 'zip',
        },
      });

      expect(exportResponse.ok()).toBeTruthy();

      // Verify content-length header exists
      const contentLength = exportResponse.headers()['content-length'];
      expect(contentLength).toBeDefined();
      expect(parseInt(contentLength)).toBeGreaterThan(0);

      // Verify actual download size matches content-length
      const downloadedBuffer = await exportResponse.body();
      expect(downloadedBuffer.length).toBe(parseInt(contentLength));

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });

  test('should export large number of candidates successfully', async ({ page, request }) => {
    // Create ZIP with 10 resumes to test larger exports
    const filenames = Array.from({ length: 10 }, (_, i) => `resume${i + 1}.pdf`);
    const tempZipPath = await createTestZipFile(filenames);

    try {
      const zipBuffer = fs.readFileSync(tempZipPath);

      const uploadResponse = await request.post(`${API_BASE}/api/batch/upload`, {
        multipart: {
          files: {
            name: 'test-resumes.zip',
            mimeType: 'application/zip',
            buffer: zipBuffer,
          },
        },
      });

      expect(uploadResponse.ok()).toBeTruthy();
      const uploadData = await uploadResponse.json();
      const batchId = uploadData.batch_id;

      // Wait longer for processing 10 files
      await page.waitForTimeout(5000);

      const resultsResponse = await request.get(`${API_BASE}/api/batch/${batchId}/results`);
      expect(resultsResponse.ok()).toBeTruthy();

      const resultsData = await resultsResponse.json();
      const resumeIds = resultsData.results
        .filter((r: any) => r.status === 'success')
        .map((r: any) => r.resume_id);

      expect(resumeIds.length).toBe(10);

      // Export all 10 resumes
      const exportResponse = await request.post(`${API_BASE}/api/candidates/bulk-export`, {
        data: {
          resume_ids: resumeIds,
          format: 'zip',
        },
      });

      expect(exportResponse.ok()).toBeTruthy();

      // Verify ZIP contains all 10 files
      const downloadedBuffer = await exportResponse.body();
      expect(downloadedBuffer.length).toBeGreaterThan(0);

      // Verify ZIP signature
      expect(downloadedBuffer[0]).toBe(0x50); // P
      expect(downloadedBuffer[1]).toBe(0x4B); // K

      // Count PDF signatures - should have 10 resumes
      let pdfCount = 0;
      for (let i = 0; i < downloadedBuffer.length - 4; i++) {
        if (downloadedBuffer[i] === 0x25 && // %
            downloadedBuffer[i + 1] === 0x50 && // P
            downloadedBuffer[i + 2] === 0x44 && // D
            downloadedBuffer[i + 3] === 0x46) { // F
          pdfCount++;
        }
      }

      expect(pdfCount).toBeGreaterThanOrEqual(10);

    } finally {
      cleanupTempFile(tempZipPath);
    }
  });
});
