import React from 'react';
import { AnimatePresence, motion, HTMLMotionProps, Transition, Variants } from 'framer-motion';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { transitions, variants, presets } from '../../config/motion';

/**
 * Transition direction options
 *
 * Determines the direction of the page transition animation
 */
export type TransitionDirection = 'up' | 'down' | 'left' | 'right' | 'none';

/**
 * Transition type options
 *
 * Pre-configured transition types for common page transition patterns
 */
export type TransitionType =
  | 'fade' // Simple fade in/out
  | 'slide' // Slide in/out with direction
  | 'scale' // Scale in/out with fade
  | 'flip' // Flip animation
  | 'blur' // Blur and fade
  | 'page'; // Combined page transition (slide + fade)

/**
 * Transition speed options
 */
export type TransitionSpeed = 'instant' | 'fast' | 'normal' | 'slow';

/**
 * Base container props interface
 */
export interface ContainerBaseProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  id?: string;
}

/**
 * TransitionContainer component props interface
 *
 * Combines container props with Framer Motion animation capabilities
 */
export interface TransitionContainerProps extends Omit<HTMLMotionProps<'div'>, 'transition' | 'variants'>, ContainerBaseProps {
  /**
   * Animation state for controlling when content is visible
   * When false, content will animate out if exit animation is provided
   */
  isVisible?: boolean;

  /**
   * Transition type to use
   * If provided, will automatically configure variants based on type
   */
  type?: TransitionType;

  /**
   * Direction for slide/transition animations
   * Only applies to 'slide' and 'page' types
   */
  direction?: TransitionDirection;

  /**
   * Custom animation variants
   * Overrides type if both are provided
   */
  variants?: Variants;

  /**
   * Custom transition config
   * Overrides type transition if provided
   */
  transition?: Transition;

  /**
   * Transition speed preset
   */
  speed?: TransitionSpeed;

  /**
   * Animation delay in seconds
   */
  delay?: number;

  /**
   * Animation duration in seconds
   * Overrides speed preset duration
   */
  duration?: number;

  /**
   * Initial animation state
   * Defaults to 'hidden' for most types
   */
  initial?: string | boolean;

  /**
   * Target animation state
   * Defaults to 'visible' for most types
   */
  animate?: string | boolean;

  /**
   * Exit animation state
   * When provided, element will animate out when removed
   */
  exit?: string | boolean;

  /**
   * CSS class name
   */
  className?: string;

  /**
   * Additional inline styles
   */
  style?: React.CSSProperties;

  /**
   * Theme-aware styles
   */
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);

  /**
   * Container element ID
   */
  id?: string;

  /**
   * If true, enables AnimatePresence wrapper for enter/exit animations
   * This is useful for routing transitions where components mount/unmount
   */
  enablePresence?: boolean;

  /**
   * Container mode
   * - 'full': Full viewport width and height
   * - 'width': Full viewport width, auto height
   * - 'height': Full viewport height, auto width
   * - 'auto': Auto width and height (default)
   */
  mode?: 'full' | 'width' | 'height' | 'auto';
}

/**
 * Get transition duration from speed preset
 */
const getSpeedDuration = (speed: TransitionSpeed): number => {
  switch (speed) {
    case 'instant':
      return 0.1;
    case 'fast':
      return 0.2;
    case 'normal':
      return 0.3;
    case 'slow':
      return 0.5;
    default:
      return 0.3;
  }
};

/**
 * Get animation variants from type and direction
 */
const getTypeVariants = (type: TransitionType, direction: TransitionDirection): Variants => {
  const dirOffset = 30;

  switch (type) {
    case 'fade':
      return variants.fade.in;

    case 'slide':
      switch (direction) {
        case 'up':
          return variants.slide.up;
        case 'down':
          return variants.slide.down;
        case 'left':
          return variants.slide.left;
        case 'right':
          return variants.slide.right;
        default:
          return variants.fade.in;
      }

    case 'scale':
      return variants.scale.in;

    case 'flip':
      return variants.flip.horizontal;

    case 'blur':
      return variants.blur.in;

    case 'page':
      // Page transition combines slide and fade
      return {
        hidden: {
          opacity: 0,
          x: direction === 'left' ? dirOffset : direction === 'right' ? -dirOffset : 0,
          y: direction === 'up' ? dirOffset : direction === 'down' ? -dirOffset : 0,
        },
        visible: {
          opacity: 1,
          x: 0,
          y: 0,
          transition: {
            duration: 0.3,
            ease: [0.4, 0, 0.2, 1],
          },
        },
        exit: {
          opacity: 0,
          x: direction === 'left' ? -dirOffset : direction === 'right' ? dirOffset : 0,
          y: direction === 'up' ? -dirOffset : direction === 'down' ? dirOffset : 0,
          transition: {
            duration: 0.2,
            ease: [0.4, 0, 1, 1],
          },
        },
      };

    default:
      return variants.fade.in;
  }
};

/**
 * Get container styles based on mode
 */
const getContainerStyles = (mode: 'full' | 'width' | 'height' | 'auto'): React.CSSProperties => {
  switch (mode) {
    case 'full':
      return {
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
      };
    case 'width':
      return {
        width: '100%',
      };
    case 'height':
      return {
        height: '100vh',
        overflow: 'hidden',
      };
    case 'auto':
    default:
      return {};
  }
};

