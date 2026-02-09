import React from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';
import Paper, { PaperProps } from '../ui/Paper';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Hover animation variant types
 */
export type HoverAnimationType =
  | 'scale'
  | 'lift'
  | 'glow'
  | 'border-glow'
  | 'shimmer'
  | 'none';

/**
 * HoverCard component props interface
 * Extends PaperProps with HoverCard-specific properties
 */
export interface HoverCardProps extends Omit<PaperProps, 'elevation'> {
  /**
   * Card content - can be a function (render prop) or React node
   * When using render prop, receives HoverCardContent interface
   */
  children?: React.ReactNode | ((props: HoverCardContentProps) => React.ReactNode);
  /**
   * Card actions - typically buttons or links at the bottom of the card
   */
  actions?: React.ReactNode;
  /**
   * Type of hover animation to apply
   * - scale: Card scales up slightly on hover
   * - lift: Card lifts up with enhanced shadow
   * - glow: Card adds a glow effect on hover
   * - border-glow: Border glows with color on hover
   * - shimmer: Shimmer effect sweeps across the card
   * - none: No hover animation
   * @default 'lift'
   */
  hoverAnimation?: HoverAnimationType;
  /**
   * Scale amount for scale animation (1.0 = no scale, 1.05 = 5% larger)
   * @default 1.02
   */
  hoverScale?: number;
  /**
   * Lift amount in pixels for lift animation
   * @default 4
   */
  hoverLift?: number;
  /**
   * Glow color for glow and border-glow animations
   * Can be a theme color key or CSS color value
   * @default 'primary.main'
   */
  glowColor?: string;
  /**
   * If true, card will be outlined instead of elevated
   */
  outlined?: boolean;
  /**
   * If true, card will have a border
   */
  bordered?: boolean;
  /**
   * Border color (when bordered or outlined)
   */
  borderColor?: string;
  /**
   * Custom padding for card content
   */
  padding?: string | number;
  /**
   * If true, removes default padding from card content
   */
  disablePadding?: boolean;
  /**
   * Animation duration in milliseconds
   * @default 300
   */
  animationDuration?: number;
  /**
   * Animation easing function
   * @default 'cubic-bezier(0.4, 0, 0.2, 1)'
   */
  animationEasing?: string;
}

/**
 * HoverCard content props interface (for render prop)
 */
export interface HoverCardContentProps {
  /** Hover state */
  hovered: boolean;
}

/**
 * HoverCard content area component
 */
const StyledHoverCardContent = styled('div')<{
  disablePadding?: boolean;
  padding?: string | number;
}>(
  {
    flex: '1 1 auto',
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Padding
    if (!props.disablePadding) {
      if (props.padding !== undefined) {
        styles.padding =
          typeof props.padding === 'number' ? `${props.padding}px` : props.padding;
      } else {
        styles.padding = theme.spacing.lg;
      }
    }

    return styles;
  }
);

/**
 * HoverCard actions component
 */
const StyledHoverCardActions = styled('div')(() => {
  const theme = useEmotionTheme().theme;
  return {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing.md,
    borderTop: `1px solid ${theme.divider}`,
    '&:empty': {
      display: 'none',
    },
  };
});

/**
 * Resolve color from theme or CSS value
 */
const resolveColor = (color: string, theme: EmotionTheme): string => {
  // Check if it's a theme color key (e.g., 'primary.main', 'text.primary')
  if (color.includes('.')) {
    const parts = color.split('.');
    let value: any = theme;
    for (const part of parts) {
      value = value?.[part];
    }
    return typeof value === 'string' ? value : color;
  }
  // Check if it's a theme root key
  if (theme[color as keyof EmotionTheme]) {
    return theme[color as keyof EmotionTheme] as string;
  }
  return color;
};

/**
 * Styled HoverCard base component
 */
const StyledHoverCard = styled(Paper)<
  HoverCardProps & { isHovering?: boolean }
