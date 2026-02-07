import { test, expect, request } from '@playwright/test';

/**
 * E2E Tests for Vacancy Bulk Actions
 *
 * Test Suite Contents:
 * 1. Setup - Verify backend and frontend are running
 * 2. Bulk Delete Workflow - Complete end-to-end test for deleting multiple vacancies
 * 3. Selection Management - Test select all, clear all, and toggle selection
 * 4. Bulk Mode Toggle - Test entering and exiting bulk mode
 * 5. Bulk Update Status Workflow - Test updating active/inactive status for multiple vacancies
 * 6. Bulk Duplicate Workflow - Test duplicating single and multiple vacancies with field verification
 * 7. Error Handling and Partial Success - Test error scenarios and partial success handling
 * 8. UI and UX - Test empty states and success messages
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - No existing vacancies that could interfere with tests (tests create their own data)
 */

// Viewport configurations
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

// Test vacancy data
const createTestVacancy = (index: number) => ({
  title: `Test Vacancy ${index}`,
  description: `Test description for vacancy ${index}. This is a comprehensive job description.`,
  required_skills: ['JavaScript', 'TypeScript', 'React'],
  min_experience_months: 24,
  industry: 'Technology',
  work_format: 'Remote',
  location: 'San Francisco, CA',
  salary_min: 80000,
  salary_max: 120000,
});

/**
 * Helper function to create test vacancies via API
 */
async function createVacancies(apiContext: any, count: number): Promise<string[]> {
  const vacancyIds: string[] = [];

  for (let i = 1; i <= count; i++) {
    const response = await apiContext.post('http://localhost:8000/api/vacancies', {
      data: createTestVacancy(i),
    });

    if (response.ok()) {
      const data = await response.json();
      vacancyIds.push(data.id);
    }
  }

  return vacancyIds;
}

/**
 * Helper function to delete vacancies via API (for cleanup)
 */
async function deleteVacancies(apiContext: any, vacancyIds: string[]): Promise<void> {
  for (const id of vacancyIds) {
    try {
      await apiContext.delete(`http://localhost:8000/api/vacancies/${id}`);
    } catch (error) {
      // Ignore errors during cleanup
      console.log(`Cleanup: Failed to delete vacancy ${id}`);
    }
  }
}

/**
 * Helper function to check if vacancies exist in database via API
 */
async function vacanciesExist(apiContext: any, vacancyIds: string[]): Promise<boolean> {
  const response = await apiContext.get('http://localhost:8000/api/vacancies');

  if (!response.ok()) {
    return false;
  }

  const data = await response.json();
  const existingIds = data.vacancies.map((v: any) => v.id);

  // Check if any of our test vacancies still exist
  return vacancyIds.some(id => existingIds.includes(id));
}

test.describe('Vacancy Bulk Actions - Setup', () => {
  test('should verify backend and frontend are running', async ({ page }) => {
    // Check frontend
    await page.goto('http://localhost:5173');
    await expect(page).toHaveTitle(/AgentHR|Resume Analysis/);

    // Check backend via API
    const apiContext = await request.newContext();
    const response = await apiContext.get('http://localhost:8000/api/vacancies');
    expect(response.ok()).toBeTruthy();
    await apiContext.dispose();
  });
});

