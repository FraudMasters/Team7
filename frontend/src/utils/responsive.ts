/**
 * Responsive Utilities
 *
 * Lightweight utility functions for breakpoint matching without MUI dependencies.
 * Provides synchronous media query helpers using window.matchMedia.
 *
 * @module utils/responsive
 */

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
 * Breakpoint query order for comparisons
 */
const BREAKPOINT_ORDER: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];

/**
 * Get the current breakpoint based on window width
 *
 * @param width - Current window width in pixels
 * @returns Current breakpoint name
 *
 * @example
 * ```ts
 * import { getCurrentBreakpoint } from '@/utils/responsive';
 *
 * const breakpoint = getCurrentBreakpoint(window.innerWidth);
 * console.log(breakpoint); // 'md'
 * ```
 */
export function getCurrentBreakpoint(width: number): Breakpoint {
  if (width < BREAKPOINT_VALUES.sm) return 'xs';
  if (width < BREAKPOINT_VALUES.md) return 'sm';
  if (width < BREAKPOINT_VALUES.lg) return 'md';
  if (width < BREAKPOINT_VALUES.xl) return 'lg';
  return 'xl';
}

/**
 * Check if viewport width is >= specific breakpoint
 *
 * @param breakpoint - Breakpoint to check
 * @param width - Current window width in pixels
 * @returns true if viewport width >= breakpoint
 *
 * @example
 * ```ts
 * import { up } from '@/utils/responsive';
 *
 * if (up('md', window.innerWidth)) {
 *   // Render desktop layout
 * }
 * ```
 */
export function up(breakpoint: Breakpoint, width: number): boolean {
  return width >= BREAKPOINT_VALUES[breakpoint];
}

/**
 * Check if viewport width is < specific breakpoint
 *
 * @param breakpoint - Breakpoint to check
 * @param width - Current window width in pixels
 * @returns true if viewport width < breakpoint
 *
 * @example
 * ```ts
 * import { down } from '@/utils/responsive';
 *
 * if (down('md', window.innerWidth)) {
 *   // Render mobile/tablet layout
 * }
 * ```
 */
export function down(breakpoint: Breakpoint, width: number): boolean {
  if (breakpoint === 'xs') return false; // Nothing is below xs
  return width < BREAKPOINT_VALUES[breakpoint];
}

/**
 * Check if viewport is between two breakpoints
 *
 * @param start - Start breakpoint (inclusive)
 * @param end - End breakpoint (exclusive)
 * @param width - Current window width in pixels
 * @returns true if viewport is in range
 *
 * @example
 * ```ts
 * import { between } from '@/utils/responsive';
 *
 * if (between('sm', 'lg', window.innerWidth)) {
 *   // Render tablet-only layout
 * }
 * ```
 */
export function between(
  start: Breakpoint,
  end: Breakpoint,
  width: number
): boolean {
  const startIndex = BREAKPOINT_ORDER.indexOf(start);
  const endIndex = BREAKPOINT_ORDER.indexOf(end);

  if (startIndex === -1 || endIndex === -1 || startIndex >= endIndex) {
    console.warn(
      `between(${start}, ${end}): Invalid range - start must be before end`
    );
    return false;
  }

  return width >= BREAKPOINT_VALUES[start] && width < BREAKPOINT_VALUES[end];
}

/**
 * Check if viewport matches only one breakpoint range
 *
 * @param breakpoint - Breakpoint to check
 * @param width - Current window width in pixels
 * @returns true if viewport is in breakpoint range
 *
 * @example
 * ```ts
 * import { only } from '@/utils/responsive';
 *
 * if (only('md', window.innerWidth)) {
 *   // Render md-only layout (900px - 1199px)
 * }
 * ```
 */
export function only(breakpoint: Breakpoint, width: number): boolean {
  const index = BREAKPOINT_ORDER.indexOf(breakpoint);
  if (index === -1) return false;

  const startValue = BREAKPOINT_VALUES[breakpoint];
  const endValue =
    index < BREAKPOINT_ORDER.length - 1
      ? BREAKPOINT_VALUES[BREAKPOINT_ORDER[index + 1]]
      : Infinity;

  return width >= startValue && width < endValue;
}

