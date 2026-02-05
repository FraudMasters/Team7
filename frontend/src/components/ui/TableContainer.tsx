import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface TableContainerProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  component?: React.ElementType;
}

const StyledTableContainer = styled.div<{ theme: EmotionTheme }>`
  width: 100%;
  overflow-x: auto;
  box-sizing: border-box;

  /* Custom scrollbar for webkit browsers */
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: ${({ theme }) => theme.colors?.background || '#f5f5f5'};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors?.border || '#bdbdbd'};
    border-radius: 4px;

    &:hover {
      background: ${({ theme }) => theme.colors?.textSecondary || '#9e9e9e'};
    }
  }
`;

export const TableContainer: React.FC<TableContainerProps> = ({
  children,
  className,
  style,
  sx,
  component = 'div',
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  return (
    <StyledTableContainer
      as={component}
      theme={theme}
      className={className}
      style={{ ...style, ...sxStyles }}
    >
      {children}
    </StyledTableContainer>
  );
};

TableContainer.displayName = 'TableContainer';

export default TableContainer;
