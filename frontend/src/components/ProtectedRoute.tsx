import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuthContext } from '@/contexts/AuthContext';

/**
 * User role types for role-based access control
 */
export type UserRole = 'jobseeker' | 'recruiter' | 'admin';

/**
 * Props for ProtectedRoute component
 */
export interface ProtectedRouteProps {
  /**
   * Child components to be rendered when authenticated
   */
  children: ReactNode;

  /**
   * Required user role(s) to access this route
   * If provided, only users with matching roles can access
   */
  requiredRoles?: UserRole[];

  /**
   * Redirect path when unauthenticated
   * @default '/login'
   */
  redirectTo?: string;

  /**
   * Whether to show a loading indicator while checking auth
   * @default true
   */
  showLoading?: boolean;
}

/**
 * ProtectedRoute Component
 *
 * A route wrapper component that protects routes requiring authentication.
 * Redirects unauthenticated users to the login page and optionally supports
 * role-based access control.
 *
 * @example
 * ```tsx
 * // Basic protected route
 * <ProtectedRoute>
 *   <DashboardPage />
 * </ProtectedRoute>
 *
 * // With role-based access
 * <ProtectedRoute requiredRoles={['recruiter', 'admin']}>
 *   <RecruiterDashboardPage />
 * </ProtectedRoute>
 *
 * // With custom redirect
 * <ProtectedRoute redirectTo="/auth/login">
 *   <SettingsPage />
 * </ProtectedRoute>
 *
 * // Without loading indicator
 * <ProtectedRoute showLoading={false}>
 *   <QuickViewPage />
 * </ProtectedRoute>
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  redirectTo = '/login',
  showLoading = true,
}) => {
  const { isAuthenticated, loading, user } = useAuthContext();
  const location = useLocation();

  // Show loading indicator while checking authentication
  if (loading) {
    if (showLoading) {
      return (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
          }}
        >
          <CircularProgress size={40} />
        </Box>
      );
    }
    return null;
  }

  // Redirect to login if not authenticated
  // Save the current location to redirect back after login
  if (!isAuthenticated) {
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location }}
        replace
      />
    );
  }

  // Check role-based access control if roles are specified
  if (requiredRoles && requiredRoles.length > 0) {
    // For now, we don't have role info in the User interface
    // This is a placeholder for future role-based access control
    // When user roles are implemented, add the check here
    // Example:
    // const hasRequiredRole = requiredRoles.some(role => user?.role === role);
    // if (!hasRequiredRole) {
    //   return <Navigate to="/unauthorized" replace />;
    // }
  }

  // User is authenticated, render children
  return <>{children}</>;
};

export default ProtectedRoute;
