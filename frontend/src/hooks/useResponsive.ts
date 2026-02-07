/**
 * useResponsive Hook
 *
 * A custom hook for responsive breakpoint queries without MUI dependencies.
 * Provides a simplified interface for responsive design using native
 * window.matchMedia API. Follows the same API pattern as useBreakpoints
 * for easy migration.
 *
 * @module hooks/useResponsive
 */

import { useEffect, useState, useMemo, useCallback } from 'react';
import type {
  Breakpoint,
  BREAKPOINT_VALUES,
} from '../utils/responsive';

/**
 * Re-export types from utils for convenience
 */
export type { Breakpoint };
export { BREAKPOINT_VALUES };

/**
 * Responsive query result
 *
 * Provides boolean flags for each breakpoint direction
 * and utility methods for common responsive checks.
 */
export interface ResponsiveResult {
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
   * Current window width in pixels
   */
  width: number;

  /**
   * Check if viewport is >= specific breakpoint
   *
   * @param breakpoint - Breakpoint to check
   * @returns true if viewport width >= breakpoint
   *
   * @example
   * ```ts
   * const responsive = useResponsive();
   * if (responsive.up('lg')) {
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
   * const responsive = useResponsive();
   * if (responsive.down('md')) {
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
   * const responsive = useResponsive();
   * if (responsive.between('sm', 'lg')) {
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
   * const responsive = useResponsive();
   * if (responsive.only('md')) {
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
 * useResponsive Hook
 *
 * Provides convenient access to responsive breakpoint queries for
 * responsive design without MUI dependencies. Returns boolean flags
 * for common breakpoints and utility methods for custom breakpoint checks.
 *
 * Uses native window.matchMedia API for efficient breakpoint detection
 * with automatic cleanup on unmount.
 *
 * @returns ResponsiveResult object with breakpoint information
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const responsive = useResponsive();
 *
 *   return (
 *     <Box>
 *       {responsive.isXsOnly && <MobileView />}
 *       {responsive.isMdUp && <DesktopView />}
 *
 *       <Typography>
 *         Current breakpoint: {responsive.currentBreakpoint}
 *       </Typography>
 *     </Box>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function ResponsiveGrid() {
 *   const responsive = useResponsive();
 *
 *   const columns = useMemo(() => {
 *     if (responsive.up('xl')) return 4;
 *     if (responsive.up('lg')) return 3;
 *     if (responsive.up('md')) return 2;
 *     return 1;
 *   }, [responsive]);
 *
 *   return <Grid container columns={columns}>...</Grid>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function TabletOnlyComponent() {
 *   const responsive = useResponsive();
 *
 *   // Only render on tablet (sm to md)
 *   if (!responsive.between('sm', 'lg')) {
 *     return null;
 *   }
 *
 *   return <TabletLayout />;
 * }
 * ```
 */
export function useResponsive(): ResponsiveResult {
  // State to track window width
  const [width, setWidth] = useState<number>(() => {
    if (typeof window === 'undefined') return BREAKPOINT_VALUES.md;
    return window.innerWidth;
  });

  // Update width on resize
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Determine current breakpoint
  const currentBreakpoint = useMemo((): Breakpoint => {
    return getCurrentBreakpoint(width);
  }, [width]);

  // Calculate boolean flags
  const isSmUp = useMemo(() => width >= BREAKPOINT_VALUES.sm, [width]);
  const isMdUp = useMemo(() => width >= BREAKPOINT_VALUES.md, [width]);
  const isLgUp = useMemo(() => width >= BREAKPOINT_VALUES.lg, [width]);
  const isXlUp = useMemo(() => width >= BREAKPOINT_VALUES.xl, [width]);

  const isXsOnly = useMemo(() => width < BREAKPOINT_VALUES.sm, [width]);
  const isSmOnly = useMemo(() => width < BREAKPOINT_VALUES.md, [width]);
  const isMdOnly = useMemo(() => width < BREAKPOINT_VALUES.lg, [width]);

  // Utility methods
  const up = useCallback(
    (breakpoint: Breakpoint): boolean => {
      return width >= BREAKPOINT_VALUES[breakpoint];
    },
    [width]
  );

  const down = useCallback(
    (breakpoint: Breakpoint): boolean => {
      if (breakpoint === 'xs') return false;
      return width < BREAKPOINT_VALUES[breakpoint];
    },
    [width]
  );

  const only = useCallback(
    (breakpoint: Breakpoint): boolean => {
      const breakpointOrder: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
      const index = breakpointOrder.indexOf(breakpoint);
      if (index === -1) return false;

      const startValue = BREAKPOINT_VALUES[breakpoint];
      const endValue =
        index < breakpointOrder.length - 1
          ? BREAKPOINT_VALUES[breakpointOrder[index + 1]]
          : Infinity;

      return width >= startValue && width < endValue;
    },
    [width]
  );

  const between = useCallback(
    (start: Breakpoint, end: Breakpoint): boolean => {
      const breakpointOrder: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
      const startIndex = breakpointOrder.indexOf(start);
      const endIndex = breakpointOrder.indexOf(end);

      if (startIndex === -1 || endIndex === -1 || startIndex >= endIndex) {
        console.warn(
          `useResponsive: Invalid between(${start}, ${end}) - start must be before end`
        );
        return false;
      }

      return (
        width >= BREAKPOINT_VALUES[start] && width < BREAKPOINT_VALUES[end]
      );
    },
    [width]
  );

  // Create the result object
  const result = useMemo<ResponsiveResult>(
    () => ({
      isSmUp,
      isMdUp,
      isLgUp,
      isXlUp,
      isXsOnly,
      isSmOnly,
      isMdOnly,
      currentBreakpoint,
      width,
      up,
      down,
      between,
      only,
    }),
    [
      isSmUp,
      isMdUp,
      isLgUp,
      isXlUp,
      isXsOnly,
      isSmOnly,
      isMdOnly,
      currentBreakpoint,
      width,
      up,
      down,
      between,
      only,
    ]
  );

  return result;
}

export default useResponsive;
