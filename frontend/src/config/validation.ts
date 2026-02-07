/**
 * Configuration validation utilities
 *
 * This module provides validation functions for all configuration values.
 * Validation is performed on startup to ensure all required values are present
 * and valid. Invalid configuration will prevent the application from starting.
 *
 * @example
 * ```ts
 * import { validateConfig, ValidationResult } from '@/config/validation';
 *
 * const result = validateConfig(config);
 * if (!result.valid) {
 *   console.error('Configuration errors:', result.errors);
 *   // Handle invalid configuration
 * }
 * ```
 */

import type {
  ApiConfig,
  AppConfig,
  FeatureConfig,
  UploadConfig,
  UiConfig,
  DisplayConfig,
  ResultsDisplayConfig,
  AuthConfig,
  NotificationConfig,
  CacheConfig,
  RateLimitConfig,
  SeoConfig,
  I18nConfig,
  ValidationResult,
} from './types';

/**
 * Validate API configuration
 *
 * @param config - API configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateApiConfig(config: ApiConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Validate URL
  if (!config.url) {
    errors.push('API URL is required');
  } else {
    try {
      new URL(config.url);
    } catch {
      errors.push(`Invalid API URL format: ${config.url}`);
    }
  }

  // Validate timeout
  if (config.timeout < 1000) {
    warnings.push(`API timeout (${config.timeout}ms) is very short, recommend at least 1000ms`);
  }
  if (config.timeout > 300000) {
    warnings.push(`API timeout (${config.timeout}ms) is very long, recommend at most 300000ms (5 minutes)`);
  }

  // Validate retry settings
  if (config.retryEnabled && config.retryMaxAttempts < 1) {
    errors.push('Retry max attempts must be at least 1 when retry is enabled');
  }
  if (config.retryMaxAttempts > 10) {
    warnings.push('Retry max attempts is very high (max 10 recommended)');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate application configuration
 *
 * @param config - Application configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateAppConfig(config: AppConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!config.title) {
    errors.push('Application title is required');
  }

  if (!config.version) {
    warnings.push('Application version is not set');
  }

  const validEnvironments: Array<'development' | 'staging' | 'production'> = ['development', 'staging', 'production'];
  if (!validEnvironments.includes(config.environment)) {
    errors.push(`Invalid environment: ${config.environment}. Must be one of: ${validEnvironments.join(', ')}`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate upload configuration
 *
 * @param config - Upload configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateUploadConfig(config: UploadConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.maxSizeMb < 1) {
    errors.push('Max upload size must be at least 1MB');
  }
  if (config.maxSizeMb > 100) {
    warnings.push('Max upload size is very large (>100MB), consider reducing for better performance');
  }

  if (!config.allowedFileTypes || config.allowedFileTypes.length === 0) {
    errors.push('At least one allowed file type must be specified');
  }

  // Validate file type format (should start with dot)
  const invalidTypes = config.allowedFileTypes.filter((type) => !type.startsWith('.'));
  if (invalidTypes.length > 0) {
    errors.push(`Invalid file type format: ${invalidTypes.join(', ')}. File types must start with '.'`);
  }

  if (config.progressUpdateInterval < 100) {
    warnings.push('Progress update interval is very short, may cause performance issues');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate UI configuration
 *
 * @param config - UI configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateUiConfig(config: UiConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!config.defaultLanguage) {
    errors.push('Default language is required');
  }

  if (!config.supportedLanguages.includes(config.defaultLanguage)) {
    errors.push('Default language must be included in supported languages');
  }

  const validThemes: Array<'light' | 'dark' | 'auto'> = ['light', 'dark', 'auto'];
  if (!validThemes.includes(config.theme)) {
    errors.push(`Invalid theme: ${config.theme}. Must be one of: ${validThemes.join(', ')}`);
  }

  // Validate color format (hex color)
  const hexColorRegex = /^#[0-9A-Fa-f]{6}$/;
  if (!hexColorRegex.test(config.primaryColor)) {
    errors.push(`Invalid primary color format: ${config.primaryColor}. Must be a hex color (e.g., #1976d2)`);
  }
  if (!hexColorRegex.test(config.secondaryColor)) {
    errors.push(`Invalid secondary color format: ${config.secondaryColor}. Must be a hex color (e.g., #dc004e)`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate display configuration
 *
 * @param config - Display configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateDisplayConfig(config: DisplayConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.itemsPerPage < 1) {
    errors.push('Items per page must be at least 1');
  }
  if (config.itemsPerPage > 100) {
    warnings.push('Items per page is very large (>100), may affect performance');
  }

  if (config.maxResults < config.itemsPerPage) {
    errors.push('Max results must be greater than or equal to items per page');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate results display configuration
 *
 * @param config - Results display configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateResultsDisplayConfig(config: ResultsDisplayConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.autoRefreshResults) {
    if (config.resultsRefreshInterval < 1000) {
      warnings.push('Results refresh interval is very short (<1s), may cause excessive API calls');
    }
    if (config.maxRefreshDuration < config.resultsRefreshInterval) {
      errors.push('Max refresh duration must be greater than refresh interval');
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate authentication configuration
 *
 * @param config - Authentication configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateAuthConfig(config: AuthConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const validProviders: Array<'jwt' | 'oauth' | 'auth0'> = ['jwt', 'oauth', 'auth0'];
  if (!validProviders.includes(config.provider)) {
    errors.push(`Invalid auth provider: ${config.provider}. Must be one of: ${validProviders.join(', ')}`);
  }

  const validStorage: Array<'localStorage' | 'sessionStorage' | 'cookie'> = ['localStorage', 'sessionStorage', 'cookie'];
  if (!validStorage.includes(config.tokenStorage)) {
    errors.push(`Invalid token storage: ${config.tokenStorage}. Must be one of: ${validStorage.join(', ')}`);
  }

  if (config.sessionTimeoutMinutes < 1) {
    errors.push('Session timeout must be at least 1 minute');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate notification configuration
 *
 * @param config - Notification configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateNotificationConfig(config: NotificationConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.duration < 1000) {
    warnings.push('Notification duration is very short (<1s), users may not see it');
  }
  if (config.duration > 30000) {
    warnings.push('Notification duration is very long (>30s), may be intrusive');
  }

  const validPositions: Array<'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'> = [
    'top-left',
    'top-right',
    'bottom-left',
    'bottom-right',
  ];
  if (!validPositions.includes(config.position)) {
    errors.push(`Invalid notification position: ${config.position}. Must be one of: ${validPositions.join(', ')}`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate cache configuration
 *
 * @param config - Cache configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateCacheConfig(config: CacheConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.duration < 0) {
    errors.push('Cache duration must be non-negative');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate rate limiting configuration
 *
 * @param config - Rate limiting configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateRateLimitConfig(config: RateLimitConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (config.maxRequestsPerMinute < 1) {
    errors.push('Max requests per minute must be at least 1');
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate SEO configuration
 *
 * @param config - SEO configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateSeoConfig(config: SeoConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!config.siteName) {
    errors.push('Site name is required');
  }

  if (!config.siteUrl) {
    errors.push('Site URL is required');
  } else {
    try {
      new URL(config.siteUrl);
    } catch {
      errors.push(`Invalid site URL format: ${config.siteUrl}`);
    }
  }

  const validCardTypes: Array<'summary' | 'summary_large_image'> = ['summary', 'summary_large_image'];
  if (!validCardTypes.includes(config.twitterCardType)) {
    errors.push(`Invalid Twitter card type: ${config.twitterCardType}. Must be one of: ${validCardTypes.join(', ')}`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate i18n configuration
 *
 * @param config - i18n configuration to validate
 * @returns Validation result with any errors or warnings
 */
