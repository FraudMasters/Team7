/**
 * useSwipeGesture Hook
 *
 * A custom hook for handling touch swipe gestures on elements.
 * Provides a simplified interface for detecting swipe directions
 * (left, right, up, down) with configurable threshold and callbacks.
 *
 * @module hooks/useSwipeGesture
 */

import { useCallback, useRef } from 'react';
import { useSwipeable } from 'react-swipeable';

/**
 * Swipe direction names
 */
export type SwipeDirection = 'left' | 'right' | 'up' | 'down';

/**
 * Swipe event data
 *
 * Contains information about the swipe gesture including
 * direction, distance, velocity, and original event.
 */
export interface SwipeEventData {
  /**
   * Direction of the swipe gesture
   */
  direction: SwipeDirection;

  /**
   * Horizontal distance traveled in pixels
   */
  deltaX: number;

  /**
   * Vertical distance traveled in pixels
   */
  deltaY: number;

  /**
   * Absolute distance traveled in pixels
   */
  absX: number;

  /**
   * Absolute vertical distance traveled in pixels
   */
  absY: number;

  /**
   * Swipe velocity in pixels/second
   */
  velocity: number;

  /**
   * Original touch event
   */
  event: React.TouchEvent | TouchEvent;
}

/**
 * Swipe callback function
 *
 * Called when a swipe gesture is detected.
 *
 * @param data - Swipe event data
 */
export type SwipeCallback = (data: SwipeEventData) => void;

/**
 * Swipe gesture handlers configuration
 *
 * Optional callbacks for each swipe direction.
 */
export interface SwipeHandlers {
  /**
   * Called when swiping left (moving from right to left)
   *
   * @example
   * ```tsx
   * onSwipedLeft: () => {
   *   // Navigate to next item
   *   setNextItem();
   * }
   * ```
   */
  onSwipedLeft?: SwipeCallback;

  /**
   * Called when swiping right (moving from left to right)
   *
   * @example
   * ```tsx
   * onSwipedRight: () => {
   *   // Navigate to previous item
   *   setPreviousItem();
   * }
   * ```
   */
  onSwipedRight?: SwipeCallback;

  /**
   * Called when swiping up (moving from bottom to top)
   *
   * @example
   * ```tsx
   * onSwipedUp: () => {
   *   // Show more details
   *   expandCard();
   * }
   * ```
   */
  onSwipedUp?: SwipeCallback;

  /**
   * Called when swiping down (moving from top to bottom)
   *
   * @example
   * ```tsx
   * onSwipedDown: () => {
   *   // Dismiss card
   *   dismissModal();
   * }
   * ```
   */
  onSwipedDown?: SwipeCallback;

  /**
   * Called when swiping starts
   *
   * @example
   * ```tsx
   * onSwipeStart: () => {
   *   // Prepare for swipe
   *   setSwipeActive(true);
   * }
   * ```
   */
  onSwipeStart?: (event: React.TouchEvent | TouchEvent) => void;

  /**
   * Called during swiping (throttled)
   *
   * @example
   * ```tsx
   * onSwiping: (eventData) => {
   *   // Update UI during swipe
   *   setSwipeOffset(eventData.deltaX);
   * }
   * ```
   */
  onSwiping?: (eventData: SwipeEventData) => void;

  /**
   * Called when swiping ends (after direction callbacks)
   *
   * @example
   * ```tsx
   * onSwiped: (eventData) => {
   *   // Cleanup after swipe
   *   setSwipeActive(false);
   *   resetOffset();
   * }
   * ```
   */
  onSwiped?: (eventData: SwipeEventData) => void;
}

/**
 * useSwipeGesture configuration options
 *
 * Optional configuration to customize swipe detection behavior.
 */
export interface UseSwipeGestureOptions {
  /**
   * Minimum distance (in pixels) for a swipe to be detected
   * @default 10
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   delta: 20 // Require 20px swipe
   * });
   * ```
   */
  delta?: number;

