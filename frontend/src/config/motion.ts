/**
 * Motion Configuration
 *
 * Centralized Framer Motion configuration for the application.
 * Provides pre-defined animation variants, transitions, and presets
 * for consistent motion design across the 2026 design system.
 *
 * @module config/motion
 * @example
 * ```tsx
 * import { motion } from 'framer-motion';
 * import { variants, transitions } from '@/config/motion';
 *
 * <motion.div
 *   initial="hidden"
 *   animate="visible"
 *   exit="hidden"
 *   variants={variants.fade.in}
 *   transition={transitions.default}
 * >
 *   Content with animation
 * </motion.div>
 * ```
 */

/**
 * Default transition configuration
 *
 * Standard transition values for consistent animation timing
 * and easing across all motion components.
 */
export const transitions = {
  /**
   * Default transition for most animations
   * Balanced timing for smooth, responsive feel
   */
  default: {
    type: 'tween' as const,
    duration: 0.3,
    ease: [0.4, 0, 0.2, 1] as const, // cubic-bezier(0.4, 0, 0.2, 1)
  },

  /**
   * Fast transition for micro-interactions
   * Quick feedback for hover, focus, tap states
   */
  fast: {
    type: 'tween' as const,
    duration: 0.15,
    ease: [0.4, 0, 0.2, 1] as const,
  },

  /**
   * Slow transition for dramatic animations
   * Used for page transitions and major state changes
   */
  slow: {
    type: 'tween' as const,
    duration: 0.5,
    ease: [0.4, 0, 0.2, 1] as const,
  },

  /**
   * Spring transition for natural movement
   * Physics-based animation with bounce effect
   */
  spring: {
    type: 'spring' as const,
    stiffness: 300,
    damping: 25,
  },

  /**
   * Smooth spring for gentle movements
   * Less bounce, more smooth settling
   */
  springSmooth: {
    type: 'spring' as const,
    stiffness: 150,
    damping: 20,
  },

  /**
   * Bouncy spring for playful interactions
   * More pronounced bounce effect
   */
  springBouncy: {
    type: 'spring' as const,
    stiffness: 400,
    damping: 15,
  },

  /**
   * Inertial spring for drag gestures
   * Natural momentum feel
   */
  springInertial: {
    type: 'spring' as const,
    stiffness: 200,
    damping: 30,
    mass: 1,
  },
} as const;

/**
 * Fade animation variants
 *
 * Opacity-based animations for smooth appearance/disappearance
 */
export const variants = {
  /**
   * Fade animations
   */
  fade: {
    /**
     * Simple fade in/out
     */
    in: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
    },

    /**
     * Fade in from top
     */
    inUp: {
      hidden: { opacity: 0, y: -20 },
      visible: { opacity: 1, y: 0 },
    },

    /**
     * Fade in from bottom
     */
    inDown: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    },

    /**
     * Fade in from left
     */
    inLeft: {
      hidden: { opacity: 0, x: -20 },
      visible: { opacity: 1, x: 0 },
    },

    /**
     * Fade in from right
     */
    inRight: {
      hidden: { opacity: 0, x: 20 },
      visible: { opacity: 1, x: 0 },
    },
  },

  /**
   * Slide animations
   */
  slide: {
    /**
     * Slide from left
     */
    left: {
      hidden: { x: '-100%' },
      visible: { x: 0 },
    },

    /**
     * Slide from right
     */
    right: {
      hidden: { x: '100%' },
      visible: { x: 0 },
    },

    /**
     * Slide from top
     */
    up: {
      hidden: { y: '-100%' },
      visible: { y: 0 },
    },

    /**
     * Slide from bottom
     */
    down: {
      hidden: { y: '100%' },
      visible: { y: 0 },
    },
  },

  /**
   * Scale/Zoom animations
   */
  scale: {
    /**
     * Simple scale in
     */
    in: {
      hidden: { opacity: 0, scale: 0.9 },
      visible: { opacity: 1, scale: 1 },
    },

    /**
     * Scale up from smaller
     */
    up: {
      hidden: { opacity: 0, scale: 0.5 },
      visible: { opacity: 1, scale: 1 },
    },

    /**
     * Scale down from larger
     */
    down: {
      hidden: { opacity: 0, scale: 1.1 },
      visible: { opacity: 1, scale: 1 },
    },

    /**
     * Pulse effect (scale up and down)
     */
    pulse: {
      hidden: { scale: 1 },
      visible: {
        scale: [1, 1.05, 1],
        transition: {
          duration: 0.5,
          times: [0, 0.5, 1],
        },
      },
    },
  },

  /**
   * Rotation animations
   */
  rotate: {
    /**
     * Rotate in
     */
    in: {
      hidden: { opacity: 0, rotate: -10 },
      visible: { opacity: 1, rotate: 0 },
    },

    /**
     * Spin effect
     */
    spin: {
      hidden: { rotate: 0 },
      visible: {
        rotate: 360,
        transition: {
          duration: 1,
          ease: 'linear',
          repeat: Number.POSITIVE_INFINITY,
        },
      },
    },
  },

  /**
   * Flip animations
   */
  flip: {
    /**
     * Flip horizontal
     */
    horizontal: {
      hidden: { rotateY: 90 },
      visible: { rotateY: 0 },
    },

    /**
     * Flip vertical
     */
    vertical: {
      hidden: { rotateX: 90 },
      visible: { rotateX: 0 },
    },
  },

  /**
   * Blur animations
   */
  blur: {
    /**
     * Blur in
     */
    in: {
      hidden: { opacity: 0, filter: 'blur(10px)' },
      visible: { opacity: 1, filter: 'blur(0px)' },
    },
  },
} as const;

