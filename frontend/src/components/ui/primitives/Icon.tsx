import React from 'react';
import { useEmotionTheme, EmotionTheme } from '../../../contexts/EmotionThemeContext';

/**
 * Icon size types
 * Maps to common icon sizes used in the application
 */
export type IconSize = number | 'inherit' | 'small' | 'medium' | 'large';

/**
 * Icon color types
 * Maps to theme colors for consistency
 */
export type IconColor =
  | 'inherit'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'disabled'
  | 'action'
  | string;

/**
 * Icon component props interface
 */
export interface IconProps {
  /** Icon name - maps to lucide-react icon names (e.g., 'User', 'Search', 'Menu') */
  name: string;
  /** Size of the icon in pixels or predefined size */
  size?: IconSize;
  /** Color of the icon */
  color?: IconColor;
  /** Additional CSS class name */
  className?: string;
  /** Inline styles that override defaults */
  style?: React.CSSProperties;
  /** Click handler */
  onClick?: React.MouseEventHandler<SVGSVGElement>;
  /** HTML title attribute for accessibility */
  title?: string;
  /** If true, applies primary color */
  colorPrimary?: boolean;
  /** If true, applies secondary color */
  colorSecondary?: boolean;
  /** If true, applies error color */
  colorError?: boolean;
  /** If true, applies action color (default icon color) */
  colorAction?: boolean;
  /** If true, disables the icon */
  disabled?: boolean;
}

/**
 * Convert size prop to pixel value
 */
const getSizeValue = (size: IconSize): number | string => {
  if (size === 'inherit') {
    return 'inherit';
  }
  if (typeof size === 'number') {
    return size;
  }
  switch (size) {
    case 'small':
      return 20;
    case 'medium':
      return 24;
    case 'large':
      return 32;
    default:
      return 24;
  }
};

/**
 * Get color value from color prop
 */
const getColorValue = (color: IconColor | undefined, theme: EmotionTheme): string => {
  if (!color) {
    return theme.text.secondary; // Default to action color
  }

  // If it's a custom color string, return as-is
  if (
    ![
      'inherit',
      'primary',
      'secondary',
      'success',
      'error',
      'warning',
      'info',
      'disabled',
      'action',
    ].includes(color)
  ) {
    return color;
  }

  // Map color names to theme values
  switch (color) {
    case 'inherit':
      return 'inherit';
    case 'primary':
      return theme.primary.main;
    case 'secondary':
      return theme.secondary.main;
    case 'success':
      return theme.success.main;
    case 'error':
      return theme.error.main;
    case 'warning':
      return theme.warning.main;
    case 'info':
      return theme.info.main;
    case 'disabled':
      return theme.text.disabled;
    case 'action':
      return theme.text.secondary;
    default:
      return theme.text.secondary;
  }
};

/**
 * Icon component
 *
 * A wrapper around lucide-react icons that provides a MUI-compatible API.
 * Uses dynamic import for icon resolution to support string-based names.
 *
 * @example
 * ```tsx
 * <Icon name="User" size={24} color="primary" />
 * <Icon name="Search" size="medium" />
 * <Icon name="Menu" size={32} color="inherit" />
 * ```
 */
const IconInternal: React.FC<IconProps> = ({
  name,
  size = 'medium',
  color,
  className,
  style,
  onClick,
  title,
  colorPrimary,
  colorSecondary,
  colorError,
  colorAction,
  disabled = false,
}) => {
  const theme = useEmotionTheme();

  // Handle legacy boolean color props
  const effectiveColor = React.useMemo(() => {
    if (colorPrimary) return 'primary';
    if (colorSecondary) return 'secondary';
    if (colorError) return 'error';
    if (colorAction) return 'action';
    return color;
  }, [color, colorPrimary, colorSecondary, colorError, colorAction]);

  // Dynamic icon component - loaded on first use
  const [IconComponent, setIconComponent] = React.useState<React.ComponentType<any> | null>(null);
  const [loadError, setLoadError] = React.useState(false);

  React.useEffect(() => {
    let isMounted = true;

    const loadIcon = async () => {
      try {
        // Convert icon name to various possible formats
        const formats = [
          name, // As provided (e.g., 'User', 'help-circle')
          name.charAt(0).toUpperCase() + name.slice(1), // Capitalized
          name
            .split('-')
            .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
            .join(''), // PascalCase from kebab-case
        ];

        // Try each format until we find a match
        for (const iconName of formats) {
          try {
            const lucideReact = await import('lucide-react');
            const icon = (lucideReact as any)[iconName];

            if (icon && isMounted) {
              setIconComponent(() => icon);
              setLoadError(false);
              return;
            }
          } catch (e) {
            // Continue to next format
            continue;
          }
        }

        // If no icon found, set error state
        if (isMounted) {
          setLoadError(true);
        }
      } catch (error) {
        if (isMounted) {
          setLoadError(true);
        }
      }
    };

    loadIcon();

    return () => {
      isMounted = false;
    };
  }, [name]);

  // Show fallback or placeholder while loading or on error
  if (!IconComponent) {
    if (loadError) {
      // Fallback icon when icon not found
      return (
        <svg
          width={getSizeValue(size)}
          height={getSizeValue(size)}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={className}
          style={{
            color: disabled ? theme.text.disabled : getColorValue(effectiveColor, theme),
            cursor: onClick ? 'pointer' : 'default',
            opacity: disabled ? 0.5 : 1,
            pointerEvents: disabled ? 'none' : 'auto',
            ...style,
          }}
          onClick={onClick}
          aria-label={title || name}
          role={onClick ? 'button' : 'img'}
          aria-disabled={disabled}
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    }

    // Loading placeholder
    return (
      <span
        style={{
          display: 'inline-block',
          width: typeof getSizeValue(size) === 'number' ? getSizeValue(size) as number : 24,
          height: typeof getSizeValue(size) === 'number' ? getSizeValue(size) as number : 24,
          ...style,
        }}
        aria-label={title || name}
        role="img"
      />
    );
  }

  const sizeValue = getSizeValue(size);
  const colorValue = getColorValue(effectiveColor, theme);

  const iconStyle: React.CSSProperties = {
    color: disabled ? theme.text.disabled : colorValue,
    cursor: onClick ? 'pointer' : 'default',
    opacity: disabled ? 0.5 : 1,
    pointerEvents: disabled ? 'none' : 'auto',
    ...style,
  };

  return (
    <IconComponent
      size={sizeValue}
      className={className}
      style={iconStyle}
      onClick={onClick}
      aria-label={title || name}
      role={onClick ? 'button' : 'img'}
      aria-disabled={disabled}
    />
  );
};

/**
 * Icon display name for debugging
 */
IconInternal.displayName = 'Icon';

const Icon = React.memo(IconInternal);
export { Icon };
export default Icon;
