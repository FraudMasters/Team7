import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Modal, { ModalProps } from './Modal';
import Paper from './Paper';
import Typography from './primitives/Typography';

/**
 * Dialog max width types
 */
export type DialogMaxWidth = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;

/**
 * Base Dialog props interface
 */
export interface BaseDialogProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to dialog element */
  dialogRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Dialog component
 */
export interface DialogProps extends BaseDialogProps, Omit<ModalProps, 'children'> {
  /** The maximum width of the dialog */
  maxWidth?: DialogMaxWidth;
  /** If true, the dialog will be full screen */
  fullScreen?: boolean;
  /** If true, the dialog will be full width on mobile */
  fullWidth?: boolean;
  /** Dialog title */
  title?: string;
  /** Dialog title ID for accessibility */
  titleId?: string;
  /** Dialog description ID for accessibility */
  descriptionId?: string;
  /** Scroll behavior */
  scroll?: 'body' | 'paper';
  /** Paper props */
  PaperProps?: {
    sx?: React.CSSProperties;
    className?: string;
  };
}

/**
 * Get max width value
 */
const getMaxWidth = (maxWidth: DialogMaxWidth): string => {
  switch (maxWidth) {
    case 'xs':
      return '444px';
    case 'sm':
      return '600px';
    case 'md':
      return '900px';
    case 'lg':
      return '1200px';
    case 'xl':
      return '1536px';
    default:
      return '600px';
  }
};

/**
 * Styled Dialog Paper component
 */
const StyledDialogPaper = styled(Paper)<{
  theme: EmotionTheme;
  maxWidth: DialogMaxWidth;
  fullScreen: boolean;
  fullWidth: boolean;
  scroll: 'body' | 'paper';
}>`
  /* Base styles */
  margin: ${({ theme, fullScreen }) => (fullScreen ? 0 : theme.spacing.xl)};
  max-height: calc(100vh - ${({ theme, fullScreen }) => (fullScreen ? 0 : theme.spacing.xxxl)});

  /* Width */
  width: ${({ fullWidth, fullScreen }) => (fullScreen ? '100%' : fullWidth ? 'calc(100% - 64px)' : 'auto')};
  max-width: ${({ maxWidth, fullScreen }) => (fullScreen ? '100%' : getMaxWidth(maxWidth))};

  /* Display and layout */
  display: flex;
  flex-direction: column;
  border-radius: ${({ fullScreen, theme }) => (fullScreen ? 0 : theme.borderRadius.lg)};

  /* Overflow */
  overflow-y: ${({ scroll }) => (scroll === 'paper' ? 'auto' : 'visible')};

  /* Animation */
  &.dialog-open {
    animation: dialog-slide-in 300ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes dialog-slide-in {
    from {
      opacity: 0;
      transform: translateY(-50px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
`;

/**
 * Styled Dialog Content container
 */
const StyledDialogContent = styled.div<{ theme: EmotionTheme; scroll: 'body' | 'paper' }>`
  /* Overflow */
  overflow-y: ${({ scroll }) => (scroll === 'body' ? 'auto' : 'visible')};

  /* Flex layout */
  display: flex;
  flex-direction: column;
  flex: 1;

  /* Reset margins for direct children */
  > *:first-child {
    margin-top: 0;
  }

  > *:last-child {
    margin-bottom: 0;
  }
`;

/**
 * DialogTitle Component
 *
 * Title component for Dialog.
 *
 * @example
 * ```tsx
 * <DialogTitle id="alert-dialog-title">Use Google's location service?</DialogTitle>
 * ```
 */
export interface DialogTitleProps {
  /** Title text */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to title element */
  titleRef?: React.Ref<HTMLHeadingElement>;
  /** ID for accessibility */
  id?: string;
  /** On close handler */
  onClose?: () => void;
  /** Show close button */
  showCloseButton?: boolean;
}

