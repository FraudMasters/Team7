import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import { Grid, GridContainer, GridItem } from './Grid';

// Mock the EmotionThemeContext
vi.mock('../../contexts/EmotionThemeContext', () => ({
  useEmotionTheme: () => ({
    theme: {
      spacing: { unit: 8 },
      breakpoints: {
        values: { xs: 0, sm: 600, md: 900, lg: 1200, xl: 1536 },
      },
    },
  }),
  EmotionThemeContext: React.createContext(null),
}));

describe('Grid Component', () => {
  describe('Grid Container', () => {
    it('renders container correctly', () => {
      render(
        <Grid container data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveStyle({ display: 'grid' });
    });

    it('applies spacing correctly', () => {
      render(
        <Grid container spacing={2} data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ gap: '16px' });
    });

    it('applies custom spacing', () => {
      render(
        <Grid container spacing="20px" data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ gap: '20px' });
    });

    it('applies direction column', () => {
      render(
        <Grid container direction="column" data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({
        gridAutoFlow: 'row',
        gridTemplateRows: 'repeat(12, 1fr)',
      });
    });

    it('applies wrap property', () => {
      render(
        <Grid container wrap="nowrap" data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ flexWrap: 'nowrap' });
    });

    it('applies alignment props', () => {
      render(
        <Grid
          container
          alignItems="center"
          justifyContent="center"
          data-testid="grid-container"
        >
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({
        alignItems: 'center',
        justifyContent: 'center',
      });
    });

    it('applies row and column spacing separately', () => {
      render(
        <Grid
          container
          rowSpacing={3}
          columnSpacing={2}
          data-testid="grid-container"
        >
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({
        rowGap: '24px',
        columnGap: '16px',
      });
    });

    it('applies custom columns', () => {
      render(
        <Grid container columns={8} data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ gridTemplateColumns: 'repeat(8, 1fr)' });
    });

    it('applies className and style', () => {
      render(
        <Grid
          container
          className="custom-class"
          style={{ backgroundColor: 'red' }}
          data-testid="grid-container"
        >
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveClass('custom-class');
      expect(container).toHaveStyle({ backgroundColor: 'red' });
    });
  });

  describe('Grid Item', () => {
    it('renders item correctly', () => {
      render(
        <Grid container>
          <Grid item data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toBeInTheDocument();
      expect(item).toHaveStyle({ gridColumn: 'span 1' });
    });

    it('applies xs prop correctly', () => {
      render(
        <Grid container>
          <Grid item xs={6} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ gridColumn: 'span 6 / span 6' });
    });

    it('applies responsive props', () => {
      render(
        <Grid container>
          <Grid item xs={12} sm={6} md={4} lg={3} xl={2} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      // xs (default)
      expect(item).toHaveStyle({ gridColumn: 'span 12 / span 12' });
      // sm breakpoint
      expect(item).toHaveStyle({ '@media (min-width: 600px)': { gridColumn: 'span 6 / span 6' } });
    });

    it('applies auto size', () => {
      render(
        <Grid container>
          <Grid item xs="auto" data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ gridColumn: 'auto' });
    });

    it('applies offset', () => {
      render(
        <Grid container>
          <Grid item xs={6} offset={3} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ marginLeft: 'calc(3 * (100% / 12))' });
    });

    it('applies order', () => {
      render(
        <Grid container>
          <Grid item order={2} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ order: '2' });
    });

    it('applies grow and shrink', () => {
      render(
        <Grid container>
          <Grid item grow={true} shrink={false} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({
        flexGrow: '1',
        flexShrink: '0',
      });
    });

    it('applies numeric grow and shrink', () => {
      render(
        <Grid container>
          <Grid item grow={2} shrink={1} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({
        flexGrow: '2',
        flexShrink: '1',
      });
    });

    it('applies alignSelf', () => {
      render(
        <Grid container>
          <Grid item alignSelf="center" data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ alignSelf: 'center' });
    });

    it('applies className and style', () => {
      render(
        <Grid container>
          <Grid
            item
            className="custom-class"
            style={{ backgroundColor: 'blue' }}
            data-testid="grid-item"
          >
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveClass('custom-class');
      expect(item).toHaveStyle({ backgroundColor: 'blue' });
    });
  });

  describe('Unified Grid Component', () => {
    it('renders as container when container prop is true', () => {
      render(
        <Grid container data-testid="grid">
          <div>Item</div>
        </Grid>
      );
      const grid = screen.getByTestId('grid');
      expect(grid).toHaveStyle({ display: 'grid' });
    });

    it('renders as item when item prop is true', () => {
      render(
        <Grid container>
          <Grid item xs={6} data-testid="grid">
            Item
          </Grid>
        </Grid>
      );
      const grid = screen.getByTestId('grid');
      expect(grid).toHaveStyle({ gridColumn: 'span 6 / span 6' });
    });

    it('renders as item when breakpoint props are provided', () => {
      render(
        <Grid container>
          <Grid xs={6} data-testid="grid">
            Item
          </Grid>
        </Grid>
      );
      const grid = screen.getByTestId('grid');
      expect(grid).toHaveStyle({ gridColumn: 'span 6 / span 6' });
    });

    it('defaults to container behavior', () => {
      render(
        <Grid data-testid="grid">
          <div>Item</div>
        </Grid>
      );
      const grid = screen.getByTestId('grid');
      expect(grid).toHaveStyle({ display: 'grid' });
    });
  });

  describe('Responsive Layouts', () => {
    it('creates responsive grid layout', () => {
      const { container } = render(
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            Item 1
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            Item 2
          </Grid>
          <Grid item xs={12} sm={12} md={4}>
            Item 3
          </Grid>
        </Grid>
      );
      expect(container).toBeInTheDocument();
    });

    it('creates complex nested grid', () => {
      const { container } = render(
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Grid container spacing={1}>
              <Grid item xs={6}>
                Nested Item 1
              </Grid>
              <Grid item xs={6}>
                Nested Item 2
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      );
      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero spacing', () => {
      render(
        <Grid container spacing={0} data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ gap: '0px' });
    });

    it('handles large spacing values', () => {
      render(
        <Grid container spacing={10} data-testid="grid-container">
          <div>Item</div>
        </Grid>
      );
      const container = screen.getByTestId('grid-container');
      expect(container).toHaveStyle({ gap: '80px' });
    });

    it('clamps column span to 1-12 range', () => {
      render(
        <Grid container>
          <Grid item xs={15} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ gridColumn: 'span 12 / span 12' });
    });

    it('handles boolean size props', () => {
      render(
        <Grid container>
          <Grid item xs={true} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ gridColumn: 'span 1' });
    });

    it('handles false size prop', () => {
      render(
        <Grid container>
          <Grid item xs={false} data-testid="grid-item">
            Item
          </Grid>
        </Grid>
      );
      const item = screen.getByTestId('grid-item');
      expect(item).toHaveStyle({ gridColumn: 'auto' });
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref for container', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Grid container ref={ref} data-testid="grid">
          <div>Item</div>
        </Grid>
      );
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('forwards ref for item', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Grid container>
          <Grid item ref={ref} data-testid="grid">
            Item
          </Grid>
        </Grid>
      );
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('forwards ref using gridRef prop', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Grid container gridRef={ref} data-testid="grid">
          <div>Item</div>
        </Grid>
      );
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });
});
