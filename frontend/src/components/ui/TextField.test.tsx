import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TextField } from './TextField';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('TextField Component', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithTheme(<TextField />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with placeholder', () => {
      renderWithTheme(<TextField placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('renders with label', () => {
      renderWithTheme(<TextField label="Username" />);
      expect(screen.getByText('Username')).toBeInTheDocument();
    });

    it('renders with default value', () => {
      renderWithTheme(<TextField value="default value" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('default value');
    });

    it('renders with custom className', () => {
      const { container } = renderWithTheme(<TextField className="custom-class" />);
      const containerDiv = container.querySelector('.custom-class');
      expect(containerDiv).toBeInTheDocument();
    });

    it('renders with custom style', () => {
      const { container } = renderWithTheme(<TextField style={{ margin: '10px' }} />);
      const containerDiv = container.firstChild as HTMLElement;
      expect(containerDiv).toHaveStyle({ margin: '10px' });
    });

    it('renders with name and id', () => {
      renderWithTheme(<TextField name="test-field" id="test-id" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('name', 'test-field');
      expect(input).toHaveAttribute('id', 'test-id');
    });
  });

  describe('Variants', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<TextField size="small" />);
      const input = container.querySelector('input') as HTMLInputElement;
      expect(input).toHaveStyle({
        minHeight: '32px',
        fontSize: '0.875rem',
      });
    });

    it('renders medium size', () => {
      const { container } = renderWithTheme(<TextField size="medium" />);
      const input = container.querySelector('input') as HTMLInputElement;
      expect(input).toHaveStyle({
        minHeight: '40px',
        fontSize: '1rem',
      });
    });
  });

  describe('Colors', () => {
    it('renders with primary color', () => {
      renderWithTheme(<TextField color="primary" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with secondary color', () => {
      renderWithTheme(<TextField color="secondary" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with error color', () => {
      renderWithTheme(<TextField color="error" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with success color', () => {
      renderWithTheme(<TextField color="success" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  });

  describe('States', () => {
    it('handles disabled state', () => {
      renderWithTheme(<TextField disabled />);
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('handles read-only state', () => {
      renderWithTheme(<TextField readOnly />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('readOnly');
    });

    it('handles error state', () => {
      renderWithTheme(<TextField error />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('displays error message', () => {
      renderWithTheme(<TextField error errorMessage="This field is required" />);
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    it('displays helper text', () => {
      renderWithTheme(<TextField helperText="Enter your name" />);
      expect(screen.getByText('Enter your name')).toBeInTheDocument();
    });

    it('prioritizes error message over helper text', () => {
      renderWithTheme(
        <TextField
          error
          errorMessage="Error message"
          helperText="Helper text"
        />
      );
      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument();
    });

    it('shows required indicator', () => {
      renderWithTheme(<TextField label="Email" required />);
      expect(screen.getByText('Email *')).toBeInTheDocument();
    });

    it('applies fullWidth', () => {
      const { container } = renderWithTheme(<TextField fullWidth />);
      const containerDiv = container.firstChild as HTMLElement;
      expect(containerDiv).toHaveStyle({ width: '100%' });
    });
  });

  describe('Input Types', () => {
    it('renders text input (default)', () => {
      renderWithTheme(<TextField type="text" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders password input', () => {
      renderWithTheme(<TextField type="password" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('password');
    });

    it('renders email input', () => {
      renderWithTheme(<TextField type="email" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('email');
    });

    it('renders number input', () => {
      renderWithTheme(<TextField type="number" />);
      const input = screen.getByRole('spinbutton');
      expect(input).toBeInTheDocument();
    });

    it('renders date input', () => {
      renderWithTheme(<TextField type="date" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('date');
    });

    it('respects min and max on number input', () => {
      renderWithTheme(<TextField type="number" min={0} max={100} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
    });

    it('respects step on number input', () => {
      renderWithTheme(<TextField type="number" step={5} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('step', '5');
    });
  });

  describe('Interactions', () => {
    it('calls onChange when value changes', () => {
      const handleChange = jest.fn();
      renderWithTheme(<TextField onChange={handleChange} />);
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'test' } });
      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('calls onFocus when focused', () => {
      const handleFocus = jest.fn();
      renderWithTheme(<TextField onFocus={handleFocus} />);
      const input = screen.getByRole('textbox');
      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);
    });

    it('calls onBlur when blurred', () => {
      const handleBlur = jest.fn();
      renderWithTheme(<TextField onBlur={handleBlur} />);
      const input = screen.getByRole('textbox');
      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('updates internal value on change (uncontrolled)', () => {
      renderWithTheme(<TextField defaultValue="" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      fireEvent.change(input, { target: { value: 'new value' } });
      expect(input.value).toBe('new value');
    });

    it('handles keyboard events', () => {
      const handleKeyDown = jest.fn();
      renderWithTheme(<TextField onKeyDown={handleKeyDown} />);
      const input = screen.getByRole('textbox');
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles click events', () => {
      const handleClick = jest.fn();
      renderWithTheme(<TextField onClick={handleClick} />);
      const input = screen.getByRole('textbox');
      fireEvent.click(input);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Multiline', () => {
    it('renders textarea when multiline is true', () => {
      renderWithTheme(<TextField multiline />);
      const textarea = screen.getByRole('textbox');
      expect(textarea.tagName.toLowerCase()).toBe('TEXTAREA');
    });

    it('respects rows prop when multiline', () => {
      renderWithTheme(<TextField multiline rows={5} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea).toHaveAttribute('rows', '5');
    });

    it('does not show floating label when multiline', () => {
      renderWithTheme(<TextField multiline label="Description" />);
      expect(screen.getByText('Description')).toBeInTheDocument();
    });
  });

  describe('Adornments', () => {
    it('renders start adornment', () => {
      const { container } = renderWithTheme(
        <TextField startAdornment={<span data-testid="start">$</span>} />
      );
      expect(container.querySelector('[data-testid="start"]')).toBeInTheDocument();
    });

    it('renders end adornment', () => {
      const { container } = renderWithTheme(
        <TextField endAdornment={<span data-testid="end">@</span>} />
      );
      expect(container.querySelector('[data-testid="end"]')).toBeInTheDocument();
    });

    it('renders both adornments', () => {
      const { container } = renderWithTheme(
        <TextField
          startAdornment={<span data-testid="start">$</span>}
          endAdornment={<span data-testid="end">@</span>}
        />
      );
      expect(container.querySelector('[data-testid="start"]')).toBeInTheDocument();
      expect(container.querySelector('[data-testid="end"]')).toBeInTheDocument();
    });
  });

  describe('InputProps', () => {
    it('merges InputProps with existing props', () => {
      renderWithTheme(
        <TextField
          placeholder="Original"
          InputProps={{ placeholder: 'Overridden' }}
        />
      );
      expect(screen.getByPlaceholderText('Overridden')).toBeInTheDocument();
    });

    it('passes through custom input attributes', () => {
      renderWithTheme(
        <TextField inputProps={{ 'data-custom': 'value', autoComplete: 'off' } as any} />
      );
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('data-custom', 'value');
    });
  });

  describe('Accessibility', () => {
    it('has proper role for textbox', () => {
      renderWithTheme(<TextField />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('can be focused', () => {
      renderWithTheme(<TextField />);
      const input = screen.getByRole('textbox');
      input.focus();
      expect(input).toHaveFocus();
    });

    it('maintains focus state', () => {
      renderWithTheme(<TextField label="Test" />);
      const input = screen.getByRole('textbox');
      fireEvent.focus(input);
      expect(input).toHaveFocus();
    });

    it('supports aria-label', () => {
      renderWithTheme(<TextField aria-label="Search field" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-label', 'Search field');
    });

    it('associates helper text with input via aria-describedby', () => {
      renderWithTheme(<TextField helperText="Help text" />);
      const input = screen.getByRole('textbox');
      const helperText = screen.getByText('Help text');

      expect(helperText).toBeInTheDocument();
      expect(helperText).toHaveAttribute('id');
      expect(input).toHaveAttribute('aria-describedby', helperText.id);
    });

    it('associates error message with input via aria-describedby', () => {
      renderWithTheme(
        <TextField
          error
          errorMessage="This field is required"
          helperText="Help text"
        />
      );
      const input = screen.getByRole('textbox');
      const errorMessage = screen.getByText('This field is required');

      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveAttribute('id');
      expect(input).toHaveAttribute('aria-describedby', errorMessage.id);
    });

    it('associates helper text with multiline textarea', () => {
      renderWithTheme(<TextField multiline helperText="Enter your description" />);
      const textarea = screen.getByRole('textbox');
      const helperText = screen.getByText('Enter your description');

      expect(helperText).toBeInTheDocument();
      expect(helperText).toHaveAttribute('id');
      expect(textarea).toHaveAttribute('aria-describedby', helperText.id);
    });

    it('shows non-floating label for multiline', () => {
      renderWithTheme(<TextField multiline label="Description" />);
      expect(screen.getByText('Description')).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('respects maxLength', () => {
      renderWithTheme(<TextField maxLength={10} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('maxlength', '10');
    });

    it('respects minLength', () => {
      renderWithTheme(<TextField minLength={3} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('minlength', '3');
    });

    it('respects pattern attribute', () => {
      renderWithTheme(<TextField inputProps={{ pattern: '[0-9]*' } as any} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('pattern', '[0-9]*');
    });
  });

  describe('Edge Cases', () => {
    it('renders without label or placeholder', () => {
      renderWithTheme(<TextField />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('handles controlled component with empty value', () => {
      renderWithTheme(<TextField value="" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('');
    });

    it('handles controlled component updates', () => {
      const { rerender } = renderWithTheme(<TextField value="initial" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('initial');

      rerender(
        <EmotionThemeProvider>
          <TextField value="updated" />
        </EmotionThemeProvider>
      );
      expect(input.value).toBe('updated');
    });

    it('preserves custom data attributes', () => {
      renderWithTheme(
        <TextField data-testid="custom-field" data-value="test" />
      );
      expect(screen.getByTestId('custom-field')).toBeInTheDocument();
    });

    it('handles ref forwarding', () => {
      const ref = React.createRef<HTMLDivElement>();
      renderWithTheme(<TextField ref={ref} />);
      expect(ref.current).toBeInTheDocument();
    });

    it('handles inputRef forwarding', () => {
      const inputRef = React.createRef<HTMLInputElement>();
      renderWithTheme(<TextField inputRef={inputRef} />);
      expect(inputRef.current).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    it('works with react-hook-form pattern', () => {
      const MockController = ({ render }: any) => {
        const [value, setValue] = React.useState('');
        return render({
          field: {
            value,
            onChange: (e: any) => setValue(e.target.value),
          },
        });
      };

      renderWithTheme(
        <MockController
          render={({ field }: any) => (
            <TextField
              {...field}
              label="Controlled Field"
              error={false}
            />
          )}
        />
      );

      const input = screen.getByRole('textbox') as HTMLInputElement;
      fireEvent.change(input, { target: { value: 'test value' } });
      expect(input.value).toBe('test value');
    });
  });
});
