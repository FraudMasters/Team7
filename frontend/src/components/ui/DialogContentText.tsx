import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface DialogContentTextProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  id?: string;
}

const StyledDialogContentText = styled.p<{ theme: EmotionTheme }>`
  margin: 0 0 16px 0;
  color: ${({ theme }) => theme.colors?.textPrimary || 'rgba(0, 0, 0, 0.87)'};
  font-family: ${({ theme }) => theme.typography?.fontFamily || 'Roboto, sans-serif'};
  font-size: 1rem;
  line-height: 1.5;

  &:last-child {
    margin-bottom: 0;
  }
`;

export const DialogContentText: React.FC<DialogContentTextProps> = ({
  children,
  className,
  style,
  sx,
  id,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  return (
    <StyledDialogContentText
      theme={theme}
      className={className}
      style={{ ...style, ...sxStyles }}
      id={id}
    >
      {children}
    </StyledDialogContentText>
  );
};

DialogContentText.displayName = 'DialogContentText';

export default DialogContentText;
