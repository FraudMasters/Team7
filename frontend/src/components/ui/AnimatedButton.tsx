import React from 'react';
import { Button } from '@/components/ui';
import type { ButtonProps } from '@/components/ui/Button';

/**
 * Gradient variants matching the design system
 * Consistent with gradients used in BentoCard, LandingPage, and other components
 */
const gradientMap = {
  primary: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  secondary: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
  success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
} as const;

/**
 * Supported gradient variants
 */
export type GradientVariant = keyof typeof gradientMap;

/**
 * Props interface extending ButtonProps
 */
export interface AnimatedButtonProps extends Omit<ButtonProps, 'variant' | 'css'> {
  /**
   * Apply gradient background instead of solid color
   * Automatically overrides variant to 'contained' when gradient is specified
   */
  gradient?: GradientVariant;
  /** CSS styles */
  css?: any;
}

/**
 * AnimatedButton Component
 *
 * Wraps Button with subtle micro-interactions using CSS:
 * - Hover: Lifts up slightly and adds shadow
 * - Press/Click: Scales down slightly
 * - Fast transitions (0.1-0.2s duration) for responsive feel
 *
 * All standard Button props are supported via ...rest spread.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <AnimatedButton variant="contained" color="primary">
 *   Click Me
 * </AnimatedButton>
 *
 * // With gradient variant
 * <AnimatedButton gradient="primary">
 *   Get Started
 * </AnimatedButton>
 * ```
 */
export const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  gradient,
  css,
  children,
  ...rest
}) => {
  // Apply gradient styles if gradient prop is provided
  const gradientCss = gradient
    ? {
        background: gradientMap[gradient],
        color: 'white',
        '&:hover': {
          background: gradientMap[gradient],
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        },
        '&:active': {
          transform: 'scale(0.98)',
        },
        transition: 'transform 0.1s ease-out, box-shadow 0.1s ease-out',
        // Override variant to contained for gradient buttons
        ...(css || {}),
      }
    : {
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        },
        '&:active': {
          transform: 'scale(0.98)',
        },
        transition: 'transform 0.1s ease-out, box-shadow 0.1s ease-out',
        ...css,
      };

  return (
    <Button
      // Force variant to contained if gradient is specified
      variant={gradient ? 'contained' : (rest.variant || 'text')}
      css={gradientCss}
      {...rest}
    >
      {children}
    </Button>
  );
};

export default AnimatedButton;
