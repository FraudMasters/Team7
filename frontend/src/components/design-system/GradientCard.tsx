import React from 'react';
import styled from '@emotion/styled';
import { motion, HTMLMotionProps } from 'framer-motion';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Gradient variant options
 */
export type GradientVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'grey'
  | 'rainbow'
  | 'glossy'
  | 'shimmer'
  | 'custom';

/**
 * Gradient position options
 */
export type GradientPosition = 'top' | 'right' | 'bottom' | 'left' | 'all' | 'none';

/**
 * GradientCard component props interface
 */
export interface GradientCardProps extends Omit<HTMLMotionProps<'div'>, 'transition'> {
  /**
   * Card content
   */
  children?: React.ReactNode;
  /**
   * Gradient variant to use
   */
  variant?: GradientVariant;
  /**
   * Custom gradient (when variant is 'custom')
   */
  customGradient?: string;
  /**
   * Gradient border width in pixels
   */
  borderWidth?: number;
  /**
   * Gradient position (which sides have the gradient)
   */
  gradientPosition?: GradientPosition;
  /**
   * Card background color
   */
  background?: string;
  /**
   * If true, enables hover scale effect
   */
  hoverScale?: boolean;
  /**
   * Scale amount on hover (1.0 = no scale, 1.05 = 5% larger)
   */
  hoverScaleAmount?: number;
  /**
   * If true, enables elevation/shadow on hover
   */
  hoverElevation?: boolean;
  /**
   * If true, enables gradient rotation on hover
   */
  hoverRotate?: boolean;
  /**
   * Rotation angle in degrees on hover
   */
  hoverRotateAmount?: number;
  /**
   * If true, enables shimmer effect on hover
   */
  hoverShimmer?: boolean;
  /**
   * Border radius
   */
  borderRadius?: number | string;
  /**
   * Padding for card content
   */
  padding?: string | number;
  /**
   * If true, removes padding
   */
  disablePadding?: boolean;
  /**
   * CSS class name
   */
  className?: string;
  /**
   * Additional inline styles
   */
  style?: React.CSSProperties;
  /**
   * Reference to element
   */
  cardRef?: React.Ref<HTMLDivElement>;
}

/**
 * Get gradient from theme based on variant
 */
const getGradient = (variant: GradientVariant, theme: EmotionTheme, customGradient?: string): string => {
  if (variant === 'custom' && customGradient) {
    return customGradient;
  }

  const gradients = theme.gradients;
  switch (variant) {
    case 'primary':
      return gradients.primary;
    case 'secondary':
      return gradients.secondary;
    case 'success':
      return gradients.success;
    case 'error':
      return gradients.error;
    case 'warning':
      return gradients.warning;
    case 'info':
      return gradients.info;
    case 'grey':
      return gradients.grey;
    case 'rainbow':
      return gradients.rainbow;
    case 'glossy':
      return gradients.glossy;
    case 'shimmer':
      return gradients.shimmer;
    default:
      return gradients.primary;
  }
};

/**
 * Generate gradient border styles based on position
 */
const generateGradientBorder = (
  gradient: string,
  borderWidth: number,
  position: GradientPosition
): string => {
  const bw = typeof borderWidth === 'number' ? `${borderWidth}px` : borderWidth;

  switch (position) {
    case 'top':
      return `border-top: ${bw} solid transparent; border-image: linear-gradient(90deg, ${gradient.replace(/linear-gradient\([^,]+,\s*/, '').replace(')', '')}) 1;`;
    case 'right':
      return `border-right: ${bw} solid transparent; border-image: linear-gradient(180deg, ${gradient.replace(/linear-gradient\([^,]+,\s*/, '').replace(')', '')}) 1;`;
    case 'bottom':
      return `border-bottom: ${bw} solid transparent; border-image: linear-gradient(90deg, ${gradient.replace(/linear-gradient\([^,]+,\s*/, '').replace(')', '')}) 1;`;
    case 'left':
      return `border-left: ${bw} solid transparent; border-image: linear-gradient(180deg, ${gradient.replace(/linear-gradient\([^,]+,\s*/, '').replace(')', '')}) 1;`;
    case 'none':
      return '';
    case 'all':
    default:
      // Use pseudo-element approach for full gradient border
      return '';
  }
};

