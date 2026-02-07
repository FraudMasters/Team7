/**
 * Tests for Configuration Service
 *
 * Tests the centralized configuration management system including
 * type-safe config loading, validation, and helper functions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  config,
  reloadConfig,
  getEnvironment,
  isDevelopment,
  isProduction,
  isFeatureEnabled,
} from './index';
import { validateConfig } from './validation';
import type { Config, Environment } from './types';

// Mock import.meta.env for testing
const mockEnv = {
  VITE_API_URL: 'http://localhost:8000',
  VITE_API_TIMEOUT: '120000',
  VITE_API_RETRY_ENABLED: 'true',
  VITE_API_RETRY_MAX_ATTEMPTS: '3',
  VITE_APP_TITLE: 'Resume Analysis Platform',
  VITE_APP_DESCRIPTION: 'AI-powered resume analysis platform',
  VITE_APP_VERSION: '1.0.0',
  VITE_ENVIRONMENT: 'development',
  VITE_ENABLE_DARK_MODE: 'false',
  VITE_ENABLE_ANALYTICS: 'false',
  VITE_MAX_UPLOAD_SIZE_MB: '10',
  VITE_ALLOWED_FILE_TYPES: '.pdf,.docx',
  VITE_DEFAULT_LANGUAGE: 'en',
  VITE_SUPPORTED_LANGUAGES: 'en,ru',
  VITE_THEME: 'light',
  VITE_PRIMARY_COLOR: '#1976d2',
  VITE_SECONDARY_COLOR: '#dc004e',
  VITE_ITEMS_PER_PAGE: '10',
  VITE_MAX_RESULTS: '100',
  VITE_SHOW_PROCESSING_TIME: 'true',
  VITE_ENABLE_AUTH: 'false',
  VITE_AUTH_PROVIDER: 'jwt',
  VITE_TOKEN_STORAGE: 'localStorage',
  VITE_SESSION_TIMEOUT_MINUTES: '60',
  VITE_NOTIFICATION_DURATION: '5000',
  VITE_NOTIFICATION_POSITION: 'top-right',
  VITE_CACHE_DURATION: '300000',
  VITE_CLEAR_CACHE_ON_LOGOUT: 'true',
  VITE_MAX_REQUESTS_PER_MINUTE: '60',
  VITE_SITE_NAME: 'Resume Analysis Platform',
  VITE_SITE_URL: 'http://localhost:5173',
  VITE_DEFAULT_OG_IMAGE: '/og-image.png',
  VITE_TWITTER_CARD_TYPE: 'summary_large_image',
  VITE_DATE_FORMAT: 'medium',
  VITE_TIME_FORMAT: 'short',
  VITE_TIMEZONE: 'UTC',
};

describe('config', () => {
  describe('config object', () => {
    it('should be defined', () => {
      expect(config).toBeDefined();
      expect(config).not.toBeNull();
    });

    it('should have all required configuration sections', () => {
      expect(config).toHaveProperty('api');
      expect(config).toHaveProperty('app');
      expect(config).toHaveProperty('features');
      expect(config).toHaveProperty('upload');
      expect(config).toHaveProperty('ui');
      expect(config).toHaveProperty('display');
      expect(config).toHaveProperty('resultsDisplay');
      expect(config).toHaveProperty('auth');
      expect(config).toHaveProperty('analytics');
      expect(config).toHaveProperty('errorTracking');
      expect(config).toHaveProperty('support');
      expect(config).toHaveProperty('notification');
      expect(config).toHaveProperty('cache');
      expect(config).toHaveProperty('rateLimit');
      expect(config).toHaveProperty('seo');
      expect(config).toHaveProperty('i18n');
    });
  });

  describe('api config', () => {
    it('should have correct API URL', () => {
      expect(config.api.url).toBeDefined();
      expect(typeof config.api.url).toBe('string');
      expect(config.api.url).toBeTruthy();
    });

    it('should have valid timeout value', () => {
      expect(config.api.timeout).toBeDefined();
      expect(typeof config.api.timeout).toBe('number');
      expect(config.api.timeout).toBeGreaterThan(0);
    });

    it('should have retry configuration', () => {
      expect(config.api.retryEnabled).toBeDefined();
      expect(typeof config.api.retryEnabled).toBe('boolean');
      expect(config.api.retryMaxAttempts).toBeDefined();
      expect(typeof config.api.retryMaxAttempts).toBe('number');
    });

    it('should have valid URL format', () => {
      expect(() => new URL(config.api.url)).not.toThrow();
    });
  });

  describe('app config', () => {
    it('should have application title', () => {
      expect(config.app.title).toBeDefined();
      expect(typeof config.app.title).toBe('string');
      expect(config.app.title.length).toBeGreaterThan(0);
    });

    it('should have application description', () => {
      expect(config.app.description).toBeDefined();
      expect(typeof config.app.description).toBe('string');
    });

    it('should have version', () => {
      expect(config.app.version).toBeDefined();
      expect(typeof config.app.version).toBe('string');
    });

    it('should have valid environment', () => {
      const validEnvironments: Environment[] = ['development', 'staging', 'production'];
      expect(validEnvironments).toContain(config.app.environment);
    });
  });

  describe('features config', () => {
    it('should have all feature flags as boolean', () => {
      const featureKeys = Object.keys(config.features) as Array<keyof typeof config.features>;
      featureKeys.forEach((key) => {
        expect(typeof config.features[key]).toBe('boolean');
      });
    });

    it('should have dark mode feature flag', () => {
      expect(config.features.enableDarkMode).toBeDefined();
      expect(typeof config.features.enableDarkMode).toBe('boolean');
    });

    it('should have analytics feature flag', () => {
      expect(config.features.enableAnalytics).toBeDefined();
      expect(typeof config.features.enableAnalytics).toBe('boolean');
    });
  });

  describe('upload config', () => {
    it('should have max upload size', () => {
      expect(config.upload.maxSizeMb).toBeDefined();
      expect(typeof config.upload.maxSizeMb).toBe('number');
      expect(config.upload.maxSizeMb).toBeGreaterThan(0);
    });

    it('should have allowed file types', () => {
      expect(config.upload.allowedFileTypes).toBeDefined();
      expect(Array.isArray(config.upload.allowedFileTypes)).toBe(true);
      expect(config.upload.allowedFileTypes.length).toBeGreaterThan(0);
    });

    it('should have file types starting with dot', () => {
      config.upload.allowedFileTypes.forEach((type) => {
        expect(type.startsWith('.')).toBe(true);
      });
    });
  });

  describe('ui config', () => {
    it('should have default language', () => {
      expect(config.ui.defaultLanguage).toBeDefined();
      expect(typeof config.ui.defaultLanguage).toBe('string');
      expect(config.ui.defaultLanguage.length).toBe(2);
    });

    it('should have supported languages including default', () => {
      expect(config.ui.supportedLanguages).toBeDefined();
      expect(Array.isArray(config.ui.supportedLanguages)).toBe(true);
      expect(config.ui.supportedLanguages).toContain(config.ui.defaultLanguage);
    });

    it('should have valid theme', () => {
      const validThemes = ['light', 'dark', 'auto'];
      expect(validThemes).toContain(config.ui.theme);
    });

    it('should have valid hex colors', () => {
      const hexColorRegex = /^#[0-9A-Fa-f]{6}$/;
      expect(hexColorRegex.test(config.ui.primaryColor)).toBe(true);
      expect(hexColorRegex.test(config.ui.secondaryColor)).toBe(true);
    });
  });

  describe('display config', () => {
    it('should have positive items per page', () => {
      expect(config.display.itemsPerPage).toBeDefined();
      expect(config.display.itemsPerPage).toBeGreaterThan(0);
    });

    it('should have max results >= items per page', () => {
      expect(config.display.maxResults).toBeGreaterThanOrEqual(config.display.itemsPerPage);
    });
  });

  describe('auth config', () => {
    it('should have valid provider', () => {
      const validProviders = ['jwt', 'oauth', 'auth0'];
      expect(validProviders).toContain(config.auth.provider);
    });

    it('should have valid token storage', () => {
      const validStorage = ['localStorage', 'sessionStorage', 'cookie'];
      expect(validStorage).toContain(config.auth.tokenStorage);
    });

    it('should have positive session timeout', () => {
      expect(config.auth.sessionTimeoutMinutes).toBeGreaterThan(0);
    });
  });

  describe('notification config', () => {
    it('should have positive duration', () => {
      expect(config.notification.duration).toBeDefined();
      expect(config.notification.duration).toBeGreaterThan(0);
    });

    it('should have valid position', () => {
      const validPositions = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
      expect(validPositions).toContain(config.notification.position);
    });
  });

  describe('cache config', () => {
    it('should have non-negative duration', () => {
      expect(config.cache.duration).toBeGreaterThanOrEqual(0);
    });
  });

  describe('rate limit config', () => {
    it('should have positive max requests', () => {
      expect(config.rateLimit.maxRequestsPerMinute).toBeGreaterThan(0);
    });
  });

  describe('seo config', () => {
    it('should have site name', () => {
      expect(config.seo.siteName).toBeDefined();
      expect(config.seo.siteName.length).toBeGreaterThan(0);
    });

    it('should have valid site URL', () => {
      expect(() => new URL(config.seo.siteUrl)).not.toThrow();
    });

    it('should have valid Twitter card type', () => {
      const validTypes = ['summary', 'summary_large_image'];
      expect(validTypes).toContain(config.seo.twitterCardType);
    });
  });

  describe('i18n config', () => {
    it('should have valid date format', () => {
      const validFormats = ['short', 'medium', 'long', 'full'];
      expect(validFormats).toContain(config.i18n.dateFormat);
    });

    it('should have valid time format', () => {
      const validFormats = ['short', 'medium', 'long'];
      expect(validFormats).toContain(config.i18n.timeFormat);
    });

    it('should have timezone', () => {
      expect(config.i18n.timezone).toBeDefined();
      expect(typeof config.i18n.timezone).toBe('string');
    });
  });

  describe('getEnvironment', () => {
    it('should return environment type', () => {
      const env = getEnvironment();
      const validEnvironments: Environment[] = ['development', 'staging', 'production'];
      expect(validEnvironments).toContain(env);
    });

    it('should match config environment', () => {
      expect(getEnvironment()).toBe(config.app.environment);
    });
  });

  describe('isDevelopment', () => {
    it('should return boolean', () => {
      expect(typeof isDevelopment()).toBe('boolean');
    });

    it('should return true when environment is development', () => {
      const originalEnv = config.app.environment;
      (config.app as { environment: Environment }).environment = 'development';
      expect(isDevelopment()).toBe(true);
      (config.app as { environment: Environment }).environment = originalEnv;
    });
  });

  describe('isProduction', () => {
    it('should return boolean', () => {
      expect(typeof isProduction()).toBe('boolean');
    });

    it('should return true when environment is production', () => {
      const originalEnv = config.app.environment;
      (config.app as { environment: Environment }).environment = 'production';
      expect(isProduction()).toBe(true);
      (config.app as { environment: Environment }).environment = originalEnv;
    });
  });

  describe('isFeatureEnabled', () => {
    it('should return boolean for valid feature', () => {
      expect(typeof isFeatureEnabled('enableDarkMode')).toBe('boolean');
      expect(typeof isFeatureEnabled('enableAnalytics')).toBe('boolean');
    });

    it('should return the feature flag value', () => {
      expect(isFeatureEnabled('enableDarkMode')).toBe(config.features.enableDarkMode);
    });
  });

  describe('reloadConfig', () => {
    it('should return config object', () => {
      const reloaded = reloadConfig();
      expect(reloaded).toBeDefined();
      expect(reloaded.api).toBeDefined();
      expect(reloaded.app).toBeDefined();
    });
  });
});

describe('validateConfig', () => {
  const createValidConfig = (): Config => ({
    api: {
      url: 'http://localhost:8000',
      timeout: 120000,
      retryEnabled: true,
      retryMaxAttempts: 3,
    },
    app: {
      title: 'Test App',
      description: 'Test Description',
      version: '1.0.0',
      environment: 'development',
    },
    features: {
      enableDarkMode: false,
      enableAnalytics: false,
      enableErrorTracking: false,
      enableExperimentalFeatures: false,
      enableDragDrop: true,
      enableFilePreview: true,
      enablePagination: true,
      enablePdfExport: false,
      enableCsvExport: false,
      enableJsonExport: true,
      enableLazyLoading: true,
      enableCodeSplitting: true,
      enableCompression: true,
      enableAuth: false,
      enableSocialSharing: false,
      enableBrowserNotifications: false,
      enableCache: true,
      enableRateLimiting: true,
      enableAriaLabels: true,
      enableKeyboardNavigation: true,
      enableScreenReader: true,
    },
    upload: {
      maxSizeMb: 10,
      allowedFileTypes: ['.pdf', '.docx'],
      showUploadProgress: true,
      progressUpdateInterval: 500,
    },
    ui: {
      defaultLanguage: 'en',
      supportedLanguages: ['en', 'ru'],
      theme: 'light',
      primaryColor: '#1976d2',
      secondaryColor: '#dc004e',
    },
    display: {
      itemsPerPage: 10,
      maxResults: 100,
      showProcessingTime: true,
      showConfidenceScores: true,
      showDetailedErrors: true,
      friendlyErrors: true,
    },
    resultsDisplay: {
      highlightMatchedSkills: true,
      highlightMissingSkills: true,
      showMatchPercentage: true,
      showExperienceDetails: true,
      showGrammarSuggestions: true,
      autoRefreshResults: true,
      resultsRefreshInterval: 5000,
      maxRefreshDuration: 60000,
    },
    auth: {
      provider: 'jwt',
      tokenStorage: 'localStorage',
      sessionTimeoutMinutes: 60,
    },
    analytics: {},
    errorTracking: {},
    support: {
      helpDocsUrl: 'https://docs.example.com',
      supportEmail: 'support@example.com',
      reportIssueUrl: 'https://github.com/example/repo/issues',
    },
    notification: {
      duration: 5000,
      position: 'top-right',
    },
    cache: {
      duration: 300000,
      clearOnLogout: true,
    },
    rateLimit: {
      maxRequestsPerMinute: 60,
    },
    seo: {
      siteName: 'Test Site',
      siteUrl: 'http://localhost:5173',
      defaultOgImage: '/og-image.png',
      twitterCardType: 'summary_large_image',
    },
    i18n: {
      dateFormat: 'medium',
      timeFormat: 'short',
      timezone: 'UTC',
    },
  });

  it('should validate valid configuration', () => {
    const validConfig = createValidConfig();
    const result = validateConfig(validConfig);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should detect invalid API URL', () => {
    const invalidConfig = createValidConfig();
    invalidConfig.api.url = 'not-a-valid-url';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid API URL format'))).toBe(true);
  });

  it('should detect invalid upload size', () => {
    const invalidConfig = createValidConfig();
    invalidConfig.upload.maxSizeMb = 0;
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('must be at least 1MB'))).toBe(true);
  });

  it('should detect invalid file type format', () => {
    const invalidConfig = createValidConfig();
    invalidConfig.upload.allowedFileTypes = ['pdf', 'docx']; // Missing dots
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('must start with'))).toBe(true);
  });

  it('should detect invalid theme', () => {
    const invalidConfig = createValidConfig();
    (invalidConfig.ui as { theme: string }).theme = 'invalid';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid theme'))).toBe(true);
  });

  it('should detect invalid color format', () => {
    const invalidConfig = createValidConfig();
    invalidConfig.ui.primaryColor = 'red';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid primary color format'))).toBe(true);
  });

  it('should detect max results less than items per page', () => {
    const invalidConfig = createValidConfig();
    invalidConfig.display.itemsPerPage = 50;
    invalidConfig.display.maxResults = 10;
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('must be greater than or equal to'))).toBe(true);
  });

  it('should detect invalid auth provider', () => {
    const invalidConfig = createValidConfig();
    (invalidConfig.auth as { provider: string }).provider = 'invalid';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid auth provider'))).toBe(true);
  });

  it('should detect invalid notification position', () => {
    const invalidConfig = createValidConfig();
    (invalidConfig.notification as { position: string }).position = 'center';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid notification position'))).toBe(true);
  });

  it('should detect invalid date format', () => {
    const invalidConfig = createValidConfig();
    (invalidConfig.i18n as { dateFormat: string }).dateFormat = 'invalid';
    const result = validateConfig(invalidConfig);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('Invalid date format'))).toBe(true);
  });
});
