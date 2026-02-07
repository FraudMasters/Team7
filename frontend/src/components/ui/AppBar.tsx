import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * AppBar position types
 */
export type AppBarPosition = 'fixed' | 'absolute' | 'static' | 'sticky';

/**
 * AppBar color types
 */
export type AppBarColor = 'primary' | 'secondary' | 'default' | 'inherit' | 'transparent';

/**
 * Base AppBar props interface
 */
export interface BaseAppBarProps {
  /** Child content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  appBarRef?: React.Ref<HTMLHeaderElement>;
}

/**
 * Props for AppBar component
 */
export interface AppBarProps extends BaseAppBarProps, Omit<React.HTMLAttributes<HTMLHeaderElement>, 'color'> {
  /** Position of the AppBar */
  position?: AppBarPosition;
  /** Color of the AppBar */
  color?: AppBarColor;
  /** Elevation shadow depth (0-24) */
  elevation?: number;
  /** If true, the AppBar will be transparent */
  enableColorOnDark?: boolean;
}

/**
 * Get color styles based on color prop
 */
const getColorStyles = (color: AppBarColor, theme: EmotionTheme) => {
  if (color === 'primary') {
    return {
      backgroundColor: theme.primary.main,
      color: theme.primary.contrastText,
    };
  }

  if (color === 'secondary') {
    return {
      backgroundColor: theme.secondary.main,
      color: theme.secondary.contrastText,
    };
  }

  if (color === 'inherit') {
    return {
      backgroundColor: 'inherit',
      color: 'inherit',
    };
  }

  if (color === 'transparent') {
    return {
      backgroundColor: 'transparent',
      color: theme.text.primary,
    };
  }

  // default color
  return {
    backgroundColor: theme.background.paper,
    color: theme.text.primary,
  };
};

/**
 * Get position styles
 */
const getPositionStyles = (position: AppBarPosition) => {
  const positionMap = {
    fixed: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 1100,
    },
    absolute: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 1100,
    },
    sticky: {
      position: 'sticky',
      top: 0,
      zIndex: 1100,
    },
    static: {
      position: 'static',
    },
  };

  return positionMap[position];
};

/**
 * Get elevation shadow
 */
const getElevationShadow = (elevation: number, theme: EmotionTheme): string => {
  if (elevation === 0) return 'none';

  const shadows = [
    'none',
    theme.shadows.sm,
    theme.shadows.md,
    theme.shadows.lg,
    theme.shadows.xl,
  ];

  // Simple elevation to shadow mapping
  if (elevation <= 4) {
    return shadows[Math.min(elevation, shadows.length - 1)];
  }

  // Create custom shadow for higher elevations
  const shadowIntensity = elevation * 0.1;
  return `0 ${elevation}px ${elevation * 2}px rgba(0, 0, 0, ${Math.min(shadowIntensity, 0.5)})`;
};

/**
 * Styled AppBar component
 */
const StyledAppBar = styled.header<AppBarProps & { theme: EmotionTheme; position: AppBarPosition }>`
  /* Reset and base styles */
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  width: 100%;
  font-family: ${({ theme }) => theme.typography.fontFamily};

  /* Position styles */
  ${({ position }) => getPositionStyles(position)}

  /* Color styles */
  ${({ color, theme }) => getColorStyles(color || 'default', theme)}

  /* Elevation shadow */
  ${({ elevation, theme }) => elevation !== undefined ? `box-shadow: ${getElevationShadow(elevation, theme)};` : ''}

  /* Border bottom for default color without elevation */
  ${({ color, elevation, theme }) =>
    color === 'default' && elevation === 0
      ? `border-bottom: 1px solid ${theme.divider};`
      : ''}
`;

/**
 * AppBar Component
 *
 * A navigation bar component that typically contains toolbar elements.
 * Can be positioned at the top of the screen or within a container.
 *
 * @example
 * ```tsx
 * // Basic AppBar
 * <AppBar>
 *   <Toolbar>
 *     <Typography>My App</Typography>
 *   </Toolbar>
 * </AppBar>
 *
 * // Fixed position with primary color
 * <AppBar position="fixed" color="primary" elevation={4}>
 *   <Toolbar>
 *     <Typography color="inherit">Header</Typography>
 *   </Toolbar>
 * </AppBar>
 *
 * // Transparent AppBar
 * <AppBar position="absolute" color="transparent" elevation={0}>
 *   <Toolbar>
 *     <Typography>Transparent Header</Typography>
 *   </Toolbar>
 * </AppBar>
 * ```
 */
export const AppBar = React.forwardRef<HTMLHeaderElement, AppBarProps>(
  (
    {
      children,
      position = 'fixed',
      color = 'primary',
      elevation = 4,
      enableColorOnDark = false,
      className,
      style,
      appBarRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledAppBar
        ref={ref || appBarRef}
        theme={theme}
        position={position}
        color={color}
        elevation={elevation}
        className={className}
        style={style}
        {...rest}
      >
        {children}
      </StyledAppBar>
    );
  }
);

AppBar.displayName = 'AppBar';

export default AppBar;
