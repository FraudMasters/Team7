import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Tooltip placement types
 */
export type TooltipPlacement =
  | 'top'
  | 'top-start'
  | 'top-end'
  | 'bottom'
  | 'bottom-start'
  | 'bottom-end'
  | 'left'
  | 'left-start'
  | 'left-end'
  | 'right'
  | 'right-start'
  | 'right-end';

/**
 * Tooltip variant types
 */
export type TooltipVariant = 'default' | 'light' | 'dark';

/**
 * Base Tooltip props interface
 */
export interface BaseTooltipProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to tooltip element */
  tooltipRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Tooltip component
 */
export interface TooltipProps extends BaseTooltipProps {
  /** Tooltip title/text content */
  title: React.ReactNode;
  /** Tooltip placement */
  placement?: TooltipPlacement;
  /** If true, the tooltip is shown */
  open?: boolean;
  /** Control tooltip open state manually */
  disableHoverListener?: boolean;
  /** Disable focus listener */
  disableFocusListener?: boolean;
  /** Disable touch listener */
  disableTouchListener?: boolean;
  /** Delay in ms before showing tooltip */
  enterDelay?: number;
  /** Delay in ms before hiding tooltip */
  leaveDelay?: number;
  /** Disable portal rendering */
  disablePortal?: boolean;
  /** Popper props for positioning */
  PopperProps?: {
    sx?: React.CSSProperties;
  };
  /** Tooltip variant */
  variant?: TooltipVariant;
  /** Arrow visibility */
  arrow?: boolean;
  /** Max width of tooltip */
  maxWidth?: number | string;
  /** Z-index of the tooltip */
  zIndex?: number;
  /** If true, the tooltip will follow the cursor */
  followCursor?: boolean;
}

/**
 * Styled Tooltip container
 */
const StyledTooltipContainer = styled.div<{ theme: EmotionTheme; variant: TooltipVariant }>`
  /* Reset */
  padding: 8px 12px;
  border-radius: ${({ theme }) => theme.borderRadius.sm};
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  line-height: 1.4;
  font-weight: ${({ theme }) => theme.typography.fontWeight.normal};
  white-space: pre-wrap;
  word-break: break-word;

  /* Position */
  position: absolute;
  z-index: 1070;
  pointer-events: none;

  /* Variant styles */
  background-color: ${({ theme, variant }) =>
    variant === 'light'
      ? theme.background.paper
      : variant === 'dark'
        ? '#000000'
        : theme.mode === 'dark'
          ? 'rgba(255, 255, 255, 0.9)'
          : 'rgba(0, 0, 0, 0.75)'};
  color: ${({ theme, variant }) =>
    variant === 'light' || variant === 'dark' ? (variant === 'light' ? theme.text.primary : '#ffffff') : '#ffffff'};

  /* Shadow */
  box-shadow: ${({ theme, variant }) =>
    variant === 'light' ? theme.shadows.md : theme.shadows.lg};

  /* Border for light variant */
  border: ${({ theme, variant }) => (variant === 'light' ? `1px solid ${theme.divider}` : 'none')};

  /* Animation */
  opacity: 0;
  transform: scale(0.9);
  transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1),
    transform 150ms cubic-bezier(0.4, 0, 0.2, 1);

  &.tooltip-visible {
    opacity: 1;
    transform: scale(1);
  }

  /* Arrow */
  &.with-arrow::before {
    content: '';
    position: absolute;
    width: 0;
    height: 0;
    border: 6px solid transparent;
    z-index: -1;
  }

  /* Arrow positions */
  &.placement-top::before {
    bottom: -12px;
    left: calc(50% - 6px);
    border-top-color: ${({ theme, variant }) =>
      variant === 'light'
        ? theme.divider
        : variant === 'dark'
          ? '#000000'
          : theme.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.9)'
            : 'rgba(0, 0, 0, 0.75)'};
  }

  &.placement-bottom::before {
    top: -12px;
    left: calc(50% - 6px);
    border-bottom-color: ${({ theme, variant }) =>
      variant === 'light'
        ? theme.divider
        : variant === 'dark'
          ? '#000000'
          : theme.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.9)'
            : 'rgba(0, 0, 0, 0.75)'};
  }

  &.placement-left::before {
    right: -12px;
    top: calc(50% - 6px);
    border-left-color: ${({ theme, variant }) =>
      variant === 'light'
        ? theme.divider
        : variant === 'dark'
          ? '#000000'
          : theme.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.9)'
            : 'rgba(0, 0, 0, 0.75)'};
  }

  &.placement-right::before {
    left: -12px;
    top: calc(50% - 6px);
    border-right-color: ${({ theme, variant }) =>
      variant === 'light'
        ? theme.divider
        : variant === 'dark'
          ? '#000000'
          : theme.mode === 'dark'
            ? 'rgba(255, 255, 255, 0.9)'
            : 'rgba(0, 0, 0, 0.75)'};
  }
`;

