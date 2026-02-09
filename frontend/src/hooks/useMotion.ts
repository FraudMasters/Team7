/**
 * useMotion Hook
 *
 * A custom hook for managing Framer Motion animations in React components.
 * Provides motion control, animation state tracking, variant presets,
 * and accessibility support for reduced motion preferences.
 *
 * @module hooks/useMotion
 * @example
 * ```tsx
 * import { motion } from 'framer-motion';
 * import { useMotion } from '@/hooks/useMotion';
 *
 * function AnimatedComponent() {
 *   const { controls, variants, state } = useMotion({
 *     variant: 'fadeUp',
 *     autoStart: true
 *   });
 *
 *   return (
 *     <motion.div
 *       animate={controls}
 *       variants={variants}
 *       initial="hidden"
 *     >
 *       Content with animation
 *     </motion.div>
 *   );
 * }
 * ```
 */

import { useEffect, useCallback, useMemo, useState } from 'react';
import type { Variants as VariantsType, AnimationControls } from 'framer-motion';
import { variants, transitions } from '@/config/motion';
import {
  getVariants,
  getTransition,
  createFadeVariant,
  createScaleVariant,
  prefersReducedMotion,
} from '@/utils/motion';

/**
 * Motion control options
 */
export interface UseMotionOptions {
  /**
   * Animation variant preset name
   * @default 'fade'
   */
  variant?: 'fade' | 'fadeUp' | 'fadeDown' | 'fadeLeft' | 'fadeRight' |
    'slideLeft' | 'slideRight' | 'slideUp' | 'slideDown' |
    'scaleIn' | 'scaleUp' | 'scaleDown' | 'scalePulse' |
    'rotateIn' | 'flipHorizontal' | 'flipVertical' | 'blurIn';

  /**
   * Custom variants object
   * Overrides variant preset if provided
   */
  variants?: VariantsType;

  /**
   * Transition type or speed
   * @default 'default'
   */
  transition?: 'fast' | 'default' | 'slow' | 'tween' | 'spring' |
    'springSmooth' | 'springBouncy' | 'springInertial';

  /**
   * Auto-start animation on mount
   * @default true
   */
  autoStart?: boolean;

  /**
   * Animation duration in seconds
   * Overrides transition duration
   */
  duration?: number;

  /**
   * Animation delay in seconds
   * @default 0
   */
  delay?: number;

  /**
   * Respect user's reduced motion preference
   * @default true
   */
  respectReducedMotion?: boolean;

  /**
   * Direction for directional fade animations
   * @default 'up'
   */
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';

  /**
   * Distance for directional animations in pixels
   * @default 20
   */
  distance?: number;

  /**
   * Scale values for scale animations
   */
  scale?: {
    from?: number;
    to?: number;
  };
}

/**
 * Motion state information
 */
export interface MotionState {
  /**
   * Current animation state
   */
  state: 'idle' | 'animating' | 'complete';

  /**
   * Whether reduced motion is preferred
   */
  reducedMotion: boolean;

  /**
   * Whether animation is currently playing
   */
  isPlaying: boolean;

  /**
   * Whether animation is paused
   */
  isPaused: boolean;
}

/**
 * Motion control methods
 */
export interface MotionControls {
  /**
   * Start the animation
   */
  play: () => void;

  /**
   * Pause the animation
   */
  pause: () => void;

  /**
   * Stop and reset the animation
   */
  stop: () => void;

  /**
   * Restart the animation from beginning
   */
  restart: () => void;

  /**
   * Reverse the animation direction
   */
  reverse: () => void;

  /**
   * Toggle between play and pause
   */
  toggle: () => void;
}

/**
 * useMotion Hook return value
 */
export interface UseMotionResult {
  /**
   * Animation state string ('hidden' | 'visible' | 'exit')
   * Pass to motion component's animate/initial props
   */
  controls: string;

  /**
   * Animation variants object
   * Pass to motion component's variants prop
   */
  variants: VariantsType;

  /**
   * Transition configuration
   * Pass to motion component's transition prop
   */
  transition: object;

  /**
   * Current motion state information
   */
  state: MotionState;

  /**
   * Motion control methods
   */
  controlsAPI: MotionControls;
}

