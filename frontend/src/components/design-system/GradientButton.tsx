import React from 'react';
import styled from '@emotion/styled';
import { motion, HTMLMotionProps } from 'framer-motion';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Icon from '../ui/primitives/Icon';

/**
 * Gradient variant types using theme gradients
 */
export type GradientVariant =
  | 'primary'
  | 'primaryReverse'
  | 'primarySubtle'
  | 'primaryLight'
  | 'secondary'
  | 'secondaryReverse'
  | 'secondarySubtle'
  | 'secondaryLight'
  | 'success'
  | 'successReverse'
  | 'successSubtle'
  | 'error'
  | 'errorReverse'
  | 'errorSubtle'
  | 'warning'
  | 'warningReverse'
  | 'warningSubtle'
  | 'info'
  | 'infoReverse'
  | 'infoSubtle'
  | 'grey'
  | 'greyLight'
  | 'greySubtle'
  | 'neutral'
  | 'neutralSubtle'
  | 'rainbow'
  | 'rainbowSubtle'
  | 'rainbowHorizontal'
  | 'glossy'
  | 'glass'
  | 'shine'
  | 'radialPrimary'
  | 'radialSecondary'
  | 'glow'
  | 'glowSuccess'
  | 'glowError'
  | 'glowWarning'
  | 'meshPrimary'
  | 'meshSecondary'
  | 'meshColorful';

/**
 * Button size types
 */
export type GradientButtonSize = 'small' | 'medium' | 'large';

/**
 * Animation variant types
 */
export type AnimationVariant = 'scale' | 'lift' | 'shimmer' | 'glow' | 'none';

/**
 * Base gradient button props interface
 */
export interface BaseGradientButtonProps {
  /** Child content */
  children?: React.ReactNode;
  /** Gradient variant to use */
  variant?: GradientVariant;
  /** Button size */
  size?: GradientButtonSize;
  /** Disable the button */
  disabled?: boolean;
  /** Full width button */
  fullWidth?: boolean;
  /** Icon to display before children */
  startIcon?: React.ReactElement;
  /** Icon to display after children */
  endIcon?: React.ReactElement;
  /** Click handler */
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  /** HTML type attribute */
  type?: 'button' | 'submit' | 'reset';
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Tab index */
  tabIndex?: number;
  /** ARIA label for accessibility */
  'aria-label'?: string;
  /** Reference to button element */
  buttonRef?: React.Ref<HTMLButtonElement>;
  /** Animation variant for hover/click effects */
  animation?: AnimationVariant;
  /** If true, button has rounded pill shape */
  pill?: boolean;
  /** If true, removes shadow */
  disableShadow?: boolean;
  /** Custom gradient string (overrides variant) */
  customGradient?: string;
  /** Text color override (default is white/contrast) */
  textColor?: string;
  /** Border radius override */
  borderRadius?: string;
}

/**
 * Props for GradientButton component
 * Extends standard HTML button attributes
 */
export interface GradientButtonProps extends BaseGradientButtonProps, Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'size'> {}

/**
 * Get gradient from theme based on variant
 */
