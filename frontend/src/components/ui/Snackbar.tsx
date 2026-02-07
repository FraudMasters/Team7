import React, { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Icon from './primitives/Icon';
import Alert, { AlertSeverity, AlertAction } from './Alert';

/**
 * Snackbar anchor positions
 */
export type SnackbarOrigin =
  | 'left'
  | 'center'
  | 'right';

/**
 * Snackbar vertical positions
 */
export type SnackbarVertical =
  | 'top'
  | 'bottom';

/**
 * Snackbar props interface
 */
export interface SnackbarProps {
  /** Whether the snackbar is open */
  open: boolean;
  /** Message to display */
  message: string;
  /** Severity level (affects icon and color) */
  severity?: AlertSeverity;
  /** Action button configuration */
  action?: AlertAction;
  /** Duration in milliseconds to auto-close (0 for no auto-close) */
  autoHideDuration?: number;
  /** Callback when snackbar is closed */
  onClose?: () => void;
  /** Horizontal position */
  anchorOrigin?: SnackbarOrigin;
  /** Vertical position */
  verticalOrigin?: SnackbarVertical;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
}

/**
 * Snackbar container (fixed position)
 */
const SnackbarContainer = styled('div')<{
  open: boolean;
  anchorOrigin: SnackbarOrigin;
  verticalOrigin: SnackbarVertical;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const styles: Record<string, any> = {
    position: 'fixed',
    zIndex: theme.zIndex.snackbar,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    pointerEvents: 'none',
    transition: theme.transitions.default,
  };

  // Horizontal positioning
  if (props.anchorOrigin === 'left') {
    styles.left = theme.spacing.lg;
    styles.right = 'auto';
  } else if (props.anchorOrigin === 'right') {
    styles.right = theme.spacing.lg;
    styles.left = 'auto';
  } else {
    // center
    styles.left = '50%';
    styles.right = 'auto';
    styles.transform = 'translateX(-50%)';
  }

  // Vertical positioning
  if (props.verticalOrigin === 'top') {
    styles.top = theme.spacing.lg;
    styles.bottom = 'auto';
  } else {
    // bottom
    styles.bottom = theme.spacing.lg;
    styles.top = 'auto';
  }

  // Animation states
  if (!props.open) {
    styles.opacity = '0';
    styles.pointerEvents = 'none';
  } else {
    styles.opacity = '1';
  }

  return styles;
});

/**
 * Snackbar content wrapper
 */
const SnackbarContent = styled('div')(() => {
  const theme = useEmotionTheme().theme;
  return {
    pointerEvents: 'auto',
    maxWidth: '560px',
    width: '100%',
    backgroundColor: theme.background.paper,
    borderRadius: theme.borderRadius.md,
    boxShadow: theme.shadows.lg,
    overflow: 'hidden',
  };
});

/**
 * Internal alert wrapper for snackbar content
 */
const SnackbarAlert = styled(Alert)<{
  severity: AlertSeverity;
}>((props) => {
  return {
    margin: 0,
    borderRadius: 0,
    border: 'none',
  };
});

/**
 * Snackbar Component
 *
 * A temporary notification popup that displays brief messages about app processes
 * at the bottom or top of the screen.
 *
 * @example
 * ```tsx
 * // Basic usage with state
 * const [open, setOpen] = useState(false);
 *
 * <Snackbar
 *   open={open}
 *   message="File uploaded successfully"
 *   severity="success"
 *   onClose={() => setOpen(false)}
 * />
 *
 * // With action button
 * <Snackbar
 *   open={open}
 *   message="Changes will be lost"
 *   severity="warning"
 *   action={{ label: 'Undo', onClick: () => undoChanges() }}
 *   autoHideDuration={6000}
 *   onClose={() => setOpen(false)}
 * />
 *
 * // Positioned at top right
 * <Snackbar
 *   open={open}
 *   message="New message received"
 *   severity="info"
 *   anchorOrigin="right"
 *   verticalOrigin="top"
 *   onClose={() => setOpen(false)}
 * />
 *
 * // No auto-hide (manual close required)
 * <Snackbar
 *   open={open}
 *   message="Critical error occurred"
 *   severity="error"
 *   action={{ label: 'Dismiss', onClick: () => setOpen(false) }}
 *   autoHideDuration={0}
 * />
 * ```
 */
const Snackbar: React.FC<SnackbarProps> = ({
  open,
  message,
  severity = 'info',
  action,
  autoHideDuration = 5000,
  onClose,
  anchorOrigin = 'center',
  verticalOrigin = 'bottom',
  className,
  style,
}) => {
  const [isVisible, setIsVisible] = useState(open);

  // Handle open state changes
  useEffect(() => {
    if (open) {
      setIsVisible(true);
    } else {
      // Delay hiding for animation
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 300); // Match transition duration
      return () => clearTimeout(timer);
    }
  }, [open]);

  // Auto-hide timer
  useEffect(() => {
    if (open && autoHideDuration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoHideDuration);
      return () => clearTimeout(timer);
    }
  }, [open, autoHideDuration]);

  const handleClose = () => {
    onClose?.();
  };

  // Don't render if not visible (after animation)
  if (!isVisible) {
    return null;
  }

  return (
    <SnackbarContainer
      open={open}
      anchorOrigin={anchorOrigin}
      verticalOrigin={verticalOrigin}
      className={className}
      style={style}
    >
      <SnackbarContent>
        <SnackbarAlert
          severity={severity}
          variant="filled"
          message={message}
          actions={action ? [action] : []}
          onClose={handleClose}
          showIcon
        />
      </SnackbarContent>
    </SnackbarContainer>
  );
};

export default Snackbar;
