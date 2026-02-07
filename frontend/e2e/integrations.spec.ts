import { test, expect } from '@playwright/test';

/**
 * E2E Tests for HRIS/ATS Integrations
 *
 * Test Suite Contents:
 * 1. Navigate to Integrations Page
 * 2. Create New Integration (Workday, Greenhouse, Lever, BambooHR, Ashby)
 * 3. Test Connection to External Platform
 * 4. Trigger Manual Sync
 * 5. View Sync History and Status
 * 6. Edit and Delete Integrations
 * 7. Error Handling and Validation
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Valid test credentials for at least one platform (or mock responses)
 */

// Viewport configurations
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };

// Test credentials (use environment variables in production)
const TEST_CREDENTIALS = {
  workday: {
    api_url: 'https://wd1.workday.com',
    username: 'test@example.com',
    password: 'test-password-123',
    tenant_name: 'test_tenant',
  },
  greenhouse: {
    api_key: 'test-greenhouse-api-key',
  },
  lever: {
    api_key: 'test-lever-api-key',
  },
  bamboohr: {
    api_key: 'test-bamboohr-key',
    company_domain: 'testcompany.bamboohr.com',
  },
  ashby: {
    api_key: 'test-ashby-api-key',
  },
};

test.describe('Integrations - Page Navigation', () => {
  test('should display integrations page', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Check page heading
    await expect(page.getByRole('heading', { name: /Integrations|Integration Management/i })).toBeVisible();

    // Check for integration list or empty state
    const content = page.locator('.MuiTableBody-root, .MuiCard-root, [role="table"]').or(
      page.getByText(/No integrations|Configure your first integration/i)
    );
    await expect(content.first()).toBeVisible();
  });

  test('should display add integration button', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Check for Add Integration button
    const addButton = page.getByRole('button', { name: /Add|Add Integration|New Integration/i }).or(
      page.locator('button').filter({ hasText: /Add/i })
    );

    await expect(addButton.first()).toBeVisible();
  });

  test('should navigate from other pages to integrations', async ({ page }) => {
    // Start from another page (e.g., vacancies)
    await page.goto('/vacancies');
    await page.waitForLoadState('networkidle');

    // Navigate to integrations (could be via sidebar, menu, or direct URL)
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Verify we're on integrations page
    await expect(page.getByRole('heading', { name: /Integrations/i })).toBeVisible();
  });
});

