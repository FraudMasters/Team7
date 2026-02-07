import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Breakpoint keys for responsive grid
 */
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Grid size type (1-12 columns or 'auto')
 */
export type GridSize = boolean | number | 'auto';

/**
 * Grid spacing type
 */
export type GridSpacing = number | string;

/**
 * Common grid props interface
 */
export interface BaseGridProps {
  /** Grid content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  gridRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Grid container
 */
export interface GridContainerProps extends BaseGridProps {
  /** Spacing between grid items (0-10 or custom value) */
  spacing?: GridSpacing;
  /** Direction of the grid (row or column) */
  direction?: 'row' | 'column';
  /** Wrap items to next line */
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
  /** Alignment of items along the cross axis */
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  /** Alignment of items along the main axis */
  justifyContent?:
    | 'flex-start'
    | 'center'
    | 'flex-end'
    | 'space-between'
    | 'space-around'
    | 'space-evenly';
  /** Column spacing (overrides spacing for columns) */
  columnSpacing?: GridSpacing;
  /** Row spacing (overrides spacing for rows) */
  rowSpacing?: GridSpacing;
  /** Number of columns in the grid (1-12) */
  columns?: number | Record<Breakpoint, number>;
}

/**
 * Props for Grid item
 */
export interface GridItemProps extends BaseGridProps {
  /** Number of columns to span (1-12, 'auto', or responsive object) */
  xs?: GridSize;
  /** Number of columns to span at sm breakpoint */
  sm?: GridSize;
  /** Number of columns to span at md breakpoint */
  md?: GridSize;
  /** Number of columns to span at lg breakpoint */
  lg?: GridSize;
  /** Number of columns to span at xl breakpoint */
  xl?: GridSize;
  /** Column offset (0-11) */
  offset?: number | Record<Breakpoint, number>;
  /** Order of the item */
  order?: number;
  /** If true, item grows to fill container */
  grow?: boolean | number;
  /** If true, item shrinks if needed */
  shrink?: boolean | number;
  /** Alignment override for this item */
  alignSelf?: 'auto' | 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
}

/**
 * Generate grid styles for responsive breakpoints
 */
const generateGridStyles = (
  prop: GridSize | undefined,
  theme: EmotionTheme,
  propertyName: string = 'grid-column'
): string => {
  if (prop === undefined) return '';
  if (prop === true) return `${propertyName}: span 1;`;
  if (prop === false || prop === 'auto') return `${propertyName}: auto;`;

  const size = typeof prop === 'number' ? Math.min(Math.max(prop, 1), 12) : prop;
  return `${propertyName}: span ${size} / span ${size};`;
};

/**
 * Generate offset styles
 */
const generateOffsetStyles = (
  offset: number | Record<Breakpoint, number> | undefined,
  theme: EmotionTheme
): string => {
  if (offset === undefined) return '';
  if (typeof offset === 'number') {
    const offsetValue = Math.min(Math.max(offset, 0), 11);
    return `margin-left: calc(${offsetValue} * (100% / 12));`;
  }
  return '';
};

/**
 * Generate responsive styles for breakpoints
 */
const generateResponsiveStyles = (
  props: Record<Breakpoint, GridSize | undefined>,
  theme: EmotionTheme,
  propertyName: string = 'grid-column'
): string => {
  const styles: string[] = [];

  // xs (default, mobile first)
  if (props.xs !== undefined) {
    styles.push(generateGridStyles(props.xs, theme, propertyName));
  }

  // sm
  if (props.sm !== undefined) {
    styles.push(`@media (min-width: ${theme.breakpoints.values.sm}px) {`);
    styles.push(generateGridStyles(props.sm, theme, propertyName));
    styles.push('}');
  }

  // md
  if (props.md !== undefined) {
    styles.push(`@media (min-width: ${theme.breakpoints.values.md}px) {`);
    styles.push(generateGridStyles(props.md, theme, propertyName));
    styles.push('}');
  }

  // lg
  if (props.lg !== undefined) {
    styles.push(`@media (min-width: ${theme.breakpoints.values.lg}px) {`);
    styles.push(generateGridStyles(props.lg, theme, propertyName));
    styles.push('}');
  }

  // xl
  if (props.xl !== undefined) {
    styles.push(`@media (min-width: ${theme.breakpoints.values.xl}px) {`);
    styles.push(generateGridStyles(props.xl, theme, propertyName));
    styles.push('}');
  }

  return styles.join('\n');
};

/**
 * Generate spacing styles for container
 */
const generateSpacingStyles = (
  spacing: GridSpacing | undefined,
  theme: EmotionTheme,
  direction: 'row' | 'column' = 'row'
): string => {
  if (spacing === undefined) return '';

  // Use theme spacing scale if number
  const gapValue =
    typeof spacing === 'number'
      ? spacing * theme.spacing.unit
      : spacing;

  if (direction === 'row') {
    return `gap: ${gapValue};`;
  }

  // For column direction, gap applies to rows
  return `gap: ${gapValue};`;
};

/**
 * Styled Grid Container
 */
const StyledGridContainer = styled.div<
  GridContainerProps & { theme: EmotionTheme }
>`
  box-sizing: border-box;
  display: grid;
  width: 100%;

  /* Default to 12 column grid */
  grid-template-columns: repeat(12, 1fr);

  /* Custom columns if specified */
  ${({ columns, theme }) => {
    if (typeof columns === 'number') {
      return `grid-template-columns: repeat(${columns}, 1fr);`;
    }
    if (typeof columns === 'object') {
      // Responsive columns
      const styles: string[] = [];
      if (columns.xs) styles.push(`grid-template-columns: repeat(${columns.xs}, 1fr);`);
      if (columns.sm) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.sm}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.sm}, 1fr);`);
        styles.push('}');
      }
      if (columns.md) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.md}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.md}, 1fr);`);
        styles.push('}');
      }
      if (columns.lg) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.lg}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.lg}, 1fr);`);
        styles.push('}');
      }
      if (columns.xl) {
        styles.push(`@media (min-width: ${theme.breakpoints.values.xl}px) {`);
        styles.push(`grid-template-columns: repeat(${columns.xl}, 1fr);`);
        styles.push('}');
      }
      return styles.join('\n');
    }
    return '';
  }}

  /* Spacing */
  ${({ spacing, theme, direction }) =>
    generateSpacingStyles(spacing, theme, direction)}

  /* Row spacing (overrides spacing) */
  ${({ rowSpacing, theme }) => {
    if (rowSpacing !== undefined) {
      const gapValue =
        typeof rowSpacing === 'number'
          ? rowSpacing * theme.spacing.unit
          : rowSpacing;
      return `row-gap: ${gapValue};`;
    }
    return '';
  }}

  /* Column spacing (overrides spacing) */
  ${({ columnSpacing, theme }) => {
    if (columnSpacing !== undefined) {
      const gapValue =
        typeof columnSpacing === 'number'
          ? columnSpacing * theme.spacing.unit
          : columnSpacing;
      return `column-gap: ${gapValue};`;
    }
    return '';
  }}

  /* Direction */
  ${({ direction }) =>
    direction === 'column'
      ? `
    grid-auto-flow: row;
    grid-template-rows: repeat(12, 1fr);
  `
      : ''}

  /* Wrap */
  ${({ wrap }) => {
    if (wrap === 'nowrap') return 'flex-wrap: nowrap;';
    if (wrap === 'wrap-reverse') return 'flex-wrap: wrap-reverse;';
    return '';
  }}

  /* Alignment */
  ${({ alignItems }) => (alignItems ? `align-items: ${alignItems};` : '')}
  ${({ justifyContent }) =>
    justifyContent ? `justify-content: ${justifyContent};` : ''}
