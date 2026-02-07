/**
 * Configuration type definitions
 *
 * This module contains TypeScript interfaces for all configuration values
 * used throughout the frontend application. Configuration values are loaded
 * from environment variables (prefixed with VITE_) and validated on startup.
 *
 * @example
 * ```ts
 * import { config } from '@/config';
 *
 * // Access API configuration
 * const apiUrl = config.api.url;
 * const timeout = config.api.timeout;
 *
 * // Access feature flags
 * if (config.features.enableDarkMode) {
 *   // Enable dark mode
 * }
 * ```
 */

/**
 * Supported environment types
 */
export type Environment = 'development' | 'staging' | 'production';

/**
 * API configuration
 */
export interface ApiConfig {
  /** Backend API base URL */
  url: string;
  /** API request timeout in milliseconds */
  timeout: number;
  /** Enable automatic request retry on failure */
  retryEnabled: boolean;
  /** Maximum number of retry attempts */
  retryMaxAttempts: number;
}

/**
 * Application metadata configuration
 */
export interface AppConfig {
  /** Application title displayed in browser tab and header */
  title: string;
  /** Application description for SEO */
  description: string;
  /** Application version */
  version: string;
  /** Current environment */
  environment: Environment;
}

/**
 * Feature flags configuration
 */
export interface FeatureConfig {
  /** Enable dark mode theme option */
  enableDarkMode: boolean;
  /** Enable analytics tracking (Google Analytics, Plausible, etc.) */
  enableAnalytics: boolean;
  /** Enable error tracking (Sentry, Bugsnag, etc.) */
  enableErrorTracking: boolean;
  /** Enable experimental features */
  enableExperimentalFeatures: boolean;
  /** Enable drag-and-drop file upload */
  enableDragDrop: boolean;
  /** Enable file preview before upload */
  enableFilePreview: boolean;
  /** Enable results pagination */
  enablePagination: boolean;
  /** Enable PDF export */
  enablePdfExport: boolean;
  /** Enable CSV export */
  enableCsvExport: boolean;
  /** Enable JSON export */
  enableJsonExport: boolean;
  /** Enable lazy loading for images */
  enableLazyLoading: boolean;
  /** Enable code splitting */
  enableCodeSplitting: boolean;
  /** Enable compression */
  enableCompression: boolean;
  /** Enable authentication */
  enableAuth: boolean;
  /** Enable social sharing buttons */
  enableSocialSharing: boolean;
  /** Enable browser notifications */
  enableBrowserNotifications: boolean;
  /** Enable application cache */
  enableCache: boolean;
  /** Enable client-side rate limiting */
  enableRateLimiting: boolean;
  /** Enable ARIA labels for accessibility */
  enableAriaLabels: boolean;
  /** Enable keyboard navigation */
  enableKeyboardNavigation: boolean;
  /** Enable screen reader support */
  enableScreenReader: boolean;
  /** Enable performance logging for API calls */
  enablePerformanceLogging: boolean;
}

/**
 * File upload configuration
 */
export interface UploadConfig {
  /** Maximum file upload size in megabytes */
  maxSizeMb: number;
  /** Allowed file extensions (e.g., ['.pdf', '.docx']) */
  allowedFileTypes: string[];
  /** Show upload progress indicator */
  showUploadProgress: boolean;
  /** Progress update interval in milliseconds */
  progressUpdateInterval: number;
}

/**
 * UI configuration
 */
export interface UiConfig {
  /** Default language code (e.g., 'en', 'ru') */
  defaultLanguage: string;
  /** Supported language codes */
  supportedLanguages: string[];
  /** Theme: 'light', 'dark', or 'auto' */
  theme: 'light' | 'dark' | 'auto';
  /** Primary color in hex format */
  primaryColor: string;
  /** Secondary color in hex format */
  secondaryColor: string;
}

/**
 * Display configuration
 */
export interface DisplayConfig {
  /** Number of items per page in results */
  itemsPerPage: number;
  /** Maximum number of results to display */
  maxResults: number;
  /** Show processing time in results */
  showProcessingTime: boolean;
  /** Show confidence scores in analysis */
  showConfidenceScores: boolean;
  /** Show detailed error messages to users */
  showDetailedErrors: boolean;
  /** Enable user-friendly error messages */
  friendlyErrors: boolean;
}

/**
 * Analysis results display configuration
 */