/**
 * useMotion Hook
 *
 * Provides a comprehensive API for managing Framer Motion animations
 * with accessibility support and common animation patterns.
 *
 * @param options - Motion configuration options
 * @returns UseMotionResult object with animation controls and state
 *
 * @example
 * ```tsx
 * function FadeInComponent() {
 *   const { controls, variants, transition } = useMotion({
 *     variant: 'fadeUp',
 *     autoStart: true
 *   });
 *
 *   return (
 *     <motion.div
 *       initial="hidden"
 *       animate={controls}
 *       variants={variants}
 *       transition={transition}
 *     >
 *       Fades in from below
 *     </motion.div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function InteractiveCard() {
 *   const { controls, variants, transition, controlsAPI } = useMotion({
 *     variant: 'scaleIn',
 *     autoStart: false
 *   });
 *
 *   return (
 *     <motion.div
 *       initial="hidden"
 *       animate={controls}
 *       variants={variants}
 *       transition={transition}
 *       onHoverStart={controlsAPI.play}
 *       onHoverEnd={controlsAPI.reverse}
 *     >
 *       Scales in on hover
 *     </motion.div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function CustomAnimation() {
 *   const { controls, variants, transition, state } = useMotion({
 *     direction: 'left',
 *     distance: 50,
 *     duration: 0.8,
 *     delay: 0.2
 *   });
 *
 *   return (
 *     <motion.div
 *       initial="hidden"
 *       animate={controls}
 *       variants={variants}
 *       transition={transition}
 *     >
 *       Custom fade from left
 *     </motion.div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function AccessibleAnimation() {
 *   const { controls, variants, transition, state } = useMotion({
 *     variant: 'fadeUp',
 *     respectReducedMotion: true
 *   });
 *
 *   // Animation automatically respects user preferences
 *   return (
 *     <motion.div
 *       initial="hidden"
 *       animate={controls}
 *       variants={variants}
 *       transition={transition}
 *     >
 *       Respects prefers-reduced-motion
 *     </motion.div>
 *   );
 * }
 * ```
 */
export function useMotion(options: UseMotionOptions = {}): UseMotionResult {
  const {
    variant: variantPreset = 'fade',
    variants: customVariants,
    transition: transitionPreset = 'default',
    autoStart = true,
    duration,
    delay = 0,
    respectReducedMotion = true,
    direction = 'up',
    distance = 20,
    scale,
  } = options;

  // Animation state tracking
  const [animationState, setAnimationState] = useState<'idle' | 'animating' | 'complete'>('idle');
  const [isPaused, setIsPaused] = useState(false);
  const [controlState, setControlState] = useState<'hidden' | 'visible'>('hidden');

  // Check for reduced motion preference
  const reducedMotion = useMemo(() => prefersReducedMotion(), []);

  // Determine if animation should run
  const shouldAnimate = useMemo(() => {
    return !respectReducedMotion || !reducedMotion;
  }, [respectReducedMotion, reducedMotion]);

  // Build variants
  const motionVariants = useMemo(() => {
    if (customVariants) {
      return customVariants;
    }

    if (variantPreset === 'fade' && direction !== 'none') {
      return createFadeVariant(direction, distance);
    }

    if (variantPreset.startsWith('scale') && scale) {
      return createScaleVariant(scale.from, scale.to, true);
    }

    return getVariants(variantPreset);
  }, [customVariants, variantPreset, direction, distance, scale]);

  // Build transition
  const motionTransition = useMemo(() => {
    const baseTransition = getTransition(transitionPreset);

    if (!shouldAnimate) {
      return { duration: 0 };
    }

    if (duration !== undefined) {
      return { ...baseTransition, duration };
    }

    if (delay > 0) {
      return { ...baseTransition, delay };
    }

    return baseTransition;
  }, [transitionPreset, shouldAnimate, duration, delay]);

  // Auto-start animation on mount
  useEffect(() => {
    if (autoStart && shouldAnimate) {
      const timer = setTimeout(() => {
        setControlState('visible');
        setAnimationState('animating');
      }, delay * 1000);

      return () => clearTimeout(timer);
    }
  }, [autoStart, shouldAnimate, delay]);

  // Mark animation as complete after duration
  useEffect(() => {
    if (animationState === 'animating' && !isPaused) {
      const animationDuration = (duration ?? 0.3) * 1000;
      const timer = setTimeout(() => {
        setAnimationState('complete');
      }, animationDuration + delay * 1000);

      return () => clearTimeout(timer);
    }
  }, [animationState, isPaused, duration, delay]);

  // Control methods
  const play = useCallback(() => {
    if (shouldAnimate) {
      setControlState('visible');
      setAnimationState('animating');
      setIsPaused(false);
    }
  }, [shouldAnimate]);

  const pause = useCallback(() => {
    setIsPaused(true);
  }, []);

  const stop = useCallback(() => {
    setControlState('hidden');
    setAnimationState('idle');
    setIsPaused(false);
  }, []);

  const restart = useCallback(() => {
    if (shouldAnimate) {
      setControlState('hidden');
      setIsPaused(false);
      // Reset to hidden first, then animate to visible
      requestAnimationFrame(() => {
        setControlState('visible');
        setAnimationState('animating');
      });
    }
  }, [shouldAnimate]);

  const reverse = useCallback(() => {
    if (shouldAnimate) {
      setControlState(prev => prev === 'visible' ? 'hidden' : 'visible');
      setAnimationState('animating');
      setIsPaused(false);
    }
  }, [shouldAnimate]);

  const toggle = useCallback(() => {
    if (isPaused) {
      play();
    } else {
      pause();
    }
  }, [isPaused, play, pause]);

  const controlsAPI: MotionControls = useMemo(() => ({
    play,
    pause,
    stop,
    restart,
    reverse,
    toggle,
  }), [play, pause, stop, restart, reverse, toggle]);

  const state: MotionState = useMemo(() => ({
    state: animationState,
    reducedMotion,
    isPlaying: animationState === 'animating' && !isPaused,
    isPaused,
  }), [animationState, reducedMotion, isPaused]);

  return {
    controls: controlState,
    variants: motionVariants,
    transition: motionTransition,
    state,
    controlsAPI,
  };
}

