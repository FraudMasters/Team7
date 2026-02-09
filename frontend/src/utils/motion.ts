/**
 * Motion Utilities
 *
 * Helper functions and utilities for working with Framer Motion animations.
 * Provides convenience functions for creating variants, managing animation
 * states, and building common motion patterns.
 *
 * @module utils/motion
 *
 * @example
 * ```tsx
 * import { motion } from 'framer-motion';
 * import { createVariants, getTransition } from '@/utils/motion';
 *
 * const variants = createVariants({
 *   hidden: { opacity: 0, y: 20 },
 *   visible: { opacity: 1, y: 0 }
 * });
 *
 * <motion.div
 *   variants={variants}
 *   initial="hidden"
 *   animate="visible"
 *   transition={getTransition('spring')}
 * >
 *   Content
 * </motion.div>
 * ```
 */

import type { Transition, Variants as VariantsType } from 'framer-motion';
import { transitions, variants, presets } from '@/config/motion';

/**
 * Preset transition speed names
 */
export type TransitionSpeed = 'fast' | 'default' | 'slow';

/**
 * Preset transition type names
 */
export type TransitionType = 'tween' | 'spring' | 'springSmooth' | 'springBouncy' | 'springInertial';

/**
 * Animation state names
 */
export type AnimationState = 'hidden' | 'visible' | 'exit' | 'hover' | 'tap';

/**
 * Direction for directional animations
 */
export type AnimationDirection = 'up' | 'down' | 'left' | 'right' | 'none';

/**
 * Variant preset names from motion config
 */
export type VariantPreset =
  | 'fade'
  | 'fadeUp'
  | 'fadeDown'
  | 'fadeLeft'
  | 'fadeRight'
  | 'slideLeft'
  | 'slideRight'
  | 'slideUp'
  | 'slideDown'
  | 'scaleIn'
  | 'scaleUp'
  | 'scaleDown'
  | 'scalePulse'
  | 'rotateIn'
  | 'flipHorizontal'
  | 'flipVertical'
  | 'blurIn';

/**
 * Get a transition configuration by preset name
 *
 * Returns a Framer Motion transition object for the specified preset.
 *
 * @param type - Transition type preset
 * @returns Transition configuration object
 *
 * @example
 * ```ts
 * import { getTransition } from '@/utils/motion';
 *
 * const transition = getTransition('spring');
 * // { type: 'spring', stiffness: 300, damping: 25 }
 *
 * const fastTransition = getTransition('fast');
 * // { type: 'tween', duration: 0.15, ease: [0.4, 0, 0.2, 1] }
 * ```
 */
export function getTransition(type: TransitionType | TransitionSpeed): Transition {
  return transitions[type] ?? transitions.default;
}

/**
 * Get animation variants by preset name
 *
 * Returns variant configuration for common animation patterns.
 *
 * @param preset - Variant preset name
 * @returns Variant object with hidden/visible states
 *
 * @example
 * ```ts
 * import { getVariants } from '@/utils/motion';
 *
 * const fadeVariants = getVariants('fadeUp');
 * // { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }
 *
 * const scaleVariants = getVariants('scaleIn');
 * // { hidden: { opacity: 0, scale: 0.9 }, visible: { opacity: 1, scale: 1 } }
 * ```
 */
export function getVariants(preset: VariantPreset): VariantsType {
  switch (preset) {
    case 'fade':
      return variants.fade.in;
    case 'fadeUp':
      return variants.fade.inDown;
    case 'fadeDown':
      return variants.fade.inUp;
    case 'fadeLeft':
      return variants.fade.inRight;
    case 'fadeRight':
      return variants.fade.inLeft;
    case 'slideLeft':
      return variants.slide.left;
    case 'slideRight':
      return variants.slide.right;
    case 'slideUp':
      return variants.slide.up;
    case 'slideDown':
      return variants.slide.down;
    case 'scaleIn':
      return variants.scale.in;
    case 'scaleUp':
      return variants.scale.up;
    case 'scaleDown':
      return variants.scale.down;
    case 'scalePulse':
      return variants.scale.pulse;
    case 'rotateIn':
      return variants.rotate.in;
    case 'flipHorizontal':
      return variants.flip.horizontal;
    case 'flipVertical':
      return variants.flip.vertical;
    case 'blurIn':
      return variants.blur.in;
    default:
      return variants.fade.in;
  }
}

