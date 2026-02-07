import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { ToggleButton } from './ToggleButton';

export interface ToggleButtonGroupProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  value?: string | number | (string | number)[];
  exclusive?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  orientation?: 'horizontal' | 'vertical';
  onChange?: (event: React.MouseEvent<HTMLElement>, value: string | number | (string | number)[]) => void;
}

const StyledToggleButtonGroup = styled.div<{ orientation: string }>`
  display: inline-flex;
  flex-direction: ${({ orientation }) => orientation === 'vertical' ? 'column' : 'row'};

  & > *:not(:first-child) {
    margin-left: ${({ orientation }) => orientation === 'horizontal' ? '-1px' : '0'};
    margin-top: ${({ orientation }) => orientation === 'vertical' ? '-1px' : '0'};
  }

  & > *:first-child {
    border-top-left-radius: 4px;
    border-bottom-left-radius: ${({ orientation }) => orientation === 'horizontal' ? '4px' : '0'};
    border-top-right-radius: ${({ orientation }) => orientation === 'horizontal' ? '0' : '4px'};
  }

  & > *:last-child {
    border-top-left-radius: ${({ orientation }) => orientation === 'horizontal' ? '0' : '4px'};
    border-bottom-left-radius: ${({ orientation }) => orientation === 'horizontal' ? '4px' : '0'};
    border-bottom-right-radius: 4px;
  }

  & > *:not(:first-child):not(:last-child) {
    border-radius: 0;
  }
`;

export const ToggleButtonGroup: React.FC<ToggleButtonGroupProps> = ({
  children,
  className,
  style,
  sx,
  value,
  exclusive = true,
  disabled = false,
  size = 'medium',
  orientation = 'horizontal',
  onChange,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  const handleChildClick = (event: React.MouseEvent<HTMLElement>, childValue: string | number) => {
    if (disabled) return;

    let newValue: string | number | (string | number)[];

    if (exclusive) {
      newValue = value === childValue ? '' : childValue;
    } else {
      const valueArray = Array.isArray(value) ? value : [];
      if (valueArray.includes(childValue)) {
        newValue = valueArray.filter((v) => v !== childValue);
      } else {
        newValue = [...valueArray, childValue];
      }
    }

    if (onChange) {
      onChange(event, newValue);
    }
  };

  const isChildSelected = (childValue: string | number): boolean => {
    if (exclusive) {
      return value === childValue;
    }
    return Array.isArray(value) && value.includes(childValue);
  };

  const enhancedChildren = React.Children.map(children, (child) => {
    if (React.isValidElement(child) && child.type === ToggleButton) {
      return React.cloneElement(child, {
        selected: isChildSelected(child.props.value),
        disabled: disabled || child.props.disabled,
        size: child.props.size || size,
        onChange: (e: React.MouseEvent<HTMLElement>) => handleChildClick(e, child.props.value),
      } as Partial<typeof child.props>);
    }
    return child;
  });

  return (
    <StyledToggleButtonGroup
      orientation={orientation}
      className={className}
      style={{ ...style, ...sxStyles }}
    >
      {enhancedChildren}
    </StyledToggleButtonGroup>
  );
};

ToggleButtonGroup.displayName = 'ToggleButtonGroup';

export default ToggleButtonGroup;