`;

/**
 * Styled Grid Item
 */
const StyledGridItem = styled.div<GridItemProps & { theme: EmotionTheme }>`
  box-sizing: border-box;
  /* Default to spanning 1 column */
  grid-column: span 1;

  /* Responsive column spans */
  ${({ xs, sm, md, lg, xl, theme }) =>
    generateResponsiveStyles({ xs, sm, md, lg, xl }, theme, 'grid-column')}

  /* Offset */
  ${({ offset, theme }) => generateOffsetStyles(offset, theme)}

  /* Flex grow */
  ${({ grow }) =>
    grow !== undefined
      ? `flex-grow: ${typeof grow === 'boolean' ? (grow ? '1' : '0') : grow};`
      : ''}

  /* Flex shrink */
  ${({ shrink }) =>
    shrink !== undefined
      ? `flex-shrink: ${typeof shrink === 'boolean' ? (shrink ? '1' : '0') : shrink};`
      : ''}

  /* Order */
  ${({ order }) => (order !== undefined ? `order: ${order};` : '')}

  /* Self alignment */
  ${({ alignSelf }) => (alignSelf ? `align-self: ${alignSelf};` : '')}
`;

/**
 * Grid Container Component
 *
 * A CSS Grid container for responsive layouts.
 * Uses a 12-column grid system by default.
 *
 * @example
 * ```tsx
 * // Basic grid with spacing
 * <Grid container spacing={2}>
 *   <Grid item xs={12} sm={6} md={4}>
 *     Item 1
 *   </Grid>
 *   <Grid item xs={12} sm={6} md={4}>
 *     Item 2
 *   </Grid>
 *   <Grid item xs={12} sm={12} md={4}>
 *     Item 3
 *   </Grid>
 * </Grid>
 *
 * // Custom columns
 * <Grid container columns={8} spacing={2}>
 *   <Grid item xs={4}>Span 4 of 8</Grid>
 *   <Grid item xs={4}>Span 4 of 8</Grid>
 * </Grid>
 *
 * // With alignment
 * <Grid container spacing={2} alignItems="center" justifyContent="center">
 *   <Grid item xs={6}>Centered Content</Grid>
 * </Grid>
 *
 * // Direction column
 * <Grid container direction="column" spacing={2}>
 *   <Grid item xs={12}>Row 1</Grid>
 *   <Grid item xs={12}>Row 2</Grid>
 * </Grid>
 *
 * // Different spacing for rows and columns
 * <Grid container rowSpacing={4} columnSpacing={2}>
 *   <Grid item xs={6}>Item</Grid>
 *   <Grid item xs={6}>Item</Grid>
 * </Grid>
 * ```
 */
export const GridContainer = React.forwardRef<HTMLDivElement, GridContainerProps>(
  (
    {
      children,
      spacing,
      direction = 'row',
      wrap = 'wrap',
      alignItems,
      justifyContent,
      columnSpacing,
      rowSpacing,
      columns,
      className,
      style,
      gridRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledGridContainer
        ref={ref || gridRef}
        theme={theme}
        spacing={spacing}
        direction={direction}
        wrap={wrap}
        alignItems={alignItems}
        justifyContent={justifyContent}
        columnSpacing={columnSpacing}
        rowSpacing={rowSpacing}
        columns={columns}
        className={className}
        style={style}
      >
        {children}
      </StyledGridContainer>
    );
  }
);

GridContainer.displayName = 'GridContainer';

/**
 * Grid Item Component
 *
 * An item within a Grid container.
 * Controls how many columns the item spans at each breakpoint.
 *
 * @example
 * ```tsx
 * // Spans 12 columns on mobile, 6 on tablet, 4 on desktop
 * <Grid item xs={12} sm={6} md={4}>
 *   Content
 * </Grid>
 *
 * // Auto width
 * <Grid item xs="auto">
 *   Auto width content
 * </Grid>
 *
 * // With offset
 * <Grid item xs={6} offset={3}>
 *   Offset by 3 columns
 * </Grid>
 *
 * // Custom order
 * <Grid item xs={6} order={2}>
 *   Second
 * </Grid>
 * <Grid item xs={6} order={1}>
 *   First
 * </Grid>
 *
 * // Grow to fill space
 * <Grid item xs={6} grow>
 *   Grows to fill
 * </Grid>
 * ```
 */
export const GridItem = React.forwardRef<HTMLDivElement, GridItemProps>(
  (
    {
      children,
      xs,
      sm,
      md,
      lg,
      xl,
      offset,
      order,
      grow,
      shrink,
      alignSelf,
      className,
      style,
      gridRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledGridItem
        ref={ref || gridRef}
        theme={theme}
        xs={xs}
        sm={sm}
        md={md}
        lg={lg}
        xl={xl}
        offset={offset}
        order={order}
        grow={grow}
        shrink={shrink}
        alignSelf={alignSelf}
        className={className}
        style={style}
      >
        {children}
      </StyledGridItem>
    );
  }
);

GridItem.displayName = 'GridItem';

/**
 * Grid Component
 *
 * Unified Grid component that can act as both container and item.
 * Use the `container` prop to create a grid container.
 * Use the `item` prop to create a grid item.
 *
 * @example
 * ```tsx
 * // Container mode
 * <Grid container spacing={2}>
 *   <Grid item xs={12} sm={6}>
 *     Item 1
 *   </Grid>
 *   <Grid item xs={12} sm={6}>
 *     Item 2
 *   </Grid>
 * </Grid>
 *
 * // Compact syntax
 * <Grid container spacing={2}>
 *   <Grid xs={12} sm={6}>Item 1</Grid>
 *   <Grid xs={12} sm={6}>Item 2</Grid>
 * </Grid>
 * ```
 */
export interface GridProps extends GridContainerProps, GridItemProps {
  /** If true, component acts as a container */
  container?: boolean;
  /** If true, component acts as an item */
  item?: boolean;
  /** Zero-width separator between items */
  zeroMinWidth?: boolean;
}

export const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ container, item, children, zeroMinWidth, ...rest }, ref) => {
    if (container) {
      return (
        <GridContainer ref={ref} {...(rest as GridContainerProps)}>
          {children}
        </GridContainer>
      );
    }

    if (item || rest.xs !== undefined || rest.sm !== undefined) {
      return (
        <GridItem ref={ref} {...(rest as GridItemProps)}>
          {children}
        </GridItem>
      );
    }

    // Default to container behavior
    return (
      <GridContainer ref={ref} {...(rest as GridContainerProps)}>
        {children}
      </GridContainer>
    );
  }
);

Grid.displayName = 'Grid';

// Default export
export default Grid;
