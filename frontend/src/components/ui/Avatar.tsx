import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Avatar size types
 */
export type AvatarSize = 'small' | 'medium' | 'large';

/**
 * Avatar variant types
 */
export type AvatarVariant = 'circular' | 'rounded' | 'square';

/**
 * Avatar component props interface
 */
export interface AvatarProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'size'> {
  /** Avatar content - can be string (for initials), React node, or image src */
  children?: React.ReactNode;
  /** Alternative text for images */
  alt?: string;
  /** Image source URL */
  src?: string;
  /** Image source set for responsive images */
  srcSet?: string;
  /** Avatar size */
  size?: AvatarSize;
  /** Avatar variant */
  variant?: AvatarVariant;
  /** Fallback text to show if image fails to load */
  fallback?: string;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  avatarRef?: React.Ref<HTMLDivElement | HTMLImageElement>;
  /** Handler for image load error */
  onError?: (event: React.SyntheticEvent<HTMLImageElement, Event>) => void;
}

/**
 * Get size styles
 */
const getSizeStyles = (size: AvatarSize) => {
  const sizeMap = {
    small: {
      width: '24px',
      height: '24px',
      fontSize: '0.75rem',
    },
    medium: {
      width: '40px',
      height: '40px',
      fontSize: '1rem',
    },
    large: {
      width: '56px',
      height: '56px',
      fontSize: '1.5rem',
    },
  };

  return sizeMap[size];
};

/**
 * Get variant styles
 */
const getVariantStyles = (variant: AvatarVariant, theme: EmotionTheme) => {
  const variantMap = {
    circular: {
      borderRadius: '50%',
    },
    rounded: {
      borderRadius: theme.borderRadius.md,
    },
    square: {
      borderRadius: 0,
    },
  };

  return variantMap[variant];
};

/**
 * Avatar root container
 */
const AvatarRoot = styled('div')<{
  theme: EmotionTheme;
  size: AvatarSize;
  variant: AvatarVariant;
}>`
  /* Base styles */
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};
  overflow: hidden;
  user-select: none;

  /* Size styles */
  ${({ size }) => getSizeStyles(size)}

  /* Variant styles */
  ${({ variant, theme }) => getVariantStyles(variant, theme)}

  /* Color */
  background-color: ${({ theme }) => theme.palette.grey[400]};
  color: ${({ theme }) => theme.palette.grey[700]};

  /* Dark mode adjustments */
  @media (prefers-color-scheme: dark) {
    background-color: ${({ theme }) => theme.palette.grey[700]};
    color: ${({ theme }) => theme.palette.grey[200]};
  }
`;

/**
 * Avatar image
 */
const AvatarImage = styled('img')<{
  theme: EmotionTheme;
  variant: AvatarVariant;
}>`
  width: 100%;
  height: 100%;
  object-fit: cover;
  text-align: center;
  text-indent: 10000px;

  /* Variant styles */
  ${({ variant, theme }) => getVariantStyles(variant, theme)}
`;

/**
 * Avatar fallback (initials)
 */
const AvatarFallback = styled('div')<{
  theme: EmotionTheme;
}>`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
`;

/**
 * Generate initials from name
 */
const getInitials = (name: string, maxInitials: number = 2): string => {
  const parts = name.trim().split(' ');
  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase();
  }
  return parts
    .slice(0, maxInitials)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
};

/**
 * Generate color from string
 */
const stringToColor = (str: string, theme: EmotionTheme): string => {
  const colors = [
    theme.primary.main,
    theme.secondary.main,
    theme.success.main,
    theme.warning.main,
    theme.info.main,
  ];

  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  const index = Math.abs(hash % colors.length);
  return colors[index];
};

/**
 * Avatar Component
 *
 * Avatars are found throughout the web, representing users, organizations,
 * and other entities. They can display images, icons, or initials.
 *
 * @example
 * ```tsx
 * // Image avatar
 * <Avatar
 *   src="/path/to/image.jpg"
 *   alt="John Doe"
 * />
 *
 * // Initials avatar
 * <Avatar>JD</Avatar>
 *
 * // Auto-generated initials from name
 * <Avatar fallback="John Doe">
 *   <img src="/path/to/image.jpg" alt="John" />
 * </Avatar>
 *
 * // Different sizes
 * <Avatar size="small">AB</Avatar>
 * <Avatar size="medium">CD</Avatar>
 * <Avatar size="large">EF</Avatar>
 *
 * // Different variants
 * <Avatar variant="circular">A</Avatar>
 * <Avatar variant="rounded">B</Avatar>
 * <Avatar variant="square">C</Avatar>
 *
 * // With icon
 * <Avatar>
 *   <Icon name="Person" />
 * </Avatar>
 *
 * // With fallback
 * <Avatar fallback="John Doe" />
 * ```
 */
export const Avatar = React.forwardRef<HTMLDivElement | HTMLImageElement, AvatarProps>(
  (
    {
      children,
      alt,
      src,
      srcSet,
      size = 'medium',
      variant = 'circular',
      fallback: fallbackProp,
      className,
      style,
      avatarRef,
      onError,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const [hasError, setHasError] = React.useState(false);
    const [imageLoaded, setImageLoaded] = React.useState(false);

    // If src is provided and no error, show image
    if (src && !hasError) {
      return (
        <AvatarRoot
          ref={ref as React.RefObject<HTMLDivElement>}
          theme={theme}
          size={size}
          variant={variant}
          className={className}
          style={style}
        >
          <AvatarImage
            ref={avatarRef as React.RefObject<HTMLImageElement>}
            theme={theme}
            variant={variant}
            src={src}
            srcSet={srcSet}
            alt={alt}
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              setHasError(true);
              onError?.(e);
            }}
            {...(rest as React.ImgHTMLAttributes<HTMLImageElement>)}
          />
        </AvatarRoot>
      );
    }

    // Render content (initials or children)
    let content: React.ReactNode = children;

    // If children is a string, render as initials
    if (typeof children === 'string') {
      const initials = getInitials(children);
      const backgroundColor = stringToColor(children, theme);

      content = (
        <AvatarFallback
          theme={theme}
          style={{ backgroundColor, color: theme.palette.common.white }}
        >
          {initials}
        </AvatarFallback>
      );
    }
    // If fallback provided and no children, use fallback
    else if (!children && fallbackProp) {
      const initials = getInitials(fallbackProp);
      const backgroundColor = stringToColor(fallbackProp, theme);

      content = (
        <AvatarFallback
          theme={theme}
          style={{ backgroundColor, color: theme.palette.common.white }}
        >
          {initials}
        </AvatarFallback>
      );
    }
    // If children is not a string, render as-is (icon, etc.)
    else if (children) {
      content = <AvatarFallback theme={theme}>{children}</AvatarFallback>;
    }
    // Default placeholder
    else {
      content = (
        <AvatarFallback theme={theme}>
          <span
            style={{
              fontSize: '1.5rem',
              opacity: 0.5,
            }}
          >
            ?
          </span>
        </AvatarFallback>
      );
    }

    return (
      <AvatarRoot
        ref={ref as React.RefObject<HTMLDivElement>}
        theme={theme}
        size={size}
        variant={variant}
        className={className}
        style={style}
      >
        {content}
      </AvatarRoot>
    );
  }
);

Avatar.displayName = 'Avatar';

export default Avatar;
