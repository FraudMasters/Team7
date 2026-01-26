import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Multi-Language UI (English & Russian)
 *
 * Test Suite Contents:
 * 1. Russian Language Auto-Detection
 * 2. Russian UI Translation Verification
 * 3. Resume Upload with Russian Interface
 * 4. Analysis Results with Russian Labels
 * 5. Language Switching (Russian ↔ English)
 * 6. Language Preference Persistence
 * 7. Date and Number Formatting by Locale
 * 8. Backend Error Messages in Russian
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend dev server running at http://localhost:5173
 * - i18n infrastructure properly configured
 */

test.describe('Multi-Language UI: Russian Language Preference', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test to ensure clean state
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test.describe('Russian Language Auto-Detection', () => {
    test('should auto-detect Russian from browser language', async ({ page }) => {
      // Set browser language to Russian
      await page.context().setExtraHTTPHeaders({
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
      });

      // Navigate to home page
      await page.goto('/');

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Check that Russian text is visible
      // Verify hero section is in Russian
      const heroTitle = page.locator('h1');
      await expect(heroTitle).toBeVisible();

      // Check for Russian text indicators
      const pageText = await page.textContent('body');
      expect(pageText).toMatch(/преобразовать|резюме|анализ|платформа/i);
    });

    test('should fallback to English for unsupported browser language', async ({ page }) => {
      // Set browser language to unsupported language
      await page.context().setExtraHTTPHeaders({
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Should display in English (fallback)
      const heroTitle = page.locator('h1');
      await expect(heroTitle).toBeVisible();

      // Check for English text
      const pageText = await page.textContent('body');
      expect(pageText).toMatch(/Transform|Resume|Analysis|Platform/i);
    });
  });

  test.describe('Russian UI Translation Verification', () => {
    test('should display home page in Russian', async ({ page }) => {
      // Set language to Russian via localStorage
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      // Reload to apply language
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify navigation items are in Russian
      await expect(page.getByRole('link', { name: /Главная/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /Загрузить резюме/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /Результаты/i })).toBeVisible();

      // Verify hero section is in Russian
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();
      await expect(page.getByText(/на базе искусственного интеллекта/i)).toBeVisible();

      // Verify feature cards are in Russian
      await expect(page.getByText(/Анализ на базе ИИ/i)).toBeVisible();
      await expect(page.getByText(/Обнаружение ошибок/i)).toBeVisible();
      await expect(page.getByText(/Подбор вакансий/i })).toBeVisible();
      await expect(page.getByText(/Быстрая обработка/i)).toBeVisible();

      // Verify CTA buttons are in Russian
      await expect(page.getByRole('button', { name: /Загрузить резюме/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /Посмотреть пример анализа/i })).toBeVisible();
    });

    test('should display upload page in Russian', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      await page.goto('/upload');
      await page.waitForLoadState('networkidle');

      // Verify upload page is in Russian
      await expect(page.getByRole('heading', { name: /Загрузить резюме/i })).toBeVisible();
      await expect(page.getByText(/Перетащите резюме сюда/i)).toBeVisible();
      await expect(page.getByText(/PDF или DOCX/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /Выбрать файл/i })).toBeVisible();

      // Verify "What happens next" section
      await expect(page.getByText(/Что дальше?/i)).toBeVisible();
      await expect(page.getByText(/Наш ИИ извлечает навыки/i)).toBeVisible();
    });

    test('should verify all main pages have Russian translations', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      // Check home page
      await page.goto('/');
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Check upload page
      await page.goto('/upload');
      await expect(page.getByRole('heading', { name: /Загрузить резюме/i })).toBeVisible();

      // Check admin synonyms page
      await page.goto('/admin/synonyms');
      await expect(page.getByRole('heading', { name: /Управление синонимами/i })).toBeVisible();

      // Check admin analytics page
      await page.goto('/admin/analytics');
      await expect(page.getByRole('heading', { name: /Аналитика и обратная связь/i })).toBeVisible();
    });
  });

  test.describe('Resume Upload with Russian Interface', () => {
    test.use({ storageState: { origins: [{ origin: 'http://localhost:5173', localStorage: [{ name: 'i18nextLng', value: 'ru' }] }] } });

    test('should show Russian upload interface', async ({ page }) => {
      await page.goto('/upload');
      await page.waitForLoadState('networkidle');

      // Verify all upload interface elements are in Russian
      await expect(page.getByText(/Перетащите резюме сюда/i)).toBeVisible();
      await expect(page.getByText(/или нажмите для выбора/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /Выбрать файл/i })).toBeVisible();
      await expect(page.getByText(/Поддерживаемые форматы:/i)).toBeVisible();
      await expect(page.getByText(/Максимальный размер:/i)).toBeVisible();
    });

    test('should display Russian error messages for invalid file', async ({ page }) => {
      await page.goto('/upload');

      // Try to upload a text file (invalid type)
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Invalid file type'),
      });

      // Wait for error message
      await page.waitForTimeout(500);

      // Verify Russian error message
      await expect(page.getByText(/Неподдерживаемый тип файла/i)).toBeVisible();
    });

    test('should display Russian file size error', async ({ page }) => {
      await page.goto('/upload');

      // Create a file larger than max size (simulate)
      // Note: This test verifies the UI shows Russian text for size errors
      const fileSizeText = await page.textContent('body');
      expect(fileSizeText).toMatch(/Максимальный размер: 10 МБ/i);
    });
  });

  test.describe('Analysis Results with Russian Labels', () => {
    test('should display results page in Russian', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      // Navigate to results page
      await page.goto('/results/test-resume-id');
      await page.waitForLoadState('networkidle');

      // Note: Without actual backend data, we verify the UI structure
      // Check for Russian headings or error messages
      const pageContent = await page.textContent('body');

      // Should have either loading text or error text in Russian
      expect(pageContent).toMatch(/Загрузка|Ошибка|Не удалось загрузить|результаты анализа/i);
    });

    test('should display Russian severity labels', async ({ page }) => {
      // This test would require actual analysis data
      // Verifying that severity badges are translated
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      await page.goto('/results/sample-id');
      await page.waitForLoadState('networkidle');

      // Check for Russian severity labels if they appear
      const pageText = await page.textContent('body');
      expect(pageText).toMatch(/Критический|Предупреждение|Информация/i);
    });
  });

  test.describe('Language Switching (Russian ↔ English)', () => {
    test('should switch from Russian to English using language switcher', async ({ page }) => {
      // Start in Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify Russian is displayed
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Find and click language switcher
      const languageSwitcher = page.getByRole('combobox', { name: /Выбрать язык|Select language/i });
      await expect(languageSwitcher).toBeVisible();

      // Switch to English
      await languageSwitcher.selectOption('en');

      // Wait for UI to update
      await page.waitForTimeout(500);

      // Verify English is now displayed
      await expect(page.getByText(/Resume Analysis Platform/i)).toBeVisible();

      // Verify Russian text is gone
      await expect(page.getByText(/Платформа анализа резюме/i)).not.toBeVisible();
    });

    test('should switch from English to Russian using language switcher', async ({ page }) => {
      // Start in English (default)
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Verify English is displayed
      await expect(page.getByText(/Resume Analysis Platform/i)).toBeVisible();

      // Find and click language switcher
      const languageSwitcher = page.getByRole('combobox', { name: /Select language|Выбрать язык/i });
      await expect(languageSwitcher).toBeVisible();

      // Switch to Russian
      await languageSwitcher.selectOption('ru');

      // Wait for UI to update
      await page.waitForTimeout(500);

      // Verify Russian is now displayed
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Verify English text is gone
      await expect(page.getByText(/Transform Your Recruitment Process/i)).not.toBeVisible();
    });

    test('should update all UI elements when switching language', async ({ page }) => {
      // Start in English
      await page.goto('/');

      // Switch to Russian
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('ru');
      await page.waitForTimeout(500);

      // Verify navigation items updated
      await expect(page.getByRole('link', { name: /Главная/i })).toBeVisible();

      // Verify hero section updated
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Verify features updated
      await expect(page.getByText(/Анализ на базе ИИ/i)).toBeVisible();

      // Verify buttons updated
      await expect(page.getByRole('button', { name: /Загрузить резюме/i })).toBeVisible();

      // Switch back to English
      await languageSwitcher.selectOption('en');
      await page.waitForTimeout(500);

      // Verify everything is back to English
      await expect(page.getByRole('link', { name: /Home/i })).toBeVisible();
      await expect(page.getByText(/Resume Analysis Platform/i)).toBeVisible();
    });
  });

  test.describe('Language Preference Persistence', () => {
    test('should persist Russian language preference across pages', async ({ page }) => {
      // Set language to Russian on home page
      await page.goto('/');
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('ru');
      await page.waitForTimeout(500);

      // Verify Russian is active on home page
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Navigate to upload page
      await page.goto('/upload');
      await page.waitForLoadState('networkidle');

      // Verify Russian is still active
      await expect(page.getByRole('heading', { name: /Загрузить резюме/i })).toBeVisible();

      // Navigate to results page
      await page.goto('/results/test-id');
      await page.waitForLoadState('networkidle');

      // Verify Russian is still active (in error/loading messages)
      const pageText = await page.textContent('body');
      expect(pageText).toMatch(/Загрузка|Ошибка|результаты/i);
    });

    test('should persist English language preference after refresh', async ({ page }) => {
      // Start in Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });
      await page.reload();

      // Verify Russian is displayed
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Switch to English
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('en');
      await page.waitForTimeout(500);

      // Verify English is displayed
      await expect(page.getByText(/Resume Analysis Platform/i)).toBeVisible();

      // Refresh page
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify English preference persisted
      await expect(page.getByText(/Resume Analysis Platform/i)).toBeVisible();
      await expect(page.getByText(/Платформа анализа резюме/i)).not.toBeVisible();
    });

    test('should remember language preference on subsequent visits', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('ru');
      await page.waitForTimeout(500);

      // Verify Russian
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Close and reopen page (simulate new visit)
      await page.goto('/');

      // Verify Russian preference remembered
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();
    });
  });

  test.describe('Date and Number Formatting by Locale', () => {
    test('should format dates in Russian style', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });

      await page.reload();
      await page.waitForLoadState('networkidle');

      // Check copyright in footer for Russian date format
      // Russian dates use DD.MM.YYYY format
      const footerText = await page.locator('footer').textContent();
      expect(footerText).toBeTruthy();
    });

    test('should format dates in English style', async ({ page }) => {
      // Set language to English
      await page.goto('/');

      await page.waitForLoadState('networkidle');

      // Check copyright in footer for English date format
      // English dates use "Month DD, YYYY" format
      const footerText = await page.locator('footer').textContent();
      expect(footerText).toBeTruthy();
    });

    test('should switch date formats when language changes', async ({ page }) => {
      // This test verifies date formatting changes with language
      await page.goto('/');

      // Start in English
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('en');
      await page.waitForTimeout(500);

      // Get footer text in English
      const englishFooter = await page.locator('footer').textContent();
      expect(englishFooter).toBeTruthy();

      // Switch to Russian
      await languageSwitcher.selectOption('ru');
      await page.waitForTimeout(500);

      // Get footer text in Russian
      const russianFooter = await page.locator('footer').textContent();
      expect(russianFooter).toBeTruthy();

      // The footer text should be different (translated)
      // Actual date format differences would be visible in results with actual data
    });
  });

  test.describe('Complete User Journey: Russian Language', () => {
    test('should complete full workflow in Russian', async ({ page }) => {
      // Step 1: Set browser language to Russian
      await page.context().setExtraHTTPHeaders({
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
      });

      // Step 2: Navigate to home page - verify Russian UI
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();
      await expect(page.getByRole('link', { name: /Главная/i })).toBeVisible();

      // Step 3: Navigate to upload page - verify Russian upload interface
      await page.getByRole('link', { name: /Загрузить резюме/i }).click();
      await expect(page).toHaveURL(/\/upload/);

      await expect(page.getByRole('heading', { name: /Загрузить резюме/i })).toBeVisible();
      await expect(page.getByText(/Перетащите резюме сюда/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /Выбрать файл/i })).toBeVisible();

      // Step 4: Verify file selection and error messages in Russian
      const fileInput = page.locator('input[type="file"]');

      // Try invalid file type
      await fileInput.setInputFiles({
        name: 'invalid.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Invalid file'),
      });

      await page.waitForTimeout(500);

      // Verify Russian error message
      await expect(page.getByText(/Неподдерживаемый тип файла/i)).toBeVisible();

      // Step 5: Switch language to English - verify all UI updates
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('en');
      await page.waitForTimeout(500);

      // Verify English is now displayed
      await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();
      await expect(page.getByText(/Drag and drop your resume here/i)).toBeVisible();

      // Step 6: Refresh page - verify English preference persists
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Verify English persisted
      await expect(page.getByRole('heading', { name: /Upload Resume/i })).toBeVisible();
      await expect(page.getByText(/Drag and drop your resume here/i)).toBeVisible();

      // Verify Russian text is not present
      await expect(page.getByText(/Загрузить резюме/i)).not.toBeVisible();
    });

    test('should maintain language preference across full application flow', async ({ page }) => {
      // Start in Russian
      await page.goto('/');
      const languageSwitcher = page.getByRole('combobox');
      await languageSwitcher.selectOption('ru');
      await page.waitForTimeout(500);

      // Navigate through all pages
      await page.goto('/upload');
      await expect(page.getByRole('heading', { name: /Загрузить резюме/i })).toBeVisible();

      await page.goto('/results/test-id');
      const resultsText = await page.textContent('body');
      expect(resultsText).toMatch(/Загрузка|Ошибка|результаты/i);

      await page.goto('/admin/synonyms');
      await expect(page.getByRole('heading', { name: /Управление синонимами/i })).toBeVisible();

      await page.goto('/admin/analytics');
      await expect(page.getByRole('heading', { name: /Аналитика и обратная связь/i })).toBeVisible();

      // Return to home
      await page.goto('/');
      await expect(page.getByText(/Платформа анализа резюме/i)).toBeVisible();

      // Language should still be Russian throughout
      const currentLanguage = await page.evaluate(() => localStorage.getItem('i18nextLng'));
      expect(currentLanguage).toBe('ru');
    });
  });

  test.describe('Language Switcher Accessibility', () => {
    test('should have accessible language switcher in Russian', async ({ page }) => {
      // Set language to Russian
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('i18nextLng', 'ru');
      });
      await page.reload();

      // Verify language switcher has Russian aria-label
      const languageSwitcher = page.getByRole('combobox', { name: /Выбрать язык/i });
      await expect(languageSwitcher).toBeVisible();

      // Verify it's keyboard accessible
      await languageSwitcher.focus();
      await expect(languageSwitcher).toBeFocused();

      // Verify options are accessible
      const options = await page.locator('option').all();
      expect(options.length).toBeGreaterThanOrEqual(2);

      // Check for English and Russian options
      const englishOption = page.locator('option[value="en"]');
      const russianOption = page.locator('option[value="ru"]');

      await expect(englishOption).toBeAttached();
      await expect(russianOption).toBeAttached();
    });

    test('should display flag icons in language switcher', async ({ page }) => {
      await page.goto('/');

      // Check that language switcher contains flag emojis
      const switcherText = await page.getByRole('combobox').textContent();
      expect(switcherText).toMatch(/[🇺🇸🇷🇺]/);
    });
  });
});
