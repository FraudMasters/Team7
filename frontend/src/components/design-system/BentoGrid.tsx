import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Breakpoint keys for responsive bento grid
 */
export type BentoBreakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Bento size type (number of columns/rows to span)
 */
export type BentoSize = number | 'auto' | 'full';

/**
 * Grid spacing type
 */
export type BentoSpacing = number | string;

/**
 * Common bento props interface
 */
export interface BaseBentoProps {
  /** Bento content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  bentoRef?: React.Ref<HTMLDivElement>;
}

/**
 * Span configuration for a single dimension (row or column)
 */
export interface BentoSpan {
  /** Number of cells to span */
  span?: BentoSize;
  /** Starting position (1-based) */
  start?: number;
  /** Ending position */
  end?: number;
}

/**
 * Responsive span configuration
 */
export type ResponsiveBentoSpan = BentoSize | BentoSpan | Record<BentoBreakpoint, BentoSize | BentoSpan>;

/**
 * Props for BentoGrid container
 */
export interface BentoGridProps extends BaseBentoProps {
  /** Spacing between grid items (0-10 or custom value) */
  spacing?: BentoSpacing;
  /** Number of columns in the grid (default: 4) */
  columns?: number | Record<BentoBreakpoint, number>;
  /** Minimum column width in pixels (for responsive columns) */
  minColumnWidth?: number;
  /** Maximum grid width */
  maxWidth?: string | number;
  /** If true, grid auto-fits columns based on minColumnWidth */
  autoFit?: boolean;
  /** Padding around the grid */
  padding?: BentoSpacing;
  /** Horizontal alignment */
  justifyItems?: 'start' | 'end' | 'center' | 'stretch';
  /** Vertical alignment */
  alignItems?: 'start' | 'end' | 'center' | 'stretch';
}

/**
 * Props for BentoItem
 */
export interface BentoItemProps extends BaseBentoProps {
  /** Column span configuration */
  col?: ResponsiveBentoSpan;
  /** Row span configuration */
  row?: ResponsiveBentoSpan;
  /** Order of the item */
  order?: number;
  /** If true, item grows to fill available space */
  grow?: boolean;
}

/**
 * Helper function to extract span value from BentoSize or BentoSpan
 */
const getSpanValue = (value: BentoSize | BentoSpan): BentoSize | BentoSpan => {
  if (typeof value === 'object' && 'span' in value) {
    return value.span ?? 1;
  }
  return value;
};

/**
 * Generate grid column/row style from span value
 */
const generateGridSpanStyle = (
  value: BentoSize | BentoSpan | undefined,
  propertyName: 'grid-column' | 'grid-row'
): string => {
  if (value === undefined) return '';
  if (value === 'auto') return `${propertyName}: auto;`;
  if (value === 'full') return `${propertyName}: 1 / -1;`;

  if (typeof value === 'number') {
    return `${propertyName}: span ${value} / span ${value};`;
  }

  // BentoSpan object with start/end
  if ('start' in value || 'end' in value) {
    const start = value.start ?? 'auto';
    const end = value.end ?? 'auto';
    return `${propertyName}: ${start} / ${end};`;
  }

  // BentoSpan with span property
  return `${propertyName}: span ${value.span ?? 1} / span ${value.span ?? 1};`;
};

/**
 * Generate responsive span styles
 */
const generateResponsiveSpanStyles = (
  prop: ResponsiveBentoSpan | undefined,
  theme: EmotionTheme,
  propertyName: 'grid-column' | 'grid-row'
): string => {
  if (prop === undefined) return '';

  const styles: string[] = [];

  // Handle responsive object
  if (typeof prop === 'object' && !('span' in prop) && !('start' in prop)) {
    // xs (default, mobile first)
    if (prop.xs !== undefined) {
      styles.push(generateGridSpanStyle(prop.xs, propertyName));
    }

    // sm
    if (prop.sm !== undefined) {
      styles.push(`@media (min-width: ${theme.breakpoints.values.sm}px) {`);
      styles.push(generateGridSpanStyle(prop.sm, propertyName));
      styles.push('}');
    }

    // md
    if (prop.md !== undefined) {
      styles.push(`@media (min-width: ${theme.breakpoints.values.md}px) {`);
      styles.push(generateGridSpanStyle(prop.md, propertyName));
      styles.push('}');
    }

    // lg
    if (prop.lg !== undefined) {
      styles.push(`@media (min-width: ${theme.breakpoints.values.lg}px) {`);
      styles.push(generateGridSpanStyle(prop.lg, propertyName));
      styles.push('}');
    }

    // xl
    if (prop.xl !== undefined) {
      styles.push(`@media (min-width: ${theme.breakpoints.values.xl}px) {`);
      styles.push(generateGridSpanStyle(prop.xl, propertyName));
      styles.push('}');
    }

    return styles.join('\n');
  }

  // Single value
  return generateGridSpanStyle(prop, propertyName);
};

/**
 * Generate spacing value from theme
 */
const getSpacingValue = (spacing: BentoSpacing, theme: EmotionTheme): string => {
  if (typeof spacing === 'number') {
    return `${spacing * theme.spacing.unit}px`;
  }
  return spacing;
};

/**
 * Styled BentoGrid Container
 */
const StyledBentoGrid = styled.div<BentoGridProps & { theme: EmotionTheme }>`
  box-sizing: border-box;
  display: grid;
  width: 100%;
  margin: 0 auto;

  /* Default columns */
  grid-template-columns: repeat(4, 1fr);

  /* Auto-fit with min column width */
  ${({ autoFit, minColumnWidth }) =>
    autoFit && minColumnWidth
      ? `grid-template-columns: repeat(auto-fit, minmax(${minColumnWidth}px, 1fr));`
      : ''}

  /* Custom columns if specified */
  ${({ columns, theme, autoFit, minColumnWidth }) => {
    if (autoFit && minColumnWidth) return ''; // Already handled above

    if (typeof columns === 'number') {
      return `grid-template-columns: repeat(${columns}, 1fr);`;
    }
    if (typeof columns === 'object') {
      const styles: string[] = [];
      // Default (xs)
      if (columns.xs) styles.push(`grid-template-columns: repeat(${columns.xs}, 1fr);`);
      // sm
      if (columns.sm) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.sm}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.sm}, 1fr);`);
        styles.push('}');
      }
      // md
      if (columns.md) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.md}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.md}, 1fr);`);
        styles.push('}');
      }
      // lg
      if (columns.lg) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.lg}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.lg}, 1fr);`);
        styles.push('}');
      }
      // xl
      if (columns.xl) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.xl}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.xl}, 1fr);`);
        styles.push('}');
      }
      return styles.join('\n');
    }
    return '';
  }}

  /* Max width */
  ${({ maxWidth }) => (maxWidth !== undefined ? `max-width: ${typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth};` : '')}

  /* Spacing */
  ${({ spacing, theme }) => {
    if (spacing !== undefined) {
      return `gap: ${getSpacingValue(spacing, theme)};`;
    }
    return 'gap: 16px;';
  }}

  /* Padding */
  ${({ padding, theme }) => {
    if (padding !== undefined) {
      return `padding: ${getSpacingValue(padding, theme)};`;
    }
    return '';
  }}

  /* Alignment */
  ${({ justifyItems }) =>
    justifyItems ? `justify-items: ${justifyItems};` : ''}
  ${({ alignItems }) =>
    alignItems ? `align-items: ${alignItems};` : ''}
`;

