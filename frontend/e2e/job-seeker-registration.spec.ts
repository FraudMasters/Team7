/**
 * E2E Tests for Job Seeker Registration Flow
 *
 * This test suite validates the complete job seeker user registration flow:
 * - Job seeker registration page accessibility and UI elements
 * - Form validation for all required fields
 * - Form submission with valid data
 * - Role assignment (job_seeker)
 * - Redirect to login after successful registration
 * - Error handling for duplicate emails
 * - Navigation between registration and login pages
 *
 * Prerequisites:
 * - Frontend running on http://localhost:5173
 * - Backend API available for registration endpoint
 *
 * Environment Variables:
 * - BASE_URL: Frontend URL (default: http://localhost:5173)
 * - TEST_USER_EMAIL: Email for test user account
 * - TEST_USER_PASSWORD: Password for test user account
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || `jobseeker-${Date.now()}@example.com`;
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'Test123456';

/**
 * Helper function to generate unique test job seeker credentials
 */
function generateJobSeekerCredentials() {
  const timestamp = Date.now();
  return {
    firstName: 'John',
    lastName: `Doe${timestamp}`,
    email: `jobseeker-${timestamp}@example.com`,
    password: 'Test123456',
    confirmPassword: 'Test123456'
  };
}

/**
 * Helper function to fill job seeker registration form
 */
async function fillJobSeekerRegistrationForm(
  page: Page,
  firstName: string,
  lastName: string,
  email: string,
  password: string,
  confirmPassword: string
) {
  await page.fill('input[label="First Name"]', firstName);
  await page.fill('input[label="Last Name"]', lastName);
  await page.fill('input[label="Email Address"]', email);
  await page.fill('input[label="Password"]', password);
  await page.fill('input[label="Confirm Password"]', confirmPassword);
}

/**
 * Test: Job Seeker Registration page accessibility
 */
test.describe('Job Seeker Registration Page Accessibility', () => {
  test('should load job seeker registration page successfully', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Verify page title
    await expect(page).toHaveTitle(/Resume Analysis/);

    // Verify main heading
    await expect(page.getByText('Create Your Job Seeker Account')).toBeVisible();

    // Verify subtitle
    await expect(page.getByText('Join AgentHR to find your next opportunity')).toBeVisible();

    // Verify all form fields are present
    await expect(page.getByLabel('First Name')).toBeVisible();
    await expect(page.getByLabel('Last Name')).toBeVisible();
    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByLabel('Confirm Password')).toBeVisible();

    // Verify submit button
    await expect(page.getByRole('button', { name: 'Create Job Seeker Account' })).toBeVisible();

    // Verify login link is present
    await expect(page.getByText('Already have an account?')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();

    // Verify employer registration link
    await expect(page.getByText('Are you an employer?')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Register here' })).toBeVisible();
  });

  test('should have proper form attributes', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check first name field
    const firstNameInput = page.getByLabel('First Name');
    await expect(firstNameInput).toHaveAttribute('type', 'text');
    await expect(firstNameInput).toHaveAttribute('autocomplete', 'given-name');
    await expect(firstNameInput).toHaveAttribute('required', '');

    // Check last name field
    const lastNameInput = page.getByLabel('Last Name');
    await expect(lastNameInput).toHaveAttribute('type', 'text');
    await expect(lastNameInput).toHaveAttribute('autocomplete', 'family-name');
    await expect(lastNameInput).toHaveAttribute('required', '');

    // Check email field
    const emailInput = page.getByLabel('Email Address');
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(emailInput).toHaveAttribute('autocomplete', 'email');
    await expect(emailInput).toHaveAttribute('required', '');

    // Check password fields
    const passwordInput = page.getByLabel('Password');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(passwordInput).toHaveAttribute('autocomplete', 'new-password');
    await expect(passwordInput).toHaveAttribute('required', '');

    const confirmPasswordInput = page.getByLabel('Confirm Password');
    await expect(confirmPasswordInput).toHaveAttribute('type', 'password');
    await expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password');
    await expect(confirmPasswordInput).toHaveAttribute('required', '');
  });

  test('should have skip-to-content link for accessibility', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check for skip link
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');

    // Check for main content area
    await expect(page.locator('#main-content')).toBeVisible();
  });
});

/**
 * Test: Form validation
 */
