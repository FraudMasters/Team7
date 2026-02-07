import React from 'react';
import {
  Alert,
  Box,
  Button,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Paper,
  Typography,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';

/**
 * Error type enumeration for all supported error categories
 */
export type ErrorType =
  | 'network'      // Network connectivity issues
  | 'auth'         // Authentication/authorization errors
  | 'validation'   // Form validation errors
  | 'fileUpload'   // File upload errors
  | 'server'       // Server-side errors
  | 'notFound'     // Resource not found errors
  // Resume upload workflow errors
  | 'fileSizeExceeded'      // File size exceeds maximum
  | 'invalidFileFormat'     // File format not supported
  | 'resumeParseError'      // Resume parsing failed
  // Vacancy management workflow errors
  | 'vacancyValidation'     // Vacancy form validation errors
  | 'vacancySaveFailed'     // Failed to save vacancy
  // Candidate management workflow errors
  | 'candidateLoadFailed'   // Failed to load candidates
  | 'candidateMoveFailed'   // Failed to move candidate between stages
  | 'batchActionFailed';    // Batch action (move, tag, delete) failed

/**
 * Recovery action button configuration
 */
export interface ErrorAction {
  /**
   * Button label
   */
  label: string;

  /**
   * Click handler for the action
   */
  onClick: () => void;

  /**
   * Button variant
   * @default 'contained'
   */
  variant?: 'contained' | 'outlined' | 'text';

  /**
   * Button color
   * @default 'primary'
   */
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

  /**
   * Whether this is the primary action
   * @default false
   */
  primary?: boolean;
}

/**
 * Props for ErrorMessage component
 */
export interface ErrorMessageProps {
  /**
   * The error object or error type to display
   * Can be an Error instance, error type string, or custom error message
   */
  error: Error | ErrorType | string;

  /**
   * Optional custom title to override the default
   * If not provided, title is derived from error type
   */
  title?: string;

  /**
   * Optional custom message to override the default
   * If not provided, message is derived from error type or error object
   */
  message?: string;

  /**
   * Recovery action buttons to display
   * At least one action is recommended for better UX
   */
  actions?: ErrorAction[];

  /**
   * Error severity level
   * @default 'error'
   */
  severity?: 'error' | 'warning' | 'info';

  /**
   * Display mode
   * - 'inline': Show as an alert/box in the flow
   * - 'modal': Show as a modal dialog
   * - 'fullPage': Show as a full page error
   * @default 'inline'
   */
  mode?: 'inline' | 'modal' | 'fullPage';

  /**
   * Whether to show the error icon
   * @default true
   */
  showIcon?: boolean;

  /**
   * Whether the modal is open (only for modal mode)
   * @default true
   */
  open?: boolean;

  /**
   * Callback when modal is closed (only for modal mode)
   */
  onClose?: () => void;

  /**
   * Optional error details for debugging (collapsed by default)
   */
  details?: string;
}

/**
 * Get default error title for error type
 */
const getDefaultTitle = (errorType: ErrorType): string => {
  switch (errorType) {
    case 'network':
      return 'Network Connection Error';
    case 'auth':
      return 'Authentication Error';
    case 'validation':
      return 'Validation Error';
    case 'fileUpload':
      return 'File Upload Error';
    case 'server':
      return 'Server Error';
    case 'notFound':
      return 'Resource Not Found';
    case 'fileSizeExceeded':
      return 'File Size Exceeded';
    case 'invalidFileFormat':
      return 'Invalid File Format';
    case 'resumeParseError':
      return 'Resume Parse Error';
    case 'vacancyValidation':
      return 'Vacancy Validation Error';
    case 'vacancySaveFailed':
      return 'Failed to Save Vacancy';
    case 'candidateLoadFailed':
      return 'Failed to Load Candidates';
    case 'candidateMoveFailed':
      return 'Failed to Move Candidate';
    case 'batchActionFailed':
      return 'Batch Action Failed';
    default:
      return 'Error';
  }
};

/**
 * Get default error message for error type
 */
const getDefaultMessage = (errorType: ErrorType): string => {
  switch (errorType) {
    case 'network':
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    case 'auth':
      return 'You are not authorized to perform this action. Please log in and try again.';
    case 'validation':
      return 'Please correct the errors in the form and try again.';
    case 'fileUpload':
      return 'The file could not be uploaded. Please check the file format and size.';
    case 'server':
      return 'Something went wrong on our end. Our team has been notified and we are working to fix it.';
    case 'notFound':
      return 'The requested resource could not be found. It may have been moved or deleted.';
    case 'fileSizeExceeded':
      return 'The file is too large. Please compress it or choose a smaller file.';
    case 'invalidFileFormat':
      return 'The file format is not supported. Please upload a PDF, DOC, or DOCX file.';
    case 'resumeParseError':
      return 'Could not parse the resume. Please ensure it contains readable text and try again.';
    case 'vacancyValidation':
      return 'Please fill in all required fields and fix any validation errors.';
    case 'vacancySaveFailed':
      return 'Failed to save the vacancy. Please check your connection and try again.';
    case 'candidateLoadFailed':
      return 'Failed to load candidates. Please refresh the page to try again.';
    case 'candidateMoveFailed':
      return 'Failed to move the candidate to the new stage. Please try again.';
    case 'batchActionFailed':
      return 'Failed to complete the batch action. Some changes may not have been applied.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
};

/**
 * Get icon for error type
 */
const getErrorIcon = (errorType: ErrorType): string => {
  switch (errorType) {
    case 'network':
      return 'wifi-off';
    case 'auth':
      return 'lock';
    case 'validation':
      return 'alert-circle';
    case 'fileUpload':
      return 'upload';
    case 'server':
      return 'cloud-off';
    case 'notFound':
      return 'search';
    case 'fileSizeExceeded':
      return 'hard-drive';
    case 'invalidFileFormat':
      return 'file';
    case 'resumeParseError':
      return 'file-text';
    case 'vacancyValidation':
      return 'alert-triangle';
    case 'vacancySaveFailed':
      return 'database';
    case 'candidateLoadFailed':
      return 'users';
    case 'candidateMoveFailed':
      return 'user-check';
    case 'batchActionFailed':
      return 'list-x';
    default:
      return 'alert-circle';
  }
};

/**
 * Detect error type from Error object or message
 */
const detectErrorType = (error: Error | string): ErrorType => {
  const message = typeof error === 'string' ? error : error.message;

  // Network errors
  if (
    message.toLowerCase().includes('network') ||
    message.toLowerCase().includes('connection') ||
    message.toLowerCase().includes('fetch') ||
    message.includes('ERR_NETWORK') ||
    message.includes('ERR_INTERNET_DISCONNECTED')
  ) {
    return 'network';
  }

  // Auth errors
  if (
    message.toLowerCase().includes('unauthorized') ||
    message.toLowerCase().includes('authentication') ||
    message.toLowerCase().includes('login') ||
    message.toLowerCase().includes('token') ||
    message.includes('401') ||
    message.includes('403')
  ) {
    return 'auth';
  }

  // File size errors (specific check before validation)
  if (
    message.toLowerCase().includes('size') &&
    (message.toLowerCase().includes('too large') ||
     message.toLowerCase().includes('exceeded') ||
     message.toLowerCase().includes('maximum') ||
     message.toLowerCase().includes('limit'))
  ) {
    return 'fileSizeExceeded';
  }

  // Invalid file format errors
  if (
    message.toLowerCase().includes('format') ||
    message.toLowerCase().includes('unsupported') ||
    message.toLowerCase().includes('extension')
  ) {
    return 'invalidFileFormat';
  }

  // Resume parse errors
  if (
    message.toLowerCase().includes('parse') ||
    message.toLowerCase().includes('could not read') ||
    message.toLowerCase().includes('unable to extract')
  ) {
    return 'resumeParseError';
  }

  // Vacancy validation errors
  if (
    message.toLowerCase().includes('vacancy') &&
    message.toLowerCase().includes('validation')
  ) {
    return 'vacancyValidation';
  }

  // Vacancy save errors
  if (
    message.toLowerCase().includes('vacancy') &&
    (message.toLowerCase().includes('save') || message.toLowerCase().includes('create') || message.toLowerCase().includes('update'))
  ) {
    return 'vacancySaveFailed';
  }

  // Candidate load errors
  if (
    message.toLowerCase().includes('candidate') &&
    message.toLowerCase().includes('load')
  ) {
    return 'candidateLoadFailed';
  }

  // Candidate move errors
  if (
    message.toLowerCase().includes('candidate') &&
    message.toLowerCase().includes('move')
  ) {
    return 'candidateMoveFailed';
  }

  // Batch action errors
  if (
    message.toLowerCase().includes('batch') ||
    message.toLowerCase().includes('bulk')
  ) {
    return 'batchActionFailed';
  }

  // Validation errors (general)
  if (
    message.toLowerCase().includes('validation') ||
    message.toLowerCase().includes('required') ||
    message.toLowerCase().includes('invalid') ||
    message.includes('422') ||
    message.includes('400')
  ) {
    return 'validation';
  }

  // File upload errors (general)
  if (
    message.toLowerCase().includes('upload') ||
    message.toLowerCase().includes('file')
  ) {
    return 'fileUpload';
  }

  // Not found errors
  if (
    message.toLowerCase().includes('not found') ||
    message.toLowerCase().includes('does not exist') ||
    message.includes('404')
  ) {
    return 'notFound';
  }

  // Server errors
  if (
    message.toLowerCase().includes('server') ||
    message.toLowerCase().includes('internal') ||
    message.includes('500') ||
    message.includes('502') ||
    message.includes('503')
  ) {
    return 'server';
  }

  // Default to server error for unknown errors
  return 'server';
};

/**
 * ErrorMessage Component
 *
 * A comprehensive error message component with specific templates for all error types
 * including network, auth, validation, file upload, server, and not found errors.
 * Supports inline, modal, and full-page display modes with recovery actions.
 *
 * @example
 * ```tsx
 * // Network error with retry action
 * <ErrorMessage
 *   error={new Error('Network request failed')}
 *   actions={[{ label: 'Retry', onClick: () => retry() }]}
 * />
 *
 * // Validation error with multiple actions
 * <ErrorMessage
 *   error="validation"
 *   title="Please fix the errors"
 *   message="There are 3 validation errors in the form."
 *   actions={[
 *     { label: 'View Errors', onClick: () => scrollToErrors() },
 *     { label: 'Reset Form', onClick: () => reset(), variant: 'outlined' },
 *   ]}
 * />
 *
 * // File upload error
 * <ErrorMessage
 *   error="fileUpload"
 *   message="resume.pdf is too large. Maximum size is 10MB."
 *   actions={[{ label: 'Remove File', onClick: () => removeFile() }]}
 * />
 *
 * // Modal error dialog
 * <ErrorMessage
 *   error={error}
 *   mode="modal"
 *   actions={[
 *     { label: 'Try Again', onClick: () => retry() },
 *     { label: 'Go Back', onClick: () => goBack(), variant: 'outlined' },
 *   ]}
 * />
 *
 * // Full page error
 * <ErrorMessage
 *   error="notFound"
 *   mode="fullPage"
 *   actions={[{ label: 'Go Home', onClick: () => navigate('/') }]}
 * />
 * ```
 */
const ErrorMessage: React.FC<ErrorMessageProps> = ({
  error,
  title,
  message,
  actions = [],
  severity = 'error',
  mode = 'inline',
  showIcon = true,
  open = true,
  onClose,
  details,
}) => {
  const theme = useEmotionTheme();

  // Detect error type
  const errorType: ErrorType = React.useMemo(() => {
    const validErrorTypes: ErrorType[] = [
      'network', 'auth', 'validation', 'fileUpload', 'server', 'notFound',
      'fileSizeExceeded', 'invalidFileFormat', 'resumeParseError',
      'vacancyValidation', 'vacancySaveFailed',
      'candidateLoadFailed', 'candidateMoveFailed', 'batchActionFailed'
    ];
    if (typeof error === 'string' && validErrorTypes.includes(error as ErrorType)) {
      return error as ErrorType;
    }
    return detectErrorType(error);
  }, [error]);

  // Get default title and message
  const defaultTitle = getDefaultTitle(errorType);
  const defaultMessage = getDefaultMessage(errorType);

  // Use custom or default values
  const displayTitle = title || defaultTitle;
  const displayMessage = message || (typeof error === 'string' ? error : error.message) || defaultMessage;

  // Get error icon name
  const iconName = getErrorIcon(errorType);

  // Inline mode
  if (mode === 'inline') {
    return (
      <Alert
        severity={severity}
        showIcon={showIcon}
        icon={showIcon ? <Icon name={iconName} size={24} /> : undefined}
        sx={{
          mb: 2,
          '& .alert-icon': {
            fontSize: '2rem',
          },
        }}
        action={
          actions.length > 0 ? (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {actions.map((action, index) => (
                <Button
                  key={index}
                  size="small"
                  variant={action.variant || (action.primary ? 'contained' : 'outlined')}
                  color={action.color || 'primary'}
                  onClick={action.onClick}
                >
                  {action.label}
                </Button>
              ))}
            </Box>
          ) : undefined
        }
      >
        <Typography variant="subtitle2" component="div" sx={{ fontWeight: 'bold' }}>
          {displayTitle}
        </Typography>
        <Typography variant="body2">{displayMessage}</Typography>
        {details && (
          <Box
            sx={{
              mt: 1,
              p: 1,
              bgcolor: 'rgba(0, 0, 0, 0.05)',
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              overflow: 'auto',
              maxHeight: 100,
            }}
          >
            {details}
          </Box>
        )}
      </Alert>
    );
  }

  // Modal mode
  if (mode === 'modal') {
    return (
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="sm"
        fullWidth
        aria-labelledby="error-dialog-title"
        aria-describedby="error-dialog-description"
      >
        {onClose && (
          <IconButton
            aria-label="close"
            onClick={onClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: 'grey.500',
            }}
          >
            <Icon name="x" size={20} />
          </IconButton>
        )}
        <DialogTitle id="error-dialog-title" sx={{ pr: onClose ? 5 : 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {showIcon && <Icon name={iconName} size={24} color="error.main" />}
            <Typography variant="h6" as="span">
              {displayTitle}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="error-dialog-description" color="primary">
            {displayMessage}
          </DialogContentText>
          {details && (
            <Box
              sx={{
                mt: 2,
                p: 1.5,
                bgcolor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                overflow: 'auto',
                maxHeight: 150,
              }}
            >
              {details}
            </Box>
          )}
        </DialogContent>
        {actions.length > 0 && (
          <DialogActions sx={{ p: 2, pt: 0 }}>
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || (action.primary ? 'contained' : 'outlined')}
                color={action.color || 'primary'}
                onClick={action.onClick}
                autoFocus={action.primary}
              >
                {action.label}
              </Button>
            ))}
          </DialogActions>
        )}
      </Dialog>
    );
  }

  // Full page mode
  if (mode === 'fullPage') {
    return (
      <Paper
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          p: 4,
          textAlign: 'center',
          bgcolor: 'background.paper',
        }}
      >
        {showIcon && (
          <Box
            sx={{
              fontSize: '4rem',
              color: 'error.main',
              mb: 2,
            }}
          >
            <Icon name={iconName} size={64} color="error.main" />
          </Box>
        )}
        <Typography variant="h4" gutterBottom color="primary">
          {displayTitle}
        </Typography>
        <Typography
          variant="body1"
          color="secondary"
          sx={{ maxWidth: 600, mb: 3 }}
        >
          {displayMessage}
        </Typography>
        {details && (
          <Box
            sx={{
              mb: 3,
              p: 2,
              bgcolor: 'rgba(0, 0, 0, 0.05)',
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              overflow: 'auto',
              maxWidth: 600,
              maxHeight: 150,
            }}
          >
            {details}
          </Box>
        )}
        {actions.length > 0 && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || (action.primary ? 'contained' : 'outlined')}
                color={action.color || 'primary'}
                size="large"
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            ))}
          </Box>
        )}
      </Paper>
    );
  }

  return null;
};

