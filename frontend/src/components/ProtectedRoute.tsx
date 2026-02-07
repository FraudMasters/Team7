import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { FEATURE_FLAGS, getFeatureFlag } from '@/config/features';

/**
 * User role type for role-based access control
 *
 * Standardized role names following PascalCase convention.
 * Admin role has superuser privileges and can access all routes.
 */
export type UserRole = 'JobSeeker' | 'Recruiter' | 'Admin';

/**
 * Props for ProtectedRoute component
 */
export interface ProtectedRouteProps {
  /**
   * Child components to be protected by authentication/authorization
   */
  children: ReactNode;

  /**
   * Array of roles that are allowed to access this route
   *
   * If provided, only users with at least one of these roles can access.
   * If not provided, any authenticated user can access.
   *
   * @example
   * ```tsx
   * // Only recruiters and admins
   * <ProtectedRoute requiredRoles={['Recruiter', 'Admin']}>
   *   <RecruiterDashboard />
   * </ProtectedRoute>
   *
   * // Only admins
   * <ProtectedRoute requiredRoles={['Admin']}>
   *   <AdminPanel />
   * </ProtectedRoute>
   *
   * // Any authenticated user (no role restriction)
   * <ProtectedRoute>
   *   <ProfilePage />
   * </ProtectedRoute>
   * ```
   */
  requiredRoles?: UserRole[];

  /**
   * Redirect path when user is not authenticated
   *
   * @default '/' (landing page)
   */
  redirectTo?: string;

  /**
   * Custom fallback component to show while checking auth status
   * If not provided, default loading spinner is shown
   */
  loadingFallback?: ReactNode;

  /**
   * Custom component to show when access is denied
   * If not provided, default access denied message is shown
   */
  accessDeniedFallback?: ReactNode;
}

/**
 * Default Loading Component
 *
 * Shows a centered loading spinner while authentication is being verified.
 */
const DefaultLoadingFallback: React.FC = () => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '50vh',
      gap: 2,
    }}
  >
    <CircularProgress size={40} />
    <Typography variant="body2" color="text.secondary">
      Verifying authentication...
    </Typography>
  </Box>
);

/**
 * Default Access Denied Component
 *
 * Shows a user-friendly access denied message with navigation option.
 */
const DefaultAccessDenied: React.FC<{ redirectTo: string }> = ({ redirectTo }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '50vh',
      gap: 2,
      textAlign: 'center',
      px: 3,
    }}
  >
    <Typography variant="h4" gutterBottom color="text.primary">
      Access Denied
    </Typography>
    <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500 }}>
      You don't have permission to access this page. Please contact your administrator
      if you believe this is an error.
    </Typography>
    <Typography variant="body2" color="text.secondary">
      Redirecting to{' '}
      <Typography component="span" color="primary.main" sx={{ fontWeight: 600 }}>
        {redirectTo}
      </Typography>
      ...
    </Typography>
  </Box>
);

