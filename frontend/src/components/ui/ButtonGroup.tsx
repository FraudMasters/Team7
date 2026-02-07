import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * ButtonGroup orientation
 */
export type ButtonGroupOrientation = 'horizontal' | 'vertical';

/**
 * ButtonGroup variant for child buttons
 */
export type ButtonGroupVariant = 'contained' | 'outlined' | 'text';

/**
 * ButtonGroup color for child buttons
 */
export type ButtonGroupColor =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'inherit';

/**
 * ButtonGroup size for child buttons
 */
export type ButtonGroupSize = 'small' | 'medium' | 'large';

/**
 * Base ButtonGroup props interface
 */
export interface BaseButtonGroupProps {
  /** Button content */
  children?: React.ReactNode;
  /** Group orientation */
  orientation?: ButtonGroupOrientation;
  /** Variant to apply to all buttons */
  variant?: ButtonGroupVariant;
  /** Color to apply to all buttons */
  color?: ButtonGroupColor;
  /** Size to apply to all buttons */
  size?: ButtonGroupSize;
  /** Disable all buttons in the group */
  disabled?: boolean;
  /** If true, only the first and last buttons will have rounded corners */
  disableRipple?: boolean;
  /** If true, the buttons will not have elevation */
  disableElevation?: boolean;
  /** Full width button group */
  fullWidth?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  groupRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for ButtonGroup component
 */
export interface ButtonGroupProps extends BaseButtonGroupProps {}

/**
 * Get size styles
 */
const getSizeStyles = (size: ButtonGroupSize) => {
  const sizeMap = {
    small: {
      minHeight: '32px',
    },
    medium: {
      minHeight: '40px',
    },
    large: {
      minHeight: '48px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled ButtonGroup container
 */
const StyledButtonGroup = styled.div<{
  orientation: ButtonGroupOrientation;
  fullWidth?: boolean;
  disableElevation?: boolean;
  size: ButtonGroupSize;
}>`
  display: inline-flex;
  flex-direction: ${({ orientation }) => (orientation === 'vertical' ? 'column' : 'row')};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  overflow: hidden;
  box-sizing: border-box;

  /* Full width */
  ${({ fullWidth }) => (fullWidth ? 'width: 100%; display: flex;' : '')}

  /* Remove elevation */
  ${({ disableElevation }) =>
    disableElevation
      ? `
    box-shadow: none;
    & > * {
      box-shadow: none;
    }
  `
      : ''}

  /* Size */
  ${({ size }) => getSizeStyles(size)}

  /* Apply styles to child buttons */
  & > * {
    /* Remove border radius except for first/last items */
    border-radius: 0;

    /* Remove margin between buttons */
    margin: 0;

    /* Remove right border for all but last button in horizontal mode */
    ${({ orientation }) =>
      orientation === 'horizontal'
        ? `
      &:not(:last-child) {
        border-right: none;
      }
    `
        : ''}

    /* Remove bottom border for all but last button in vertical mode */
    ${({ orientation }) =>
      orientation === 'vertical'
        ? `
      &:not(:last-child) {
        border-bottom: none;
      }
    `
        : ''}
  }

  /* First child - left/top rounded corners */
  & > *:first-child {
    border-top-left-radius: ${({ theme, orientation }) =>
      orientation === 'vertical' ? theme.borderRadius.md : theme.borderRadius.md};
    border-top-right-radius: ${({ orientation }) => (orientation === 'vertical' ? '0' : '0')};
    border-bottom-left-radius: ${({ orientation }) => (orientation === 'vertical' ? '0' : theme.borderRadius.md)};
    border-bottom-right-radius: 0;
  }

  /* Last child - right/bottom rounded corners */
  & > *:last-child {
    border-top-left-radius: 0;
    border-top-right-radius: ${({ orientation }) => (orientation === 'vertical' ? theme.borderRadius.md : theme.borderRadius.md)};
    border-bottom-left-radius: 0;
    border-bottom-right-radius: ${({ theme, orientation }) =>
      orientation === 'vertical' ? theme.borderRadius.md : theme.borderRadius.md};
  }

  /* Single child - all rounded corners */
  & > *:only-child {
    border-radius: ${({ theme }) => theme.borderRadius.md};
  }
`;

/**
 * ButtonGroup Component
 *
 * A container component that groups related buttons together with proper styling.
 * Built with Emotion to replace Material-UI ButtonGroup component.
 *
 * @example
 * ```tsx
 * // Basic horizontal button group
 * <ButtonGroup>
 *   <Button>Button 1</Button>
 *   <Button>Button 2</Button>
 *   <Button>Button 3</Button>
 * </ButtonGroup>
 *
 * // Vertical orientation
 * <ButtonGroup orientation="vertical">
 *   <Button>Top</Button>
 *   <Button>Middle</Button>
 *   <Button>Bottom</Button>
 * </ButtonGroup>
 *
 * // With variant and color
 * <ButtonGroup variant="outlined" color="primary">
 *   <Button>Left</Button>
 *   <Button>Middle</Button>
 *   <Button>Right</Button>
 * </ButtonGroup>
 *
 * // With size
 * <ButtonGroup size="small">
 *   <Button>Small</Button>
 *   <Button>Small</Button>
 * </ButtonGroup>
 *
 * // Full width
 * <ButtonGroup fullWidth>
 *   <Button>Full 1</Button>
 *   <Button>Full 2</Button>
 * </ButtonGroup>
 *
 * // Disable elevation
 * <ButtonGroup variant="contained" disableElevation>
 *   <Button>Flat 1</Button>
 *   <Button>Flat 2</Button>
 * </ButtonGroup>
 *
 * // Disabled group
 * <ButtonGroup disabled>
 *   <Button>Disabled 1</Button>
 *   <Button>Disabled 2</Button>
 * </ButtonGroup>
 *
 * // With icon buttons
 * <ButtonGroup>
 *   <IconButton name="AlignLeft" aria-label="Align left" />
 *   <IconButton name="AlignCenter" aria-label="Align center" />
 *   <IconButton name="AlignRight" aria-label="Align right" />
 * </ButtonGroup>
 *
 * // Mixed sizes (overrides group size)
 * <ButtonGroup size="medium">
 *   <Button>Medium</Button>
 *   <Button size="small">Small</Button>
 *   <Button size="large">Large</Button>
 * </ButtonGroup>
 * ```
 */
export const ButtonGroup = React.forwardRef<HTMLDivElement, ButtonGroupProps>(
  (
    {
      children,
      orientation = 'horizontal',
      variant,
      color,
      size,
      disabled,
      disableRipple = false,
      disableElevation = false,
      fullWidth = false,
      className,
      style,
      groupRef,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Clone children and apply group props if they don't have their own
    const enhancedChildren = React.Children.map(children, (child) => {
      if (!React.isValidElement(child)) {
        return child;
      }

      // Only apply props if child is a Button or IconButton component
      const childType = child.type as any;
      const componentName = childType.displayName || childType.name;

      if (componentName === 'Button' || componentName === 'IconButton') {
        const childProps: any = {};

        // Apply variant if child doesn't have one
        if (variant && !child.props.variant) {
          childProps.variant = variant;
        }

        // Apply color if child doesn't have one
        if (color && !child.props.color) {
          childProps.color = color;
        }

        // Apply size if child doesn't have one
        if (size && !child.props.size) {
          childProps.size = size;
        }

        // Apply disabled if child doesn't have one
        if (disabled && !child.props.disabled) {
          childProps.disabled = disabled;
        }

        // If there are props to apply, clone the element
        if (Object.keys(childProps).length > 0) {
          return React.cloneElement(child, childProps);
        }
      }

      return child;
    });

    return (
      <StyledButtonGroup
        ref={ref || groupRef}
        theme={theme}
        orientation={orientation}
        fullWidth={fullWidth}
        disableElevation={disableElevation}
        size={size || 'medium'}
        className={className}
        style={style}
      >
        {enhancedChildren}
      </StyledButtonGroup>
    );
  }
);

ButtonGroup.displayName = 'ButtonGroup';

export default ButtonGroup;
