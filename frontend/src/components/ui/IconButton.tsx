import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import Icon from './primitives/Icon';

/**
 * IconButton size types
 */
export type IconButtonSize = 'small' | 'medium' | 'large';

/**
 * IconButton color types
 */
export type IconButtonColor =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'inherit'
  | 'default';

/**
 * Base IconButton props interface
 */
export interface BaseIconButtonProps {
  /** Icon to display (can be Icon component or icon name) */
  icon?: React.ReactElement | string;
  /** Icon name (alternative to icon prop) */
  name?: string;
  /** Button size */
  size?: IconButtonSize;
  /** Button color */
  color?: IconButtonColor;
  /** Disable the button */
  disabled?: boolean;
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
  /** If true, edges will be rounded */
  edge?: 'start' | 'end' | false;
}

/**
 * Props for IconButton component
 * Extends standard HTML button attributes
 */
export interface IconButtonProps extends BaseIconButtonProps, Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'color' | 'size'> {}

/**
 * Get color styles based on color and theme
 */
const getColorStyles = (color: IconButtonColor, theme: EmotionTheme) => {
  const isDark = theme.mode === 'dark';

  if (color === 'inherit') {
    return {
      color: 'inherit',
      '&:hover': {
        backgroundColor: isDark
          ? 'rgba(255, 255, 255, 0.08)'
          : 'rgba(0, 0, 0, 0.04)',
      },
    };
  }

  if (color === 'default') {
    return {
      color: theme.text.secondary,
      '&:hover': {
        backgroundColor: theme.action.hover,
      },
    };
  }

  const colorMap = {
    primary: theme.primary,
    secondary: theme.secondary,
    success: theme.success,
    error: theme.error,
    warning: theme.warning,
    info: theme.info,
  };

  const colors = colorMap[color];

  return {
    color: colors.main,
    '&:hover': {
      backgroundColor: `${colors.main}${isDark ? '1a' : '0f'}`, // 10% opacity
      '@media (hover: none)': {
        backgroundColor: 'transparent',
      },
    },
  };
};

/**
 * Get size styles
 */
const getSizeStyles = (size: IconButtonSize) => {
  const sizeMap = {
    small: {
      padding: '5px',
      width: '32px',
      height: '32px',
      fontSize: '1.125rem',
    },
    medium: {
      padding: '8px',
      width: '40px',
      height: '40px',
      fontSize: '1.25rem',
    },
    large: {
      padding: '12px',
      width: '48px',
      height: '48px',
      fontSize: '1.5rem',
    },
  };

  return sizeMap[size];
};

/**
 * Styled IconButton component
 */
const StyledIconButton = styled.button<IconButtonProps & { theme: EmotionTheme; edge?: 'start' | 'end' | false }>`
  /* Reset and base styles */
  appearance: none;
  box-sizing: border-box;
  user-select: none;
  cursor: pointer;
  outline: none;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  border-radius: ${({ theme, edge }) => {
    if (edge === 'start') return '0 50% 50% 0';
    if (edge === 'end') return '50% 0 0 50%';
    return theme.borderRadius.md;
  }};
  transition: background-color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut},
    color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border: none;
  background-color: transparent;

  /* Size styles */
  ${({ size }) => getSizeStyles(size || 'medium')}

  /* Edge styles */
  ${({ edge }) => (edge === 'start' ? 'margin-left: 8px;' : '')}
  ${({ edge }) => (edge === 'end' ? 'margin-right: 8px;' : '')}

  /* Color styles */
  ${({ color, theme }) => getColorStyles(color || 'default', theme)}

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
    outline: 2px solid ${({ theme, color }) => {
      if (color === 'inherit' || color === 'default') return theme.text.primary;
      return theme[color || 'primary'].main;
    }};
    outline-offset: 2px;
  }

  /* Remove default button styles */
  &::-moz-focus-inner {
    border-style: none;
    padding: 0;
  }

  /* Active state */
  &:active {
    transform: scale(0.96);
  }
`;

/**
 * IconButton Component
 *
 * A button component that displays an icon without text.
 * Built with Emotion to replace Material-UI IconButton component.
 *
 * @example
 * ```tsx
 * // Basic icon button with icon name
 * <IconButton name="Menu" aria-label="Open menu" />
 *
 * // With color and size
 * <IconButton name="Delete" color="error" size="large" aria-label="Delete" />
 *
 * // With Icon component
 * <IconButton icon={<Icon name="Search" />} aria-label="Search" />
 *
 * // With edge styling
 * <IconButton name="ChevronLeft" edge="start" aria-label="Previous" />
 *
 * // Disabled
 * <IconButton name="Send" disabled aria-label="Send message" />
 *
 * // With onClick handler
 * <IconButton
 *   name="Close"
 *   onClick={handleClose}
 *   aria-label="Close dialog"
 * />
 *
 * // As submit button
 * <IconButton name="Check" type="submit" aria-label="Submit" />
 * ```
 */
export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  name,
  size = 'medium',
  color = 'default',
  disabled = false,
  onClick,
  type = 'button',
  className,
  style,
  tabIndex,
  'aria-label': ariaLabel,
  buttonRef,
  edge,
  ...rest
}) => {
  const { theme } = useEmotionTheme();

  // Determine icon content
  const renderIcon = () => {
    // If icon element is provided, use it
    if (icon) {
      // If it's an Icon component, clone with size
      if (React.isValidElement(icon) && icon.type === Icon) {
        return React.cloneElement(icon, {
          size: size === 'small' ? 'small' : size === 'large' ? 'large' : 'medium',
        } as React.ComponentProps<typeof Icon>);
      }
      // Otherwise render as-is
      return icon;
    }

    // If name is provided, create Icon component
    if (name) {
      const iconSize = size === 'small' ? 'small' : size === 'large' ? 'large' : 'medium';
      return <Icon name={name} size={iconSize} />;
    }

    return null;
  };

  return (
    <StyledIconButton
      ref={buttonRef}
      theme={theme}
      size={size}
      color={color}
      disabled={disabled}
      onClick={onClick}
      type={type}
      className={className}
      style={style}
      tabIndex={tabIndex}
      aria-label={ariaLabel || (typeof name === 'string' ? name : undefined)}
      aria-disabled={disabled}
      edge={edge}
      {...rest}
    >
      {renderIcon()}
    </StyledIconButton>
  );
};

export default IconButton;
