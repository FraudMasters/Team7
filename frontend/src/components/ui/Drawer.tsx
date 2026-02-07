import React, { useEffect, useCallback } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Drawer anchor types
 */
export type DrawerAnchor = 'left' | 'top' | 'right' | 'bottom';

/**
 * Drawer variant types
 */
export type DrawerVariant = 'temporary' | 'permanent' | 'persistent';

/**
 * Base Drawer props interface
 */
export interface BaseDrawerProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  drawerRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Drawer component
 */
export interface DrawerProps extends BaseDrawerProps {
  /** Side of the screen from which the drawer will appear */
  anchor?: DrawerAnchor;
  /** Variant of the drawer */
  variant?: DrawerVariant;
  /** If true, the drawer is open */
  open?: boolean;
  /** Callback fired when the drawer is requested to be closed */
  onClose?: (event: React.MouseEvent | React.KeyboardEvent, reason: string) => void;
  /** Width of the drawer (for left/right anchors) */
  width?: number | string;
  /** Elevation shadow depth */
  elevation?: number;
  /** Modal backdrop props */
  ModalProps?: {
    keepMounted?: boolean;
    onBackdropClick?: () => void;
  };
  /** Paper props for the drawer content */
  PaperProps?: {
    sx?: React.CSSProperties;
  };
}

/**
 * Get anchor styles
 */
const getAnchorStyles = (anchor: DrawerAnchor, width: number | string) => {
  const baseStyles = {
    position: 'fixed',
    zIndex: 1200,
    backgroundColor: 'background.paper',
  };

  switch (anchor) {
    case 'left':
      return {
        ...baseStyles,
        top: 0,
        bottom: 0,
        left: 0,
        width: typeof width === 'number' ? `${width}px` : width,
        transform: 'translateX(-100%)',
      };
    case 'right':
      return {
        ...baseStyles,
        top: 0,
        bottom: 0,
        right: 0,
        width: typeof width === 'number' ? `${width}px` : width,
        transform: 'translateX(100%)',
      };
    case 'top':
      return {
        ...baseStyles,
        top: 0,
        left: 0,
        right: 0,
        height: typeof width === 'number' ? `${width}px` : width,
        transform: 'translateY(-100%)',
      };
    case 'bottom':
      return {
        ...baseStyles,
        bottom: 0,
        left: 0,
        right: 0,
        height: typeof width === 'number' ? `${width}px` : width,
        transform: 'translateY(100%)',
      };
    default:
      return baseStyles;
  }
};

/**
 * Get elevation shadow
 */
const getElevationShadow = (elevation: number, theme: EmotionTheme): string => {
  if (elevation === 0) return 'none';
  if (elevation <= 4) {
    return theme.shadows.md;
  }
  if (elevation <= 8) {
    return theme.shadows.lg;
  }
  return theme.shadows.xl;
};

/**
 * Styled Drawer paper component
 */
const StyledDrawerPaper = styled.div<{
  theme: EmotionTheme;
  anchor: DrawerAnchor;
  width: number | string;
  elevation: number;
  open: boolean;
}>`
  /* Reset and base styles */
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  background-color: ${({ theme }) => theme.background.paper};
  color: ${({ theme }) => theme.text.primary};
  transition: transform ${({ theme }) => theme.transitions.duration.complex}ms
    ${({ theme }) => theme.transitions.easing.easeOut};
  overflow-y: auto;
  overflow-x: hidden;

  /* Anchor-specific styles */
  ${({ anchor, width }) => getAnchorStyles(anchor, width)}

  /* Elevation shadow */
  ${({ elevation, theme }) => `box-shadow: ${getElevationShadow(elevation, theme)};`}

  /* Border */
  ${({ anchor, theme }) => {
    if (anchor === 'left' || anchor === 'right') {
      return `border-right: ${anchor === 'left' ? '1' : '0'}px solid ${theme.divider}; border-left: ${anchor === 'right' ? '1' : '0'}px solid ${theme.divider};`;
    }
    return `border-top: ${anchor === 'top' ? '1' : '0'}px solid ${theme.divider}; border-bottom: ${anchor === 'bottom' ? '1' : '0'}px solid ${theme.divider};`;
  }}

  /* Open state */
  ${({ open }) => (open ? 'transform: translate(0, 0);' : '')}
`;

