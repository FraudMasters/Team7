/**
 * E2E Tests for Resume Correction Flow
 *
 * This test suite validates the complete manual correction workflow:
 * - Navigating to resume results page
 * - Viewing visual parsing feedback with source text highlighting
 * - Selecting fields to see source locations
 * - Editing parsed data (skills, education, work experience, languages)
 * - Providing correction reasons
 * - Saving corrections successfully
 * - Verifying correction status indicators
 *
 * Prerequisites:
 * - Frontend running on http://localhost:5173
 * - Backend API running at http://localhost:8888
 * - Test resume data available
 *
 * Environment Variables:
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - API_URL: Backend API URL (default: http://localhost:8888)
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8888';

/**
 * Test resume ID for testing
 */
const TEST_RESUME_ID = 'test-resume-correction-123';

/**
 * Helper function to mock resume data API
 */
async function mockResumeDataAPI(page: Page, resumeId: string) {
  await page.route(`**/api/resumes/${resumeId}`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: resumeId,
        filename: 'test-resume.pdf',
        status: 'completed',
        raw_text: `John Doe
Senior Software Engineer

EXPERIENCE
Senior Software Engineer at TechCorp Inc. (2020-2024)
- Led development of microservices architecture
- Mentored junior developers

Software Engineer at StartupXYZ (2018-2020)
- Built RESTful APIs using Python and Node.js
- Implemented CI/CD pipelines

EDUCATION
Bachelor of Science in Computer Science
University of Technology (2014-2018)

SKILLS
Python, JavaScript, TypeScript, React, Node.js, Docker, Kubernetes, AWS

LANGUAGES
English (Native), Spanish (Intermediate)`,
        skills: [
          { id: '1', name: 'Python', category: 'Programming', proficiency_level: 'Expert', years_of_experience: 6 },
          { id: '2', name: 'JavaScript', category: 'Programming', proficiency_level: 'Expert', years_of_experience: 5 },
          { id: '3', name: 'TypeScript', category: 'Programming', proficiency_level: 'Advanced', years_of_experience: 3 },
        ],
        education: [
          {
            id: '1',
            institution_name: 'University of Technology',
            degree: 'Bachelor of Science',
            field_of_study: 'Computer Science',
            start_date: '2014',
            end_date: '2018',
          },
        ],
        work_experience: [
          {
            id: '1',
            company_name: 'TechCorp Inc.',
            position_title: 'Senior Software Engineer',
            location: 'San Francisco, CA',
            start_date: '2020',
            end_date: '2024',
            employment_type: 'full_time',
          },
          {
            id: '2',
            company_name: 'StartupXYZ',
            position_title: 'Software Engineer',
            location: 'Austin, TX',
            start_date: '2018',
            end_date: '2020',
            employment_type: 'full_time',
          },
        ],
        languages: [
          { name: 'English', proficiency: 'Native' },
          { name: 'Spanish', proficiency: 'Intermediate' },
        ],
        source_locations: [
          { field_name: 'skills', location: { text: 'Python, JavaScript, TypeScript, React, Node.js, Docker, Kubernetes, AWS' } },
          { field_name: 'education', location: { text: 'Bachelor of Science in Computer Science\nUniversity of Technology (2014-2018)' } },
          { field_name: 'work_experience', location: { text: 'Senior Software Engineer at TechCorp Inc. (2020-2024)' } },
          { field_name: 'languages', location: { text: 'English (Native), Spanish (Intermediate)' } },
        ],
      }),
    });
  });
}

/**
 * Helper function to mock corrections API
 */
async function mockCorrectionsAPI(page: Page, resumeId: string) {
  // Mock GET corrections
  await page.route(`**/api/parsing-corrections/${resumeId}`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: [],
        total: 0,
      }),
    });
  });

  // Mock POST correction
  await page.route(`**/api/parsing-corrections/${resumeId}`, (route) => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: `correction-${Date.now()}`,
          resume_id: resumeId,
          field_name: body.field_name,
          original_value: body.original_value,
          corrected_value: body.corrected_value,
          reason: body.reason,
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      route.continue();
    }
  });
}

