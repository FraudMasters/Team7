/**
 * ServiceErrorFallback Component
 *
 * A specialized error fallback component for handling microservice failures.
 * Displays user-friendly error messages when backend services are unavailable
 * and provides retry mechanisms with configurable options.
 *
 * @example
 * ```tsx
 * // Basic usage with ApiError
 * <ServiceErrorFallback
 *   error={{ detail: 'Service unavailable', status: 503 }}
 *   onRetry={() => refetch()}
 * />
 *
 * // With custom service name
 * <ServiceErrorFallback
 *   error={{ detail: 'Network error', status: 0 }}
 *   serviceName="Candidate Service"
 *   onRetry={() => refetch()}
 * />
 *
 * // With custom actions
 * <ServiceErrorFallback
 *   error={apiError}
 *   serviceName="Analytics Service"
 *   onRetry={() => refetch()}
 *   secondaryActions={[
 *     { label: 'Go to Dashboard', onClick: () => navigate('/dashboard') },
 *   ]}
 * />
 *
 * // Compact mode for inline display
 * <ServiceErrorFallback
 *   error={error}
 *   compact
 *   onRetry={() => refetch()}
 * />
 *
 * // Without retry button
 * <ServiceErrorFallback
 *   error={{ detail: 'Service temporarily unavailable', status: 503 }}
 *   showRetry={false}
 * />
 * ```
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Container,
  CircularProgress,
  Alert,
  AlertTitle,
  IconButton,
  Collapse,
  alpha,
} from '@mui/material';
import {
  CloudOff,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  ErrorOutline,
  WifiOff,
  Schedule,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import type { ApiError } from '@/types/api';

/**
 * Props for ServiceErrorFallback component
 */
export interface ServiceErrorFallbackProps {
  /**
   * The API error object containing error details
   */
  error: ApiError | Error;

  /**
   * Name of the microservice that failed
   * If not provided, a generic service name is used
   */
  serviceName?: string;

  /**
   * Callback function to retry the failed operation
   * If provided, a retry button will be shown
   */
  onRetry?: () => void | Promise<void>;

  /**
   * Additional secondary actions to display
   */
  secondaryActions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'text' | 'outlined' | 'contained';
  }>;

  /**
   * Display mode
   * - 'fullPage': Full-page error display (default)
   * - 'compact': Compact inline error display
   * - 'alert': Alert-style inline error
   * @default 'fullPage'
   */
  mode?: 'fullPage' | 'compact' | 'alert';

  /**
   * Whether to show the retry button
   * @default true
   */
  showRetry?: boolean;

  /**
   * Whether to show error details in collapsible section
   * @default false
   */
  showDetails?: boolean;

  /**
   * Custom error message to override the default
   */
  message?: string;

  /**
   * Custom title to override the default
   */
  title?: string;

  /**
   * Whether to show a home button
   * @default false
   */
  showHomeButton?: boolean;

  /**
   * Additional component to render below the error message
   */
  additionalInfo?: React.ReactNode;
}

/**
 * Determine error category from ApiError status code
 */
const getErrorCategory = (error: ApiError | Error): {
  type: 'network' | 'timeout' | 'server' | 'unavailable';
  icon: React.ReactElement;
  defaultTitle: string;
  defaultMessage: string;
} => {
  const status = 'status' in error ? error.status : undefined;

  // Network error (no response)
  if (status === 0 || (error.message && (
    error.message.toLowerCase().includes('network') ||
    error.message.toLowerCase().includes('connection')
  ))) {
    return {
      type: 'network',
      icon: <WifiOff />,
      defaultTitle: 'Network Error',
      defaultMessage: 'Unable to connect to the service. Please check your internet connection.',
    };
  }

  // Timeout error
  if (status === 408 || (error.message && (
    error.message.toLowerCase().includes('timeout')
  ))) {
    return {
      type: 'timeout',
      icon: <Schedule />,
      defaultTitle: 'Request Timeout',
      defaultMessage: 'The service took too long to respond. Please try again.',
    };
  }

  // Service unavailable
  if (status === 503 || status === 502) {
    return {
      type: 'unavailable',
      icon: <CloudOff />,
      defaultTitle: 'Service Unavailable',
      defaultMessage: 'The service is temporarily unavailable. Please try again later.',
    };
  }

  // Default server error
  return {
    type: 'server',
    icon: <CloudOff />,
    defaultTitle: 'Service Error',
    defaultMessage: 'An error occurred while communicating with the service.',
  };
};

/**
 * ServiceErrorFallback Component
 */
