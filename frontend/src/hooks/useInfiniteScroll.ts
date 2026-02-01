/**
 * Infinite Scroll Hook
 *
 * A React hook for implementing infinite scroll functionality.
 * Detects when user scrolls near bottom of container and triggers load more callback.
 *
 * @example
 * ```tsx
 * const { ref, isNearBottom } = useInfiniteScroll({
 *   threshold: 200,
 *   enabled: true,
 * });
 *
 * useEffect(() => {
 *   if (isNearBottom && enabled && !isLoading) {
 *     loadMore();
 *   }
 * }, [isNearBottom]);
 * ```
 */

import { useEffect, useRef, useState } from 'react';

interface UseInfiniteScrollOptions {
  /**
   * Distance from bottom (in pixels) to trigger callback
   * @default 200
   */
  threshold?: number;

  /**
   * Whether infinite scroll is enabled
   * @default true
   */
  enabled?: boolean;
}

interface UseInfiniteScrollReturn {
  /**
   * Ref to attach to scrollable container element
   */
  ref: React.RefObject<HTMLDivElement>;

  /**
   * Whether user has scrolled near bottom
   */
  isNearBottom: boolean;

  /**
   * Manually check if near bottom (useful for initial load)
   */
  checkIfNearBottom: () => void;
}

export const useInfiniteScroll = ({
  threshold = 200,
  enabled = true,
}: UseInfiniteScrollOptions = {}): UseInfiniteScrollReturn => {
  const ref = useRef<HTMLDivElement>(null);
  const [isNearBottom, setIsNearBottom] = useState(false);

  /**
   * Check if user has scrolled near bottom of container
   */
  const checkIfNearBottom = () => {
    if (!ref.current || !enabled) {
      setIsNearBottom(false);
      return;
    }

    const { scrollTop, scrollHeight, clientHeight } = ref.current;
    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);

    setIsNearBottom(distanceFromBottom <= threshold);
  };

  /**
   * Attach scroll event listener
   */
  useEffect(() => {
    const element = ref.current;
    if (!element || !enabled) return;

    // Use passive event listener for better scroll performance
    const handleScroll = () => {
      requestAnimationFrame(checkIfNearBottom);
    };

    element.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      element.removeEventListener('scroll', handleScroll);
    };
  }, [enabled, threshold]);

  return {
    ref,
    isNearBottom,
    checkIfNearBottom,
  };
};