/**
 * Styled backdrop component
 */
const StyledBackdrop = styled.div<{ theme: EmotionTheme; open: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1199;
  opacity: ${({ open }) => (open ? 1 : 0)};
  transition: opacity ${({ theme }) => theme.transitions.duration.standard}ms
    ${({ theme }) => theme.transitions.easing.easeOut};
  pointer-events: ${({ open }) => (open ? 'auto' : 'none')};
`;

/**
 * Drawer Component
 *
 * A navigation drawer that can be temporary or permanent.
 * Slides in from the side of the screen.
 *
 * @example
 * ```tsx
 * // Temporary drawer (opens/closes based on open prop)
 * const [open, setOpen] = useState(false);
 *
 * <Drawer
 *   anchor="left"
 *   open={open}
 *   onClose={() => setOpen(false)}
 *   variant="temporary"
 *   ModalProps={{ keepMounted: true }}
 * >
 *   <List>
 *     <ListItem button>Item 1</ListItem>
 *     <ListItem button>Item 2</ListItem>
 *   </List>
 * </Drawer>
 *
 * // Permanent drawer
 * <Drawer
 *   variant="permanent"
 *   anchor="left"
 *   width={280}
 * >
 *   <Toolbar />
 *   <div style={{ flex: 1 }}>
 *     <List>
 *       <ListItem button>Navigation</ListItem>
 *     </List>
 *   </div>
 * </Drawer>
 * ```
 */
export const Drawer = React.forwardRef<HTMLDivElement, DrawerProps>(
  (
    {
      children,
      anchor = 'left',
      variant = 'temporary',
      open = false,
      onClose,
      width = 280,
      elevation = 16,
      ModalProps,
      PaperProps,
      className,
      style,
      drawerRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Handle escape key to close drawer
    const handleEscape = useCallback(
      (event: KeyboardEvent) => {
        if (event.key === 'Escape' && open && variant === 'temporary' && onClose) {
          onClose(event as unknown as React.KeyboardEvent, 'escapeKeyDown');
        }
      },
      [open, variant, onClose]
    );

    useEffect(() => {
      if (variant === 'temporary') {
        document.addEventListener('keydown', handleEscape);
        return () => {
          document.removeEventListener('keydown', handleEscape);
        };
      }
    }, [handleEscape, variant]);

    // Handle backdrop click
    const handleBackdropClick = useCallback(
      (event: React.MouseEvent) => {
        if (open && variant === 'temporary') {
          if (ModalProps?.onBackdropClick) {
            ModalProps.onBackdropClick();
          }
          if (onClose) {
            onClose(event, 'backdropClick');
          }
        }
      },
      [open, variant, ModalProps, onClose]
    );

    // For permanent drawer, always show
    const shouldShow = variant === 'permanent' || open || (ModalProps?.keepMounted && open);

    // For permanent drawer, don't show backdrop
    const showBackdrop = variant === 'temporary' && open;

    return (
      <>
        {showBackdrop && (
          <StyledBackdrop
            theme={theme}
            open={open}
            onClick={handleBackdropClick}
            aria-hidden="true"
          />
        )}
        <StyledDrawerPaper
          ref={ref || drawerRef}
          theme={theme}
          anchor={anchor}
          width={width}
          elevation={elevation}
          open={variant === 'permanent' ? true : open}
          className={className}
          style={{ ...style, ...PaperProps?.sx }}
          role="complementary"
          aria-hidden={variant === 'temporary' ? (!open ? 'true' : 'false') : 'false'}
          {...rest}
        >
          {children}
        </StyledDrawerPaper>
      </>
    );
  }
);

Drawer.displayName = 'Drawer';

export default Drawer;
