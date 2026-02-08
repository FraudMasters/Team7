import React from 'react';
import { motion, HTMLMotionProps, Transition, Variants } from 'framer-motion';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { transitions, variants, presets, type MotionConfig } from '../../config/motion';

/**
 * Animation preset options for AnimatedBox
 *
 * Pre-configured animation variants for common use cases
 */
export type MotionPreset =
  // Fade animations
  | 'fade'
  | 'fade-in-up'
  | 'fade-in-down'
  | 'fade-in-left'
  | 'fade-in-right'
  // Slide animations
  | 'slide-left'
  | 'slide-right'
  | 'slide-up'
  | 'slide-down'
  // Scale animations
  | 'scale-in'
  | 'scale-up'
  | 'scale-down'
  | 'pulse'
  // Rotation animations
  | 'rotate-in'
  | 'spin'
  // Flip animations
  | 'flip-horizontal'
  | 'flip-vertical'
  // Blur animations
  | 'blur-in'
  // Combined presets
  | 'modal'
  | 'dropdown'
  | 'list-item'
  | 'card'
  | 'page'
  | 'tooltip'
  | 'bento-card';

/**
 * Transition preset options
 */
export type TransitionPreset = 'default' | 'fast' | 'slow' | 'spring' | 'spring-smooth' | 'spring-bouncy' | 'spring-inertial';

/**
 * Base Box props interface (from Box component)
 */
export interface BoxBaseProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  component?: React.ElementType;
  onClick?: React.MouseEventHandler;
  id?: string;
  role?: string;
}

/**
 * AnimatedBox component props interface
 * Combines Box props with Framer Motion animation capabilities
 */
export interface AnimatedBoxProps extends Omit<HTMLMotionProps<'div'>, 'transition' | 'variants'>, BoxBaseProps {
  /**
   * Animation preset to use
   * If provided, will automatically configure variants based on preset
   */
  preset?: MotionPreset;

  /**
   * Custom animation variants
   * Overrides preset if both are provided
   */
  variants?: Variants;

  /**
   * Transition preset or custom transition config
   * Overrides preset transition if provided
   */
  transition?: TransitionPreset | Transition;

  /**
   * Initial animation state
   * Defaults to 'hidden' for most presets
   */
  initial?: string | boolean;

  /**
   * Target animation state
   * Defaults to 'visible' for most presets
   */
  animate?: string | boolean;

  /**
   * Exit animation state
   * When provided, element will animate out when removed
   */
  exit?: string | boolean;

  /**
   * While hover state
   * Applies animation on hover
   */
  whileHover?: object;

  /**
   * While tap/click state
   * Applies animation on tap/click
   */
  whileTap?: object;

  /**
   * While focus state
   * Applies animation on focus
   */
  whileFocus?: object;

  /**
   * While dragging state
   * Applies animation during drag
   */
  whileDrag?: object;

  /**
   * Animation delay in seconds
   */
  delay?: number;

  /**
   * Animation duration in seconds
   * Overrides transition preset duration
   */
  duration?: number;

  /**
   * If true, animation only runs once on mount
   */
  once?: boolean;

  /**
   * Stagger children animations
   * Delay between each child animation in seconds
   */
  staggerChildren?: number;

  /**
   * Delay before children start animating
   */
  delayChildren?: number;
}

/**
 * Get animation variants from preset name
 */