const StyledDialogTitle = styled.div<{ theme: EmotionTheme }>`
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.lg};
  padding-bottom: ${({ theme }) => theme.spacing.md};

  /* Typography */
  font-size: ${({ theme }) => theme.typography.fontSize['2xl']};
  font-weight: ${({ theme }) => theme.typography.fontWeight.semibold};
  color: ${({ theme }) => theme.text.primary};

  /* Border */
  border-bottom: 1px solid ${({ theme }) => theme.divider};

  /* Zero margins */
  margin: 0;
`;

const CloseButton = styled.button<{ theme: EmotionTheme }>`
  /* Reset */
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: ${({ theme }) => theme.borderRadius.sm};
  color: ${({ theme }) => theme.text.secondary};
  transition: all 150ms ease-in-out;

  /* Hover state */
  &:hover {
    background-color: ${({ theme }) => theme.action.hover};
    color: ${({ theme }) => theme.text.primary};
  }

  /* Focus state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: 2px;
  }
`;

export const DialogTitle = React.forwardRef<HTMLHeadingElement, DialogTitleProps>(
  ({ children, className, style, titleRef, id, onClose, showCloseButton = false }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledDialogTitle
        ref={ref || titleRef}
        theme={theme}
        className={className}
        style={style}
        id={id}
        role="heading"
        aria-level={2}
      >
        <span>{children}</span>
        {showCloseButton && onClose && (
          <CloseButton theme={theme} onClick={onClose} aria-label="Close dialog">
            <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </CloseButton>
        )}
      </StyledDialogTitle>
    );
  }
);

DialogTitle.displayName = 'DialogTitle';

/**
 * DialogContent Component
 *
 * Content container for Dialog.
 *
 * @example
 * ```tsx
 * <DialogContent dividers>
 *   <Typography>Dialog content goes here.</Typography>
 * </DialogContent>
 * ```
 */
export interface DialogContentProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to content element */
  contentRef?: React.Ref<HTMLDivElement>;
  /** ID for accessibility */
  id?: string;
  /** If true, the dialog content will have dividers */
  dividers?: boolean;
}

const StyledDialogContentInner = styled.div<{ theme: EmotionTheme; dividers: boolean }>`
  /* Padding */
  padding: ${({ theme }) => theme.spacing.lg};

  /* Typography base */
  font-size: ${({ theme }) => theme.typography.fontSize.base};
  color: ${({ theme }) => theme.text.primary};

  /* Dividers */
  border-top: ${({ dividers, theme }) => (dividers ? `1px solid ${theme.divider}` : 'none')};
  border-bottom: ${({ dividers, theme }) => (dividers ? `1px solid ${theme.divider}` : 'none')};
  margin-top: ${({ dividers, theme }) => (dividers ? theme.spacing.lg : 0)};
  margin-bottom: ${({ dividers, theme }) => (dividers ? theme.spacing.lg : 0)};
  padding-top: ${({ dividers, theme }) => (dividers ? theme.spacing.lg : 0)};
  padding-bottom: ${({ dividers, theme }) => (dividers ? theme.spacing.lg : 0)};
`;

export const DialogContent = React.forwardRef<HTMLDivElement, DialogContentProps>(
  ({ children, className, style, contentRef, id, dividers = false }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledDialogContentInner
        ref={ref || contentRef}
        theme={theme}
        className={className}
        style={style}
        id={id}
        dividers={dividers}
      >
        {children}
      </StyledDialogContentInner>
    );
  }
);

DialogContent.displayName = 'DialogContent';

/**
 * DialogActions Component
 *
 * Action buttons container for Dialog.
 *
 * @example
 * ```tsx
 * <DialogActions>
 *   <Button onClick={handleCancel}>Cancel</Button>
 *   <Button onClick={handleAgree} variant="contained">Agree</Button>
 * </DialogActions>
 * ```
 */
export interface DialogActionsProps {
  /** Child content (typically buttons) */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to actions element */
  actionsRef?: React.Ref<HTMLDivElement>;
  /** Alignment of actions */
  disableSpacing?: boolean;
}

