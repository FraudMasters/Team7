import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

export interface TypographyProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  component?: React.ElementType;
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'subtitle1' | 'subtitle2' | 'body1' | 'body2' | 'caption' | 'overline';
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' | 'textPrimary' | 'textSecondary' | string;
  align?: 'left' | 'center' | 'right' | 'justify';
  gutterBottom?: boolean;
  noWrap?: boolean;
  paragraph?: boolean;
  onClick?: React.MouseEventHandler;
  id?: string;
}

const StyledTypography = styled.p<{
  theme: EmotionTheme;
  variant: string;
  color?: string;
  align?: string;
}>`
  margin: 0;
  box-sizing: border-box;
  font-family: ${({ theme }) => theme.typography.fontFamily};

  /* Variant styles */
  ${({ variant, theme }) => {
    switch (variant) {
      case 'h1':
        return `
          font-size: ${theme.typography.h1.fontSize || '2.5rem'};
          font-weight: ${theme.typography.h1.fontWeight || 700};
          line-height: 1.2;
        `;
      case 'h2':
        return `
          font-size: ${theme.typography.h2.fontSize || '2rem'};
          font-weight: ${theme.typography.h2.fontWeight || 700};
          line-height: 1.2;
        `;
      case 'h3':
        return `
          font-size: ${theme.typography.h3.fontSize || '1.75rem'};
          font-weight: ${theme.typography.h3.fontWeight || 600};
          line-height: 1.2;
        `;
      case 'h4':
        return `
          font-size: ${theme.typography.h4.fontSize || '1.5rem'};
          font-weight: ${theme.typography.h4.fontWeight || 600};
          line-height: 1.2;
        `;
      case 'h5':
        return `
          font-size: ${theme.typography.h5.fontSize || '1.25rem'};
          font-weight: ${theme.typography.h5.fontWeight || 600};
          line-height: 1.2;
        `;
      case 'h6':
        return `
          font-size: ${theme.typography.h6.fontSize || '1rem'};
          font-weight: ${theme.typography.h6.fontWeight || 600};
          line-height: 1.2;
        `;
      case 'subtitle1':
        return `
          font-size: 1rem;
          font-weight: 500;
          line-height: 1.5;
        `;
      case 'subtitle2':
        return `
          font-size: 0.875rem;
          font-weight: 500;
          line-height: 1.5;
        `;
      case 'body1':
        return `
          font-size: 1rem;
          font-weight: 400;
          line-height: 1.5;
        `;
      case 'body2':
        return `
          font-size: 0.875rem;
          font-weight: 400;
          line-height: 1.4;
        `;
      case 'caption':
        return `
          font-size: 0.75rem;
          font-weight: 400;
          line-height: 1.3;
        `;
      case 'overline':
        return `
          font-size: 0.75rem;
          font-weight: 400;
          line-height: 2;
          text-transform: uppercase;
        `;
      default:
        return '';
    }
  }};

  /* Color styles */
  ${({ color, theme }) => {
    if (!color) return '';
    const colorMap: Record<string, string> = {
      primary: theme.colors?.primary || '#1976d2',
      secondary: theme.colors?.secondary || '#9c27b0',
      error: theme.colors?.error || '#d32f2f',
      warning: theme.colors?.warning || '#ed6c02',
      info: theme.colors?.info || '#0288d1',
      success: theme.colors?.success || '#2e7d32',
      textPrimary: theme.colors?.textPrimary || 'rgba(0, 0, 0, 0.87)',
      textSecondary: theme.colors?.textSecondary || 'rgba(0, 0, 0, 0.6)',
    };
    return `color: ${colorMap[color] || color};`;
  }};

  /* Alignment */
  ${({ align }) => {
    if (align === 'center' || align === 'justify') {
      return 'text-align: center;';
    }
    if (align === 'right') {
      return 'text-align: right;';
    }
    return 'text-align: left;';
  }};

  /* Gutter bottom */
  ${({ gutterBottom }) => (gutterBottom ? 'margin-bottom: 0.35em;' : '')};

  /* No wrap */
  ${({ noWrap }) => (noWrap ? 'white-space: nowrap;' : '')};

  /* Paragraph */
  ${({ paragraph }) => (paragraph ? 'margin-bottom: 1em;' : '')};
`;

export const Typography: React.FC<TypographyProps> = ({
  children,
  className,
  style,
  sx,
  component = 'p',
  variant = 'body1',
  color,
  align = 'left',
  gutterBottom = false,
  noWrap = false,
  paragraph = false,
  ...props
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  const Component = variant.startsWith('h') ? variant : component;

  return (
    <StyledTypography
      as={Component}
      theme={theme}
      variant={variant}
      color={color}
      align={align}
      className={className}
      style={{ ...style, ...sxStyles }}
      {...props}
    >
      {children}
    </StyledTypography>
  );
};

Typography.displayName = 'Typography';

export default Typography;