/**
 * Calculate tooltip position based on placement
 */
const calculateTooltipPosition = (
  placement: TooltipPlacement,
  anchorRect: DOMRect,
  tooltipRect: DOMRect,
  margin: number
): { top: number; left: number } => {
  let top = 0;
  let left = 0;

  // Calculate vertical position
  if (placement.startsWith('top')) {
    top = anchorRect.top - tooltipRect.height - margin;
  } else if (placement.startsWith('bottom')) {
    top = anchorRect.bottom + margin;
  } else {
    // left or right
    top = anchorRect.top + (anchorRect.height - tooltipRect.height) / 2;
  }

  // Calculate horizontal position
  if (placement.endsWith('start')) {
    left = anchorRect.left;
  } else if (placement.endsWith('end')) {
    left = anchorRect.right - tooltipRect.width;
  } else if (placement.startsWith('left')) {
    left = anchorRect.left - tooltipRect.width - margin;
  } else if (placement.startsWith('right')) {
    left = anchorRect.right + margin;
  } else {
    // top or bottom center
    left = anchorRect.left + (anchorRect.width - tooltipRect.width) / 2;
  }

  return { top, left };
};

/**
 * Tooltip Component
 *
 * A tooltip that displays informative text when hovering over an element.
 *
 * @example
 * ```tsx
 * <Tooltip title="Delete" placement="top">
 *   <Button>
 *     <DeleteIcon />
 *   </Button>
 * </Tooltip>
 *
 * // With arrow
 * <Tooltip title="Help" arrow>
 *   <IconButton>
 *     <HelpIcon />
 *   </IconButton>
 * </Tooltip>
 *
 * // Light variant
 * <Tooltip title="Light tooltip" variant="light">
 *   <span>Hover me</span>
 * </Tooltip>
 * ```
 */
