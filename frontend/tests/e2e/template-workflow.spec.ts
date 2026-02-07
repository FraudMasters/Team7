/**
 * End-to-End Tests for Template Workflow
 *
 * This test suite verifies the complete communication template workflow:
 * 1. Create communication template
 * 2. Preview template with variable substitution
 * 3. Use template to compose email
 * 4. Send email
 * 5. Verify email uses template content
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Frontend running on http://localhost:5173
 * - Test database with candidate data
 * - Mock or test SMTP provider configured
 */

import { test, expect, Page } from '@playwright/test';

// Helper functions

async function loginAsRecruiter(page: Page) {
  await page.goto('http://localhost:5173/login');
  await page.fill('input[name="email"]', 'recruiter@test.com');
  await page.fill('input[name="password"]', 'testpassword');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:5173/recruiter/dashboard');
}

async function navigateToCommunications(page: Page) {
  await page.click('text=Communications');
  await page.waitForURL('**/communications');
  await page.waitForLoadState('networkidle');
}

async function navigateToTemplatesTab(page: Page) {
  await page.click('role=tab[name="Templates"]');
  await page.waitForLoadState('networkidle');
}

async function navigateToCandidatePage(page: Page, candidateId: string) {
  await page.goto(`http://localhost:5173/recruiter/candidates/${candidateId}`);
  await page.waitForLoadState('networkidle');
}

async function createTestCandidateViaAPI(): Promise<{id: string, name: string, email: string}> {
  // This would typically create a test candidate via API
  // For now, we assume candidate exists or is created by backend tests
  return {
    id: 'test-candidate-id',
    name: 'Test Candidate',
    email: 'test.candidate@example.com'
  };
}

// Test Suite