/**
 * Create a media query string for a breakpoint
 *
 * @param breakpoint - Breakpoint
 * @returns Media query string (e.g., "(min-width: 600px)")
 *
 * @example
 * ```ts
 * import { createMediaQuery } from '@/utils/responsive';
 *
 * const query = createMediaQuery('sm');
 * console.log(query); // "(min-width: 600px)"
 * ```
 */
export function createMediaQuery(breakpoint: Breakpoint): string {
  return `(min-width: ${BREAKPOINT_VALUES[breakpoint]}px)`;
}

/**
 * Create a media query string for "down" breakpoint
 *
 * @param breakpoint - Breakpoint
 * @returns Media query string (e.g., "(max-width: 599px)")
 *
 * @example
 * ```ts
 * import { createMediaQueryDown } from '@/utils/responsive';
 *
 * const query = createMediaQueryDown('sm');
 * console.log(query); // "(max-width: 599px)"
 * ```
 */
export function createMediaQueryDown(breakpoint: Breakpoint): string {
  if (breakpoint === 'xs') return '(min-width: 0px)';
  return `(max-width: ${BREAKPOINT_VALUES[breakpoint] - 1}px)`;
}

/**
 * Create a media query string for "only" breakpoint range
 *
 * @param breakpoint - Breakpoint
 * @returns Media query string (e.g., "(min-width: 600px) and (max-width: 899px)")
 *
 * @example
 * ```ts
 * import { createMediaQueryOnly } from '@/utils/responsive';
 *
 * const query = createMediaQueryOnly('md');
 * console.log(query); // "(min-width: 900px) and (max-width: 1199px)"
 * ```
 */
export function createMediaQueryOnly(breakpoint: Breakpoint): string {
  const index = BREAKPOINT_ORDER.indexOf(breakpoint);
  if (index === -1) return '';

  const minValue = BREAKPOINT_VALUES[breakpoint];
  const maxValue =
    index < BREAKPOINT_ORDER.length - 1
      ? BREAKPOINT_VALUES[BREAKPOINT_ORDER[index + 1]] - 1
      : Infinity;

  if (maxValue === Infinity) {
    return `(min-width: ${minValue}px)`;
  }

  return `(min-width: ${minValue}px) and (max-width: ${maxValue}px)`;
}

/**
 * Synchronously check if a media query matches
 *
 * @param query - Media query string
 * @returns true if the media query currently matches
 *
 * @example
 * ```ts
 * import { matches } from '@/utils/responsive';
 *
 * if (matches('(min-width: 600px)')) {
 *   // Desktop layout
 * }
 * ```
 */
export function matches(query: string): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia(query).matches;
}

/**
 * Add a listener for media query changes
 *
 * @param query - Media query string
 * @param callback - Function to call when media query match status changes
 * @returns Cleanup function to remove the listener
 *
 * @example
 * ```ts
 * import { listen } from '@/utils/responsive';
 *
 * const cleanup = listen('(min-width: 600px)', (matches) => {
 *   console.log('Is desktop:', matches);
 * });
 *
 * // Later: cleanup();
 * ```
 */
export function listen(
  query: string,
  callback: (matches: boolean) => void
): () => void {
  if (typeof window === 'undefined') return () => {};

  const mediaQuery = window.matchMedia(query);

  // Use modern listener API if available, fallback to deprecated API
  const handler = (e: MediaQueryListEvent | MediaQueryList) => {
    callback(e.matches);
  };

  // Add listener
  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener('change', handler);
  } else {
    // Fallback for older browsers
    mediaQuery.addListener(handler);
  }

  // Return cleanup function
  return () => {
    if (mediaQuery.removeEventListener) {
      mediaQuery.removeEventListener('change', handler);
    } else {
      // Fallback for older browsers
      mediaQuery.removeListener(handler);
    }
  };
}