const ServiceErrorFallback: React.FC<ServiceErrorFallbackProps> = ({
  error,
  serviceName,
  onRetry,
  secondaryActions = [],
  mode = 'fullPage',
  showRetry = true,
  showDetails: showDetailsProp = false,
  message,
  title,
  showHomeButton = false,
  additionalInfo,
}) => {
  const { t } = useTranslation();
  const [isRetrying, setIsRetrying] = useState(false);
  const [detailsExpanded, setDetailsExpanded] = useState(false);

  // Get error category
  const errorCategory = React.useMemo(() => getErrorCategory(error), [error]);

  // Get error message
  const errorMessage = message ||
    ('detail' in error ? error.detail : error.message) ||
    errorCategory.defaultMessage;

  // Get error title
  const errorTitle = title || errorCategory.defaultTitle;

  // Handle retry action
  const handleRetry = async () => {
    if (!onRetry) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  // Handle go home
  const handleGoHome = () => {
    window.location.href = '/';
  };

  // Get display text with service name if provided
  const getDisplayMessage = () => {
    if (serviceName) {
      return `${errorMessage} (${serviceName})`;
    }
    return errorMessage;
  };

  // Alert mode (compact inline display)
  if (mode === 'alert') {
    return (
      <Alert
        severity="error"
        icon={errorCategory.icon}
        action={
          showRetry && onRetry && (
            <Button
              size="small"
              color="inherit"
              onClick={handleRetry}
              disabled={isRetrying}
              startIcon={isRetrying ? <CircularProgress size={16} /> : <RefreshIcon />}
            >
              {isRetrying ? 'Retrying...' : 'Retry'}
            </Button>
          )
        }
      >
        <AlertTitle>{errorTitle}</AlertTitle>
        <Typography variant="body2">{getDisplayMessage()}</Typography>
      </Alert>
    );
  }

  // Compact mode
  if (mode === 'compact') {
    return (
      <Paper
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          bgcolor: 'error.lighter',
          border: '1px solid',
          borderColor: 'error.light',
        }}
      >
        <Box sx={{ color: 'error.main' }}>
          {errorCategory.icon}
        </Box>
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle2" color="text.primary">
            {errorTitle}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {getDisplayMessage()}
          </Typography>
        </Box>
        {showRetry && onRetry && (
          <Button
            size="small"
            variant="outlined"
            onClick={handleRetry}
            disabled={isRetrying}
            startIcon={isRetrying ? <CircularProgress size={16} /> : <RefreshIcon />}
          >
            {isRetrying ? 'Retrying...' : 'Retry'}
          </Button>
        )}
      </Paper>
    );
  }

  // Full page mode (default)
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
                color: 'error.main',
              }}
            >
              {errorCategory.icon}
            </Box>
          </Box>

          {/* Error Title */}
          <Typography variant="h4" gutterBottom color="text.primary">
            {errorTitle}
          </Typography>

          {/* Error Message */}
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}
          >
            {getDisplayMessage()}
          </Typography>

          {/* Additional Info */}
          {additionalInfo && (
            <Box sx={{ mb: 3 }}>
              {additionalInfo}
            </Box>
          )}

          {/* Primary Actions */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 2 }}>
            {showRetry && onRetry && (
              <Button
                variant="contained"
                color="primary"
                startIcon={isRetrying ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={handleRetry}
                disabled={isRetrying}
                size="large"
              >
                {isRetrying ? t('serviceError.retrying', 'Retrying...') : t('serviceError.retry', 'Retry')}
              </Button>
            )}
            {showHomeButton && (
              <Button
                variant="outlined"
                color="primary"
                startIcon={<HomeIcon />}
                onClick={handleGoHome}
                size="large"
              >
                {t('serviceError.goHome', 'Go Home')}
              </Button>
            )}
          </Box>

          {/* Secondary Actions */}
          {secondaryActions.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap', mb: 3 }}>
              {secondaryActions.map((action, index) => (
                <Button
                  key={index}
                  variant={action.variant || 'text'}
                  color="primary"
                  onClick={action.onClick}
                  size="small"
                >
                  {action.label}
                </Button>
              ))}
            </Box>
          )}

          {/* Error Details Toggle */}
          {showDetailsProp && (
            <Box sx={{ mt: 3 }}>
              <Button
                size="small"
                onClick={() => setDetailsExpanded(!detailsExpanded)}
                startIcon={detailsExpanded ? <ExpandLess /> : <ExpandMore />}
                sx={{ mb: 1 }}
              >
                {detailsExpanded ? 'Hide' : 'Show'} Error Details
              </Button>
              <Collapse in={detailsExpanded}>
                <Box
                  sx={{
                    p: 2,
                    bgcolor: alpha('#000', 0.05),
                    borderRadius: 1,
                    textAlign: 'left',
                    maxWidth: 600,
                    mx: 'auto',
                  }}
                >
                  <Typography variant="subtitle2" gutterBottom color="text.primary">
                    Error Details:
                  </Typography>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      color: 'error.main',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {errorMessage}
                  </Typography>
                  {'status' in error && error.status && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Status Code: {error.status}
                    </Typography>
                  )}
                </Box>
              </Collapse>
            </Box>
          )}
        </Paper>
      </Container>
    </Box>
  );
};

/**
 * Pre-configured service error fallback components for common scenarios
 */

/**
 * Network error fallback
 */
export const NetworkErrorFallback: React.FC<Omit<ServiceErrorFallbackProps, 'error'>> = (props) => (
  <ServiceErrorFallback
    error={{ detail: 'Network error. Please check your connection.', status: 0 }}
    {...props}
  />
);

/**
 * Timeout error fallback
 */
export const TimeoutErrorFallback: React.FC<Omit<ServiceErrorFallbackProps, 'error'>> = (props) => (
  <ServiceErrorFallback
    error={{ detail: 'Request timeout. The service took too long to respond.', status: 408 }}
    {...props}
  />
);

/**
 * Service unavailable fallback
 */
export const ServiceUnavailableFallback: React.FC<Omit<ServiceErrorFallbackProps, 'error'>> = (props) => (
  <ServiceErrorFallback
    error={{ detail: 'Service temporarily unavailable. Please try again later.', status: 503 }}
    {...props}
  />
);

/**
 * Bad gateway fallback
 */
export const BadGatewayFallback: React.FC<Omit<ServiceErrorFallbackProps, 'error'>> = (props) => (
  <ServiceErrorFallback
    error={{ detail: 'Bad gateway. Unable to reach the service.', status: 502 }}
    {...props}
  />
);

export default ServiceErrorFallback;
