import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Icon from './primitives/Icon';

/**
 * Alert severity levels
 */
export type AlertSeverity = 'success' | 'info' | 'warning' | 'error';

/**
 * Alert variant types
 */
export type AlertVariant = 'filled' | 'outlined' | 'standard';

/**
 * Alert action button configuration
 */
export interface AlertAction {
  /** Button label */
  label: string;
  /** Click handler */
  onClick: () => void;
  /** Button variant (text or outlined) */
  variant?: 'text' | 'outlined';
}

/**
 * Props for Alert component
 */
export interface AlertProps {
  /** Alert title */
  title?: string;
  /** Alert message */
  message: string;
  /** Severity level */
  severity?: AlertSeverity;
  /** Visual variant */
  variant?: AlertVariant;
  /** Action buttons to display */
  actions?: AlertAction[];
  /** Whether to show the icon */
  showIcon?: boolean;
  /** Whether to allow closing the alert */
  onClose?: () => void;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** ARIA attributes */
  role?: string;
}

/**
 * Get icon name for severity level
 */
const getSeverityIcon = (severity: AlertSeverity): string => {
  switch (severity) {
    case 'success':
      return 'CheckCircle';
    case 'info':
      return 'Info';
    case 'warning':
      return 'AlertTriangle';
    case 'error':
      return 'AlertCircle';
    default:
      return 'Info';
  }
};

/**
 * Get color styles based on severity and theme
 */
const getSeverityStyles = (severity: AlertSeverity, theme: EmotionTheme) => {
  const colorMap = {
    success: theme.success,
    info: theme.info,
    warning: theme.warning,
    error: theme.error,
  };

  return colorMap[severity];
};

/**
 * Styled Alert container
 */
const StyledAlert = styled('div')<{
  severity: AlertSeverity;
  variant: AlertVariant;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const colors = getSeverityStyles(props.severity, theme);
  const styles: Record<string, any> = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: theme.spacing.md,
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius.md,
    position: 'relative',
    overflow: 'hidden',
    transition: theme.transitions.default,
  };

  if (props.variant === 'filled') {
    styles.backgroundColor = colors.main;
    styles.color = colors.contrastText;
  } else if (props.variant === 'outlined') {
    styles.backgroundColor = 'transparent';
    styles.border = `1px solid ${colors.main}`;
    styles.color = colors.main;
  } else {
    // standard
    styles.backgroundColor = colors.light;
    styles.color = colors.dark;
    styles.borderLeft = `4px solid ${colors.main}`;
  }

  return styles;
});

/**
 * Alert icon container
 */
const AlertIcon = styled('div')<{ severity: AlertSeverity; variant: AlertVariant }>(
  (props) => {
    const theme = useEmotionTheme().theme;
    const colors = getSeverityStyles(props.severity, theme);

    return {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      fontSize: '1.5rem',
      color: props.variant === 'filled' ? colors.contrastText : colors.main,
    };
  }
);

/**
 * Alert content container
 */
const AlertContent = styled('div')(() => {
  const theme = useEmotionTheme().theme;
  return {
    flex: '1 1 auto',
    minWidth: 0, // Prevents text overflow issues
  };
});

/**
 * Alert title
 */
const AlertTitle = styled('div')<{ severity: AlertSeverity; variant: AlertVariant }>(
  (props) => {
    const theme = useEmotionTheme().theme;
    const colors = getSeverityStyles(props.severity, theme);

    return {
      fontWeight: 600,
      fontSize: '1rem',
      marginBottom: theme.spacing.xs,
      color: props.variant === 'filled' ? colors.contrastText : colors.dark,
    };
  }
);

/**
 * Alert message
 */
const AlertMessage = styled('div')<{ severity: AlertSeverity; variant: AlertVariant }>(
  (props) => {
    const theme = useEmotionTheme().theme;
    const colors = getSeverityStyles(props.severity, theme);

    return {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      color: props.variant === 'filled' ? colors.contrastText : colors.dark,
    };
  }
);

/**
 * Alert actions container
 */
