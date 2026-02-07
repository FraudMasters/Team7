import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Elevation levels for Paper component
 * Maps to Material Design elevation system
 */
export type Elevation = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24;

/**
 * Paper component props interface
 */
export interface PaperProps {
  /** Child elements */
  children?: React.ReactNode;
  /** HTML component to render as */
  component?: React.ElementType;
  /** Additional CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Click handler */
  onClick?: React.MouseEventHandler;
  /** Reference to the underlying DOM element */
  ref?: React.Ref<HTMLElement>;
  /**
   * Shadow depth - corresponds to elevation level
   * 0 = flat, 24 = highest elevation
   * Accepts number 0-24 or theme shadow keys (sm, md, lg, xl)
   */
  elevation?: Elevation | 'sm' | 'md' | 'lg' | 'xl';
  /**
   * If true, the paper's background will be transparent
   * Useful for nested papers or overlays
   */
  transparent?: boolean;
  /**
   * If true, rounded corners will be disabled
   */
  square?: boolean;
  /**
   * Custom box-shadow value
   * Overrides elevation if provided
   */
  boxShadow?: string;
  /**
   * Custom border-radius value
   * Overrides theme default if provided
   */
  borderRadius?: string | number;
  /**
   * Background color
   * Overrides theme default if provided
   */
  bgcolor?: string;
  /**
   * System props for additional styling
   */
  sx?: React.CSSProperties;
}

/**
 * Get elevation shadow value
 * Converts elevation number or shadow key to CSS box-shadow value
 */
const getElevationShadow = (
  elevation: PaperProps['elevation'],
  theme: EmotionTheme
): string => {
  // If custom shadow keys are used
  if (elevation === 'sm') return theme.shadows.sm;
  if (elevation === 'md') return theme.shadows.md;
  if (elevation === 'lg') return theme.shadows.lg;
  if (elevation === 'xl') return theme.shadows.xl;
  if (elevation === 'none') return theme.shadows.none;

  // If numeric elevation is provided (Material Design elevation system)
  const num = elevation as number;
  if (typeof num === 'number') {
    // Create elevation shadows similar to MUI's system
    // These approximate Material Design's elevation system
    const elevations: Record<number, string> = {
      0: 'none',
      1: '0 2px 1px -1px rgba(0,0,0,0.2), 0 1px 1px 0 rgba(0,0,0,0.14), 0 1px 3px 0 rgba(0,0,0,0.12)',
      2: '0 3px 1px -2px rgba(0,0,0,0.2), 0 2px 2px 0 rgba(0,0,0,0.14), 0 1px 5px 0 rgba(0,0,0,0.12)',
      3: '0 3px 3px -2px rgba(0,0,0,0.2), 0 3px 4px 0 rgba(0,0,0,0.14), 0 1px 8px 0 rgba(0,0,0,0.12)',
      4: '0 2px 4px -1px rgba(0,0,0,0.2), 0 4px 5px 0 rgba(0,0,0,0.14), 0 1px 10px 0 rgba(0,0,0,0.12)',
      5: '0 3px 5px -1px rgba(0,0,0,0.2), 0 5px 8px 0 rgba(0,0,0,0.14), 0 1px 14px 0 rgba(0,0,0,0.12)',
      6: '0 3px 5px -1px rgba(0,0,0,0.2), 0 6px 10px 0 rgba(0,0,0,0.14), 0 1px 18px 0 rgba(0,0,0,0.12)',
      7: '0 4px 5px -2px rgba(0,0,0,0.2), 0 7px 10px 1px rgba(0,0,0,0.14), 0 2px 16px 1px rgba(0,0,0,0.12)',
      8: '0 5px 5px -3px rgba(0,0,0,0.2), 0 8px 10px 1px rgba(0,0,0,0.14), 0 3px 14px 2px rgba(0,0,0,0.12)',
      9: '0 5px 6px -3px rgba(0,0,0,0.2), 0 9px 12px 1px rgba(0,0,0,0.14), 0 3px 16px 2px rgba(0,0,0,0.12)',
      10: '0 6px 6px -3px rgba(0,0,0,0.2), 0 10px 14px 1px rgba(0,0,0,0.14), 0 4px 18px 3px rgba(0,0,0,0.12)',
      11: '0 6px 7px -4px rgba(0,0,0,0.2), 0 11px 15px 1px rgba(0,0,0,0.14), 0 4px 20px 3px rgba(0,0,0,0.12)',
      12: '0 7px 8px -4px rgba(0,0,0,0.2), 0 12px 17px 2px rgba(0,0,0,0.14), 0 5px 22px 4px rgba(0,0,0,0.12)',
      13: '0 7px 8px -4px rgba(0,0,0,0.2), 0 13px 19px 2px rgba(0,0,0,0.14), 0 5px 24px 4px rgba(0,0,0,0.12)',
      14: '0 7px 9px -4px rgba(0,0,0,0.2), 0 14px 21px 2px rgba(0,0,0,0.14), 0 5px 26px 4px rgba(0,0,0,0.12)',
      15: '0 8px 9px -5px rgba(0,0,0,0.2), 0 15px 22px 2px rgba(0,0,0,0.14), 0 6px 28px 5px rgba(0,0,0,0.12)',
      16: '0 8px 10px -5px rgba(0,0,0,0.2), 0 16px 24px 2px rgba(0,0,0,0.14), 0 6px 30px 5px rgba(0,0,0,0.12)',
      17: '0 8px 11px -5px rgba(0,0,0,0.2), 0 17px 26px 2px rgba(0,0,0,0.14), 0 6px 32px 5px rgba(0,0,0,0.12)',
      18: '0 9px 11px -5px rgba(0,0,0,0.2), 0 18px 28px 2px rgba(0,0,0,0.14), 0 7px 34px 6px rgba(0,0,0,0.12)',
      19: '0 9px 12px -6px rgba(0,0,0,0.2), 0 19px 29px 2px rgba(0,0,0,0.14), 0 7px 36px 6px rgba(0,0,0,0.12)',
      20: '0 10px 13px -6px rgba(0,0,0,0.2), 0 20px 31px 3px rgba(0,0,0,0.14), 0 8px 38px 7px rgba(0,0,0,0.12)',
      21: '0 10px 13px -6px rgba(0,0,0,0.2), 0 21px 33px 3px rgba(0,0,0,0.14), 0 8px 40px 7px rgba(0,0,0,0.12)',
      22: '0 10px 14px -6px rgba(0,0,0,0.2), 0 22px 35px 3px rgba(0,0,0,0.14), 0 8px 42px 7px rgba(0,0,0,0.12)',
      23: '0 11px 14px -7px rgba(0,0,0,0.2), 0 23px 36px 3px rgba(0,0,0,0.14), 0 9px 44px 8px rgba(0,0,0,0.12)',
      24: '0 11px 15px -7px rgba(0,0,0,0.2), 0 24px 38px 3px rgba(0,0,0,0.14), 0 9px 46px 8px rgba(0,0,0,0.12)',
    };
    return elevations[num] || elevations[1];
  }

  // Default to small shadow
  return theme.shadows.sm;
};

