import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Icon from './primitives/Icon';

/**
 * Button variant types
 */
export type ButtonVariant = 'contained' | 'outlined' | 'text';

/**
 * Button size types
 */
export type ButtonSize = 'small' | 'medium' | 'large';

/**
 * Button color types
 */
export type ButtonColor =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'inherit';

/**
 * Base button props interface
 */
export interface BaseButtonProps {
  /** Child content */
  children?: React.ReactNode;
  /** Button variant */
  variant?: ButtonVariant;
  /** Button color */
  color?: ButtonColor;
  /** Button size */
  size?: ButtonSize;
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
}

/**
 * Props for Button component
 * Extends standard HTML button attributes
 */
export interface ButtonProps extends BaseButtonProps, Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'color' | 'size'> {}

/**
 * Get color styles based on color and theme
 */
const getColorStyles = (color: ButtonColor, variant: ButtonVariant, theme: EmotionTheme) => {
  const colorMap = {
    primary: theme.primary,
    secondary: theme.secondary,
    success: theme.success,
    error: theme.error,
    warning: theme.warning,
    info: theme.info,
    inherit: {
      main: 'inherit',
      light: 'inherit',
      dark: 'inherit',
      contrastText: theme.text.primary,
    },
  };

  const colors = colorMap[color];
  const isDark = theme.mode === 'dark';

  if (variant === 'contained') {
    return {
      backgroundColor: color === 'inherit' ? 'transparent' : colors.main,
      color: colors.contrastText,
      '&:hover': {
        backgroundColor: color === 'inherit' ? 'rgba(0, 0, 0, 0.04)' : colors.dark,
        '@media (hover: none)': {
          backgroundColor: color === 'inherit' ? 'transparent' : colors.main,
        },
      },
      '&:active': {
        backgroundColor: color === 'inherit' ? 'rgba(0, 0, 0, 0.08)' : colors.dark,
      },
    };
  }

  if (variant === 'outlined') {
    return {
      border: `1px solid ${color === 'inherit' ? 'currentColor' : colors.main}`,
      color: color === 'inherit' ? 'inherit' : colors.main,
      backgroundColor: 'transparent',
      '&:hover': {
        backgroundColor: color === 'inherit'
          ? isDark
            ? 'rgba(255, 255, 255, 0.08)'
            : 'rgba(0, 0, 0, 0.04)'
          : `${colors.main}${isDark ? '33' : '0f'}`, // 20% opacity
        border: `1px solid ${color === 'inherit' ? 'currentColor' : colors.main}`,
        '@media (hover: none)': {
          backgroundColor: 'transparent',
        },
      },
      '&:active': {
        backgroundColor: color === 'inherit'
          ? isDark
            ? 'rgba(255, 255, 255, 0.12)'
            : 'rgba(0, 0, 0, 0.08)'
          : `${colors.main}${isDark ? '4d' : '1a'}`, // 30% opacity
      },
    };
  }

  // text variant
  return {
    color: color === 'inherit' ? 'inherit' : colors.main,
    backgroundColor: 'transparent',
    border: 'none',
    '&:hover': {
      backgroundColor: color === 'inherit'
        ? isDark
          ? 'rgba(255, 255, 255, 0.08)'
          : 'rgba(0, 0, 0, 0.04)'
        : `${colors.main}${isDark ? '1a' : '08'}`, // 10% opacity
      '@media (hover: none)': {
        backgroundColor: 'transparent',
      },
    },
    '&:active': {
      backgroundColor: color === 'inherit'
        ? isDark
          ? 'rgba(255, 255, 255, 0.12)'
          : 'rgba(0, 0, 0, 0.08)'
        : `${colors.main}${isDark ? '26' : '0f'}`, // 15% opacity
    },
  };
};

/**
 * Get size styles
 */
const getSizeStyles = (size: ButtonSize) => {
  const sizeMap = {
    small: {
      padding: '6px 12px',
      fontSize: '0.875rem',
      lineHeight: 1.5,
      letterSpacing: '0.01071em',
    },
    medium: {
      padding: '8px 16px',
      fontSize: '1rem',
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    large: {
      padding: '10px 22px',
      fontSize: '1.125rem',
      lineHeight: 1.5,
      letterSpacing: '0.00714em',
    },
  };

  return sizeMap[size];
};

/**
 * Styled Button component
 */
const StyledButton = styled.button<ButtonProps & { theme: EmotionTheme }>`
  /* Reset and base styles */
  appearance: none;
  box-sizing: border-box;
  user-select: none;
  cursor: pointer;
  outline: none;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.02857em;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  transition: all ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-decoration: none;
  white-space: nowrap;

  /* Size styles */
  ${({ size }) => getSizeStyles(size || 'medium')}

  /* Width styles */
  ${({ fullWidth }) => (fullWidth ? 'width: 100%;' : '')}

  /* Color and variant styles */
  ${({ color, variant, theme }) => getColorStyles(color || 'primary', variant || 'contained', theme)}

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
    outline: 2px solid ${({ theme, color }) => (color === 'inherit' ? theme.text.primary : theme[color || 'primary'].main)};
    outline-offset: 2px;
  }

  /* Remove default button styles */
  &::-moz-focus-inner {
    border-style: none;
    padding: 0;
  }
`;

/**
 * Button Component
 *
 * A customizable button component with variants, sizes, and colors.
 * Built with Emotion to replace Material-UI Button component.
 *
 * @example
 * ```tsx
 * // Basic contained button
 * <Button>Click me</Button>
 *
 * // With variant and color
 * <Button variant="outlined" color="secondary">Outlined</Button>
 *
 * // With icons
 * <Button
 *   startIcon={<Icon name="Plus" />}
 *   endIcon={<Icon name="ArrowRight" />}
 * >
 *   With Icons
 * </Button>
 *
 * // Full width button
 * <Button fullWidth variant="contained" color="primary">
 *   Full Width
 * </Button>
 *
 * // Disabled button
 * <Button disabled>Disabled</Button>
 * ```
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'contained',
  color = 'primary',
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

  return (
    <StyledButton
      ref={buttonRef}
      theme={theme}
      variant={variant}
      color={color}
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
      {...rest}
    >
      {renderIcon(startIcon)}
      {children}
      {renderIcon(endIcon)}
    </StyledButton>
  );
};

export default Button;