/**
 * Shimmer animation keyframes
 */
const shimmerAnimation = {
  shimmer: {
    '0%': { backgroundPosition: '-200% 0' },
    '100%': { backgroundPosition: '200% 0' },
  },
};

/**
 * Styled GradientCard wrapper for gradient border effect
 */
const GradientBorderWrapper = styled.div<{
  gradient: string;
  borderWidth: number;
  borderRadius: number | string;
  background: string;
}>`
  position: relative;
  background: ${({ background }) => background};
  border-radius: ${({ borderRadius }) => (typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius)};
  padding: ${({ borderWidth }) => borderWidth}px;
  background-clip: padding-box;

  /* Gradient border using pseudo-element */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: ${({ borderWidth }) => borderWidth}px;
    background: ${({ gradient }) => gradient};
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }
`;

/**
 * Styled GradientCard content area
 */
const StyledGradientCard = styled(motion.div)<{
  borderRadius: number | string;
  background: string;
  padding?: string | number;
  disablePadding?: boolean;
}>`
  position: relative;
  overflow: hidden;
  border-radius: ${({ borderRadius }) => (typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius)};
  background: ${({ background }) => background};
  box-sizing: border-box;

  /* Padding */
  ${({ disablePadding, padding }) => {
    if (disablePadding) return 'padding: 0;';
    if (padding !== undefined) {
      return typeof padding === 'number' ? `padding: ${padding}px;` : `padding: ${padding};`;
    }
    return 'padding: 24px;';
  }}
`;

/**
 * Shimmer overlay for hover effect
 */
const ShimmerOverlay = styled(motion.div)<{ shimmerGradient: string }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.1) 45%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.1) 55%,
    transparent 100%
  );
  background-size: 200% 100%;
  pointer-events: none;
  opacity: 0;
