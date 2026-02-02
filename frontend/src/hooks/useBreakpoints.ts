/**
 * useBreakpoints Hook
 *
 * A custom hook for convenient access to MUI breakpoint queries.
 * Provides a simplified interface for responsive design with commonly
 * used breakpoint checks.
 *
 * @module hooks/useBreakpoints
 */

import { useTheme, useMediaQuery } from '@mui/material';
import { useMemo } from 'react';

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
 * Breakpoint query result
 *
 * Provides boolean flags for each breakpoint direction
 * and utility methods for common responsive checks.
 */
export interface BreakpointsResult {
  /**
   * Viewport width is >= sm (600px)
   */
  isSmUp: boolean;

  /**
   * Viewport width is >= md (900px)
   */
  isMdUp: boolean;

  /**
   * Viewport width is >= lg (1200px)
   */
  isLgUp: boolean;

  /**
   * Viewport width is >= xl (1536px)
   */
  isXlUp: boolean;

  /**
   * Viewport width is < sm (600px) - mobile
   */
  isXsOnly: boolean;

  /**
   * Viewport width is < md (900px) - mobile and tablet
   */
  isSmOnly: boolean;

  /**
   * Viewport width is < lg (1200px)
   */
  isMdOnly: boolean;

  /**
   * Current active breakpoint
   */
  currentBreakpoint: Breakpoint;

  /**
   * Check if viewport is >= specific breakpoint
   *
   * @param breakpoint - Breakpoint to check
   * @returns true if viewport width >= breakpoint
   *
   * @example
   * ```ts
   * const breakpoints = useBreakpoints();
   * if (breakpoints.up('lg')) {
   *   // Render desktop layout
   * }
   * ```
   */
  up: (breakpoint: Breakpoint) => boolean;

  /**
   * Check if viewport is < specific breakpoint
   *
   * @param breakpoint - Breakpoint to check
   * @returns true if viewport width < breakpoint
   *
   * @example
   * ```ts
   * const breakpoints = useBreakpoints();
   * if (breakpoints.down('md')) {
   *   // Render mobile/tablet layout
   * }
   * ```
   */
  down: (breakpoint: Breakpoint) => boolean;

  /**
   * Check if viewport is between two breakpoints
   *
   * @param start - Start breakpoint (inclusive)
   * @param end - End breakpoint (exclusive)
   * @returns true if viewport is in range
   *
   * @example
   * ```ts
   * const breakpoints = useBreakpoints();
   * if (breakpoints.between('sm', 'lg')) {
   *   // Render tablet-only layout
   * }
   * ```
   */
  between: (start: Breakpoint, end: Breakpoint) => boolean;

  /**
   * Check if viewport matches only one breakpoint
   *
   * @param breakpoint - Breakpoint to check
   * @returns true if viewport is in breakpoint range
   *
   * @example
   * ```ts
   * const breakpoints = useBreakpoints();
   * if (breakpoints.only('md')) {
   *   // Render md-only layout (900px - 1199px)
   * }
   * ```
   */
  only: (breakpoint: Breakpoint) => boolean;
}

/**
 * Get the current breakpoint based on window width
 *
 * @param width - Current window width in pixels
 * @returns Current breakpoint name
 *
 * @private
 */
function getCurrentBreakpoint(width: number): Breakpoint {
  if (width < BREAKPOINT_VALUES.sm) return 'xs';
  if (width < BREAKPOINT_VALUES.md) return 'sm';
  if (width < BREAKPOINT_VALUES.lg) return 'md';
  if (width < BREAKPOINT_VALUES.xl) return 'lg';
  return 'xl';
}

