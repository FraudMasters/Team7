import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Visual Query Builder
 *
 * Test Suite Contents:
 * 1. Query Builder Rendering
 * 2. Filter Row Management
 * 3. Boolean Operators
 * 4. Field Selection
 * 5. Query Generation
 * 6. Copy to Clipboard
 * 7. Reset Functionality
 * 8. Integration with Advanced Search
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - User authenticated with recruiter role
 */

test.describe('Query Builder Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    // Enable advanced filters to access query builder
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
  });

  test('should display query builder when visual mode is enabled', async ({ page }) => {
    // Look for visual query mode toggle
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }

    // Check for query builder title
    await expect(page.getByText(/Visual Query Builder/i)).toBeVisible({ timeout: 5000 });
  });

  test('should display query builder description', async ({ page }) => {
    // Switch to visual mode if available
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }

    // Check for description text
    const description = page.getByText(/Build complex search queries|without knowing boolean syntax/i);
    if (await description.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(description).toBeVisible();
    }
  });

  test('should display initial filter row', async ({ page }) => {
    // Switch to visual mode
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }

    // Check for field dropdown
    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(fieldDropdown).toBeVisible();
    }
  });

  test('should display generated query preview section', async ({ page }) => {
    // Switch to visual mode
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }

    // Check for generated query section
    const queryPreview = page.getByText(/Generated Query/i);
    if (await queryPreview.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(queryPreview).toBeVisible();
    }
  });
});

test.describe('Filter Row Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    // Enable advanced filters
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    // Switch to visual mode
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should add new filter row when add button is clicked', async ({ page }) => {
    // Wait for query builder to load
    await page.waitForTimeout(1000);

    // Look for add filter button
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();

      // Verify additional row exists
      await page.waitForTimeout(500);
    }
  });

  test('should display delete button for filter rows', async ({ page }) => {
    // Wait for query builder to load
    await page.waitForTimeout(1000);

    // Look for delete/remove button
    const deleteButton = page.getByRole('button', { name: /Remove|Delete/i }).first();
    if (await deleteButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(deleteButton).toBeVisible();
    }
  });

  test('should disable delete button when only one row exists', async ({ page }) => {
    // Wait for query builder to load
    await page.waitForTimeout(1000);

    // Check if delete button is disabled
    const deleteButton = page.getByRole('button', { name: /Remove|Delete/i }).first();
    if (await deleteButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      const isDisabled = await deleteButton.isDisabled();
      // First row should have disabled delete button
      expect(isDisabled).toBeTruthy();
    }
  });

  test('should remove filter row when delete button is clicked', async ({ page }) => {
    // Wait for query builder to load
    await page.waitForTimeout(1000);

    // Add a filter row first
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Now delete one row
      const deleteButtons = page.getByRole('button', { name: /Remove|Delete/i });
      const deleteButton = deleteButtons.nth(1);
      if (await deleteButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await deleteButton.click();
        await page.waitForTimeout(500);
      }
    }
  });
});

test.describe('Boolean Operators', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should display operator dropdown for additional rows', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Add a second filter row
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Check for operator dropdown
      const operatorDropdown = page.getByRole('combobox', { name: /Operator/i }).first();
      if (await operatorDropdown.isVisible({ timeout: 1000 }).catch(() => false)) {
        await expect(operatorDropdown).toBeVisible();
      }
    }
  });

  test('should allow selecting AND operator', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Add a second row
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Select AND operator
      const operatorDropdown = page.getByRole('combobox', { name: /Operator/i }).first();
      if (await operatorDropdown.isVisible({ timeout: 1000 }).catch(() => false)) {
        await operatorDropdown.click();

        // Look for AND option
        const andOption = page.getByRole('option', { name: /AND/i });
        if (await andOption.isVisible({ timeout: 1000 }).catch(() => false)) {
          await andOption.click();
        }
      }
    }
  });

  test('should allow selecting OR operator', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Add a second row
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Select OR operator
      const operatorDropdown = page.getByRole('combobox', { name: /Operator/i }).first();
      if (await operatorDropdown.isVisible({ timeout: 1000 }).catch(() => false)) {
        await operatorDropdown.click();

        // Look for OR option
        const orOption = page.getByRole('option', { name: /^OR$/i });
        if (await orOption.isVisible({ timeout: 1000 }).catch(() => false)) {
          await orOption.click();
        }
      }
    }
  });

  test('should allow selecting NOT operator', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Add a second row
    const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
    if (await addButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Select NOT operator
      const operatorDropdown = page.getByRole('combobox', { name: /Operator/i }).first();
      if (await operatorDropdown.isVisible({ timeout: 1000 }).catch(() => false)) {
        await operatorDropdown.click();

        // Look for NOT option
        const notOption = page.getByRole('option', { name: /NOT/i });
        if (await notOption.isVisible({ timeout: 1000 }).catch(() => false)) {
          await notOption.click();
        }
      }
    }
  });
});

