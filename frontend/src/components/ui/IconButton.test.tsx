import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { IconButton } from './IconButton';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('IconButton Component', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithTheme(<IconButton name="Menu" aria-label="Menu" />);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders with icon name', () => {
      renderWithTheme(<IconButton name="Search" aria-label="Search" />);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders with default props', () => {
      const { container } = renderWithTheme(<IconButton name="Check" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('renders with custom className', () => {
      const { container } = renderWithTheme(
        <IconButton name="Check" className="custom-class" aria-label="Check" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveClass('custom-class');
    });

    it('renders with custom style', () => {
      const { container } = renderWithTheme(
        <IconButton name="Check" style={{ margin: '10px' }} aria-label="Check" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({ margin: '10px' });
    });

    it('renders with aria-label', () => {
      renderWithTheme(<IconButton name="Close" aria-label="Close dialog" />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Close dialog');
    });

    it('renders with custom type', () => {
      const { container } = renderWithTheme(
        <IconButton name="Submit" type="submit" aria-label="Submit" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('renders with tabIndex', () => {
      const { container } = renderWithTheme(
        <IconButton name="Skip" tabIndex={-1} aria-label="Skip" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveAttribute('tabIndex', '-1');
    });
  });

  describe('Colors', () => {
    it('renders with inherit color', () => {
      const { container } = renderWithTheme(<IconButton name="Check" color="inherit" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with primary color', () => {
      const { container } = renderWithTheme(<IconButton name="Check" color="primary" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with secondary color', () => {
      const { container } = renderWithTheme(
        <IconButton name="Check" color="secondary" aria-label="Check" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with error color', () => {
      const { container } = renderWithTheme(<IconButton name="Delete" color="error" aria-label="Delete" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });

    it('renders with default color', () => {
      const { container } = renderWithTheme(<IconButton name="Check" color="default" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<IconButton name="Check" size="small" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        width: '32px',
        height: '32px',
        padding: '5px',
      });
    });

    it('renders medium size', () => {
      const { container } = renderWithTheme(<IconButton name="Check" size="medium" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        width: '40px',
        height: '40px',
        padding: '8px',
      });
    });

    it('renders large size', () => {
      const { container } = renderWithTheme(<IconButton name="Check" size="large" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toHaveStyle({
        width: '48px',
        height: '48px',
        padding: '12px',
      });
    });
  });

  describe('States', () => {
    it('handles disabled state', () => {
      const { container } = renderWithTheme(<IconButton name="Check" disabled aria-label="Check" />);
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
        <IconButton name="Check" onClick={handleClick} disabled aria-label="Check" />
      );
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Edge Styling', () => {
    it('renders with start edge', () => {
      const { container } = renderWithTheme(
        <IconButton name="ChevronLeft" edge="start" aria-label="Previous" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveStyle({ marginLeft: '8px' });
    });

    it('renders with end edge', () => {
      const { container } = renderWithTheme(
        <IconButton name="ChevronRight" edge="end" aria-label="Next" />
      );
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toHaveStyle({ marginRight: '8px' });
    });

    it('renders without edge', () => {
      const { container } = renderWithTheme(<IconButton name="Check" edge={false} aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClick when clicked', () => {
      const handleClick = jest.fn();
      renderWithTheme(<IconButton name="Check" onClick={handleClick} aria-label="Check" />);
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard enter key', () => {
      const handleClick = jest.fn();
      renderWithTheme(<IconButton name="Check" onClick={handleClick} aria-label="Check" />);
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard space key', () => {
      const handleClick = jest.fn();
      renderWithTheme(<IconButton name="Check" onClick={handleClick} aria-label="Check" />);
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: ' ', code: 'Space' });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has proper role attribute', () => {
      renderWithTheme(<IconButton name="Check" aria-label="Check" />);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('sets aria-disabled when disabled', () => {
      renderWithTheme(<IconButton name="Check" disabled aria-label="Check" />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('can be focused', () => {
      const { container } = renderWithTheme(<IconButton name="Check" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it('has visible focus state', () => {
      const { container } = renderWithTheme(<IconButton name="Check" aria-label="Check" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      button.focus();
      expect(button).toHaveFocus();
    });

    it('generates aria-label from name if not provided', () => {
      renderWithTheme(<IconButton name="Menu" />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Menu');
    });
  });

  describe('Edge Cases', () => {
    it('renders without icon name', () => {
      const { container } = renderWithTheme(<IconButton aria-label="Empty" />);
      const button = container.querySelector('button') as HTMLButtonElement;
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    it('handles multiple clicks', () => {
      const handleClick = jest.fn();
      renderWithTheme(<IconButton name="Check" onClick={handleClick} aria-label="Check" />);
      const button = screen.getByRole('button');
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(3);
    });

    it('preserves custom data attributes', () => {
      const { container } = renderWithTheme(
        <IconButton name="Check" data-testid="custom-button" data-value="test" aria-label="Check" />
      );
      const button = container.querySelector('[data-testid="custom-button"]') as HTMLButtonElement;
      expect(button).toHaveAttribute('data-value', 'test');
    });
  });
});