const getGradient = (variant: GradientVariant, theme: EmotionTheme, customGradient?: string): string => {
  if (customGradient) {
    return customGradient;
  }

  // Map gradient variants to theme gradients
  const gradientMap: Record<GradientVariant, keyof EmotionTheme['gradients']> = {
    primary: 'primary',
    primaryReverse: 'primaryReverse',
    primarySubtle: 'primarySubtle',
    primaryLight: 'primaryLight',
    secondary: 'secondary',
    secondaryReverse: 'secondaryReverse',
    secondarySubtle: 'secondarySubtle',
    secondaryLight: 'secondaryLight',
    success: 'success',
    successReverse: 'successReverse',
    successSubtle: 'successSubtle',
    error: 'error',
    errorReverse: 'errorReverse',
    errorSubtle: 'errorSubtle',
    warning: 'warning',
    warningReverse: 'warningReverse',
    warningSubtle: 'warningSubtle',
    info: 'info',
    infoReverse: 'infoReverse',
    infoSubtle: 'infoSubtle',
    grey: 'grey',
    greyLight: 'greyLight',
    greySubtle: 'greySubtle',
    neutral: 'neutral',
    neutralSubtle: 'neutralSubtle',
    rainbow: 'rainbow',
    rainbowSubtle: 'rainbowSubtle',
    rainbowHorizontal: 'rainbowHorizontal',
    glossy: 'glossy',
    glass: 'glass',
    shine: 'shine',
    radialPrimary: 'radialPrimary',
    radialSecondary: 'radialSecondary',
    glow: 'glow',
    glowSuccess: 'glowSuccess',
    glowError: 'glowError',
    glowWarning: 'glowWarning',
    meshPrimary: 'meshPrimary',
    meshSecondary: 'meshSecondary',
    meshColorful: 'meshColorful',
  };

  const gradientKey = gradientMap[variant] || 'primary';
  return theme.gradients[gradientKey] || theme.gradients.primary;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: GradientButtonSize) => {
  const sizeMap = {
    small: {
      padding: '6px 14px',
      fontSize: '0.875rem',
      lineHeight: 1.5,
      letterSpacing: '0.01071em',
      minHeight: '32px',
    },
    medium: {
      padding: '8px 18px',
      fontSize: '1rem',
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
      minHeight: '40px',
    },
    large: {
      padding: '12px 24px',
      fontSize: '1.125rem',
      lineHeight: 1.5,
      letterSpacing: '0.00714em',
      minHeight: '48px',
    },
  };

  return sizeMap[size];
};

/**
 * Get animation variants for Framer Motion
 */
const getAnimationVariants = (animation: AnimationVariant) => {
  const variants = {
    scale: {
      hover: { scale: 1.05, transition: { duration: 0.2, ease: 'easeInOut' } },
      tap: { scale: 0.95, transition: { duration: 0.1 } },
    },
    lift: {
      hover: { y: -2, transition: { duration: 0.2, ease: 'easeInOut' } },
      tap: { y: 0, transition: { duration: 0.1 } },
    },
    shimmer: {
      hover: {
        backgroundPosition: ['200% center', '0 center'],
        transition: { duration: 1.5, ease: 'linear' },
      },
      tap: { scale: 0.98, transition: { duration: 0.1 } },
    },
    glow: {
      hover: {
        boxShadow: '0 0 20px rgba(25, 118, 210, 0.5)',
        transition: { duration: 0.2, ease: 'easeInOut' },
      },
      tap: { scale: 0.98, transition: { duration: 0.1 } },
    },
    none: {
      hover: {},
      tap: {},
    },
  };

  return variants[animation] || variants.scale;
};

/**
 * Styled Gradient Button component
 */
const StyledGradientButton = styled(motion.button)<GradientButtonProps & { theme: EmotionTheme }>`
  /* Reset and base styles */
  appearance: none;
  box-sizing: border-box;
  user-select: none;
  cursor: pointer;
  outline: none;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-weight: 600;
  text-transform: none;
  border: none;
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
  background-size: 200% auto;

  /* Size styles */
  ${({ size }) => getSizeStyles(size || 'medium')}

  /* Width styles */
  ${({ fullWidth }) => (fullWidth ? 'width: 100%;' : '')}

  /* Border radius */
  border-radius: ${({ pill, borderRadius, theme }) =>
    pill ? '9999px' : borderRadius || theme.borderRadius.lg};

  /* Gradient background */
  background: ${({ variant, theme, customGradient }) =>
    getGradient(variant || 'primary', theme, customGradient)};

  /* Text color */
  color: ${({ textColor, theme }) => textColor || '#ffffff'};

  /* Shadow */
  box-shadow: ${({ disableShadow, theme }) =>
    disableShadow
      ? 'none'
      : theme.shadows.md};

  /* Transition */
  transition: all ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};

  /* Disabled state */
  ${({ disabled }) =>
    disabled
      ? `
    cursor: not-allowed;
    pointer-events: none;
    opacity: 0.5;
    box-shadow: none;
  `
      : ''}

  /* Focus visible state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: 2px;
  }

  /* Remove default button styles */
  &::-moz-focus-inner {
    border-style: none;
    padding: 0;
  }

  /* Shimmer effect overlay */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.2) 50%,
      transparent 100%
    );
    transform: translateX(-100%);
    transition: transform 0.6s ease;
  }

  &:hover:not(:disabled)::before {
    transform: translateX(100%);
  }
`;