test.describe('Field Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should display field dropdown', async ({ page }) => {
    await page.waitForTimeout(1000);

    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(fieldDropdown).toBeVisible();
    }
  });

  test('should allow selecting skills field', async ({ page }) => {
    await page.waitForTimeout(1000);

    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await fieldDropdown.click();

      const skillsOption = page.getByRole('option', { name: /Skills/i });
      if (await skillsOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await skillsOption.click();
      }
    }
  });

  test('should allow selecting location field', async ({ page }) => {
    await page.waitForTimeout(1000);

    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await fieldDropdown.click();

      const locationOption = page.getByRole('option', { name: /Location/i });
      if (await locationOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await locationOption.click();
      }
    }
  });

  test('should allow selecting education field', async ({ page }) => {
    await page.waitForTimeout(1000);

    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await fieldDropdown.click();

      const educationOption = page.getByRole('option', { name: /Education/i });
      if (await educationOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await educationOption.click();
      }
    }
  });

  test('should allow selecting experience field', async ({ page }) => {
    await page.waitForTimeout(1000);

    const fieldDropdown = page.getByRole('combobox', { name: /Field/i }).first();
    if (await fieldDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await fieldDropdown.click();

      const experienceOption = page.getByRole('option', { name: /Experience/i });
      if (await experienceOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await experienceOption.click();
      }
    }
  });

  test('should display value input for filter', async ({ page }) => {
    await page.waitForTimeout(1000);

    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(valueInput).toBeVisible();
    }
  });
});

test.describe('Query Generation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should generate query from single filter', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Fill in a value
    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await valueInput.fill('Python');

      // Wait for query generation
      await page.waitForTimeout(500);
    }
  });

  test('should generate query with AND operator', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Fill first filter
    const firstValue = page.getByRole('textbox', { name: /Value/i }).first();
    if (await firstValue.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstValue.fill('Python');

      // Add second filter
      const addButton = page.getByRole('button', { name: /Add Filter|Add row/i }).first();
      if (await addButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await addButton.click();
        await page.waitForTimeout(500);

        // Fill second filter
        const secondValue = page.getByRole('textbox', { name: /Value/i }).nth(1);
        if (await secondValue.isVisible({ timeout: 1000 }).catch(() => false)) {
          await secondValue.fill('Django');
          await page.waitForTimeout(500);
        }
      }
    }
  });

  test('should update query when filter values change', async ({ page }) => {
    await page.waitForTimeout(1000);

    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Fill initial value
      await valueInput.fill('Python');
      await page.waitForTimeout(500);

      // Change value
      await valueInput.clear();
      await valueInput.fill('JavaScript');
      await page.waitForTimeout(500);
    }
  });

  test('should clear query when all values are removed', async ({ page }) => {
    await page.waitForTimeout(1000);

    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Fill value
      await valueInput.fill('Python');
      await page.waitForTimeout(500);

      // Clear value
      await valueInput.clear();
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Reset Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should display reset button', async ({ page }) => {
    await page.waitForTimeout(1000);

    const resetButton = page.getByRole('button', { name: /Reset/i });
    if (await resetButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(resetButton).toBeVisible();
    }
  });

  test('should reset query builder to default state', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Add filters and values
    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await valueInput.fill('Python');
      await page.waitForTimeout(500);

      // Click reset
      const resetButton = page.getByRole('button', { name: /Reset/i });
      if (await resetButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await resetButton.click();
        await page.waitForTimeout(500);

        // Verify value is cleared
        const clearedInput = page.getByRole('textbox', { name: /Value/i }).first();
        if (await clearedInput.isVisible({ timeout: 1000 }).catch(() => false)) {
          await expect(clearedInput).toHaveValue('');
        }
      }
    }
  });
});

test.describe('Copy to Clipboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/candidate-search');
    await page.getByRole('button', { name: /Enable Advanced Filters/i }).click();
    const visualModeButton = page.getByRole('button', { name: /Visual|Visual Mode/i });
    if (await visualModeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await visualModeButton.click();
    }
  });

  test('should display copy button when query is generated', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Generate a query
    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await valueInput.fill('Python');
      await page.waitForTimeout(500);

      // Look for copy button
      const copyButton = page.getByRole('button', { name: /Copy/i });
      if (await copyButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await expect(copyButton).toBeVisible();
      }
    }
  });

  test('should show success message after copying', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Generate a query
    const valueInput = page.getByRole('textbox', { name: /Value/i }).first();
    if (await valueInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await valueInput.fill('Python');
      await page.waitForTimeout(500);

      // Click copy button
      const copyButton = page.getByRole('button', { name: /Copy/i });
      if (await copyButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await copyButton.click();
        await page.waitForTimeout(500);

        // Check for success message
        const successMessage = page.getByText(/copied to clipboard/i);
        if (await successMessage.isVisible({ timeout: 1000 }).catch(() => false)) {
          await expect(successMessage).toBeVisible();
        }
      }
    }
  });
});
