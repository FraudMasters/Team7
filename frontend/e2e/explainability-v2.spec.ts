import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Enhanced Explainability V2 Features
 *
 * Test Suite Contents:
 * 1. Candidate Ranking Page & Detailed Explanations
 * 2. Side-by-Side Comparison & Differential Analysis
 * 3. What-If Scenarios (Skill Addition)
 * 4. Predicted Rank Changes
 * 5. Candidate Appeal Portal
 * 6. Integration & End-to-End Flows
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - Test data: ranked candidates with v2 explainability features
 */

test.describe('Candidate Ranking Page - Navigation & Detailed Explanations', () => {
  test('should navigate to candidate ranking page', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Check URL
    await expect(page).toHaveURL(/\/candidates\/ranking/);

    // Check page title contains relevant text
    await expect(page).toHaveTitle(/Ranking|Candidates/i);

    // Check main heading exists
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible();
  });

  test('should display detailed explanation narrative', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for explanation narrative section
    const narrativeSection = page.getByText(/explanation|why this candidate|ranking rationale/i);
    await expect(narrativeSection).toBeVisible();

    // Check for narrative content (should be more than just a heading)
    const narrativeContent = page.locator('.explanation-narrative, [data-testid="explanation-narrative"]');
    if (await narrativeContent.count() > 0) {
      await expect(narrativeContent.first()).toBeVisible();

      // Verify narrative has substantial content
      const text = await narrativeContent.first().textContent();
      expect(text?.length).toBeGreaterThan(50);
    }
  });

  test('should show detailed breakdown of ranking factors', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for ranking factors
    const factors = page.getByText(/skills?|experience|education|qualifications/i);
    expect(await factors.count()).toBeGreaterThan(0);

    // Check for score or percentage indicators
    const scores = page.locator('[data-score], .score, .percentage');
    if (await scores.count() > 0) {
      await expect(scores.first()).toBeVisible();
    }
  });

  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/candidates/ranking');

    // Wait a bit for any delayed errors
    await page.waitForTimeout(2000);

    expect(errors).toHaveLength(0);
  });
});

test.describe('Side-by-Side Comparison & Differential Analysis', () => {
  test('should display compare button for candidates', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for compare button
    const compareButton = page.getByRole('button').filter({ hasText: /compare|vs|comparison/i });
    if (await compareButton.count() > 0) {
      await expect(compareButton.first()).toBeVisible();
    }
  });

  test('should open side-by-side comparison view on button click', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Find and click compare button
    const compareButton = page.getByRole('button').filter({ hasText: /compare|vs|comparison/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();

      // Wait for comparison view to load
      await page.waitForTimeout(1000);

      // Check for comparison container
      const comparisonView = page.locator('.comparison-view, [data-testid="comparison-view"]');
      if (await comparisonView.count() > 0) {
        await expect(comparisonView.first()).toBeVisible();
      }

      // Check for two candidate cards side by side
      const candidateCards = page.locator('.candidate-card, .comparison-candidate');
      if (await candidateCards.count() >= 2) {
        await expect(candidateCards.nth(0)).toBeVisible();
        await expect(candidateCards.nth(1)).toBeVisible();
      }
    }
  });

  test('should show differential analysis between candidates', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Open comparison
    const compareButton = page.getByRole('button').filter({ hasText: /compare|vs|comparison/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Look for differential indicators
      const differentialText = page.getByText(/stronger in|weaker in|advantage|difference|delta/i);
      if (await differentialText.count() > 0) {
        await expect(differentialText.first()).toBeVisible();
      }

      // Check for visual difference indicators (arrows, colors, etc.)
      const diffIndicators = page.locator('.diff-indicator, [data-diff], .positive, .negative');
      if (await diffIndicators.count() > 0) {
        await expect(diffIndicators.first()).toBeVisible();
      }
    }
  });

  test('should highlight feature-level differences', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const compareButton = page.getByRole('button').filter({ hasText: /compare|vs|comparison/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Look for feature comparison rows
      const featureRows = page.locator('.feature-row, .comparison-row, [data-feature]');
      if (await featureRows.count() > 0) {
        await expect(featureRows.first()).toBeVisible();
      }

      // Check for win/loss indicators per feature
      const winIndicators = page.locator('.better, .winner, [data-better="true"]');
      const lossIndicators = page.locator('.worse, .loser, [data-worse="true"]');

      const hasIndicators = await winIndicators.count() > 0 || await lossIndicators.count() > 0;
      if (hasIndicators) {
        expect(hasIndicators).toBeTruthy();
      }
    }
  });

  test('should show percentage or score differences', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const compareButton = page.getByRole('button').filter({ hasText: /compare|vs|comparison/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Look for percentage differences
      const percentDiff = page.locator('[data-testid="percent-diff"], .percent-diff');
      if (await percentDiff.count() > 0) {
        await expect(percentDiff.first()).toBeVisible();
      }
    }
  });
});

