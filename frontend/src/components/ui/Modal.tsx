import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Base Modal props interface
 */
export interface BaseModalProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to modal element */
  modalRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Modal component
 */
export interface ModalProps extends BaseModalProps {
  /** If true, the modal is open */
  open: boolean;
  /** Callback fired when the modal is requested to be closed */
  onClose?: (event: React.MouseEvent | React.KeyboardEvent, reason: string) => void;
  /** If true, clicking the backdrop will not fire the onClose callback */
  disableBackdropClick?: boolean;
  /** If true, hitting escape will not fire the onClose callback */
  disableEscapeKeyDown?: boolean;
  /** Whether to keep the modal mounted in the DOM when closed */
  keepMounted?: boolean;
  /** Z-index of the modal */
  zIndex?: number;
  /** Backdrop visibility */
  backdropVisible?: boolean;
  /** Backdrop color/invisible */
  backdropInvisible?: boolean;
  /** Transition duration in ms */
  transitionDuration?: number;
}

/**
 * Styled backdrop component
 */
const StyledBackdrop = styled.div<{ theme: EmotionTheme; open: boolean; invisible: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: ${({ invisible, theme }) =>
    invisible ? 'transparent' : `rgba(0, 0, 0, ${theme.mode === 'dark' ? 0.7 : 0.5})`};
  z-index: 1040;
  opacity: ${({ open }) => (open ? 1 : 0)};
  transition: opacity ${({ theme, open }) => (open ? theme.transitions.duration.standard : 0)}ms
    ${({ theme }) => theme.transitions.easing.easeOut};
  pointer-events: ${({ open }) => (open ? 'auto' : 'none')};
  -webkit-tap-highlight-color: transparent;
`;

/**
 * Styled Modal container component
 */
const StyledModalContainer = styled.div<{ theme: EmotionTheme; zIndex: number }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: ${({ zIndex }) => zIndex};
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  pointer-events: none;
`;

/**
 * Styled Modal content wrapper
 */
const StyledModalContent = styled.div<{ theme: EmotionTheme; open: boolean }>`
  pointer-events: auto;
  opacity: ${({ open }) => (open ? 1 : 0)};
  transform: ${({ open }) => (open ? 'scale(1)' : 'scale(0.9)')};
  transition: opacity ${({ theme, open }) => (open ? theme.transitions.duration.standard : 0)}ms
    ${({ theme }) => theme.transitions.easing.easeOut},
    transform ${({ theme, open }) => (open ? theme.transitions.duration.standard : 0)}ms
    ${({ theme }) => theme.transitions.easing.easeOut};
`;

/**
 * Modal Component
 *
 * A simple modal component that renders children in an overlay with backdrop.
 * Lower-level component used by Dialog.
 *
 * @example
 * ```tsx
 * const [open, setOpen] = useState(false);
 *
 * <Button onClick={() => setOpen(true)}>Open Modal</Button>
 *
 * <Modal open={open} onClose={() => setOpen(false)}>
 *   <Box sx={{ backgroundColor: 'white', p: 4, borderRadius: 2 }}>
 *     <h2>Modal Content</h2>
 *     <p>This is a simple modal</p>
 *   </Box>
 * </Modal>
 * ```
 */
export const Modal = React.forwardRef<HTMLDivElement, ModalProps>(
  (
    {
      children,
      open = false,
      onClose,
      disableBackdropClick = false,
      disableEscapeKeyDown = false,
      keepMounted = false,
      zIndex = 1050,
      backdropVisible = true,
      backdropInvisible = false,
      transitionDuration,
      className,
      style,
      modalRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const modalRootRef = React.useRef<HTMLDivElement | null>(null);

    // Create modal root element on mount
    useEffect(() => {
      if (typeof document === 'undefined') return;

      const modalRoot = document.createElement('div');
      modalRoot.setAttribute('data-modal-container', 'true');
      document.body.appendChild(modalRoot);
      modalRootRef.current = modalRoot;

      // Prevent body scroll when modal is open
      if (open) {
        document.body.style.overflow = 'hidden';
      }

      return () => {
        if (modalRootRef.current && modalRootRef.current.parentNode) {
          modalRootRef.current.parentNode.removeChild(modalRootRef.current);
        }
        document.body.style.overflow = '';
      };
    }, []);

    // Handle body scroll when modal opens/closes
    useEffect(() => {
      if (open) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }, [open]);

    // Handle escape key to close modal
    const handleEscape = useCallback(
      (event: KeyboardEvent) => {
        if (event.key === 'Escape' && open && !disableEscapeKeyDown && onClose) {
          onClose(event as unknown as React.KeyboardEvent, 'escapeKeyDown');
        }
      },
      [open, disableEscapeKeyDown, onClose]
    );

    useEffect(() => {
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }, [handleEscape]);

    // Handle backdrop click
    const handleBackdropClick = useCallback(
      (event: React.MouseEvent) => {
        if (open && !disableBackdropClick && onClose) {
          // Only close if clicking the backdrop itself, not its children
          if (event.target === event.currentTarget) {
            onClose(event, 'backdropClick');
          }
        }
      },
      [open, disableBackdropClick, onClose]
    );

    // Don't render if not mounted and not keeping mounted
    if (!keepMounted && !open) {
      return null;
    }

    const modalContent = (
      <>
        {backdropVisible && (
          <StyledBackdrop
            theme={theme}
            open={open}
            invisible={backdropInvisible}
            onClick={handleBackdropClick}
            aria-hidden="true"
          />
        )}
        <StyledModalContainer theme={theme} zIndex={zIndex}>
          <StyledModalContent
            ref={ref || modalRef}
            theme={theme}
            open={open}
            className={className}
            style={style}
            role="presentation"
            {...rest}
          >
            {children}
          </StyledModalContent>
        </StyledModalContainer>
      </>
    );

    // Render in portal
    if (modalRootRef.current) {
      return createPortal(modalContent, modalRootRef.current);
    }

    return null;
  }
);

Modal.displayName = 'Modal';

export default Modal;