/**
 * Pre-configured error message components for common error types
 */

/**
 * Network error message component
 */
export const NetworkError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="network"
    title="Network Connection Error"
    message="Unable to connect to the server. Please check your internet connection and try again."
    {...props}
  />
);

/**
 * Authentication error message component
 */
export const AuthError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="auth"
    title="Authentication Error"
    message="You are not authorized to perform this action. Please log in and try again."
    {...props}
  />
);

/**
 * Validation error message component
 */
export const ValidationError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="validation"
    title="Validation Error"
    message="Please correct the errors in the form and try again."
    {...props}
  />
);

/**
 * File upload error message component
 */
export const FileTypeError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="fileUpload"
    title="File Upload Error"
    message="The file could not be uploaded. Please check the file format and size."
    {...props}
  />
);

/**
 * Server error message component
 */
export const ServerError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="server"
    title="Server Error"
    message="Something went wrong on our end. Our team has been notified and we are working to fix it."
    {...props}
  />
);

/**
 * Not found error message component
 */
export const NotFoundError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="notFound"
    title="Resource Not Found"
    message="The requested resource could not be found. It may have been moved or deleted."
    {...props}
  />
);

/**
 * Workflow-specific error message components for Resume Upload
 */

/**
 * File size exceeded error for resume upload
 */