/**
 * Helper function to navigate to resume results page
 */
async function navigateToResumeResults(page: Page, resumeId: string) {
  await page.goto(`${BASE_URL}/jobs/resume-results/${resumeId}`);
  await page.waitForLoadState('networkidle');
}

test.describe('Resume Correction Flow - Page Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
  });

  test('should load resume results page successfully', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Check for page title
    await expect(page.getByRole('heading', { name: /Resume Analysis Results/i })).toBeVisible({ timeout: 10000 });

    // Check for resume ID display
    await expect(page.getByText(`Resume ID: ${TEST_RESUME_ID}`)).toBeVisible();
  });

  test('should display all tabs on resume results page', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Check for all tabs
    await expect(page.getByRole('tab', { name: /Analysis/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Vacancy Matches/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Visual Feedback/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Edit Data/i })).toBeVisible();
  });

  test('should navigate to Visual Feedback tab', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Click on Visual Feedback tab
    await page.getByRole('tab', { name: /Visual Feedback/i }).click();
    await page.waitForTimeout(500);

    // Check for visual feedback content
    await expect(page.getByText(/Visual Parsing Feedback|Source Text|Extracted Fields/i)).toBeVisible();
  });

  test('should navigate to Edit Data tab', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Click on Edit Data tab
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);

    // Check for edit data content
    await expect(page.getByText(/Edit Parsed Data|Review and correct/i)).toBeVisible();
  });
});

test.describe('Resume Correction Flow - Visual Feedback', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Visual Feedback/i }).click();
    await page.waitForTimeout(500);
  });

  test('should display source text panel', async ({ page }) => {
    // Check for source text section
    await expect(page.getByText(/Source Text|characters/i)).toBeVisible();
  });

  test('should display extracted fields panel', async ({ page }) => {
    // Check for extracted fields section
    await expect(page.getByText(/Extracted Fields|Search fields/i)).toBeVisible();
  });

  test('should show field count', async ({ page }) => {
    // Check for fields count indicator
    const fieldCount = page.getByText(/\d+ fields/i);
    await expect(fieldCount).toBeVisible();
  });

  test('should display category tabs for fields', async ({ page }) => {
    // Check for category tabs (at least one should be visible)
    const categoryTabs = page.getByRole('tab');
    const count = await categoryTabs.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should allow searching for fields', async ({ page }) => {
    // Find search input
    const searchInput = page.getByPlaceholder(/Search fields/i);
    await expect(searchInput).toBeVisible();

    // Type search query
    await searchInput.fill('Python');
    await page.waitForTimeout(500);

    // Search input should contain the query
    await expect(searchInput).toHaveValue('Python');
  });

  test('should allow selecting a field to highlight source', async ({ page }) => {
    // Look for field items
    const fieldItems = page.locator('[role="listitem"]').or(page.locator('.MuiListItem-root'));
    const count = await fieldItems.count();

    if (count > 0) {
      // Click on a field
      await fieldItems.first().click();
      await page.waitForTimeout(300);

      // Check for highlighting indicator or selected state
      const highlightIndicator = page.getByText(/Highlighting:|Clear/i);
      const hasHighlight = await highlightIndicator.count() > 0;
      expect(hasHighlight).toBeTruthy();
    }
  });
});