const AlertActions = styled('div')(() => {
  const theme = useEmotionTheme().theme;
  return {
    display: 'flex',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
    alignItems: 'center',
  };
});

/**
 * Alert action button
 */
const AlertActionButton = styled('button')<{ severity: AlertSeverity }>((props) => {
  const theme = useEmotionTheme().theme;
  const colors = getSeverityStyles(props.severity, theme);

  return {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    fontSize: '0.875rem',
    fontWeight: 500,
    borderRadius: theme.borderRadius.sm,
    border: 'none',
    backgroundColor: colors.main,
    color: colors.contrastText,
    cursor: 'pointer',
    transition: theme.transitions.default,
    '&:hover': {
      backgroundColor: colors.dark,
    },
    '&:focus-visible': {
      outline: `2px solid ${colors.main}`,
      outlineOffset: '2px',
    },
  };
});

/**
 * Alert close button
 */
const AlertCloseButton = styled('button')<{ severity: AlertSeverity; variant: AlertVariant }>(
  (props) => {
    const theme = useEmotionTheme().theme;
    const colors = getSeverityStyles(props.severity, theme);

    return {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '28px',
      height: '28px',
      padding: 0,
      border: 'none',
      borderRadius: '50%',
      backgroundColor: 'transparent',
      color: props.variant === 'filled' ? colors.contrastText : colors.main,
      cursor: 'pointer',
      transition: theme.transitions.default,
      flexShrink: 0,
      '&:hover': {
        backgroundColor: props.variant === 'filled'
          ? 'rgba(255, 255, 255, 0.1)'
          : colors.light,
      },
      '&:focus-visible': {
        outline: `2px solid ${colors.main}`,
        outlineOffset: '2px',
      },
    };
  }
);

/**
 * Alert Component
 *
 * A feedback component for displaying important messages with different severity levels.
 *
 * @example
 * ```tsx
 * // Success alert
 * <Alert
 *   severity="success"
 *   message="Your changes have been saved successfully."
 * />
 *
 * // Error alert with title and action
 * <Alert
 *   severity="error"
 *   title="Upload Failed"
 *   message="The file could not be uploaded. Please try again."
 *   actions={[{ label: 'Retry', onClick: () => retryUpload() }]}
 *   onClose={() => setShowAlert(false)}
 * />
 *
 * // Warning alert (outlined)
 * <Alert
 *   severity="warning"
 *   variant="outlined"
 *   message="Your session will expire in 5 minutes."
 * />
 *
 * // Info alert (filled)
 * <Alert
 *   severity="info"
 *   variant="filled"
 *   title="New Feature"
 *   message="We've added a new feature to help you manage your candidates."
 *   actions={[{ label: 'Learn More', onClick: () => navigate('/help') }]}
 * />
 * ```
 */
const Alert: React.FC<AlertProps> = ({
  title,
  message,
  severity = 'info',
  variant = 'standard',
  actions = [],
  showIcon = true,
  onClose,
  className,
  style,
  role = 'alert',
}) => {
  const iconName = getSeverityIcon(severity);

  return (
    <StyledAlert
      severity={severity}
      variant={variant}
      className={className}
      style={style}
      role={role}
    >
      {showIcon && (
        <AlertIcon severity={severity} variant={variant}>
          <Icon name={iconName} />
        </AlertIcon>
      )}

      <AlertContent>
        {title && <AlertTitle severity={severity} variant={variant}>{title}</AlertTitle>}
        <AlertMessage severity={severity} variant={variant}>{message}</AlertMessage>

        {actions.length > 0 && (
          <AlertActions>
            {actions.map((action, index) => (
              <AlertActionButton
                key={index}
                severity={severity}
                onClick={action.onClick}
                type="button"
              >
                {action.label}
              </AlertActionButton>
            ))}
          </AlertActions>
        )}
      </AlertContent>

      {onClose && (
        <AlertCloseButton
          severity={severity}
          variant={variant}
          onClick={onClose}
          type="button"
          aria-label="Close"
        >
          <Icon name="X" size="small" />
        </AlertCloseButton>
      )}
    </StyledAlert>
  );
};

export { AlertTitle };
export default Alert;