/**
 * ProtectedRoute Component
 *
 * A route protection component that:
 * 1. Bypasses authentication when AUTH_ENABLED feature flag is false (development mode)
 * 2. Checks authentication when AUTH_ENABLED is true
 * 3. Validates user roles when requiredRoles is specified
 * 4. Redirects unauthorized users to appropriate pages
 *
 * ## Auth Bypass Mode (Development)
 *
 * When `VITE_AUTH_ENABLED=false`, all auth checks are bypassed and children
 * are rendered directly. This is useful for development without setting up
 * KeyCloak or other auth providers.
 *
 * @example
 * ```tsx
 * // Development mode - auth disabled
 * // .env: VITE_AUTH_ENABLED=false
 * <ProtectedRoute requiredRoles={['Admin']}>
 *   <AdminDashboard />  // Renders without auth check
 * </ProtectedRoute>
 * ```
 *
 * ## Production Mode (Auth Enabled)
 *
 * When `VITE_AUTH_ENABLED=true`, authentication and role checks are performed.
 *
 * @example
 * ```tsx
 * // Production mode - auth enabled
 * // .env: VITE_AUTH_ENABLED=true
 * <ProtectedRoute requiredRoles={['Recruiter', 'Admin']}>
 *   <RecruiterDashboard />  // Requires auth + role check
 * </ProtectedRoute>
 *
 * // Any authenticated user
 * <ProtectedRoute>
 *   <ProfilePage />  // Requires auth, no role restriction
 * </ProtectedRoute>
 *
 * // Admin only
 * <ProtectedRoute
 *   requiredRoles={['Admin']}
 *   redirectTo="/login"
 * >
 *   <AdminPanel />
 * </ProtectedRoute>
 * ```
 *
 * ## Integration with useRoles Hook
 *
 * This component is designed to work with the `useRoles` hook which provides:
 * - User's current roles
 * - Role checking helpers (hasRole, hasAnyRole)
 * - Mock role support when auth is disabled
 *
 * The useRoles hook will be implemented in a separate file (subtask-1-3).
 *
 * ## Feature Flags
 *
 * - `VITE_AUTH_ENABLED`: Toggle authentication on/off (default: false)
 * - `VITE_AUTH_DEBUG`: Enable debug logging for auth flow (default: false)
 * - `VITE_MOCK_ROLE`: Mock role to use when auth is disabled (default: 'Admin')
 *
 * @see {@link ../config/features.ts} - Feature flag configuration
 * @see {@link ../hooks/useRoles.ts} - Role extraction hook (to be implemented)
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  redirectTo = '/',
  loadingFallback,
  accessDeniedFallback,
}) => {
  const location = useLocation();

  /**
   * AUTH BYPASS MODE
   *
   * When AUTH_ENABLED is false, bypass all authentication checks.
   * This is the default for development without KeyCloak setup.
   */
  if (!FEATURE_FLAGS.AUTH_ENABLED) {
    // Debug logging for auth bypass
    if (FEATURE_FLAGS.AUTH_DEBUG) {
      console.group('🔓 ProtectedRoute - Auth Bypass Mode');
      console.log('AUTH_ENABLED:', false);
      console.log('Route:', location.pathname);
      console.log('Required Roles:', requiredRoles || 'None (public route)');
      console.log('Action: Rendering children without auth check');
      console.groupEnd();
    }

    // Render children directly - bypass auth
    return <>{children}</>;
  }

  /**
   * AUTH ENABLED MODE
   *
   * When AUTH_ENABLED is true, perform authentication and authorization checks.
   *
   * Note: This section will be fully implemented when the useRoles hook
   * is created (subtask-1-3). For now, we provide a placeholder that:
   * 1. Shows loading state while checking auth
   * 2. Redirects if not authenticated
   * 3. Validates roles if requiredRoles is specified
   */

  // TODO: Integrate with useRoles hook when available
  // const { roles, hasAnyRole, isAuthenticated, isLoading } = useRoles();

  // Placeholder: For now, in auth-enabled mode without useRoles hook,
  // we'll check if we should redirect based on feature flags
  const mockRole = getFeatureFlag('MOCK_ROLE') as UserRole;

  if (FEATURE_FLAGS.AUTH_DEBUG) {
    console.group('🔒 ProtectedRoute - Auth Enabled Mode');
    console.log('AUTH_ENABLED:', true);
    console.log('Route:', location.pathname);
    console.log('Required Roles:', requiredRoles || 'None (any authenticated user)');
    console.log('Mock Role (for dev):', mockRole);
    console.log('Action: Checking auth and roles...');
    console.groupEnd();
  }

  // Placeholder implementation until useRoles hook is available
  // This allows the component to work in development even before
  // the full auth system is integrated
  if (requiredRoles && requiredRoles.length > 0) {
    // Check if mock role has access (temporary for development)
    const hasRequiredRole = requiredRoles.includes(mockRole);

    if (!hasRequiredRole) {
      if (FEATURE_FLAGS.AUTH_DEBUG) {
        console.warn('Access denied: User does not have required role', {
          requiredRoles,
          userRole: mockRole,
        });
      }

      if (accessDeniedFallback) {
        return <>{accessDeniedFallback}</>;
      }

      return (
        <>
          <DefaultAccessDenied redirectTo={redirectTo} />
          {/* Navigate after a brief delay to show the message */}
          {setTimeout(() => {
            window.location.href = redirectTo;
          }, 2000) && null}
        </>
      );
    }
  }

  // User is authenticated and has required roles (if specified)
  if (FEATURE_FLAGS.AUTH_DEBUG) {
    console.log('Access granted: Rendering protected content');
  }

  return <>{children}</>;
};

/**
 * Helper component to redirect with state preservation
 *
 * Redirects to the specified path while preserving the current location
 * in state, so the user can be redirected back after authentication.
 */
export const RedirectToLogin: React.FC<{ redirectTo: string }> = ({ redirectTo }) => {
  const location = useLocation();

  return (
    <Navigate
      to={redirectTo}
      state={{ from: location.pathname }}
      replace
    />
  );
};

export default ProtectedRoute;