/**
 * Styled BentoItem
 */
const StyledBentoItem = styled.div<BentoItemProps & { theme: EmotionTheme }>`
  box-sizing: border-box;
  min-width: 0; /* Prevent grid blowout */

  /* Default: span 1 column, 1 row */
  grid-column: span 1;
  grid-row: span 1;

  /* Column span */
  ${({ col, theme }) => generateResponsiveSpanStyles(col, theme, 'grid-column')}

  /* Row span */
  ${({ row, theme }) => generateResponsiveSpanStyles(row, theme, 'grid-row')}

  /* Order */
  ${({ order }) => (order !== undefined ? `order: ${order};` : '')}

  /* Grow */
  ${({ grow }) =>
    grow ? `display: flex; flex-direction: column; flex: 1;` : ''}
`;

/**
 * BentoGrid Component
 *
 * A modern, responsive grid layout system inspired by bento box designs.
 * Supports items spanning multiple columns and rows with responsive breakpoints.
 *
 * @example
 * ```tsx
 * // Basic bento grid
 * <BentoGrid spacing={4}>
 *   <BentoItem col={{ span: 2 }}>Large card</BentoItem>
 *   <BentoItem>Small card</BentoItem>
 *   <BentoItem>Small card</BentoItem>
 *   <BentoItem row={{ span: 2 }}>Tall card</BentoItem>
 *   <BentoItem>Card</BentoItem>
 * </BentoGrid>
 *
 * // With responsive columns
 * <BentoGrid columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={4}>
 *   <BentoItem>Responsive item</BentoItem>
 * </BentoGrid>
 *
 * // Responsive item spanning
 * <BentoGrid columns={4} spacing={4}>
 *   <BentoItem col={{ xs: 1, md: 2, lg: 3 }}>Spans 1/2/3 columns</BentoItem>
 *   <BentoItem col="full">Full width item</BentoItem>
 * </BentoGrid>
 *
 * // Auto-fit columns
 * <BentoGrid autoFit minColumnWidth={250} spacing={4}>
 *   <BentoItem>Auto-fits to available space</BentoItem>
 * </BentoGrid>
 *
 * // Mixed column and row spans
 * <BentoGrid columns={4} spacing={4}>
 *   <BentoItem col={2} row={2}>2x2 large item</BentoItem>
 *   <BentoItem col={2}>Wide item</BentoItem>
 *   <BentoItem>Item</BentoItem>
 *   <BentoItem row={2}>Tall item</BentoItem>
 * </BentoGrid>
 *
 * // With positioning
 * <BentoGrid columns={4} spacing={4}>
 *   <BentoItem col={{ start: 2, end: 4 }}>From column 2 to 4</BentoItem>
 * </BentoGrid>
 *
 * // With alignment
 * <BentoGrid spacing={4} justifyItems="center" alignItems="center">
 *   <BentoItem>Centered content</BentoItem>
 * </BentoGrid>
 * ```
 */