>(
  {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    position: 'relative',
    cursor: 'pointer',
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Outlined style
    if (props.outlined || props.bordered) {
      styles.boxShadow = 'none';
      styles.border = `1px solid ${props.borderColor || theme.divider}`;
    }

    // Glow effect on hover
    if (props.isHovering && props.hoverAnimation === 'glow') {
      const color = resolveColor(props.glowColor || 'primary.main', theme);
      styles.boxShadow = `0 0 20px ${color}, 0 4px 12px rgba(0, 0, 0, 0.15)`;
    }

    // Border glow effect on hover
    if (props.isHovering && props.hoverAnimation === 'border-glow') {
      const color = resolveColor(props.glowColor || 'primary.main', theme);
      styles.boxShadow = `0 0 0 2px ${color}, 0 4px 12px rgba(0, 0, 0, 0.15)`;
    }

    // Shimmer effect overlay
    if (props.hoverAnimation === 'shimmer') {
      styles['&::before'] = {
        content: '""',
        position: 'absolute',
        top: 0,
        left: '-100%',
        width: '50%',
        height: '100%',
        background:
          'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
        transform: 'skewX(-20deg)',
        transition: 'left 0.5s',
        pointerEvents: 'none',
      };
      if (props.isHovering) {
        styles['&::before'].left = '150%';
      }
    }

    // If outlined, override elevation
    if (props.outlined) {
      styles.elevation = 0;
    }

    return styles;
  }
);

/**
 * Motion wrapper for hover animations
 */
const MotionWrapper = styled(motion.div)<{
  duration?: number;
  easing?: string;
}>((props) => ({
  width: '100%',
  height: '100%',
  transition: `all ${props.duration || 300}ms ${props.easing || 'cubic-bezier(0.4, 0, 0.2, 1)'}`,
}));

/**
 * HoverCard Component
 *
 * A card component with smooth hover scale and elevation animations.
 * Built on top of Paper with Framer Motion for fluid micro-interactions.
 *
 * Features:
 * - Multiple hover animation types (scale, lift, glow, border-glow, shimmer)
 * - Configurable animation duration and easing
 * - Outlined/bordered variants
 * - Flexible content area with optional padding
 * - Actions area at the bottom
 * - Render prop for advanced hover state control
 * - Fully accessible and themeable
 *
 * @example
 * ```tsx
 * // Basic hover card with default lift animation
 * <HoverCard>
 *   <Typography variant="h6">Hover Me</Typography>
 *   <Typography variant="body2">Watch me lift on hover</Typography>
 * </HoverCard>
 *
 * // Scale animation
 * <HoverCard hoverAnimation="scale" hoverScale={1.05}>
 *   <Typography variant="h6">Scale Effect</Typography>
 *   <Typography variant="body2">I grow larger on hover</Typography>
 * </HoverCard>
 *
 * // Glow effect
 * <HoverCard hoverAnimation="glow" glowColor="primary.main">
 *   <Typography variant="h6">Glow Effect</Typography>
 *   <Typography variant="body2">I glow on hover</Typography>
 * </HoverCard>
 *
 * // Border glow
 * <HoverCard hoverAnimation="border-glow" glowColor="success.main">
 *   <Typography variant="h6">Border Glow</Typography>
 *   <Typography variant="body2">My border glows on hover</Typography>
 * </HoverCard>
 *
 * // Shimmer effect
 * <HoverCard hoverAnimation="shimmer">
 *   <Typography variant="h6">Shimmer Effect</Typography>
 *   <Typography variant="body2">Watch the shimmer sweep</Typography>
 * </HoverCard>
 *
 * // With actions
 * <HoverCard
 *   hoverAnimation="lift"
 *   actions={
 *     <>
 *       <Button size="small">Learn More</Button>
 *       <Button size="small" color="primary">
 *         Action
 *       </Button>
 *     </>
 *   }
 * >
 *   <Typography variant="h6">Card with Actions</Typography>
 *   <Typography variant="body2">This card has action buttons</Typography>
 * </HoverCard>
 *
 * // Outlined variant
 * <HoverCard hoverAnimation="scale" outlined>
 *   <Typography variant="h6">Outlined HoverCard</Typography>
 *   <Typography variant="body2">Clean, outlined design</Typography>
 * </HoverCard>
 *
 * // Render prop for advanced control
 * <HoverCard hoverAnimation="lift">
 *   {({ hovered }) => (
 *     <>
 *       <Typography variant="h6">
 *         {hovered ? 'I'm hovered!' : 'Hover me'}
 *       </Typography>
 *       <Typography variant="body2">
 *         Status: {hovered ? 'active' : 'idle'}
 *       </Typography>
 *     </>
 *   )}
 * </HoverCard>
 *
 * // Custom animation timing
 * <HoverCard
 *   hoverAnimation="scale"
 *   hoverScale={1.08}
 *   animationDuration={400}
 *   animationEasing="cubic-bezier(0.34, 1.56, 0.64, 1)"
 * >
 *   <Typography variant="h6">Bouncy Scale</Typography>
 *   <Typography variant="body2">Custom easing for bouncy feel</Typography>
 * </HoverCard>
 *
 * // Square with custom padding
 * <HoverCard square padding={24} hoverAnimation="lift">
 *   <Typography variant="h6">Custom Styling</Typography>
 *   <Typography variant="body2">24px padding, no rounded corners</Typography>
 * </HoverCard>
 * ```
 */
