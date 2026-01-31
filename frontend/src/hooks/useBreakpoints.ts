import { useState, useEffect, useCallback, useMemo } from 'react';

/**
 * Breakpoint names for responsive design
 *
 * These align with Material-UI's default breakpoints for consistency.
 */
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Breakpoint configuration
 *
 * Defines the minimum width for each breakpoint.
 * The value represents the minimum viewport width in pixels.
 */
export interface BreakpointConfig {
  /** Breakpoint name */
  name: Breakpoint;
  /** Display name */
  displayName: string;
  /** Minimum width in pixels */
  minWidth: number;
  /** Typical device */
  device: string;
}

/**
 * Supported breakpoints configuration
 *
 * Aligned with Material-UI's default breakpoints:
 * - xs: 0px (extra small - mobile phones)
 * - sm: 600px (small - tablets, large phones)
 * - md: 900px (medium - landscape tablets, small desktops)
 * - lg: 1200px (large - desktops)
 * - xl: 1536px (extra large - large desktops)
 */
export const BREAKPOINTS: Record<Breakpoint, BreakpointConfig> = {
  xs: {
    name: 'xs',
    displayName: 'Extra Small',
    minWidth: 0,
    device: 'Mobile phones',
  },
  sm: {
    name: 'sm',
    displayName: 'Small',
    minWidth: 600,
    device: 'Tablets, large phones',
  },
  md: {
    name: 'md',
    displayName: 'Medium',
    minWidth: 900,
    device: 'Landscape tablets, small desktops',
  },
  lg: {
    name: 'lg',
    displayName: 'Large',
    minWidth: 1200,
    device: 'Desktops',
  },
  xl: {
    name: 'xl',
    displayName: 'Extra Large',
    minWidth: 1536,
    device: 'Large desktops',
  },
} as const;

/**
 * Breakpoint values return type
 *
 * Provides boolean flags for each breakpoint and utility functions.
 */
export interface BreakpointValues {
  /** Current breakpoint name */
  currentBreakpoint: Breakpoint;
  /** Viewport width in pixels */
  width: number;
  /** Viewport height in pixels */
  height: number;
  /** Extra small screen (0px and up) */
  isXs: boolean;
  /** Small screen (600px and up) */
  isSm: boolean;
  /** Medium screen (900px and up) */
  isMd: boolean;
  /** Large screen (1200px and up) */
  isLg: boolean;
  /** Extra large screen (1536px and up) */
  isXl: boolean;
  /** Mobile-only screen (less than 600px) */
  isMobile: boolean;
  /** Tablet-only screen (600px to 899px) */
  isTablet: boolean;
  /** Desktop screen (900px and up) */
  isDesktop: boolean;
  /** Check if current viewport is at least the given breakpoint */
  isUp: (breakpoint: Breakpoint) => boolean;
  /** Check if current viewport is below the given breakpoint */
  isDown: (breakpoint: Breakpoint) => boolean;
  /** Check if current viewport is between two breakpoints (inclusive) */
  isBetween: (minBreakpoint: Breakpoint, maxBreakpoint: Breakpoint) => boolean;
  /** Get breakpoint configuration */
  getBreakpointConfig: (breakpoint: Breakpoint) => BreakpointConfig;
}

/**
 * Get current breakpoint based on window width
 *
 * @param width - Window width in pixels
 * @returns Current breakpoint name
 */
const getCurrentBreakpoint = (width: number): Breakpoint => {
  if (width >= BREAKPOINTS.xl.minWidth) return 'xl';
  if (width >= BREAKPOINTS.lg.minWidth) return 'lg';
  if (width >= BREAKPOINTS.md.minWidth) return 'md';
  if (width >= BREAKPOINTS.sm.minWidth) return 'sm';
  return 'xs';
};