/**
 * useBreakpoints Hook
 *
 * Provides convenient access to MUI breakpoint queries for responsive design.
 * Returns boolean flags for common breakpoints and utility methods for
 * custom breakpoint checks.
 *
 * @returns BreakpointsResult object with breakpoint information
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const breakpoints = useBreakpoints();
 *
 *   return (
 *     <Box>
 *       {breakpoints.isXsOnly && <MobileView />}
 *       {breakpoints.isMdUp && <DesktopView />}
 *
 *       <Typography>
 *         Current breakpoint: {breakpoints.currentBreakpoint}
 *       </Typography>
 *     </Box>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function ResponsiveGrid() {
 *   const breakpoints = useBreakpoints();
 *
 *   const columns = useMemo(() => {
 *     if (breakpoints.up('xl')) return 4;
 *     if (breakpoints.up('lg')) return 3;
 *     if (breakpoints.up('md')) return 2;
 *     return 1;
 *   }, [breakpoints]);
 *
 *   return <Grid container columns={columns}>...</Grid>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function TabletOnlyComponent() {
 *   const breakpoints = useBreakpoints();
 *
 *   // Only render on tablet (sm to md)
 *   if (!breakpoints.between('sm', 'lg')) {
 *     return null;
 *   }
 *
 *   return <TabletLayout />;
 * }
 * ```
 */
export function useBreakpoints(): BreakpointsResult {
  const theme = useTheme();

  // Call all media query hooks at top level (React Hooks rules)
  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));

  const isSmUp = useMediaQuery(theme.breakpoints.up('sm'));
  const isMdUp = useMediaQuery(theme.breakpoints.up('md'));
  const isLgUp = useMediaQuery(theme.breakpoints.up('lg'));
  const isXlUp = useMediaQuery(theme.breakpoints.up('xl'));

  const isSmDown = useMediaQuery(theme.breakpoints.down('sm'));
  const isMdDown = useMediaQuery(theme.breakpoints.down('md'));
  const isLgDown = useMediaQuery(theme.breakpoints.down('lg'));

  // Determine current breakpoint
  const currentBreakpoint = useMemo((): Breakpoint => {
    if (isXl) return 'xl';
    if (isLg) return 'lg';
    if (isMd) return 'md';
    if (isSm) return 'sm';
    return 'xs';
  }, [isXs, isSm, isMd, isLg, isXl]);

  // Create the result object with memoized methods
  const result = useMemo<BreakpointsResult>(() => {
    const up = (breakpoint: Breakpoint): boolean => {
      switch (breakpoint) {
        case 'xs':
          return true; // Always true since xs starts at 0
        case 'sm':
          return isSmUp;
        case 'md':
          return isMdUp;
        case 'lg':
          return isLgUp;
        case 'xl':
          return isXlUp;
        default:
          return false;
      }
    };

    const down = (breakpoint: Breakpoint): boolean => {
      switch (breakpoint) {
        case 'xs':
          return false; // Nothing is below xs
        case 'sm':
          return isSmDown;
        case 'md':
          return isMdDown;
        case 'lg':
          return isLgDown;
        case 'xl':
          return true; // Everything is below xl max
        default:
          return false;
      }
    };

    const only = (breakpoint: Breakpoint): boolean => {
      switch (breakpoint) {
        case 'xs':
          return isXs;
        case 'sm':
          return isSm;
        case 'md':
          return isMd;
        case 'lg':
          return isLg;
        case 'xl':
          return isXl;
        default:
          return false;
      }
    };

    const between = (start: Breakpoint, end: Breakpoint): boolean => {
      // Convert breakpoint names to indices for comparison
      const breakpointOrder: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
      const startIndex = breakpointOrder.indexOf(start);
      const endIndex = breakpointOrder.indexOf(end);

      if (startIndex === -1 || endIndex === -1 || startIndex >= endIndex) {
        console.warn(
          `useBreakpoints: Invalid between(${start}, ${end}) - start must be before end`
        );
        return false;
      }

      // Check if current breakpoint is in range
      const currentIndex = breakpointOrder.indexOf(currentBreakpoint);
      return currentIndex >= startIndex && currentIndex < endIndex;
    };

    return {
      isSmUp,
      isMdUp,
      isLgUp,
      isXlUp,
      isXsOnly: isXs,
      isSmOnly: isSmDown,
      isMdOnly: isLgDown,
      currentBreakpoint,
      up,
      down,
      between,
      only,
    };
  }, [
    isSmUp,
    isMdUp,
    isLgUp,
    isXlUp,
    isXs,
    isSmDown,
    isMdDown,
    isLgDown,
    currentBreakpoint,
  ]);

  return result;
}

export default useBreakpoints;
