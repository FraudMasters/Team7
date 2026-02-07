import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  SxProps,
  Theme,
  alpha,
} from '@mui/material';
import { useSwipeGesture } from '../../hooks/useSwipeGesture';

export interface PullToRefreshProps {
  /**
   * Children content to be wrapped with pull-to-refresh functionality
   */
  children: React.ReactNode;

  /**
   * Callback function triggered when refresh is activated
   * Should return a promise that resolves when refresh is complete
   */
  onRefresh: () => Promise<void>;

  /**
   * Pull distance threshold (in pixels) to trigger refresh
   * @default 80
   */
  threshold?: number;

  /**
   * Maximum pull distance (in pixels) for visual feedback
   * @default 120
   */
  maxPullDistance?: number;

  /**
   * Whether the component is currently refreshing
   * @default false
   */
  refreshing?: boolean;

  /**
   * Height of the loading indicator area
   * @default 60
   */
  loaderHeight?: number;

  /**
   * Size of the loading spinner
   * @default 32
   */
  spinnerSize?: number;

  /**
   * Custom loading message
   */
  loadingMessage?: string;

  /**
   * Pull to refresh message
   */
  pullMessage?: string;

  /**
   * Release to refresh message
   */
  releaseMessage?: string;

  /**
   * Whether pull-to-refresh is enabled
   * @default true
   */
  enabled?: boolean;

  /**
   * Additional styles for the container
   */
  sx?: SxProps<Theme>;

  /**
   * Additional styles for the content wrapper
   */
  contentSx?: SxProps<Theme>;
}

/**
 * PullToRefresh Component
 *
 * A mobile-optimized pull-to-refresh component that detects downward swipe gestures
 * and triggers a refresh callback. Provides visual feedback during the pull gesture
 * and shows a loading indicator during refresh.
 *
 * @example
 * ```tsx
 * function CandidateList() {
 *   const [refreshing, setRefreshing] = useState(false);
 *
 *   const handleRefresh = async () => {
 *     setRefreshing(true);
 *     await fetchCandidates();
 *     setRefreshing(false);
 *   };
 *
 *   return (
 *     <PullToRefresh
 *       onRefresh={handleRefresh}
 *       refreshing={refreshing}
 *       loadingMessage="Updating candidates..."
 *     >
 *       <CandidateList />
 *     </PullToRefresh>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With custom threshold and messages
 * <PullToRefresh
 *   onRefresh={refreshData}
 *   threshold={100}
 *   maxPullDistance={150}
 *   pullMessage="Pull down to refresh"
 *   releaseMessage="Release to update"
 *   loadingMessage="Loading..."
 * >
 *   <Content />
 * </PullToRefresh>
 * ```
 */
const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  threshold = 80,
  maxPullDistance = 120,
  refreshing: externalRefreshing = false,
  loaderHeight = 60,
  spinnerSize = 32,
  loadingMessage = 'Loading...',
  pullMessage = 'Pull down to refresh',
  releaseMessage = 'Release to refresh',
  enabled = true,
  sx,
  contentSx,
}) => {
  const [internalRefreshing, setInternalRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [pulling, setPulling] = useState(false);

  const refreshing = externalRefreshing || internalRefreshing;
  const containerRef = useRef<HTMLDivElement>(null);
  const startTouchY = useRef<number>(0);
  const currentTouchY = useRef<number>(0);

  // Calculate pull progress (0 to 1)
  const pullProgress = Math.min(pullDistance / threshold, 1);

  // Handle refresh action
  const handleRefresh = useCallback(async () => {
    if (refreshing) return;

    setInternalRefreshing(true);
    setPullDistance(0);
    setPulling(false);

    try {
      await onRefresh();
    } catch (error) {
      console.error('Pull-to-refresh error:', error);
    } finally {
      setInternalRefreshing(false);
    }
  }, [onRefresh, refreshing]);

  // Handle pull start
  const handlePullStart = useCallback(() => {
    if (refreshing || !enabled) return;
    setPulling(true);
    startTouchY.current = 0;
    currentTouchY.current = 0;
  }, [refreshing, enabled]);

  // Handle pulling
  const handlePulling = useCallback((eventData: { deltaY: number; absY: number }) => {
    if (refreshing || !enabled || !pulling) return;

    // Only track downward pulls (positive deltaY)
    if (eventData.deltaY > 0) {
      const newDistance = Math.min(eventData.deltaY, maxPullDistance);
      setPullDistance(newDistance);
      currentTouchY.current = eventData.absY;
    }
  }, [refreshing, enabled, pulling, maxPullDistance]);

  // Handle pull end
  const handlePullEnd = useCallback(() => {
    if (refreshing || !enabled || !pulling) return;

    setPulling(false);

    // Trigger refresh if threshold exceeded
    if (pullDistance >= threshold) {
      handleRefresh();
    } else {
      // Reset if threshold not met
      setPullDistance(0);
    }
  }, [refreshing, enabled, pulling, pullDistance, threshold, handleRefresh]);

  // Setup swipe gesture for pull-down detection
  const swipeProps = useSwipeGesture(
    {
      onSwipeStart: handlePullStart,
      onSwiping: handlePulling as any,
      onSwiped: handlePullEnd,
    },
    {
      delta: 5,
      track: 'down',
      enabled,
      touchAction: 'pan-y',
    }
  );

  // Calculate rotation for spinner based on pull distance
  const spinnerRotation = pullDistance * 2;

  // Determine which message to show
  const getMessage = () => {
    if (refreshing) return loadingMessage;
    if (pullDistance >= threshold) return releaseMessage;
    if (pullDistance > 0) return pullMessage;
    return null;
  };

  const message = getMessage();

  return (
    <Box
      ref={(node) => {
        // Attach both refs
        if (node) {
          containerRef.current = node;
          (swipeProps as any).ref(node);
        }
      }}
      sx={{
        position: 'relative',
        width: '100%',
        overflow: 'hidden',
        ...sx,
      }}
    >
      {/* Loading Indicator Area */}
      <Box
        sx={{
          height: loaderHeight,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          transform: `translateY(${-loaderHeight + Math.max(0, pullDistance - loaderHeight)}px)`,
          opacity: pullDistance > 0 || refreshing ? 1 : 0,
          transition: refreshing ? 'none' : 'transform 0.1s ease-out, opacity 0.2s',
          bgcolor: (theme) => alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(4px)',
          zIndex: 10,
        }}
      >
        {refreshing ? (
          // Full spinner when refreshing
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <CircularProgress size={spinnerSize} />
            {message && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontSize: '0.75rem' }}
              >
                {message}
              </Typography>
            )}
          </Box>
        ) : (
          // Partially visible spinner during pull
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
              opacity: pullProgress,
              transform: `rotate(${spinnerRotation}deg)`,
            }}
          >
            <CircularProgress
              size={spinnerSize}
              value={pullProgress * 100}
              variant={pullProgress > 0 ? 'determinate' : 'indeterminate'}
              sx={{
                transition: 'none',
              }}
            />
            {message && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontSize: '0.75rem' }}
              >
                {message}
              </Typography>
            )}
          </Box>
        )}
      </Box>

      {/* Content Wrapper */}
      <Box
        sx={{
          transform: refreshing
            ? 'none'
            : `translateY(${Math.max(0, pullDistance - loaderHeight)}px)`,
          transition: refreshing || pulling
            ? 'none'
            : 'transform 0.3s ease-out',
          ...contentSx,
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default PullToRefresh;
