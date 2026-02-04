import { useAuthContext } from '../contexts/AuthContext';

/**
 * Re-export auth types for convenience
 */
export type { User, UserRole, AuthTokens } from '../contexts/AuthContext';

/**
 * Authentication State
 *
 * Provides access to authentication state and login/logout functions.
 * This is a convenient hook wrapper around the AuthContext.
 *
 * @example
 * ```tsx
 * const { isAuthenticated, user, login, logout } = useAuth();
 *
 * // Check authentication
 * if (isAuthenticated) {
 *   console.log(`Welcome, ${user?.name}`);
 * }
 *
 * // Login
 * await login('user@example.com', 'password');
 *
 * // Logout
 * logout();
 * ```
 */
export function useAuth() {
  return useAuthContext();
}
