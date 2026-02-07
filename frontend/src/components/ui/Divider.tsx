import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Divider orientation type
 */
export type DividerOrientation = 'horizontal' | 'vertical';

/**
 * Divider text alignment type
 */
export type DividerTextAlign = 'left' | 'center' | 'right';

/**
 * Divider component props interface
 */
export interface DividerProps extends React.HTMLAttributes<HTMLDivElement | HTMLHRElement> {
  /** Divider orientation */
  orientation?: DividerOrientation;
  /** If true, divider is flexible (will grow in vertical orientation) */
  flexItem?: boolean;
  /** Text to display in the middle of the divider */
  children?: React.ReactNode;
  /** Alignment of the text (if children provided) */
  textAlign?: DividerTextAlign;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  dividerRef?: React.Ref<HTMLDivElement | HTMLHRElement>;
}

/**
 * Get text alignment styles
 */
const getTextAlignStyles = (textAlign: DividerTextAlign): string => {
  const alignMap = {
    left: 'flex-start',
    center: 'center',
    right: 'flex-end',
  };
  return alignMap[textAlign];
};

/**
 * Styled horizontal divider
 */
const StyledHorizontalDivider = styled.hr<{ theme: EmotionTheme }>`
  border: none;
  border-top: 1px solid ${({ theme }) => theme.divider};
  margin: 0;
  flex-shrink: 0;
`;

/**
 * Styled vertical divider
 */
const StyledVerticalDivider = styled.hr<{ theme: EmotionTheme; flexItem?: boolean }>`
  border: none;
  border-left: 1px solid ${({ theme }) => theme.divider};
  margin: 0;
  flex-shrink: 0;
  ${({ flexItem }) => (flexItem ? 'height: auto;' : '')}
`;

/**
 * Wrapper for dividers with text
 */
const DividerWrapper = styled.div<{
  theme: EmotionTheme;
  orientation: DividerOrientation;
  textAlign: DividerTextAlign;
  flexItem?: boolean;
}>`
  display: flex;
  align-items: center;
  ${({ orientation }) => (orientation === 'vertical' ? 'flex-direction: column;' : '')}
  ${({ orientation, flexItem }) =>
    orientation === 'vertical' && flexItem ? 'height: auto;' : ''}
  width: ${({ orientation }) => (orientation === 'vertical' && !flexItem ? '0px' : '100%')};
  margin: ${({ theme, orientation }) =>
    orientation === 'horizontal' ? `${theme.spacing.md} 0` : `0 ${theme.spacing.md}`};
  gap: ${({ theme }) => theme.spacing.md};

  &::before,
  &::after {
    content: '';
    flex: 1;
    ${({ orientation }) =>
      orientation === 'horizontal'
        ? `border-top: 1px solid currentColor;`
        : `border-left: 1px solid currentColor;`}
    border-color: ${({ theme }) => theme.divider};
    opacity: 0.6;
  }

  ${({ textAlign, orientation }) => {
    if (orientation === 'horizontal') {
      if (textAlign === 'left') {
        return `
          &::before { flex: 0; }
          &::after { flex: 1; }
        `;
      }
      if (textAlign === 'right') {
        return `
          &::before { flex: 1; }
          &::after { flex: 0; }
        `;
      }
    }
    return '';
  }}
`;

/**
 * Divider text content
 */
const DividerText = styled.span<{ theme: EmotionTheme }>`
  color: ${({ theme }) => theme.text.secondary};
  font-size: 0.875rem;
  white-space: nowrap;
  padding: 0 ${({ theme }) => theme.spacing.sm};
`;

/**
 * Divider Component
 *
 * A divider line separates content into clear groups.
 * Can be horizontal or vertical, and can include text.
 *
 * @example
 * ```tsx
 * // Basic horizontal divider
 * <Divider />
 *
 * // Vertical divider
 * <Divider orientation="vertical" flexItem />
 *
 * // With text
 * <Divider>OR</Divider>
 *
 * // With left-aligned text
 * <Divider textAlign="left">Section Title</Divider>
 *
 * // With right-aligned text
 * <Divider textAlign="right">End</Divider>
 *
 * // In a flex container
 * <Box display="flex" alignItems="center">
 *   <Item>Item 1</Item>
 *   <Divider orientation="vertical" flexItem />
 *   <Item>Item 2</Item>
 * </Box>
 * ```
 */
export const Divider = React.forwardRef<HTMLDivElement | HTMLHRElement, DividerProps>(
  (
    {
      orientation = 'horizontal',
      flexItem = false,
      children,
      textAlign = 'center',
      className,
      style,
      dividerRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // If children provided, render as wrapper with text
    if (children) {
      return (
        <DividerWrapper
          ref={ref as React.RefObject<HTMLDivElement>}
          theme={theme}
          orientation={orientation}
          textAlign={textAlign}
          flexItem={flexItem}
          className={className}
          style={style}
          {...(rest as React.HTMLAttributes<HTMLDivElement>)}
        >
          <DividerText theme={theme}>{children}</DividerText>
        </DividerWrapper>
      );
    }

    // Render simple divider
    if (orientation === 'vertical') {
      return (
        <StyledVerticalDivider
          ref={ref as React.RefObject<HTMLHRElement>}
          theme={theme}
          flexItem={flexItem}
          className={className}
          style={style}
          {...(rest as React.HTMLAttributes<HTMLHRElement>)}
        />
      );
    }

    return (
      <StyledHorizontalDivider
        ref={ref as React.RefObject<HTMLHRElement>}
        theme={theme}
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLHRElement>)}
      />
    );
  }
);

Divider.displayName = 'Divider';

export default Divider;
