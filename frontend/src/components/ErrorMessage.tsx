import React, { useState, useCallback, useEffect, ReactNode } from 'react';
import { Snackbar, Alert, AlertProps, Slide, SlideProps, Button, Box, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

/**
 * Slide transition for Snackbar
 *
 * Animates the message sliding in from the bottom.
 */
function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

/**
 * Action button configuration for error messages
 */
export interface ErrorAction {
  /** Label for the action button */
  label: string;
  /** Click handler for the action */
  onClick: () => void;
  /** Whether this action should close the error message */
  closeOnClick?: boolean;
}

/**
 * Structured error message details
 * Provides comprehensive error information with actionable guidance
 */
export interface ErrorDetails {
  /** Brief title of what went wrong */
  title: string;
  /** Detailed explanation of the error */
  description: string;
  /** Why the error occurred (root cause) */
  reason?: string;
  /** How to fix the error (actionable steps) */
  solution?: string;
  /** Optional action buttons */
  actions?: ErrorAction[];
}

/**
 * Error message configuration
 */
export interface ErrorMessageConfig {
  /** Whether the message is currently visible */
  open: boolean;
  /** The message content (can be simple string or structured ErrorDetails) */
  message: string | ErrorDetails;
  /** Severity level of the message */
  severity: AlertProps['severity'];
  /** Auto-hide duration in milliseconds (null for no auto-hide) */
  autoHideDuration?: number | null;
}

/**
 * ErrorMessage Component Props
 */
export interface ErrorMessageProps {
  /** Custom error message state (optional, component manages its own state if not provided) */
  errorState?: ErrorMessageConfig;
  /** Callback when error state changes (optional) */
  onErrorStateChange?: (state: ErrorMessageConfig) => void;
  /** Position of the snackbar */
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
  /** Enable slide transition */
  enableSlideTransition?: boolean;
  /** Children wrapper to provide error context (optional) */
  children?: ReactNode;
}

/**
 * Predefined error templates for common failures
 * Each template includes: what went wrong, why it happened, and how to fix it
 */
export const ErrorTemplates = {
  /**
   * Network connection error
   * Occurs when the application cannot reach the backend server
   */
  networkError: (details?: { endpoint?: string }): ErrorDetails => ({
    title: 'Connection Error',
    description: 'Unable to connect to the server. Please check your internet connection.',
    reason: details?.endpoint
      ? `The request to ${details.endpoint} failed due to a network issue.`
      : 'A network error occurred while communicating with the server.',
    solution: '1. Check your internet connection\n2. Verify the server is running\n3. Try refreshing the page\n4. Contact support if the issue persists',
    actions: [
      { label: 'Retry', onClick: () => window.location.reload(), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Authentication error
   * Occurs when user is not logged in or session has expired
   */
  authError: (): ErrorDetails => ({
    title: 'Authentication Required',
    description: 'You need to log in to access this feature.',
    reason: 'Your session may have expired or you are not logged in.',
    solution: 'Please log in again to continue. If the problem persists, try clearing your browser cookies.',
    actions: [
      { label: 'Log In', onClick: () => (window.location.href = '/login'), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Permission denied error
   * Occurs when user tries to access resources they don't have permission for
   */
  permissionError: (details?: { resource?: string }): ErrorDetails => ({
    title: 'Access Denied',
    description: details?.resource
      ? `You don't have permission to access ${details.resource}.`
      : "You don't have permission to perform this action.",
    reason: 'Your account does not have the required permissions for this resource.',
    solution: 'Contact your administrator to request access, or try accessing a different resource.',
    actions: [
      { label: 'Go Back', onClick: () => window.history.back(), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * File upload error - invalid type
   */
  fileTypeError: (details?: { allowedTypes?: string[] }): ErrorDetails => ({
    title: 'Invalid File Type',
    description: 'The file you uploaded is not supported.',
    reason: 'This file type is not accepted by the system.',
    solution: details?.allowedTypes
      ? `Please upload one of the following file types: ${details.allowedTypes.join(', ')}`
      : 'Please upload a PDF or DOCX file.',
    actions: [
      { label: 'Choose Another File', onClick: () => {}, closeOnClick: true },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * File upload error - size exceeded
   */
  fileSizeError: (details?: { maxSize?: string }): ErrorDetails => ({
    title: 'File Too Large',
    description: 'The file you uploaded exceeds the size limit.',
    reason: 'The system has a maximum file size limit for uploads.',
    solution: details?.maxSize
      ? `Please compress your file or choose a file smaller than ${details.maxSize}.`
      : 'Please compress your file or choose a smaller file (max 10MB).',
    actions: [
      { label: 'Choose Another File', onClick: () => {}, closeOnClick: true },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Validation error
   * Occurs when user input fails validation
   */
  validationError: (details?: { field?: string; message?: string }): ErrorDetails => ({
    title: 'Validation Error',
    description: details?.message || 'Please check your input and try again.',
    reason: details?.field
      ? `The field "${details.field}" contains invalid data or is incomplete.`
      : 'One or more fields contain invalid data or are incomplete.',
    solution: '1. Review the highlighted fields\n2. Correct any errors marked in red\n3. Ensure all required fields are filled\n4. Try again',
    actions: [
      { label: 'Fix Errors', onClick: () => {}, closeOnClick: true },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Not found error
   * Occurs when a requested resource doesn't exist
   */
  notFoundError: (details?: { resource?: string }): ErrorDetails => ({
    title: 'Not Found',
    description: details?.resource
      ? `The requested ${details.resource} could not be found.`
      : 'The requested resource could not be found.',
    reason: 'The resource may have been deleted, moved, or never existed.',
    solution: '1. Check the URL for typos\n2. Go back to the previous page\n3. Use search to find what you are looking for',
    actions: [
      { label: 'Go Back', onClick: () => window.history.back(), closeOnClick: false },
      { label: 'Home', onClick: () => (window.location.href = '/'), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Generic server error
   */
  serverError: (details?: { statusCode?: number }): ErrorDetails => ({
    title: 'Server Error',
    description: 'Something went wrong on our end. Please try again later.',
    reason: details?.statusCode
      ? `The server returned an error code (${details.statusCode}).`
      : 'An unexpected error occurred while processing your request.',
    solution: '1. Wait a moment and try again\n2. Refresh the page\n3. If the problem persists, contact support',
    actions: [
      { label: 'Retry', onClick: () => window.location.reload(), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),

  /**
   * Generic error fallback
   */
  genericError: (details?: { message?: string }): ErrorDetails => ({
    title: 'Error',
    description: details?.message || 'An unexpected error occurred.',
    reason: 'The application encountered an unexpected condition.',
    solution: 'Please try again. If the problem persists, contact support with details about what you were doing.',
    actions: [
      { label: 'Retry', onClick: () => window.location.reload(), closeOnClick: false },
      { label: 'Close', onClick: () => {}, closeOnClick: true },
    ],
  }),
};

/**
 * Helper function to create a simple error message (backward compatible)
 */
export const createSimpleErrorMessage = (
  message: string,
  severity: AlertProps['severity'] = 'error'
): ErrorMessageConfig => ({
  open: true,
  message,
  severity,
  autoHideDuration: 6000,
});

/**
 * Helper function to create a structured error message with actionable steps
 */
export const createStructuredErrorMessage = (
  errorDetails: ErrorDetails,
  severity: AlertProps['severity'] = 'error'
): ErrorMessageConfig => ({
  open: true,
  message: errorDetails,
  severity,
  autoHideDuration: null, // Don't auto-hide structured messages
});

/**
 * Format error details as a readable message string
 * This is used when displaying ErrorDetails in the Alert component
 */
const formatErrorDetails = (details: ErrorDetails): string => {
  let message = `${details.title}\n\n${details.description}`;

  if (details.reason) {
    message += `\n\nWhy: ${details.reason}`;
  }

  if (details.solution) {
    message += `\n\nHow to fix:\n${details.solution}`;
  }

  return message;
};

/**
 * Default error message state
 */
const defaultErrorState: ErrorMessageConfig = {
  open: false,
  message: '',
  severity: 'error',
  autoHideDuration: 6000,
};

/**
 * ErrorMessage Component
 *
 * A reusable component for displaying error and notification messages throughout the application.
 * Replaces browser alert() calls with a more user-friendly Material-UI Snackbar.
 *
 * Features:
 * - Supports multiple severity levels (error, warning, info, success)
 * - Auto-hide with configurable duration
 * - Theme-aware styling (works with light and dark modes)
 * - Smooth slide-in animation
 * - Can be controlled or uncontrolled (internal state management)
 * - Context-based usage for managing errors from child components
 * - Supports internationalization via i18next
 * - Structured error messages with actionable next steps
 * - Pre-built error templates for common failures (network, auth, file upload, etc.)
 * - Action buttons for immediate user response (retry, navigate, etc.)
 *
 * @example
 * ```tsx
 * // Simple usage (backward compatible)
 * const [error, setError] = useState({ open: false, message: '', severity: 'error' });
 *
 * <ErrorMessage
 *   errorState={{
 *     open: error.open,
 *     message: 'Failed to load data',
 *     severity: 'error'
 *   }}
 *   onErrorStateChange={setError}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // Using pre-built error templates with actionable steps
 * const [error, setError] = useState({ open: false, message: '', severity: 'error' });
 *
 * // Network error with retry button
 * setError({
 *   open: true,
 *   message: ErrorTemplates.networkError({ endpoint: '/api/vacancies' }),
 *   severity: 'error'
 * });
 *
 * <ErrorMessage errorState={error} onErrorStateChange={setError} />
 * ```
 *
 * @example
 * ```tsx
 * // Using helper functions
 * const handleError = createErrorHandler(setError);
 *
 * // Show file type error
 * handleError(
 *   ErrorTemplates.fileTypeError({ allowedTypes: ['pdf', 'docx'] })
 * );
 *
 * // Show auth error with login button
 * handleError(ErrorTemplates.authError());
 * ```
 *
 * @example
 * ```tsx
 * // Custom structured error message
 * const [error, setError] = useState({ open: false, message: '', severity: 'error' });
 *
 * setError({
 *   open: true,
 *   message: {
 *     title: 'Upload Failed',
 *     description: 'Could not upload the resume file.',
 *     reason: 'The file size exceeds the 10MB limit.',
 *     solution: 'Compress your file or choose a smaller file.',
 *     actions: [
 *       { label: 'Choose Another File', onClick: () => fileInputRef.current?.click() },
 *       { label: 'Close', onClick: () => setError({ open: false, message: '', severity: 'error' }) }
 *     ]
 *   },
 *   severity: 'error'
 * });
 * ```
 */
const ErrorMessage: React.FC<ErrorMessageProps> = ({
  errorState,
  onErrorStateChange,
  anchorOrigin = { vertical: 'bottom', horizontal: 'right' },
  enableSlideTransition = true,
  children,
}) => {
  const { t } = useTranslation();

  // Internal state for uncontrolled usage
  const [internalErrorState, setInternalErrorState] = useState<ErrorMessageConfig>(defaultErrorState);

  // Use external state if provided, otherwise use internal state
  const currentErrorState = errorState || internalErrorState;

  /**
   * Update error state (internal or external)
   */
  const updateErrorState = useCallback(
    (updates: Partial<ErrorMessageConfig>) => {
      const newState: ErrorMessageConfig = {
        ...currentErrorState,
        ...updates,
      };

      if (onErrorStateChange) {
        onErrorStateChange(newState);
      } else {
        setInternalErrorState(newState);
      }
    },
    [currentErrorState, onErrorStateChange]
  );

  /**
   * Show error message
   *
   * Displays an error or notification message with specified severity.
   * Can be called directly or exposed via context.
   *
   * @param message - The message to display (string or ErrorDetails)
   * @param severity - Severity level (default: 'error')
   * @param autoHideDuration - Duration in ms, null for no auto-hide (default: 6000)
   */
  const showError = useCallback(
    (
      message: string | ErrorDetails,
      severity: AlertProps['severity'] = 'error',
      autoHideDuration: number | null = 6000
    ) => {
      // Don't auto-hide messages with actions
      const shouldAutoHide =
        typeof message === 'string' ||
        (!message.actions || message.actions.length === 0);

      updateErrorState({
        open: true,
        message,
        severity,
        autoHideDuration: shouldAutoHide ? autoHideDuration : null,
      });
    },
    [updateErrorState]
  );

  /**
   * Close the error message
   *
   * Hides the currently displayed message.
   */
  const closeError = useCallback(() => {
    updateErrorState({ open: false });
  }, [updateErrorState]);

  /**
   * Handle Snackbar close event
   *
   * Called when user clicks the close button or after auto-hide duration.
   *
   * @param event - The event that triggered the close
   * @param reason - The reason for closing
   */
  const handleClose = useCallback(
    (_event?: React.SyntheticEvent | Event, reason?: string) => {
      // Don't close if user clicked away (reason: 'clickaway')
      if (reason === 'clickaway') {
        return;
      }
      closeError();
    },
    [closeError]
  );

  /**
   * Reset message when closed
   * Clears the message text after the Snackbar closes
   */
  useEffect(() => {
    if (!currentErrorState.open && currentErrorState.message) {
      const timeoutId = setTimeout(() => {
        updateErrorState({ message: '' });
      }, 500); // Wait for transition to complete

      return () => clearTimeout(timeoutId);
    }
  }, [currentErrorState.open, currentErrorState.message, updateErrorState]);

  /**
   * Expose error display function to window for global access
   * This provides a migration path from alert() to ErrorMessage
   */
  useEffect(() => {
    // Only expose in development or if explicitly enabled
    if (process.env.NODE_ENV === 'development') {
      (window as any).showErrorMessage = showError;
    }
  }, [showError]);

  /**
   * Render alert content
   * Handles both simple string messages and structured ErrorDetails with actions
   */
  const renderAlertContent = () => {
    const message = currentErrorState.message;

    // Handle simple string messages (backward compatible)
    if (typeof message === 'string') {
      return message;
    }

    // Handle structured ErrorDetails
    return (
      <Box>
        <Typography variant="body2" component="div" sx={{ mb: message.actions && message.actions.length > 0 ? 1.5 : 0 }}>
          <Typography component="div" variant="inherit" sx={{ fontWeight: 600, mb: 0.5 }}>
            {message.title}
          </Typography>
          <Typography component="div" variant="inherit" sx={{ mb: 0.5 }}>
            {message.description}
          </Typography>
          {message.reason && (
            <Typography component="div" variant="inherit" sx={{ fontSize: '0.9em', opacity: 0.9, mb: 0.5 }}>
              <strong>Why:</strong> {message.reason}
            </Typography>
          )}
          {message.solution && (
            <Typography component="div" variant="inherit" sx={{ fontSize: '0.9em', opacity: 0.9, whiteSpace: 'pre-line' }}>
              <strong>How to fix:</strong> {message.solution}
            </Typography>
          )}
        </Typography>
        {message.actions && message.actions.length > 0 && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {message.actions.map((action, index) => (
              <Button
                key={index}
                size="small"
                variant="outlined"
                color="inherit"
                onClick={() => {
                  action.onClick();
                  if (action.closeOnClick) {
                    closeError();
                  }
                }}
                sx={{
                  color: 'inherit',
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                  '&:hover': {
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                {action.label}
              </Button>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  // Render children with error context if provided
  if (children) {
    return (
      <>
        {children}
        <Snackbar
          open={currentErrorState.open}
          autoHideDuration={currentErrorState.autoHideDuration ?? undefined}
          onClose={handleClose}
          anchorOrigin={anchorOrigin}
          TransitionComponent={enableSlideTransition ? SlideTransition : undefined}
          sx={{
            '& .MuiAlert-root': {
              borderRadius: 2,
              boxShadow: 3,
            },
          }}
        >
          <Alert
            onClose={handleClose}
            severity={currentErrorState.severity}
            variant="filled"
            sx={{
              width: '100%',
              minWidth: 300,
              maxWidth: 600,
            }}
          >
            {renderAlertContent()}
          </Alert>
        </Snackbar>
      </>
    );
  }

  // Standalone rendering
  return (
    <Snackbar
      open={currentErrorState.open}
      autoHideDuration={currentErrorState.autoHideDuration ?? undefined}
      onClose={handleClose}
      anchorOrigin={anchorOrigin}
      TransitionComponent={enableSlideTransition ? SlideTransition : undefined}
      sx={{
        '& .MuiAlert-root': {
          borderRadius: 2,
          boxShadow: 3,
        },
      }}
    >
      <Alert
        onClose={handleClose}
        severity={currentErrorState.severity}
        variant="filled"
        sx={{
          width: '100%',
          minWidth: 300,
          maxWidth: 600,
        }}
      >
        {renderAlertContent()}
      </Alert>
    </Snackbar>
  );
};

export default ErrorMessage;

/**
 * Helper function to show error messages programmatically
 * Use this to quickly replace alert() calls without significant refactoring
 *
 * @example
 * ```tsx
 * // Before
 * alert('Failed to delete resume');
 *
 * // After - create a state and use ErrorMessage
 * const [error, setError] = useState({ open: false, message: '', severity: 'error' });
 * setError({ open: true, message: 'Failed to delete resume', severity: 'error' });
 * <ErrorMessage errorState={error} onErrorStateChange={setError} />
 * ```
 *
 * @example
 * ```tsx
 * // Using structured error messages with actionable steps
 * const handleError = createErrorHandler(setError);
 *
 * // Show network error with retry option
 * handleError(ErrorTemplates.networkError({ endpoint: '/api/vacancies' }));
 *
 * // Show file type error
 * handleError(ErrorTemplates.fileTypeError({ allowedTypes: ['pdf', 'docx'] }));
 * ```
 */
export const createErrorHandler = (
  setError: React.Dispatch<React.SetStateAction<ErrorMessageConfig>>
) => {
  return (
    message: string | ErrorDetails,
    severity: AlertProps['severity'] = 'error'
  ) => {
    // Don't auto-hide structured messages with actions
    const isStructured = typeof message !== 'string' && message.actions && message.actions.length > 0;

    setError({
      open: true,
      message,
      severity,
      autoHideDuration: isStructured ? null : 6000,
    });
  };
};