  /**
   * Prevents default behavior when swiping occurs
   * @default false
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   preventScrollOnSwipe: true // Prevent page scroll on swipe
   * });
   * ```
   */
  preventScrollOnSwipe?: boolean;

  /**
   * Direction(s) to track swipes for
   * @default ['left', 'right', 'up', 'down']
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   track: ['left', 'right'] // Only track horizontal swipes
   * });
   * ```
   */
  track?: SwipeDirection | SwipeDirection[];

  /**
   * Rotation angle (in degrees) for diagonal swipes
   * @default 0
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   rotation: 45 // Detect diagonal swipes
   * });
   * ```
   */
  rotation?: number;

  /**
   * Touch node to attach swipe handlers to
   * @default The element ref is attached to
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   touchAction: 'none' // Allow swipes with CSS touch-action: none
   * });
   * ```
   */
  touchAction?: 'none' | 'pan-y' | 'pan-x';

  /**
   * Whether the swipe detection is enabled
   * @default true
   *
   * @example
   * ```ts
   * const swipeProps = useSwipeGesture({
   *   onSwipedLeft: handleLeft,
   * }, {
   *   enabled: false // Disable swipe detection
   * });
   * ```
   */
  enabled?: boolean;
}

/**
 * Swipe gesture result
 *
 * Contains the handler props to spread onto a target element.
 */
export interface UseSwipeGestureResult {
  /**
   * Props to spread onto the target element
   *
   * @example
   * ```tsx
   * function MyComponent() {
   *   const swipeProps = useSwipeGesture({
   *     onSwipedLeft: () => console.log('Swiped left!')
   *   });
   *
   *   return <div {...swipeProps}>Swipe me!</div>;
   * }
   * ```
   */
  ref: (node: HTMLElement | null) => void;
}

/**
 * Convert react-swipeable direction to our SwipeDirection type
 *
 * @param direction - Direction from react-swipeable
 * @returns Mapped SwipeDirection or undefined
 *
 * @private
 */
function mapDirection(
  direction: 'Left' | 'Right' | 'Up' | 'Down'
): SwipeDirection | undefined {
  switch (direction) {
    case 'Left':
      return 'left';
    case 'Right':
      return 'right';
    case 'Up':
      return 'up';
    case 'Down':
      return 'down';
    default:
      return undefined;
  }
}

