/**
 * useRoles Hook
 *
 * A custom hook for managing user roles and role-based access control.
 * Provides role checking helpers and mock role support for development.
 *
 * ## Mock Role Support (Development)
 *
 * When `VITE_AUTH_ENABLED=false`, the hook returns mock roles based on
 * the `VITE_MOCK_ROLE` environment variable. This allows testing role-based
 * features without setting up the full authentication system.
 *
 * @module hooks/useRoles
 */

import { useMemo } from 'react';
import { FEATURE_FLAGS, getFeatureFlag } from '@/config/features';

/**
 * User role type for role-based access control
 *
 * Standardized role names following PascalCase convention.
 * - JobSeeker: Can browse and apply for jobs
 * - Recruiter: Can manage vacancies and candidates
 * - Admin: Has superuser privileges and can access all routes
 */
export type UserRole = 'JobSeeker' | 'Recruiter' | 'Admin';

/**
 * User information interface
 *
 * Represents the authenticated user with their associated roles.
 * This will be populated from the auth system when enabled.
 */
export interface UserInfo {
  /**
   * User's unique identifier
   */
  id: string;

  /**
   * User's display name
   */
  name: string;

  /**
   * User's email address
   */
  email: string;

  /**
   * Roles assigned to the user
   */
  roles: UserRole[];
}

/**
 * Role information returned by useRoles hook
 *
 * Provides role checking helpers and access to user's current roles.
 * Includes mock role support when auth is disabled.
 */
export interface RolesResult {
  /**
   * Array of roles assigned to the current user
   *
   * When AUTH_ENABLED=false, this contains the mock role from VITE_MOCK_ROLE.
   * When AUTH_ENABLED=true, this contains roles from the authenticated user.
   */
  roles: UserRole[];

  /**
   * Check if user has a specific role
   *
   * @param role - Role to check
   * @returns true if user has the role
   *
   * @example
   * ```ts
   * const { hasRole } = useRoles();
   *
   * if (hasRole('Admin')) {
   *   // Show admin features
   * }
   * ```
   */
  hasRole: (role: UserRole) => boolean;

  /**
   * Check if user has at least one of the specified roles
   *
   * @param roles - Array of roles to check
   * @returns true if user has at least one of the roles
   *
   * @example
   * ```ts
   * const { hasAnyRole } = useRoles();
   *
   * if (hasAnyRole(['Recruiter', 'Admin'])) {
   *   // Show recruiter/admin features
   * }
   * ```
   */
  hasAnyRole: (roles: UserRole[]) => boolean;

  /**
   * Check if user has all of the specified roles
   *
   * @param roles - Array of roles to check
   * @returns true if user has all of the roles
   *
   * @example
   * ```ts
   * const { hasAllRoles } = useRoles();
   *
   * if (hasAllRoles(['Recruiter', 'Admin'])) {
   *   // User has both recruiter and admin roles
   * }
   * ```
   */
  hasAllRoles: (roles: UserRole[]) => boolean;

  /**
   * User information (available when auth is enabled)
   *
   * When AUTH_ENABLED=false, this is undefined.
   * When AUTH_ENABLED=true, this contains the authenticated user's info.
   */
  user: UserInfo | undefined;

  /**
   * Whether authentication is currently being verified
   *
   * Always false in mock mode (AUTH_ENABLED=false).
   * In auth mode, true while checking auth status.
   */
  isLoading: boolean;

  /**
   * Whether user is authenticated
   *
   * When AUTH_ENABLED=false, always true (mock mode).
   * When AUTH_ENABLED=true, reflects actual auth state.
   */
  isAuthenticated: boolean;

  /**
   * The primary role for the user
   *
   * Returns the highest-privilege role:
   * - Admin > Recruiter > JobSeeker
   */
  primaryRole: UserRole | undefined;
}

/**
 * Get the primary (highest-privilege) role from an array of roles
 *
 * Admin has highest priority, followed by Recruiter, then JobSeeker.
 *
 * @param roles - Array of user roles
 * @returns The primary role
 *
 * @private
 */
function getPrimaryRole(roles: UserRole[]): UserRole | undefined {
  if (roles.includes('Admin')) return 'Admin';
  if (roles.includes('Recruiter')) return 'Recruiter';
  if (roles.includes('JobSeeker')) return 'JobSeeker';
  return undefined;
}