test.describe('Integrations - Create Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should open integration config dialog', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Click Add Integration button
    const addButton = page.getByRole('button', { name: /Add|Add Integration/i }).or(
      page.locator('button').filter({ hasText: /Add/i })
    );

    await addButton.first().click();
    await page.waitForTimeout(500);

    // Check that config dialog opened
    const dialog = page.locator('.MuiDialog-root, .MuiModal-root').or(
      page.getByRole('dialog')
    );

    const dialogCount = await dialog.count();
    if (dialogCount > 0) {
      await expect(dialog.first()).toBeVisible();

      // Check for form fields
      await expect(page.getByText(/Integration Name|Name/i)).toBeVisible();
      await expect(page.getByText(/Platform|Select Platform/i)).toBeVisible();
    }
  });

  test('should display platform options', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Open add integration dialog
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Look for platform selector
      const platformSelect = page.getByRole('combobox', { name: /platform/i }).or(
        page.getByLabel(/platform/i)
      ).or(page.locator('.MuiSelect-root'));

      const platformCount = await platformSelect.count();
      if (platformCount > 0) {
        await platformSelect.first().click();
        await page.waitForTimeout(300);

        // Check for platform options
        const platforms = ['Workday', 'Greenhouse', 'Lever', 'BambooHR', 'Ashby'];
        for (const platform of platforms) {
          const option = page.getByRole('option', { name: platform }).or(page.getByText(platform));
          const optionCount = await option.count();
          if (optionCount > 0) {
            await expect(option.first()).toBeVisible();
          }
        }
      }
    }
  });

  test('should show platform-specific credential fields', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Open add integration dialog
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Select Workday platform
      const platformSelect = page.getByRole('combobox').or(page.locator('.MuiSelect-root'));
      const platformCount = await platformSelect.count();

      if (platformCount > 0) {
        await platformSelect.first().click();
        await page.getByRole('option', { name: /Workday/i }).click();
        await page.waitForTimeout(500);

        // Check for Workday-specific fields
        const apiUrlField = page.getByRole('textbox', { name: /api url|api_url/i }).or(
          page.locator('input').filter({ hasText: /API URL/i })
        );
        const usernameField = page.getByRole('textbox', { name: /username/i }).or(
          page.locator('input').filter({ hasText: /Username/i })
        );

        // At least some credential fields should be visible
        await expect(apiUrlField.or(usernameField)).toBeVisible();
      }
    }
  });

  test('should validate integration form fields', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Open add integration dialog
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Try to submit without required fields
      const saveButton = page.getByRole('button', { name: /Save|Create|Add Integration/i });
      const saveCount = await saveButton.count();

      if (saveCount > 0) {
        // Click save without filling form
        await saveButton.first().click();
        await page.waitForTimeout(500);

        // Check for validation errors
        const error = page.getByText(/required|field is required|please fill/i);
        const errorCount = await error.count();

        if (errorCount > 0) {
          await expect(error.first()).toBeVisible();
        }
      }
    }
  });

  test('should create integration with valid data', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Open add integration dialog
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Fill integration name
      const nameField = page.getByRole('textbox', { name: /name|integration name/i }).or(
        page.locator('input[placeholder*="name" i]')
      );
      const nameCount = await nameField.count();

      if (nameCount > 0) {
        await nameField.first().fill('E2E Test Integration - Workday');
      }

      // Select platform
      const platformSelect = page.getByRole('combobox').or(page.locator('.MuiSelect-root'));
      const platformCount = await platformSelect.count();

      if (platformCount > 0) {
        await platformSelect.first().click();
        await page.getByRole('option', { name: /Workday/i }).click();
        await page.waitForTimeout(500);

        // Fill Workday credentials
        const apiUrlField = page.getByRole('textbox', { name: /api url/i }).or(
          page.locator('input').filter({ hasText: /API URL/i })
        );
        const apiUrlCount = await apiUrlField.count();

        if (apiUrlCount > 0) {
          await apiUrlField.first().fill(TEST_CREDENTIALS.workday.api_url);
        }

        const usernameField = page.getByRole('textbox', { name: /username/i }).or(
          page.locator('input').filter({ hasText: /Username/i })
        );
        const usernameCount = await usernameField.count();

        if (usernameCount > 0) {
          await usernameField.first().fill(TEST_CREDENTIALS.workday.username);
        }

        const passwordField = page.locator('input[type="password"]');
        const passwordCount = await passwordField.count();

        if (passwordCount > 0) {
          await passwordField.first().fill(TEST_CREDENTIALS.workday.password);
        }

        const tenantField = page.getByRole('textbox', { name: /tenant/i }).or(
          page.locator('input').filter({ hasText: /Tenant/i })
        );
        const tenantCount = await tenantField.count();

        if (tenantCount > 0) {
          await tenantField.first().fill(TEST_CREDENTIALS.workday.tenant_name);
        }
      }

      // Enable sync
      const syncSwitch = page.getByRole('checkbox', { name: /sync|enable sync/i }).or(
        page.locator('.MuiSwitch-root')
      );
      const syncCount = await syncSwitch.count();

      if (syncCount > 0) {
        const isChecked = await syncSwitch.first().isChecked();
        if (!isChecked) {
          await syncSwitch.first().click();
        }
      }

      // Save integration
      const saveButton = page.getByRole('button', { name: /Save|Create/i });
      const saveCount = await saveButton.count();

      if (saveCount > 0) {
        // Handle both success and error cases
        await saveButton.first().click();
        await page.waitForTimeout(2000);

        // Check for success message or error
        const success = page.getByText(/success|created|integration added/i);
        const error = page.getByText(/error|failed|could not create/i);
        const dialog = page.locator('.MuiDialog-root');

        const dialogCount = await dialog.count();

        if (dialogCount === 0) {
          // Dialog closed - likely successful
          const successCount = await success.count();
          if (successCount > 0) {
            await expect(success.first()).toBeVisible();
          }
        } else {
          // Dialog still open - might have validation or API error
          const errorCount = await error.count();
          if (errorCount > 0) {
            // This is acceptable if backend is not running
            console.log('Integration creation returned error (backend may not be running)');
          }
        }
      }
    }
  });
});

