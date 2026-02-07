import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface BoxProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  component?: React.ElementType;
  onClick?: React.MouseEventHandler;
  id?: string;
  role?: string;
}

const StyledBox = styled.div<{
  theme: EmotionTheme;
}>`
  box-sizing: border-box;
  margin: 0;
`;

export const Box: React.FC<BoxProps> = ({
  children,
  className,
  style,
  sx,
  component = 'div',
  ...props
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  return (
    <StyledBox
      as={component}
      theme={theme}
      className={className}
      style={{ ...style, ...sxStyles }}
      {...props}
    >
      {children}
    </StyledBox>
  );
};

Box.displayName = 'Box';

export default Box;
