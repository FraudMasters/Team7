import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Stack direction type
 */
export type StackDirection = 'row' | 'column' | 'row-reverse' | 'column-reverse';

/**
 * Spacing type
 */
export type StackSpacing = number | string;

/**
 * Alignment options
 */
export type StackAlignment =
  | 'flex-start'
  | 'center'
  | 'flex-end'
  | 'space-between'
  | 'space-around'
  | 'space-evenly'
  | 'stretch'
  | 'baseline';

/**
 * Common stack props
 */
export interface BaseStackProps {
  /** Stack content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  stackRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Stack component
 */
export interface StackProps extends BaseStackProps {
  /** Direction of the stack (row or column) */
  direction?: StackDirection;
  /** Spacing between items (0-10 or custom value) */
  spacing?: StackSpacing;
  /** Wrap items to next line/row */
  flexWrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
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
  /** If true, items will not shrink below their minimum size */
  useFlexGap?: boolean;
  /** Divider to render between each item */
  divider?: React.ReactNode;
  /** If true, the stack will have flex-grow: 1 */
  flexGrow?: boolean | number;
  /** If true, the stack will be displayed as an inline-flex container */
  inline?: boolean;
}

/**
 * Generate spacing value from theme
 */
const getSpacingValue = (spacing: StackSpacing, theme: EmotionTheme): string => {
  if (typeof spacing === 'number') {
    return `${spacing * theme.spacing.unit}px`;
  }
  return spacing;
};

/**
 * Generate gap styles with fallback for older browsers
 */
const generateGapStyles = (
  spacing: StackSpacing | undefined,
  theme: EmotionTheme,
  direction: StackDirection
): string => {
  if (spacing === undefined) return '';

  const gapValue = getSpacingValue(spacing, theme);
  const isRow = direction === 'row' || direction === 'row-reverse';

  // Use gap property with fallback for older browsers
  return `
    gap: ${gapValue};

    /* Fallback for browsers that don't support gap in flexbox */
    @supports not (gap: ${gapValue}) {
      > *:not(:last-child) {
        ${isRow ? `margin-right: ${gapValue};` : `margin-bottom: ${gapValue};`}
      }

      /* For row-reverse and column-reverse */
      ${direction === 'row-reverse' ? '> *:not(:last-child) { margin-right: 0; margin-left: ' + gapValue + '; }' : ''}
      ${direction === 'column-reverse' ? '> *:not(:last-child) { margin-bottom: 0; margin-top: ' + gapValue + '; }' : ''}
    }
  `;
};

/**
 * Styled Stack Component
 */
const StyledStack = styled.div<StackProps & { theme: EmotionTheme; direction: StackDirection }>`
  display: ${({ inline }) => (inline ? 'inline-flex' : 'flex')};
  flex-direction: ${({ direction }) => direction};
  box-sizing: border-box;

  /* Flex grow */
  ${({ flexGrow }) =>
    flexGrow !== undefined
      ? `flex-grow: ${typeof flexGrow === 'boolean' ? (flexGrow ? '1' : '0') : flexGrow};`
      : ''}

  /* Spacing */
  ${({ spacing, theme, direction }) => generateGapStyles(spacing, theme, direction)}

  /* Wrap */
  ${({ flexWrap }) => (flexWrap !== undefined ? `flex-wrap: ${flexWrap};` : '')}

  /* Alignment */
  ${({ alignItems }) => (alignItems ? `align-items: ${alignItems};` : '')}
  ${({ justifyContent }) =>
    justifyContent ? `justify-content: ${justifyContent};` : ''}
`;

/**
 * Stack Item Component
 *
 * Internal component for rendering stack items with dividers
 */
const StackItem = styled.div<{ withDivider?: boolean }>`
  display: flex;
  align-items: center;

  ${({ withDivider }) =>
    withDivider
      ? `
    &:not(:last-child) {
      display: flex;
      align-items: center;
      flex: 1;

      &::after {
        content: '';
        flex: 1 1 auto;
      }
    }
  `
      : ''}
`;

/**
 * Stack Component
 *
 * A one-dimensional layout component using CSS Flexbox.
 * Stack items horizontally (row) or vertically (column) with consistent spacing.
 *
 * @example
 * ```tsx
 * // Basic vertical stack
 * <Stack spacing={2}>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </Stack>
 *
 * // Horizontal stack
 * <Stack direction="row" spacing={2}>
 *   <Button>Button 1</Button>
 *   <Button>Button 2</Button>
 *   <Button>Button 3</Button>
 * </Stack>
 *
 * // With alignment
 * <Stack direction="row" spacing={2} alignItems="center" justifyContent="center">
 *   <Typography>Centered Content</Typography>
 *   <Button>Action</Button>
 * </Stack>
 *
 * // Column reverse
 * <Stack direction="column-reverse" spacing={2}>
 *   <div>Item 1 (at bottom)</div>
 *   <div>Item 2 (in middle)</div>
 *   <div>Item 3 (at top)</div>
 * </Stack>
 *
 * // With divider
 * <Stack spacing={2} divider={<Divider />}>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </Stack>
 *
 * // Custom spacing
 * <Stack spacing="20px">
 *   <div>Custom 20px spacing</div>
 *   <div>Item 2</div>
 * </Stack>
 *
 * // Flex grow to fill space
 * <Stack flexGrow spacing={2}>
 *   <div>Grows to fill container</div>
 * </Stack>
 *
 * // Inline stack (inline-flex)
 * <Stack inline direction="row" spacing={2}>
 *   <span>Inline</span>
 *   <span>Stack</span>
 * </Stack>
 *
 * // Wrap items
 * <Stack direction="row" spacing={2} flexWrap="wrap">
 *   {items.map(item => (
 *     <Chip key={item.id} label={item.name} />
 *   ))}
 * </Stack>
 *
 * // Using theme spacing scale
 * <Stack spacing={3}> // 3 * 8px = 24px
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 * </Stack>
 * ```
 */
export const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  (
    {
      children,
      direction = 'column',
      spacing,
      flexWrap,
      alignItems,
      justifyContent,
      useFlexGap = true,
      divider,
      flexGrow,
      inline = false,
      className,
      style,
      stackRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Convert children to array for divider handling
    const childrenArray = React.Children.toArray(children);

    // Render with dividers
    if (divider) {
      return (
        <StyledStack
          ref={ref || stackRef}
          theme={theme}
          direction={direction}
          spacing={spacing}
          flexWrap={flexWrap}
          alignItems={alignItems}
          justifyContent={justifyContent}
          flexGrow={flexGrow}
          inline={inline}
          className={className}
          style={style}
        >
          {childrenArray.map((child, index) => (
            <React.Fragment key={index}>
              <StackItem>{child}</StackItem>
              {index < childrenArray.length - 1 && divider}
            </React.Fragment>
          ))}
        </StyledStack>
      );
    }

    // Render without dividers
    return (
      <StyledStack
        ref={ref || stackRef}
        theme={theme}
        direction={direction}
        spacing={spacing}
        flexWrap={flexWrap}
        alignItems={alignItems}
        justifyContent={justifyContent}
        flexGrow={flexGrow}
        inline={inline}
        className={className}
        style={style}
      >
        {children}
      </StyledStack>
    );
  }
);

Stack.displayName = 'Stack';

/**
 * HStack Component (Horizontal Stack)
 *
 * Convenience component for horizontal stacks.
 * Equivalent to `<Stack direction="row" />`
 *
 * @example
 * ```tsx
 * <HStack spacing={2}>
 *   <Button>Button 1</Button>
 *   <Button>Button 2</Button>
 * </HStack>
 * ```
 */
export interface HStackProps extends Omit<StackProps, 'direction'> {}

export const HStack = React.forwardRef<HTMLDivElement, HStackProps>((props, ref) => {
  return <Stack ref={ref} direction="row" {...props} />;
});

HStack.displayName = 'HStack';

/**
 * VStack Component (Vertical Stack)
 *
 * Convenience component for vertical stacks.
 * Equivalent to `<Stack direction="column" />`
 *
 * @example
 * ```tsx
 * <VStack spacing={2}>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 * </VStack>
 * ```
 */
export interface VStackProps extends Omit<StackProps, 'direction'> {}

export const VStack = React.forwardRef<HTMLDivElement, VStackProps>((props, ref) => {
  return <Stack ref={ref} direction="column" {...props} />;
});

VStack.displayName = 'VStack';

// Default export
export default Stack;
