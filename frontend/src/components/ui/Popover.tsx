import React, { useEffect, useRef, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Paper from './Paper';

/**
 * Popover position types
 */
export type PopoverVerticalPosition = 'top' | 'center' | 'bottom';
export type PopoverHorizontalPosition = 'left' | 'center' | 'right';

/**
 * Popover origin interface
 */
export interface PopoverOrigin {
  vertical: PopoverVerticalPosition;
  horizontal: PopoverHorizontalPosition;
}

/**
 * Base Popover props interface
 */
export interface BasePopoverProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to popover element */
  popoverRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Popover component
 */
export interface PopoverProps extends BasePopoverProps {
  /** If true, the popover is visible */
  open: boolean;
  /** Callback fired when the popover is requested to be closed */
  onClose?: (event: React.MouseEvent | React.KeyboardEvent, reason?: string) => void;
  /** Anchor element for positioning */
  anchorEl?: HTMLElement | null;
  /** Position of the popover relative to anchor */
  anchorOrigin?: PopoverOrigin;
  /** Position of the popover content itself */
  transformOrigin?: PopoverOrigin;
  /** Elevation shadow depth */
  elevation?: number;
  /** Disable portal rendering */
  disablePortal?: boolean;
  /** Margin between anchor and popover */
  marginThreshold?: number;
  /** Popover container to render in */
  container?: HTMLElement | (() => HTMLElement) | null;
  /** Z-index of the popover */
  zIndex?: number;
  /** If true, the popover will not restore focus to the anchor on close */
  disableRestoreFocus?: boolean;
  /** If true, the popover will not auto-position itself */
  disableAutoFocus?: boolean;
  /** Transition duration in ms */
  transitionDuration?: number;
  /** Maximum width of the popover */
  maxWidth?: number | string;
  /** Minimum width of the popover */
  minWidth?: number | string;
  /** Height of the popover */
  height?: number | string;
  /** Maximum height of the popover */
  maxHeight?: number | string;
}

/**
 * Styled Popover Paper component
 */
const StyledPopoverPaper = styled(Paper)<{
  theme: EmotionTheme;
  elevation: number;
  maxWidth: number | string;
  minWidth: number | string;
  height: number | string | undefined;
  maxHeight: number | string | undefined;
}>`
  /* Position */
  position: absolute;
  z-index: 1060;

  /* Sizing */
  max-width: ${({ maxWidth }) => (typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth)};
  min-width: ${({ minWidth }) => (typeof minWidth === 'number' ? `${minWidth}px` : minWidth)};
  height: ${({ height }) => (typeof height === 'number' ? `${height}px` : height)};
  max-height: ${({ maxHeight }) => (typeof maxHeight === 'number' ? `${maxHeight}px` : maxHeight)};
  overflow-y: auto;
  overflow-x: hidden;

  /* Base styles */
  box-sizing: border-box;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  background-color: ${({ theme }) => theme.background.paper};
  color: ${({ theme }) => theme.text.primary};
  border-radius: ${({ theme }) => theme.borderRadius.md};

  /* Animation */
  opacity: 0;
  transform: scale(0.95);
  transition: opacity ${({ transitionDuration }) => transitionDuration || 150}ms
    cubic-bezier(0.4, 0, 0.2, 1),
    transform ${({ transitionDuration }) => transitionDuration || 150}ms cubic-bezier(0.4, 0, 0.2, 1);

  &.popover-open {
    opacity: 1;
    transform: scale(1);
  }
`;

/**
 * Styled Popover container
 */
const StyledPopoverContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1060;
  overflow: hidden;
`;

/**
 * Calculate popover position based on anchor and origins
 */
const calculatePopoverPosition = (
  anchorEl: HTMLElement,
  anchorOrigin: PopoverOrigin,
  transformOrigin: PopoverOrigin,
  marginThreshold: number
): { top: number; left: number; transformOrigin: string } => {
  const anchorRect = anchorEl.getBoundingClientRect();
  const popoverRect = { width: 0, height: 0 }; // Will be updated after render

  // Calculate vertical position
  let top: number;
  switch (anchorOrigin.vertical) {
    case 'top':
      top = anchorRect.top;
      break;
    case 'center':
      top = anchorRect.top + anchorRect.height / 2;
      break;
    case 'bottom':
      top = anchorRect.bottom;
      break;
  }

  // Calculate horizontal position
  let left: number;
  switch (anchorOrigin.horizontal) {
    case 'left':
      left = anchorRect.left;
      break;
    case 'center':
      left = anchorRect.left + anchorRect.width / 2;
      break;
    case 'right':
      left = anchorRect.right;
      break;
  }

  // Add margin
  if (anchorOrigin.vertical === 'bottom') {
    top += marginThreshold;
  } else if (anchorOrigin.vertical === 'top') {
    top -= marginThreshold;
  }

  if (anchorOrigin.horizontal === 'right') {
    left += marginThreshold;
  } else if (anchorOrigin.horizontal === 'left') {
    left -= marginThreshold;
  }

  // Calculate transform origin string
  const transformOriginValue = `${transformOrigin.vertical} ${transformOrigin.horizontal}`;

  return { top, left, transformOrigin: transformOriginValue };
};

/**
 * Popover Component
 *
 * A popover that displays content positioned relative to an anchor element.
 *
 * @example
 * ```tsx
 * const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
 *
 * const handleClick = (event: React.MouseEvent<HTMLElement>) => {
 *   setAnchorEl(event.currentTarget);
 * };
 *
 * const handleClose = () => {
 *   setAnchorEl(null);
 * };
 *
 * <Button onClick={handleClick}>Open Popover</Button>
 *
 * <Popover
 *   open={Boolean(anchorEl)}
 *   anchorEl={anchorEl}
 *   onClose={handleClose}
 *   anchorOrigin={{
 *     vertical: 'bottom',
 *     horizontal: 'left',
 *   }}
 * >
 *   <Box sx={{ p: 2 }}>
 *     <Typography>Popover content</Typography>
 *   </Box>
 * </Popover>
 * ```
 */
export const Popover = React.forwardRef<HTMLDivElement, PopoverProps>(
  (
    {
      children,
      open = false,
      onClose,
      anchorEl,
      anchorOrigin = { vertical: 'bottom', horizontal: 'left' },
      transformOrigin = { vertical: 'top', horizontal: 'left' },
      elevation = 8,
      disablePortal = false,
      marginThreshold = 16,
      container,
      zIndex = 1060,
      disableRestoreFocus = false,
      disableAutoFocus = false,
      transitionDuration,
      maxWidth = 'calc(100vw - 32px)',
      minWidth = 16,
      height,
      maxHeight = 'calc(100vh - 32px)',
      className,
      style,
      popoverRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const popoverRootRef = useRef<HTMLDivElement | null>(null);
    const internalRef = useRef<HTMLDivElement>(null);
    const anchorElRef = useRef<HTMLElement | null>(null);
    const previousFocusRef = useRef<HTMLElement | null>(null);
    const [position, setPosition] = useState({ top: 0, left: 0, transformOrigin: 'top left' });

    // Combine refs
    React.useImperativeHandle(ref, () => internalRef.current!);
    React.useImperativeHandle(popoverRef, () => internalRef.current!);

    // Create popover root element on mount
    useEffect(() => {
      if (typeof document === 'undefined' || disablePortal) return;

      const popoverRoot = document.createElement('div');
      popoverRoot.setAttribute('data-popover-container', 'true');
      document.body.appendChild(popoverRoot);
      popoverRootRef.current = popoverRoot;

      return () => {
        if (popoverRootRef.current && popoverRootRef.current.parentNode) {
          popoverRootRef.current.parentNode.removeChild(popoverRootRef.current);
        }
      };
    }, [disablePortal]);

    // Store anchor element ref
    useEffect(() => {
      if (anchorEl) {
        anchorElRef.current = anchorEl;
      }
    }, [anchorEl]);

    // Calculate position when open and anchor is available
    useEffect(() => {
      if (open && anchorEl && internalRef.current) {
        const updatePosition = () => {
          if (!anchorEl) return;

          const newPos = calculatePopoverPosition(
            anchorEl,
            anchorOrigin,
            transformOrigin,
            marginThreshold
          );
          setPosition(newPos);
        };

        updatePosition();

        // Recalculate on scroll/resize
        window.addEventListener('scroll', updatePosition, true);
        window.addEventListener('resize', updatePosition);

        return () => {
          window.removeEventListener('scroll', updatePosition, true);
          window.removeEventListener('resize', updatePosition);
        };
      }
    }, [open, anchorEl, anchorOrigin, transformOrigin, marginThreshold]);

    // Handle focus restoration
    useEffect(() => {
      if (open && !disableAutoFocus && internalRef.current) {
        // Store the currently focused element
        previousFocusRef.current = document.activeElement as HTMLElement;

        // Focus the popover
        internalRef.current.focus();

        return () => {
          if (!disableRestoreFocus && previousFocusRef.current) {
            previousFocusRef.current.focus();
          }
        };
      }
    }, [open, disableAutoFocus, disableRestoreFocus]);

    // Handle escape key to close popover
    const handleEscape = useCallback(
      (event: KeyboardEvent) => {
        if (event.key === 'Escape' && open && onClose) {
          onClose(event as unknown as React.KeyboardEvent, 'escapeKeyDown');
        }
      },
      [open, onClose]
    );

    useEffect(() => {
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }, [handleEscape]);

    // Handle click outside
    const handleClickOutside = useCallback(
      (event: MouseEvent) => {
        if (
          open &&
          internalRef.current &&
          !internalRef.current.contains(event.target as Node) &&
          anchorElRef.current &&
          !anchorElRef.current.contains(event.target as Node) &&
          onClose
        ) {
          onClose(event as unknown as React.MouseEvent, 'backdropClick');
        }
      },
      [open, onClose]
    );

    useEffect(() => {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }, [handleClickOutside]);

    // Don't render if closed
    if (!open) {
      return null;
    }

    const popoverContent = (
      <StyledPopoverContainer>
        <StyledPopoverPaper
          ref={internalRef}
          theme={theme}
          elevation={elevation}
          maxWidth={maxWidth}
          minWidth={minWidth}
          height={height}
          maxHeight={maxHeight}
          className={`${className || ''} ${open ? 'popover-open' : ''}`}
          style={{
            top: position.top,
            left: position.left,
            transformOrigin: position.transformOrigin,
            ...style,
          }}
          tabIndex={-1}
          role="presentation"
          {...rest}
        >
          {children}
        </StyledPopoverPaper>
      </StyledPopoverContainer>
    );

    // Determine container
    let popoverContainer: HTMLElement | null = null;
    if (container) {
      popoverContainer = typeof container === 'function' ? container() : container;
    } else if (popoverRootRef.current) {
      popoverContainer = popoverRootRef.current;
    }

    // Render in portal if not disabled
    if (!disablePortal && popoverContainer) {
      return createPortal(popoverContent, popoverContainer);
    }

    return popoverContent;
  }
);

Popover.displayName = 'Popover';

export default Popover;