/**
 * Stagger animation configuration
 *
 * Controls timing for animating child elements in sequence
 */
export const stagger = {
  /**
   * Default stagger delay between children
   */
  default: 0.1,

  /**
   * Fast stagger for quick sequences
   */
  fast: 0.05,

  /**
   * Slow stagger for dramatic sequences
   */
  slow: 0.2,

  /**
   * Stagger container variants
   */
  container: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  },

  /**
   * Stagger item variants
   */
  item: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  },
} as const;

/**
 * Hover state animations
 *
 * Micro-interactions for hover/focus states
 */
export const hover = {
  /**
   * Scale on hover
   */
  scale: {
    scale: 1.05,
    transition: transitions.fast,
  },

  /**
   * Lift up on hover
   */
  lift: {
    y: -4,
    transition: transitions.fast,
  },

  /**
   * Glow effect on hover
   */
  glow: {
    boxShadow: '0 0 20px rgba(25, 118, 210, 0.4)',
    transition: transitions.fast,
  },

  /**
   * Brighten on hover
   */
  brighten: {
    filter: 'brightness(1.1)',
    transition: transitions.fast,
  },

  /**
   * Scale and lift on hover
   */
  scaleAndLift: {
    scale: 1.02,
    y: -2,
    transition: transitions.fast,
  },
} as const;

/**
 * Tap/click state animations
 *
 * Micro-interactions for active/tap states
 */
export const tap = {
  /**
   * Scale down on tap
   */
  scale: {
    scale: 0.95,
    transition: {
      type: 'spring' as const,
      stiffness: 400,
      damping: 17,
    },
  },

  /**
   * Shrink on tap
   */
  shrink: {
    scale: 0.98,
    transition: transitions.fast,
  },
} as const;

/**
 * Drag gesture configuration
 *
 * Settings for draggable components
 */
export const drag = {
  /**
   * Default drag constraints
   */
  default: {
    bounce: 0.2,
    bounceStiffness: 300,
    damping: 20,
  },

  /**
   * Free drag (no constraints)
   */
  free: {
    drag: true,
    dragConstraints: { left: 0, right: 0, top: 0, bottom: 0 },
    dragElastic: 0.1,
  },

  /**
   * Elastic drag
   */
  elastic: {
    drag: true,
    dragElastic: 0.5,
    dragTransition: {
      type: 'spring' as const,
      stiffness: 200,
      damping: 20,
    },
  },

  /**
   * Snap drag (snaps to position)
   */
  snap: {
    drag: true,
    dragConstraints: { left: 0, right: 0, top: 0, bottom: 0 },
    dragElastic: 0,
    whileDrag: { scale: 1.05, cursor: 'grabbing' },
  },
} as const;

/**
 * Layout animation configuration
 *
 * Automatic animations for layout changes
 */