/**
 * Preset motion configurations
 *
 * Common motion patterns ready to use with useMotion hook.
 *
 * @example
 * ```tsx
 * import { motionPresets, useMotion } from '@/hooks/useMotion';
 *
 * function MyComponent() {
 *   const motion = useMotion(motionPresets.fadeIn);
 *   return <motion.div {...motion}>Content</motion.div>;
 * }
 * ```
 */
export const motionPresets = {
  /**
   * Fade in animation
   */
  fadeIn: {
    variant: 'fade' as const,
    autoStart: true,
  },

  /**
   * Fade in from bottom
   */
  fadeUp: {
    variant: 'fadeUp' as const,
    autoStart: true,
  },

  /**
   * Fade in from top
   */
  fadeDown: {
    variant: 'fadeDown' as const,
    autoStart: true,
  },

  /**
   * Fade in from left
   */
  fadeLeft: {
    variant: 'fadeLeft' as const,
    autoStart: true,
  },

  /**
   * Fade in from right
   */
  fadeRight: {
    variant: 'fadeRight' as const,
    autoStart: true,
  },

  /**
   * Scale in animation
   */
  scaleIn: {
    variant: 'scaleIn' as const,
    autoStart: true,
  },

  /**
   * Slide from left
   */
  slideLeft: {
    variant: 'slideLeft' as const,
    autoStart: true,
  },

  /**
   * Slide from right
   */
  slideRight: {
    variant: 'slideRight' as const,
    autoStart: true,
  },

  /**
   * Slide from top
   */
  slideUp: {
    variant: 'slideUp' as const,
    autoStart: true,
  },

  /**
   * Slide from bottom
   */
  slideDown: {
    variant: 'slideDown' as const,
    autoStart: true,
  },

  /**
   * Blur in animation
   */
  blurIn: {
    variant: 'blurIn' as const,
    autoStart: true,
  },

  /**
   * Fast animation preset
   */
  fast: {
    variant: 'fade' as const,
    transition: 'fast' as const,
    autoStart: true,
  },

  /**
   * Slow animation preset
   */
  slow: {
    variant: 'fadeUp' as const,
    transition: 'slow' as const,
    autoStart: true,
  },

  /**
   * Spring animation preset
   */
  spring: {
    variant: 'scaleIn' as const,
    transition: 'spring' as const,
    autoStart: true,
  },
} as const;

/**
 * Hook for managing animation variants with custom states
 *
 * Simplified hook that focuses on variant management
 * without full animation controls.
 *
 * @param initialState - Initial animation state
 * @returns Current state and state setter
 *
 * @example
 * ```tsx
 * function Modal() {
 *   const [isOpen, setIsOpen] = useState(false);
 *   const { state, setState } = useAnimationState('hidden');
 *
 *   useEffect(() => {
 *     setState(isOpen ? 'visible' : 'hidden');
 *   }, [isOpen, setState]);
 *
 *   return (
 *     <motion.div
 *       initial="hidden"
 *       animate={state}
 *       variants={getVariants('fadeUp')}
 *     >
 *       Modal content
 *     </motion.div>
 *   );
 * }
 * ```
 */
export function useAnimationState(
  initialState: 'hidden' | 'visible' | 'exit' = 'hidden'
): {
  state: 'hidden' | 'visible' | 'exit';
  setState: (state: 'hidden' | 'visible' | 'exit') => void;
  toggle: () => void;
} {
  const [state, setState] = useState<'hidden' | 'visible' | 'exit'>(initialState);

  const toggle = useCallback(() => {
    setState(prev => prev === 'hidden' ? 'visible' : 'hidden');
  }, []);

  return { state, setState, toggle };
}

export default useMotion;
