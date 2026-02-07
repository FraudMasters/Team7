import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface InputAdornmentProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  position?: 'start' | 'end';
  disablePointerEvents?: boolean;
  disableTypography?: boolean;
}

const StyledInputAdornment = styled.div<{ position: string; disablePointerEvents?: boolean }>`
  display: flex;
  align-items: center;
  color: rgba(0, 0, 0, 0.6);
  pointer-events: ${({ disablePointerEvents }) => (disablePointerEvents ? 'none' : 'auto')};
  margin: ${({ position }) => (position === 'start' ? '0 8px 0 0' : '0 0 0 8px')};
  max-height: 56px;

  & > * {
    line-height: 1;
  }
`;

export const InputAdornment: React.FC<InputAdornmentProps> = ({
  children,
  className,
  style,
  sx,
  position = 'start',
  disablePointerEvents = false,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  return (
    <StyledInputAdornment
      position={position}
      disablePointerEvents={disablePointerEvents}
      className={className}
      style={{ ...style, ...sxStyles }}
    >
      {children}
    </StyledInputAdornment>
  );
};

InputAdornment.displayName = 'InputAdornment';

export default InputAdornment;
