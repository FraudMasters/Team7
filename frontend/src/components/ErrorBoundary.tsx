import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { ErrorOutline, Refresh as RefreshIcon, Home as HomeIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Props for ErrorBoundary component
 */
export interface ErrorBoundaryProps {
  /**
   * Child components to be wrapped by the error boundary
   */
  children: ReactNode;

  /**
   * Custom fallback component to render when an error is caught
   * If not provided, the default ErrorFallback is used
   */
  fallback?: ReactNode;

  /**
   * Custom error handler function called when an error is caught
   * Use this for custom error logging or reporting
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;

  /**
   * Whether to show the error details (stack trace, component stack)
   * @default false (hide details in production)
   */
  showDetails?: boolean;
}

/**
 * State for ErrorBoundary component
 */
interface ErrorBoundaryState {
  /**
   * Whether an error has been caught
   */
  hasError: boolean;

  /**
   * The error object (if an error was caught)
   */
  error: Error | null;

  /**
   * Error info containing component stack (if an error was caught)
   */
  errorInfo: ErrorInfo | null;
}

/**
 * Default Error Fallback Component
 *
 * Displays a user-friendly error message with recovery actions.
 */
const ErrorFallback: React.FC<{
  error: Error;
  errorInfo: ErrorInfo;
  showDetails?: boolean;
  onReset?: () => void;
}> = ({ error, errorInfo, showDetails = false, onReset }) => {
  const { t } = useTranslation();

  const handleRefresh = () => {
    window.location.reload();
  };

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
          {/* Error Icon */}
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
                bgcolor: 'error.light',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ErrorOutline
                sx={{
                  fontSize: 48,
                  color: 'error.main',
                }}
              />
            </Box>
          </Box>

          {/* Error Title */}
          <Typography variant="h4" gutterBottom color="text.primary">
            {t('errorBoundary.title', 'Something went wrong')}
          </Typography>

          {/* Error Message */}
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}
          >
            {t(
              'errorBoundary.message',
              'An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.'
            )}
          </Typography>

          {/* Recovery Actions */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 4 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              size="large"
            >
              {t('errorBoundary.refresh', 'Refresh Page')}
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<HomeIcon />}
              onClick={handleGoHome}
              size="large"
            >
              {t('errorBoundary.goHome', 'Go Home')}
            </Button>
          </Box>

          {/* Error Details (development or when explicitly enabled) */}
          {showDetails && (process.env.NODE_ENV === 'development' || import.meta.env.DEV) && (
            <Box
              sx={{
                mt: 4,
                p: 2,
                bgcolor: 'grey.100',
                borderRadius: 1,
                textAlign: 'left',
                overflow: 'auto',
                maxHeight: 300,
              }}
            >
              <Typography variant="subtitle2" gutterBottom color="text.primary">
                {t('errorBoundary.errorDetails', 'Error Details:')}
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  color: 'error.main',
                  mb: 2,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {error.message}
              </Typography>
              {error.stack && (
                <>
                  <Typography variant="subtitle2" gutterBottom color="text.primary">
                    {t('errorBoundary.stackTrace', 'Stack Trace:')}
                  </Typography>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      color: 'text.secondary',
                      mb: 2,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {error.stack}
                  </Typography>
                </>
              )}
              {errorInfo && errorInfo.componentStack && (
                <>
                  <Typography variant="subtitle2" gutterBottom color="text.primary">
                    {t('errorBoundary.componentStack', 'Component Stack:')}
                  </Typography>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      color: 'text.secondary',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {errorInfo.componentStack}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </Paper>
      </Container>
    </Box>
  );
};

/**
 * ErrorBoundary Component
 *
 * A React error boundary component that catches JavaScript errors anywhere in the
 * child component tree, logs those errors, and displays a fallback UI instead of
 * crashing the entire application.
 *
 * This component is designed for React 18, which requires class components for
 * error boundaries (React 19 will have built-in error boundary support).
 *
 * @example
 * ```tsx
 * // Basic usage with default fallback
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 *
 * // With custom error handler
 * <ErrorBoundary
 *   onError={(error, errorInfo) => {
 *     console.error('Error caught by boundary:', error, errorInfo);
 *     logErrorToService(error, errorInfo);
 *   }}
 * >
 *   <MyComponent />
 * </ErrorBoundary>
 *
 * // With custom fallback component
 * <ErrorBoundary
 *   fallback={<CustomErrorFallback />}
 *   showDetails={true}
 * >
 *   <MyComponent />
 * </ErrorBoundary>
 *
 * // Wrap entire page for maximum protection
 * <ErrorBoundary>
 *   <UploadPage />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Static method to update state when an error is thrown
   * This is called when an error is caught in the component tree
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Called when an error is caught
   * Logs error information and calls the custom onError handler if provided
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Log error to console for debugging
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error Info:', errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to external error tracking service if available
    // Example: Sentry, LogRocket, etc.
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      });
    }
  }

  /**
   * Reset the error boundary state
   * Call this to recover from an error and retry rendering
   */
  resetErrorBoundary = (): void => {
    const { error } = this.state;

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Call onReset if provided (optional prop, not in interface yet)
    if ((this.props as any).onReset && typeof (this.props as any).onReset === 'function') {
      (this.props as any).onReset();
    }
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, showDetails } = this.props;

    // If an error was caught, render the fallback UI
    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Use default error fallback if error and errorInfo are available
      if (error && errorInfo) {
        return (
          <ErrorFallback
            error={error}
            errorInfo={errorInfo}
            showDetails={showDetails}
            onReset={this.resetErrorBoundary}
          />
        );
      }
    }

    // Render children normally if no error
    return children;
  }
}

export default ErrorBoundary;