const HoverCard = React.forwardRef<HTMLElement, HoverCardProps>(
  (
    {
      children,
      actions,
      hoverAnimation = 'lift',
      hoverScale = 1.02,
      hoverLift = 4,
      glowColor,
      outlined = false,
      bordered = false,
      borderColor,
      padding,
      disablePadding = false,
      animationDuration = 300,
      animationEasing = 'cubic-bezier(0.4, 0, 0.2, 1)',
      elevation,
      onClick,
      ...rest
    },
    ref
  ) => {
    const [isHovering, setIsHovering] = React.useState(false);

    // Default elevation for cards
    const cardElevation = elevation !== undefined ? elevation : outlined ? 0 : 2;

    // Motion variants for scale animation
    const scaleVariants = {
      rest: { scale: 1 },
      hover: { scale: hoverScale },
    };

    // Motion variants for lift animation
    const liftVariants = {
      rest: { y: 0 },
      hover: { y: -hoverLift },
    };

    // Get appropriate variants based on animation type
    const getVariants = () => {
      if (hoverAnimation === 'scale') {
        return scaleVariants;
      }
      if (hoverAnimation === 'lift') {
        return liftVariants;
      }
      return {
        rest: { scale: 1, y: 0 },
        hover: { scale: hoverScale, y: -hoverLift },
      };
    };

    // Animation props for Framer Motion
    const motionProps = {
      initial: 'rest',
      animate: isHovering ? 'hover' : 'rest',
      variants: getVariants(),
      transition: {
        duration: animationDuration / 1000,
        ease: animationEasing,
      },
      onHoverStart: () => setIsHovering(true),
      onHoverEnd: () => setIsHovering(false),
      onClick,
    };

    return (
      <MotionWrapper {...motionProps}>
        <StyledHoverCard
          ref={ref as any}
          elevation={cardElevation}
          hoverAnimation={hoverAnimation}
          hoverScale={hoverScale}
          hoverLift={hoverLift}
          glowColor={glowColor}
          outlined={outlined}
          bordered={bordered}
          borderColor={borderColor}
          isHovering={isHovering}
          {...rest}
          onClick={undefined} // Handle click in MotionWrapper
        >
          <StyledHoverCardContent disablePadding={disablePadding} padding={padding}>
            {typeof children === 'function'
              ? (children as (props: HoverCardContentProps) => React.ReactNode)({
                  hovered: isHovering,
                })
              : children}
          </StyledHoverCardContent>
          {actions && <StyledHoverCardActions>{actions}</StyledHoverCardActions>}
        </StyledHoverCard>
      </MotionWrapper>
    );
  }
);

HoverCard.displayName = 'HoverCard';

