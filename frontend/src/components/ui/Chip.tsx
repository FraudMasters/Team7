import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Chip size types
 */
export type ChipSize = 'small' | 'medium';

/**
 * Chip color types
 */
export type ChipColor =
  | 'default'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info';

/**
 * Chip variant types
 */
export type ChipVariant = 'filled' | 'outlined';

/**
 * Chip delete icon component
 */
interface DeleteIconProps {
  className?: string;
  onClick?: (event: React.MouseEvent) => void;
}

const DeleteIcon: React.FC<DeleteIconProps> = ({ className, onClick }) => (
  <svg
    className={className}
    onClick={onClick}
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="currentColor"
    focusable="false"
    aria-hidden="true"
  >
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
  </svg>
);

/**
 * Chip component props interface
 */
export interface ChipProps extends Omit<React.ButtonHTMLAttributes<HTMLDivElement>, 'color'> {
  /** Chip label */
  label: React.ReactNode;
  /** Avatar element to display before label */
  avatar?: React.ReactElement;
  /** Icon element to display before label */
  icon?: React.ReactElement;
  /** Delete icon handler */
  onDelete?: (event: React.MouseEvent) => void;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  /** Chip color */
  color?: ChipColor;
  /** Chip variant */
  variant?: ChipVariant;
  /** Chip size */
  size?: ChipSize;
  /** If true, chip is disabled */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  chipRef?: React.Ref<HTMLDivElement>;
}

/**
 * Get color styles based on color and theme
 */
const getColorStyles = (color: ChipColor, variant: ChipVariant, theme: EmotionTheme) => {
  const colorMap = {
    default: {
      main: theme.text.primary,
      light: theme.background.paper,
      dark: theme.divider,
      contrastText: theme.text.primary,
    },
    primary: theme.primary,
    secondary: theme.secondary,
    success: theme.success,
    error: theme.error,
    warning: theme.warning,
    info: theme.info,
  };

  const colors = colorMap[color];
  const isDark = theme.mode === 'dark';

  if (variant === 'filled') {
    return {
      backgroundColor: color === 'default' ? theme.background.default : colors.main,
      color: colors.contrastText,
      '&:hover': {
        backgroundColor: color === 'default' ? theme.background.paper : colors.dark,
      },
    };
  }

  // outlined variant
  return {
    backgroundColor: 'transparent',
    border: `1px solid ${color === 'default' ? theme.divider : colors.main}`,
    color: color === 'default' ? theme.text.primary : colors.main,
    '&:hover': {
      backgroundColor:
        color === 'default'
          ? isDark
            ? 'rgba(255, 255, 255, 0.08)'
            : 'rgba(0, 0, 0, 0.04)'
          : `${colors.main}${isDark ? '1a' : '08'}`,
    },
  };
};

/**
 * Get size styles
 */