/**
 * Create custom animation variants
 *
 * Helper function to create variants with proper typing and defaults.
 *
 * @param customVariants - Custom variant definitions
 * @returns Variant object
 *
 * @example
 * ```ts
 * import { createVariants } from '@/utils/motion';
 *
 * const variants = createVariants({
 *   hidden: { opacity: 0, scale: 0.8 },
 *   visible: { opacity: 1, scale: 1 },
 *   exit: { opacity: 0, scale: 0.8 }
 * });
 * ```
 */
export function createVariants<T extends string = AnimationState>(
  customVariants: Record<string, unknown>
): VariantsType {
  return customVariants as VariantsType;
}

/**
 * Create a fade variant with custom direction and distance
 *
 * @param direction - Direction to fade from
 * @param distance - Distance in pixels
 * @returns Variant object with hidden/visible states
 *
 * @example
 * ```ts
 * import { createFadeVariant } from '@/utils/motion';
 *
 * const variants = createFadeVariant('up', 30);
 * // { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }
 * ```
 */
export function createFadeVariant(
  direction: AnimationDirection = 'none',
  distance: number = 20
): VariantsType {
  const hidden: Record<string, unknown> = { opacity: 0 };
  const visible: Record<string, unknown> = { opacity: 1 };

  switch (direction) {
    case 'up':
      hidden.y = distance;
      visible.y = 0;
      break;
    case 'down':
      hidden.y = -distance;
      visible.y = 0;
      break;
    case 'left':
      hidden.x = distance;
      visible.x = 0;
      break;
    case 'right':
      hidden.x = -distance;
      visible.x = 0;
      break;
    case 'none':
      // No movement, just opacity
      break;
  }

  return { hidden, visible };
}

/**
 * Create scale variant with custom scale values
 *
 * @param fromScale - Starting scale value (default: 0.9)
 * @param toScale - Ending scale value (default: 1)
 * @param includeOpacity - Whether to include opacity animation
 * @returns Variant object with hidden/visible states
 *
 * @example
 * ```ts
 * import { createScaleVariant } from '@/utils/motion';
 *
 * const variants = createScaleVariant(0.5, 1, true);
 * // { hidden: { opacity: 0, scale: 0.5 }, visible: { opacity: 1, scale: 1 } }
 * ```
 */
export function createScaleVariant(
  fromScale: number = 0.9,
  toScale: number = 1,
  includeOpacity: boolean = true
): VariantsType {
  const hidden: Record<string, unknown> = { scale: fromScale };
  const visible: Record<string, unknown> = { scale: toScale };

  if (includeOpacity) {
    hidden.opacity = 0;
    visible.opacity = 1;
  }

  return { hidden, visible };
}

/**
 * Create stagger variants for animating children in sequence
 *
 * @param staggerDelay - Delay between each child
 * @param initialDelay - Delay before first child
 * @param childVariant - Optional custom variant for children
 * @returns Object with container and item variants
 *
 * @example
 * ```ts
 * import { createStaggerVariants } from '@/utils/motion';
 *
 * const { container, item } = createStaggerVariants(0.1, 0.2);
 *
 * <motion.div variants={container} initial="hidden" animate="visible">
 *   {items.map((item) => (
 *     <motion.div key={item.id} variants={item}>
 *       {item.content}
 *     </motion.div>
 *   ))}
 * </motion.div>
 * ```
 */
export function createStaggerVariants(
  staggerDelay: number = 0.1,
  initialDelay: number = 0,
  childVariant?: VariantsType
): { container: VariantsType; item: VariantsType } {
  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
        delayChildren: initialDelay,
      },
    },
  };

  const item =
    childVariant ??
    ({
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    } as VariantsType);

  return { container, item };
}