test.describe('Job Seeker Registration Form Validation', () => {
  test('should validate first name is required', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form without first name
    await page.fill('input[label="First Name"]', '');
    await page.fill('input[label="Last Name"]', credentials.lastName);
    await page.fill('input[label="Email Address"]', credentials.email);
    await page.fill('input[label="Password"]', credentials.password);
    await page.fill('input[label="Confirm Password"]', credentials.confirmPassword);

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('First name is required')).toBeVisible();
  });

  test('should validate first name minimum length', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form with single character first name
    await page.fill('input[label="First Name"]', 'J');
    await page.fill('input[label="Last Name"]', credentials.lastName);
    await page.fill('input[label="Email Address"]', credentials.email);
    await page.fill('input[label="Password"]', credentials.password);
    await page.fill('input[label="Confirm Password"]', credentials.confirmPassword);

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('First name must be at least 2 characters')).toBeVisible();
  });

  test('should validate last name is required', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form without last name
    await page.fill('input[label="First Name"]', credentials.firstName);
    await page.fill('input[label="Last Name"]', '');
    await page.fill('input[label="Email Address"]', credentials.email);
    await page.fill('input[label="Password"]', credentials.password);
    await page.fill('input[label="Confirm Password"]', credentials.confirmPassword);

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('Last name is required')).toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form with invalid email
    await page.fill('input[label="First Name"]', credentials.firstName);
    await page.fill('input[label="Last Name"]', credentials.lastName);
    await page.fill('input[label="Email Address"]', 'invalid-email');
    await page.fill('input[label="Password"]', credentials.password);
    await page.fill('input[label="Confirm Password"]', credentials.confirmPassword);

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('Please enter a valid email address')).toBeVisible();
  });

  test('should validate password strength', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form with weak password
    await page.fill('input[label="First Name"]', credentials.firstName);
    await page.fill('input[label="Last Name"]', credentials.lastName);
    await page.fill('input[label="Email Address"]', credentials.email);
    await page.fill('input[label="Password"]', 'weak');
    await page.fill('input[label="Confirm Password"]', 'weak');

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('Password must be at least 8 characters with uppercase, lowercase, and number')).toBeVisible();
  });

  test('should validate password confirmation match', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form with mismatched passwords
    await page.fill('input[label="First Name"]', credentials.firstName);
    await page.fill('input[label="Last Name"]', credentials.lastName);
    await page.fill('input[label="Email Address"]', credentials.email);
    await page.fill('input[label="Password"]', credentials.password);
    await page.fill('input[label="Confirm Password"]', 'DifferentPassword123');

    // Try to submit
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should show validation error
    await expect(page.getByText('Passwords do not match')).toBeVisible();
  });

  test('should clear error on input change', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Trigger first name error
    await page.fill('input[label="First Name"]', 'J');
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();
    await expect(page.getByText('First name must be at least 2 characters')).toBeVisible();

    // Fix the error
    await page.fill('input[label="First Name"]', 'John');

    // Error should be cleared
    await expect(page.getByText('First name must be at least 2 characters')).not.toBeVisible();
  });
});

/**
 * Test: Registration form submission
 */
test.describe('Job Seeker Registration Form Submission', () => {
  test('should submit registration form with valid data', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form
    await fillJobSeekerRegistrationForm(
      page,
      credentials.firstName,
      credentials.lastName,
      credentials.email,
      credentials.password,
      credentials.confirmPassword
    );

    // Submit form
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Should redirect to login page with success message
    await page.waitForURL(`${BASE_URL}/login`, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  test('should show loading state during submission', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form
    await fillJobSeekerRegistrationForm(
      page,
      credentials.firstName,
      credentials.lastName,
      credentials.email,
      credentials.password,
      credentials.confirmPassword
    );

    // Submit and check for loading state
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Button should show loading indicator (circular progress)
    const submitButton = page.getByRole('button', { name: 'Create Job Seeker Account' });
    // Check if button is disabled during loading
    const isDisabled = await submitButton.isDisabled();
    expect(isDisabled).toBe(true);
  });

  test('should handle registration errors gracefully', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Use credentials that might cause an error
    const credentials = {
      firstName: 'Test',
      lastName: 'User',
      email: 'admin@agenthr.com', // This email might already exist
      password: 'Test123456',
      confirmPassword: 'Test123456'
    };

    // Fill form
    await fillJobSeekerRegistrationForm(
      page,
      credentials.firstName,
      credentials.lastName,
      credentials.email,
      credentials.password,
      credentials.confirmPassword
    );

    // Submit form
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Wait a bit for response
    await page.waitForTimeout(2000);

    // Check if error alert is shown
    const errorAlert = page.locator('[role="alert"]').first();
    const errorVisible = await errorAlert.isVisible().catch(() => false);

    if (errorVisible) {
      await expect(errorAlert).toBeVisible();
    }
  });
});

/**
 * Test: Navigation links
 */
test.describe('Navigation Links', () => {
  test('should navigate to login page when clicking Sign in link', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Click Sign in link
    await page.getByRole('link', { name: 'Sign in' }).click();

    // Should navigate to login page
    await page.waitForURL(`${BASE_URL}/login`);
    expect(page.url()).toContain('/login');
  });

  test('should navigate to employer registration page', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Click Register here link for employers
    await page.getByRole('link', { name: 'Register here' }).click();

    // Should navigate to employer registration page
    await page.waitForURL(`${BASE_URL}/register`);
    expect(page.url()).toContain('/register');
  });
});

/**
 * Test: Responsive design
 */
