import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Skeleton animation types
 */
export type SkeletonAnimation = 'pulse' | 'wave' | 'none';

/**
 * Skeleton variant types
 */
export type SkeletonVariant = 'text' | 'circular' | 'rectangular';

/**
 * Props for Skeleton component
 */
export interface SkeletonProps {
  /** Variant type */
  variant?: SkeletonVariant;
  /** Width of the skeleton (can be number in px or percentage string) */
  width?: number | string;
  /** Height of the skeleton (can be number in px or percentage string) */
  height?: number | string;
  /** Animation type */
  animation?: SkeletonAnimation;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** ARIA label for accessibility */
  'aria-label'?: string;
}

/**
 * Get animation styles based on animation type
 */
const getAnimationStyles = (animation: SkeletonAnimation) => {
  if (animation === 'pulse') {
    return {
      animation: 'skeleton-pulse 1.5s ease-in-out 0.5s infinite',
    };
  }

  if (animation === 'wave') {
    return {
      position: 'relative',
      overflow: 'hidden',
      '&::after': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
        animation: 'skeleton-wave 1.6s linear 0.5s infinite',
        transform: 'translateX(-100%)',
      },
    };
  }

  return {};
};

/**
 * Base skeleton styles
 */
const BaseSkeleton = styled('span')<{
  variant: SkeletonVariant;
  width?: number | string;
  height?: number | string;
  animation: SkeletonAnimation;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const styles: Record<string, any> = {
    display: 'inline-block',
    backgroundColor: theme.palette.action.hover,
    cursor: 'default',
    userSelect: 'none',
    pointerEvents: 'none',
    ...getAnimationStyles(props.animation),
  };

  // Width
  if (props.width !== undefined) {
    styles.width = typeof props.width === 'number' ? `${props.width}px` : props.width;
  }

  // Height
  if (props.height !== undefined) {
    styles.height = typeof props.height === 'number' ? `${props.height}px` : props.height;
  }

  // Variant-specific styles
  if (props.variant === 'text') {
    if (!props.height) {
      styles.height = '1em';
    }
    if (!props.width) {
      styles.width = '100%';
    }
    styles.borderRadius = '4px';
  } else if (props.variant === 'circular') {
    styles.borderRadius = '50%';
    if (!props.width) {
      styles.width = '40px';
    }
    if (!props.height) {
      styles.height = '40px';
    }
  } else if (props.variant === 'rectangular') {
    styles.borderRadius = theme.borderRadius.sm;
    if (!props.width) {
      styles.width = '100%';
    }
    if (!props.height) {
      styles.height = '1.75em';
    }
  }

  return styles;
});

/**
 * Animation keyframes
 */
const animationKeyframes = `
  @keyframes skeleton-pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  @keyframes skeleton-wave {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
`;

/**
 * Skeleton Component
 *
 * A placeholder component that displays a pulsing or wave animation to indicate
 * that content is loading. Used to improve perceived performance.
 *
 * @example
 * ```tsx
 * // Text skeleton (default)
 * <Skeleton />
 *
 * // Custom width text skeleton
 * <Skeleton width="60%" />
 *
 * // Rectangular skeleton (for cards, images)
 * <Skeleton variant="rectangular" height={200} />
 *
 * // Circular skeleton (for avatars)
 * <Skeleton variant="circular" width={40} height={40} />
 *
 * // Wave animation
 * <Skeleton variant="text" animation="wave" width={200} />
 *
 * // Multiple text lines
 * <Box>
 *   <Skeleton width="70%" />
 *   <Skeleton />
 *   <Skeleton width="60%" />
 * </Box>
 *
 * // Card skeleton pattern
 * <Box>
 *   <Skeleton variant="rectangular" height={180} />
 *   <Skeleton width="60%" sx={{ mt: 1 }} />
 *   <Skeleton />
 * </Box>
 * ```
 */
const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  animation = 'pulse',
  className,
  style,
  'aria-label': ariaLabel = 'Loading...',
}) => {
  return (
    <>
      <style>{animationKeyframes}</style>
      <BaseSkeleton
        variant={variant}
        width={width}
        height={height}
        animation={animation}
        className={className}
        style={style}
        aria-label={ariaLabel}
        role="status"
      />
    </>
  );
};

export default Skeleton;