export interface ResultsDisplayConfig {
  /** Highlight matched skills in green */
  highlightMatchedSkills: boolean;
  /** Highlight missing skills in red */
  highlightMissingSkills: boolean;
  /** Show skill match percentage */
  showMatchPercentage: boolean;
  /** Show experience verification details */
  showExperienceDetails: boolean;
  /** Show grammar/spelling suggestions */
  showGrammarSuggestions: boolean;
  /** Auto-refresh results */
  autoRefreshResults: boolean;
  /** Results refresh interval in milliseconds */
  resultsRefreshInterval: number;
  /** Maximum auto-refresh duration in milliseconds */
  maxRefreshDuration: number;
}

/**
 * Authentication configuration
 */
export interface AuthConfig {
  /** Auth provider: 'jwt', 'oauth', 'auth0' */
  provider: 'jwt' | 'oauth' | 'auth0';
  /** Token storage method: 'localStorage', 'sessionStorage', 'cookie' */
  tokenStorage: 'localStorage' | 'sessionStorage' | 'cookie';
  /** Session timeout in minutes */
  sessionTimeoutMinutes: number;
}

/**
 * Analytics configuration
 */
export interface AnalyticsConfig {
  /** Google Analytics tracking ID */
  gaTrackingId?: string;
  /** Plausible analytics domain */
  plausibleDomain?: string;
  /** PostHog API key */
  posthogKey?: string;
  /** PostHog host URL */
  posthogHost?: string;
}

/**
 * Error tracking configuration
 */
export interface ErrorTrackingConfig {
  /** Sentry DSN */
  sentryDsn?: string;
  /** Sentry environment */
  sentryEnvironment?: string;
}

/**
 * Help and support configuration
 */
export interface SupportConfig {
  /** Help documentation URL */
  helpDocsUrl: string;
  /** Support email address */
  supportEmail: string;
  /** Report issue URL */
  reportIssueUrl: string;
}

/**
 * Notification configuration
 */
export interface NotificationConfig {
  /** Notification duration in milliseconds */
  duration: number;
  /** Notification position */
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

/**
 * Cache configuration
 */
export interface CacheConfig {
  /** Cache duration in milliseconds */
  duration: number;
  /** Clear cache on logout */
  clearOnLogout: boolean;
}

/**
 * Rate limiting configuration
 */
export interface RateLimitConfig {
  /** Maximum requests per minute */
  maxRequestsPerMinute: number;
}

/**
 * SEO configuration
 */
export interface SeoConfig {
  /** Site name */
  siteName: string;
  /** Site URL */
  siteUrl: string;
  /** Default Open Graph image path */
  defaultOgImage: string;
  /** Twitter card type */
  twitterCardType: 'summary' | 'summary_large_image';
}

/**
 * Internationalization configuration
 */
export interface I18nConfig {
  /** Default date format */
  dateFormat: 'short' | 'medium' | 'long' | 'full';
  /** Default time format */
  timeFormat: 'short' | 'medium' | 'long';
  /** Default timezone */
  timezone: string;
}

/**
 * Complete application configuration
 *
 * Contains all configuration values loaded from environment variables.
 * All values are validated and type-safe.
 */
export interface Config {
  /** API configuration */
  api: ApiConfig;
  /** Application metadata */
  app: AppConfig;
  /** Feature flags */
  features: FeatureConfig;
  /** File upload settings */
  upload: UploadConfig;
  /** UI settings */
  ui: UiConfig;
  /** Display settings */
  display: DisplayConfig;
  /** Analysis results display */
  resultsDisplay: ResultsDisplayConfig;
  /** Authentication settings */
  auth: AuthConfig;
  /** Analytics settings */
  analytics: AnalyticsConfig;
  /** Error tracking settings */
  errorTracking: ErrorTrackingConfig;
  /** Help and support links */
  support: SupportConfig;
  /** Notification settings */
  notification: NotificationConfig;
  /** Cache settings */
  cache: CacheConfig;
  /** Rate limiting settings */
  rateLimit: RateLimitConfig;
  /** SEO settings */
  seo: SeoConfig;
  /** Internationalization settings */
  i18n: I18nConfig;
}

/**
 * Configuration validation result
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean;
  /** Array of validation error messages */
  errors: string[];
  /** Array of validation warning messages */
  warnings: string[];
}
