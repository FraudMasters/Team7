/**
 * Feature Flag Configuration
 *
 * Centralized feature flag management for the application.
 * All flags can be toggled via environment variables for easy
 * feature enable/disable without code changes.
 *
 * @module config/features
 */

/**
 * Feature flag configuration object
 *
 * All flags are read from environment variables at build time.
 * Environment variables must start with VITE_ to be accessible
 * in the Vite frontend.
 *
 * @example
 * ```ts
 * import { FEATURE_FLAGS } from '@/config/features';
 *
 * if (FEATURE_FLAGS.AUTH_ENABLED) {
 *   // Protected code path
 * }
 * ```
 */
export const FEATURE_FLAGS = {
  /**
   * Enable/disable authentication system
   *
   * When disabled:
   * - Routes are accessible without authentication
   * - Mock roles can be used for development
   * - KeyCloak/OIDC flow is bypassed
   *
   * Environment variable: VITE_AUTH_ENABLED
   * Default: false (auth disabled for development)
   *
   * @example
   * ```bash
   * # Enable auth
   * VITE_AUTH_ENABLED=true
   *
   * # Disable auth (development)
   * VITE_AUTH_ENABLED=false
   * ```
   */
  AUTH_ENABLED: parseBooleanFeature(import.meta.env.VITE_AUTH_ENABLED, false),

  /**
   * Enable mock role for development when auth is disabled
   *
   * This allows testing role-based features without setting up
   * the full authentication system.
   *
   * Environment variable: VITE_MOCK_ROLE
   * Default: 'Admin'
   *
   * @example
   * ```bash
   * # Set mock role to Recruiter
   * VITE_MOCK_ROLE=Recruiter
   * ```
   */
  MOCK_ROLE: import.meta.env.VITE_MOCK_ROLE || 'Admin',

  /**
   * Enable KeyCloak OIDC authentication
   *
   * This is the full authentication provider. When enabled,
   * users will be redirected to KeyCloak for login.
   *
   * Environment variable: VITE_OIDC_ENABLED
   * Default: false
   */
  OIDC_ENABLED: parseBooleanFeature(import.meta.env.VITE_OIDC_ENABLED, false),

  /**
   * KeyCloak authority URL (realm)
   *
   * Environment variable: VITE_OIDC_AUTHORITY
   * Default: 'http://localhost:8080/realms/agenthr'
   */
  OIDC_AUTHORITY: import.meta.env.VITE_OIDC_AUTHORITY || 'http://localhost:8080/realms/agenthr',

  /**
   * KeyCloak client ID
   *
   * Environment variable: VITE_OIDC_CLIENT_ID
   * Default: 'agenthr-frontend'
   */
  OIDC_CLIENT_ID: import.meta.env.VITE_OIDC_CLIENT_ID || 'agenthr-frontend',

  /**
   * Enable admin routes and functionality
   *
   * Environment variable: VITE_ENABLE_ADMIN_FEATURES
   * Default: true
   */
  ADMIN_ENABLED: parseBooleanFeature(import.meta.env.VITE_ENABLE_ADMIN_FEATURES, true),

  /**
   * Enable error boundaries for route sections
   *
   * Environment variable: VITE_ENABLE_ERROR_BOUNDARIES
   * Default: true
   */
  ERROR_BOUNDARIES_ENABLED: parseBooleanFeature(import.meta.env.VITE_ENABLE_ERROR_BOUNDARIES, true),

  /**
   * Enable service degradation handling
   *
   * When enabled, shows user-friendly error messages
   * when microservices are unavailable.
   *
   * Environment variable: VITE_ENABLE_SERVICE_DEGRADATION
   * Default: true
   */
  SERVICE_DEGRADATION_ENABLED: parseBooleanFeature(
    import.meta.env.VITE_ENABLE_SERVICE_DEGRADATION,
    true
  ),

  /**
   * Enable navigation failure handling
   *
   * Environment variable: VITE_ENABLE_NAVIGATION_FAILURE_HANDLING
   * Default: true
   */
  NAVIGATION_FAILURE_HANDLING_ENABLED: parseBooleanFeature(
    import.meta.env.VITE_ENABLE_NAVIGATION_FAILURE_HANDLING,
    true
  ),

  /**
   * Enable role-based route protection
   *
   * Environment variable: VITE_ENABLE_ROUTE_PROTECTION
   * Default: true
   */
  ROUTE_PROTECTION_ENABLED: parseBooleanFeature(import.meta.env.VITE_ENABLE_ROUTE_PROTECTION, true),

  /**
   * Enable debug mode for auth/routing
   *
   * Shows detailed logs about authentication state and
   * routing decisions in the console.
   *
   * Environment variable: VITE_AUTH_DEBUG
   * Default: false
   */
  AUTH_DEBUG: parseBooleanFeature(import.meta.env.VITE_AUTH_DEBUG, false),
} as const;

/**
 * Type definition for feature flag keys
 */
export type FeatureFlagKey = keyof typeof FEATURE_FLAGS;

/**
 * Type definition for feature flag values
 */
export type FeatureFlagValue = (typeof FEATURE_FLAGS)[FeatureFlagKey];

/**
 * Parse a boolean feature flag from an environment variable
 *
 * Handles string values ('true', 'false') and ensures type safety.
 * Returns the default value if the environment variable is undefined.
 *
 * @param value - Environment variable value
 * @param defaultValue - Default value if env var is undefined
 * @returns Boolean value
 *
 * @example
 * ```ts
 * parseBooleanFeature('true', false)  // returns true
 * parseBooleanFeature('false', true)  // returns false
 * parseBooleanFeature(undefined, true) // returns true
 * ```
 */
