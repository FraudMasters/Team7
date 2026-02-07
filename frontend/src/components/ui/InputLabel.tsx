import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface InputLabelProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  disabled?: boolean;
  error?: boolean;
  required?: boolean;
  shrink?: boolean;
  htmlFor?: string;
  id?: string;
  onClick?: React.MouseEventHandler;
}

const StyledInputLabel = styled.label<{
  theme: EmotionTheme;
  disabled?: boolean;
  error?: boolean;
}>`
  display: block;
  font-family: ${({ theme }) => theme.typography?.fontFamily || 'Roboto, sans-serif'};
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.5;
  color: ${({ theme, error, disabled }) => {
    if (disabled) return theme.colors?.textSecondary || 'rgba(0, 0, 0, 0.6)';
    if (error) return theme.colors?.error || '#d32f2f';
    return theme.colors?.textSecondary || 'rgba(0, 0, 0, 0.6)';
  }};
  margin-bottom: 4px;
  transition: color 0.2s ease;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'default')};

  &:hover {
    color: ${({ theme, disabled, error }) => {
    if (disabled) return theme.colors?.textSecondary || 'rgba(0, 0, 0, 0.6)';
    if (error) return theme.colors?.error || '#d32f2f';
    return theme.colors?.textPrimary || 'rgba(0, 0, 0, 0.87)';
  }};
  }
`;

export const InputLabel: React.FC<InputLabelProps> = ({
  children,
  className,
  style,
  sx,
  disabled = false,
  error = false,
  required = false,
  shrink,
  htmlFor,
  id,
  onClick,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  return (
    <StyledInputLabel
      theme={theme}
      disabled={disabled}
      error={error}
      className={className}
      style={{ ...style, ...sxStyles }}
      htmlFor={htmlFor}
      id={id}
      onClick={onClick}
    >
      {children}
      {required && <span style={{ color: 'inherit', marginLeft: '2px' }}>*</span>}
    </StyledInputLabel>
  );
};

InputLabel.displayName = 'InputLabel';

export default InputLabel;
