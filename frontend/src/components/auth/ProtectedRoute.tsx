import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/hooks/useAuth';

/**
 * Protected Route Props
 */
interface ProtectedRouteProps {
  /** Child components to render if authenticated */
  children: ReactNode;
  /** Required role(s) to access the route */
  requiredRoles?: UserRole | UserRole[];
}

/**
 * ProtectedRoute Component
 *
 * Wraps routes that require authentication. Redirects unauthenticated users to login.
 * Optionally checks for specific user roles before granting access.
 *
 * Features:
 * - Redirects unauthenticated users to /login with return URL
 * - Optionally restricts access to specific roles
 * - Shows loading state while checking authentication
 * - Preserves the intended destination for post-login redirect
 *
 * @example
 * ```tsx
 * // Basic authentication check
 * <ProtectedRoute>
 *   <Dashboard />
 * </ProtectedRoute>
 *
 * // Single role requirement
 * <ProtectedRoute requiredRoles="Admin">
 *   <AdminPanel />
 * </ProtectedRoute>
 *
 * // Multiple role requirement (user needs at least one)
 * <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
 *   <RecruiterDashboard />
 * </ProtectedRoute>
 *
 * // In route configuration
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
 *       <Dashboard />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRoles }) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  /**
   * Show loading state while checking authentication
   */
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress size={40} aria-label="Loading authentication status" />
      </Box>
    );
  }

  /**
   * Redirect to login if not authenticated
   * Preserves the intended destination in the redirect URL
   */
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  /**
   * Check role-based access control if roles are specified
   */
  if (requiredRoles) {
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];

    // Check if user has any of the required roles
    const hasRequiredRole = user && roles.includes(user.role);

    if (!hasRequiredRole) {
      // User doesn't have required role - redirect to unauthorized page
      return <Navigate to="/unauthorized" replace />;
    }
  }

  /**
   * User is authenticated and has required roles - render children
   */
  return <>{children}</>;
};

export default ProtectedRoute;
