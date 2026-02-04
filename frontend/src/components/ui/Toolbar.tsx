import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Toolbar variant types
 */
export type ToolbarVariant = 'regular' | 'dense';

/**
 * Base Toolbar props interface
 */
export interface BaseToolbarProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  toolbarRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Toolbar component
 */
export interface ToolbarProps extends BaseToolbarProps, Omit<React.HTMLAttributes<HTMLDivElement>, 'color'> {
  /** Variant of the toolbar */
  variant?: ToolbarVariant;
  /** Disable gutters (padding) */
  disableGutters?: boolean;
  /** If true, the toolbar has no spacing */
  dense?: boolean;
}

/**
 * Get height based on variant
 */
const getHeightStyles = (variant: ToolbarVariant, dense: boolean) => {
  if (dense) {
    return {
      minHeight: '48px',
      padding: '0 8px',
    };
  }

  if (variant === 'dense') {
    return {
      minHeight: '48px',
      padding: '0 8px',
    };
  }

  // regular variant
  return {
    minHeight: '64px',
    padding: '0 16px',
  };
};

/**
 * Styled Toolbar component
 */
const StyledToolbar = styled.div<ToolbarProps & { theme: EmotionTheme }>`
  /* Reset and base styles */
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  transition: ${({ theme }) =>
    `all ${theme.transitions.duration.standard}ms ${theme.transitions.easing.easeInOut}`};

  /* Height and padding based on variant */
  ${({ variant, dense }) => getHeightStyles(variant || 'regular', dense || false)}

  /* Disable gutters */
  ${({ disableGutters }) =>
    disableGutters
      ? `
    padding-left: 0;
    padding-right: 0;
  `
      : ''}

  /* Responsive padding */
  @media (min-width: ${({ theme }) => theme.breakpoints.sm}) {
    ${({ variant, dense }) => {
      if (dense) {
        return '';
      }
      if (variant === 'dense') {
        return 'padding: 0 16px;';
      }
      return 'padding: 0 24px;';
    }}
  }

  @media (min-width: ${({ theme }) => theme.breakpoints.md}) {
    ${({ variant, dense }) => {
      if (dense) {
        return '';
      }
      if (variant === 'dense') {
        return 'padding: 0 24px;';
      }
      return 'padding: 0 32px;';
    }}
  }
`;

/**
 * Toolbar Component
 *
 * A container for toolbar items, typically used within an AppBar.
 * Provides consistent spacing and alignment for navigation elements.
 *
 * @example
 * ```tsx
 * // Basic toolbar
 * <Toolbar>
 *   <Typography>My App</Typography>
 *   <div style={{ flex: 1 }} />
 *   <Button>Action</Button>
 * </Toolbar>
 *
 * // Dense toolbar
 * <Toolbar variant="dense">
 *   <IconButton>
 *     <Icon name="Menu" />
 *   </IconButton>
 *   <Typography>Dense Toolbar</Typography>
 * </Toolbar>
 *
 * // Without gutters
 * <Toolbar disableGutters>
 *   <Typography>No padding toolbar</Typography>
 * </Toolbar>
 * ```
 */
export const Toolbar = React.forwardRef<HTMLDivElement, ToolbarProps>(
  (
    {
      children,
      variant = 'regular',
      disableGutters = false,
      dense = false,
      className,
      style,
      toolbarRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledToolbar
        ref={ref || toolbarRef}
        theme={theme}
        variant={variant}
        disableGutters={disableGutters}
        dense={dense}
        className={className}
        style={style}
        {...rest}
      >
        {children}
      </StyledToolbar>
    );
  }
);

Toolbar.displayName = 'Toolbar';

export default Toolbar;
