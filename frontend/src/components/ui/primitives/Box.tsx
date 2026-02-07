import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../../contexts/EmotionThemeContext';

/**
 * Spacing utility type - can be a number, string, or array for responsive values
 */
export type SpacingValue =
  | number
  | string
  | [number, number?]
  | [number, number?, number?]
  | [number, number?, number?, number?];

/**
 * System style props interface
 * Supports common CSS properties with shorthand notation
 */
export interface SystemStyleProps {
  /** Spacing properties - can use theme spacing units (0-8) or pixel values */
  m?: SpacingValue;
  mt?: SpacingValue;
  mr?: SpacingValue;
  mb?: SpacingValue;
  ml?: SpacingValue;
  mx?: SpacingValue;
  my?: SpacingValue;
  p?: SpacingValue;
  pt?: SpacingValue;
  pr?: SpacingValue;
  pb?: SpacingValue;
  pl?: SpacingValue;
  px?: SpacingValue;
  py?: SpacingValue;

  /** Display property */
  display?: React.CSSProperties['display'];

  /** Flexbox properties */
  flexDirection?: React.CSSProperties['flexDirection'];
  justifyContent?: React.CSSProperties['justifyContent'];
  alignItems?: React.CSSProperties['alignItems'];
  flexWrap?: React.CSSProperties['flexWrap'];
  flexGrow?: React.CSSProperties['flexGrow'];
  flexShrink?: React.CSSProperties['flexShrink'];
  flexBasis?: React.CSSProperties['flexBasis'];
  gap?: SpacingValue;
  flex?: React.CSSProperties['flex'];

  /** Grid properties */
  gridTemplateColumns?: React.CSSProperties['gridTemplateColumns'];
  gridTemplateRows?: React.CSSProperties['gridTemplateRows'];
  gridColumn?: React.CSSProperties['gridColumn'];
  gridRow?: React.CSSProperties['gridRow'];
  gridAutoFlow?: React.CSSProperties['gridAutoFlow'];

  /** Layout properties */
  width?: React.CSSProperties['width'];
  height?: React.CSSProperties['height'];
  maxWidth?: React.CSSProperties['maxWidth'];
  maxHeight?: React.CSSProperties['maxHeight'];
  minWidth?: React.CSSProperties['minWidth'];
  minHeight?: React.CSSProperties['minHeight'];

  /** Position properties */
  position?: React.CSSProperties['position'];
  top?: SpacingValue | 'auto' | string;
  right?: SpacingValue | 'auto' | string;
  bottom?: SpacingValue | 'auto' | string;
  left?: SpacingValue | 'auto' | string;
  zIndex?: React.CSSProperties['zIndex'];

  /** Color properties */
  color?: string;
  bgcolor?: string;
  backgroundColor?: string;
  opacity?: React.CSSProperties['opacity'];

  /** Typography properties */
  fontSize?: React.CSSProperties['fontSize'];
  fontWeight?: React.CSSProperties['fontWeight'];
  lineHeight?: React.CSSProperties['lineHeight'];
  textAlign?: React.CSSProperties['textAlign'];
  textTransform?: React.CSSProperties['textTransform'];
  letterSpacing?: React.CSSProperties['letterSpacing'];

  /** Border properties */
  border?: React.CSSProperties['border'];
  borderTop?: React.CSSProperties['borderTop'];
  borderRight?: React.CSSProperties['borderRight'];
  borderBottom?: React.CSSProperties['borderBottom'];
  borderLeft?: React.CSSProperties['borderLeft'];
  borderColor?: string;
  borderRadius?: SpacingValue | string;
  borderWidth?: React.CSSProperties['borderWidth'];

  /** Shadow and background */
  boxShadow?: string;
  background?: React.CSSProperties['background'];
  backgroundImage?: React.CSSProperties['backgroundImage'];
  backgroundSize?: React.CSSProperties['backgroundSize'];
  backgroundPosition?: React.CSSProperties['backgroundPosition'];

  /** Overflow */
  overflow?: React.CSSProperties['overflow'];
  overflowX?: React.CSSProperties['overflowX'];
  overflowY?: React.CSSProperties['overflowY'];

  /** Other common properties */
  cursor?: React.CSSProperties['cursor'];
  transition?: React.CSSProperties['transition'];
  transform?: React.CSSProperties['transform'];

  /** Responsive breakpoints */
  xs?: Partial<SystemStyleProps>;
  sm?: Partial<SystemStyleProps>;
  md?: Partial<SystemStyleProps>;
  lg?: Partial<SystemStyleProps>;
  xl?: Partial<SystemStyleProps>;
}

/**
 * Box component props interface
 */
