/**
 * useBreakpoints Hook
 *
 * Convenient wrapper around useResponsive that provides
 * a simpler API for common breakpoint checks.
 *
 * @module hooks/useBreakpoints
 */

import { useResponsive } from './useResponsive';
import type { Breakpoint } from '../utils/responsive';

export type { Breakpoint };
export { BREAKPOINT_VALUES } from '../utils/responsive';

/**
 * Breakpoints query result
 */
export interface BreakpointsResult {
  /**
   * Viewport is mobile (< sm breakpoint)
   */
  isMobile: boolean;

  /**
   * Viewport is tablet (>= sm, < lg)
   */
  isTablet: boolean;

  /**
   * Viewport is desktop (>= lg)
   */
  isDesktop: boolean;

  /**
   * Current active breakpoint
   */
  currentBreakpoint: Breakpoint;

  /**
   * Current window width in pixels
   */
  width: number;
}

/**
 * useBreakpoints Hook
 *
 * Provides simplified breakpoint information for responsive design.
 * Wraps useResponsive with a cleaner API focused on device categories.
 *
 * @returns BreakpointsResult object with device type flags
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isMobile, isTablet, isDesktop } = useBreakpoints();
 *
 *   return (
 *     <Box>
 *       {isMobile && <MobileView />}
 *       {isTablet && <TabletView />}
 *       {isDesktop && <DesktopView />}
 *     </Box>
 *   );
 * }
 * ```
 */
export function useBreakpoints(): BreakpointsResult {
  const responsive = useResponsive();

  return {
    isMobile: responsive.isXsOnly,
    isTablet: responsive.between('sm', 'lg'),
    isDesktop: responsive.isLgUp,
    currentBreakpoint: responsive.currentBreakpoint,
    width: responsive.width,
  };
}

export default useBreakpoints;
