import { useState, useEffect } from 'react';

/**
 * useMediaQuery Hook
 *
 * A hook that listens for matches to a CSS media query.
 *
 * @param query - The media query to match
 * @returns Boolean indicating if the media query matches
 *
 * @example
 * ```tsx
 * const isMobile = useMediaQuery('(max-width: 768px)');
 * const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
 * ```
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia(query);
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);

    // Set initial value
    setMatches(mediaQuery.matches);

    // Add listener for changes
    mediaQuery.addEventListener('change', handler);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener('change', handler);
    };
  }, [query]);

  return matches;
}

export default useMediaQuery;
