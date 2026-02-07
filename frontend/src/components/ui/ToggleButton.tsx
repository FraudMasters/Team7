import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface ToggleButtonProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  selected?: boolean;
  disabled?: boolean;
  value?: string | number;
  onChange?: (event: React.MouseEvent<HTMLElement>, value: string | number) => void;
  size?: 'small' | 'medium' | 'large';
}

const StyledToggleButton = styled.button<{
  theme: EmotionTheme;
  selected: boolean;
  disabled: boolean;
  size: string;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 1px solid ${({ theme }) => theme.colors?.border || 'rgba(0, 0, 0, 0.23)'};
  background: ${({ selected, theme }) => selected ? (theme.colors?.primary || '#1976d2') : 'transparent'};
  color: ${({ selected, disabled, theme }) => {
    if (disabled) return theme.colors?.textDisabled || 'rgba(0, 0, 0, 0.38)';
    if (selected) return '#ffffff';
    return theme.colors?.textPrimary || 'rgba(0, 0, 0, 0.87)';
  }};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  font-family: ${({ theme }) => theme.typography?.fontFamily || 'Roboto, sans-serif'};
  font-weight: 500;
  transition: all 0.2s ease;
  user-select: none;

  ${({ size }) => {
    switch (size) {
      case 'small':
        return `
          padding: 4px 8px;
          font-size: 0.75rem;
          min-width: 32px;
        `;
      case 'large':
        return `
          padding: 12px 16px;
          font-size: 1rem;
          min-width: 48px;
        `;
      default:
        return `
          padding: 8px 12px;
          font-size: 0.875rem;
          min-width: 40px;
        `;
    }
  }}

  &:hover:not(:disabled) {
    background: ${({ selected, theme }) => selected ? (theme.colors?.primaryDark || '#1565c0') : (theme.colors?.action?.hover || 'rgba(0, 0, 0, 0.04)')};
  }

  &:active:not(:disabled) {
    background: ${({ selected, theme }) => selected ? (theme.colors?.primaryDark || '#1565c0') : (theme.colors?.action?.active || 'rgba(0, 0, 0, 0.12)')};
  }

  &:disabled {
    opacity: 0.6;
  }
`;

export const ToggleButton = React.forwardRef<HTMLButtonElement, ToggleButtonProps>(
  ({ children, className, style, sx, selected = false, disabled = false, value, onChange, size = 'medium', ...props }, ref) => {
    const { theme } = useEmotionTheme();

    const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
      if (!disabled && onChange) {
        onChange(event, value as string | number);
      }
    };

    return (
      <StyledToggleButton
        ref={ref}
        theme={theme}
        selected={selected}
        disabled={disabled}
        size={size}
        className={className}
        style={{ ...style, ...sxStyles }}
        onClick={handleClick}
        disabled={disabled}
        {...props}
      >
        {children}
      </StyledToggleButton>
    );
  }
);

ToggleButton.displayName = 'ToggleButton';

export default ToggleButton;
