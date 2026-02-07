import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Badge overlap type
 */
export type BadgeOverlap = 'rectangular' | 'circular';

/**
 * Badge anchor origin position
 */
export interface BadgeOrigin {
  vertical: 'top' | 'bottom';
  horizontal: 'left' | 'right';
}

/**
 * Badge max value (shows 99+ when exceeded)
 */
const DEFAULT_MAX = 99;

/**
 * Badge component props interface
 */
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Badge content (typically a number or string) */
  badgeContent?: React.ReactNode;
  /** Child component to wrap */
  children?: React.ReactNode;
  /** Maximum value to display (shows 99+ when exceeded) */
  max?: number;
  /** If true, badge is hidden */
  invisible?: boolean;
  /** Badge overlap behavior */
  overlap?: BadgeOverlap;
  /** Badge position */
  anchorOrigin?: BadgeOrigin;
  /** Badge color */
  color?: 'default' | 'primary' | 'secondary' | 'error' | 'success' | 'warning' | 'info';
  /** If true, show dot instead of badgeContent */
  showZero?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  badgeRef?: React.Ref<HTMLDivElement>;
}

/**
 * Badge anchor positions
 */
const getAnchorStyles = (anchorOrigin: BadgeOrigin, overlap: BadgeOverlap): string => {
  const { vertical, horizontal } = anchorOrigin;

  const verticalTransform = vertical === 'top' ? '0%' : '100%';
  const horizontalTransform = horizontal === 'left' ? '0%' : '100%';
  const verticalOffset = vertical === 'top' ? '0%' : '-100%';
  const horizontalOffset = horizontal === 'left' ? '0%' : '-100%';

  let top = 'auto';
  let bottom = 'auto';
  let left = 'auto';
  let right = 'auto';

  if (vertical === 'top') {
    top = '0';
  } else {
    bottom = '0';
  }

  if (horizontal === 'left') {
    left = '0';
  } else {
    right = '0';
  }

  const transform = `translate(${horizontalOffset}, ${verticalOffset})`;

  // Overlap adjustments
  const overlapOffset = overlap === 'circular' ? '50%' : '0';

  return `
    ${vertical}: ${vertical === 'top' ? `calc(${top} - ${overlapOffset})` : `calc(${bottom} - ${overlapOffset})`};
    ${horizontal}: ${horizontal === 'left' ? `calc(${left} - ${overlapOffset})` : `calc(${right} - ${overlapOffset})`};
    transform: ${transform};
  `;
};

/**
 * Badge wrapper container
 */
const BadgeRoot = styled.div<{ theme: EmotionTheme; invisible?: boolean }>`
  position: relative;
  display: inline-flex;
  vertical-align: middle;
  flex-shrink: 0;

  /* Hide badge when invisible */
  ${({ invisible }) =>
    invisible
      ? `
    & > *:not([data-badge]) {
      display: none;
    }
  `
      : ''}
`;

/**
 * Badge component
 */
const BadgeBadge = styled('span')<{
  theme: EmotionTheme;
  color: string;
  overlap: BadgeOverlap;
  anchorOrigin: BadgeOrigin;
}>`
  position: absolute;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  align-content: center;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  z-index: 1;
  transition: transform 225ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Anchor positioning */
  ${({ anchorOrigin, overlap }) => getAnchorStyles(anchorOrigin, overlap)}

  /* Overlap adjustments */
  ${({ overlap }) =>
    overlap === 'circular'
      ? `
    transform-origin: 100% 0%;
  `
      : ''}

  /* Color styles */
  ${({ theme, color }) => {
    const colorMap = {
      default: {
        backgroundColor: theme.error.main,
        color: theme.error.contrastText,
      },
      primary: {
        backgroundColor: theme.primary.main,
        color: theme.primary.contrastText,
      },
      secondary: {
        backgroundColor: theme.secondary.main,
        color: theme.secondary.contrastText,
      },
      error: {
        backgroundColor: theme.error.main,
        color: theme.error.contrastText,
      },
      success: {
        backgroundColor: theme.success.main,
        color: theme.success.contrastText,
      },
      warning: {
        backgroundColor: theme.warning.main,
        color: theme.warning.contrastText,
      },
      info: {
        backgroundColor: theme.info.main,
        color: theme.info.contrastText,
      },
    };

    const styles = colorMap[color as keyof typeof colorMap] || colorMap.default;
    return `
      background-color: ${styles.backgroundColor};
      color: ${styles.color};
    `;
  }}

  /* Dot variant */
  &[data-dot='true'] {
    min-width: 8px;
    height: 8px;
    padding: 0;
    border-radius: 50%;
  }
`;

/**
 * Badge Component
 *
 * Badge generates a small badge to the top-right of its child element.
 *
 * @example
 * ```tsx
 * // Basic badge
 * <Badge badgeContent={5}>
 *   <Icon name="Mail" />
 * </Badge>
 *
 * // With color
 * <Badge badgeContent={12} color="primary">
 *   <Icon name="Notifications" />
 * </Badge>
 *
 * // Dot badge
 * <Badge color="success" variant="dot">
 *   <Icon name="Check" />
 * </Badge>
 *
 * // With max value
 * <Badge badgeContent={150} max={99}>
 *   <Icon name="Messages" />
 * </Badge>
 *
 * // Show zero
 * <Badge badgeContent={0} showZero>
 *   <Icon name="Inbox" />
 * </Badge>
 *
 * // Custom anchor origin
 * <Badge
 *   badgeContent={5}
 *   anchorOrigin={{
 *     vertical: 'bottom',
 *     horizontal: 'left',
 *   }}
 * >
 *   <Icon name="Alert" />
 * </Badge>
 *
 * // With overlap
 * <Badge badgeContent={4} overlap="circular">
 *   <Avatar>JD</Avatar>
 * </Badge>
 * ```
 */
export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  (
    {
      badgeContent,
      children,
      max = DEFAULT_MAX,
      invisible = false,
      overlap = 'rectangular',
      anchorOrigin = { vertical: 'top', horizontal: 'right' },
      color = 'default',
      showZero = false,
      className,
      style,
      badgeRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Determine if badge should be displayed
    const displayBadge = badgeContent !== undefined && badgeContent !== null;

    // Check if invisible (zero content and showZero is false)
    const isInvisible =
      invisible || (!displayBadge && !showZero) || (badgeContent === 0 && !showZero);

    // Format badge content
    let formattedContent: React.ReactNode = badgeContent;
    if (typeof badgeContent === 'number' && badgeContent > max) {
      formattedContent = `${max}+`;
    }

    // Check if should show as dot
    const isDot = badgeContent === null || badgeContent === undefined;

    return (
      <BadgeRoot
        ref={ref || badgeRef}
        theme={theme}
        invisible={isInvisible}
        className={className}
        style={style}
        {...rest}
      >
        {children}
        {displayBadge || isDot ? (
          <BadgeBadge
            theme={theme}
            color={color}
            overlap={overlap}
            anchorOrigin={anchorOrigin}
            data-dot={isDot}
            data-badge="true"
            aria-label={`${badgeContent} notifications`}
          >
            {isDot ? null : formattedContent}
          </BadgeBadge>
        ) : null}
      </BadgeRoot>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