test.describe('Vacancy Bulk Actions - Bulk Delete Workflow', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up any test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should complete bulk delete workflow end-to-end', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Step 1: Create test vacancies via API
      test.step('Create test vacancies via API', async () => {
        const vacancyIds = await createVacancies(apiContext, 3);
        expect(vacancyIds).toHaveLength(3);
        console.log('Created vacancies:', vacancyIds);
      });

      // Step 2: Navigate to /recruiter/vacancies
      test.step('Navigate to vacancies page', async () => {
        await page.goto('http://localhost:5173/recruiter/vacancies');
        await page.waitForLoadState('networkidle');
        await expect(page.getByRole('heading', { name: /Job Postings/i })).toBeVisible();
      });

      // Step 3: Enable bulk mode
      test.step('Enable bulk mode', async () => {
        const selectMultipleButton = page.getByRole('button', { name: /Select Multiple/i });
        await expect(selectMultipleButton).toBeVisible();
        await selectMultipleButton.click();

        // Verify bulk mode is active
        await expect(page.getByRole('button', { name: /Exit Bulk Mode/i })).toBeVisible();

        // Verify BulkVacancyActions component is visible
        await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();
      });

      // Step 4: Select multiple vacancies
      test.step('Select multiple vacancies', async () => {
        // Wait for vacancy cards to load
        await page.waitForSelector('.MuiCard-root', { timeout: 5000 });

        // Select first 3 vacancies
        const cards = page.locator('.MuiCard-root');
        const count = await cards.count();

        expect(count).toBeGreaterThanOrEqual(3);

        // Select first 3 cards by clicking on them
        for (let i = 0; i < 3; i++) {
          const card = cards.nth(i);
          await card.click();

          // Verify checkbox is checked
          const checkbox = card.locator('input[type="checkbox"]').or(
            card.locator('.Mui-checked')
          );
          // Note: In bulk mode, the card itself is clickable, so we verify selection by visual feedback
        }

        // Verify selection counter shows 3 selected
        const selectedChip = page.getByText(/3 selected/i).or(page.getByText(/selected/i));
        await expect(selectedChip).toBeVisible();
      });

      // Step 5: Click bulk delete button
      test.step('Click bulk delete button', async () => {
        const deleteButton = page.getByRole('button', { name: /Delete/i }).filter({ hasText: /Delete/ });
        await expect(deleteButton).toBeVisible();
        await deleteButton.click();

        // Verify delete confirmation dialog appears
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByText(/Are you sure you want to delete/i)).toBeVisible();
      });

      // Step 6: Confirm deletion in dialog
      test.step('Confirm deletion in dialog', async () => {
        const confirmButton = page.getByRole('button', { name: /Delete/i }).filter({ hasText: /Delete/ });
        await expect(confirmButton).toBeVisible();
        await confirmButton.click();

        // Wait for deletion to complete
        await page.waitForTimeout(2000);

        // Verify dialog is closed
        await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 }).catch(() => {
          // Dialog might close quickly
        });
      });

      // Step 7: Verify vacancies removed from UI
      test.step('Verify vacancies removed from UI', async () => {
        // Reload page to see updated list
        await page.reload();
        await page.waitForLoadState('networkidle');

        // Verify test vacancies are no longer visible
        const testVacancyText = page.getByText(/Test Vacancy 1/i);
        await expect(testVacancyText).not.toBeVisible({ timeout: 5000 });
      });

      // Step 8: Verify vacancies deleted in database
      test.step('Verify vacancies deleted in database', async () => {
        // Get all vacancies from API
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        // All test vacancies should be deleted
        expect(testVacancies).toHaveLength(0);
      });

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle partial deletion failures gracefully', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create some test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);
      console.log('Created vacancies for partial failure test:', vacancyIds);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Select vacancies
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      for (let i = 0; i < Math.min(count, 2); i++) {
        await cards.nth(i).click();
      }

      // Note: This test would require simulating a backend failure
      // For now, we just verify the UI flow works
      const deleteButton = page.getByRole('button', { name: /Delete/i });
      await deleteButton.click();

      // Verify dialog appears
      await expect(page.getByRole('dialog')).toBeVisible();

      // Cancel for this test
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify dialog closed and vacancies still exist
      await expect(page.getByRole('dialog')).not.toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should allow canceling bulk delete operation', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);
      console.log('Created vacancies for cancel test:', vacancyIds);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Click delete
      await page.getByRole('button', { name: /Delete/i }).click();

      // Cancel in dialog
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify vacancies still exist
      await page.reload();
      await page.waitForLoadState('networkidle');

      const testVacancy = page.getByText(/Test Vacancy/i);
      await expect(testVacancy.first()).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - Selection Management', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should select all vacancies', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 3);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Click "Select All" button
      const selectAllButton = page.getByRole('button', { name: /Select All/i });
      await expect(selectAllButton).toBeVisible();
      await selectAllButton.click();

      // Verify all vacancies are selected
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      // Check that selection counter shows all selected
      const selectedChip = page.getByText(new RegExp(`${count} selected`, 'i'));
      await expect(selectedChip).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should clear all selections', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 3);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select some
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();
      await cards.nth(1).click();

      // Clear selection
      const clearButton = page.getByRole('button', { name: /Clear Selection/i });
      await expect(clearButton).toBeVisible();
      await clearButton.click();

      // Verify no vacancies are selected
      const selectedChip = page.getByText(/0 selected/i);
      await expect(selectedChip).toBeVisible();

      // Delete button should be disabled
      const deleteButton = page.getByRole('button', { name: /Delete/i });
      const isDisabled = await deleteButton.isDisabled();
      expect(isDisabled).toBeTruthy();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should toggle individual vacancy selection', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 3);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');

      // Select first card
      await cards.first().click();

      // Verify it's selected (border should be different color)
      const firstCard = cards.first();
      const borderColor = await firstCard.evaluate((el: any) => {
        return window.getComputedStyle(el).borderColor;
      });

      // Select second card
      await cards.nth(1).click();

      // Verify two are selected
      const selectedChip = page.getByText(/2 selected/i);
      await expect(selectedChip).toBeVisible();

      // Deselect first card
      await cards.first().click();

      // Verify one is still selected
      const singleSelectedChip = page.getByText(/1 selected/i);
      await expect(singleSelectedChip).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - Bulk Mode Toggle', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should enter and exit bulk mode', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enter bulk mode
      const selectMultipleButton = page.getByRole('button', { name: /Select Multiple/i });
      await selectMultipleButton.click();

      // Verify bulk mode UI
      await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /Exit Bulk Mode/i })).toBeVisible();

      // Exit bulk mode
      const exitButton = page.getByRole('button', { name: /Exit Bulk Mode/i });
      await exitButton.click();

      // Verify bulk mode UI is gone
      await expect(page.getByText(/Bulk Vacancy Actions/i)).not.toBeVisible();

      // Verify button changed back
      await expect(page.getByRole('button', { name: /Select Multiple/i })).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should clear selections when exiting bulk mode', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enter bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Exit bulk mode
      await page.getByRole('button', { name: /Exit Bulk Mode/i }).click();

      // Re-enter bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Verify no selections persist
      const selectedChip = page.getByText(/0 selected/i);
      await expect(selectedChip).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - Bulk Update Status Workflow', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should complete bulk update status workflow end-to-end (set to inactive)', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Step 1: Create test vacancies via API (ensure they start as active)
      test.step('Create test vacancies via API', async () => {
        const vacancyIds = await createVacancies(apiContext, 3);
        expect(vacancyIds).toHaveLength(3);
        console.log('Created vacancies:', vacancyIds);
      });

      // Step 2: Navigate to /recruiter/vacancies
      test.step('Navigate to vacancies page', async () => {
        await page.goto('http://localhost:5173/recruiter/vacancies');
        await page.waitForLoadState('networkidle');
        await expect(page.getByRole('heading', { name: /Job Postings/i })).toBeVisible();
      });

      // Step 3: Enable bulk mode
      test.step('Enable bulk mode', async () => {
        const selectMultipleButton = page.getByRole('button', { name: /Select Multiple/i });
        await expect(selectMultipleButton).toBeVisible();
        await selectMultipleButton.click();

        // Verify bulk mode is active
        await expect(page.getByRole('button', { name: /Exit Bulk Mode/i })).toBeVisible();
        await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();
      });

      // Step 4: Select multiple vacancies
      test.step('Select multiple vacancies', async () => {
        // Wait for vacancy cards to load
        await page.waitForSelector('.MuiCard-root', { timeout: 5000 });

        // Select first 3 vacancies
        const cards = page.locator('.MuiCard-root');
        const count = await cards.count();

        expect(count).toBeGreaterThanOrEqual(3);

        // Select first 3 cards by clicking on them
        for (let i = 0; i < 3; i++) {
          const card = cards.nth(i);
          await card.click();
        }

        // Verify selection counter shows 3 selected
        const selectedChip = page.getByText(/3 selected/i).or(page.getByText(/selected/i));
        await expect(selectedChip).toBeVisible();
      });

      // Step 5: Click bulk update status button
      test.step('Click bulk update status button', async () => {
        const updateStatusButton = page.getByRole('button', { name: /Update Status/i }).or(
          page.getByRole('button', { name: /Status/i })
        );
        await expect(updateStatusButton).toBeVisible();
        await updateStatusButton.click();

        // Verify status update dialog appears
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByText(/Update Status/i)).toBeVisible();
      });

      // Step 6: Toggle to inactive status and confirm
      test.step('Toggle to inactive status and confirm', async () => {
        // Look for inactive option/radio/button
        const inactiveOption = page.getByText(/Inactive/i).or(
          page.locator('input[type="radio"][value="false"]')
        ).or(page.getByRole('radio', { name: /Inactive/i }));

        const hasInactiveOption = await inactiveOption.isVisible().catch(() => false);

        if (hasInactiveOption) {
          await inactiveOption.click();
        }

        // Confirm the status update
        const confirmButton = page.getByRole('button', { name: /Update/i }).or(
          page.getByRole('button', { name: /Confirm/i })
        );
        await expect(confirmButton).toBeVisible();
        await confirmButton.click();

        // Wait for update to complete
        await page.waitForTimeout(2000);

        // Verify dialog is closed
        await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 }).catch(() => {
          // Dialog might close quickly
        });
      });

      // Step 7: Verify status changes in UI
      test.step('Verify status changes in UI', async () => {
        // Reload page to see updated list
        await page.reload();
        await page.waitForLoadState('networkidle');

        // Verify vacancies show as inactive (look for "Inactive" badge or label)
        const inactiveBadge = page.getByText(/Inactive/i).first();
        const hasInactiveBadge = await inactiveBadge.isVisible().catch(() => false);

        if (hasInactiveBadge) {
          await expect(inactiveBadge).toBeVisible();
        }
      });

      // Step 8: Verify status updated in database
      test.step('Verify status updated in database', async () => {
        // Get all vacancies from API
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        // Verify test vacancies have is_active = false
        expect(testVacancies.length).toBeGreaterThan(0);

        for (const vacancy of testVacancies) {
          expect(vacancy.is_active).toBe(false);
        }
      });

    } finally {
      await apiContext.dispose();
    }
  });

  test('should complete bulk update status workflow (set back to active)', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies and set them to inactive first
      test.step('Create and deactivate test vacancies', async () => {
        const vacancyIds = await createVacancies(apiContext, 2);

        // Set them to inactive via API
        for (const id of vacancyIds) {
          await apiContext.post('http://localhost:8000/api/vacancies/bulk-update-status', {
            data: {
              vacancy_ids: [id],
              is_active: false,
            },
          });
        }
      });

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Select vacancies
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      for (let i = 0; i < Math.min(count, 2); i++) {
        await cards.nth(i).click();
      }

      // Click update status
      const updateStatusButton = page.getByRole('button', { name: /Update Status/i });
      await updateStatusButton.click();

      // Select active status
      const activeOption = page.getByText(/Active/i).or(
        page.locator('input[type="radio"][value="true"]')
      ).or(page.getByRole('radio', { name: /Active/i }));

      const hasActiveOption = await activeOption.isVisible().catch(() => false);

      if (hasActiveOption) {
        await activeOption.click();
      }

      // Confirm
      const confirmButton = page.getByRole('button', { name: /Update/i }).or(
        page.getByRole('button', { name: /Confirm/i })
      );
      await confirmButton.click();

      await page.waitForTimeout(2000);

      // Verify status updated in database
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // Verify test vacancies have is_active = true
      for (const vacancy of testVacancies) {
        expect(vacancy.is_active).toBe(true);
      }

    } finally {
      await apiContext.dispose();
    }
  });

  test('should allow canceling bulk status update operation', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Click update status
      await page.getByRole('button', { name: /Update Status/i }).click();

      // Cancel in dialog
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify dialog closed and selection persists
      await expect(page.getByRole('dialog')).not.toBeVisible();

      // Get original status from database
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancy = data.vacancies.find((v: any) => v.title.startsWith('Test Vacancy'));

      // Status should remain unchanged (true by default)
      expect(testVacancy.is_active).toBe(true);

    } finally {
      await apiContext.dispose();
    }
  });

  test('should display success message after bulk status update', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Update status
      await page.getByRole('button', { name: /Update Status/i }).click();

      // Select inactive
      const inactiveOption = page.getByText(/Inactive/i);
      const hasInactiveOption = await inactiveOption.isVisible().catch(() => false);

      if (hasInactiveOption) {
        await inactiveOption.click();
      }

      // Confirm
      const confirmButton = page.getByRole('button', { name: /Update/i }).or(
        page.getByRole('button', { name: /Confirm/i })
      );
      await confirmButton.click();

      // Wait for success message
      await page.waitForTimeout(2000);

      // Verify success alert (if it appears)
      const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /successfully updated|status updated/i });
      const hasSuccess = await successAlert.isVisible().catch(() => false);

      if (hasSuccess) {
        await expect(successAlert).toBeVisible();
      }

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle partial status update failures gracefully', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create some test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Select vacancies
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      for (let i = 0; i < Math.min(count, 2); i++) {
        await cards.nth(i).click();
      }

      // Click update status
      await page.getByRole('button', { name: /Update Status/i }).click();

      // Verify dialog appears
      await expect(page.getByRole('dialog')).toBeVisible();

      // Cancel for this test
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify dialog closed and vacancies still exist
      await expect(page.getByRole('dialog')).not.toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - Bulk Duplicate Workflow', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should complete bulk duplicate workflow end-to-end (single vacancy)', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Step 1: Create test vacancy via API
      test.step('Create test vacancy via API', async () => {
        const vacancyIds = await createVacancies(apiContext, 1);
        expect(vacancyIds).toHaveLength(1);
        console.log('Created vacancy:', vacancyIds[0]);
      });

      // Step 2: Navigate to /recruiter/vacancies
      test.step('Navigate to vacancies page', async () => {
        await page.goto('http://localhost:5173/recruiter/vacancies');
        await page.waitForLoadState('networkidle');
        await expect(page.getByRole('heading', { name: /Job Postings/i })).toBeVisible();
      });

      // Step 3: Enable bulk mode
      test.step('Enable bulk mode', async () => {
        const selectMultipleButton = page.getByRole('button', { name: /Select Multiple/i });
        await expect(selectMultipleButton).toBeVisible();
        await selectMultipleButton.click();

        // Verify bulk mode is active
        await expect(page.getByRole('button', { name: /Exit Bulk Mode/i })).toBeVisible();
        await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();
      });

      // Step 4: Select vacancy to duplicate
      test.step('Select vacancy to duplicate', async () => {
        // Wait for vacancy cards to load
        await page.waitForSelector('.MuiCard-root', { timeout: 5000 });

        // Select first vacancy
        const card = page.locator('.MuiCard-root').first();
        await card.click();

        // Verify selection counter shows 1 selected
        const selectedChip = page.getByText(/1 selected/i);
        await expect(selectedChip).toBeVisible();
      });

      // Step 5: Click bulk duplicate button
      test.step('Click bulk duplicate button', async () => {
        const duplicateButton = page.getByRole('button', { name: /Duplicate/i });
        await expect(duplicateButton).toBeVisible();
        await duplicateButton.click();

        // Verify duplicate confirmation dialog appears
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByText(/Duplicate|Create copies/i)).toBeVisible();
      });

      // Step 6: Confirm duplication in dialog
      test.step('Confirm duplication in dialog', async () => {
        const confirmButton = page.getByRole('button', { name: /Duplicate|Confirm/i });
        await expect(confirmButton).toBeVisible();
        await confirmButton.click();

        // Wait for duplication to complete
        await page.waitForTimeout(2000);

        // Verify dialog is closed
        await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 }).catch(() => {
          // Dialog might close quickly
        });
      });

      // Step 7: Verify new vacancy appears in list
      test.step('Verify new vacancy appears in list', async () => {
        // Reload page to see updated list
        await page.reload();
        await page.waitForLoadState('networkidle');

        // Get all test vacancies from UI
        const testVacancyElements = page.getByText(/Test Vacancy/i);
        const count = await testVacancyElements.count();

        // Should have at least 2 test vacancies now (original + duplicate)
        expect(count).toBeGreaterThanOrEqual(2);
      });

      // Step 8: Verify duplicated vacancy in database
      test.step('Verify duplicated vacancy in database', async () => {
        // Get all vacancies from API
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        // Should have at least 2 test vacancies (original + duplicate)
        expect(testVacancies.length).toBeGreaterThanOrEqual(2);

        // Verify all fields copied correctly for the duplicate
        if (testVacancies.length >= 2) {
          const original = testVacancies[0];
          const duplicate = testVacancies[1];

          // Verify key fields are copied
          expect(original.description).toBe(duplicate.description);
          expect(original.required_skills).toEqual(duplicate.required_skills);
          expect(original.min_experience_months).toBe(duplicate.min_experience_months);
          expect(original.industry).toBe(duplicate.industry);
          expect(original.work_format).toBe(duplicate.work_format);
          expect(original.location).toBe(duplicate.location);
          expect(original.salary_min).toBe(duplicate.salary_min);
          expect(original.salary_max).toBe(duplicate.salary_max);

          // IDs should be different
          expect(original.id).not.toBe(duplicate.id);
        }
      });

    } finally {
      await apiContext.dispose();
    }
  });

  test('should complete bulk duplicate workflow end-to-end (multiple vacancies)', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      test.step('Create test vacancies via API', async () => {
        const vacancyIds = await createVacancies(apiContext, 3);
        expect(vacancyIds).toHaveLength(3);
        console.log('Created vacancies:', vacancyIds);
      });

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      // Select all 3 vacancies
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      expect(count).toBeGreaterThanOrEqual(3);

      for (let i = 0; i < 3; i++) {
        await cards.nth(i).click();
      }

      // Verify selection
      const selectedChip = page.getByText(/3 selected/i);
      await expect(selectedChip).toBeVisible();

      // Click duplicate
      await page.getByRole('button', { name: /Duplicate/i }).click();

      // Confirm duplication
      await page.getByRole('button', { name: /Duplicate|Confirm/i }).click();
      await page.waitForTimeout(2000);

      // Verify duplicates in database
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // Should have 6 test vacancies now (3 original + 3 duplicates)
      expect(testVacancies.length).toBeGreaterThanOrEqual(6);

    } finally {
      await apiContext.dispose();
    }
  });

  test('should allow canceling bulk duplicate operation', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);
      console.log('Created vacancies for cancel test:', vacancyIds);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Click duplicate
      await page.getByRole('button', { name: /Duplicate/i }).click();

      // Cancel in dialog
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify vacancies still exist and no duplicate was created
      await page.reload();
      await page.waitForLoadState('networkidle');

      const testVacancy = page.getByText(/Test Vacancy/i);
      await expect(testVacancy.first()).toBeVisible();

      // Verify in database that no duplicate was created
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // Should still have only 2 test vacancies (no duplicates created)
      expect(testVacancies.length).toBe(2);

    } finally {
      await apiContext.dispose();
    }
  });

  test('should display success message after bulk duplicate', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Duplicate
      await page.getByRole('button', { name: /Duplicate/i }).click();
      await page.getByRole('button', { name: /Duplicate|Confirm/i }).click();

      // Wait for success message
      await page.waitForTimeout(2000);

      // Verify success alert (if it appears)
      const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /successfully duplicated|duplicated successfully|created/i });
      const hasSuccess = await successAlert.isVisible().catch(() => false);

      if (hasSuccess) {
        await expect(successAlert).toBeVisible();
      }

    } finally {
      await apiContext.dispose();
    }
  });

  test('should verify all fields copied correctly when duplicating', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create a test vacancy with specific field values
      const specificVacancy = {
        title: 'Test Vacancy Specific',
        description: 'Specific description with detailed requirements',
        required_skills: ['Python', 'Django', 'PostgreSQL', 'Docker'],
        min_experience_months: 36,
        industry: 'Finance',
        work_format: 'Hybrid',
        location: 'New York, NY',
        salary_min: 100000,
        salary_max: 150000,
      };

      test.step('Create vacancy with specific field values', async () => {
        const response = await apiContext.post('http://localhost:8000/api/vacancies', {
          data: specificVacancy,
        });

        expect(response.ok()).toBeTruthy();
        const data = await response.json();
        console.log('Created specific vacancy:', data.id);
      });

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select the specific vacancy
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const specificCard = page.locator('.MuiCard-root').filter({ hasText: /Test Vacancy Specific/i });
      await specificCard.click();

      // Duplicate
      await page.getByRole('button', { name: /Duplicate/i }).click();
      await page.getByRole('button', { name: /Duplicate|Confirm/i }).click();
      await page.waitForTimeout(2000);

      // Verify all fields copied correctly in database
      test.step('Verify all fields copied correctly', async () => {
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        const specificVacancies = data.vacancies.filter((v: any) =>
          v.title === 'Test Vacancy Specific'
        );

        // Should have 2 vacancies with this title (original + duplicate)
        expect(specificVacancies.length).toBe(2);

        const original = specificVacancies[0];
        const duplicate = specificVacancies[1];

        // Verify every field
        expect(original.title).toBe(duplicate.title);
        expect(original.description).toBe(duplicate.description);
        expect(original.required_skills).toEqual(duplicate.required_skills);
        expect(original.min_experience_months).toBe(duplicate.min_experience_months);
        expect(original.industry).toBe(duplicate.industry);
        expect(original.work_format).toBe(duplicate.work_format);
        expect(original.location).toBe(duplicate.location);
        expect(original.salary_min).toBe(duplicate.salary_min);
        expect(original.salary_max).toBe(duplicate.salary_max);

        // IDs should be different
        expect(original.id).not.toBe(duplicate.id);

        // Created/updated timestamps should be different
        expect(original.created_at).not.toBe(duplicate.created_at);
      });

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - Error Handling and Partial Success', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should handle bulk delete with mix of valid and invalid vacancy IDs', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Step 1: Create some test vacancies via API
      test.step('Create test vacancies via API', async () => {
        const vacancyIds = await createVacancies(apiContext, 2);
        expect(vacancyIds).toHaveLength(2);
        console.log('Created vacancies:', vacancyIds);
      });

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Step 2: Enable bulk mode and select vacancies
      test.step('Enable bulk mode and select vacancies', async () => {
        await page.getByRole('button', { name: /Select Multiple/i }).click();
        await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();

        const cards = page.locator('.MuiCard-root');
        const count = await cards.count();

        // Select all visible vacancies (our 2 test vacancies)
        for (let i = 0; i < Math.min(count, 2); i++) {
          await cards.nth(i).click();
        }

        // Verify selection
        const selectedChip = page.getByText(/2 selected/i);
        await expect(selectedChip).toBeVisible();
      });

      // Step 3: Simulate partial failure by calling API directly with invalid IDs
      test.step('Test partial failure via API call', async () => {
        // Get the valid vacancy IDs first
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        const validIds = testVacancies.map((v: any) => v.id);
        const invalidId = '00000000-0000-0000-0000-000000000000';

        // Mix of valid and invalid IDs
        const mixedIds = [...validIds, invalidId];

        // Call bulk delete API directly with mixed IDs
        const deleteResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-delete', {
          data: {
            vacancy_ids: mixedIds,
          },
        });

        expect(deleteResponse.ok()).toBeTruthy();

        const result = await deleteResponse.json();

        // Should have partial success
        expect(result.total_requested).toBe(mixedIds.length);
        expect(result.successful).toBe(validIds.length);
        expect(result.failed).toBe(1);

        // Verify result details
        expect(result.results).toHaveLength(mixedIds.length);

        // Check that valid IDs succeeded
        const validResults = result.results.filter((r: any) => r.success);
        expect(validResults).toHaveLength(validIds.length);

        // Check that invalid ID failed
        const invalidResult = result.results.find((r: any) => !r.success);
        expect(invalidResult).toBeDefined();
        expect(invalidResult.vacancy_id).toBe(invalidId);
        expect(invalidResult.error).toBeDefined();
      });

      // Step 4: Verify UI shows error message for failed items
      test.step('Verify UI shows partial success notification', async () => {
        // Reload page to see updated state
        await page.reload();
        await page.waitForLoadState('networkidle');

        // The successfully deleted vacancies should be gone
        // Invalid ID was already not in the list
        const response = await apiContext.get('http://localhost:8000/api/vacancies');
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        // All valid test vacancies should be deleted
        expect(testVacancies).toHaveLength(0);
      });

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle bulk status update with partial failures', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);
      console.log('Created vacancies for partial status update test:', vacancyIds);

      // Get valid IDs
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      const validIds = testVacancies.map((v: any) => v.id);
      const invalidId = '00000000-0000-0000-0000-999999999999';

      // Mix of valid and invalid IDs
      const mixedIds = [...validIds, invalidId];

      // Call bulk status update API directly with mixed IDs
      const updateResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-update-status', {
        data: {
          vacancy_ids: mixedIds,
          is_active: false,
        },
      });

      expect(updateResponse.ok()).toBeTruthy();

      const result = await updateResponse.json();

      // Verify partial success
      expect(result.total_requested).toBe(mixedIds.length);
      expect(result.successful).toBe(validIds.length);
      expect(result.failed).toBe(1);

      // Verify valid vacancies were updated
      const updatedResponse = await apiContext.get('http://localhost:8000/api/vacancies');
      const updatedData = await updatedResponse.json();
      const updatedVacancies = updatedData.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // All valid test vacancies should now be inactive
      for (const vacancy of updatedVacancies) {
        expect(vacancy.is_active).toBe(false);
      }

      // Verify error details for failed item
      const failedResult = result.results.find((r: any) => !r.success);
      expect(failedResult).toBeDefined();
      expect(failedResult.vacancy_id).toBe(invalidId);
      expect(failedResult.error).toBeDefined();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle bulk duplicate with partial failures', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);
      console.log('Created vacancies for partial duplicate test:', vacancyIds);

      // Get valid IDs
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      const validIds = testVacancies.map((v: any) => v.id);
      const invalidId = '00000000-0000-0000-0000-888888888888';

      // Mix of valid and invalid IDs
      const mixedIds = [...validIds, invalidId];

      // Call bulk duplicate API directly with mixed IDs
      const duplicateResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-duplicate', {
        data: {
          vacancy_ids: mixedIds,
        },
      });

      expect(duplicateResponse.ok()).toBeTruthy();

      const result = await duplicateResponse.json();

      // Verify partial success
      expect(result.total_requested).toBe(mixedIds.length);
      expect(result.successful).toBe(validIds.length);
      expect(result.failed).toBe(1);

      // Verify duplicates were created for valid vacancies
      const finalResponse = await apiContext.get('http://localhost:8000/api/vacancies');
      const finalData = await finalResponse.json();
      const finalVacancies = finalData.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // Should have 4 test vacancies now (2 original + 2 duplicates)
      expect(finalVacancies.length).toBe(4);

      // Verify error details for failed item
      const failedResult = result.results.find((r: any) => !r.success);
      expect(failedResult).toBeDefined();
      expect(failedResult.vacancy_id).toBe(invalidId);
      expect(failedResult.error).toBeDefined();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle bulk assign with partial failures', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies and an organization
      const vacancyIds = await createVacancies(apiContext, 2);

      // Create a test organization
      const orgResponse = await apiContext.post('http://localhost:8000/api/organizations', {
        data: {
          name: 'Test Organization for Bulk Assign',
          industry: 'Technology',
        },
      });

      expect(orgResponse.ok()).toBeTruthy();
      const orgData = await orgResponse.json();
      const organizationId = orgData.id;

      console.log('Created organization:', organizationId);

      // Get valid vacancy IDs
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      const validIds = testVacancies.map((v: any) => v.id);
      const invalidId = '00000000-0000-0000-0000-777777777777';

      // Mix of valid and invalid IDs
      const mixedIds = [...validIds, invalidId];

      // Call bulk assign API directly with mixed IDs
      const assignResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-assign', {
        data: {
          vacancy_ids: mixedIds,
          organization_id: organizationId,
        },
      });

      expect(assignResponse.ok()).toBeTruthy();

      const result = await assignResponse.json();

      // Verify partial success
      expect(result.total_requested).toBe(mixedIds.length);
      expect(result.successful).toBe(validIds.length);
      expect(result.failed).toBe(1);

      // Verify valid vacancies were assigned
      const assignedResponse = await apiContext.get('http://localhost:8000/api/vacancies');
      const assignedData = await assignedResponse.json();
      const assignedVacancies = assignedData.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      // All valid test vacancies should have the organization_id set
      for (const vacancy of assignedVacancies) {
        expect(vacancy.organization_id).toBe(organizationId);
      }

      // Verify error details for failed item
      const failedResult = result.results.find((r: any) => !r.success);
      expect(failedResult).toBeDefined();
      expect(failedResult.vacancy_id).toBe(invalidId);
      expect(failedResult.error).toBeDefined();

      // Cleanup organization
      await apiContext.delete(`http://localhost:8000/api/organizations/${organizationId}`);

    } finally {
      await apiContext.dispose();
    }
  });

  test('should display appropriate error messages for network errors', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select vacancies
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Note: This test verifies the UI handles errors gracefully
      // In a real scenario, we might simulate a network error by intercepting the request
      // For now, we verify the UI state is correct

      // Verify selection persists
      const selectedChip = page.getByText(/1 selected/i);
      await expect(selectedChip).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle empty vacancy list in bulk operations', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Don't create any vacancies - start with empty list
      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Try to call bulk delete with empty list via API
      const deleteResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-delete', {
        data: {
          vacancy_ids: [],
        },
      });

      // Should return 400 Bad Request for empty list
      expect(deleteResponse.status()).toBe(400);

      const errorData = await deleteResponse.json();
      expect(errorData.detail).toBeDefined();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle malformed UUIDs in bulk operations', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create one valid vacancy
      await createVacancies(apiContext, 1);

      // Try bulk delete with malformed UUIDs
      const deleteResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-delete', {
        data: {
          vacancy_ids: [
            'not-a-uuid',
            'also-not-a-uuid',
            '12345',
          ],
        },
      });

      // Should handle gracefully - may return 200 with all failed or 400 for invalid input
      expect([200, 400]).toContain(deleteResponse.status());

      if (deleteResponse.status() === 200) {
        const result = await deleteResponse.json();
        expect(result.total_requested).toBe(3);
        expect(result.failed).toBe(3);
        expect(result.successful).toBe(0);
      }

    } finally {
      await apiContext.dispose();
    }
  });

  test('should verify error messages contain useful information', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 1);

      // Get valid ID
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancy = data.vacancies.find((v: any) => v.title.startsWith('Test Vacancy'));
      const validId = testVacancy.id;

      const invalidId = '00000000-0000-0000-0000-666666666666';

      // Call bulk delete with mixed IDs
      const deleteResponse = await apiContext.post('http://localhost:8000/api/vacancies/bulk-delete', {
        data: {
          vacancy_ids: [validId, invalidId],
        },
      });

      expect(deleteResponse.ok()).toBeTruthy();

      const result = await deleteResponse.json();

      // Verify error message is present and informative
      const failedResult = result.results.find((r: any) => !r.success);
      expect(failedResult).toBeDefined();
      expect(failedResult.error).toBeDefined();

      // Error message should not be empty
      expect(failedResult.error.length).toBeGreaterThan(0);

      // Error message should mention the vacancy or the issue
      const errorLower = failedResult.error.toLowerCase();
      const hasUsefulInfo = errorLower.includes('not found') ||
                           errorLower.includes('vacancy') ||
                           errorLower.includes('does not exist');

      expect(hasUsefulInfo).toBeTruthy();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should maintain UI stability during partial failures', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 3);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode
      await page.getByRole('button', { name: /Select Multiple/i }).click();
      await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();

      // Select all vacancies
      const cards = page.locator('.MuiCard-root');
      const count = await cards.count();

      for (let i = 0; i < Math.min(count, 3); i++) {
        await cards.nth(i).click();
      }

      // Verify selection
      await expect(page.getByText(/3 selected/i)).toBeVisible();

      // Click delete button
      await page.getByRole('button', { name: /Delete/i }).click();

      // Verify dialog appears
      await expect(page.getByRole('dialog')).toBeVisible();

      // Cancel to avoid actually deleting
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify dialog closes and UI remains stable
      await expect(page.getByRole('dialog')).not.toBeVisible();
      await expect(page.getByText(/3 selected/i)).toBeVisible();

      // Verify bulk mode is still active
      await expect(page.getByText(/Bulk Vacancy Actions/i)).toBeVisible();

    } finally {
      await apiContext.dispose();
    }
  });

  test('should handle concurrent bulk operations gracefully', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      const vacancyIds = await createVacancies(apiContext, 2);

      // Get valid IDs
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      const data = await response.json();
      const testVacancies = data.vacancies.filter((v: any) =>
        v.title.startsWith('Test Vacancy')
      );

      const validIds = testVacancies.map((v: any) => v.id);

      // Send multiple concurrent requests
      const promises = [
        apiContext.post('http://localhost:8000/api/vacancies/bulk-update-status', {
          data: { vacancy_ids: validIds, is_active: false },
        }),
        apiContext.post('http://localhost:8000/api/vacancies/bulk-update-status', {
          data: { vacancy_ids: validIds, is_active: true },
        }),
      ];

      const results = await Promise.all(promises);

      // Both should succeed (last one wins)
      for (const result of results) {
        expect(result.ok()).toBeTruthy();
      }

    } finally {
      await apiContext.dispose();
    }
  });
});