/**
 * Create hover animation variant
 *
 * @param scale - Scale amount on hover (default: 1.05)
 * @param lift - Y-axis lift on hover (default: 0)
 * @returns Object with hover state
 *
 * @example
 * ```ts
 * import { createHoverVariant } from '@/utils/motion';
 *
 * const hoverVariant = createHoverVariant(1.05, -4);
 * // { scale: 1.05, y: -4, transition: { duration: 0.15, ease: [...] } }
 *
 * <motion.div whileHover={hoverVariant}>
 *   Hover me
 * </motion.div>
 * ```
 */
export function createHoverVariant(scale: number = 1.05, lift: number = 0): Record<string, unknown> {
  const hoverState: Record<string, unknown> = {
    transition: transitions.fast,
  };

  if (scale !== 1) {
    hoverState.scale = scale;
  }

  if (lift !== 0) {
    hoverState.y = lift;
  }

  return hoverState;
}

/**
 * Create tap animation variant
 *
 * @param scale - Scale amount on tap (default: 0.95)
 * @returns Object with tap state
 *
 * @example
 * ```ts
 * import { createTapVariant } from '@/utils/motion';
 *
 * <motion.button whileTap={createTapVariant(0.95)}>
 *   Click me
 * </motion.button>
 * ```
 */
export function createTapVariant(scale: number = 0.95): Record<string, unknown> {
  return {
    scale,
    transition: transitions.fast,
  };
}

/**
 * Combine multiple variants into one
 *
 * Useful for creating complex animations from simple building blocks.
 *
 * @param variantPresets - Array of variant preset names or custom variants
 * @returns Combined variant object
 *
 * @example
 * ```ts
 * import { combineVariants } from '@/utils/motion';
 *
 * const variants = combineVariants([
 *   getVariants('fadeUp'),
 *   getVariants('scaleIn')
 * ]);
 * // Combines both fade and scale animations
 * ```
 */
export function combineVariants(variantPresets: Array<VariantsType | VariantPreset>): VariantsType {
  const combined: Record<string, unknown> = {};

  variantPresets.forEach((preset) => {
    const variant = typeof preset === 'string' ? getVariants(preset) : preset;

    Object.entries(variant).forEach(([key, value]) => {
      if (!combined[key]) {
        combined[key] = {};
      }
      Object.assign(combined[key] as Record<string, unknown>, value as Record<string, unknown>);
    });
  });

  return combined as VariantsType;
}

/**
 * Get a complete preset with variants and transitions
 *
 * Returns pre-configured animation presets for common UI patterns.
 *
 * @param presetName - Name of the preset ('modal', 'dropdown', 'listItem', 'card', 'page', 'tooltip', 'bentoCard')
 * @returns Complete preset with variants and exit states
 *
 * @example
 * ```ts
 * import { getPreset } from '@/utils/motion';
 *
 * const modalPreset = getPreset('modal');
 *
 * <motion.div
 *   variants={modalPreset}
 *   initial="hidden"
 *   animate="visible"
 *   exit="exit"
 * >
 *   Modal content
 * </motion.div>
 * ```
 */
export function getPreset(
  presetName: 'modal' | 'dropdown' | 'listItem' | 'card' | 'page' | 'tooltip' | 'bentoCard'
): VariantsType {
  return presets[presetName] as VariantsType;
}

/**
 * Create animation props for a motion component
 *
 * Convenience function that returns all common animation props.
 *
 * @param options - Animation options
 * @returns Props object for motion components
 *
 * @example
 * ```ts
 * import { createMotionProps } from '@/utils/motion';
 *
 * const props = createMotionProps({
 *   variant: 'fadeUp',
 *   transition: 'spring',
 *   delay: 0.2
 * });
 *
 * <motion.div {...props}>
 *   Content
 * </motion.div>
 * ```
 */