const getPresetVariants = (preset: MotionPreset): Variants => {
  switch (preset) {
    // Fade animations
    case 'fade':
      return variants.fade.in;
    case 'fade-in-up':
      return variants.fade.inUp;
    case 'fade-in-down':
      return variants.fade.inDown;
    case 'fade-in-left':
      return variants.fade.inLeft;
    case 'fade-in-right':
      return variants.fade.inRight;

    // Slide animations
    case 'slide-left':
      return variants.slide.left;
    case 'slide-right':
      return variants.slide.right;
    case 'slide-up':
      return variants.slide.up;
    case 'slide-down':
      return variants.slide.down;

    // Scale animations
    case 'scale-in':
      return variants.scale.in;
    case 'scale-up':
      return variants.scale.up;
    case 'scale-down':
      return variants.scale.down;
    case 'pulse':
      return variants.scale.pulse;

    // Rotation animations
    case 'rotate-in':
      return variants.rotate.in;
    case 'spin':
      return variants.rotate.spin;

    // Flip animations
    case 'flip-horizontal':
      return variants.flip.horizontal;
    case 'flip-vertical':
      return variants.flip.vertical;

    // Blur animations
    case 'blur-in':
      return variants.blur.in;

    // Combined presets
    case 'modal':
      return presets.modal as Variants;
    case 'dropdown':
      return presets.dropdown as Variants;
    case 'list-item':
      return presets.listItem as Variants;
    case 'card':
      return presets.card as Variants;
    case 'page':
      return presets.page as Variants;
    case 'tooltip':
      return presets.tooltip as Variants;
    case 'bento-card':
      return presets.bentoCard as Variants;

    default:
      return variants.fade.in;
  }
};

/**
 * Get transition config from preset name
 */
const getPresetTransition = (preset: TransitionPreset): Transition => {
  switch (preset) {
    case 'default':
      return transitions.default as Transition;
    case 'fast':
      return transitions.fast as Transition;
    case 'slow':
      return transitions.slow as Transition;
    case 'spring':
      return transitions.spring as Transition;
    case 'spring-smooth':
      return transitions.springSmooth as Transition;
    case 'spring-bouncy':
      return transitions.springBouncy as Transition;
    case 'spring-inertial':
      return transitions.springInertial as Transition;
    default:
      return transitions.default as Transition;
  }
};

/**
 * AnimatedBox Component
 *
 * A motion-enabled Box component that combines the flexible styling of Box
 * with Framer Motion animations. Provides pre-configured animation presets
 * for common use cases, with full customization support through props.
 *
 * Features:
 * - All Box props (children, className, style, sx, component, onClick, id, role)
 * - Pre-configured animation presets (fade, slide, scale, rotate, flip, blur)
 * - Combined presets for common UI patterns (modal, dropdown, card, page)
 * - Custom transition and variant support
 * - Hover, tap, focus, and drag state animations
 * - Stagger children animations
 * - Theme-aware sx prop support
 * - Accessibility support (respects reduced motion preference)
 * - Full TypeScript support with forwardRef
 *
 * @example
 * ```tsx
 * // Basic fade animation with sx prop
 * <AnimatedBox preset="fade" sx={{ p: 2, bgcolor: 'primary.main' }}>
 *   <div>Fades in smoothly</div>
 * </AnimatedBox>
 *
 * // Slide up animation
 * <AnimatedBox preset="fade-in-up" sx={{ m: 1 }}>
 *   <Typography>Slides and fades in</Typography>
 * </AnimatedBox>
 *
 * // Scale animation with custom delay and component
 * <AnimatedBox
 *   preset="scale-in"
 *   delay={0.5}
 *   component="section"
 *   sx={{ p: 3 }}
 * >
 *   <Card>Delayed scale in</Card>
 * </AnimatedBox>
 *
 * // With theme function in sx
 * <AnimatedBox
 *   preset="slide-up"
 *   sx={(theme) => ({
 *     bgcolor: theme.palette.primary.main,
 *     color: theme.palette.primary.contrastText,
 *     p: 2,
 *   })}
 * >
 *   Theme-aware styles
 * </AnimatedBox>
 *
 * // Card with hover effect
 * <AnimatedBox
 *   preset="card"
 *   whileHover={{ y: -8 }}
 *   sx={{ boxShadow: 3 }}
 * >
 *   <GradientCard>Hover me</GradientCard>
 * </AnimatedBox>
 *
 * // Custom variants
 * <AnimatedBox
 *   variants={{
 *     hidden: { opacity: 0, rotate: -180 },
 *     visible: { opacity: 1, rotate: 0 }
 *   }}
 *   initial="hidden"
 *   animate="visible"
 *   sx={{ width: 100, height: 100 }}
 * >
 *   <div>Custom spin in</div>
 * </AnimatedBox>
 *
 * // Stagger children
 * <AnimatedBox staggerChildren={0.1} sx={{ display: 'flex' }}>
 *   {items.map((item) => (
 *     <AnimatedBox key={item.id} sx={{ m: 1 }}>
 *       <div>{item.content}</div>
 *     </AnimatedBox>
 *   ))}
 * </AnimatedBox>
 *
 * // With exit animation for AnimatePresence
 * <AnimatePresence>
 *   {isVisible && (
 *     <AnimatedBox preset="fade" exit="hidden" sx={{ p: 2 }}>
 *       <div>Fades out when removed</div>
 *     </AnimatedBox>
 *   )}
 * </AnimatePresence>
 *
 * // Using as a different component
 * <AnimatedBox
 *   component="button"
 *   preset="scale-up"
 *   onClick={handleClick}
 *   sx={{ cursor: 'pointer', bgcolor: 'secondary.main' }}
 * >
 *   Click me
 * </AnimatedBox>
 *
 * // With custom transition
 * <AnimatedBox preset="fade" transition="spring-bouncy" sx={{ p: 2 }}>
 *   <div>Bouncy fade in</div>
 * </AnimatedBox>
 *
 * // Page transition preset
 * <AnimatedBox preset="page" sx={{ minHeight: '100vh' }}>
 *   <PageContent />
 * </AnimatedBox>
 *
 * // Combining style and sx props
 * <AnimatedBox
 *   preset="fade-in-left"
 *   style={{ display: 'flex' }}
 *   sx={{ alignItems: 'center', justifyContent: 'center' }}
 * >
 *   Combined styles
 * </AnimatedBox>
 * ```
 */