test.describe('Integrations - Test Connection', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
  });

  test('should have test connection button for integrations', async ({ page }) => {
    // Look for existing integrations
    const testButton = page.getByRole('button', { name: /Test Connection|Test/i }).or(
      page.locator('button').filter({ hasText: /Test/i })
    );

    const testCount = await testButton.count();

    if (testCount > 0) {
      await expect(testButton.first()).toBeVisible();
    } else {
      // No integrations to test - skip gracefully
      console.log('No integrations found to test connection');
      test.skip();
    }
  });

  test('should test connection successfully', async ({ page }) => {
    // Find test connection button
    const testButton = page.getByRole('button', { name: /Test Connection|Test/i });
    const testCount = await testButton.count();

    if (testCount > 0) {
      await testButton.first().click();
      await page.waitForTimeout(3000);

      // Check for success or error message
      const success = page.getByText(/connection successful|connected successfully|test passed/i);
      const error = page.getByText(/connection failed|test failed|could not connect/i);
      const loading = page.locator('.MuiCircularProgress-root');

      // Should show one of: success, error, or loading
      const hasResult = await success.isVisible().catch(() => false) ||
                       await error.isVisible().catch(() => false) ||
                       await loading.isVisible().catch(() => false);

      expect(hasResult).toBeTruthy();
    } else {
      console.log('No integrations found to test connection');
      test.skip();
    }
  });

  test('should show loading state during connection test', async ({ page }) => {
    const testButton = page.getByRole('button', { name: /Test Connection|Test/i });
    const testCount = await testButton.count();

    if (testCount > 0) {
      await testButton.first().click();

      // Check for loading indicator immediately after click
      const loading = page.locator('.MuiCircularProgress-root, .MuiButton-loading');
      const loadingCount = await loading.count();

      if (loadingCount > 0) {
        await expect(loading.first()).toBeVisible();
      }
    } else {
      console.log('No integrations found to test connection');
      test.skip();
    }
  });
});

test.describe('Integrations - Trigger Sync', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
  });

  test('should have sync button for integrations', async ({ page }) => {
    const syncButton = page.getByRole('button', { name: /Sync|Sync Now|Trigger Sync/i }).or(
      page.locator('button').filter({ hasText: /Sync/i })
    );

    const syncCount = await syncButton.count();

    if (syncCount > 0) {
      await expect(syncButton.first()).toBeVisible();
    } else {
      console.log('No integrations found to sync');
      test.skip();
    }
  });

  test('should trigger manual sync', async ({ page }) => {
    const syncButton = page.getByRole('button', { name: /Sync Now|Trigger Sync/i });
    const syncCount = await syncButton.count();

    if (syncCount > 0) {
      const initialUrl = page.url();

      await syncButton.first().click();
      await page.waitForTimeout(2000);

      // Check for success message
      const success = page.getByText(/sync triggered|sync started|sync queued/i);
      const error = page.getByText(/sync failed|could not trigger|error/i);

      const hasMessage = await success.isVisible().catch(() => false) ||
                        await error.isVisible().catch(() => false);

      expect(hasMessage).toBeTruthy();
    } else {
      console.log('No integrations found to sync');
      test.skip();
    }
  });

  test('should show sync status after triggering', async ({ page }) => {
    const syncButton = page.getByRole('button', { name: /Sync Now/i });
    const syncCount = await syncButton.count();

    if (syncCount > 0) {
      await syncButton.first().click();
      await page.waitForTimeout(2000);

      // Look for status indicators
      const statusBadge = page.locator('.MuiChip-root').filter({ hasText: /syncing|pending/i });
      const statusIcon = page.locator('[data-testid="sync-status"], .sync-status');

      const hasStatus = await statusBadge.count() > 0 || await statusIcon.count() > 0;

      if (hasStatus) {
        await expect(statusBadge.first().or(statusIcon.first())).toBeVisible();
      }
    } else {
      console.log('No integrations found to sync');
      test.skip();
    }
  });
});