export interface BoxProps extends SystemStyleProps {
  /** Child elements */
  children?: React.ReactNode;
  /** HTML component to render as */
  component?: React.ElementType;
  /** Additional CSS class name */
  className?: string;
  /** Inline styles that override system props */
  style?: React.CSSProperties;
  /** Click handler */
  onClick?: React.MouseEventHandler;
  /** Reference to the underlying DOM element */
  as?: React.ElementType;
}

/**
 * Convert spacing value to CSS string
 */
const parseSpacing = (
  value: SpacingValue | string | undefined,
  theme: EmotionTheme
): string | number => {
  if (value === undefined) return '';

  // If already a string with units, return as-is
  if (typeof value === 'string') {
    // Check if it's a theme spacing value
    if (value in theme.spacing) {
      return theme.spacing[value as keyof typeof theme.spacing] as string;
    }
    return value;
  }

  // If it's a number, multiply by base spacing unit (8px)
  if (typeof value === 'number') {
    return `${value * 8}px`;
  }

  // If it's an array, handle multiple values
  if (Array.isArray(value)) {
    return value
      .map((v) => (typeof v === 'number' ? `${v * 8}px` : v))
      .join(' ');
  }

  return value;
};

/**
 * Create media query for breakpoint
 */
const createMediaQuery = (breakpoint: string, styles: Record<string, any>) => {
  return `@media (min-width: ${breakpoint}) {
    ${Object.entries(styles)
      .map(([key, value]) => `${key}: ${value};`)
      .join('\n      ')}
  }`;
};

/**
 * Styled Box Component
 *
 * A flexible container component that provides a comprehensive set of system props
 * for styling, similar to MUI's Box component. Uses Emotion for CSS-in-JS styling.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <Box p={2} bgcolor="primary.main">
 *   Content with padding
 * </Box>
 *
 * // Flexbox layout
 * <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
 *   <Box>Left</Box>
 *   <Box>Right</Box>
 * </Box>
 *
 * // Grid layout
 * <Box display="grid" gridTemplateColumns="repeat(3, 1fr)" gap={2}>
 *   <Box>Item 1</Box>
 *   <Box>Item 2</Box>
 *   <Box>Item 3</Box>
 * </Box>
 *
 * // Responsive styles
 * <Box p={{ xs: 1, md: 2, lg: 3 }}>
 *   Responsive padding
 * </Box>
 *
 * // As a custom component
 * <Box component="a" href="#" color="primary.main">
 *   Link styled as box
 * </Box>
 * ```
 */
