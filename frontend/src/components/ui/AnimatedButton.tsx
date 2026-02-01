import React from 'react';
import { Button, ButtonProps } from '@mui/material';
import { motion } from 'framer-motion';

// Create motion-wrapped Button component
const MotionButton = motion(Button);

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
 * Props interface extending MUI ButtonProps
 */
export interface AnimatedButtonProps extends Omit<ButtonProps, 'variant'> {
  /**
   * Apply gradient background instead of solid color
   * Automatically overrides variant to 'contained' when gradient is specified
   */
  gradient?: GradientVariant;
}

/**
 * AnimatedButton Component
 *
 * Wraps MUI Button with subtle micro-interactions:
 * - Hover: Lifts up slightly (y: -2px)
 * - Press/Click: Scales down slightly (scale: 0.98)
 * - Fast animations (0.1-0.2s duration) for responsive feel
 *
 * All standard MUI Button props are supported via ...rest spread.
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
  sx,
  children,
  ...rest
}) => {
  // Apply gradient styles if gradient prop is provided
  const gradientSx = gradient
    ? {
        background: gradientMap[gradient],
        color: 'white',
        '&:hover': {
          background: gradientMap[gradient],
        },
        // Override variant to contained for gradient buttons
        ...(sx || {}),
      }
    : sx;

  return (
    <MotionButton
      // Framer Motion animations
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.1 }}
      // Force variant to contained if gradient is specified
      variant={gradient ? 'contained' : (rest.variant || 'text')}
      sx={gradientSx}
      {...rest}
    >
      {children}
    </MotionButton>
  );
};

export default AnimatedButton;
