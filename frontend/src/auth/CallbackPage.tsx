import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Container, CircularProgress, Typography, Paper } from '@mui/material';
import { useAuth } from 'react-oidc-context';

/**
 * Get user roles from the OIDC token
 * Roles can be in different locations in Keycloak tokens:
 * - realm_access.roles - realm-level roles
 * - resource_access.{client}.roles - client-level roles
 * - profile.roles - user profile roles
 */
const getUserRoles = (auth: any): string[] => {
  // Try to get roles from various locations in the token/user info
  const roles = new Set<string>();

  // 1. Check realm_access.roles (most common in Keycloak)
  const realmAccess = auth.user?.profile?.realm_access;
  if (realmAccess?.roles && Array.isArray(realmAccess.roles)) {
    realmAccess.roles.forEach((role: string) => roles.add(role));
  }

  // 2. Check resource_access for client-specific roles
  const resourceAccess = auth.user?.profile?.resource_access;
  if (resourceAccess) {
    Object.keys(resourceAccess).forEach((client) => {
      const clientRoles = resourceAccess[client]?.roles;
      if (clientRoles && Array.isArray(clientRoles)) {
        clientRoles.forEach((role: string) => roles.add(role));
      }
    });
  }

  // 3. Check direct profile.roles
  const profileRoles = auth.user?.profile?.roles;
  if (profileRoles && Array.isArray(profileRoles)) {
    profileRoles.forEach((role: string) => roles.add(role));
  }

  return Array.from(roles);
};

/**
 * CallbackPage Component
 *
 * Handles the OIDC authentication callback from Keycloak.
 * This page is the redirect_uri target where Keycloak sends the user
 * after successful authentication.
 *
 * The page:
 * 1. Processes the authorization code from Keycloak
 * 2. Exchanges it for JWT tokens (handled by react-oidc-context)
 * 3. Redirects to the appropriate page based on user role:
 *    - recruiter → /recruiter/dashboard
 *    - job_seeker → /jobs
 *    - no role → /jobs (default)
 *
 * This component must be mounted at the /callback route to match
 * the redirect_uri configured in the OIDC settings.
 *
 * @example
 * ```tsx
 * <Route path="/callback" element={<CallbackPage />} />
 * ```
 */
const CallbackPage: React.FC = () => {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    /**
     * Handle the OIDC callback
     *
     * When the user is redirected back from Keycloak with an authorization code,
     * react-oidc-context automatically exchanges it for tokens.
     *
     * We wait for the authentication to complete, then redirect to the
     * appropriate page based on user role.
     */
    const handleCallback = async () => {
      try {
        // Wait for oidc-client-ts to process the callback
        if (auth.isLoading) {
          // Still processing the callback
          return;
        }

        if (auth.error) {
          // Authentication failed - redirect to login with error
          console.error('Authentication error:', auth.error);
          navigate('/login', { replace: true });
          return;
        }

        if (auth.user) {
          // Authentication succeeded - determine redirect based on role
          const roles = getUserRoles(auth);

          console.log('User roles:', roles);

          // Get original path if stored (from protected route redirect)
          const originalPath = sessionStorage.getItem('oidc-original-path');

          // Determine redirect based on role
          let redirectPath = '/jobs'; // Default for job seekers

          if (roles.includes('admin')) {
            // Admin users go to recruiter dashboard (they have full access)
            redirectPath = originalPath || '/recruiter/dashboard';
          } else if (roles.includes('recruiter')) {
            redirectPath = originalPath || '/recruiter/dashboard';
          } else if (roles.includes('job_seeker')) {
            redirectPath = originalPath || '/jobs';
          }

          navigate(redirectPath, { replace: true });
          sessionStorage.removeItem('oidc-original-path');
        } else {
          // No user yet - might still be loading
          // If not loading and no user, something went wrong
          if (!auth.isLoading) {
            navigate('/login', { replace: true });
          }
        }
      } catch (error) {
        console.error('Callback processing error:', error);
        navigate('/login', { replace: true });
      }
    };

    handleCallback();
  }, [auth, navigate]);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <CircularProgress size={60} sx={{ color: '#667eea' }} />
          <Typography variant="h5" component="h1" gutterBottom>
            Completing Authentication...
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            Please wait while we verify your identity.
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
};

export default CallbackPage;
