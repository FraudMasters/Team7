import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Linear progress variant types
 */
export type LinearProgressVariant = 'determinate' | 'indeterminate' | 'buffer';

/**
 * Props for LinearProgress component
 */
export interface LinearProgressProps {
  /** Progress value (0-100) for determinate variant */
  value?: number;
  /** Buffer value (0-100) for buffer variant */
  valueBuffer?: number;
  /** Color of the progress indicator */
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'inherit';
  /** Variant type */
  variant?: LinearProgressVariant;
  /** Height of the progress bar in pixels */
  height?: number;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** ARIA attributes for accessibility */
  'aria-label'?: string;
  'aria-valuenow'?: number;
  'aria-valuemin'?: number;
  'aria-valuemax'?: number;
}

/**
 * Get color based on color prop and theme
 */
const getColorStyles = (color: string, theme: EmotionTheme) => {
  const colorMap: Record<string, string> = {
    primary: theme.primary.main,
    secondary: theme.secondary.main,
    success: theme.success.main,
    error: theme.error.main,
    warning: theme.warning.main,
    info: theme.info.main,
    inherit: 'currentColor',
  };

  return colorMap[color] || colorMap.primary;
};

/**
 * Root container
 */
const Root = styled('span')<{
  height: number;
}>((props) => {
  const theme = useEmotionTheme().theme;

  return {
    display: 'block',
    width: '100%',
    height: `${props.height}px`,
    backgroundColor: theme.palette.action.hover,
    borderRadius: theme.borderRadius.sm,
    overflow: 'hidden',
    position: 'relative',
  };
});

/**
 * Progress bar container
 */
const ProgressContainer = styled('span')(() => {
  return {
    display: 'block',
    width: '100%',
    height: '100%',
    position: 'relative',
    overflow: 'hidden',
  };
});

/**
 * Progress bar (determinate and indeterminate)
 */
const ProgressBar = styled('span')<{
  color: string;
  variant: LinearProgressVariant;
  width?: number;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const color = getColorStyles(props.color, theme);

  const styles: Record<string, any> = {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: props.variant === 'determinate' ? `${props.width}%` : '100%',
    backgroundColor: color,
    transition: 'width 0.3s ease',
  };

  if (props.variant === 'indeterminate') {
    styles.width = 'auto';
    styles.animation = 'linear-indeterminate-bar 2s infinite linear';
    styles.transformOrigin = 'left';
  }

  return styles;
});

/**
 * Buffer bar (for buffer variant)
 */
const BufferBar = styled('span')<{
  color: string;
  width?: number;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const color = getColorStyles(props.color, theme);

  return {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: props.width !== undefined ? `${props.width}%` : '0%',
    backgroundColor: color,
    opacity: 0.3,
    transition: 'width 0.3s ease',
  };
});

/**
 * Add keyframes for indeterminate animation
 */
const indeterminateKeyframes = `
  @keyframes linear-indeterminate-bar {
    0% {
      transform: translateX(-100%) scaleX(0.5);
    }
    50% {
      transform: translateX(0%) scaleX(0.5);
    }
    75% {
      transform: translateX(75%) scaleX(0.25);
    }
    100% {
      transform: translateX(125%) scaleX(0.5);
    }
  }
`;

/**
 * LinearProgress Component
 *
 * A linear progress indicator that visualizes an ongoing process in a horizontal bar.
 *
 * @example
 * ```tsx
 * // Indeterminate (loading) bar
 * <LinearProgress />
 *
 * // Determinate progress (45% complete)
 * <LinearProgress variant="determinate" value={45} />
 *
 * // With custom color and height
 * <LinearProgress color="success" height={8} />
 *
 * // Buffer variant (for loading with buffered content)
 * <LinearProgress
 *   variant="buffer"
 *   value={30}
 *   valueBuffer={60}
 * />
 *
 * // Error progress
 * <LinearProgress variant="determinate" value={75} color="error" />
 * ```
 */
const LinearProgress: React.FC<LinearProgressProps> = ({
  value = 0,
  valueBuffer = 0,
  color = 'primary',
  variant = 'indeterminate',
  height = 4,
  className,
  style,
  'aria-label': ariaLabel = 'Loading...',
  'aria-valuenow': ariaValueNow,
  'aria-valuemin': ariaValueMin = 0,
  'aria-valuemax': ariaValueMax = 100,
}) => {
  // ARIA props for determinate variant
  const ariaProps = variant === 'determinate'
    ? {
        'aria-label': ariaLabel,
        'aria-valuenow': ariaValueNow ?? value,
        'aria-valuemin': ariaValueMin,
        'aria-valuemax': ariaValueMax,
        role: 'progressbar',
      }
    : {
        'aria-label': ariaLabel,
        role: 'status',
      };

  return (
    <>
      <style>{indeterminateKeyframes}</style>
      <Root height={height} className={className} style={style} {...ariaProps}>
        <ProgressContainer>
          {variant === 'buffer' && (
            <BufferBar color={color} width={valueBuffer} />
          )}
          <ProgressBar
            color={color}
            variant={variant}
            width={variant === 'determinate' || variant === 'buffer' ? value : undefined}
          />
        </ProgressContainer>
      </Root>
    </>
  );
};

export default LinearProgress;
