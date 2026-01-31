import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Container, Typography, Button, Alert, AlertTitle } from '@mui/material';
import { Refresh as RefreshIcon, Home as HomeIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * ErrorBoundary Props
 */
export interface ErrorBoundaryProps {
  /** Children components to be wrapped by error boundary */
  children: ReactNode;
  /** Custom fallback UI (optional) */
  fallback?: ReactNode;
  /** Callback when error is caught (optional) */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Custom error message title (optional) */
  title?: string;
  /** Show reload button (default: true) */
  showReloadButton?: boolean;
  /** Show home button (default: true) */
  showHomeButton?: boolean;
}

/**
 * ErrorBoundary State
 */
interface ErrorBoundaryState {
  /** Whether an error has occurred */
  hasError: boolean;
  /** The error that occurred */
  error: Error | null;
  /** Additional error information */
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary Internal Props (with i18n hook)
 */
interface ErrorBoundaryInternalProps extends ErrorBoundaryProps {
  /** Translation function */
  t: (key: string, options?: any) => string;
}

/**
 * Error Boundary Fallback Component
 *
 * Displays user-friendly error message when an error occurs.
 *
 * @param props - Fallback component props
 * @returns Error UI component
 */
const ErrorFallback: React.FC<{
  error: Error | null;
  errorInfo: ErrorInfo | null;
  title: string;
  showReloadButton: boolean;
  showHomeButton: boolean;
  t: (key: string, options?: any) => string;
}> = ({ error, errorInfo, title, showReloadButton, showHomeButton, t }) => {
  /**
   * Reload the page to recover from error
   */
  const handleReload = () => {
    window.location.reload();
  };

  /**
   * Navigate to home page
   */
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
        py: 4,
        px: 2,
      }}
    >
      <Container maxWidth="md">
        <Alert
          severity="error"
          variant="outlined"
          sx={{
            borderRadius: 2,
            p: 4,
          }}
        >
          <AlertTitle variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
            {title}
          </AlertTitle>

          <Typography variant="body1" sx={{ mb: 3 }}>
            {t('errorBoundary.message')}
          </Typography>

          {/* Error details (only in development) */}
          {process.env.NODE_ENV === 'development' && error && (
            <Box
              sx={{
                mt: 3,
                p: 2,
                bgcolor: 'error.dark',
                borderRadius: 1,
                overflow: 'auto',
                maxHeight: 300,
              }}
            >
              <Typography variant="subtitle2" sx={{ color: 'common.white', fontWeight: 600, mb: 1 }}>
                {t('errorBoundary.errorDetails')}:
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  color: 'common.white',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {error.toString()}
                {errorInfo && errorInfo.componentStack}
              </Typography>
            </Box>
          )}

          {/* Action buttons */}
          <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
            {showReloadButton && (
              <Button
                variant="contained"
                color="primary"
                startIcon={<RefreshIcon />}
                onClick={handleReload}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  px: 3,
                  py: 1,
                }}
              >
                {t('errorBoundary.reload')}
              </Button>
            )}
            {showHomeButton && (
              <Button
                variant="outlined"
                color="primary"
                startIcon={<HomeIcon />}
                onClick={handleGoHome}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  px: 3,
                  py: 1,
                }}
              >
                {t('errorBoundary.goHome')}
              </Button>
            )}
          </Box>
        </Alert>

        {/* Additional support information */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {t('errorBoundary.support')}
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

/**
 * ErrorBoundary Component
 *
 * A React Error Boundary component that catches JavaScript errors anywhere in the
 * child component tree, logs those errors, and displays a fallback UI.
 *
 * This component prevents the entire app from crashing when an error occurs in a
 * part of the UI, allowing users to continue using the rest of the application.
 *
 * Features:
 * - Catches JavaScript errors in component tree
 * - Logs errors to console and optional callback
 * - Displays user-friendly error message
 * - Provides recovery options (reload, go home)
 * - Shows error details in development mode
 * - Supports internationalization
 * - Customizable fallback UI
 * - Theme-aware styling
 *
 * @example
 * ```tsx
 * // Basic usage
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * ```
 *
 * @example
 * ```tsx
 * // With custom error handler
 * <ErrorBoundary
 *   onError={(error, errorInfo) => {
 *     console.error('Error caught by boundary:', error, errorInfo);
 *     // Log to error tracking service (e.g., Sentry)
 *   }}
 * >
 *   <App />
 * </ErrorBoundary>
 * ```
 *
 * @example
 * ```tsx
 * // With custom fallback UI
 * <ErrorBoundary
 *   fallback={<div>Something went wrong</div>}
 *   showReloadButton={false}
 * >
 *   <App />
 * </ErrorBoundary>
 * ```
 *
 * @example
 * ```tsx
 * // Wrap specific components for granular error handling
 * <ErrorBoundary>
 *   <Layout />
 * </ErrorBoundary>
 * ```
 *
 * @see [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
 */
class ErrorBoundaryClass extends Component<ErrorBoundaryInternalProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryInternalProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Update state when error is caught
   *
   * This lifecycle method is called when an error is thrown in a component.
   * It allows us to display a fallback UI instead of the crashed component.
   *
   * @param error - The error that was thrown
   * @returns New state with error information
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error information
   *
   * Called when an error is caught by the boundary.
   * Logs the error and calls the optional onError callback.
   *
   * @param error - The error that was thrown
   * @param errorInfo - Additional information about the error
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log to console
    console.error('Error caught by ErrorBoundary:', error);
    console.error('Component stack:', errorInfo.componentStack);

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Reset error state
   *
   * Allows the boundary to recover from errors and try rendering again.
   * This can be called when attempting to recover from an error.
   */
  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const {
      children,
      fallback,
      title,
      showReloadButton = true,
      showHomeButton = true,
      t,
    } = this.props;

    // Render fallback UI if error occurred
    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Use default error fallback
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          title={title || t('errorBoundary.defaultTitle')}
          showReloadButton={showReloadButton}
          showHomeButton={showHomeButton}
          t={t}
        />
      );
    }

    // Render children normally if no error
    return children;
  }
}

/**
 * ErrorBoundary Wrapper Component
 *
 * Functional component wrapper that provides i18n context to the class-based ErrorBoundary.
 * This allows us to use the useTranslation hook while maintaining the class-based
 * component required by React's error boundary API.
 *
 * @param props - ErrorBoundary props
 * @returns ErrorBoundary component with i18n support
 */
export const ErrorBoundary: React.FC<ErrorBoundaryProps> = (props) => {
  const { t } = useTranslation();

  return <ErrorBoundaryClass {...props} t={t} />;
};

export default ErrorBoundary;
