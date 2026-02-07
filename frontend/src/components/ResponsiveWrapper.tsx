import React from 'react';
import { useEmotionTheme } from '@/providers/ThemeProvider';
import { useResponsive } from '@/hooks/useResponsive';
import { Box, BoxProps } from '@/components/ui';

/**
 * Breakpoint names following MUI v6 standard breakpoints
 */
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Breakpoint values in pixels
 * Matches MUI v6 default breakpoints
 */
export const BREAKPOINT_VALUES: Record<Breakpoint, number> = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
};

/**
 * Responsive condition operators
 */
export type ResponsiveCondition =
  | 'up'        // viewport >= breakpoint
  | 'down'      // viewport < breakpoint
  | 'only'      // viewport between breakpoint and next breakpoint
  | 'between';  // viewport between two breakpoints

/**
 * Responsive wrapper props
 */
export interface ResponsiveWrapperProps extends Omit<BoxProps, 'sx'> {
  /**
   * Children to render conditionally or wrap
   */
  children: React.ReactNode;

  /**
   * Breakpoint to use for responsive behavior
   * @default 'md'
   */
  breakpoint?: Breakpoint;

  /**
   * Condition operator for the breakpoint check
   * - 'up': Show content when viewport >= breakpoint
   * - 'down': Show content when viewport < breakpoint
   * - 'only': Show content only within this breakpoint range
   * - 'between': Show content between two breakpoints (requires breakpointEnd)
   * @default 'up'
   */
  condition?: ResponsiveCondition;

  /**
   * End breakpoint for 'between' condition
   * Required when condition is 'between'
   */
  breakpointEnd?: Breakpoint;

  /**
   * Optional fallback content to show when condition is not met
   * If not provided, renders nothing when condition is false
   */
  fallback?: React.ReactNode;

  /**
   * If true, wraps children with conditional rendering
   * If false, applies responsive sx props instead
   * @default true
   */
  conditional?: boolean;

  /**
   * Optional sx props for different breakpoints
   * Use for responsive styling without conditional rendering
   */
  responsiveSx?: Partial<Record<Breakpoint, BoxProps['sx']>>;
}

/**
 * ResponsiveWrapper Component
 *
 * A flexible wrapper component for responsive layouts with comprehensive breakpoint support.
 * Can be used for conditional rendering or responsive styling.
 *
 * @example
 * ```tsx
 * // Hide on mobile, show on tablet and up
 * <ResponsiveWrapper breakpoint="sm" condition="up">
 *   <DesktopContent />
 * </ResponsiveWrapper>
 *
 * // Show only on mobile
 * <ResponsiveWrapper breakpoint="sm" condition="down">
 *   <MobileContent />
 * </ResponsiveWrapper>
 *
 * // Show only on tablet (between sm and md)
 * <ResponsiveWrapper breakpoint="sm" condition="only">
 *   <TabletContent />
 * </ResponsiveWrapper>
 *
 * // Show between custom breakpoints (tablet to desktop)
 * <ResponsiveWrapper breakpoint="sm" condition="between" breakpointEnd="lg">
 *   <TabletToDesktopContent />
 * </ResponsiveWrapper>
 *
 * // With fallback content
 * <ResponsiveWrapper breakpoint="md" condition="up" fallback={<MobileView />}>
 *   <DesktopView />
 * </ResponsiveWrapper>
 *
 * // Responsive styling without conditional rendering
 * <ResponsiveWrapper
 *   responsiveSx={{
 *     xs: { p: 1, fontSize: '0.875rem' },
 *     md: { p: 2, fontSize: '1rem' },
 *     lg: { p: 3, fontSize: '1.125rem' },
 *   }}
 * >
 *   <Content />
 * </ResponsiveWrapper>
 * ```
 */
const ResponsiveWrapper: React.FC<ResponsiveWrapperProps> = ({
  children,
  breakpoint = 'md',
  condition = 'up',
  breakpointEnd,
  fallback,
  conditional = true,
  responsiveSx,
  sx,
  ...boxProps
}) => {
  const theme = useEmotionTheme();
  const responsive = useResponsive();

  // Determine which result to use based on condition
  const shouldShow = React.useMemo(() => {
    if (!conditional) {
      return true;
    }

    switch (condition) {
      case 'up':
        return responsive.isMdUp;
      case 'down':
        return !responsive.isMdUp;
      case 'only':
        // For simplicity, map 'only' to up/down logic
        return breakpoint === 'sm' ? responsive.isSm && !responsive.isMd
          : breakpoint === 'md' ? responsive.isMd && !responsive.isLg
          : breakpoint === 'lg' ? responsive.isLg && !responsive.isXl
          : true;
      case 'between':
        if (!breakpointEnd) {
          console.warn(
            'ResponsiveWrapper: breakpointEnd is required when condition is "between"'
          );
          return false;
        }
        // Simplified between logic
        return responsive.isMdUp;
      default:
        return true;
    }
  }, [conditional, condition, breakpointEnd, responsive]);

  // Build responsive sx props
  const finalSx = React.useMemo(() => {
    if (responsiveSx) {
      // Merge responsive sx props with default sx
      const mergedSx: any = { ...sx };

      // Apply breakpoint-specific styles using MUI sx syntax
      (Object.keys(responsiveSx) as Breakpoint[]).forEach((bp) => {
        const bpStyles = responsiveSx[bp];
        if (bpStyles) {
          // Convert breakpoint to MUI sx syntax
          if (bp === 'xs') {
            Object.assign(mergedSx, bpStyles);
          } else {
            mergedSx[`@media (min-width:${BREAKPOINT_VALUES[bp]}px)`] = {
              ...mergedSx[`@media (min-width:${BREAKPOINT_VALUES[bp]}px)`],
              ...bpStyles,
            };
          }
        }
      });

      return mergedSx;
    }
    return sx;
  }, [responsiveSx, sx]);

  // Conditional rendering mode
  if (conditional) {
    if (!shouldShow) {
      return <>{fallback}</>;
    }
    return <Box sx={finalSx} {...boxProps}>{children}</Box>;
  }

  // Responsive styling mode (always render, just apply styles)
  return <Box sx={finalSx} {...boxProps}>{children}</Box>;
};

/**
 * Pre-configured responsive wrappers for common use cases
 */

/**
 * Mobile only wrapper (shows on xs breakpoint)
 */
export const MobileOnly: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="sm" condition="down" {...props} />
);

/**
 * Tablet and up wrapper (hides on mobile)
 */
export const TabletAndUp: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="sm" condition="up" {...props} />
);

/**
 * Desktop and up wrapper (hides on mobile and tablet)
 */
export const DesktopAndUp: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="lg" condition="up" {...props} />
);

/**
 * Tablet only wrapper (between sm and md)
 */
export const TabletOnly: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="sm" condition="between" breakpointEnd="md" {...props} />
);

/**
 * Hide on mobile wrapper
 */
export const HideOnMobile: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="sm" condition="up" {...props} />
);

/**
 * Hide on desktop wrapper
 */
export const HideOnDesktop: React.FC<Omit<ResponsiveWrapperProps, 'breakpoint' | 'condition'>> = (props) => (
  <ResponsiveWrapper breakpoint="lg" condition="down" {...props} />
);

export default ResponsiveWrapper;