export const BentoGrid = React.forwardRef<HTMLDivElement, BentoGridProps>(
  (
    {
      children,
      spacing,
      columns = 4,
      minColumnWidth,
      maxWidth,
      autoFit = false,
      padding,
      justifyItems,
      alignItems,
      className,
      style,
      bentoRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledBentoGrid
        ref={ref || bentoRef}
        theme={theme}
        spacing={spacing}
        columns={columns}
        minColumnWidth={minColumnWidth}
        maxWidth={maxWidth}
        autoFit={autoFit}
        padding={padding}
        justifyItems={justifyItems}
        alignItems={alignItems}
        className={className}
        style={style}
      >
        {children}
      </StyledBentoGrid>
    );
  }
);

BentoGrid.displayName = 'BentoGrid';

/**
 * BentoItem Component
 *
 * An item within a BentoGrid container.
 * Controls how many columns and rows the item spans at each breakpoint.
 *
 * @example
 * ```tsx
 * // Span 2 columns
 * <BentoItem col={2}>Wide card</BentoItem>
 *
 * // Span 2 rows
 * <BentoItem row={2}>Tall card</BentoItem>
 *
 * // Span both
 * <BentoItem col={2} row={2}>Large card</BentoItem>
 *
 * // Full width
 * <BentoItem col="full">Full width</BentoItem>
 *
 * // Auto width
 * <BentoItem col="auto">Auto width</BentoItem>
 *
 * // Responsive spanning
 * <BentoItem col={{ xs: 1, sm: 2, md: 3 }}>Responsive</BentoItem>
 *
 * // With span object
 * <BentoItem col={{ span: 2, start: 1 }}>Spans 2 from column 1</BentoItem>
 *
 * // With positioning
 * <BentoItem col={{ start: 2, end: 4 }}>From column 2 to 4</BentoItem>
 *
 * // Custom order
 * <BentoItem order={1}>First</BentoItem>
 *
 * // Grow to fill
 * <BentoItem grow>Grows vertically</BentoItem>
 * ```
 */
export const BentoItem = React.forwardRef<HTMLDivElement, BentoItemProps>(
  (
    {
      children,
      col,
      row,
      order,
      grow,
      className,
      style,
      bentoRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledBentoItem
        ref={ref || bentoRef}
        theme={theme}
        col={col}
        row={row}
        order={order}
        grow={grow}
        className={className}
        style={style}
      >
        {children}
      </StyledBentoItem>
    );
  }
);

BentoItem.displayName = 'BentoItem';

// Default export
export default BentoGrid;