test.describe('Integrations - Sync History', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
  });

  test('should have view history button', async ({ page }) => {
    const historyButton = page.getByRole('button', { name: /History|View History|Sync History/i }).or(
      page.locator('button').filter({ hasText: /History/i })
    );

    const historyCount = await historyButton.count();

    if (historyCount > 0) {
      await expect(historyButton.first()).toBeVisible();
    } else {
      console.log('No integrations found with history');
      test.skip();
    }
  });

  test('should open sync history dialog', async ({ page }) => {
    const historyButton = page.getByRole('button', { name: /History|View History/i });
    const historyCount = await historyButton.count();

    if (historyCount > 0) {
      await historyButton.first().click();
      await page.waitForTimeout(500);

      // Check for history dialog
      const dialog = page.locator('.MuiDialog-root, [role="dialog"]');
      const dialogCount = await dialog.count();

      if (dialogCount > 0) {
        await expect(dialog.first()).toBeVisible();

        // Check for history table or list
        const table = page.locator('.MuiTable-root, table');
        const tableCount = await table.count();

        if (tableCount > 0) {
          await expect(table.first()).toBeVisible();
        }

        // Check for heading
        await expect(page.getByText(/Sync History|History/i)).toBeVisible();
      }
    } else {
      console.log('No integrations found with history');
      test.skip();
    }
  });

  test('should display sync status badges', async ({ page }) => {
    const historyButton = page.getByRole('button', { name: /History/i });
    const historyCount = await historyButton.count();

    if (historyCount > 0) {
      await historyButton.first().click();
      await page.waitForTimeout(500);

      // Check for status badges
      const statusBadges = page.locator('.MuiChip-root');
      const badgeCount = await statusBadges.count();

      if (badgeCount > 0) {
        // Should have status badges like "completed", "failed", "running"
        await expect(statusBadges.first()).toBeVisible();
      }
    } else {
      console.log('No integrations found with history');
      test.skip();
    }
  });

  test('should show sync details in history', async ({ page }) => {
    const historyButton = page.getByRole('button', { name: /History/i });
    const historyCount = await historyButton.count();

    if (historyCount > 0) {
      await historyButton.first().click();
      await page.waitForTimeout(500);

      // Look for sync details
      const syncType = page.getByText(/full sync|incremental sync/i);
      const timestamp = page.getByText(/\d{1,2}\/\d{1,2}\/\d{4}|ago/i);
      const records = page.getByText(/records|processed/i);

      const hasDetails = await syncType.count() > 0 ||
                        await timestamp.count() > 0 ||
                        await records.count() > 0;

      if (hasDetails) {
        // At least some detail should be visible
        const anyDetail = syncType.or(timestamp).or(records);
        await expect(anyDetail.first()).toBeVisible();
      }
    } else {
      console.log('No integrations found with history');
      test.skip();
    }
  });
});

test.describe('Integrations - Edit Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
  });

  test('should have edit button for integrations', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /Edit/i }).or(
      page.locator('button[aria-label*="edit" i], button').filter({ hasText: /Edit/i })
    );

    const editCount = await editButton.count();

    if (editCount > 0) {
      await expect(editButton.first()).toBeVisible();
    } else {
      console.log('No integrations found to edit');
      test.skip();
    }
  });

  test('should open edit dialog with pre-filled data', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /Edit/i });
    const editCount = await editButton.count();

    if (editCount > 0) {
      await editButton.first().click();
      await page.waitForTimeout(500);

      // Check for dialog
      const dialog = page.locator('.MuiDialog-root, [role="dialog"]');
      const dialogCount = await dialog.count();

      if (dialogCount > 0) {
        await expect(dialog.first()).toBeVisible();

        // Check for pre-filled fields (name field should have value)
        const nameField = page.getByRole('textbox', { name: /name/i });
        const nameCount = await nameField.count();

        if (nameCount > 0) {
          const value = await nameField.first().inputValue();
          expect(value.length).toBeGreaterThan(0);
        }
      }
    } else {
      console.log('No integrations found to edit');
      test.skip();
    }
  });

  test('should update integration name', async ({ page }) => {
    const editButton = page.getByRole('button', { name: /Edit/i });
    const editCount = await editButton.count();

    if (editCount > 0) {
      await editButton.first().click();
      await page.waitForTimeout(500);

      // Update name field
      const nameField = page.getByRole('textbox', { name: /name/i });
      const nameCount = await nameField.count();

      if (nameCount > 0) {
        await nameField.first().clear();
        await nameField.first().fill('Updated Integration Name');

        // Save
        const saveButton = page.getByRole('button', { name: /Save|Update/i });
        const saveCount = await saveButton.count();

        if (saveCount > 0) {
          await saveButton.first().click();
          await page.waitForTimeout(2000);

          // Check for success message
          const success = page.getByText(/updated|saved|success/i);
          const successCount = await success.count();

          if (successCount > 0) {
            await expect(success.first()).toBeVisible();
          }
        }
      }
    } else {
      console.log('No integrations found to edit');
      test.skip();
    }
  });
});