const StyledDialogActions = styled.div<{ theme: EmotionTheme; disableSpacing: boolean }>`
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: ${({ disableSpacing, theme }) => (disableSpacing ? 0 : theme.spacing.sm)};
  padding: ${({ theme }) => theme.spacing.lg};
  padding-top: ${({ theme }) => theme.spacing.md};

  /* Border */
  border-top: 1px solid ${({ theme }) => theme.divider};

  /* Button margins */
  > * {
    margin-left: ${({ disableSpacing, theme }) => (disableSpacing ? 0 : theme.spacing.xs)};

    &:first-child {
      margin-left: 0;
    }
  }
`;

export const DialogActions = React.forwardRef<HTMLDivElement, DialogActionsProps>(
  ({ children, className, style, actionsRef, disableSpacing = false }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledDialogActions
        ref={ref || actionsRef}
        theme={theme}
        className={className}
        style={style}
        disableSpacing={disableSpacing}
      >
        {children}
      </StyledDialogActions>
    );
  }
);

DialogActions.displayName = 'DialogActions';

/**
 * Dialog Component
 *
 * A modal dialog that can be used for alerts, confirmations, or custom content.
 * Built on top of the Modal component.
 *
 * @example
 * ```tsx
 * const [open, setOpen] = useState(false);
 *
 * <Button onClick={() => setOpen(true)}>Open Dialog</Button>
 *
 * <Dialog
 *   open={open}
 *   onClose={() => setOpen(false)}
 *   title="Dialog Title"
 *   maxWidth="sm"
 *   fullWidth
 * >
 *   <DialogContent>
 *     <Typography>Dialog content goes here.</Typography>
 *   </DialogContent>
 *   <DialogActions>
 *     <Button onClick={() => setOpen(false)}>Cancel</Button>
 *     <Button onClick={handleAgree} variant="contained">Agree</Button>
 *   </DialogActions>
 * </Dialog>
 * ```
 */
export const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
  (
    {
      children,
      open = false,
      onClose,
      maxWidth = 'sm',
      fullScreen = false,
      fullWidth = false,
      title,
      titleId,
      descriptionId,
      scroll = 'paper',
      disableBackdropClick = false,
      disableEscapeKeyDown = false,
      keepMounted = false,
      PaperProps,
      className,
      style,
      dialogRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const [exited, setExited] = React.useState(!open);

    // Handle exit animation
    React.useEffect(() => {
      if (!open) {
        const timer = setTimeout(() => setExited(true), theme.transitions.duration.leavingScreen);
        return () => clearTimeout(timer);
      } else {
        setExited(false);
      }
    }, [open, theme.transitions.duration.leavingScreen]);

    // Don't render if exited and not keeping mounted
    if (!keepMounted && exited && !open) {
      return null;
    }

    return (
      <Modal
        open={open}
        onClose={onClose}
        disableBackdropClick={disableBackdropClick}
        disableEscapeKeyDown={disableEscapeKeyDown}
        keepMounted={keepMounted}
        {...rest}
      >
        <StyledDialogPaper
          ref={ref || dialogRef}
          theme={theme}
          maxWidth={maxWidth}
          fullScreen={fullScreen}
          fullWidth={fullWidth}
          scroll={scroll}
          elevation={24}
          className={`${PaperProps?.className || ''} ${className || ''} ${open ? 'dialog-open' : ''}`}
          style={{ ...PaperProps?.sx, ...style }}
          role="dialog"
          aria-labelledby={titleId}
          aria-describedby={descriptionId}
          aria-modal="true"
        >
          {title && (
            <DialogTitle id={titleId} onClose={onClose} showCloseButton={!disableBackdropClick}>
              {title}
            </DialogTitle>
          )}
          <StyledDialogContent theme={theme} scroll={scroll}>
            {children}
          </StyledDialogContent>
        </StyledDialogPaper>
      </Modal>
    );
  }
);

Dialog.displayName = 'Dialog';

export default Dialog;