/**
 * useRoles Hook
 *
 * Provides role-based access control helpers with mock role support
 * for development when authentication is disabled.
 *
 * ## Mock Mode (AUTH_ENABLED=false)
 *
 * When auth is disabled, returns mock role from `VITE_MOCK_ROLE`.
 * This allows testing role-based features without KeyCloak setup.
 *
 * @example
 * ```tsx
 * function AdminPanel() {
 *   const { hasRole, primaryRole } = useRoles();
 *
 *   if (!hasRole('Admin')) {
 *     return <AccessDenied />;
 *   }
 *
 *   return <AdminDashboard />;
 * }
 * ```
 *
 * ## Auth Mode (AUTH_ENABLED=true)
 *
 * When auth is enabled, extracts roles from authenticated user context.
 * This will be integrated with the actual auth provider.
 *
 * @example
 * ```tsx
 * function UserProfile() {
 *   const { user, hasRole } = useRoles();
 *
 *   return (
 *     <div>
 *       <h1>{user?.name}</h1>
 *       {hasRole('Admin') && <AdminBadge />}
 *     </div>
 *   );
 * }
 * ```
 *
 * ## Role Checking Helpers
 *
 * @example
 * ```tsx
 * function RecruiterFeatures() {
 *   const { hasRole, hasAnyRole, hasAllRoles } = useRoles();
 *
 *   // Single role check
 *   if (hasRole('Admin')) {
 *     return <AdminFeatures />;
 *   }
 *
 *   // Multiple role check (OR)
 *   if (hasAnyRole(['Recruiter', 'Admin'])) {
 *     return <RecruiterFeatures />;
 *   }
 *
 *   // All roles check (AND)
 *   if (hasAllRoles(['Recruiter', 'Admin'])) {
 *     return <MultiRoleFeatures />;
 *   }
 *
 *   return <PublicFeatures />;
 * }
 * ```
 *
 * ## Integration with ProtectedRoute
 *
 * This hook is designed to work with the `ProtectedRoute` component:
 *
 * @example
 * ```tsx
 * import { ProtectedRoute } from '@/components/ProtectedRoute';
 * import { useRoles } from '@/hooks/useRoles';
 *
 * function MyComponent() {
 *   const { hasRole } = useRoles();
 *
 *   // Manual role check within component
 *   if (hasRole('Admin')) {
 *     return <AdminOnlyContent />;
 *   }
 *
 *   // Or use ProtectedRoute wrapper
 *   return (
 *     <ProtectedRoute requiredRoles={['Admin']}>
 *       <AdminOnlyContent />
 *     </ProtectedRoute>
 *   );
 * }
 * ```
 */
export function useRoles(): RolesResult {
  // Use useMemo to prevent unnecessary recalculations
  const result = useMemo<RolesResult>(() => {
    /**
     * MOCK MODE (AUTH_ENABLED=false)
     *
     * When auth is disabled, return mock role from environment variable.
     * This is the default behavior for development without KeyCloak.
     */
    if (!FEATURE_FLAGS.AUTH_ENABLED) {
      const mockRole = getFeatureFlag('MOCK_ROLE') as UserRole;

      // Validate mock role
      const validRoles: UserRole[] = ['JobSeeker', 'Recruiter', 'Admin'];
      const normalizedMockRole = validRoles.includes(mockRole) ? mockRole : 'Admin';

      // Debug logging for mock mode
      if (FEATURE_FLAGS.AUTH_DEBUG) {
        console.group('🔓 useRoles - Mock Mode');
        console.log('AUTH_ENABLED:', false);
        console.log('MOCK_ROLE:', mockRole);
        console.log('Normalized Role:', normalizedMockRole);
        console.log('Action: Returning mock role for development');
        console.groupEnd();
      }

      return {
        roles: [normalizedMockRole],
        hasRole: (role: UserRole) => role === normalizedMockRole,
        hasAnyRole: (roles: UserRole[]) => roles.includes(normalizedMockRole),
        hasAllRoles: (roles: UserRole[]) => roles.every((r) => r === normalizedMockRole),
        user: undefined,
        isLoading: false,
        isAuthenticated: true, // Mock mode always "authenticated"
        primaryRole: normalizedMockRole,
      };
    }

    /**
     * AUTH MODE (AUTH_ENABLED=true)
     *
     * When auth is enabled, extract roles from authenticated user.
     *
     * TODO: This is a placeholder implementation. The actual integration
     * with the auth provider (KeyCloak, AuthContext, etc.) will be done
     * in a future task. For now, we use the mock role as a fallback.
     */
    const mockRole = getFeatureFlag('MOCK_ROLE') as UserRole;
    const validRoles: UserRole[] = ['JobSeeker', 'Recruiter', 'Admin'];
    const fallbackRole = validRoles.includes(mockRole) ? mockRole : 'Admin';

    // Debug logging for auth mode
    if (FEATURE_FLAGS.AUTH_DEBUG) {
      console.group('🔒 useRoles - Auth Mode');
      console.log('AUTH_ENABLED:', true);
      console.log('Action: Returning fallback role (auth integration pending)');
      console.log('Fallback Role:', fallbackRole);
      console.groupEnd();
    }

    return {
      roles: [fallbackRole],
      hasRole: (role: UserRole) => role === fallbackRole,
      hasAnyRole: (roles: UserRole[]) => roles.includes(fallbackRole),
      hasAllRoles: (roles: UserRole[]) => roles.every((r) => r === fallbackRole),
      user: undefined, // Will be populated from auth context
      isLoading: false, // Will reflect actual loading state
      isAuthenticated: true, // Will reflect actual auth state
      primaryRole: fallbackRole,
    };
  }, []); // Empty deps - this runs once on mount

  return result;
}