`;

/**
 * GradientCard Component
 *
 * A modern card component with gradient borders and Framer Motion hover effects.
 * Supports multiple gradient variants, custom animations, and micro-interactions.
 *
 * Features:
 * - Gradient borders using CSS pseudo-elements
 * - Framer Motion hover animations (scale, rotate, elevation)
 * - Shimmer effect on hover
 * - Multiple gradient variants from theme
 * - Custom gradient support
 * - Configurable border width, radius, and padding
 * - Fully accessible and themeable
 *
 * @example
 * ```tsx
 * // Basic gradient card
 * <GradientCard variant="primary">
 *   <Typography variant="h6">Primary Gradient</Typography>
 *   <Typography variant="body2">Content goes here...</Typography>
 * </GradientCard>
 *
 * // With hover scale
 * <GradientCard variant="secondary" hoverScale>
 *   <Typography variant="h6">Hover Me!</Typography>
 * </GradientCard>
 *
 * // With hover elevation
 * <GradientCard variant="success" hoverElevation hoverScale>
 *   <Typography variant="h6">Success Card</Typography>
 * </GradientCard>
 *
 * // With shimmer effect
 * <GradientCard variant="rainbow" hoverShimmer>
 *   <Typography variant="h6">Rainbow Shimmer</Typography>
 * </GradientCard>
 *
 * // Custom gradient
 * <GradientCard
 *   variant="custom"
 *   customGradient="linear-gradient(135deg, #ff6b6b 0%, #feca57 100%)"
 * >
 *   <Typography variant="h6">Custom Gradient</Typography>
 * </GradientCard>
 *
 * // With all hover effects
 * <GradientCard
 *   variant="info"
 *   hoverScale
 *   hoverElevation
 *   hoverShimmer
 *   hoverScaleAmount={1.05}
 * >
 *   <Typography variant="h6">Full Effects</Typography>
 * </GradientCard>
 *
 * // Without padding
 * <GradientCard variant="warning" disablePadding>
 *   <img src="/image.jpg" alt="No padding" />
 * </GradientCard>
 *
 * // Custom styling
 * <GradientCard
 *   variant="error"
 *   borderRadius={16}
 *   borderWidth={3}
 *   padding={32}
 * >
 *   <Typography variant="h6">Custom Styled</Typography>
 * </GradientCard>
 * ```
 */
export const GradientCard = React.forwardRef<HTMLDivElement, GradientCardProps>(
  (
    {
      children,
      variant = 'primary',
      customGradient,
      borderWidth = 2,
      gradientPosition = 'all',
      background = 'transparent',
      hoverScale = false,
      hoverScaleAmount = 1.03,
      hoverElevation = false,
      hoverRotate = false,
      hoverRotateAmount = 5,
      hoverShimmer = false,
      borderRadius = 12,
      padding,
      disablePadding = false,
      className,
      style,
      cardRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const gradient = getGradient(variant, theme, customGradient);

    // Motion variants for hover effects
    const cardVariants = {
      rest: {
        scale: 1,
        rotate: 0,
        boxShadow: hoverElevation
          ? '0 2px 8px -2px rgba(0, 0, 0, 0.1)'
          : '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      },
      hover: {
        scale: hoverScale ? hoverScaleAmount : 1,
        rotate: hoverRotate ? hoverRotateAmount : 0,
        boxShadow: hoverElevation
          ? '0 12px 24px -4px rgba(0, 0, 0, 0.15), 0 8px 12px -2px rgba(0, 0, 0, 0.1)'
          : '0 4px 12px -2px rgba(0, 0, 0, 0.1), 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
      },
    };

    // Transition config
    const transition = {
      type: 'spring' as const,
      stiffness: 400,
      damping: 25,
      mass: 0.8,
    };

    return (
      <GradientBorderWrapper
        gradient={gradient}
        borderWidth={borderWidth}
        borderRadius={borderRadius}
        background={background}
        className={className}
        style={style}
      >
        <StyledGradientCard
          ref={ref || cardRef}
          borderRadius={borderRadius}
          background={background}
          padding={padding}
          disablePadding={disablePadding}
          variants={cardVariants}
          initial="rest"
          whileHover="hover"
          transition={transition}
          {...rest}
        >
          {children}
          {hoverShimmer && (
            <ShimmerOverlay
              shimmerGradient={gradient}
              variants={{
                rest: { opacity: 0 },
                hover: {
                  opacity: 1,
                  transition: {
                    duration: 0.3,
                  },
                },
              }}
              animate={hoverShimmer ? 'hover' : 'rest'}
            >
              <motion.div
                style={{
                  width: '100%',
                  height: '100%',
                  background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)`,
                  backgroundSize: '200% 100%',
                }}
                animate={
                  hoverShimmer
                    ? {
                        backgroundPosition: ['200% 0', '-200% 0'],
                      }
                    : {}
                }
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            </ShimmerOverlay>
          )}
        </StyledGradientCard>
      </GradientBorderWrapper>
    );
  }
);

GradientCard.displayName = 'GradientCard';

/**
 * GradientCardContent Component
 *
 * A convenience component for GradientCard content area.
 * Automatically applies padding unless disabled.
 *
 * @example
 * ```tsx
 * <GradientCard>
 *   <GradientCardContent>
 *     <Typography variant="h5">Card Title</Typography>
 *     <Typography variant="body2">Card content...</Typography>
 *   </GradientCardContent>
 * </GradientCard>
 * ```
 */
export const GradientCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    disablePadding?: boolean;
    padding?: string | number;
  }
>(({ children, disablePadding = false, padding, ...rest }, ref) => {
  return (
    <div
      ref={ref}
      style={{
        padding: disablePadding ? 0 : padding !== undefined ? (typeof padding === 'number' ? `${padding}px` : padding) : undefined,
      }}
      {...rest}
    >
      {children}
    </div>
  );
});

GradientCardContent.displayName = 'GradientCardContent';

// Default export
export default GradientCard;