/**
 * GradientButton Component
 *
 * A gradient button component with smooth animations and micro-interactions.
 * Built with Emotion and Framer Motion to provide a modern, polished look.
 *
 * @example
 * ```tsx
 * // Basic gradient button
 * <GradientButton>Click me</GradientButton>
 *
 * // With gradient variant
 * <GradientButton variant="secondary">Secondary</GradientButton>
 *
 * // With size
 * <GradientButton variant="success" size="large">Large Button</GradientButton>
 *
 * // With icons
 * <GradientButton
 *   variant="primary"
 *   startIcon={<Icon name="Plus" />}
 *   endIcon={<Icon name="ArrowRight" />}
 * >
 *   With Icons
 * </GradientButton>
 *
 * // With animation variant
 * <GradientButton variant="rainbow" animation="shimmer">
 *   Shimmer Effect
 * </GradientButton>
 *
 * // Pill shaped
 * <GradientButton variant="error" pill>
 *   Pill Button
 * </GradientButton>
 *
 * // Custom gradient
 * <GradientButton
 *   customGradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
 * >
 *   Custom Gradient
 * </GradientButton>
 *
 * // Full width button
 * <GradientButton variant="primary" fullWidth>
 *   Full Width
 * </GradientButton>
 * ```
 */
export const GradientButton: React.FC<GradientButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  fullWidth = false,
  startIcon,
  endIcon,
  onClick,
  type = 'button',
  className,
  style,
  tabIndex,
  'aria-label': ariaLabel,
  buttonRef,
  animation = 'scale',
  pill = false,
  disableShadow = false,
  customGradient,
  textColor,
  borderRadius,
  ...rest
}) => {
  const { theme } = useEmotionTheme();

  // Render icon if provided
  const renderIcon = (icon: React.ReactElement | undefined) => {
    if (!icon) return null;
    // If it's already an Icon component, clone with size
    if (React.isValidElement(icon) && icon.type === Icon) {
      return React.cloneElement(icon, {
        size: size === 'small' ? 'small' : size === 'large' ? 'large' : 'medium',
      } as React.ComponentProps<typeof Icon>);
    }
    // Otherwise render as-is
    return icon;
  };

  // Get animation variants
  const animationVariants = getAnimationVariants(animation);

  // Motion props
  const motionProps: HTMLMotionProps<'button'> = {
    whileHover: !disabled ? animationVariants.hover : undefined,
    whileTap: !disabled ? animationVariants.tap : undefined,
  };

  return (
    <StyledGradientButton
      ref={buttonRef}
      theme={theme}
      variant={variant}
      size={size}
      disabled={disabled}
      fullWidth={fullWidth}
      onClick={onClick}
      type={type}
      className={className}
      style={style}
      tabIndex={tabIndex}
      aria-label={ariaLabel}
      aria-disabled={disabled}
      animation={animation}
      pill={pill}
      disableShadow={disableShadow}
      customGradient={customGradient}
      textColor={textColor}
      borderRadius={borderRadius}
      {...motionProps}
      {...rest}
    >
      {renderIcon(startIcon)}
      {children}
      {renderIcon(endIcon)}
    </StyledGradientButton>
  );
};

export default GradientButton;
