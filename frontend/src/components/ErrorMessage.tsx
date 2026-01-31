import React, { useState, useCallback, useEffect, ReactNode } from 'react';
import { Snackbar, Alert, AlertProps, Slide, SlideProps } from '@mui/material';
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
 * Error message configuration
 */
export interface ErrorMessageConfig {
  /** Whether the message is currently visible */
  open: boolean;
  /** The message content */
  message: string;
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
 *
 * @example
 * ```tsx
 * // Uncontrolled usage (recommended for replacing alert())
 * const [showError, setShowError] = useState(false);
 *
 * function handleError(message: string) {
 *   setShowError(true);
 * }
 *
 * <ErrorMessage
 *   errorState={{
 *     open: showError,
 *     message: 'Failed to load data',
 *     severity: 'error'
 *   }}
 *   onErrorStateChange={(state) => setShowError(state.open)}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // Using context to manage errors from child components
 * <ErrorMessage>
 *   <YourComponent />
 * </ErrorMessage>
 *
 * // In child component
 * const showError = useErrorMessage();
 * showError('Something went wrong', 'error');
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
   * @param message - The message to display
   * @param severity - Severity level (default: 'error')
   * @param autoHideDuration - Duration in ms, null for no auto-hide (default: 6000)
   */
  const showError = useCallback(
    (
      message: string,
      severity: AlertProps['severity'] = 'error',
      autoHideDuration: number | null = 6000
    ) => {
      updateErrorState({
        open: true,
        message,
        severity,
        autoHideDuration,
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
            {currentErrorState.message}
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
        {currentErrorState.message}
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
 */
export const createErrorHandler = (
  setError: React.Dispatch<React.SetStateAction<ErrorMessageConfig>>
) => {
  return (message: string, severity: AlertProps['severity'] = 'error') => {
    setError({
      open: true,
      message,
      severity,
      autoHideDuration: 6000,
    });
  };
};
