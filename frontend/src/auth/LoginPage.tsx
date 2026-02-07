import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Login as LoginIcon,
  Email as EmailIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useAuth } from 'react-oidc-context';

/**
 * LoginPage Component
 *
 * Login page that initiates OIDC authentication flow with Keycloak.
 * Since we're using OIDC with Keycloak, the actual authentication happens
 * on the Keycloak server. This page serves as the entry point to trigger
 * the login redirect.
 *
 * Features:
 * - Redirects to Keycloak login page when login button is clicked
 * - Displays loading state during authentication
 * - Shows error messages if authentication fails
 * - Provides "Forgot Password" link (handled by Keycloak)
 * - Provides link to registration page
 * - Redirects authenticated users to the page they came from or home
 *
 * @example
 * ```tsx
 * <Route path="/login" element={<LoginPage />} />
 * ```
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();

  /**
   * Get the redirect path from location state
   * Defaults to home page if no redirect path specified
   */
  const from = (location.state as any)?.from?.pathname || '/';

  /**
   * Handle login button click
   * Triggers OIDC redirect to Keycloak
   */
  const handleLogin = () => {
    // Store original path for redirect after login
    if (location.state?.from?.pathname) {
      sessionStorage.setItem('oidc-original-path', location.state.from.pathname);
    }
    auth.signinRedirect();
  };

  /**
   * Handle registration link click
   * Navigates to registration page
   */
  const handleRegister = () => {
    navigate('/register', { state: { from: location.state } });
  };

  /**
   * Redirect authenticated users away from login page
   */
  React.useEffect(() => {
    if (auth.user && !auth.isLoading) {
      navigate(from, { replace: true });
    }
  }, [auth.user, auth.isLoading, navigate, from]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 2,
              }}
            >
              <LoginIcon sx={{ fontSize: 36, color: 'white' }} />
            </Box>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
              Welcome Back
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Sign in to access the AgentHR platform
            </Typography>
          </Box>

          {/* Error Alert */}
          {auth.error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              Authentication failed. Please try again.
            </Alert>
          )}

          {/* Info Alert about OIDC */}
          <Alert severity="info" sx={{ mb: 3 }}>
            You'll be redirected to Keycloak for secure authentication.
          </Alert>

          {/* Login Form */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Email Field (visual only, actual auth happens on Keycloak) */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Email
              </Typography>
              <TextField
                fullWidth
                placeholder="Enter your email"
                disabled
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                sx={{
                  bgcolor: 'action.disabledBackground',
                  borderRadius: 1,
                  '& .MuiInputBase-root': {
                    bgcolor: 'action.disabledBackground',
                  },
                }}
              />
            </Box>

            {/* Password Field (visual only, actual auth happens on Keycloak) */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Password
              </Typography>
              <TextField
                fullWidth
                type="password"
                placeholder="Enter your password"
                disabled
                InputProps={{
                  startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                sx={{
                  bgcolor: 'action.disabledBackground',
                  borderRadius: 1,
                  '& .MuiInputBase-root': {
                    bgcolor: 'action.disabledBackground',
                  },
                }}
              />
            </Box>

            {/* Forgot Password Link */}
            <Box sx={{ textAlign: 'right' }}>
              <Link
                component="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  handleLogin(); // Keycloak handles forgot password flow
                }}
                sx={{ fontWeight: 500 }}
              >
                Forgot password?
              </Link>
            </Box>

            {/* Login Button */}
            <Button
              fullWidth
              variant="contained"
              size="large"
              startIcon={auth.isLoading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
              onClick={handleLogin}
              disabled={auth.isLoading}
              sx={{
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
              }}
            >
              {auth.isLoading ? 'Signing in...' : 'Sign In'}
            </Button>

            {/* Divider */}
            <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
              <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
              <Typography variant="body2" sx={{ mx: 2, color: 'text.secondary' }}>
                OR
              </Typography>
              <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
            </Box>

            {/* Register Link */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{' '}
                <Link
                  component="button"
                  variant="body2"
                  onClick={handleRegister}
                  sx={{ fontWeight: 600, color: 'primary.main' }}
                >
                  Create one
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Additional Help Text */}
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Contact your administrator if you need access to the platform.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;