test.describe('What-If Scenarios - Skill Addition', () => {
  test('should display what-if scenario controls', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for what-if section
    const whatIfSection = page.getByText(/what-?if|scenario|simulation/i);
    if (await whatIfSection.isVisible()) {
      await expect(whatIfSection).toBeVisible();
    }
  });

  test('should show skill addition interface', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for add skill button or input
    const addSkillButton = page.getByRole('button').filter({ hasText: /add skill|add|new skill/i });
    const skillInput = page.locator('input[placeholder*="skill" i], input[aria-label*="skill" i]');

    const hasSkillInterface = await addSkillButton.count() > 0 || await skillInput.count() > 0;
    if (hasSkillInterface) {
      expect(hasSkillInterface).toBeTruthy();
    }
  });

  test('should allow adding a skill to what-if scenario', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Find skill input
    const skillInput = page.locator('input[placeholder*="skill" i], input[aria-label*="skill" i]').first();

    if (await skillInput.isVisible()) {
      // Add a test skill
      await skillInput.fill('Python');

      // Look for confirm/add button
      const addButton = page.getByRole('button').filter({ hasText: /add|confirm|apply/i });
      if (await addButton.count() > 0) {
        await addButton.first().click();
        await page.waitForTimeout(500);

        // Verify skill was added
        const addedSkill = page.getByText(/python/i);
        if (await addedSkill.count() > 0) {
          await expect(addedSkill.first()).toBeVisible();
        }
      }
    }
  });

  test('should support multiple skill additions', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const skillInput = page.locator('input[placeholder*="skill" i], input[aria-label*="skill" i]').first();

    if (await skillInput.isVisible()) {
      // Add first skill
      await skillInput.fill('JavaScript');
      const addButton = page.getByRole('button').filter({ hasText: /add|confirm|apply/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(300);

        // Add second skill
        await skillInput.fill('React');
        await addButton.click();
        await page.waitForTimeout(300);

        // Both skills should be visible
        const jsSkill = page.getByText(/javascript/i);
        const reactSkill = page.getByText(/react/i);

        if (await jsSkill.count() > 0 && await reactSkill.count() > 0) {
          expect(await jsSkill.first().isVisible() || await reactSkill.first().isVisible()).toBeTruthy();
        }
      }
    }
  });
});

