import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../../contexts/EmotionThemeContext';

/**
 * Container component props interface
 */
export interface ContainerProps {
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
  /** If true, the container will disable its gutters (padding) */
  disableGutters?: boolean;
  /**
   * Set the max-width to match the min-width of the current breakpoint.
   * This is useful if you'd prefer to design for a fixed set of sizes
   * instead of trying to accommodate a fully fluid viewport.
   * It's powerful when combined with the `disableGutters` prop.
   */
  fixed?: boolean;
  /**
   * Determine the max-width of the container.
   * The container width grows with the size of the screen.
   * Set the max-width to break fluid width.
   */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false | string;
  /** Inline styles that override system props */
  sx?: React.CSSProperties;
}

/**
 * Get max-width value for breakpoint
 */
const getMaxWidth = (maxWidth: ContainerProps['maxWidth'], theme: EmotionTheme): string => {
  if (maxWidth === false) return '100%';
  if (maxWidth === undefined) return '100%';
  if (typeof maxWidth === 'string' && maxWidth in theme.breakpoints) {
    // Return the breakpoint value minus a small amount for padding
    return theme.breakpoints[maxWidth as keyof typeof theme.breakpoints];
  }
  return maxWidth as string;
};

/**
 * Styled Container Component
 */
const StyledContainer = styled('div')<ContainerProps>(
  {
    width: '100%',
    boxSizing: 'border-box',
    marginLeft: 'auto',
    marginRight: 'auto',
    paddingLeft: '16px',
    paddingRight: '16px',
    display: 'block',
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Disable gutters
    if (props.disableGutters) {
      styles.paddingLeft = 0;
      styles.paddingRight = 0;
    }

    // Max-width
    if (props.maxWidth !== undefined) {
      styles.maxWidth = getMaxWidth(props.maxWidth, theme);
    }

    // Fixed mode - use specific breakpoints
    if (props.fixed) {
      if (!props.maxWidth || props.maxWidth === 'lg') {
        styles['@media (min-width: 1280px)'] = {
          maxWidth: '1280px',
        };
      } else if (props.maxWidth === 'xl') {
        styles['@media (min-width: 1920px)'] = {
          maxWidth: '1920px',
        };
      }
    }

    // Responsive padding based on breakpoints
    if (!props.disableGutters) {
      // Extra small screens (default is already set)
      // Small screens
      styles['@media (min-width: 600px)'] = {
        paddingLeft: '24px',
        paddingRight: '24px',
      };
    }

    return styles;
  }
);

/**
 * Container Component
 *
 * A container component that centers your content horizontally.
 * It's the most basic layout element, designed to limit the width of your content
 * and center it on the page.
 *
 * While containers can be nested, most layout elements do not require a nested container.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <Container>
 *   <Box>Content centered on page</Box>
 * </Container>
 *
 * // Fixed width
 * <Container fixed>
 *   <Box>Fixed width container</Box>
 * </Container>
 *
 * // Max width
 * <Container maxWidth="sm">
 *   <Box>Small container</Box>
 * </Container>
 *
 * // Disable gutters (no horizontal padding)
 * <Container disableGutters>
 *   <Box>Full width content</Box>
 * </Container>
 *
 * // Custom component
 * <Container component="section">
 *   <Box>Semantic section container</Box>
 * </Container>
 * ```
 */
const Container = React.forwardRef<HTMLElement, ContainerProps>(
  (
    {
      component,
      children,
      className,
      style,
      onClick,
      disableGutters = false,
      fixed = false,
      maxWidth,
      sx,
      ...rest
    },
    ref
  ) => {
    // Determine which component to render
    const Component = component || 'div';

    return (
      <StyledContainer
        as={Component}
        className={className}
        style={{ ...sx, ...style }}
        onClick={onClick}
        ref={ref as any}
        disableGutters={disableGutters}
        fixed={fixed}
        maxWidth={maxWidth}
        {...rest}
      >
        {children}
      </StyledContainer>
    );
  }
);

Container.displayName = 'Container';

export default Container;
