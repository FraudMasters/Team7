import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Button,
  Box,
  Alert,
  CircularProgress,
  Typography,
  Link,
} from '@mui/material';
import {
  LinkedIn as LinkedInIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api';
import type {
  LinkedInAuthUrlResponse,
  LinkedInCallbackResponse,
} from '@/types/api';

/**
 * Authentication state interface
 */
interface AuthState {
  loading: boolean;
  error: string | null;
  success: boolean;
  connected: boolean;
}

/**
 * LinkedInAuthButton Component Props
 */
interface LinkedInAuthButtonProps {
  /** Callback when authentication completes successfully */
  onAuthComplete?: (accessToken: string) => void;
  /** Callback when authentication fails */
  onAuthError?: (error: string) => void;
  /** Optional scopes to request from LinkedIn */
  scopes?: string[];
  /** Force user to re-login even if already authenticated */
  forceLogin?: boolean;
  /** Button variant */
  variant?: 'text' | 'outlined' | 'contained';
  /** Button size */
  size?: 'small' | 'medium' | 'large';
  /** Disable default redirect handling (useful for custom OAuth flow) */
  disableRedirect?: boolean;
  /** Full width button */
  fullWidth?: boolean;
}

/**
 * LinkedInAuthButton Component
 *
 * Provides LinkedIn OAuth 2.0 authentication functionality with:
 * - One-click LinkedIn authentication
 * - Loading and error states
 * - Success state with access token
 * - Callback support for custom handling
 * - CSRF protection via state parameter
 *
 * @example
 * ```tsx
 * <LinkedInAuthButton
 *   onAuthComplete={(token) => console.log('Access token:', token)}
 *   onAuthError={(error) => console.error('Auth failed:', error)}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // With custom scopes
 * <LinkedInAuthButton
 *   scopes={['r_liteprofile', 'r_emailaddress']}
 *   variant="outlined"
 *   size="large"
 *   onAuthComplete={(token) => {
 *     // Store token and proceed
 *     localStorage.setItem('linkedin_token', token);
 *   }}
 * />
 * ```
 */
const LinkedInAuthButton: React.FC<LinkedInAuthButtonProps> = ({
  onAuthComplete,
  onAuthError,
  scopes,
  forceLogin = false,
  variant = 'contained',
  size = 'medium',
  disableRedirect = false,
  fullWidth = false,
}) => {
  const { t } = useTranslation();

  const [authState, setAuthState] = useState<AuthState>({
    loading: false,
    error: null,
    success: false,
    connected: false,
  });

  /**
   * Handle LinkedIn OAuth callback
   * This is called when the user returns from LinkedIn authorization
   */
  const handleCallback = useCallback(
    async (code: string, state: string) => {
      setAuthState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const response: LinkedInCallbackResponse = await apiClient.processLinkedInCallback(
          { code, state }
        );

        if (response.success && response.access_token) {
          setAuthState({
            loading: false,
            error: null,
            success: true,
            connected: true,
          });
          onAuthComplete?.(response.access_token);
        } else {
          const error = response.message || t('errors.linkedin.authFailed');
          setAuthState((prev) => ({
            ...prev,
            loading: false,
            error,
          }));
          onAuthError?.(error);
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : t('errors.linkedin.networkError');
        setAuthState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
        onAuthError?.(errorMessage);
      }
    },
    [onAuthComplete, onAuthError, t]
  );

  /**
   * Check for OAuth callback in URL on mount
   * This handles the return from LinkedIn authorization page
   */
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      const errorMessage = t('errors.linkedin.accessDenied');
      setAuthState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
      onAuthError?.(errorMessage);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
      return;
    }

    if (code && state) {
      handleCallback(code, state);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [handleCallback, onAuthError, t]);

  /**
   * Initiate LinkedIn OAuth flow
   * Generates auth URL and redirects user to LinkedIn
   */
  const handleLinkedInAuth = useCallback(async () => {
    setAuthState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response: LinkedInAuthUrlResponse = await apiClient.getLinkedInAuthUrl(
        scopes,
        forceLogin
      );

      // Store state for callback verification
      sessionStorage.setItem('linkedin_oauth_state', response.state);

      if (disableRedirect) {
        // Return the URL for custom handling
        setAuthState((prev) => ({ ...prev, loading: false, success: true }));
        onAuthComplete?.(response.auth_url);
      } else {
        // Redirect to LinkedIn authorization page
        window.location.href = response.auth_url;
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : t('errors.linkedin.urlGenerationFailed');
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      onAuthError?.(errorMessage);
    }
  }, [scopes, forceLogin, disableRedirect, onAuthComplete, onAuthError, t]);

  /**
   * Reset authentication state
   */
  const handleReset = useCallback(() => {
    setAuthState({
      loading: false,
      error: null,
      success: false,
      connected: false,
    });
    // Clear stored state
    sessionStorage.removeItem('linkedin_oauth_state');
  }, []);

  return (
    <Box sx={{ width: fullWidth ? '100%' : 'auto' }}>
      {/* Error Alert */}
      {authState.error && (
        <Alert
          severity="error"
          icon={<ErrorIcon />}
          sx={{ mb: 2 }}
          action={
            !authState.loading && (
              <Button
                color="inherit"
                size="small"
                onClick={handleReset}
                disabled={authState.loading}
              >
                {t('common.tryAgain')}
              </Button>
            )
          }
        >
          {authState.error}
        </Alert>
      )}

      {/* Success Alert */}
      {authState.success && authState.connected && (
        <Alert
          severity="success"
          icon={<SuccessIcon />}
          sx={{ mb: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={handleReset}
              disabled={authState.loading}
            >
              {t('linkedin.disconnect')}
            </Button>
          }
        >
          <Typography variant="body2">
            {t('linkedin.auth.success')}
          </Typography>
        </Alert>
      )}

      {/* LinkedIn Auth Button */}
      {!authState.connected && (
        <Button
          variant={variant}
          size={size}
          fullWidth={fullWidth}
          onClick={handleLinkedInAuth}
          disabled={authState.loading}
          startIcon={
            authState.loading ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <LinkedInIcon />
            )
          }
          sx={{
            bgcolor: '#0077b5',
            '&:hover': {
              bgcolor: '#006396',
            },
            '&:disabled': {
              bgcolor: '#0077b5',
              opacity: 0.7,
            },
          }}
        >
          {authState.loading
            ? t('linkedin.auth.connecting')
            : t('linkedin.auth.connect')}
        </Button>
      )}

      {/* Help Text */}
      {!authState.connected && !authState.loading && (
        <Typography
          variant="caption"
          color="text.secondary"
          display="block"
          sx={{ mt: 1, textAlign: 'center' }}
        >
          {t('linkedin.auth.helpText')}{' '}
          <Link
            href="https://www.linkedin.com/help/linkedin/answer/34633"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('linkedin.auth.learnMore')}
          </Link>
        </Typography>
      )}
    </Box>
  );
};

export default LinkedInAuthButton;