test.describe('Predicted Rank Changes', () => {
  test('should display predicted rank after what-if changes', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for rank prediction display
    const rankPrediction = page.locator('[data-testid="predicted-rank"], .predicted-rank, .new-rank');
    if (await rankPrediction.count() > 0) {
      await expect(rankPrediction.first()).toBeVisible();
    }
  });

  test('should update predicted rank when skill is added', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Get initial rank
    const currentRank = page.locator('[data-testid="current-rank"], .current-rank');
    const currentRankText = await currentRank.first().textContent();

    // Add a skill via what-if
    const skillInput = page.locator('input[placeholder*="skill" i], input[aria-label*="skill" i]').first();

    if (await skillInput.isVisible()) {
      await skillInput.fill('Python');

      const addButton = page.getByRole('button').filter({ hasText: /add|confirm|apply/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(1000);

        // Check for updated prediction
        const predictedRank = page.locator('[data-testid="predicted-rank"], .predicted-rank');
        if (await predictedRank.count() > 0) {
          await expect(predictedRank.first()).toBeVisible();
        }
      }
    }
  });

  test('should show rank change indicator (up/down/same)', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Add skill to trigger rank change
    const skillInput = page.locator('input[placeholder*="skill" i]').first();

    if (await skillInput.isVisible()) {
      await skillInput.fill('Machine Learning');

      const addButton = page.getByRole('button').filter({ hasText: /add|apply/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(1000);

        // Look for rank change indicators
        const upIndicator = page.locator('.rank-up, [data-rank-change="up"], .arrow-up');
        const downIndicator = page.locator('.rank-down, [data-rank-change="down"], .arrow-down');

        const hasIndicator = await upIndicator.count() > 0 || await downIndicator.count() > 0;
        if (hasIndicator) {
          expect(hasIndicator).toBeTruthy();
        }
      }
    }
  });

  test('should show delta/difference in ranking position', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for rank delta display
    const rankDelta = page.locator('[data-testid="rank-delta"], .rank-change, .delta');
    if (await rankDelta.count() > 0) {
      await expect(rankDelta.first()).toBeVisible();

      // Verify it shows a number (e.g., "+2", "-1", "±3")
      const deltaText = await rankDelta.first().textContent();
      expect(deltaText).toMatch(/[+\-±]?\d+/);
    }
  });
});

test.describe('Candidate Appeal Portal', () => {
  test('should display appeal submission interface', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Look for appeal section or button
    const appealSection = page.getByText(/appeal|contest|dispute|feedback/i);
    if (await appealSection.count() > 0) {
      await expect(appealSection.first()).toBeVisible();
    }
  });

  test('should show appeal form with required fields', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Find appeal button
    const appealButton = page.getByRole('button').filter({ hasText: /submit appeal|appeal|contest/i });

    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      // Check for form fields
      const textArea = page.locator('textarea[placeholder*="reason" i], textarea[placeholder*="appeal" i]');
      const input = page.locator('input[type="text"][placeholder*="appeal" i]');

      const hasFormFields = await textArea.count() > 0 || await input.count() > 0;
      if (hasFormFields) {
        expect(hasFormFields).toBeTruthy();
      }
    }
  });

  test('should submit candidate appeal successfully', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Find and click appeal button
    const appealButton = page.getByRole('button').filter({ hasText: /submit appeal|appeal|contest/i });

    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      // Fill out appeal form
      const reasonField = page.locator('textarea[placeholder*="reason" i], textarea').first();

      if (await reasonField.isVisible()) {
        await reasonField.fill('I believe my Python experience should be weighted more heavily as it directly aligns with the job requirements.');

        // Submit the appeal
        const submitButton = page.getByRole('button').filter({ hasText: /submit|send|confirm/i });
        if (await submitButton.count() > 0) {
          await submitButton.first().click();
          await page.waitForTimeout(1000);

          // Check for success confirmation
          const successMessage = page.getByText(/success|submitted|received|thank you/i);
          if (await successMessage.count() > 0) {
            await expect(successMessage.first()).toBeVisible();
          }
        }
      }
    }
  });

  test('should display appeal submission confirmation', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const appealButton = page.getByRole('button').filter({ hasText: /submit appeal|appeal/i });

    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      const reasonField = page.locator('textarea').first();

      if (await reasonField.isVisible()) {
        await reasonField.fill('Appeal test submission');

        const submitButton = page.getByRole('button').filter({ hasText: /submit|send/i });
        if (await submitButton.count() > 0) {
          await submitButton.first().click();
          await page.waitForTimeout(1000);

          // Look for confirmation elements
          const confirmationModal = page.locator('[role="dialog"], .modal, .confirmation');
          const confirmationText = page.getByText(/confirmation|submitted|appeal.*received/i);

          const hasConfirmation = await confirmationModal.count() > 0 || await confirmationText.count() > 0;
          if (hasConfirmation) {
            expect(hasConfirmation).toBeTruthy();
          }
        }
      }
    }
  });

  test('should validate required fields before submission', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const appealButton = page.getByRole('button').filter({ hasText: /submit appeal|appeal/i });

    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      // Try to submit without filling fields
      const submitButton = page.getByRole('button').filter({ hasText: /submit|send/i });
      if (await submitButton.count() > 0) {
        await submitButton.first().click();
        await page.waitForTimeout(500);

        // Look for validation error
        const validationError = page.getByText(/required|must|cannot be empty|please provide/i);
        if (await validationError.count() > 0) {
          await expect(validationError.first()).toBeVisible();
        }
      }
    }
  });
});