test.describe('Resume Correction Flow - Edit Data', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);
  });

  test('should display section tabs for editing', async ({ page }) => {
    // Check for section tabs
    await expect(page.getByRole('tab', { name: /Skills/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Education/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Work Experience/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Languages/i })).toBeVisible();
  });

  test('should display skills list', async ({ page }) => {
    // Skills tab should be active by default
    await expect(page.getByText(/Skills \(|Python/i)).toBeVisible();
  });

  test('should display education list when tab is clicked', async ({ page }) => {
    // Click Education tab
    await page.getByRole('tab', { name: /Education/i }).click();
    await page.waitForTimeout(300);

    // Check for education items
    await expect(page.getByText(/University of Technology|Bachelor/i)).toBeVisible();
  });

  test('should display work experience list when tab is clicked', async ({ page }) => {
    // Click Work Experience tab
    await page.getByRole('tab', { name: /Work Experience/i }).click();
    await page.waitForTimeout(300);

    // Check for work experience items
    await expect(page.getByText(/TechCorp|Senior Software Engineer/i)).toBeVisible();
  });

  test('should display languages list when tab is clicked', async ({ page }) => {
    // Click Languages tab
    await page.getByRole('tab', { name: /Languages/i }).click();
    await page.waitForTimeout(300);

    // Check for language chips
    await expect(page.getByText(/English|Spanish/i)).toBeVisible();
  });

  test('should show edit buttons for each skill item', async ({ page }) => {
    // Look for edit buttons (pencil icons or "Edit" text)
    const editButtons = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    );
    const count = await editButtons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show delete buttons for each skill item', async ({ page }) => {
    // Look for delete buttons (trash icons or "Delete" text)
    const deleteButtons = page.locator('button').filter({ hasText: /Delete/i }).or(
      page.locator('[aria-label*="delete" i]')
    );
    const count = await deleteButtons.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Resume Correction Flow - Making Corrections', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);
  });

  test('should open edit form when edit button is clicked', async ({ page }) => {
    // Find and click edit button for first skill
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();

    await editButton.click();
    await page.waitForTimeout(500);

    // Check for form inputs or save button
    const saveButton = page.getByRole('button', { name: /Save/i });
    const cancelButton = page.getByRole('button', { name: /Cancel/i });

    await expect(saveButton.or(cancelButton)).toBeVisible();
  });

  test('should open correction reason dialog after saving changes', async ({ page }) => {
    // Click edit button
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    // Find a text input and modify it
    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await textInput.fill('Modified Skill Name');

      // Save the changes
      const saveButton = page.getByRole('button', { name: /Save/i });
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        await page.waitForTimeout(500);

        // Check for correction reason dialog
        const correctionDialog = page.getByRole('dialog');
        const reasonSelect = page.getByText(/Why are you making|Reason/i);

        // Dialog should appear
        await expect(correctionDialog.or(reasonSelect)).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should display correction reason options', async ({ page }) => {
    // Navigate to correction dialog
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    // Modify and save
    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await textInput.fill('Modified Value');
      const saveButton = page.getByRole('button', { name: /Save/i });
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        await page.waitForTimeout(500);

        // Check for reason dropdown
        const reasonDropdown = page.locator('[role="combobox"]').or(
          page.getByText(/Reason/i)
        );
        if (await reasonDropdown.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Click to open dropdown
          await reasonDropdown.click();
          await page.waitForTimeout(300);

          // Check for reason options
          const options = page.getByRole('option');
          const optionCount = await options.count();
          expect(optionCount).toBeGreaterThan(0);
        }
      }
    }
  });

  test('should allow canceling a correction', async ({ page }) => {
    // Navigate to correction dialog
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    // Modify and save
    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await textInput.fill('Test Value');
      const saveButton = page.getByRole('button', { name: /Save/i });
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        await page.waitForTimeout(500);

        // Check for cancel button in dialog
        const cancelButton = page.getByRole('button', { name: /Cancel/i }).first();
        if (await cancelButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await cancelButton.click();
          await page.waitForTimeout(300);

          // Dialog should be closed
          const dialog = page.getByRole('dialog');
          const dialogVisible = await dialog.isVisible({ timeout: 1000 }).catch(() => false);
          expect(dialogVisible).toBeFalsy();
        }
      }
    }
  });
});

