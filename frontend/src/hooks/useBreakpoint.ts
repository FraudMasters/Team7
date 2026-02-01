import { useMemo } from 'react';
import { useTheme, useMediaQuery } from '@mui/material/styles';

/**
 * Breakpoint names for responsive design
 *
 * These align with Material-UI's default breakpoints.
 */
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Breakpoint values return type
 *
 * Provides the current breakpoint and convenience boolean flags.
 */
export interface BreakpointResult {
  /** Current breakpoint name */
  breakpoint: Breakpoint;
  /** Extra small screen (0px - 599px) */
  isXs: boolean;
  /** Small screen (600px - 899px) */
  isSm: boolean;
  /** Medium screen (900px - 1199px) */
  isMd: boolean;
  /** Large screen (1200px - 1535px) */
  isLg: boolean;
  /** Extra large screen (1536px and up) */
  isXl: boolean;
  /** Mobile-only screen (less than 600px) */
  isMobile: boolean;
  /** Tablet-only screen (600px - 899px) */
  isTablet: boolean;
  /** Desktop screen (900px and up) */
  isDesktop: boolean;
}

/**
 * useBreakpoint Hook
 *
 * Provides responsive breakpoint detection using MUI's breakpoint system.
 * Returns the current breakpoint and convenience boolean flags for common screen sizes.
 *
 * This hook uses MUI's useMediaQuery and useTheme hooks, ensuring consistency
 * with MUI's responsive utilities and theme configuration.
 *
 * @returns Breakpoint result with current breakpoint and boolean flags
 *
 * @example
 * ```tsx
 * const { breakpoint, isMobile, isDesktop, isTablet } = useBreakpoint();
 *
 * // Show different content based on screen size
 * {isMobile && <MobileNavigation />}
 * {isDesktop && <DesktopNavigation />}
 *
 * // Conditional styling
 * <Box sx={{
 *   fontSize: isMobile ? '14px' : '16px',
 *   padding: isTablet ? 2 : 4
 * }}>
 *   Responsive content
 * </Box>
 * ```
 */
export const useBreakpoint = (): BreakpointResult => {
  const theme = useTheme();

  // Use MUI's useMediaQuery to detect each breakpoint
  // These queries check if the screen is AT LEAST the breakpoint size
  const isXs = useMediaQuery(theme.breakpoints.up('xs'));
  const isSm = useMediaQuery(theme.breakpoints.up('sm'));
  const isMd = useMediaQuery(theme.breakpoints.up('md'));
  const isLg = useMediaQuery(theme.breakpoints.up('lg'));
  const isXl = useMediaQuery(theme.breakpoints.up('xl'));

  // Determine current breakpoint based on which queries match
  const breakpoint = useMemo<Breakpoint>(() => {
    if (isXl) return 'xl';
    if (isLg) return 'lg';
    if (isMd) return 'md';
    if (isSm) return 'sm';
    return 'xs';
  }, [isXs, isSm, isMd, isLg, isXl]);

  // Convenience flags for common device categories
  const isMobile = useMemo(() => breakpoint === 'xs', [breakpoint]);
  const isTablet = useMemo(() => breakpoint === 'sm', [breakpoint]);
  const isDesktop = useMemo(() => ['md', 'lg', 'xl'].includes(breakpoint), [breakpoint]);

  return {
    breakpoint,
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    isMobile,
    isTablet,
    isDesktop,
  };
};

export default useBreakpoint;
