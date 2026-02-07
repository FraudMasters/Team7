import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from './Button';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithTheme(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders children correctly', () => {
      renderWithTheme(<Button>Test Button</Button>);
      expect(screen.getByRole('button')).toHaveTextContent('Test Button');
    });

    it('renders with default props', () => {
      const { container } = renderWithTheme(<Button>Default</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('renders with custom className', () => {
      const { container } = renderWithTheme(<Button className="custom-class">Test</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveClass('custom-class');
    });

    it('renders with custom style', () => {
      const { container } = renderWithTheme(<Button style={{ margin: '10px' }}>Test</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({ margin: '10px' });
    });

    it('renders with aria-label', () => {
      renderWithTheme(<Button aria-label="close button">X</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'close button');
    });

    it('renders with custom type', () => {
      const { container } = renderWithTheme(<Button type="submit">Submit</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('renders with tabIndex', () => {
      const { container } = renderWithTheme(<Button tabIndex={-1}>Skip</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveAttribute('tabIndex', '-1');
    });
  });

  describe('Variants', () => {
    it('renders contained variant', () => {
      const { container } = renderWithTheme(<Button variant="contained">Contained</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        backgroundColor: expect.any(String),
      });
    });

    it('renders outlined variant', () => {
      const { container } = renderWithTheme(<Button variant="outlined">Outlined</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        border: expect.stringContaining('solid'),
        backgroundColor: 'transparent',
      });
    });

    it('renders text variant', () => {
      const { container } = renderWithTheme(<Button variant="text">Text</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        backgroundColor: 'transparent',
        border: 'none',
      });
    });
  });

  describe('Colors', () => {
    it('renders with primary color', () => {
      const { container } = renderWithTheme(<Button color="primary">Primary</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with secondary color', () => {
      const { container } = renderWithTheme(<Button color="secondary">Secondary</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with error color', () => {
      const { container } = renderWithTheme(<Button color="error">Error</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with warning color', () => {
      const { container } = renderWithTheme(<Button color="warning">Warning</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with success color', () => {
      const { container } = renderWithTheme(<Button color="success">Success</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with info color', () => {
      const { container } = renderWithTheme(<Button color="info">Info</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with inherit color', () => {
      const { container } = renderWithTheme(<Button color="inherit">Inherit</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<Button size="small">Small</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        fontSize: '0.875rem',
        padding: '6px 12px',
      });
    });

    it('renders medium size', () => {
      const { container } = renderWithTheme(<Button size="medium">Medium</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        fontSize: '1rem',
        padding: '8px 16px',
      });
    });

    it('renders large size', () => {
      const { container } = renderWithTheme(<Button size="large">Large</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        fontSize: '1.125rem',
        padding: '10px 22px',
      });
    });
  });

  describe('States', () => {
    it('handles disabled state', () => {
      const { container } = renderWithTheme(<Button disabled>Disabled</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-disabled', 'true');
      expect(button).toHaveStyle({
        cursor: 'not-allowed',
        opacity: '0.5',
      });
    });

    it('does not call onClick when disabled', () => {
      const handleClick = jest.fn();
      renderWithTheme(
        <Button onClick={handleClick} disabled>
          Click me
        </Button>
      );
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('applies fullWidth', () => {
      const { container } = renderWithTheme(<Button fullWidth>Full Width</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({ width: '100%' });
    });
  });

  describe('Interactions', () => {
    it('calls onClick when clicked', () => {
      const handleClick = jest.fn();
      renderWithTheme(<Button onClick={handleClick}>Click me</Button>);
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard enter key', () => {
      const handleClick = jest.fn();
      renderWithTheme(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard space key', () => {
      const handleClick = jest.fn();
      renderWithTheme(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button'));
      fireEvent.keyDown(button, { key: ' ', code: 'Space' });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Icons', () => {
    it('renders with startIcon', () => {
      // Mock icon component
      const MockIcon = () => <span data-testid="start-icon">→</span>;
      const { container } = renderWithTheme(
        <Button startIcon={<MockIcon />}>With Start Icon</Button>
      );
      expect(container.querySelector('[data-testid="start-icon"]')).toBeInTheDocument();
    });

    it('renders with endIcon', () => {
      // Mock icon component
      const MockIcon = () => <span data-testid="end-icon">←</span>;
      const { container } = renderWithTheme(<Button endIcon={<MockIcon />}>With End Icon</Button>);
      expect(container.querySelector('[data-testid="end-icon"]')).toBeInTheDocument();
    });

    it('renders with both start and end icons', () => {
      const StartIcon = () => <span data-testid="start-icon">→</span>;
      const EndIcon = () => <span data-testid="end-icon">←</span>;
      const { container } = renderWithTheme(
        <Button startIcon={<StartIcon />} endIcon={<EndIcon />}>
          Both Icons
        </Button>
      );
      expect(container.querySelector('[data-testid="start-icon"]')).toBeInTheDocument();
      expect(container.querySelector('[data-testid="end-icon"]')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper role attribute', () => {
      renderWithTheme(<Button>Accessible Button</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('sets aria-disabled when disabled', () => {
      renderWithTheme(<Button disabled>Disabled Button</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('can be focused', () => {
      const { container } = renderWithTheme(<Button>Focusable</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it('has visible focus state', () => {
      const { container } = renderWithTheme(<Button>Focus Test</Button>);
      const button = container.querySelector('button') as HTMLButtonElement;
      // Focus should add outline
      button.focus();
      expect(button).toHaveFocus();
    });
  });

  describe('Combinations', () => {
    it('renders contained primary large button', () => {
      const { container } = renderWithTheme(
        <Button variant="contained" color="primary" size="large">
          Large Primary
        </Button>
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Large Primary');
    });

    it('renders outlined secondary small button', () => {
      const { container } = renderWithTheme(
        <Button variant="outlined" color="secondary" size="small">
          Small Secondary
        </Button>
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Small Secondary');
    });

    it('renders text error medium button with fullWidth', () => {
      const { container } = renderWithTheme(
        <Button variant="text" color="error" size="medium" fullWidth>
          Full Width Error
        </Button>
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveStyle({ width: '100%' });
    });
  });

  describe('Edge Cases', () => {
    it('renders without children', () => {
      const { container } = renderWithTheme(<Button />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    it('handles multiple clicks', () => {
      const handleClick = jest.fn();
      renderWithTheme(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button');
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(3);
    });

    it('preserves custom data attributes', () => {
      const { container } = renderWithTheme(
        <Button data-testid="custom-button" data-value="test">
          Custom Data
        </Button>
      );
      const button = container.querySelector('[data-testid="custom-button"]') as HTMLButtonElement;
      expect(button).toHaveAttribute('data-value', 'test');
    });
  });
});
