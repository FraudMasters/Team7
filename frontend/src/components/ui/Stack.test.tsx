import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import { Stack, HStack, VStack } from './Stack';

// Mock the EmotionThemeContext
vi.mock('../../contexts/EmotionThemeContext', () => ({
  useEmotionTheme: () => ({
    theme: {
      spacing: { unit: 8 },
    },
  }),
  EmotionThemeContext: React.createContext(null),
}));

describe('Stack Component', () => {
  describe('Basic Rendering', () => {
    it('renders stack correctly', () => {
      render(
        <Stack data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toBeInTheDocument();
      expect(stack).toHaveStyle({ display: 'flex' });
    });

    it('renders children correctly', () => {
      render(
        <Stack data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack.children).toHaveLength(3);
    });
  });

  describe('Direction', () => {
    it('renders column direction by default', () => {
      render(
        <Stack data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexDirection: 'column' });
    });

    it('renders row direction when specified', () => {
      render(
        <Stack direction="row" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexDirection: 'row' });
    });

    it('renders row-reverse direction', () => {
      render(
        <Stack direction="row-reverse" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexDirection: 'row-reverse' });
    });

    it('renders column-reverse direction', () => {
      render(
        <Stack direction="column-reverse" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexDirection: 'column-reverse' });
    });
  });

  describe('Spacing', () => {
    it('applies spacing using theme scale', () => {
      render(
        <Stack spacing={2} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ gap: '16px' });
    });

    it('applies custom spacing string', () => {
      render(
        <Stack spacing="20px" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ gap: '20px' });
    });

    it('handles zero spacing', () => {
      render(
        <Stack spacing={0} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ gap: '0px' });
    });

    it('handles large spacing values', () => {
      render(
        <Stack spacing={5} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ gap: '40px' });
    });
  });

  describe('Flex Wrap', () => {
    it('applies wrap property', () => {
      render(
        <Stack flexWrap="wrap" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexWrap: 'wrap' });
    });

    it('applies nowrap property', () => {
      render(
        <Stack flexWrap="nowrap" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexWrap: 'nowrap' });
    });

    it('applies wrap-reverse property', () => {
      render(
        <Stack flexWrap="wrap-reverse" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexWrap: 'wrap-reverse' });
    });
  });

  describe('Alignment', () => {
    it('applies alignItems', () => {
      render(
        <Stack alignItems="center" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ alignItems: 'center' });
    });

    it('applies justifyContent', () => {
      render(
        <Stack justifyContent="space-between" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ justifyContent: 'space-between' });
    });

    it('applies both alignment props', () => {
      render(
        <Stack
          alignItems="flex-start"
          justifyContent="flex-end"
          data-testid="stack"
        >
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({
        alignItems: 'flex-start',
        justifyContent: 'flex-end',
      });
    });
  });

  describe('Flex Grow', () => {
    it('applies flexGrow as boolean', () => {
      render(
        <Stack flexGrow={true} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexGrow: '1' });
    });

    it('applies flexGrow as number', () => {
      render(
        <Stack flexGrow={2} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexGrow: '2' });
    });

    it('handles flexGrow false', () => {
      render(
        <Stack flexGrow={false} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ flexGrow: '0' });
    });
  });

  describe('Inline Display', () => {
    it('renders as inline-flex when inline is true', () => {
      render(
        <Stack inline data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ display: 'inline-flex' });
    });

    it('renders as regular flex by default', () => {
      render(
        <Stack data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ display: 'flex' });
    });
  });

  describe('Dividers', () => {
    it('renders dividers between items', () => {
      const Divider = () => <div data-testid="divider">|</div>;
      render(
        <Stack divider={<Divider />} data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Stack>
      );
      const dividers = screen.getAllByTestId('divider');
      expect(dividers).toHaveLength(2);
    });

    it('does not render divider after last item', () => {
      const Divider = () => <div data-testid="divider">|</div>;
      render(
        <Stack divider={<Divider />} data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      );
      const dividers = screen.getAllByTestId('divider');
      expect(dividers).toHaveLength(1);
    });

    it('renders correctly with single item and divider', () => {
      const Divider = () => <div data-testid="divider">|</div>;
      render(
        <Stack divider={<Divider />} data-testid="stack">
          <div>Item 1</div>
        </Stack>
      );
      const dividers = screen.queryAllByTestId('divider');
      expect(dividers).toHaveLength(0);
    });
  });

  describe('Custom Props', () => {
    it('applies className', () => {
      render(
        <Stack className="custom-class" data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveClass('custom-class');
    });

    it('applies inline styles', () => {
      render(
        <Stack style={{ padding: '20px' }} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveStyle({ padding: '20px' });
    });

    it('applies both className and style', () => {
      render(
        <Stack
          className="custom-class"
          style={{ margin: '10px' }}
          data-testid="stack"
        >
          <div>Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveClass('custom-class');
      expect(stack).toHaveStyle({ margin: '10px' });
    });
  });

  describe('HStack Component', () => {
    it('renders horizontal stack by default', () => {
      render(
        <HStack data-testid="hstack">
          <div>Item 1</div>
          <div>Item 2</div>
        </HStack>
      );
      const hstack = screen.getByTestId('hstack');
      expect(hstack).toHaveStyle({ flexDirection: 'row' });
    });

    it('accepts all stack props except direction', () => {
      render(
        <HStack spacing={2} alignItems="center" data-testid="hstack">
          <div>Item</div>
        </HStack>
      );
      const hstack = screen.getByTestId('hstack');
      expect(hstack).toHaveStyle({
        flexDirection: 'row',
        alignItems: 'center',
        gap: '16px',
      });
    });
  });

  describe('VStack Component', () => {
    it('renders vertical stack by default', () => {
      render(
        <VStack data-testid="vstack">
          <div>Item 1</div>
          <div>Item 2</div>
        </VStack>
      );
      const vstack = screen.getByTestId('vstack');
      expect(vstack).toHaveStyle({ flexDirection: 'column' });
    });

    it('accepts all stack props except direction', () => {
      render(
        <VStack spacing={3} justifyContent="center" data-testid="vstack">
          <div>Item</div>
        </VStack>
      );
      const vstack = screen.getByTestId('vstack');
      expect(vstack).toHaveStyle({
        flexDirection: 'column',
        justifyContent: 'center',
        gap: '24px',
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty children', () => {
      render(
        <Stack data-testid="stack">
          {[]}
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack.children).toHaveLength(0);
    });

    it('handles single child', () => {
      render(
        <Stack data-testid="stack">
          <div>Single Item</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack.children).toHaveLength(1);
    });

    it('handles null and undefined children', () => {
      render(
        <Stack data-testid="stack">
          <div>Item 1</div>
          {null}
          {undefined}
          <div>Item 2</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack.children).toHaveLength(2);
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref using ref prop', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Stack ref={ref} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('forwards ref using stackRef prop', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Stack stackRef={ref} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('uses ref prop when both ref and stackRef are provided', () => {
      const ref1 = React.createRef<HTMLDivElement>();
      const ref2 = React.createRef<HTMLDivElement>();
      render(
        <Stack ref={ref1} stackRef={ref2} data-testid="stack">
          <div>Item</div>
        </Stack>
      );
      expect(ref1.current).toBeInstanceOf(HTMLDivElement);
      expect(ref2.current).toBeNull();
    });
  });

  describe('Common Use Cases', () => {
    it('creates button group', () => {
      const { container } = render(
        <Stack direction="row" spacing={2}>
          <button>Button 1</button>
          <button>Button 2</button>
          <button>Button 3</button>
        </Stack>
      );
      expect(container).toBeInTheDocument();
    });

    it('creates form fields', () => {
      const { container } = render(
        <Stack spacing={3}>
          <div>Field 1</div>
          <div>Field 2</div>
          <div>Field 3</div>
        </Stack>
      );
      expect(container).toBeInTheDocument();
    });

    it('creates centered content', () => {
      const { container } = render(
        <Stack
          direction="row"
          spacing={2}
          alignItems="center"
          justifyContent="center"
        >
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      );
      expect(container).toBeInTheDocument();
    });

    it('creates wrapping chip list', () => {
      const { container } = render(
        <Stack direction="row" spacing={1} flexWrap="wrap">
          <div>Chip 1</div>
          <div>Chip 2</div>
          <div>Chip 3</div>
          <div>Chip 4</div>
        </Stack>
      );
      expect(container).toBeInTheDocument();
    });
  });
});
