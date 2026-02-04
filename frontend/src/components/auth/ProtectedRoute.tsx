import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Box, Typography, Container, Paper, Button } from '@mui/material';
import { LockOutlined } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types/api';

/**
 * Props for ProtectedRoute component
 */
export interface ProtectedRouteProps {
  /**
   * Child components to be rendered when authorization checks pass
   */
  children: ReactNode;

  /**
   * Optional role requirement for access control
   * If provided, only users with this role (or higher) can access the route
   * Multiple roles can be specified using an array
   *
   * @example
   * // Require recruiter role only
   * <ProtectedRoute requiredRole={UserRole.RECRUITER}>
   *
   * // Require admin role only
   * <ProtectedRoute requiredRole={UserRole.ADMIN}>
   *
   * // Require either recruiter or hiring manager
   * <ProtectedRoute requiredRole={[UserRole.RECRUITER, UserRole.HIRING_MANAGER]}>
   */
  requiredRole?: UserRole | UserRole[];

  /**
   * Optional fallback path for redirect when unauthorized
   * Defaults to '/login' for unauthenticated users
   * For authenticated but unauthorized users, shows unauthorized page instead
   *
   * @default '/login'
   */
  redirectTo?: string;
}

/**
 * Unauthorized Access Component
 *
 * Displays a user-friendly "access denied" message when a user is authenticated
 * but lacks the required role to access a protected resource.
 */
const UnauthorizedAccess: React.FC = () => {
  const { t } = useTranslation();

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: 3,
      }}
    >
      <Container maxWidth="md">
        <Paper
          sx={{
            p: 4,
            textAlign: 'center',
            borderRadius: 2,
          }}
        >
          {/* Lock Icon */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              mb: 3,
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: 'warning.light',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <LockOutlined
                sx={{
                  fontSize: 48,
                  color: 'warning.main',
                }}
              />
            </Box>
          </Box>

          {/* Unauthorized Title */}
          <Typography variant="h4" gutterBottom color="text.primary">
            {t('protectedRoute.unauthorized.title', 'Access Denied')}
          </Typography>

          {/* Unauthorized Message */}
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}
          >
            {t(
              'protectedRoute.unauthorized.message',
              "You don't have permission to access this resource. Please contact your administrator if you believe this is an error."
            )}
          </Typography>

          {/* Action Button */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleGoHome}
              size="large"
            >
              {t('protectedRoute.unauthorized.goHome', 'Go to Home')}
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

/**
 * ProtectedRoute Component
 *
 * A route protection component that enforces authentication and optional role-based
 * access control for child routes. Redirects unauthenticated users to login and
 * shows an unauthorized page for authenticated users lacking required roles.
 *
 * Role Hierarchy (from highest to lowest):
 * - ADMIN: Full system access, can access all routes
 * - HIRING_MANAGER: Can access recruiter and viewer routes
 * - RECRUITER: Can access recruiter and viewer routes
 * - VIEWER: Read-only access to basic routes
 *
 * @example
 * ```tsx
 * // Basic authentication check (any authenticated user)
 * <ProtectedRoute>
 *   <DashboardPage />
 * </ProtectedRoute>
 *
 * // Require recruiter role or higher
 * <ProtectedRoute requiredRole={UserRole.RECRUITER}>
 *   <CandidatesKanbanPage />
 * </ProtectedRoute>
 *
 * // Require admin role only
 * <ProtectedRoute requiredRole={UserRole.ADMIN}>
 *   <AdminSettingsPage />
 * </ProtectedRoute>
 *
 * // Require one of multiple roles
 * <ProtectedRoute requiredRole={[UserRole.RECRUITER, UserRole.HIRING_MANAGER]}>
 *   <VacancyManagementPage />
 * </ProtectedRoute>
 *
 * // Use in React Router
 * <Route
 *   path="/recruiter/dashboard"
 *   element={
 *     <ProtectedRoute requiredRole={UserRole.RECRUITER}>
 *       <DashboardPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  redirectTo = '/login',
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { t } = useTranslation();

  // Show loading state while checking authentication
  // This prevents flash of unauthorized content during initial load
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <Typography variant="body1" color="text.secondary">
          {t('protectedRoute.loading', 'Loading...')}
        </Typography>
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    // Save the current location for redirect after login
    // This allows users to return to the page they tried to access
    const currentPath = window.location.pathname + window.location.search;
    if (currentPath !== '/' && currentPath !== '/login') {
      sessionStorage.setItem('redirectAfterLogin', currentPath);
    }

    return <Navigate to={redirectTo} replace />;
  }

  // Check role-based access control if roles are required
  if (requiredRole) {
    const userRole = user.role;

    // If user has no role assigned, deny access
    if (!userRole) {
      return <UnauthorizedAccess />;
    }

    // Define role hierarchy (higher index = higher privilege)
    const roleHierarchy: Record<UserRole, number> = {
      [UserRole.VIEWER]: 0,
      [UserRole.RECRUITER]: 1,
      [UserRole.HIRING_MANAGER]: 2,
      [UserRole.ADMIN]: 3,
    };

    // Normalize required roles to array for consistent handling
    const requiredRoles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];

    // Check if user's role meets any of the required role levels
    // A user can access a route if their role level is >= required role level
    const hasRequiredRole = requiredRoles.some((role) => {
      const requiredLevel = roleHierarchy[role];
      const userLevel = roleHierarchy[userRole];
      return userLevel >= requiredLevel;
    });

    if (!hasRequiredRole) {
      return <UnauthorizedAccess />;
    }
  }

  // All checks passed - render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;