/**
 * useBreakpoints Hook
 *
 * Provides responsive breakpoint detection for React components.
 * Automatically tracks viewport size and updates breakpoint values on resize.
 *
 * This hook is SSR-safe and will default to desktop dimensions on the server.
 *
 * @returns Breakpoint values and utility functions
 *
 * @example
 * ```tsx
 * const { currentBreakpoint, isMobile, isDesktop, isUp } = useBreakpoints();
 *
 * // Show different content based on screen size
 * {isMobile && <MobileNavigation />}
 * {isDesktop && <DesktopNavigation />}
 *
 * // Check if screen is at least a certain size
 * {isUp('md') && <AdvancedFeatures />}
 *
 * // Conditional styling
 * <div style={{ fontSize: isMobile ? '14px' : '16px' }}>
 *   Responsive text
 * </div>
 *
 * // Conditional classes
 * <div className={currentBreakpoint === 'xs' ? 'mobile' : 'desktop'}>
 *   Content
 * </div>
 * ```
 */
export const useBreakpoints = (): BreakpointValues => {
  // Initialize state with default values (SSR-safe)
  const [windowSize, setWindowSize] = useState(() => {
    // Default to desktop dimensions for SSR
    if (typeof window === 'undefined') {
      return {
        width: 1200, // Default to lg breakpoint
        height: 800,
      };
    }
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  });

  // Update window size on resize
  useEffect(() => {
    // Skip effect on server
    if (typeof window === 'undefined') {
      return;
    }

    let timeoutId: NodeJS.Timeout;

    // Handle window resize with debouncing
    const handleResize = () => {
      // Clear previous timeout
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Debounce resize event to avoid excessive re-renders
      timeoutId = setTimeout(() => {
        setWindowSize({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, 150); // 150ms debounce
    };

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Initial check in case window size changed during initialization
    handleResize();

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  // Memoize current breakpoint calculation
  const currentBreakpoint = useMemo<Breakpoint>(() => {
    return getCurrentBreakpoint(windowSize.width);
  }, [windowSize.width]);

  // Memoize breakpoint flags
  const breakpointFlags = useMemo(() => {
    const { width } = windowSize;
    return {
      isXs: width >= BREAKPOINTS.xs.minWidth,
      isSm: width >= BREAKPOINTS.sm.minWidth,
      isMd: width >= BREAKPOINTS.md.minWidth,
      isLg: width >= BREAKPOINTS.lg.minWidth,
      isXl: width >= BREAKPOINTS.xl.minWidth,
      // Convenience flags for common breakpoints
      isMobile: width < BREAKPOINTS.sm.minWidth,
      isTablet:
        width >= BREAKPOINTS.sm.minWidth && width < BREAKPOINTS.md.minWidth,
      isDesktop: width >= BREAKPOINTS.md.minWidth,
    };
  }, [windowSize.width]);

  // Check if viewport is at least the given breakpoint
  const isUp = useCallback(
    (breakpoint: Breakpoint): boolean => {
      return windowSize.width >= BREAKPOINTS[breakpoint].minWidth;
    },
    [windowSize.width]
  );

  // Check if viewport is below the given breakpoint
  const isDown = useCallback(
    (breakpoint: Breakpoint): boolean => {
      return windowSize.width < BREAKPOINTS[breakpoint].minWidth;
    },
    [windowSize.width]
  );

  // Check if viewport is between two breakpoints (inclusive)
  const isBetween = useCallback(
    (minBreakpoint: Breakpoint, maxBreakpoint: Breakpoint): boolean => {
      const minWidth = BREAKPOINTS[minBreakpoint].minWidth;
      const maxWidth = BREAKPOINTS[maxBreakpoint].minWidth;
      return windowSize.width >= minWidth && windowSize.width < maxWidth;
    },
    [windowSize.width]
  );

  // Get breakpoint configuration
  const getBreakpointConfig = useCallback(
    (breakpoint: Breakpoint): BreakpointConfig => {
      return BREAKPOINTS[breakpoint];
    },
    []
  );

  return {
    currentBreakpoint,
    width: windowSize.width,
    height: windowSize.height,
    ...breakpointFlags,
    isUp,
    isDown,
    isBetween,
    getBreakpointConfig,
  };
};

export default useBreakpoints;