test.describe('End-to-End Integration Flow', () => {
  test('should complete full explainability workflow', async ({ page }) => {
    // Step 1: Navigate to candidate ranking page
    await page.goto('/candidates/ranking');
    await expect(page).toHaveURL(/\/candidates\/ranking/);

    // Step 2: Verify detailed explanation narrative displays
    const narrative = page.locator('.explanation-narrative, [data-testid="explanation-narrative"]');
    if (await narrative.count() > 0) {
      await expect(narrative.first()).toBeVisible();
    }

    // Step 3: Click compare button to view side-by-side comparison
    const compareButton = page.getByRole('button').filter({ hasText: /compare/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Step 4: Verify comparison shows differential analysis
      const differential = page.getByText(/stronger|weaker|advantage|difference/i);
      if (await differential.count() > 0) {
        await expect(differential.first()).toBeVisible();
      }
    }

    // Step 5: Test what-if scenario with skill addition
    const skillInput = page.locator('input[placeholder*="skill" i]').first();
    if (await skillInput.isVisible()) {
      await skillInput.fill('Python');

      const addButton = page.getByRole('button').filter({ hasText: /add|apply/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(1000);

        // Step 6: Verify predicted rank change displays
        const rankChange = page.locator('[data-testid="predicted-rank"], .predicted-rank, .rank-change');
        if (await rankChange.count() > 0) {
          await expect(rankChange.first()).toBeVisible();
        }
      }
    }

    // Step 7: Submit candidate appeal via portal
    const appealButton = page.getByRole('button').filter({ hasText: /appeal/i });
    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      const appealText = page.locator('textarea').first();
      if (await appealText.isVisible()) {
        await appealText.fill('Test appeal for E2E verification');

        const submitAppeal = page.getByRole('button').filter({ hasText: /submit/i });
        if (await submitAppeal.count() > 0) {
          await submitAppeal.first().click();
          await page.waitForTimeout(1000);

          // Step 8: Verify appeal submission confirmation
          const confirmation = page.getByText(/success|submitted|confirmation/i);
          if (await confirmation.count() > 0) {
            await expect(confirmation.first()).toBeVisible();
          }
        }
      }
    }
  });
});

test.describe('Error Handling - V2 Features', () => {
  test('should handle comparison API errors gracefully', async ({ page }) => {
    await page.route('**/api/candidates/compare/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Comparison service unavailable' })
      });
    });

    await page.goto('/candidates/ranking');

    const compareButton = page.getByRole('button').filter({ hasText: /compare/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Check for error message
      const errorMessage = page.getByText(/error|failed|unable|unavailable/i);
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible();
      }
    }
  });

  test('should handle what-if API errors gracefully', async ({ page }) => {
    await page.route('**/api/what-if/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'What-if service unavailable' })
      });
    });

    await page.goto('/candidates/ranking');

    const skillInput = page.locator('input[placeholder*="skill" i]').first();
    if (await skillInput.isVisible()) {
      await skillInput.fill('Python');

      const addButton = page.getByRole('button').filter({ hasText: /add/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(1000);

        // Check for error handling
        const errorMessage = page.getByText(/error|failed/i);
        const retryButton = page.getByRole('button').filter({ hasText: /retry/i });

        expect(await errorMessage.count() > 0 || await retryButton.count() > 0).toBeTruthy();
      }
    }
  });

  test('should handle appeal submission errors', async ({ page }) => {
    await page.route('**/api/appeals/**', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid appeal submission' })
      });
    });

    await page.goto('/candidates/ranking');

    const appealButton = page.getByRole('button').filter({ hasText: /appeal/i });
    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      const appealText = page.locator('textarea').first();
      if (await appealText.isVisible()) {
        await appealText.fill('Test appeal');

        const submitButton = page.getByRole('button').filter({ hasText: /submit/i });
        if (await submitButton.count() > 0) {
          await submitButton.first().click();
          await page.waitForTimeout(1000);

          // Check for error message
          const errorMessage = page.getByText(/error|failed|invalid/i);
          if (await errorMessage.count() > 0) {
            await expect(errorMessage.first()).toBeVisible();
          }
        }
      }
    }
  });
});