/**
 * TransitionContainer Component
 *
 * A specialized container component for page and section transitions using Framer Motion.
 * Provides pre-configured transition types with smooth enter/exit animations.
 *
 * Features:
 * - Pre-configured transition types (fade, slide, scale, flip, blur, page)
 * - Directional control for slide and page transitions
 * - AnimatePresence support for mount/unmount animations
 * - Container modes (full, width, height, auto)
 * - Theme-aware sx prop support
 * - Speed presets (instant, fast, normal, slow)
 * - Custom transition and variant support
 * - Full TypeScript support with forwardRef
 *
 * @example
 * ```tsx
 * // Basic fade transition
 * <TransitionContainer type="fade">
 *   <div>Page content</div>
 * </TransitionContainer>
 *
 * // Slide transition with direction
 * <TransitionContainer type="slide" direction="up">
 *   <Typography>Slides up from bottom</Typography>
 * </TransitionContainer>
 *
 * // Page transition with AnimatePresence
 * <AnimatePresence mode="wait">
 *   {currentPath === '/about' && (
 *     <TransitionContainer
 *       key="about"
 *       type="page"
 *       direction="left"
 *       enablePresence
 *     >
 *       <AboutPage />
 *     </TransitionContainer>
 *   )}
 * </AnimatePresence>
 *
 * // Full viewport container
 * <TransitionContainer type="scale" mode="full">
 *   <FullPageContent />
 * </TransitionContainer>
 *
 * // With custom duration and delay
 * <TransitionContainer
 *   type="fade"
 *   duration={0.5}
 *   delay={0.2}
 *   sx={{ p: 2 }}
 * >
 *   <div>Delayed fade in</div>
 * </TransitionContainer>
 *
 * // Custom variants
 * <TransitionContainer
 *   variants={{
 *     hidden: { opacity: 0, scale: 0.8, rotate: -10 },
 *     visible: { opacity: 1, scale: 1, rotate: 0 }
 *   }}
 *   initial="hidden"
 *   animate="visible"
 * >
 *   <div>Custom scale and rotate</div>
 * </TransitionContainer>
 *
 * // With exit animation
 * <TransitionContainer
 *   type="blur"
 *   exit="hidden"
 *   sx={{ minHeight: 200 }}
 * >
 *   <div>Blurs out on unmount</div>
 * </TransitionContainer>
 *
 * // Speed preset
 * <TransitionContainer type="slide" direction="right" speed="fast">
 *   <div>Fast slide transition</div>
 * </TransitionContainer>
 *
 * // Theme-aware styles
 * <TransitionContainer
 *   type="fade"
 *   sx={(theme) => ({
 *     bgcolor: theme.palette.background.paper,
 *     p: 3,
 *   })}
 * >
 *   <div>Themed container</div>
 * </TransitionContainer>
 *
 * // Conditional visibility
 * <TransitionContainer type="scale" isVisible={showContent}>
 *   <div>{showContent ? 'Visible' : 'Hidden'}</div>
 * </TransitionContainer>
 * ```
 */
export const TransitionContainer = React.forwardRef<HTMLDivElement, TransitionContainerProps>(
  (
    {
      children,
      isVisible = true,
      type = 'fade',
      direction = 'up',
      variants: customVariants,
      transition: customTransition,
      speed = 'normal',
      delay,
      duration,
      initial,
      animate,
      exit,
      className,
      style,
      sx,
      id,
      enablePresence = false,
      mode = 'auto',
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Process sx prop (can be a function or object)
    const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

    // Get variants from type or use custom variants
    const motionVariants = type ? getTypeVariants(type, direction) : customVariants;

    // Get transition config
    let motionTransition: Transition;
    if (customTransition) {
      motionTransition = customTransition;
    } else {
      const baseDuration = duration !== undefined ? duration : getSpeedDuration(speed);
      motionTransition = {
        duration: baseDuration,
        delay: delay ?? 0,
        ease: [0.4, 0, 0.2, 1],
      };
    }

    // Determine initial and animate states
    const motionInitial = initial !== undefined ? initial : 'hidden';
    const motionAnimate = animate !== undefined ? animate : (isVisible ? 'visible' : 'hidden');

    // Get container styles based on mode
    const containerStyles = getContainerStyles(mode);

    // Combine all styles
    const combinedStyle = {
      boxSizing: 'border-box',
      margin: 0,
      ...containerStyles,
      ...style,
      ...sxStyles,
    };

    // Motion element to render
    const motionElement = (
      <motion.div
        ref={ref}
        variants={motionVariants}
        initial={motionInitial}
        animate={motionAnimate}
        exit={exit}
        transition={motionTransition}
        className={className}
        style={combinedStyle}
        id={id}
        {...rest}
      >
        {children}
      </motion.div>
    );

    // Wrap with AnimatePresence if enabled
    if (enablePresence) {
      return (
        <AnimatePresence mode="wait" initial={false}>
          {isVisible && motionElement}
        </AnimatePresence>
      );
    }

    return motionElement;
  }
);

TransitionContainer.displayName = 'TransitionContainer';

// Default export
export default TransitionContainer;
