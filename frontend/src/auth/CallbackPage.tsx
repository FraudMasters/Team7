import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Container, CircularProgress, Typography, Paper } from '@mui/material';
import { useAuth } from 'react-oidc-context';

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
 * 3. Redirects to the home page or originally requested page
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
     * We wait for the authentication to complete, then redirect to the home page.
     * In a more sophisticated implementation, we could redirect to the page
     * the user originally tried to access (stored in session storage).
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
          // Authentication succeeded - redirect to home
          // In production, you might redirect to the original destination
          const originalPath = sessionStorage.getItem('oidc-original-path');
          navigate(originalPath || '/', { replace: true });
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