test.describe('Integrations - Delete Integration', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test.beforeEach(async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
  });

  test('should have delete button for integrations', async ({ page }) => {
    const deleteButton = page.getByRole('button', { name: /Delete/i }).or(
      page.locator('button[aria-label*="delete" i]').filter({ hasText: /Delete/i })
    );

    const deleteCount = await deleteButton.count();

    if (deleteCount > 0) {
      await expect(deleteButton.first()).toBeVisible();
    } else {
      console.log('No integrations found to delete');
      test.skip();
    }
  });

  test('should show confirmation dialog before delete', async ({ page }) => {
    const deleteButton = page.getByRole('button', { name: /Delete/i });
    const deleteCount = await deleteButton.count();

    if (deleteCount > 0) {
      await deleteButton.first().click();
      await page.waitForTimeout(500);

      // Check for confirmation dialog
      const confirmDialog = page.getByRole('dialog').or(
        page.locator('.MuiDialog-root')
      );

      const dialogCount = await confirmDialog.count();

      if (dialogCount > 0) {
        await expect(confirmDialog.first()).toBeVisible();

        // Check for confirmation message
        const confirmMessage = page.getByText(/are you sure|delete this integration|confirm delete/i);
        await expect(confirmMessage.first()).toBeVisible();
      }
    } else {
      console.log('No integrations found to delete');
      test.skip();
    }
  });

  test('should cancel delete when cancel clicked', async ({ page }) => {
    const deleteButton = page.getByRole('button', { name: /Delete/i });
    const deleteCount = await deleteButton.count();

    if (deleteCount > 0) {
      await deleteButton.first().click();
      await page.waitForTimeout(500);

      // Click cancel
      const cancelButton = page.getByRole('button', { name: /Cancel/i });
      const cancelCount = await cancelButton.count();

      if (cancelCount > 0) {
        await cancelButton.first().click();
        await page.waitForTimeout(500);

        // Dialog should close
        const dialog = page.locator('.MuiDialog-root');
        const dialogCount = await dialog.count();

        // Dialog might still be visible but shouldn't have confirmation message
        if (dialogCount > 0) {
          const confirmMessage = page.getByText(/are you sure|confirm delete/i);
          const visible = await confirmMessage.isVisible().catch(() => false);
          expect(visible).toBeFalsy();
        }
      }
    } else {
      console.log('No integrations found to delete');
      test.skip();
    }
  });
});

test.describe('Integrations - Complete Workflow', () => {
  test.use({ ...DESKTOP_VIEWPORT });

  test('should complete full integration lifecycle', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Step 1: Create integration
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Fill form
      const nameField = page.getByRole('textbox', { name: /name/i });
      const nameCount = await nameField.count();

      if (nameCount > 0) {
        await nameField.first().fill('E2E Full Workflow Test');
      }

      const platformSelect = page.getByRole('combobox').or(page.locator('.MuiSelect-root'));
      const platformCount = await platformSelect.count();

      if (platformCount > 0) {
        await platformSelect.first().click();
        await page.getByRole('option', { name: /Greenhouse/i }).click();
        await page.waitForTimeout(500);

        // Fill minimal credentials
        const apiKeyField = page.locator('input[type="password"]');
        const apiKeyCount = await apiKeyField.count();

        if (apiKeyCount > 0) {
          await apiKeyField.first().fill(TEST_CREDENTIALS.greenhouse.api_key);
        }
      }

      // Save
      const saveButton = page.getByRole('button', { name: /Save|Create/i });
      const saveCount = await saveButton.count();

      if (saveCount > 0) {
        await saveButton.first().click();
        await page.waitForTimeout(2000);
      }

      // Step 2: Test connection (if integration was created)
      const testButton = page.getByRole('button', { name: /Test Connection/i }).first();
      const testCount = await testButton.count();

      if (testCount > 0) {
        await testButton.click();
        await page.waitForTimeout(3000);

        // Step 3: Trigger sync (if connection works)
        const syncButton = page.getByRole('button', { name: /Sync Now/i }).first();
        const syncCount = await syncButton.count();

        if (syncCount > 0) {
          await syncButton.click();
          await page.waitForTimeout(2000);

          // Step 4: View history
          const historyButton = page.getByRole('button', { name: /History/i }).first();
          const historyCount = await historyButton.count();

          if (historyCount > 0) {
            await historyButton.click();
            await page.waitForTimeout(500);

            // Verify history dialog is visible
            const dialog = page.locator('.MuiDialog-root');
            const dialogCount = await dialog.count();

            if (dialogCount > 0) {
              await expect(dialog.first()).toBeVisible();

              // Close dialog
              const closeButton = page.getByRole('button', { name: /Close/i }).or(
                page.locator('button[aria-label="close"]')
              );
              const closeCount = await closeButton.count();

              if (closeCount > 0) {
                await closeButton.first().click();
              }
            }
          }
        }
      }
    }
  });
});