const StyledBox = styled('div')<BoxProps>(
  {
    boxSizing: 'border-box',
    margin: 0,
    minWidth: 0, // Prevent flex items from overflowing
  },
  (props) => {
    const theme = useEmotionTheme().theme;
    const styles: Record<string, any> = {};

    // Spacing - margin
    if (props.m !== undefined) styles.margin = parseSpacing(props.m, theme);
    if (props.mt !== undefined) styles.marginTop = parseSpacing(props.mt, theme);
    if (props.mr !== undefined) styles.marginRight = parseSpacing(props.mr, theme);
    if (props.mb !== undefined) styles.marginBottom = parseSpacing(props.mb, theme);
    if (props.ml !== undefined) styles.marginLeft = parseSpacing(props.ml, theme);
    if (props.mx !== undefined) {
      const val = parseSpacing(props.mx, theme);
      styles.marginLeft = val;
      styles.marginRight = val;
    }
    if (props.my !== undefined) {
      const val = parseSpacing(props.my, theme);
      styles.marginTop = val;
      styles.marginBottom = val;
    }

    // Spacing - padding
    if (props.p !== undefined) styles.padding = parseSpacing(props.p, theme);
    if (props.pt !== undefined) styles.paddingTop = parseSpacing(props.pt, theme);
    if (props.pr !== undefined) styles.paddingRight = parseSpacing(props.pr, theme);
    if (props.pb !== undefined) styles.paddingBottom = parseSpacing(props.pb, theme);
    if (props.pl !== undefined) styles.paddingLeft = parseSpacing(props.pl, theme);
    if (props.px !== undefined) {
      const val = parseSpacing(props.px, theme);
      styles.paddingLeft = val;
      styles.paddingRight = val;
    }
    if (props.py !== undefined) {
      const val = parseSpacing(props.py, theme);
      styles.paddingTop = val;
      styles.paddingBottom = val;
    }

    // Display
    if (props.display !== undefined) styles.display = props.display;

    // Flexbox
    if (props.flexDirection !== undefined) styles.flexDirection = props.flexDirection;
    if (props.justifyContent !== undefined) styles.justifyContent = props.justifyContent;
    if (props.alignItems !== undefined) styles.alignItems = props.alignItems;
    if (props.flexWrap !== undefined) styles.flexWrap = props.flexWrap;
    if (props.flexGrow !== undefined) styles.flexGrow = props.flexGrow;
    if (props.flexShrink !== undefined) styles.flexShrink = props.flexShrink;
    if (props.flexBasis !== undefined) styles.flexBasis = props.flexBasis;
    if (props.gap !== undefined) styles.gap = parseSpacing(props.gap, theme);
    if (props.flex !== undefined) styles.flex = props.flex;

    // Grid
    if (props.gridTemplateColumns !== undefined)
      styles.gridTemplateColumns = props.gridTemplateColumns;
    if (props.gridTemplateRows !== undefined) styles.gridTemplateRows = props.gridTemplateRows;
    if (props.gridColumn !== undefined) styles.gridColumn = props.gridColumn;
    if (props.gridRow !== undefined) styles.gridRow = props.gridRow;
    if (props.gridAutoFlow !== undefined) styles.gridAutoFlow = props.gridAutoFlow;

    // Layout
    if (props.width !== undefined) styles.width = props.width;
    if (props.height !== undefined) styles.height = props.height;
    if (props.maxWidth !== undefined) styles.maxWidth = props.maxWidth;
    if (props.maxHeight !== undefined) styles.maxHeight = props.maxHeight;
    if (props.minWidth !== undefined) styles.minWidth = props.minWidth;
    if (props.minHeight !== undefined) styles.minHeight = props.minHeight;

    // Position
    if (props.position !== undefined) styles.position = props.position;
    if (props.top !== undefined) styles.top = parseSpacing(props.top as SpacingValue, theme);
    if (props.right !== undefined) styles.right = parseSpacing(props.right as SpacingValue, theme);
    if (props.bottom !== undefined) styles.bottom = parseSpacing(props.bottom as SpacingValue, theme);
    if (props.left !== undefined) styles.left = parseSpacing(props.left as SpacingValue, theme);
    if (props.zIndex !== undefined) styles.zIndex = props.zIndex;

    // Colors
    if (props.color !== undefined) styles.color = props.color;
    if (props.bgcolor !== undefined) styles.backgroundColor = props.bgcolor;
    if (props.backgroundColor !== undefined) styles.backgroundColor = props.backgroundColor;
    if (props.opacity !== undefined) styles.opacity = props.opacity;

    // Typography
    if (props.fontSize !== undefined) styles.fontSize = props.fontSize;
    if (props.fontWeight !== undefined) styles.fontWeight = props.fontWeight;
    if (props.lineHeight !== undefined) styles.lineHeight = props.lineHeight;
    if (props.textAlign !== undefined) styles.textAlign = props.textAlign;
    if (props.textTransform !== undefined) styles.textTransform = props.textTransform;
    if (props.letterSpacing !== undefined) styles.letterSpacing = props.letterSpacing;

    // Border
    if (props.border !== undefined) styles.border = props.border;
    if (props.borderTop !== undefined) styles.borderTop = props.borderTop;
    if (props.borderRight !== undefined) styles.borderRight = props.borderRight;
    if (props.borderBottom !== undefined) styles.borderBottom = props.borderBottom;
    if (props.borderLeft !== undefined) styles.borderLeft = props.borderLeft;
    if (props.borderColor !== undefined) styles.borderColor = props.borderColor;
    if (props.borderRadius !== undefined) {
      styles.borderRadius = parseSpacing(props.borderRadius as SpacingValue, theme);
    }
    if (props.borderWidth !== undefined) styles.borderWidth = props.borderWidth;

    // Shadow and background
    if (props.boxShadow !== undefined) styles.boxShadow = props.boxShadow;
    if (props.background !== undefined) styles.background = props.background;
    if (props.backgroundImage !== undefined) styles.backgroundImage = props.backgroundImage;
    if (props.backgroundSize !== undefined) styles.backgroundSize = props.backgroundSize;
    if (props.backgroundPosition !== undefined) styles.backgroundPosition = props.backgroundPosition;

    // Overflow
    if (props.overflow !== undefined) styles.overflow = props.overflow;
    if (props.overflowX !== undefined) styles.overflowX = props.overflowX;
    if (props.overflowY !== undefined) styles.overflowY = props.overflowY;

    // Other
    if (props.cursor !== undefined) styles.cursor = props.cursor;
    if (props.transition !== undefined) styles.transition = props.transition;
    if (props.transform !== undefined) styles.transform = props.transform;

    return styles;
  }
);

/**
 * Box Component
 *
 * A versatile container component that provides system props for common styling needs.
 * Acts as a foundational primitive for layout and composition.
 *
 * @param props - Box props
 * @returns Box component
 */
const Box = React.forwardRef<HTMLElement, BoxProps>(
  ({ component, as, children, className, style, onClick, ...systemProps }, ref) => {
    // Determine which component to render
    const Component = component || as || 'div';

    return (
      <StyledBox
        as={Component}
        className={className}
        style={style}
        onClick={onClick}
        ref={ref as any}
        {...systemProps}
      >
        {children}
      </StyledBox>
    );
  }
);

Box.displayName = 'Box';

export default Box;