function validateI18nConfig(config: I18nConfig): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const validDateFormats: Array<'short' | 'medium' | 'long' | 'full'> = ['short', 'medium', 'long', 'full'];
  if (!validDateFormats.includes(config.dateFormat)) {
    errors.push(`Invalid date format: ${config.dateFormat}. Must be one of: ${validDateFormats.join(', ')}`);
  }

  const validTimeFormats: Array<'short' | 'medium' | 'long'> = ['short', 'medium', 'long'];
  if (!validTimeFormats.includes(config.timeFormat)) {
    errors.push(`Invalid time format: ${config.timeFormat}. Must be one of: ${validTimeFormats.join(', ')}`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate complete configuration object
 *
 * Performs validation on all configuration sections and returns
 * a combined validation result.
 *
 * @param config - Complete configuration object to validate
 * @returns Combined validation result with all errors and warnings
 *
 * @example
 * ```ts
 * const result = validateConfig(appConfig);
 * if (!result.valid) {
 *   console.error('Invalid configuration:');
 *   result.errors.forEach(err => console.error(`  - ${err}`));
 * }
 * if (result.warnings.length > 0) {
 *   console.warn('Configuration warnings:');
 *   result.warnings.forEach(warn => console.warn(`  - ${warn}`));
 * }
 * ```
 */
export function validateConfig(config: {
  api: ApiConfig;
  app: AppConfig;
  features: FeatureConfig;
  upload: UploadConfig;
  ui: UiConfig;
  display: DisplayConfig;
  resultsDisplay: ResultsDisplayConfig;
  auth: AuthConfig;
  notification: NotificationConfig;
  cache: CacheConfig;
  rateLimit: RateLimitConfig;
  seo: SeoConfig;
  i18n: I18nConfig;
}): ValidationResult {
  const allErrors: string[] = [];
  const allWarnings: string[] = [];

  // Validate each section
  const apiResult = validateApiConfig(config.api);
  allErrors.push(...apiResult.errors);
  allWarnings.push(...apiResult.warnings);

  const appResult = validateAppConfig(config.app);
  allErrors.push(...appResult.errors);
  allWarnings.push(...appResult.warnings);

  const uploadResult = validateUploadConfig(config.upload);
  allErrors.push(...uploadResult.errors);
  allWarnings.push(...uploadResult.warnings);

  const uiResult = validateUiConfig(config.ui);
  allErrors.push(...uiResult.errors);
  allWarnings.push(...uiResult.warnings);

  const displayResult = validateDisplayConfig(config.display);
  allErrors.push(...displayResult.errors);
  allWarnings.push(...displayResult.warnings);

  const resultsDisplayResult = validateResultsDisplayConfig(config.resultsDisplay);
  allErrors.push(...resultsDisplayResult.errors);
  allWarnings.push(...resultsDisplayResult.warnings);

  const authResult = validateAuthConfig(config.auth);
  allErrors.push(...authResult.errors);
  allWarnings.push(...authResult.warnings);

  const notificationResult = validateNotificationConfig(config.notification);
  allErrors.push(...notificationResult.errors);
  allWarnings.push(...notificationResult.warnings);

  const cacheResult = validateCacheConfig(config.cache);
  allErrors.push(...cacheResult.errors);
  allWarnings.push(...cacheResult.warnings);

  const rateLimitResult = validateRateLimitConfig(config.rateLimit);
  allErrors.push(...rateLimitResult.errors);
  allWarnings.push(...rateLimitResult.warnings);

  const seoResult = validateSeoConfig(config.seo);
  allErrors.push(...seoResult.errors);
  allWarnings.push(...seoResult.warnings);

  const i18nResult = validateI18nConfig(config.i18n);
  allErrors.push(...i18nResult.errors);
  allWarnings.push(...i18nResult.warnings);

  return {
    valid: allErrors.length === 0,
    errors: allErrors,
    warnings: allWarnings,
  };
}