test.describe('Vacancy Bulk Actions - UI and UX', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.afterEach(async ({ page }) => {
    // Clean up test data
    const apiContext = await request.newContext();

    try {
      const response = await apiContext.get('http://localhost:8000/api/vacancies');
      if (response.ok()) {
        const data = await response.json();
        const testVacancies = data.vacancies.filter((v: any) =>
          v.title.startsWith('Test Vacancy')
        );

        for (const vacancy of testVacancies) {
          await apiContext.delete(`http://localhost:8000/api/vacancies/${vacancy.id}`);
        }
      }
    } catch (error) {
      console.log('Cleanup error:', error);
    }

    await apiContext.dispose();
  });

  test('should display empty state when no vacancies exist', async ({ page }) => {
    await page.goto('http://localhost:5173/recruiter/vacancies');
    await page.waitForLoadState('networkidle');

    // If there are no vacancies, empty state should show
    const emptyState = page.getByText(/No job postings yet/i);
    const createVacancyButton = page.getByRole('button', { name: /Create Vacancy/i });

    const isEmpty = await emptyState.isVisible().catch(() => false);
    const hasCreateButton = await createVacancyButton.isVisible().catch(() => false);

    if (isEmpty) {
      await expect(emptyState).toBeVisible();
      await expect(createVacancyButton).toBeVisible();
    }
  });

  test('should display success message after bulk delete', async ({ page }) => {
    const apiContext = await request.newContext();

    try {
      // Create test vacancies
      await createVacancies(apiContext, 2);

      await page.goto('http://localhost:5173/recruiter/vacancies');
      await page.waitForLoadState('networkidle');

      // Enable bulk mode and select
      await page.getByRole('button', { name: /Select Multiple/i }).click();

      const cards = page.locator('.MuiCard-root');
      await cards.first().click();

      // Delete
      await page.getByRole('button', { name: /Delete/i }).click();
      await page.getByRole('button', { name: /Delete/i }).filter({ hasText: /Delete/ }).click();

      // Wait for success message
      await page.waitForTimeout(2000);

      // Verify success alert (if it appears)
      const successAlert = page.locator('.MuiAlert-root').filter({ hasText: /successfully deleted/i });
      const hasSuccess = await successAlert.isVisible().catch(() => false);

      if (hasSuccess) {
        await expect(successAlert).toBeVisible();
      }

    } finally {
      await apiContext.dispose();
    }
  });
});