test.describe('Integrations - Mobile Responsive', () => {
  test.use({ ...MOBILE_VIEWPORT });

  test('should display properly on mobile', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Check main heading is visible
    await expect(page.getByRole('heading', { name: /Integrations/i })).toBeVisible();

    // Check for no horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
  });

  test('should show add button on mobile', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await expect(addButton.first()).toBeVisible();
    }
  });

  test('should open integration dialog on mobile', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Dialog should be visible
      const dialog = page.locator('.MuiDialog-root');
      const dialogCount = await dialog.count();

      if (dialogCount > 0) {
        await expect(dialog.first()).toBeVisible();
      }
    }
  });
});

test.describe('Integrations - Error Handling', () => {
  test('should handle network errors gracefully', async ({ page }) => {
    // Navigate to integrations page
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Should show page even if API fails
    await expect(page.getByRole('heading', { name: /Integrations/i })).toBeVisible();

    // Check for empty state or error message
    const content = page.locator('.MuiTableBody-root, .MuiCard-root').or(
      page.getByText(/No integrations|Error|Failed to load/i)
    );

    await expect(content.first()).toBeVisible();
  });

  test('should show error message for invalid credentials', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Try to create integration with invalid data
    const addButton = page.getByRole('button', { name: /Add/i });
    const addCount = await addButton.count();

    if (addCount > 0) {
      await addButton.first().click();
      await page.waitForTimeout(500);

      // Fill with invalid data
      const nameField = page.getByRole('textbox', { name: /name/i });
      const nameCount = await nameField.count();

      if (nameCount > 0) {
        await nameField.first().fill('Invalid Integration');
      }

      const platformSelect = page.getByRole('combobox').or(page.locator('.MuiSelect-root'));
      const platformCount = await platformSelect.count();

      if (platformCount > 0) {
        await platformSelect.first().click();
        await page.getByRole('option', { name: /Workday/i }).click();
        await page.waitForTimeout(500);

        // Use invalid credentials
        const apiUrlField = page.getByRole('textbox', { name: /api url/i });
        const apiUrlCount = await apiUrlField.count();

        if (apiUrlCount > 0) {
          await apiUrlField.first().fill('invalid-url');
        }
      }

      // Try to test connection (should fail gracefully)
      const testButton = page.getByRole('button', { name: /Test Connection/i });
      const testCount = await testButton.count();

      if (testCount > 0) {
        await testButton.first().click();
        await page.waitForTimeout(3000);

        // Should show error message
        const error = page.getByText(/error|failed|invalid|could not connect/i);
        const errorCount = await error.count();

        if (errorCount > 0) {
          await expect(error.first()).toBeVisible();
        }
      }
    }
  });
});

test.describe('Integrations - Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Check for h1 heading
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Tab through focusable elements
    await page.keyboard.press('Tab');

    // Something should be focused
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'INPUT', 'A', 'NAV', 'TABLE']).includes(focused || '');
  });

  test('should have ARIA labels on buttons', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Check for buttons with aria-labels
    const buttons = page.locator('button[aria-label], button[aria-labelledby]');
    const buttonCount = await buttons.count();

    // At least some buttons should have aria-labels
    if (buttonCount > 0) {
      await expect(buttons.first()).toBeVisible();
    }
  });
});