/**
 * Styled Paper Component
 */
const StyledPaper = styled('div')<PaperProps>(
  {
    boxSizing: 'border-box',
    transition: 'box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Background color
    if (props.transparent) {
      styles.backgroundColor = 'transparent';
    } else if (props.bgcolor) {
      styles.backgroundColor = props.bgcolor;
    } else {
      styles.backgroundColor = theme.background.paper;
    }

    // Box shadow (elevation)
    if (props.boxShadow !== undefined) {
      styles.boxShadow = props.boxShadow;
    } else {
      const elevation = props.elevation !== undefined ? props.elevation : 1;
      styles.boxShadow = getElevationShadow(elevation, theme);
    }

    // Border radius
    if (props.square) {
      styles.borderRadius = '0';
    } else if (props.borderRadius !== undefined) {
      styles.borderRadius =
        typeof props.borderRadius === 'number'
          ? `${props.borderRadius}px`
          : props.borderRadius;
    } else {
      styles.borderRadius = theme.borderRadius.md;
    }

    // Apply sx prop styles
    if (props.sx) {
      Object.assign(styles, props.sx);
    }

    return styles;
  }
);

/**
 * Paper Component
 *
 * A container component that adds elevation (shadow) to its children.
 * Paper is a foundational component for building cards, modals, and other elevated surfaces.
 *
 * Follows Material Design's elevation system with 25 levels (0-24).
 * Also supports semantic shadow names (sm, md, lg, xl) for convenience.
 *
 * @example
 * ```tsx
 * // Basic usage with default elevation
 * <Paper>
 *   <Typography>Content with elevation</Typography>
 * </Paper>
 *
 * // Custom elevation level
 * <Paper elevation={3}>
 *   <Typography>Higher elevation</Typography>
 * </Paper>
 *
 * // Semantic shadow names
 * <Paper elevation="lg">
 *   <Typography>Large shadow</Typography>
 * </Paper>
 *
 * // Square (no rounded corners)
 * <Paper square elevation={2}>
 *   <Typography>Square paper</Typography>
 * </Paper>
 *
 * // Transparent background
 * <Paper transparent elevation={4}>
 *   <Typography>Transparent with shadow</Typography>
 * </Paper>
 *
 * // Custom styling
 * <Paper
 *   elevation={2}
 *   sx={{
 *     padding: '16px',
 *     backgroundColor: 'primary.main',
 *     color: 'white',
 *   }}
 * >
 *   <Typography>Custom styled paper</Typography>
 * </Paper>
 *
 * // As a different element
 * <Paper component="section" elevation={1}>
 *   <Typography>Semantic section element</Typography>
 * </Paper>
 *
 * // Interactive paper
 * <Paper
 *   elevation={2}
 *   onClick={handleClick}
 *   sx={{ cursor: 'pointer' }}
 * >
 *   <Typography>Clickable paper</Typography>
 * </Paper>
 * ```
 */
const Paper = React.forwardRef<HTMLElement, PaperProps>(
  (
    {
      component,
      children,
      className,
      style,
      onClick,
      elevation = 1,
      transparent = false,
      square = false,
      boxShadow,
      borderRadius,
      bgcolor,
      sx,
      ...rest
    },
    ref
  ) => {
    // Determine which component to render
    const Component = component || 'div';

    return (
      <StyledPaper
        as={Component}
        className={className}
        style={style}
        onClick={onClick}
        ref={ref as any}
        elevation={elevation}
        transparent={transparent}
        square={square}
        boxShadow={boxShadow}
        borderRadius={borderRadius}
        bgcolor={bgcolor}
        sx={sx}
        {...rest}
      >
        {children}
      </StyledPaper>
    );
  }
);

Paper.displayName = 'Paper';

export default Paper;
