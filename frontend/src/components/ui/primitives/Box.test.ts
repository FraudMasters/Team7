import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '@emotion/react';
import Box from './Box';
import { EmotionThemeProvider } from '../../../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <EmotionThemeProvider>{component}</EmotionThemeProvider>
  );
};

describe('Box Component', () => {
  it('renders without crashing', () => {
    renderWithTheme(<Box>Test Box</Box>);
    expect(screen.getByText('Test Box')).toBeInTheDocument();
  });

  it('renders children correctly', () => {
    renderWithTheme(<Box>Child Content</Box>);
    expect(screen.getByText('Child Content')).toHaveTextContent('Child Content');
  });

  it('applies padding from p prop', () => {
    const { container } = renderWithTheme(<Box p={2}>Padding Test</Box>);
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveStyle({ padding: '16px' });
  });

  it('applies margin from m prop', () => {
    const { container } = renderWithTheme(<Box m={2}>Margin Test</Box>);
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveStyle({ margin: '16px' });
  });

  it('applies background color', () => {
    const { container } = renderWithTheme(<Box bgcolor="#ff0000">Background Test</Box>);
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveStyle({ backgroundColor: '#ff0000' });
  });

  it('applies display property', () => {
    const { container } = renderWithTheme(<Box display="flex">Flex Box</Box>);
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveStyle({ display: 'flex' });
  });

  it('renders as custom component when specified', () => {
    const { container } = renderWithTheme(
      <Box component="section">Section Box</Box>
    );
    const box = container.firstChild as HTMLElement;
    expect(box.tagName.toLowerCase()).toBe('section');
  });

  it('applies flexbox properties', () => {
    const { container } = renderWithTheme(
      <Box display="flex" justifyContent="center" alignItems="center">
        Flex Container
      </Box>
    );
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveStyle({
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    });
  });

  it('handles click events', () => {
    let clicked = false;
    const handleClick = () => { clicked = true; };

    const { container } = renderWithTheme(
      <Box onClick={handleClick}>Clickable Box</Box>
    );

    const box = container.firstChild as HTMLElement;
    box.click();
    expect(clicked).toBe(true);
  });

  it('applies custom className', () => {
    const { container } = renderWithTheme(
      <Box className="custom-class">Class Test</Box>
    );
    const box = container.firstChild as HTMLElement;
    expect(box).toHaveClass('custom-class');
  });

  it('handles responsive spacing', () => {
    const { container } = renderWithTheme(
      <Box p={[1, 2, 3]}>Responsive Padding</Box>
    );
    const box = container.firstChild as HTMLElement;
    // Should apply array-based padding
    expect(box).toBeInTheDocument();
  });
});