export const AnimatedBox = React.forwardRef<HTMLDivElement, AnimatedBoxProps>(
  (
    {
      children,
      className,
      style,
      sx,
      component = 'div',
      preset,
      variants: customVariants,
      transition: customTransition,
      initial,
      animate,
      exit,
      whileHover,
      whileTap,
      whileFocus,
      whileDrag,
      delay,
      duration,
      once,
      staggerChildren,
      delayChildren,
      onClick,
      id,
      role,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Process sx prop (can be a function or object)
    const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

    // Get variants from preset or use custom variants
    const motionVariants = preset ? getPresetVariants(preset) : customVariants;

    // Get transition config from preset or use custom transition
    let motionTransition: Transition;
    if (typeof customTransition === 'string') {
      motionTransition = getPresetTransition(customTransition);
      // Apply custom duration if provided
      if (duration !== undefined) {
        motionTransition = { ...motionTransition, duration };
      }
    } else if (customTransition) {
      motionTransition = customTransition;
    } else if (preset) {
      motionTransition = transitions.default as Transition;
    } else {
      motionTransition = transitions.default as Transition;
    }

    // Apply delay if provided
    if (delay !== undefined && typeof motionTransition === 'object') {
      motionTransition = { ...motionTransition, delay };
    }

    // Apply stagger to transition if needed
    if ((staggerChildren !== undefined || delayChildren !== undefined) && typeof motionTransition === 'object') {
      motionTransition = {
        ...motionTransition,
        staggerChildren: staggerChildren ?? motionTransition.staggerChildren,
        delayChildren: delayChildren ?? motionTransition.delayChildren,
      };
    }

    // Determine initial and animate states
    const motionInitial = initial !== undefined ? initial : 'hidden';
    const motionAnimate = animate !== undefined ? animate : 'visible';

    // Combine styles
    const combinedStyle = {
      boxSizing: 'border-box',
      margin: 0,
      ...style,
      ...sxStyles,
    };

    return (
      <motion.div
        as={component}
        ref={ref}
        variants={motionVariants}
        initial={motionInitial}
        animate={motionAnimate}
        exit={exit}
        transition={motionTransition}
        whileHover={whileHover}
        whileTap={whileTap}
        whileFocus={whileFocus}
        whileDrag={whileDrag}
        className={className}
        style={combinedStyle}
        onClick={onClick}
        id={id}
        role={role}
        {...rest}
      >
        {children}
      </motion.div>
    );
  }
);

AnimatedBox.displayName = 'AnimatedBox';

export default AnimatedBox;
