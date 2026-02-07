/**
 * Centralized Configuration Service
 *
 * This module provides a centralized configuration management system for the
 * frontend application. All environment variables (prefixed with VITE_) are
 * loaded, validated, and exposed through a type-safe configuration object.
 *
 * Configuration is loaded on application startup and validated to ensure
 * all required values are present and valid. Invalid configuration will
 * prevent the application from starting.
 *
 * @example
 * ```ts
 * import { config } from '@/config';
 *
 * // Access API configuration
 * const apiUrl = config.api.url;
 * const timeout = config.api.timeout;
 *
 * // Check feature flags
 * if (config.features.enableDarkMode) {
 *   // Enable dark mode
 * }
 *
 * // Get application info
 * console.log(`${config.app.title} v${config.app.version}`);
 * ```
 */

import type { Config, Environment } from './types';
import { validateConfig } from './validation';

/**
 * Get environment variable with optional default value
 *
 * @param key - Environment variable key (without VITE_ prefix)
 * @param defaultValue - Default value if variable is not set
 * @returns Environment variable value or default
 */
function getEnv(key: string, defaultValue?: string): string {
  const value = import.meta.env[`VITE_${key}`];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Required environment variable VITE_${key} is not set`);
  }
  return value ?? defaultValue ?? '';
}

/**
 * Get boolean environment variable
 *
 * @param key - Environment variable key (without VITE_ prefix)
 * @param defaultValue - Default value if variable is not set
 * @returns Boolean value
 */
function getEnvBoolean(key: string, defaultValue: boolean = false): boolean {
  const value = getEnv(key, String(defaultValue));
  return value === 'true' || value === '1';
}

/**
 * Get number environment variable
 *
 * @param key - Environment variable key (without VITE_ prefix)
 * @param defaultValue - Default value if variable is not set
 * @returns Number value
 */
function getEnvNumber(key: string, defaultValue: number): number {
  const value = getEnv(key, String(defaultValue));
  const num = Number.parseInt(value, 10);
  if (Number.isNaN(num)) {
    throw new Error(`Environment variable VITE_${key} must be a number, got: ${value}`);
  }
  return num;
}

/**
 * Get array environment variable
 *
 * @param key - Environment variable key (without VITE_ prefix)
 * @param separator - Separator character (default: comma)
 * @param defaultValue - Default value if variable is not set
 * @returns Array of strings
 */
function getEnvArray(key: string, separator: string = ',', defaultValue: string[] = []): string[] {
  const value = getEnv(key, defaultValue.join(separator));
  if (!value) return defaultValue;
  return value.split(separator).map((s) => s.trim()).filter(Boolean);
}

/**
 * Detect current environment from URL or environment variable
 *
 * @returns Detected environment
 */
function detectEnvironment(): Environment {
  const envVar = getEnv('ENVIRONMENT', 'development').toLowerCase();

  if (envVar === 'production' || envVar === 'prod') {
    return 'production';
  }
  if (envVar === 'staging' || envVar === 'stage') {
    return 'staging';
  }
  return 'development';
}

/**
 * Load API configuration from environment variables
 *
 * @returns API configuration object
 */
function loadApiConfig() {
  return {
    url: getEnv('API_URL', 'http://localhost:8000'),
    timeout: getEnvNumber('API_TIMEOUT', 120000),
    retryEnabled: getEnvBoolean('API_RETRY_ENABLED', true),
    retryMaxAttempts: getEnvNumber('API_RETRY_MAX_ATTEMPTS', 3),
  };
}

/**
 * Load application configuration from environment variables
 *
 * @returns Application configuration object
 */
function loadAppConfig() {
  return {
    title: getEnv('APP_TITLE', 'Resume Analysis Platform'),
    description: getEnv('APP_DESCRIPTION', 'AI-powered resume analysis platform with ML/NLP processing'),
    version: getEnv('APP_VERSION', '1.0.0'),
    environment: detectEnvironment(),
  };
}

/**
 * Load feature flags from environment variables
 *
 * @returns Feature flags configuration object
 */
function loadFeatureConfig() {
  return {
    enableDarkMode: getEnvBoolean('ENABLE_DARK_MODE', false),
    enableAnalytics: getEnvBoolean('ENABLE_ANALYTICS', false),
    enableErrorTracking: getEnvBoolean('ENABLE_ERROR_TRACKING', false),
    enableExperimentalFeatures: getEnvBoolean('ENABLE_EXPERIMENTAL_FEATURES', false),
    enableDragDrop: getEnvBoolean('ENABLE_DRAG_DROP', true),
    enableFilePreview: getEnvBoolean('ENABLE_FILE_PREVIEW', true),
    enablePagination: getEnvBoolean('ENABLE_PAGINATION', true),
    enablePdfExport: getEnvBoolean('ENABLE_PDF_EXPORT', false),
    enableCsvExport: getEnvBoolean('ENABLE_CSV_EXPORT', false),
    enableJsonExport: getEnvBoolean('ENABLE_JSON_EXPORT', true),
    enableLazyLoading: getEnvBoolean('ENABLE_LAZY_LOADING', true),
    enableCodeSplitting: getEnvBoolean('ENABLE_CODE_SPLITTING', true),
    enableCompression: getEnvBoolean('ENABLE_COMPRESSION', true),
    enableAuth: getEnvBoolean('ENABLE_AUTH', false),
    enableSocialSharing: getEnvBoolean('ENABLE_SOCIAL_SHARING', false),
    enableBrowserNotifications: getEnvBoolean('ENABLE_BROWSER_NOTIFICATIONS', false),
    enableCache: getEnvBoolean('ENABLE_CACHE', true),
    enableRateLimiting: getEnvBoolean('ENABLE_RATE_LIMITING', true),
    enableAriaLabels: getEnvBoolean('ENABLE_ARIA_LABELS', true),
    enableKeyboardNavigation: getEnvBoolean('ENABLE_KEYBOARD_NAVIGATION', true),
    enableScreenReader: getEnvBoolean('ENABLE_SCREEN_READER', true),
    enablePerformanceLogging: getEnvBoolean('ENABLE_PERFORMANCE_LOGGING', true),
  };
}

/**
 * Load upload configuration from environment variables
 *
 * @returns Upload configuration object
 */
function loadUploadConfig() {
  return {
    maxSizeMb: getEnvNumber('MAX_UPLOAD_SIZE_MB', 10),
    allowedFileTypes: getEnvArray('ALLOWED_FILE_TYPES', ',', ['.pdf', '.docx']),
    showUploadProgress: getEnvBoolean('SHOW_UPLOAD_PROGRESS', true),
    progressUpdateInterval: getEnvNumber('PROGRESS_UPDATE_INTERVAL', 500),
  };
}

/**
 * Load UI configuration from environment variables
 *
 * @returns UI configuration object
 */
function loadUiConfig() {
  return {
    defaultLanguage: getEnv('DEFAULT_LANGUAGE', 'en'),
    supportedLanguages: getEnvArray('SUPPORTED_LANGUAGES', ',', ['en', 'ru']),
    theme: getEnv('THEME', 'light') as 'light' | 'dark' | 'auto',
    primaryColor: getEnv('PRIMARY_COLOR', '#1976d2'),
    secondaryColor: getEnv('SECONDARY_COLOR', '#dc004e'),
  };
}

/**
 * Load display configuration from environment variables
 *
 * @returns Display configuration object
 */
function loadDisplayConfig() {
  return {
    itemsPerPage: getEnvNumber('ITEMS_PER_PAGE', 10),
    maxResults: getEnvNumber('MAX_RESULTS', 100),
    showProcessingTime: getEnvBoolean('SHOW_PROCESSING_TIME', true),
    showConfidenceScores: getEnvBoolean('SHOW_CONFIDENCE_SCORES', true),
    showDetailedErrors: getEnvBoolean('SHOW_DETAILED_ERRORS', true),
    friendlyErrors: getEnvBoolean('FRIENDLY_ERRORS', true),
  };
}

/**
 * Load results display configuration from environment variables
 *
 * @returns Results display configuration object
 */
function loadResultsDisplayConfig() {
  return {
    highlightMatchedSkills: getEnvBoolean('HIGHLIGHT_MATCHED_SKILLS', true),
    highlightMissingSkills: getEnvBoolean('HIGHLIGHT_MISSING_SKILLS', true),
    showMatchPercentage: getEnvBoolean('SHOW_MATCH_PERCENTAGE', true),
    showExperienceDetails: getEnvBoolean('SHOW_EXPERIENCE_DETAILS', true),
    showGrammarSuggestions: getEnvBoolean('SHOW_GRAMMAR_SUGGESTIONS', true),
    autoRefreshResults: getEnvBoolean('AUTO_REFRESH_RESULTS', true),
    resultsRefreshInterval: getEnvNumber('RESULTS_REFRESH_INTERVAL', 5000),
    maxRefreshDuration: getEnvNumber('MAX_REFRESH_DURATION', 60000),
  };
}

/**
 * Load authentication configuration from environment variables
 *
 * @returns Authentication configuration object
 */
function loadAuthConfig() {
  return {
    provider: getEnv('AUTH_PROVIDER', 'jwt') as 'jwt' | 'oauth' | 'auth0',
    tokenStorage: getEnv('TOKEN_STORAGE', 'localStorage') as 'localStorage' | 'sessionStorage' | 'cookie',
    sessionTimeoutMinutes: getEnvNumber('SESSION_TIMEOUT_MINUTES', 60),
  };
}

/**
 * Load analytics configuration from environment variables
 *
 * @returns Analytics configuration object
 */
function loadAnalyticsConfig() {
  return {
    gaTrackingId: import.meta.env.VITE_GA_TRACKING_ID,
    plausibleDomain: import.meta.env.VITE_PLAUSIBLE_DOMAIN,
    posthogKey: import.meta.env.VITE_POSTHOG_KEY,
    posthogHost: import.meta.env.VITE_POSTHOG_HOST,
  };
}

/**
 * Load error tracking configuration from environment variables
 *
 * @returns Error tracking configuration object
 */
function loadErrorTrackingConfig() {
  return {
    sentryDsn: import.meta.env.VITE_SENTRY_DSN,
    sentryEnvironment: import.meta.env.VITE_SENTRY_ENVIRONMENT,
  };
}

/**
 * Load support configuration from environment variables
 *
 * @returns Support configuration object
 */
function loadSupportConfig() {
  return {
    helpDocsUrl: getEnv('HELP_DOCS_URL', 'https://docs.example.com'),
    supportEmail: getEnv('SUPPORT_EMAIL', 'support@example.com'),
    reportIssueUrl: getEnv('REPORT_ISSUE_URL', 'https://github.com/example/repo/issues'),
  };
}

/**
 * Load notification configuration from environment variables
 *
 * @returns Notification configuration object
 */
function loadNotificationConfig() {
  return {
    duration: getEnvNumber('NOTIFICATION_DURATION', 5000),
    position: getEnv('NOTIFICATION_POSITION', 'top-right') as 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right',
  };
}

/**
 * Load cache configuration from environment variables
 *
 * @returns Cache configuration object
 */
function loadCacheConfig() {
  return {
    duration: getEnvNumber('CACHE_DURATION', 300000),
    clearOnLogout: getEnvBoolean('CLEAR_CACHE_ON_LOGOUT', true),
  };
}

/**
 * Load rate limiting configuration from environment variables
 *
 * @returns Rate limiting configuration object
 */
function loadRateLimitConfig() {
  return {
    maxRequestsPerMinute: getEnvNumber('MAX_REQUESTS_PER_MINUTE', 60),
  };
}

/**
 * Load SEO configuration from environment variables
 *
 * @returns SEO configuration object
 */
function loadSeoConfig() {
  return {
    siteName: getEnv('SITE_NAME', 'Resume Analysis Platform'),
    siteUrl: getEnv('SITE_URL', 'http://localhost:5173'),
    defaultOgImage: getEnv('DEFAULT_OG_IMAGE', '/og-image.png'),
    twitterCardType: getEnv('TWITTER_CARD_TYPE', 'summary_large_image') as 'summary' | 'summary_large_image',
  };
}

/**
 * Load i18n configuration from environment variables
 *
 * @returns i18n configuration object
 */
function loadI18nConfig() {
  return {
    dateFormat: getEnv('DATE_FORMAT', 'medium') as 'short' | 'medium' | 'long' | 'full',
    timeFormat: getEnv('TIME_FORMAT', 'short') as 'short' | 'medium' | 'long',
    timezone: getEnv('TIMEZONE', 'UTC'),
  };
}

/**
 * Load complete configuration from environment variables
 *
 * This function loads all configuration values from environment variables,
 * validates them, and returns a complete configuration object.
 *
 * @throws Error if configuration validation fails
 * @returns Complete configuration object
 *
 * @example
 * ```ts
 * const config = loadConfig();
 * console.log(`Loaded config for ${config.app.environment}`);
 * ```
 */
function loadConfig(): Config {
  const config = {
    api: loadApiConfig(),
    app: loadAppConfig(),
    features: loadFeatureConfig(),
    upload: loadUploadConfig(),
    ui: loadUiConfig(),
    display: loadDisplayConfig(),
    resultsDisplay: loadResultsDisplayConfig(),
    auth: loadAuthConfig(),
    analytics: loadAnalyticsConfig(),
    errorTracking: loadErrorTrackingConfig(),
    support: loadSupportConfig(),
    notification: loadNotificationConfig(),
    cache: loadCacheConfig(),
    rateLimit: loadRateLimitConfig(),
    seo: loadSeoConfig(),
    i18n: loadI18nConfig(),
  };

  // Validate configuration
  const validationResult = validateConfig(config);

  // Log warnings (non-critical)
  if (validationResult.warnings.length > 0) {
    // biome-ignore lint/suspicious/noConsole: Intentional console output for configuration warnings
    console.warn('[Config] Configuration warnings:');
    validationResult.warnings.forEach((warning) => {
      // biome-ignore lint/suspicious/noConsole: Intentional console output for configuration warnings
      console.warn(`  - ${warning}`);
    });
  }

  // Throw on errors (critical)
  if (!validationResult.valid) {
    // biome-ignore lint/suspicious/noConsole: Intentional console output for configuration errors
    console.error('[Config] Configuration validation failed:');
    validationResult.errors.forEach((error) => {
      // biome-ignore lint/suspicious/noConsole: Intentional console output for configuration errors
      console.error(`  - ${error}`);
    });
    throw new Error('Invalid configuration. Please check environment variables.');
  }

  return config;
}

/**
 * Global configuration instance
 *
 * This singleton instance is loaded once on application startup and
 * provides type-safe access to all configuration values.
 *
 * @example
 * ```ts
 * import { config } from '@/config';
 *
 * console.log(config.api.url);
 * console.log(config.app.title);
 * ```
 */
export const config: Config = loadConfig();

/**
 * Reload configuration from environment variables
 *
 * This function can be used to reload configuration after environment
 * variables have changed. Note that in a browser environment, this
 * typically requires a page reload for VITE_ environment variables.
 *
 * @returns Reloaded configuration object
 *
 * @example
 * ```ts
 * // After environment changes
 * config = reloadConfig();
 * ```
 */
export function reloadConfig(): Config {
  // biome-ignore lint/suspicious/noConsole: Intentional console output for configuration reload
  console.info('[Config] Reloading configuration...');
  return loadConfig();
}

/**
 * Get current environment
 *
 * Convenience function to get the current environment.
 *
 * @returns Current environment ('development' | 'staging' | 'production')
 *
 * @example
 * ```ts
 * import { getEnvironment } from '@/config';
 *
 * if (getEnvironment() === 'production') {
 *   // Enable production-specific features
 * }
 * ```
 */
export function getEnvironment(): Environment {
  return config.app.environment;
}

/**
 * Check if running in development mode
 *
 * @returns true if in development environment
 *
 * @example
 * ```ts
 * import { isDevelopment } from '@/config';
 *
 * if (isDevelopment()) {
 *   console.log('Debug info');
 * }
 * ```
 */
export function isDevelopment(): boolean {
  return config.app.environment === 'development';
}

/**
 * Check if running in production mode
 *
 * @returns true if in production environment
 *
 * @example
 * ```ts
 * import { isProduction } from '@/config';
 *
 * if (isProduction()) {
 *   // Enable analytics
 * }
 * ```
 */
export function isProduction(): boolean {
  return config.app.environment === 'production';
}

/**
 * Check if a feature is enabled
 *
 * @param feature - Feature name to check
 * @returns true if the feature is enabled
 *
 * @example
 * ```ts
 * import { isFeatureEnabled } from '@/config';
 *
 * if (isFeatureEnabled('enableDarkMode')) {
 *   // Show dark mode toggle
 * }
 * ```
 */
export function isFeatureEnabled(feature: keyof Config['features']): boolean {
  return config.features[feature];
}

/**
 * Export configuration type for use in other modules
 */
export type { Config, Environment };