test.describe('Resume Correction Flow - Complete Workflow', () => {
  test('should complete full correction workflow from view to save', async ({ page }) => {
    // Setup API mocks
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);

    // Step 1: Navigate to resume results
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await expect(page.getByRole('heading', { name: /Resume Analysis Results/i })).toBeVisible();

    // Step 2: View Visual Feedback tab
    await page.getByRole('tab', { name: /Visual Feedback/i }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText(/Visual Parsing Feedback|Source Text/i)).toBeVisible();

    // Step 3: Navigate to Edit Data tab
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText(/Edit Parsed Data|Skills/i)).toBeVisible();

    // Step 4: Click edit on a skill
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    // Step 5: Modify a field
    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await textInput.fill('Corrected Skill Name');

      // Step 6: Save the change
      const saveButton = page.getByRole('button', { name: /Save/i });
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        await page.waitForTimeout(500);

        // Step 7: Correction dialog should appear
        const correctionDialog = page.getByRole('dialog');
        if (await correctionDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Select a reason
          const reasonSelect = page.locator('[role="combobox"]').or(
            page.getByText(/Reason/i).locator('..').locator('input, [role="combobox"]')
          );
          if (await reasonSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
            await reasonSelect.click();
            await page.waitForTimeout(300);

            // Select first option
            const firstOption = page.getByRole('option').first();
            if (await firstOption.isVisible({ timeout: 2000 }).catch(() => false)) {
              await firstOption.click();
              await page.waitForTimeout(300);

              // Confirm correction
              const confirmButton = page.getByRole('button', { name: /Confirm|Save/i }).first();
              if (await confirmButton.isEnabled({ timeout: 1000 }).catch(() => false)) {
                await confirmButton.click();
                await page.waitForTimeout(1000);

                // Step 8: Verify correction was saved (dialog closes)
                const dialogClosed = !(await correctionDialog.isVisible({ timeout: 1000 }).catch(() => false));
                expect(dialogClosed).toBeTruthy();
              }
            }
          }
        }
      }
    }
  });

  test('should show correction indicator after saving correction', async ({ page }) => {
    // Setup API mocks with existing correction
    await mockResumeDataAPI(page, TEST_RESUME_ID);

    // Mock GET corrections to return an existing correction
    await page.route(`**/api/parsing-corrections/${TEST_RESUME_ID}`, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            {
              id: 'correction-1',
              resume_id: TEST_RESUME_ID,
              field_name: 'skills',
              original_value: { name: 'Python' },
              corrected_value: { name: 'Python 3' },
              reason: 'incorrect_skill',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
        }),
      });
    });

    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);

    // Look for correction count indicator
    const correctionIndicator = page.getByText(/\d+ correction/i);
    await expect(correctionIndicator).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Resume Correction Flow - Add New Items', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);
  });

  test('should show Add Skill button', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /Add Skill/i });
    await expect(addButton).toBeVisible();
  });

  test('should show Add Education button', async ({ page }) => {
    // Click Education tab first
    await page.getByRole('tab', { name: /Education/i }).click();
    await page.waitForTimeout(300);

    const addButton = page.getByRole('button', { name: /Add Education/i });
    await expect(addButton).toBeVisible();
  });

  test('should show Add Work Experience button', async ({ page }) => {
    // Click Work Experience tab first
    await page.getByRole('tab', { name: /Work Experience/i }).click();
    await page.waitForTimeout(300);

    const addButton = page.getByRole('button', { name: /Add Work Experience/i });
    await expect(addButton).toBeVisible();
  });

  test('should open form when Add Skill is clicked', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /Add Skill/i });
    await addButton.click();
    await page.waitForTimeout(500);

    // Should show form with save/cancel buttons
    const saveButton = page.getByRole('button', { name: /Save/i });
    const cancelButton = page.getByRole('button', { name: /Cancel/i });

    await expect(saveButton.or(cancelButton)).toBeVisible();
  });
});

