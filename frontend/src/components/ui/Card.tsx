import React from 'react';
import styled from '@emotion/styled';
import Paper, { PaperProps } from './Paper';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Card component props interface
 * Extends PaperProps with Card-specific properties
 */
export interface CardProps extends Omit<PaperProps, 'elevation'> {
  /**
   * Card content - can be a function (render prop) or React node
   * When using render prop, receives CardContent interface
   */
  children?: React.ReactNode | ((props: CardContentProps) => React.ReactNode);
  /**
   * Card actions - typically buttons or links at the bottom of the card
   */
  actions?: React.ReactNode;
  /**
   * If true, card will have hover elevation effect
   */
  hoverable?: boolean;
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
}

/**
 * Card content props interface (for render prop)
 */
export interface CardContentProps {
  /** Hover state */
  hovered: boolean;
}

/**
 * Card content area component
 */
const StyledCardContent = styled('div')<{ disablePadding?: boolean; padding?: string | number }>(
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
 * Card actions component
 */
const StyledCardActions = styled('div')(() => {
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
 * Styled Card Component
 */
const StyledCard = styled(Paper)<CardProps>(
  {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    position: 'relative',
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Hover effect
    if (props.hoverable) {
      styles['&:hover'] = {
        boxShadow: '0 8px 16px -4px rgba(0, 0, 0, 0.2), 0 6px 10px -2px rgba(0, 0, 0, 0.14)',
        transform: 'translateY(-2px)',
        transition: 'box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1), transform 300ms cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
      };
    }

    // Outlined style
    if (props.outlined || props.bordered) {
      styles.boxShadow = 'none';
      styles.border = `1px solid ${props.borderColor || theme.divider}`;
    }

    // If outlined, override elevation
    if (props.outlined) {
      styles.elevation = 0;
    }

    return styles;
  }
);

/**
 * Card Component
 *
 * A container component that extends Paper with additional features for building card UIs.
 * Cards contain content and actions about a single subject.
 *
 * Features:
 * - Built-in elevation with hover effects
 * - Outlined/ bordered variants
 * - Flexible content area with optional padding
 * - Actions area at the bottom
 * - Fully accessible and themeable
 *
 * @example
 * ```tsx
 * // Basic card
 * <Card>
 *   <Typography variant="h6">Card Title</Typography>
 *   <Typography variant="body2">Card content goes here...</Typography>
 * </Card>
 *
 * // Card with actions
 * <Card
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
 * </Card>
 *
 * // Hoverable card
 * <Card hoverable onClick={handleClick}>
 *   <Typography variant="h6">Hoverable Card</Typography>
 *   <Typography variant="body2">Hover over me!</Typography>
 * </Card>
 *
 * // Outlined card (no elevation)
 * <Card outlined>
 *   <Typography variant="h6">Outlined Card</Typography>
 *   <Typography variant="body2">Clean, flat design</Typography>
 * </Card>
 *
 * // Bordered card with custom border color
 * <Card bordered borderColor="primary.main">
 *   <Typography variant="h6">Bordered Card</Typography>
 *   <Typography variant="body2">Custom border color</Typography>
 * </Card>
 *
 * // Card without padding
 * <Card disablePadding>
 *   <img src="/image.jpg" alt="Card image" />
 *   <Typography variant="h6" sx={{ p: 2 }}>
 *     Image Card
 *   </Typography>
 * </Card>
 *
 * // Custom padding
 * <Card padding={32}>
 *   <Typography variant="h6">Custom Padding</Typography>
 *   <Typography variant="body2">32px padding</Typography>
 * </Card>
 *
 * // Render prop for advanced control
 * <Card hoverable>
 *   {({ hovered }) => (
 *     <Typography color={hovered ? 'primary.main' : 'text.primary'}>
 *       {hovered ? 'I'm hovered!' : 'Hover me'}
 *     </Typography>
 *   )}
 * </Card>
 *
 * // Square card with custom elevation
 * <Card square elevation={4}>
 *   <Typography variant="h6">Square Card</Typography>
 *   <Typography variant="body2">No rounded corners</Typography>
 * </Card>
 * ```
 */
const Card = React.forwardRef<HTMLElement, CardProps>(
  (
    {
      children,
      actions,
      hoverable = false,
      outlined = false,
      bordered = false,
      borderColor,
      padding,
      disablePadding = false,
      elevation,
      ...rest
    },
    ref
  ) => {
    // Default elevation for cards (higher than paper)
    const cardElevation = elevation !== undefined ? elevation : outlined ? 0 : 2;

    return (
      <StyledCard
        ref={ref as any}
        elevation={cardElevation}
        hoverable={hoverable}
        outlined={outlined}
        bordered={bordered}
        borderColor={borderColor}
        {...rest}
      >
        <StyledCardContent disablePadding={disablePadding} padding={padding}>
          {typeof children === 'function'
            ? (children as (props: CardContentProps) => React.ReactNode)({
                hovered: false,
              })
            : children}
        </StyledCardContent>
        {actions && <StyledCardActions>{actions}</StyledCardActions>}
      </StyledCard>
    );
  }
);

Card.displayName = 'Card';

/**
 * CardContent Component
 *
 * A convenience component for card content area.
 * Automatically applies padding unless disabled.
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardContent>
 *     <Typography variant="h5">Card Title</Typography>
 *     <Typography variant="body2">Card content...</Typography>
 *   </CardContent>
 *   <CardActions>
 *     <Button size="small">Action</Button>
 *   </CardActions>
 * </Card>
 * ```
 */
export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { disablePadding?: boolean }
>(({ children, disablePadding = false, ...rest }, ref) => {
  return (
    <StyledCardContent ref={ref} disablePadding={disablePadding}>
      {children}
    </StyledCardContent>
  );
});

CardContent.displayName = 'CardContent';

/**
 * CardActions Component
 *
 * A convenience component for card action buttons.
 * Automatically applies divider and spacing.
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardContent>
 *     <Typography variant="h5">Card Title</Typography>
 *   </CardContent>
 *   <CardActions>
 *     <Button size="small">Cancel</Button>
 *     <Button size="small" variant="contained" color="primary">
 *       Save
 *     </Button>
 *   </CardActions>
 * </Card>
 * ```
 */
export const CardActions = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ children, ...rest }, ref) => {
  return <StyledCardActions ref={ref}>{children}</StyledCardActions>;
});

CardActions.displayName = 'CardActions';

/**
 * CardHeader Component
 *
 * A convenience component for card header with title and subtitle.
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardHeader
 *     title="Card Title"
 *     subheader="September 14, 2016"
 *     avatar={<Avatar>AC</Avatar>}
 *     action={<IconButton><MoreVertIcon /></IconButton>}
 *   />
 *   <CardContent>
 *     <Typography>Card content...</Typography>
 *   </CardContent>
 * </Card>
 * ```
 */
export interface CardHeaderProps {
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

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subheader, avatar, action, className, disablePadding = false }, ref) => {
    const theme = useEmotionTheme().theme;

    return (
      <StyledCardContent
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
      </StyledCardContent>
    );
  }
);

CardHeader.displayName = 'CardHeader';

export default Card;