const getSizeStyles = (size: ChipSize) => {
  const sizeMap = {
    small: {
      height: '24px',
      fontSize: '0.75rem',
      padding: '0 8px',
    },
    medium: {
      height: '32px',
      fontSize: '0.875rem',
      padding: '0 12px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled Chip component
 */
const StyledChip = styled('div')<ChipProps & { theme: EmotionTheme }>`
  /* Reset and base styles */
  box-sizing: border-box;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-weight: 500;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  text-decoration: none;
  transition: all ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  user-select: none;
  vertical-align: middle;

  /* Size styles */
  ${({ size }) => getSizeStyles(size || 'medium')}

  /* Color and variant styles */
  ${({ color, variant, theme }) => getColorStyles(color || 'default', variant || 'filled', theme)}

  /* Disabled state */
  ${({ disabled }) =>
    disabled
      ? `
    cursor: not-allowed;
    pointer-events: none;
    opacity: 0.5;
  `
      : ''}

  /* Clickable state */
  ${({ onClick, disabled }) =>
    onClick && !disabled
      ? `
    cursor: pointer;
    &:focus-visible {
      outline: 2px solid ${({ theme, color }) => (color === 'default' ? theme.text.primary : theme[color || 'primary'].main)};
      outline-offset: 2px;
    }
  `
      : ''}
`;

/**
 * Chip content area
 */
const ChipContent = styled.span<{ theme: EmotionTheme; hasAvatarOrIcon: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: ${({ theme, hasAvatarOrIcon }) => (hasAvatarOrIcon ? theme.spacing.xs : '0')};
  overflow: hidden;
  text-overflow: ellipsis;
`;

/**
 * Chip icon/avatar container
 */
const ChipIcon = styled.span<{ theme: EmotionTheme }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;

  &[data-avatar='true'] {
    margin-left: -6px;
  }

  &[data-icon='true'] {
    margin-left: -4px;
  }
`;

/**
 * Chip delete icon container
 */
const ChipDeleteIcon = styled.span<{ theme: EmotionTheme; clickable?: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: ${({ theme, clickable }) => (clickible ? theme.spacing.md : theme.spacing.xs)};
  margin-right: -4px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity ${({ theme }) => theme.transitions.duration.shorter}ms;

  &:hover {
    opacity: 1;
  }

  svg {
    width: 20px;
    height: 20px;
  }
`;

/**
 * Chip Component
 *
 * Chips represent complex entities in small blocks, such as a contact.
 * They can feature icons, avatars, and delete functionality.
 *
 * @example
 * ```tsx
 * // Basic chip
 * <Chip label="Basic" />
 *
 * // With color
 * <Chip label="Primary" color="primary" />
 * <Chip label="Success" color="success" variant="outlined" />
 *
 * // With avatar
 * <Chip
 *   label="John Doe"
 *   avatar={<Avatar>JD</Avatar>}
 * />
 *
 * // With icon
 * <Chip
 *   label="With Icon"
 *   icon={<Icon name="Check" />}
 * />
 *
 * // Deletable
 * <Chip label="Deletable" onDelete={() => console.log('deleted')} />
 *
 * // Clickable
 * <Chip label="Clickable" onClick={() => console.log('clicked')} />
 *
 * // Clickable and deletable
 * <Chip
 *   label="Interactive"
 *   onClick={() => console.log('clicked')}
 *   onDelete={() => console.log('deleted')}
 * />
 *
 * // Disabled
 * <Chip label="Disabled" disabled />
 *
 * // Small size
 * <Chip label="Small" size="small" />
 * ```
 */
export const Chip = React.forwardRef<HTMLDivElement, ChipProps>(
  (
    {
      label,
      avatar,
      icon,
      onDelete,
      onClick,
      color = 'default',
      variant = 'filled',
      size = 'medium',
      disabled = false,
      className,
      style,
      chipRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const hasAvatarOrIcon = Boolean(avatar || icon);

    const handleDelete = (event: React.MouseEvent) => {
      if (onDelete && !disabled) {
        onDelete(event);
      }
    };

    return (
      <StyledChip
        ref={ref || chipRef}
        theme={theme}
        color={color}
        variant={variant}
        size={size}
        disabled={disabled}
        onClick={onClick}
        className={className}
        style={style}
        {...(rest as React.ButtonHTMLAttributes<HTMLDivElement>)}
      >
        {avatar && (
          <ChipIcon theme={theme} data-avatar="true">
            {avatar}
          </ChipIcon>
        )}
        {icon && !avatar && (
          <ChipIcon theme={theme} data-icon="true">
            {icon}
          </ChipIcon>
        )}
        <ChipContent theme={theme} hasAvatarOrIcon={hasAvatarOrIcon}>
          {label}
        </ChipContent>
        {onDelete && !disabled && (
          <ChipDeleteIcon theme={theme} clickable={Boolean(onClick)} onClick={handleDelete}>
            <DeleteIcon />
          </ChipDeleteIcon>
        )}
      </StyledChip>
    );
  }
);

Chip.displayName = 'Chip';

export default Chip;