export const FileSizeExceededError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="fileSizeExceeded"
    title="File Size Exceeded"
    message="The file is too large. Please compress it or choose a smaller file."
    {...props}
  />
);

/**
 * Invalid file format error for resume upload
 */
export const InvalidFileFormatError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="invalidFileFormat"
    title="Invalid File Format"
    message="The file format is not supported. Please upload a PDF, DOC, or DOCX file."
    {...props}
  />
);

/**
 * Resume parse error
 */
export const ResumeParseError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="resumeParseError"
    title="Resume Parse Error"
    message="Could not parse the resume. Please ensure it contains readable text and try again."
    {...props}
  />
);

/**
 * Workflow-specific error message components for Vacancy Management
 */

/**
 * Vacancy validation error
 */
export const VacancyValidationError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="vacancyValidation"
    title="Vacancy Validation Error"
    message="Please fill in all required fields and fix any validation errors."
    {...props}
  />
);

/**
 * Vacancy save failed error
 */
export const VacancySaveFailedError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="vacancySaveFailed"
    title="Failed to Save Vacancy"
    message="Failed to save the vacancy. Please check your connection and try again."
    {...props}
  />
);

/**
 * Workflow-specific error message components for Candidate Management
 */

/**
 * Candidate load failed error
 */
export const CandidateLoadFailedError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="candidateLoadFailed"
    title="Failed to Load Candidates"
    message="Failed to load candidates. Please refresh the page to try again."
    {...props}
  />
);

/**
 * Candidate move failed error
 */
export const CandidateMoveFailedError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="candidateMoveFailed"
    title="Failed to Move Candidate"
    message="Failed to move the candidate to the new stage. Please try again."
    {...props}
  />
);

/**
 * Batch action failed error
 */
export const BatchActionFailedError: React.FC<Omit<ErrorMessageProps, 'error' | 'title' | 'message'>> = (props) => (
  <ErrorMessage
    error="batchActionFailed"
    title="Batch Action Failed"
    message="Failed to complete the batch action. Some changes may not have been applied."
    {...props}
  />
);

export default ErrorMessage;