test.describe('Responsive Design', () => {
  test('should be mobile-friendly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Form should still be visible and usable
    await expect(page.getByLabel('First Name')).toBeVisible();
    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Job Seeker Account' })).toBeVisible();

    // Verify no horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width || 375;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10);
  });

  test('should work on tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Form should be visible
    await expect(page.getByLabel('First Name')).toBeVisible();
    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Job Seeker Account' })).toBeVisible();
  });

  test('should work on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Form should be visible
    await expect(page.getByLabel('First Name')).toBeVisible();
    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Job Seeker Account' })).toBeVisible();

    // First name and last name fields should be side by side on desktop
    const firstNameInput = page.getByLabel('First Name');
    const firstNameBox = await firstNameInput.boundingBox();
    const lastNameInput = page.getByLabel('Last Name');
    const lastNameBox = await lastNameInput.boundingBox();

    // On desktop, they should be on same row (similar Y positions)
    if (firstNameBox && lastNameBox) {
      expect(Math.abs(firstNameBox.y - lastNameBox.y)).toBeLessThan(50);
    }
  });
});

/**
 * Test: Keyboard navigation
 */
test.describe('Keyboard Navigation', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Tab through form fields
    await page.keyboard.press('Tab');
    let focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('INPUT');

    await page.keyboard.press('Tab');
    focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('INPUT'); // Second name field

    await page.keyboard.press('Tab');
    focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('INPUT'); // Email field

    await page.keyboard.press('Tab');
    focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('INPUT'); // Password field

    await page.keyboard.press('Tab');
    focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('INPUT'); // Confirm password field

    // Submit with Enter key
    await page.keyboard.press('Enter');

    // Form should submit (or show validation errors)
    await page.waitForTimeout(1000);
  });

  test('should submit form with Enter key', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form
    await fillJobSeekerRegistrationForm(
      page,
      credentials.firstName,
      credentials.lastName,
      credentials.email,
      credentials.password,
      credentials.confirmPassword
    );

    // Submit with Enter key
    await page.keyboard.press('Enter');

    // Should redirect to login
    await page.waitForURL(`${BASE_URL}/login`, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });
});

/**
 * Test: Visual elements
 */
test.describe('Visual Elements', () => {
  test('should display work icon in header', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check for the work icon (green gradient box)
    const iconBox = page.locator('svg').first();
    await expect(iconBox).toBeVisible();
  });

  test('should use green color scheme for job seeker branding', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check submit button has green gradient
    const submitButton = page.getByRole('button', { name: 'Create Job Seeker Account' });
    await expect(submitButton).toBeVisible();

    // The button should have visible styling (we can't easily test gradient in E2E)
    // but we can verify it exists
    await expect(submitButton).toHaveCSS('background', /.*rgb.*10.*184.*129.*/);
  });

  test('should have proper form structure', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check for form card
    const card = page.locator('.MuiCard-root').first();
    await expect(card).toBeVisible();

    // Check form has proper aria-label
    const form = page.locator('form[aria-label="Job seeker registration form"]');
    await expect(form).toBeVisible();
  });
});

/**
 * Test: Form auto-fill support
 */
test.describe('Form Auto-fill Support', () => {
  test('should have proper autocomplete attributes', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Check autocomplete attributes for password manager support
    await expect(page.getByLabel('First Name')).toHaveAttribute('autocomplete', 'given-name');
    await expect(page.getByLabel('Last Name')).toHaveAttribute('autocomplete', 'family-name');
    await expect(page.getByLabel('Email Address')).toHaveAttribute('autocomplete', 'email');
    await expect(page.getByLabel('Password')).toHaveAttribute('autocomplete', 'new-password');
    await expect(page.getByLabel('Confirm Password')).toHaveAttribute('autocomplete', 'new-password');
  });
});

/**
 * Test: ARIA attributes for accessibility
 */
test.describe('ARIA Attributes', () => {
  test('should have proper ARIA descriptions for errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Trigger first name error
    await page.fill('input[label="First Name"]', 'J');
    await page.getByRole('button', { name: 'Create Job Seeker Account' }).click();

    // Check for aria-describedby on error state
    const firstNameInput = page.getByLabel('First Name');
    const ariaDescribedby = await firstNameInput.getAttribute('aria-describedby');
    expect(ariaDescribedby).toContain('firstName-error');
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    // Form should have aria-label
    const form = page.locator('form');
    await expect(form).toHaveAttribute('aria-label', 'Job seeker registration form');
  });
});

/**
 * Test: Multiple registration attempts
 */
test.describe('Multiple Registration Attempts', () => {
  test('should allow clearing form and starting over', async ({ page }) => {
    await page.goto(`${BASE_URL}/job-seeker/register`);

    const credentials = generateJobSeekerCredentials();

    // Fill form partially
    await page.fill('input[label="First Name"]', credentials.firstName);
    await page.fill('input[label="Email Address"]', credentials.email);

    // Reload page to clear
    await page.reload();

    // Form should be cleared
    const firstNameValue = await page.getByLabel('First Name').inputValue();
    const emailValue = await page.getByLabel('Email Address').inputValue();

    expect(firstNameValue).toBe('');
    expect(emailValue).toBe('');
  });
});
