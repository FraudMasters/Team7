import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Circular progress variant types
 */
export type CircularProgressVariant = 'determinate' | 'indeterminate';

/**
 * Props for CircularProgress component
 */
export interface CircularProgressProps {
  /** Progress value (0-100) for determinate variant */
  value?: number;
  /** Size of the spinner in pixels */
  size?: number;
  /** Thickness of the circular stroke */
  thickness?: number;
  /** Color of the progress indicator */
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'inherit';
  /** Variant type */
  variant?: CircularProgressVariant;
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
 * SVG container
 */
const StyledSvg = styled('svg')<{
  size: number;
  color: string;
}>((props) => {
  const theme = useEmotionTheme().theme;
  const color = getColorStyles(props.color, theme);

  return {
    display: 'inline-block',
    width: `${props.size}px`,
    height: `${props.size}px`,
    color: color,
    animation: 'circular-rotate 1.4s linear infinite',
    '@keyframes circular-rotate': {
      '0%': {
        transform: 'rotate(0deg)',
      },
      '100%': {
        transform: 'rotate(360deg)',
      },
    },
  };
});

/**
 * Circular path background
 */
const CircleBackground = styled('circle')<{
  thickness: number;
}>((props) => {
  return {
    stroke: 'currentColor',
    strokeWidth: props.thickness,
    strokeDasharray: '0 0',
    opacity: 0.25,
  };
});

/**
 * Circular progress path
 */
const CircleProgress = styled('circle')<{
  thickness: number;
  circumference: number;
  dashOffset: number;
  variant: CircularProgressVariant;
}>((props) => {
  const styles: Record<string, any> = {
    stroke: 'currentColor',
    strokeWidth: props.thickness,
    strokeDasharray: `${props.circumference} ${props.circumference}`,
    strokeDashoffset: props.dashOffset,
    strokeLinecap: 'round',
    transition: 'stroke-dashoffset 0.3s ease',
  };

  if (props.variant === 'indeterminate') {
    styles.animation = 'circular-dash 1.4s ease-in-out infinite';
    styles.transition = 'none';
  }

  return styles;
});

/**
 * Add keyframes for indeterminate animation
const circularDashKeyframes = `
  @keyframes circular-dash {
    0% {
      stroke-dasharray: 1, 200;
      stroke-dashoffset: 0;
    }
    50% {
      stroke-dasharray: 89, 200;
      stroke-dashoffset: -35px;
    }
    100% {
      stroke-dasharray: 89, 200;
      stroke-dashoffset: -124px;
    }
  }
`;

/**
 * CircularProgress Component
 *
 * A circular progress indicator that visualizes an ongoing process.
 *
 * @example
 * ```tsx
 * // Indeterminate (loading) spinner
 * <CircularProgress />
 *
 * // With custom size and color
 * <CircularProgress size={60} color="success" />
 *
 * // Determinate progress (75% complete)
 * <CircularProgress variant="determinate" value={75} />
 *
 * // Thin stroke with custom color
 * <CircularProgress thickness={2} color="secondary" />
 *
 * // Small indeterminate spinner
 * <CircularProgress size={24} thickness={3} />
 * ```
 */
const CircularProgress: React.FC<CircularProgressProps> = ({
  value = 0,
  size = 40,
  thickness = 3.6,
  color = 'primary',
  variant = 'indeterminate',
  className,
  style,
  'aria-label': ariaLabel = 'Loading...',
  'aria-valuenow': ariaValueNow,
  'aria-valuemin': ariaValueMin = 0,
  'aria-valuemax': ariaValueMax = 100,
}) => {
  const theme = useEmotionTheme().theme;

  // Calculate circle dimensions
  const radius = (size - thickness) / 2;
  const circumference = radius * 2 * Math.PI;

  // Calculate dash offset for determinate variant
  const dashOffset = variant === 'determinate'
    ? circumference - (value / 100) * circumference
    : circumference - 25; // Start point for indeterminate animation

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
      <style>
        {`
          @keyframes circular-dash {
            0% {
              stroke-dasharray: 1, 200;
              stroke-dashoffset: 0;
            }
            50% {
              stroke-dasharray: 89, 200;
              stroke-dashoffset: -35px;
            }
            100% {
              stroke-dasharray: 89, 200;
              stroke-dashoffset: -124px;
            }
          }
        `}
      </style>
      <StyledSvg
        size={size}
        color={color}
        className={className}
        style={style}
        viewBox={`0 0 ${size} ${size}`}
        {...ariaProps}
      >
        <CircleBackground
          thickness={thickness}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
        />
        <CircleProgress
          thickness={thickness}
          circumference={circumference}
          dashOffset={dashOffset}
          variant={variant}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
        />
      </StyledSvg>
    </>
  );
};

export default CircularProgress;