/**
 * Helper function to validate if a value is a valid UserRole
 *
 * @param role - Role to validate
 * @returns true if role is valid
 *
 * @example
 * ```ts
 * import { isValidRole } from '@/hooks/useRoles';
 *
 * if (isValidRole('Admin')) {
 *   // Role is valid
 * }
 * ```
 */
export function isValidRole(role: string): role is UserRole {
  return ['JobSeeker', 'Recruiter', 'Admin'].includes(role);
}

/**
 * Helper function to normalize role strings
 *
 * Handles various role name formats (lowercase, snake_case, etc.)
 * and converts them to the standard PascalCase UserRole format.
 *
 * @param role - Role string to normalize
 * @returns Normalized UserRole or undefined
 *
 * @example
 * ```ts
 * import { normalizeRole } from '@/hooks/useRoles';
 *
 * normalizeRole('admin')      // 'Admin'
 * normalizeRole('recruiter')  // 'Recruiter'
 * normalizeRole('job_seeker') // 'JobSeeker'
 * normalizeRole('invalid')    // undefined
 * ```
 */
export function normalizeRole(role: string): UserRole | undefined {
  const normalized = role
    .toLowerCase()
    .replace(/[_\s](\w)/g, (_, c) => c.toUpperCase())
    .replace(/^\w/, (c) => c.toUpperCase());

  if (isValidRole(normalized)) {
    return normalized;
  }

  return undefined;
}

/**
 * Get role hierarchy level for comparison
 *
 * Returns numeric value for role priority:
 * - Admin: 3 (highest)
 * - Recruiter: 2
 * - JobSeeker: 1 (lowest)
 *
 * @param role - Role to get level for
 * @returns Numeric level (1-3) or 0 if invalid
 *
 * @example
 * ```ts
 * import { getRoleLevel } from '@/hooks/useRoles';
 *
 * getRoleLevel('Admin')      // 3
 * getRoleLevel('Recruiter')  // 2
 * getRoleLevel('JobSeeker')  // 1
 * ```
 */
export function getRoleLevel(role: UserRole): number {
  switch (role) {
    case 'Admin':
      return 3;
    case 'Recruiter':
      return 2;
    case 'JobSeeker':
      return 1;
    default:
      return 0;
  }
}

/**
 * Compare two roles by hierarchy level
 *
 * @param role1 - First role to compare
 * @param role2 - Second role to compare
 * @returns Negative if role1 < role2, positive if role1 > role2, 0 if equal
 *
 * @example
 * ```ts
 * import { compareRoles } from '@/hooks/useRoles';
 *
 * compareRoles('Admin', 'Recruiter')  // > 0 (Admin is higher)
 * compareRoles('JobSeeker', 'Admin')  // < 0 (Admin is higher)
 * compareRoles('Admin', 'Admin')      // 0 (equal)
 * ```
 */
export function compareRoles(role1: UserRole, role2: UserRole): number {
  return getRoleLevel(role1) - getRoleLevel(role2);
}

export default useRoles;