/**
 * useSwipeGesture Hook
 *
 * Provides touch swipe gesture detection for React elements.
 * Wraps react-swipeable with a simplified API that includes
 * direction-specific callbacks.
 *
 * @param handlers - Swipe handler callbacks for different directions
 * @param options - Configuration options for swipe detection
 * @returns Props object to spread onto the target element
 *
 * @example
 * ```tsx
 * import { useSwipeGesture } from '@/hooks/useSwipeGesture';
 *
 * function SwipeableCard() {
 *   const [currentIndex, setCurrentIndex] = useState(0);
 *
 *   const swipeProps = useSwipeGesture(
 *     {
 *       onSwipedLeft: () => {
 *         setCurrentIndex((i) => Math.min(i + 1, items.length - 1));
 *       },
 *       onSwipedRight: () => {
 *         setCurrentIndex((i) => Math.max(i - 1, 0));
 *       },
 *       onSwipedUp: () => {
 *         console.log('Expand card');
 *       },
 *       onSwipedDown: () => {
 *         console.log('Dismiss card');
 *       },
 *     },
 *     {
 *       delta: 50,
 *       preventScrollOnSwipe: true,
 *       track: ['left', 'right', 'up', 'down'],
 *     }
 *   );
 *
 *   return (
 *     <div {...swipeProps} className="card">
 *       <h2>Item {currentIndex}</h2>
 *       <p>Swipe left/right to navigate, up to expand, down to dismiss</p>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function PhotoCarousel() {
 *   const [currentPhoto, setCurrentPhoto] = useState(0);
 *
 *   const swipeProps = useSwipeGesture({
 *     onSwipedLeft: () => setCurrentPhoto((p) => p + 1),
 *     onSwipedRight: () => setCurrentPhoto((p) => p - 1),
 *   });
 *
 *   return (
 *     <div {...swipeProps}>
 *       <img src={photos[currentPhoto]} alt={`Photo ${currentPhoto}`} />
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function PullToRefresh() {
 *   const [refreshing, setRefreshing] = useState(false);
 *   const [offset, setOffset] = useState(0);
 *
 *   const swipeProps = useSwipeGesture(
 *     {
 *       onSwiping: (data) => {
 *         if (data.deltaY > 0) {
 *           setOffset(Math.min(data.deltaY, 100));
 *         }
 *       },
 *       onSwipedDown: async () => {
 *         if (offset > 50) {
 *           setRefreshing(true);
 *           await refreshData();
 *           setRefreshing(false);
 *         }
 *         setOffset(0);
 *       },
 *       onSwiped: () => {
 *         setOffset(0);
 *       },
 *     },
 *     {
 *       delta: 10,
 *       track: 'down',
 *     }
 *   );
 *
 *   return (
 *     <div {...swipeProps} style={{ transform: `translateY(${offset}px)` }}>
 *       {refreshing ? <LoadingSpinner /> : <Content />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useSwipeGesture(
  handlers: SwipeHandlers,
  options: UseSwipeGestureOptions = {}
): UseSwipeGestureResult {
  // Store refs to callbacks to avoid recreating handlers on every render
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  // Convert our SwipeEventData to the format react-swipeable expects
  const onSwiped = useCallback((eventData: any) => {
    const direction = mapDirection(eventData.dir);
    if (!direction) return;

    const swipeData: SwipeEventData = {
      direction,
      deltaX: eventData.deltaX,
      deltaY: eventData.deltaY,
      absX: eventData.absX,
      absY: eventData.absY,
      velocity: eventData.velocity,
      event: eventData.event,
    };

    // Call direction-specific callback
    const directionHandlers: Record<SwipeDirection, keyof SwipeHandlers> = {
      left: 'onSwipedLeft',
      right: 'onSwipedRight',
      up: 'onSwipedUp',
      down: 'onSwipedDown',
    };

    const handlerKey = directionHandlers[direction];
    const handler = handlersRef.current[handlerKey];
    if (handler) {
      handler(swipeData);
    }

    // Call general onSwiped callback
    if (handlersRef.current.onSwiped) {
      handlersRef.current.onSwiped(swipeData);
    }
  }, []);

  const onSwiping = useCallback((eventData: any) => {
    if (!handlersRef.current.onSwiping) return;

    const direction = mapDirection(eventData.dir);
    if (!direction) return;

    const swipeData: SwipeEventData = {
      direction,
      deltaX: eventData.deltaX,
      deltaY: eventData.deltaY,
      absX: eventData.absX,
      absY: eventData.absY,
      velocity: eventData.velocity,
      event: eventData.event,
    };

    handlersRef.current.onSwiping(swipeData);
  }, []);

  const onSwipeStart = useCallback((eventData: any) => {
    if (handlersRef.current.onSwipeStart) {
      handlersRef.current.onSwipeStart(eventData.event);
    }
  }, []);

  // Build react-swipeable config
  const swipeableConfig = {
    onSwiped,
    onSwiping,
    onSwipeStart,
    delta: options.delta ?? 10,
    preventScrollOnSwipe: options.preventScrollOnSwipe ?? false,
    track: options.track ?? (['left', 'right', 'up', 'down'] as any),
    rotation: options.rotation ?? 0,
    touchAction: options.touchAction ?? 'none',
    enabled: options.enabled ?? true,
  };

  // Get handler props from react-swipeable
  const swipeHandlers = useSwipeable(swipeableConfig);

  return swipeHandlers as unknown as UseSwipeGestureResult;
}

export default useSwipeGesture;