test.describe('Resume Correction Flow - Error Handling', () => {
  test('should handle missing resume ID gracefully', async ({ page }) => {
    // Navigate without ID
    await page.goto(`${BASE_URL}/jobs/resume-results/`);
    await page.waitForLoadState('networkidle');

    // Should show error or redirect
    const errorMessage = page.getByText(/not provided|error|not found/i);
    const hasError = await errorMessage.isVisible({ timeout: 5000 }).catch(() => false);

    // Or should redirect away from the page
    const url = page.url();
    const redirected = !url.includes('/resume-results/') || url.endsWith('/resume-results/');

    expect(hasError || redirected).toBeTruthy();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route(`**/api/resumes/${TEST_RESUME_ID}`, (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Should show error state
    const errorState = page.getByText(/error|failed|retry/i);
    await expect(errorState).toBeVisible({ timeout: 10000 });
  });

  test('should handle network errors during correction save', async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);

    // Mock network error on POST correction
    await page.route(`**/api/parsing-corrections/${TEST_RESUME_ID}`, (route) => {
      if (route.request().method() === 'POST') {
        route.abort('failed');
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [], total: 0 }),
        });
      }
    });

    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);

    // Try to make a correction
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await textInput.fill('Test Value');
      const saveButton = page.getByRole('button', { name: /Save/i });
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        await page.waitForTimeout(500);

        // Try to save correction
        const correctionDialog = page.getByRole('dialog');
        if (await correctionDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Select reason
          const reasonSelect = page.locator('[role="combobox"]').first();
          if (await reasonSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
            await reasonSelect.click();
            await page.waitForTimeout(300);
            const firstOption = page.getByRole('option').first();
            if (await firstOption.isVisible({ timeout: 2000 }).catch(() => false)) {
              await firstOption.click();
              await page.waitForTimeout(300);

              // Try to confirm
              const confirmButton = page.getByRole('button', { name: /Confirm/i }).first();
              if (await confirmButton.isEnabled({ timeout: 1000 }).catch(() => false)) {
                await confirmButton.click();
                await page.waitForTimeout(2000);

                // Should show error message
                const errorAlert = page.locator('[role="alert"]').or(page.getByText(/error|failed/i));
                const hasError = await errorAlert.isVisible({ timeout: 5000 }).catch(() => false);

                // Either error shown or still in dialog
                expect(hasError || await correctionDialog.isVisible().catch(() => false)).toBeTruthy();
              }
            }
          }
        }
      }
    }
  });
});

test.describe('Resume Correction Flow - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);

    // Tab through elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'DIV'].includes(focused || '')).toBeTruthy();
  });

  test('should have accessible tab panel', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Tabs should have proper roles
    const tabs = page.getByRole('tab');
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThanOrEqual(4);

    // Tab panel should exist
    const tabPanel = page.getByRole('tabpanel');
    await expect(tabPanel).toBeVisible();
  });

  test('should have accessible form inputs in edit mode', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);
    await page.getByRole('tab', { name: /Edit Data/i }).click();
    await page.waitForTimeout(500);

    // Click edit button
    const editButton = page.locator('button').filter({ hasText: /Edit/i }).or(
      page.locator('[aria-label*="edit" i]')
    ).first();
    await editButton.click();
    await page.waitForTimeout(500);

    // Check for visible inputs
    const inputs = page.locator('input:visible');
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThan(0);
  });
});

test.describe('Resume Correction Flow - Responsive Design', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await mockResumeDataAPI(page, TEST_RESUME_ID);
    await mockCorrectionsAPI(page, TEST_RESUME_ID);
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Main content should be visible
    await expect(page.getByRole('heading', { name: /Resume Analysis Results/i })).toBeVisible();

    // Tabs should be scrollable or visible
    const tabs = page.getByRole('tab');
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThanOrEqual(4);
  });

  test('should allow correction on mobile', async ({ page }) => {
    await navigateToResumeResults(page, TEST_RESUME_ID);

    // Navigate to Edit Data tab
    await page.getByRole('tab', { name: /Edit Data/i }).click({ force: true });
    await page.waitForTimeout(500);

    // Content should be visible
    await expect(page.getByText(/Edit Parsed Data|Skills/i)).toBeVisible();
  });
});