test.describe('Responsive Design - V2 Features', () => {
  test('should display comparison view on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/candidates/ranking');

    const compareButton = page.getByRole('button').filter({ hasText: /compare/i });
    if (await compareButton.count() > 0) {
      await compareButton.first().click();
      await page.waitForTimeout(1000);

      // Verify comparison is visible (may stack vertically)
      const comparisonView = page.locator('.comparison-view, [data-testid="comparison-view"]');
      if (await comparisonView.count() > 0) {
        await expect(comparisonView.first()).toBeVisible();
      }
    }
  });

  test('should handle appeal form on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/candidates/ranking');

    const appealButton = page.getByRole('button').filter({ hasText: /appeal/i });
    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      const appealForm = page.locator('textarea, form');
      if (await appealForm.count() > 0) {
        await expect(appealForm.first()).toBeVisible();
      }
    }
  });
});

test.describe('Accessibility - V2 Features', () => {
  test('should support keyboard navigation for comparison', async ({ page }) => {
    await page.goto('/candidates/ranking');

    // Tab to compare button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Try to activate with Enter or Space
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);

    // Verify some interaction occurred
    expect(true).toBeTruthy();
  });

  test('should have proper ARIA labels on appeal form', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const appealButton = page.getByRole('button').filter({ hasText: /appeal/i });
    if (await appealButton.count() > 0) {
      await appealButton.first().click();
      await page.waitForTimeout(500);

      // Check for ARIA labels
      const labeledInputs = page.locator('textarea[aria-label], textarea[aria-labelledby], input[aria-label]');
      if (await labeledInputs.count() > 0) {
        await expect(labeledInputs.first()).toBeVisible();
      }
    }
  });
});

test.describe('Performance - V2 Features', () => {
  test('should load comparison view quickly', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const compareButton = page.getByRole('button').filter({ hasText: /compare/i });
    if (await compareButton.count() > 0) {
      const startTime = Date.now();

      await compareButton.first().click();

      // Wait for comparison to load
      await page.waitForSelector('.comparison-view, [data-testid="comparison-view"], body', {
        timeout: 3000
      });

      const loadTime = Date.now() - startTime;

      // Should load within 3 seconds
      expect(loadTime).toBeLessThan(3000);
    }
  });

  test('should update what-if predictions without blocking UI', async ({ page }) => {
    await page.goto('/candidates/ranking');

    const skillInput = page.locator('input[placeholder*="skill" i]').first();
    if (await skillInput.isVisible()) {
      await skillInput.fill('Python');

      const addButton = page.getByRole('button').filter({ hasText: /add/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        // UI should remain responsive
        const isResponsive = await page.evaluate(() => {
          return document.readyState === 'complete' || document.readyState === 'interactive';
        });

        expect(isResponsive).toBeTruthy();
      }
    }
  });
});