/**
 * HoverCardContent Component
 *
 * A convenience component for HoverCard content area.
 * Automatically applies padding unless disabled.
 *
 * @example
 * ```tsx
 * <HoverCard>
 *   <HoverCardContent>
 *     <Typography variant="h5">Card Title</Typography>
 *     <Typography variant="body2">Card content...</Typography>
 *   </HoverCardContent>
 *   <HoverCardActions>
 *     <Button size="small">Action</Button>
 *   </HoverCardActions>
 * </HoverCard>
 * ```
 */
export const HoverCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { disablePadding?: boolean }
>(({ children, disablePadding = false, ...rest }, ref) => {
  return (
    <StyledHoverCardContent ref={ref} disablePadding={disablePadding} {...rest}>
      {children}
    </StyledHoverCardContent>
  );
});

HoverCardContent.displayName = 'HoverCardContent';

/**
 * HoverCardActions Component
 *
 * A convenience component for HoverCard action buttons.
 * Automatically applies divider and spacing.
 *
 * @example
 * ```tsx
 * <HoverCard>
 *   <HoverCardContent>
 *     <Typography variant="h5">Card Title</Typography>
 *   </HoverCardContent>
 *   <HoverCardActions>
 *     <Button size="small">Cancel</Button>
 *     <Button size="small" variant="contained" color="primary">
 *       Save
 *     </Button>
 *   </HoverCardActions>
 * </HoverCard>
 * ```
 */
export const HoverCardActions = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ children, ...rest }, ref) => {
  return <StyledHoverCardActions ref={ref} {...rest}>{children}</StyledHoverCardActions>;
});

HoverCardActions.displayName = 'HoverCardActions';

/**
 * HoverCardHeader Component
 *
 * A convenience component for HoverCard header with title and subtitle.
 *
 * @example
 * ```tsx
 * <HoverCard>
 *   <HoverCardHeader
 *     title="Card Title"
 *     subheader="September 14, 2016"
 *     avatar={<Avatar>HC</Avatar>}
 *     action={<IconButton><MoreVertIcon /></IconButton>}
 *   />
 *   <HoverCardContent>
 *     <Typography>Card content...</Typography>
 *   </HoverCardContent>
 * </HoverCard>
 * ```
 */
export interface HoverCardHeaderProps {
  /** Card title */
  title?: React.ReactNode;
  /** Card subtitle */
  subheader?: React.ReactNode;
  /** Avatar element */
  avatar?: React.ReactNode;
  /** Action element (typically icon button) */
  action?: React.ReactNode;
  /** Additional CSS class name */
  className?: string;
  /** Disable padding */
  disablePadding?: boolean;
}

export const HoverCardHeader = React.forwardRef<HTMLDivElement, HoverCardHeaderProps>(
  ({ title, subheader, avatar, action, className, disablePadding = false }, ref) => {
    const theme = useEmotionTheme().theme;

    return (
      <StyledHoverCardContent
        ref={ref}
        className={className}
        disablePadding={disablePadding}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: disablePadding ? 0 : theme.spacing.md,
          paddingBottom: disablePadding ? 0 : theme.spacing.sm,
        }}
      >
        {avatar && <div style={{ marginRight: theme.spacing.md }}>{avatar}</div>}
        <div style={{ flex: '1 1 auto' }}>
          {title && (
            <div
              style={{
                fontSize: theme.typography.fontSize.lg,
                fontWeight: theme.typography.fontWeight.medium,
                color: theme.text.primary,
              }}
            >
              {title}
            </div>
          )}
          {subheader && (
            <div
              style={{
                fontSize: theme.typography.fontSize.sm,
                color: theme.text.secondary,
                marginTop: theme.spacing.xs,
              }}
            >
              {subheader}
            </div>
          )}
        </div>
        {action && <div style={{ marginLeft: 'auto' }}>{action}</div>}
      </StyledHoverCardContent>
    );
  }
);

HoverCardHeader.displayName = 'HoverCardHeader';

export default HoverCard;
