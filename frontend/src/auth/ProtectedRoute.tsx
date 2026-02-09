import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography, Container } from '@mui/material';
import { useAuthContext, UserRole } from '@/contexts/AuthContext';

/**
 * Props for ProtectedRoute component
 */
interface ProtectedRouteProps {
  /** Child component(s) to render if authentication/authorization succeeds */
  children: ReactNode;
  /** Optional: Single role or array of roles required to access the route */
  requiredRoles?: UserRole | UserRole[];
  /** Optional: Custom path to redirect to if not authenticated (default: /login) */
  redirectTo?: string;
  /** Optional: Custom path to redirect to if user lacks required roles (default: /unauthorized) */
  unauthorizedTo?: string;
}

/**
 * ProtectedRoute Component
 *
 * Wrapper component for protecting routes that require authentication and/or specific roles.
 * Integrates with AuthContext to check user authentication status and role-based access control.
 *
 * Features:
 * - Redirects unauthenticated users to login page (default: /login)
 * - Shows loading spinner while checking authentication status
 * - Validates role requirements before rendering protected content
 * - Redirects unauthorized users (lacking required roles) to unauthorized page
 * - Preserves current location for post-login redirect
 *
 * @example
 * ```tsx
 * // Basic authentication check
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute>
 *       <DashboardPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // With role requirement (single role)
 * <Route
 *   path="/admin/users"
 *   element={
 *     <ProtectedRoute requiredRoles="Admin">
 *       <UserManagementPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // With role requirement (multiple roles - user needs at least one)
 * <Route
 *   path="/recruiter/vacancies"
 *   element={
 *     <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
 *       <VacancyManagementPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // With custom redirect paths
 * <Route
 *   path="/premium"
 *   element={
 *     <ProtectedRoute
 *       requiredRoles="Admin"
 *       redirectTo="/auth/login"
 *       unauthorizedTo="/403"
 *     >
 *       <PremiumPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  redirectTo = '/login',
  unauthorizedTo = '/unauthorized',
}) => {
  const { isAuthenticated, isLoading, isInitialized, hasRole, hasAnyRole, user } = useAuthContext();
  const location = useLocation();

  /**
   * Show loading state while checking authentication
   * This shows during initial auth check and during auth operations
   */
  if (isLoading || !isInitialized) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
        }}
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" sx={{ mt: 3, color: 'text.secondary' }}>
          {!isInitialized ? 'Loading...' : 'Checking authentication...'}
        </Typography>
      </Box>
    );
  }

  /**
   * Redirect to login if not authenticated
   * Preserves current location for redirect after login
   */
  if (!isAuthenticated) {
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location }}
        replace
      />
    );
  }

  /**
   * Check role requirements if specified
   */
  if (requiredRoles) {
    const hasRequiredRole = Array.isArray(requiredRoles)
      ? hasAnyRole(requiredRoles)
      : hasRole(requiredRoles);

    /**
     * Redirect to unauthorized page if user lacks required roles
     */
    if (!hasRequiredRole) {
      return (
        <Container maxWidth="md" sx={{ py: 8 }}>
          <Box
            sx={{
              textAlign: 'center',
              py: 8,
              px: 3,
              bgcolor: 'background.paper',
              borderRadius: 2,
              boxShadow: 1,
            }}
          >
            <Typography variant="h4" gutterBottom color="error">
              Access Denied
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              You do not have permission to access this page.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Required roles:{' '}
              <strong>
                {Array.isArray(requiredRoles) ? requiredRoles.join(', ') : requiredRoles}
              </strong>
            </Typography>
          </Box>
        </Container>
      );
    }
  }

  /**
   * Render protected content if all checks pass
   */
  return <>{children}</>;
};

export default ProtectedRoute;