export function createMotionProps(options: {
  variant?: VariantPreset | VariantsType;
  transition?: TransitionType | TransitionSpeed | Transition;
  delay?: number;
  duration?: number;
}): {
  initial?: string;
  animate?: string;
  exit?: string;
  variants?: VariantsType;
  transition?: Transition;
} {
  const props: {
    initial?: string;
    animate?: string;
    exit?: string;
    variants?: VariantsType;
    transition?: Transition;
  } = {
    initial: 'hidden',
    animate: 'visible',
  };

  if (options.variant) {
    const variant = typeof options.variant === 'string' ? getVariants(options.variant) : options.variant;
    props.variants = variant;

    // Set exit state if available
    if ('exit' in variant) {
      props.exit = 'exit';
    }
  }

  if (options.transition) {
    const transition =
      typeof options.transition === 'string' ? getTransition(options.transition) : options.transition;
    props.transition = transition;
  }

  // Apply delay or duration overrides
  if (options.delay !== undefined || options.duration !== undefined) {
    const baseTransition = props.transition ?? transitions.default;
    props.transition = {
      ...baseTransition,
      ...(options.delay !== undefined && { delay: options.delay }),
      ...(options.duration !== undefined && { duration: options.duration }),
    } as Transition;
  }

  return props;
}

/**
 * Calculate animation duration based on content length
 *
 * Useful for creating dynamic timing based on text length or item count.
 *
 * @param itemCount - Number of items to animate
 * @param baseDuration - Base duration per item (default: 0.05)
 * @param maxDuration - Maximum total duration (default: 0.5)
 * @returns Calculated duration in seconds
 *
 * @example
 * ```ts
 * import { calculateDuration } from '@/utils/motion';
 *
 * const duration = calculateDuration(10, 0.05, 0.5);
 * // Returns 0.5 (capped at maxDuration)
 *
 * <motion.div transition={{ duration }} />
 * ```
 */
export function calculateDuration(
  itemCount: number,
  baseDuration: number = 0.05,
  maxDuration: number = 0.5
): number {
  const calculated = itemCount * baseDuration;
  return Math.min(calculated, maxDuration);
}

/**
 * Create delay array for staggered animations
 *
 * Generates an array of delay values for animating multiple items.
 *
 * @param count - Number of items
 * @param baseDelay - Delay between each item (default: 0.1)
 * @returns Array of delay values
 *
 * @example
 * ```ts
 * import { createDelayArray } from '@/utils/motion';
 *
 * const delays = createDelayArray(5, 0.1);
 * // [0, 0.1, 0.2, 0.3, 0.4]
 *
 * items.map((item, index) => (
 *   <motion.div
 *     key={item.id}
 *     animate={{ opacity: 1 }}
 *     transition={{ delay: delays[index] }}
 *   />
 * ))
 * ```
 */
export function createDelayArray(count: number, baseDelay: number = 0.1): number[] {
  return Array.from({ length: count }, (_, i) => i * baseDelay);
}

/**
 * Check if reduced motion is preferred
 *
 * Respects user's motion preferences for accessibility.
 *
 * @returns true if user prefers reduced motion
 *
 * @example
 * ```ts
 * import { prefersReducedMotion } from '@/utils/motion';
 *
 * const duration = prefersReducedMotion() ? 0 : 0.3;
 * <motion.div transition={{ duration }} />
 * ```
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get transition with reduced motion consideration
 *
 * Returns appropriate transition based on user's motion preferences.
 *
 * @param type - Transition type
 * @returns Transition configuration
 *
 * @example
 * ```ts
 * import { getAccessibleTransition } from '@/utils/motion';
 *
 * <motion.div transition={getAccessibleTransition('spring')} />
 * ```
 */
export function getAccessibleTransition(
  type: TransitionType | TransitionSpeed = 'default'
): Transition {
  if (prefersReducedMotion()) {
    return { duration: 0.01 };
  }
  return getTransition(type);
}

/**
 * Animation variants export
 *
 * Re-exports all variant presets for convenience
 */
export { variants };

/**
 * Transition presets export
 *
 * Re-exports all transition presets for convenience
 */
export { transitions };

/**
 * Motion config export
 *
 * Re-exports complete motion configuration
 */
export { presets };