export const layout = {
  /**
   * Default layout animation
   */
  default: {
    type: 'spring' as const,
    stiffness: 350,
    damping: 25,
  },

  /**
   * Smooth layout animation
   */
  smooth: {
    type: 'spring' as const,
    stiffness: 200,
    damping: 30,
  },

  /**
   * Quick layout animation
   */
  quick: {
    type: 'tween' as const,
    duration: 0.2,
    ease: [0.4, 0, 0.2, 1] as const,
  },
} as const;

/**
 * Preset variant combinations
 *
 * Pre-configured variant sets for common use cases
 */
export const presets = {
  /**
   * Modal animation preset
   */
  modal: {
    hidden: { opacity: 0, scale: 0.9, y: 20 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 25,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.9,
      y: 20,
      transition: { duration: 0.2 },
    },
  },

  /**
   * Dropdown animation preset
   */
  dropdown: {
    hidden: { opacity: 0, y: -10, height: 0 },
    visible: {
      opacity: 1,
      y: 0,
      height: 'auto',
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 30,
      },
    },
    exit: {
      opacity: 0,
      y: -10,
      height: 0,
      transition: { duration: 0.15 },
    },
  },

  /**
   * List item animation preset
   */
  listItem: {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 24,
      },
    },
    exit: {
      opacity: 0,
      x: 20,
      transition: { duration: 0.2 },
    },
  },

  /**
   * Card animation preset
   */
  card: {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 250,
        damping: 25,
      },
    },
    hover: {
      y: -4,
      scale: 1.02,
      transition: transitions.fast,
    },
    tap: {
      scale: 0.98,
      transition: transitions.fast,
    },
  },

  /**
   * Page transition preset
   */
  page: {
    initial: { opacity: 0, y: 20 },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring' as const,
        stiffness: 200,
        damping: 25,
        delay: 0.1,
      },
    },
    exit: {
      opacity: 0,
      y: -20,
      transition: { duration: 0.2 },
    },
  },

  /**
   * Tooltip animation preset
   */
  tooltip: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 500,
        damping: 30,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.8,
      transition: { duration: 0.1 },
    },
  },

  /**
   * Bento grid card animation preset
   */
  bentoCard: {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 200,
        damping: 20,
      },
    },
    hover: {
      scale: 1.02,
      transition: transitions.fast,
    },
  },
} as const;

/**
 * Gesture handler configuration
 *
 * Default settings for gesture events
 */
export const gestures = {
  /**
   * Hover gesture config
   */
  hover: {
    whileHover: hover.scaleAndLift,
  },

  /**
   * Tap gesture config
   */
  tap: {
    whileTap: tap.scale,
  },

  /**
   * Focus gesture config
   */
  focus: {
    whileFocus: {
      scale: 1.02,
      transition: transitions.fast,
    },
  },

  /**
   * Drag gesture config
   */
  drag: {
    whileDrag: { cursor: 'grabbing', scale: 1.02 },
  },
} as const;

/**
 * Create custom fade variant
 *
 * Helper function to create fade variants with custom direction
 *
 * @param direction - Direction of fade animation
 * @param distance - Distance in pixels to move
 * @returns Custom fade variant object
 *
 * @example
 * ```ts
 * const customFade = createFadeVariant('up', 30);
 * // { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }
 * ```
 */
export function createFadeVariant(
  direction: 'up' | 'down' | 'left' | 'right' | 'none',
  distance: number = 20
) {
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
      break;
  }

  return { hidden, visible };
}

/**
 * Create stagger variants
 *
 * Helper function to create stagger variants for container with custom delay
 *
 * @param staggerDelay - Delay between each child animation
 * @param initialDelay - Delay before first child starts
 * @returns Custom stagger variants
 *
 * @example
 * ```ts
 * const staggerVariants = createStaggerVariants(0.15, 0.2);
 * ```
 */
export function createStaggerVariants(staggerDelay: number = 0.1, initialDelay: number = 0) {
  return {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: staggerDelay,
          delayChildren: initialDelay,
        },
      },
    },
    item: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    },
  };
}

/**
 * Motion presets export
 *
 * All motion configuration values combined for easy import
 */
export const motionConfig = {
  transitions,
  variants,
  stagger,
  hover,
  tap,
  drag,
  layout,
  presets,
  gestures,
} as const;

/**
 * Default export
 */
export default motionConfig;