function parseBooleanFeature(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined) {
    return defaultValue;
  }

  // Handle string boolean values
  switch (value.toLowerCase()) {
    case 'true':
    case '1':
    case 'yes':
    case 'on':
      return true;
    case 'false':
    case '0':
    case 'no':
    case 'off':
      return false;
    default:
      return defaultValue;
  }
}

/**
 * Check if a feature flag is enabled
 *
 * Helper function for runtime feature flag checks.
 * Useful for conditional logic based on feature flags.
 *
 * @param flag - Feature flag key to check
 * @returns Whether the feature flag is enabled
 *
 * @example
 * ```tsx
 * import { isFeatureEnabled } from '@/config/features';
 *
 * {isFeatureEnabled('AUTH_ENABLED') && <LoginPage />}
 * ```
 */
export function isFeatureEnabled(flag: FeatureFlagKey): boolean {
  const value = FEATURE_FLAGS[flag];

  // Handle boolean flags
  if (typeof value === 'boolean') {
    return value;
  }

  // For non-boolean flags, check if they have a truthy value
  return Boolean(value);
}

/**
 * Get a feature flag value
 *
 * Generic helper for retrieving any feature flag value.
 *
 * @param flag - Feature flag key to retrieve
 * @returns The feature flag value
 *
 * @example
 * ```ts
 * import { getFeatureFlag } from '@/config/features';
 *
 * const mockRole = getFeatureFlag('MOCK_ROLE');
 * console.log(`Using mock role: ${mockRole}`);
 * ```
 */
export function getFeatureFlag<K extends FeatureFlagKey>(flag: K): (typeof FEATURE_FLAGS)[K] {
  return FEATURE_FLAGS[flag];
}

/**
 * Feature flag categories for better organization
 *
 * Groups related feature flags together for easier access.
 */
export const FEATURE_CATEGORIES = {
  /**
   * Authentication and authorization flags
   */
  AUTH: {
    ENABLED: FEATURE_FLAGS.AUTH_ENABLED,
    OIDC_ENABLED: FEATURE_FLAGS.OIDC_ENABLED,
    MOCK_ROLE: FEATURE_FLAGS.MOCK_ROLE,
    DEBUG: FEATURE_FLAGS.AUTH_DEBUG,
  },

  /**
   * Error handling and resilience flags
   */
  RESILIENCE: {
    ERROR_BOUNDARIES: FEATURE_FLAGS.ERROR_BOUNDARIES_ENABLED,
    SERVICE_DEGRADATION: FEATURE_FLAGS.SERVICE_DEGRADATION_ENABLED,
    NAVIGATION_FAILURE: FEATURE_FLAGS.NAVIGATION_FAILURE_HANDLING_ENABLED,
  },

  /**
   * Role-based access control flags
   */
  ACCESS_CONTROL: {
    ROUTE_PROTECTION: FEATURE_FLAGS.ROUTE_PROTECTION_ENABLED,
    ADMIN_FEATURES: FEATURE_FLAGS.ADMIN_ENABLED,
  },

  /**
   * KeyCloak OIDC configuration
   */
  OIDC: {
    AUTHORITY: FEATURE_FLAGS.OIDC_AUTHORITY,
    CLIENT_ID: FEATURE_FLAGS.OIDC_CLIENT_ID,
  },
} as const;

/**
 * Log current feature flag configuration
 *
 * Outputs all feature flags and their values to console.
 * Useful for debugging configuration issues.
 *
 * @example
 * ```ts
 * import { logFeatureFlags } from '@/config/features';
 *
 * logFeatureFlags();
 * ```
 */
export function logFeatureFlags(): void {
  if (!FEATURE_FLAGS.AUTH_DEBUG) {
    return;
  }

  console.group('🚩 Feature Flags Configuration');

  console.log('Authentication:');
  console.log('  AUTH_ENABLED:', FEATURE_FLAGS.AUTH_ENABLED);
  console.log('  OIDC_ENABLED:', FEATURE_FLAGS.OIDC_ENABLED);
  console.log('  MOCK_ROLE:', FEATURE_FLAGS.MOCK_ROLE);

  console.log('Resilience:');
  console.log('  ERROR_BOUNDARIES_ENABLED:', FEATURE_FLAGS.ERROR_BOUNDARIES_ENABLED);
  console.log('  SERVICE_DEGRADATION_ENABLED:', FEATURE_FLAGS.SERVICE_DEGRADATION_ENABLED);
  console.log('  NAVIGATION_FAILURE_HANDLING_ENABLED:', FEATURE_FLAGS.NAVIGATION_FAILURE_HANDLING_ENABLED);

  console.log('Access Control:');
  console.log('  ROUTE_PROTECTION_ENABLED:', FEATURE_FLAGS.ROUTE_PROTECTION_ENABLED);
  console.log('  ADMIN_ENABLED:', FEATURE_FLAGS.ADMIN_ENABLED);

  console.log('OIDC Config:');
  console.log('  AUTHORITY:', FEATURE_FLAGS.OIDC_AUTHORITY);
  console.log('  CLIENT_ID:', FEATURE_FLAGS.OIDC_CLIENT_ID);

  console.groupEnd();
}

/**
 * Export default feature flags object
 */
export default FEATURE_FLAGS;