export const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  (
    {
      children,
      title,
      placement = 'bottom',
      open: controlledOpen,
      disableHoverListener = false,
      disableFocusListener = false,
      disableTouchListener = false,
      enterDelay = 0,
      leaveDelay = 0,
      disablePortal = false,
      PopperProps,
      variant = 'default',
      arrow = false,
      maxWidth = 300,
      zIndex = 1070,
      followCursor = false,
      className,
      style,
      tooltipRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const anchorRef = useRef<HTMLElement>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);
    const tooltipRootRef = useRef<HTMLDivElement | null>(null);
    const [internalOpen, setInternalOpen] = useState(false);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
    const enterTimerRef = useRef<NodeJS.Timeout>();
    const leaveTimerRef = useRef<NodeJS.Timeout>();

    // Combine refs
    React.useImperativeHandle(ref, () => tooltipRef.current!);
    React.useImperativeHandle(tooltipRef, () => tooltipRef.current!);

    // Create tooltip root element on mount
    useEffect(() => {
      if (typeof document === 'undefined' || disablePortal) return;

      const tooltipRoot = document.createElement('div');
      tooltipRoot.setAttribute('data-tooltip-container', 'true');
      tooltipRoot.style.position = 'fixed';
      tooltipRoot.style.top = '0';
      tooltipRoot.style.left = '0';
      tooltipRoot.style.pointerEvents = 'none';
      document.body.appendChild(tooltipRoot);
      tooltipRootRef.current = tooltipRoot;

      return () => {
        if (tooltipRootRef.current && tooltipRootRef.current.parentNode) {
          tooltipRootRef.current.parentNode.removeChild(tooltipRootRef.current);
        }
      };
    }, [disablePortal]);

    // Calculate position when tooltip opens
    useEffect(() => {
      if ((controlledOpen !== undefined ? controlledOpen : internalOpen) && anchorRef.current && tooltipRef.current) {
        const anchorRect = anchorRef.current.getBoundingClientRect();
        const tooltipRect = tooltipRef.current.getBoundingClientRect();

        let pos: { top: number; left: number };

        if (followCursor) {
          pos = { top: cursorPosition.y + 10, left: cursorPosition.x + 10 };
        } else {
          pos = calculateTooltipPosition(placement, anchorRect, tooltipRect, 8);
        }

        setPosition(pos);
      }
    }, [controlledOpen, internalOpen, placement, followCursor, cursorPosition]);

    // Clear timers on unmount
    useEffect(() => {
      return () => {
        if (enterTimerRef.current) clearTimeout(enterTimerRef.current);
        if (leaveTimerRef.current) clearTimeout(leaveTimerRef.current);
      };
    }, []);

    const handleOpen = useCallback(() => {
      if (enterTimerRef.current) clearTimeout(enterTimerRef.current);
      if (leaveTimerRef.current) clearTimeout(leaveTimerRef.current);

      if (enterDelay > 0) {
        enterTimerRef.current = setTimeout(() => {
          setInternalOpen(true);
        }, enterDelay);
      } else {
        setInternalOpen(true);
      }
    }, [enterDelay]);

    const handleClose = useCallback(() => {
      if (enterTimerRef.current) clearTimeout(enterTimerRef.current);
      if (leaveTimerRef.current) clearTimeout(leaveTimerRef.current);

      if (leaveDelay > 0) {
        leaveTimerRef.current = setTimeout(() => {
          setInternalOpen(false);
        }, leaveDelay);
      } else {
        setInternalOpen(false);
      }
    }, [leaveDelay]);

    // Child element handlers
    const handleMouseEnter = (event: React.MouseEvent) => {
      if (!disableHoverListener) {
        if (followCursor) {
          setCursorPosition({ x: event.clientX, y: event.clientY });
        }
        handleOpen();
      }
    };

    const handleMouseLeave = () => {
      if (!disableHoverListener) {
        handleClose();
      }
    };

    const handleFocus = (event: React.FocusEvent) => {
      if (!disableFocusListener) {
        handleOpen();
      }
    };

    const handleBlur = () => {
      if (!disableFocusListener) {
        handleClose();
      }
    };

    const handleTouchStart = (event: React.TouchEvent) => {
      if (!disableTouchListener) {
        handleOpen();
      }
    };

    const handleTouchEnd = () => {
      if (!disableTouchListener) {
        handleClose();
      }
    };

    const handleMouseMove = (event: React.MouseEvent) => {
      if (followCursor && (controlledOpen !== undefined ? controlledOpen : internalOpen)) {
        setCursorPosition({ x: event.clientX, y: event.clientY });
      }
    };

    const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen;

    // Clone child and add event handlers
    const childElement = React.Children.only(children) as React.ReactElement;
    const clonedChild = React.cloneElement(childElement, {
      ref: anchorRef,
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
      onMouseMove: handleMouseMove,
      onFocus: handleFocus,
      onBlur: handleBlur,
      onTouchStart: handleTouchStart,
      onTouchEnd: handleTouchEnd,
      'aria-describedby': isOpen ? 'tooltip-content' : undefined,
    });

    // Don't render tooltip if closed or no title
    if (!isOpen || !title) {
      return clonedChild;
    }

    const tooltipContent = (
      <StyledTooltipContainer
        ref={tooltipRef}
        theme={theme}
        variant={variant}
        className={`${className || ''} tooltip-visible ${arrow ? 'with-arrow' : ''} placement-${placement.split('-')[0]}`}
        style={{
          top: position.top,
          left: position.left,
          maxWidth: typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth,
          zIndex,
          ...style,
          ...PopperProps?.sx,
        }}
        role="tooltip"
        id="tooltip-content"
        {...rest}
      >
        {title}
      </StyledTooltipContainer>
    );

    // Render in portal if not disabled
    if (!disablePortal && tooltipRootRef.current) {
      return (
        <>
          {clonedChild}
          {createPortal(tooltipContent, tooltipRootRef.current)}
        </>
      );
    }

    return (
      <>
        {clonedChild}
        {tooltipContent}
      </>
    );
  }
);

Tooltip.displayName = 'Tooltip';

export default Tooltip;
