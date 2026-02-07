import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../../contexts/EmotionThemeContext';

/**
 * Typography variant types
 * Maps to MUI's typography variants for migration compatibility
 */
export type TypographyVariant =
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'h5'
  | 'h6'
  | 'subtitle1'
  | 'subtitle2'
  | 'body1'
  | 'body2'
  | 'caption'
  | 'button'
  | 'overline';

/**
 * Typography color types
 */
export type TypographyColor =
  | 'inherit'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'textPrimary'
  | 'textSecondary'
  | 'disabled';

/**
 * Typography component props interface
 */
export interface TypographyProps {
  /** The content of the typography element */
  children?: React.ReactNode;
  /** HTML component to render as */
  component?: React.ElementType;
  /** Override or extend the styles applied to the component */
  className?: string;
  /** The color of the component */
  color?: TypographyColor | string;
  /** If true, the text will have a bottom margin */
  gutterBottom?: boolean;
  /** If true, the text will not wrap, but instead will truncate with a text overflow ellipsis */
  noWrap?: boolean;
  /** The variant prop defines the style of the typography */
  variant?: TypographyVariant;
  /** The component maps the variant prop to a range of different HTML element types */
  variantMapping?: Partial<Record<TypographyVariant, React.ElementType>>;
  /** Inline styles that override system props */
  style?: React.CSSProperties;
  /** Click handler */
  onClick?: React.MouseEventHandler;
  /** Reference to the underlying DOM element */
  ref?: React.Ref<HTMLElement>;
  /** Text align property */
  align?: 'inherit' | 'left' | 'center' | 'right' | 'justify';
}

/**
 * Get default HTML element for variant
 */
const getDefaultElement = (variant: TypographyVariant): React.ElementType => {
  switch (variant) {
    case 'h1':
      return 'h1';
    case 'h2':
      return 'h2';
    case 'h3':
      return 'h3';
    case 'h4':
      return 'h4';
    case 'h5':
      return 'h5';
    case 'h6':
      return 'h6';
    case 'subtitle1':
      return 'h6';
    case 'subtitle2':
      return 'h6';
    case 'body1':
      return 'p';
    case 'body2':
      return 'p';
    case 'caption':
      return 'span';
    case 'button':
      return 'span';
    case 'overline':
      return 'span';
    default:
      return 'span';
  }
};

/**
 * Variant mapping to typography styles
 */
const getVariantStyles = (variant: TypographyVariant, theme: EmotionTheme) => {
  const { typography } = theme;

  switch (variant) {
    case 'h1':
      return {
        fontSize: typography.fontSize['6xl'],
        fontWeight: typography.fontWeight.light,
        lineHeight: typography.lineHeight.tight,
        letterSpacing: typography.letterSpacing.tight,
      };
    case 'h2':
      return {
        fontSize: typography.fontSize['5xl'],
        fontWeight: typography.fontWeight.light,
        lineHeight: typography.lineHeight.tight,
        letterSpacing: typography.letterSpacing.tight,
      };
    case 'h3':
      return {
        fontSize: typography.fontSize['4xl'],
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'h4':
      return {
        fontSize: typography.fontSize['3xl'],
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'h5':
      return {
        fontSize: typography.fontSize['2xl'],
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'h6':
      return {
        fontSize: typography.fontSize.xl,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'subtitle1':
      return {
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.relaxed,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'subtitle2':
      return {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.relaxed,
        letterSpacing: typography.letterSpacing.wide,
      };
    case 'body1':
      return {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.relaxed,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'body2':
      return {
        fontSize: typography.fontSize.sm,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.relaxed,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'caption':
      return {
        fontSize: typography.fontSize.xs,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.normal,
      };
    case 'button':
      return {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.wide,
        textTransform: 'uppercase' as const,
      };
    case 'overline':
      return {
        fontSize: typography.fontSize.xs,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
        letterSpacing: typography.letterSpacing.wide,
        textTransform: 'uppercase' as const,
      };
    default:
      return {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.normal,
        lineHeight: typography.lineHeight.normal,
      };
  }
};

/**
 * Get color value from color prop
 */
const getColorValue = (color: TypographyColor | string, theme: EmotionTheme): string => {
  // If it's a custom color string, return as-is
  if (!theme[color as keyof EmotionTheme] && typeof color === 'string') {
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
    case 'textPrimary':
      return theme.text.primary;
    case 'textSecondary':
      return theme.text.secondary;
    case 'disabled':
      return theme.text.disabled;
    default:
      return theme.text.primary;
  }
};

/**
 * Styled Typography Component
 */
const StyledTypography = styled('span')<TypographyProps>(
  {
    // Default styles
    margin: 0,
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const variant = props.variant || 'body1';
    const styles: Record<string, any> = {
      ...getVariantStyles(variant, theme),
    };

    // Color
    if (props.color) {
      styles.color = getColorValue(props.color, theme);
    }

    // Text align
    if (props.align) {
      styles.textAlign = props.align;
    }

    // No wrap
    if (props.noWrap) {
      styles.overflow = 'hidden';
      styles.textOverflow = 'ellipsis';
      styles.whiteSpace = 'nowrap';
    }

    // Gutter bottom
    if (props.gutterBottom) {
      styles.marginBottom = '0.35em';
    }

    return styles;
  }
);

/**
 * Typography Component
 *
 * A component for rendering text with consistent styling. Supports multiple variants
 * for different text types (headings, body, captions, etc.) and color options.
 *
 * @example
 * ```tsx
 * // Headings
 * <Typography variant="h1">Heading 1</Typography>
 * <Typography variant="h2">Heading 2</Typography>
 * <Typography variant="h3">Heading 3</Typography>
 *
 * // Body text
 * <Typography variant="body1">Main body text</Typography>
 * <Typography variant="body2">Secondary body text</Typography>
 *
 * // Subtitles
 * <Typography variant="subtitle1">Large subtitle</Typography>
 * <Typography variant="subtitle2">Small subtitle</Typography>
 *
 * // With colors
 * <Typography variant="h6" color="primary">Primary color</Typography>
 * <Typography variant="body2" color="error">Error message</Typography>
 *
 * // With gutter bottom
 * <Typography variant="h4" gutterBottom>
 *   Section heading with bottom margin
 * </Typography>
 *
 * // No wrap (truncates with ellipsis)
 * <Typography variant="body1" noWrap>
 *   This text will not wrap and will show ellipsis if too long
 * </Typography>
 *
 * // Text alignment
 * <Typography variant="h3" align="center">Centered heading</Typography>
 * ```
 */
const Typography = React.forwardRef<HTMLElement, TypographyProps>(
  (
    {
      component,
      children,
      className,
      color,
      gutterBottom = false,
      noWrap = false,
      variant = 'body1',
      variantMapping,
      style,
      onClick,
      align,
      ...rest
    },
    ref
  ) => {
    // Determine which component to render
    const mappedComponent = variantMapping?.[variant];
    const Component = component || mappedComponent || getDefaultElement(variant);

    return (
      <StyledTypography
        as={Component}
        className={className}
        style={style}
        onClick={onClick}
        ref={ref as any}
        variant={variant}
        color={color}
        gutterBottom={gutterBottom}
        noWrap={noWrap}
        align={align}
        {...rest}
      >
        {children}
      </StyledTypography>
    );
  }
);

Typography.displayName = 'Typography';

export default Typography;
