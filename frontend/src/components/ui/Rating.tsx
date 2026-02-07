import React, { useState, useCallback } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { Icon } from './primitives/Icon';

export interface RatingProps {
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  value?: number;
  defaultValue?: number;
  precision?: number;
  max?: number;
  readOnly?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  icon?: string;
  emptyIcon?: string;
  highlightSelectedOnly?: boolean;
  onChange?: (event: React.SyntheticEvent, value: number | null) => void;
  onChangeActive?: (event: React.SyntheticEvent, value: number) => void;
}

const StyledRatingContainer = styled.span<{ disabled?: boolean }>`
  display: inline-flex;
  cursor: ${({ disabled }) => (disabled ? 'default' : 'pointer')};
  user-select: none;
`;

const StyledStar = styled.span<{ theme: EmotionTheme; active: boolean; hover: boolean; size: string }>`
  display: inline-flex;
  align-items: center;
  color: ${({ active, hover, theme }) => {
    if (active || hover) return theme.colors?.warning?.main || '#ffc107';
    return theme.colors?.textSecondary || 'rgba(0, 0, 0, 0.6)';
  }};
  transition: color 0.2s ease;

  ${({ size }) => {
    switch (size) {
      case 'small':
        return 'font-size: 16px;';
      case 'large':
        return 'font-size: 32px;';
      default:
        return 'font-size: 24px;';
    }
  }}
`;

export const Rating: React.FC<RatingProps> = ({
  className,
  style,
  sx,
  value: controlledValue,
  defaultValue = 0,
  precision = 1,
  max = 5,
  readOnly = false,
  disabled = false,
  size = 'medium',
  icon = 'Star',
  emptyIcon = 'StarBorder',
  highlightSelectedOnly = false,
  onChange,
  onChangeActive,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  const [internalValue, setInternalValue] = useState(defaultValue);
  const [hoverValue, setHoverValue] = useState<number | null>(null);

  const isControlled = controlledValue !== undefined;
  const currentValue = isControlled ? controlledValue : internalValue;

  const handleMouseEnter = useCallback(
    (index: number) => {
      if (readOnly || disabled) return;
      const value = (index + 1) * precision;
      setHoverValue(value);
      if (onChangeActive) {
        onChangeActive({} as React.SyntheticEvent, value);
      }
    },
    [readOnly, disabled, precision, onChangeActive]
  );

  const handleMouseLeave = useCallback(() => {
    if (readOnly || disabled) return;
    setHoverValue(null);
  }, [readOnly, disabled]);

  const handleClick = useCallback(
    (index: number) => {
      if (readOnly || disabled) return;
      const newValue = (index + 1) * precision;
      if (!isControlled) {
        setInternalValue(newValue);
      }
      if (onChange) {
        onChange({} as React.SyntheticEvent, newValue);
      }
    },
    [readOnly, disabled, precision, isControlled, onChange]
  );

  const getValue = (index: number): number => (index + 1) * precision;

  const isStarActive = (index: number): boolean => {
    const displayValue = hoverValue !== null ? hoverValue : currentValue;
    return getValue(index) <= displayValue;
  };

  const isStarHovered = (index: number): boolean => {
    if (hoverValue === null) return false;
    return getValue(index) <= hoverValue;
  };

  const stars = Array.from({ length: max }, (_, index) => {
    const active = isStarActive(index);
    const hover = !highlightSelectedOnly && isStarHovered(index);

    return (
      <StyledStar
        key={index}
        theme={theme}
        active={active}
        hover={hover}
        size={size}
        onMouseEnter={() => handleMouseEnter(index)}
        onMouseMove={() => handleMouseEnter(index)}
      >
        <Icon
          name={active || hover ? icon : emptyIcon}
          size={size === 'small' ? 16 : size === 'large' ? 32 : 24}
        />
      </StyledStar>
    );
  });

  return (
    <StyledRatingContainer
      className={className}
      style={{ ...style, ...sxStyles }}
      disabled={disabled || readOnly}
      onMouseLeave={handleMouseLeave}
      onClick={(e) => {
        if (!readOnly && !disabled && hoverValue !== null) {
          const index = Math.round(hoverValue / precision) - 1;
          if (index >= 0) {
            handleClick(index);
          }
        }
      }}
    >
      {stars}
    </StyledRatingContainer>
  );
};

Rating.displayName = 'Rating';

export default Rating;