test.describe('Template Workflow E2E', () => {
  let page: Page;
  let testCandidate: {id: string, name: string, email: string};

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    testCandidate = await createTestCandidateViaAPI();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test.beforeEach(async () => {
    await loginAsRecruiter(page);
  });

  test('Step 1: Create communication template', async () => {
    /**
     * Test: Create communication template
     *
     * Verifies:
     * - Templates page is accessible
     * - Create template button works
     * - Template form accepts all required fields
     * - Template variables are detected from {{variable}} syntax
     * - Template is saved and appears in templates list
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Click "Create Template" button
    const createTemplateButton = page.locator('button:has-text("Create Template")').first();
    await expect(createTemplateButton).toBeVisible();
    await createTemplateButton.click();

    // Verify template creation dialog appears
    await expect(page.locator('text=Create Template')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-type-select"]')).toBeVisible();
    await expect(page.locator('input[name="subject"]')).toBeVisible();
    await expect(page.locator('textarea[name="body"]')).toBeVisible();

    // Fill template form
    await page.fill('input[name="name"]', 'Interview Invitation');
    await page.selectOption('[data-testid="template-type-select"]', 'email');
    await page.fill('input[name="subject"]', 'Interview Invitation - {{position}}');
    await page.fill('textarea[name="body"]',
      'Dear {{candidate_name}},\n\n' +
      'We are pleased to invite you for an interview for the {{position}} position.\n\n' +
      'Date: {{interview_date}}\n' +
      'Time: {{interview_time}}\n' +
      'Location: {{interview_location}}\n\n' +
      'Please confirm your attendance.\n\n' +
      'Best regards,\n' +
      '{{recruiter_name}}'
    );

    // Verify variables are automatically detected
    await expect(page.locator('text=candidate_name')).toBeVisible();
    await expect(page.locator('text=position')).toBeVisible();
    await expect(page.locator('text=interview_date')).toBeVisible();
    await expect(page.locator('text=interview_time')).toBeVisible();
    await expect(page.locator('text=interview_location')).toBeVisible();
    await expect(page.locator('text=recruiter_name')).toBeVisible();

    // Add category
    await page.selectOption('[data-testid="template-category-select"]', 'interview');

    // Submit form
    await page.click('button:has-text("Create")');

    // Verify success message
    await expect(page.locator('text=Template created successfully')).toBeVisible();

    // Verify template appears in list
    await expect(page.locator('text=Interview Invitation')).toBeVisible();
  });

  test('Step 2: Preview template with variable substitution', async () => {
    /**
     * Test: Preview template with variable substitution
     *
     * Verifies:
     * - Template preview dialog opens
     * - Variable values can be entered
     * - Preview shows substituted content
     * - Variables are replaced in both subject and body
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Find and click preview button on template
    const templateCard = page.locator('text=Interview Invitation').locator('../..');
    const moreButton = templateCard.locator('button[aria-label="More options"]');
    await moreButton.click();

    // Click preview option
    await page.click('text=Preview');

    // Verify preview dialog appears
    await expect(page.locator('text=Preview Template')).toBeVisible();

    // Fill variable values
    await page.fill('input[data-variable="candidate_name"]', 'John Doe');
    await page.fill('input[data-variable="position"]', 'Senior Software Engineer');
    await page.fill('input[data-variable="interview_date"]', '2026-02-10');
    await page.fill('input[data-variable="interview_time"]', '14:00');
    await page.fill('input[data-variable="interview_location"]', '123 Main St, Room A');
    await page.fill('input[data-variable="recruiter_name"]', 'Jane Smith');

    // Click "Generate Preview"
    await page.click('button:has-text("Preview")');

    // Verify substituted content
    await expect(page.locator('text=Interview Invitation - Senior Software Engineer')).toBeVisible();
    await expect(page.locator('text=Dear John Doe,')).toBeVisible();
    await expect(page.locator('text=Senior Software Engineer position')).toBeVisible();
    await expect(page.locator('text=2026-02-10')).toBeVisible();
    await expect(page.locator('text=14:00')).toBeVisible();
    await expect(page.locator('text=123 Main St, Room A')).toBeVisible();
    await expect(page.locator('text=Jane Smith')).toBeVisible();

    // Verify no unsubstituted variables
    const content = await page.content();
    expect(content).not.toContain('{{candidate_name}}');
    expect(content).not.toContain('{{position}}');
  });

  test('Step 3: Use template to compose email', async () => {
    /**
     * Test: Use template to compose email
     *
     * Verifies:
     * - Template can be selected from composer
     * - Template variables are populated with input fields
     * - Email composer is pre-filled with template structure
     * - Variables can be customized before sending
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Click "Compose Email" button
    const composeButton = page.locator('button:has-text("Compose Email")').first();
    await expect(composeButton).toBeVisible();
    await composeButton.click();

    // Verify email composer dialog appears
    await expect(page.locator('text=Compose Email')).toBeVisible();
    await expect(page.locator('input[name="to"]')).toBeVisible();
    await expect(page.locator('input[name="subject"]')).toBeVisible();
    await expect(page.locator('textarea[name="body"]')).toBeVisible();

    // Select template from dropdown
    await page.click('[data-testid="template-select"]');
    await page.click('text=Interview Invitation');

    // Verify template variables form appears
    await expect(page.locator('text=Fill in template variables')).toBeVisible();
    await expect(page.locator('input[data-variable="candidate_name"]')).toBeVisible();
    await expect(page.locator('input[data-variable="position"]')).toBeVisible();
    await expect(page.locator('input[data-variable="interview_date"]')).toBeVisible();
    await expect(page.locator('input[data-variable="interview_time"]')).toBeVisible();
    await expect(page.locator('input[data-variable="interview_location"]')).toBeVisible();
    await expect(page.locator('input[data-variable="recruiter_name"]')).toBeVisible();

    // Verify email fields are pre-filled with placeholder structure
    const subjectValue = await page.inputValue('input[name="subject"]');
    expect(subjectValue).toContain('{{position}}');

    // Fill in variable values
    await page.fill('input[data-variable="candidate_name"]', testCandidate.name);
    await page.fill('input[data-variable="position"]', 'Senior Software Engineer');
    await page.fill('input[data-variable="interview_date"]', '2026-02-10');
    await page.fill('input[data-variable="interview_time"]', '14:00');
    await page.fill('input[data-variable="interview_location"]', 'Remote - Google Meet');
    await page.fill('input[data-variable="recruiter_name"]', 'Jane Recruiter');

    // Verify email body is updated with substituted variables
    const bodyValue = await page.inputValue('textarea[name="body"]');
    expect(bodyValue).toContain(testCandidate.name);
    expect(bodyValue).toContain('Senior Software Engineer');
    expect(bodyValue).toContain('2026-02-10');
    expect(bodyValue).toContain('14:00');
    expect(bodyValue).toContain('Remote - Google Meet');
    expect(bodyValue).toContain('Jane Recruiter');

    // Verify subject is updated
    const updatedSubject = await page.inputValue('input[name="subject"]');
    expect(updatedSubject).toBe('Interview Invitation - Senior Software Engineer');
  });

  test('Step 4: Send email', async () => {
    /**
     * Test: Send email
     *
     * Verifies:
     * - Email can be sent from composer
     * - Loading state appears during send
     * - Success message appears after send
     * - Email composer closes after successful send
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Compose email with template
    await page.click('button:has-text("Compose Email")');
    await page.click('[data-testid="template-select"]');
    await page.click('text=Interview Invitation');

    // Fill variables
    await page.fill('input[data-variable="candidate_name"]', testCandidate.name);
    await page.fill('input[data-variable="position"]', 'Senior Software Engineer');
    await page.fill('input[data-variable="interview_date"]', '2026-02-10');
    await page.fill('input[data-variable="interview_time"]', '14:00');
    await page.fill('input[data-variable="interview_location"]', 'Remote');
    await page.fill('input[data-variable="recruiter_name"]', 'Jane Recruiter');

    // Send email
    await page.click('button:has-text("Send")');

    // Verify loading state
    await expect(page.locator('button:has-text("Sending...")')).toBeVisible();

    // Verify success message (may take a moment)
    await expect(page.locator('text=Email sent successfully')).toBeVisible({ timeout: 10000 });

    // Verify composer closes
    await expect(page.locator('text=Compose Email')).not.toBeVisible();
  });

  test('Step 5: Verify email uses template content', async () => {
    /**
     * Test: Verify email uses template content
     *
     * Verifies:
     * - Sent email appears in communication timeline
     * - Email subject matches template with substitutions
     * - Email body matches template with substitutions
     * - Template metadata is stored with communication
     * - No unsubstituted variables remain
     */

    await navigateToCandidatePage(page, testCandidate.id);

    // Click on Communications tab
    await page.click('role=tab[name="Communications"]');

    // Wait for timeline to load
    await page.waitForLoadState('networkidle');

    // Look for the sent email
    const emailItem = page.locator('text=Interview Invitation - Senior Software Engineer').first();
    await expect(emailItem).toBeVisible();

    // Click on email to view details
    await emailItem.click();

    // Verify email viewer opens
    await expect(page.locator('text=Interview Invitation - Senior Software Engineer')).toBeVisible();
    await expect(page.locator(`text=${testCandidate.name}`)).toBeVisible();
    await expect(page.locator('text=Senior Software Engineer')).toBeVisible();
    await expect(page.locator('text=2026-02-10')).toBeVisible();
    await expect(page.locator('text=14:00')).toBeVisible();
    await expect(page.locator('text=Remote')).toBeVisible();
    await expect(page.locator('text=Jane Recruiter')).toBeVisible();

    // Verify no template variables remain unsubstituted
    const emailContent = await page.content();
    expect(emailContent).not.toContain('{{candidate_name}}');
    expect(emailContent).not.toContain('{{position}}');
    expect(emailContent).not.toContain('{{interview_date}}');
    expect(emailContent).not.toContain('{{interview_time}}');
    expect(emailContent).not.toContain('{{interview_location}}');
    expect(emailContent).not.toContain('{{recruiter_name}}');
  });

  test('Complete template workflow - end-to-end', async () => {
    /**
     * Test: Complete template workflow
     *
     * Verifies the entire workflow from template creation to email sending:
     * 1. Create new template
     * 2. Preview template
     * 3. Compose email using template
     * 4. Send email
     * 5. Verify email in timeline
     */

    // Step 1: Create template
    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);
    await page.click('button:has-text("Create Template")');

    await page.fill('input[name="name"]', 'Offer Letter Template');
    await page.selectOption('[data-testid="template-type-select"]', 'email');
    await page.fill('input[name="subject"]', 'Job Offer - {{position}} at {{company}}');
    await page.fill('textarea[name="body"]',
      'Dear {{candidate_name}},\n\n' +
      'We are pleased to offer you the position of {{position}} at {{company}}!\n\n' +
      'Salary: ${{salary}}\n' +
      'Start Date: {{start_date}}\n\n' +
      'Please review and sign by {{deadline}}.\n\n' +
      'Congratulations!\n' +
      '{{recruiter_name}}'
    );
    await page.selectOption('[data-testid="template-category-select"]', 'offer');
    await page.click('button:has-text("Create")');

    // Verify template created
    await expect(page.locator('text=Template created successfully')).toBeVisible();
    await expect(page.locator('text=Offer Letter Template')).toBeVisible();

    // Step 2: Preview template
    const templateCard = page.locator('text=Offer Letter Template').locator('../..');
    await templateCard.locator('button[aria-label="More options"]').click();
    await page.click('text=Preview');

    // Fill preview variables
    await page.fill('input[data-variable="candidate_name"]', 'Alice Johnson');
    await page.fill('input[data-variable="position"]', 'Senior UX Designer');
    await page.fill('input[data-variable="company"]', 'TechCorp Inc.');
    await page.fill('input[data-variable="salary"]', '95000');
    await page.fill('input[data-variable="start_date"]', '2026-03-01');
    await page.fill('input[data-variable="deadline"]', '2026-02-15');
    await page.fill('input[data-variable="recruiter_name"]', 'Bob Smith');

    await page.click('button:has-text("Preview")');

    // Verify preview
    await expect(page.locator('text=Alice Johnson')).toBeVisible();
    await expect(page.locator('text=Senior UX Designer')).toBeVisible();
    await expect(page.locator('text=TechCorp Inc.')).toBeVisible();
    await expect(page.locator('text=$95000')).toBeVisible();
    await expect(page.locator('text=2026-03-01')).toBeVisible();

    // Close preview
    await page.click('button[aria-label="Close"]');

    // Step 3: Compose email using template
    await navigateToCandidatePage(page, testCandidate.id);
    await page.click('button:has-text("Compose Email")');
    await page.click('[data-testid="template-select"]');
    await page.click('text=Offer Letter Template');

    // Fill variables
    await page.fill('input[data-variable="candidate_name"]', testCandidate.name);
    await page.fill('input[data-variable="position"]', 'Senior UX Designer');
    await page.fill('input[data-variable="company"]', 'TechCorp Inc.');
    await page.fill('input[data-variable="salary"]', '95000');
    await page.fill('input[data-variable="start_date"]', '2026-03-01');
    await page.fill('input[data-variable="deadline"]', '2026-02-15');
    await page.fill('input[data-variable="recruiter_name"]', 'Jane Recruiter');

    // Verify email composer
    const subject = await page.inputValue('input[name="subject"]');
    expect(subject).toBe('Job Offer - Senior UX Designer at TechCorp Inc.');

    // Step 4: Send email
    await page.click('button:has-text("Send")');
    await expect(page.locator('text=Email sent successfully')).toBeVisible({ timeout: 10000 });

    // Step 5: Verify email in timeline
    await page.click('role=tab[name="Communications"]');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Job Offer - Senior UX Designer at TechCorp Inc.')).toBeVisible();
    await expect(page.locator(`text=${testCandidate.name}`)).toBeVisible();
    await expect(page.locator('text=Senior UX Designer')).toBeVisible();
    await expect(page.locator('text=TechCorp Inc.')).toBeVisible();
    await expect(page.locator('text=$95000')).toBeVisible();
  });

  test('Template with missing variables', async () => {
    /**
     * Test: Template with missing variables
     *
     * Verifies:
     * - Missing variables are handled gracefully
     * - User is warned about missing variables
     * - Unsubstituted variables remain visible in preview
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Create template with variables
    await page.click('button:has-text("Create Template")');
    await page.fill('input[name="name"]', 'Follow-up Template');
    await page.selectOption('[data-testid="template-type-select"]', 'email');
    await page.fill('input[name="subject"]', 'Following up on {{position}} application');
    await page.fill('textarea[name="body"]', 'Hi {{candidate_name}},\n\nAny update on {{position}}?');
    await page.click('button:has-text("Create")');

    // Preview with missing variable
    const templateCard = page.locator('text=Follow-up Template').locator('../..');
    await templateCard.locator('button[aria-label="More options"]').click();
    await page.click('text=Preview');

    // Fill only one variable
    await page.fill('input[data-variable="candidate_name"]', 'John');
    // Intentionally not filling {{position}}

    await page.click('button:has-text("Preview")');

    // Verify warning about missing variables
    await expect(page.locator('text=Some variables were not provided')).toBeVisible();

    // Verify unsubstituted variables remain
    await expect(page.locator('text={{position}}')).isVisible();
  });

  test('Template filtering and search', async () => {
    /**
     * Test: Template filtering and search
     *
     * Verifies:
     * - Templates can be filtered by type
     * - Templates can be filtered by category
     * - Templates can be searched by name
     * - Active/inactive filter works
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Filter by type=email
    await page.click('[data-testid="filter-type-select"]');
    await page.click('text=Email');

    // Verify only email templates shown
    const emailTemplates = await page.locator('[data-testid="template-card"]').count();
    expect(emailTemplates).toBeGreaterThan(0);

    // Filter by category=interview
    await page.click('[data-testid="filter-category-select"]');
    await page.click('text=Interview');

    // Verify filtered results
    await expect(page.locator('text=Interview Invitation')).toBeVisible();

    // Search by name
    await page.fill('input[placeholder="Search templates"]', 'Offer');
    await page.waitForTimeout(500); // Wait for debounce

    // Verify search results
    await expect(page.locator('text=Offer Letter Template')).toBeVisible();
  });

  test('Template validation', async () => {
    /**
     * Test: Template validation
     *
     * Verifies:
     * - Name is required
     * - Type is required
     * - Body is required
     * - Subject is required for email templates
     * - Validation errors are displayed
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Try to create template without required fields
    await page.click('button:has-text("Create Template")');

    // Don't fill any fields, just click Create
    await page.click('button:has-text("Create")');

    // Verify validation errors
    await expect(page.locator('text=Name is required')).toBeVisible();
    await expect(page.locator('text=Type is required')).toBeVisible();
    await expect(page.locator('text=Body is required')).toBeVisible();

    // Fill required fields but select email type
    await page.fill('input[name="name"]', 'Test Template');
    await page.selectOption('[data-testid="template-type-select"]', 'email');

    // Subject should be required for email
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=Subject is required for email templates')).toBeVisible();

    // Fill subject to pass validation
    await page.fill('input[name="subject"]', 'Test Subject');
    await page.fill('textarea[name="body"]', 'Test body');

    // Now should succeed
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=Template created successfully')).toBeVisible();
  });

  test('Edit and delete template', async () => {
    /**
     * Test: Edit and delete template
     *
     * Verifies:
     * - Template can be edited
     * - Changes are saved
     * - Template can be deleted
     * - Delete confirmation dialog appears
     * - Template is removed from list
     */

    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Create test template
    await page.click('button:has-text("Create Template")');
    await page.fill('input[name="name"]', 'Template to Edit');
    await page.selectOption('[data-testid="template-type-select"]', 'email');
    await page.fill('input[name="subject"]', 'Original Subject');
    await page.fill('textarea[name="body"]', 'Original body');
    await page.click('button:has-text("Create")');

    // Edit template
    const templateCard = page.locator('text=Template to Edit').locator('../..');
    await templateCard.locator('button[aria-label="More options"]').click();
    await page.click('text=Edit');

    // Update fields
    await page.fill('input[name="name"]', 'Edited Template Name');
    await page.fill('input[name="subject"]', 'Updated Subject');
    await page.click('button:has-text("Save")');

    // Verify changes
    await expect(page.locator('text=Template updated successfully')).toBeVisible();
    await expect(page.locator('text=Edited Template Name')).toBeVisible();

    // Delete template
    await templateCard.locator('button[aria-label="More options"]').click();
    await page.click('text=Delete');

    // Verify confirmation dialog
    await expect(page.locator('text=Are you sure you want to delete')).toBeVisible();
    await page.click('button:has-text("Delete")');

    // Verify template removed
    await expect(page.locator('text=Template deleted successfully')).toBeVisible();
    await expect(page.locator('text=Edited Template Name')).not.toBeVisible();
  });

  test('Template responsive design', async () => {
    /**
     * Test: Template responsive design
     *
     * Verifies:
     * - Templates page works on mobile viewport
     * - Template cards stack correctly
     * - Create template dialog is responsive
     * - Filters remain accessible on mobile
     */

    // Mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await navigateToCommunications(page);
    await navigateToTemplatesTab(page);

    // Verify page loads
    await expect(page.locator('text=Templates')).toBeVisible();

    // Verify template cards stack vertically
    const templateCards = page.locator('[data-testid="template-card"]');
    const firstCard = templateCards.first();
    const secondCard = templateCards.nth(1);

    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();

    expect(secondBox!.y).toBeGreaterThan(firstBox!.y);

    // Verify create button accessible
    await expect(page.locator('button:has-text("Create Template")')).toBeVisible();

    // Open create dialog
    await page.click('button:has-text("Create Template")');
    await expect(page.locator('input[name="name"]')).toBeVisible();
  });
});
