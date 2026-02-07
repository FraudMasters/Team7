import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Icon from './Icon';

// Mock lucide-react module with dynamic import simulation
vi.mock('lucide-react', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    User: ({ size, className, style, ...props }: any) => (
      <svg
        data-testid="icon-user"
        width={size}
        height={size}
        className={className}
        style={style}
        {...props}
      >
        <circle cx="12" cy="12" r="10" />
      </svg>
    ),
    Search: ({ size, className, style, ...props }: any) => (
      <svg
        data-testid="icon-search"
        width={size}
        height={size}
        className={className}
        style={style}
        {...props}
      >
        <circle cx="12" cy="12" r="10" />
      </svg>
    ),
    HelpCircle: ({ size, className, style, ...props }: any) => (
      <svg
        data-testid="icon-help-circle"
        width={size}
        height={size}
        className={className}
        style={style}
        {...props}
      >
        <circle cx="12" cy="12" r="10" />
      </svg>
    ),
  };
});

// Mock useEmotionTheme hook
vi.mock('../../../contexts/EmotionThemeContext', () => ({
  useEmotionTheme: () => ({
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    success: { main: '#4caf50' },
    error: { main: '#f44336' },
    warning: { main: '#ff9800' },
    info: { main: '#2196f3' },
    text: {
      primary: '#212121',
      secondary: '#757575',
      disabled: '#9e9e9e',
    },
  }),
  EmotionThemeContext: React.createContext(null),
}));

describe('Icon Component', () => {
  it('renders User icon correctly', async () => {
    render(<Icon name="User" />);
    await waitFor(() => {
      expect(screen.getByTestId('icon-user')).toBeInTheDocument();
    });
  });

  it('renders Search icon correctly', async () => {
    render(<Icon name="Search" />);
    await waitFor(() => {
      expect(screen.getByTestId('icon-search')).toBeInTheDocument();
    });
  });

  it('applies custom size', async () => {
    render(<Icon name="User" size={32} />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('width', '32');
      expect(icon).toHaveAttribute('height', '32');
    });
  });

  it('applies predefined size "small"', async () => {
    render(<Icon name="User" size="small" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('width', '20');
      expect(icon).toHaveAttribute('height', '20');
    });
  });

  it('applies predefined size "medium"', async () => {
    render(<Icon name="User" size="medium" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('width', '24');
      expect(icon).toHaveAttribute('height', '24');
    });
  });

  it('applies predefined size "large"', async () => {
    render(<Icon name="User" size="large" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('width', '32');
      expect(icon).toHaveAttribute('height', '32');
    });
  });

  it('applies custom color', async () => {
    render(<Icon name="User" color="#ff0000" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(255, 0, 0)');
    });
  });

  it('applies primary color from theme', async () => {
    render(<Icon name="User" color="primary" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(25, 118, 210)'); // #1976d2
    });
  });

  it('applies secondary color from theme', async () => {
    render(<Icon name="User" color="secondary" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(156, 39, 176)'); // #9c27b0
    });
  });

  it('applies error color from theme', async () => {
    render(<Icon name="User" color="error" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(244, 67, 54)'); // #f44336
    });
  });

  it('applies custom className', async () => {
    render(<Icon name="User" className="custom-class" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveClass('custom-class');
    });
  });

  it('applies custom style', async () => {
    render(<Icon name="User" style={{ marginTop: '10px' }} />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.marginTop).toBe('10px');
    });
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    render(<Icon name="User" onClick={handleClick} />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      icon.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  it('has pointer cursor when onClick is provided', async () => {
    render(<Icon name="User" onClick={() => {}} />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.cursor).toBe('pointer');
    });
  });

  it('has default cursor when onClick is not provided', async () => {
    render(<Icon name="User" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.cursor).toBe('default');
    });
  });

  it('applies aria-label from title prop', async () => {
    render(<Icon name="User" title="User Icon" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('aria-label', 'User Icon');
    });
  });

  it('uses icon name as aria-label when title is not provided', async () => {
    render(<Icon name="User" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('aria-label', 'User');
    });
  });

  it('has role button when onClick is provided', async () => {
    render(<Icon name="User" onClick={() => {}} />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('role', 'button');
    });
  });

  it('has role img when onClick is not provided', async () => {
    render(<Icon name="User" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('role', 'img');
    });
  });

  it('applies disabled state with reduced opacity', async () => {
    render(<Icon name="User" disabled />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.opacity).toBe('0.5');
    });
  });

  it('applies disabled color when disabled', async () => {
    render(<Icon name="User" disabled color="primary" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(158, 158, 158)'); // disabled color
    });
  });

  it('has aria-disabled attribute when disabled', async () => {
    render(<Icon name="User" disabled />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('aria-disabled', 'true');
    });
  });

  it('handles legacy colorPrimary prop', async () => {
    render(<Icon name="User" colorPrimary />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(25, 118, 210)'); // primary color
    });
  });

  it('handles legacy colorSecondary prop', async () => {
    render(<Icon name="User" colorSecondary />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(156, 39, 176)'); // secondary color
    });
  });

  it('handles legacy colorError prop', async () => {
    render(<Icon name="User" colorError />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(244, 67, 54)'); // error color
    });
  });

  it('handles legacy colorAction prop', async () => {
    render(<Icon name="User" colorAction />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(117, 117, 117)'); // action color (text.secondary)
    });
  });

  it('prioritizes explicit color prop over legacy boolean props', async () => {
    render(<Icon name="User" color="error" colorPrimary />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(244, 67, 54)'); // error color takes precedence
    });
  });

  it('renders with kebab-case icon name', async () => {
    render(<Icon name="help-circle" />);
    await waitFor(() => {
      expect(screen.getByTestId('icon-help-circle')).toBeInTheDocument();
    });
  });

  it('renders with PascalCase icon name', async () => {
    render(<Icon name="HelpCircle" />);
    await waitFor(() => {
      expect(screen.getByTestId('icon-help-circle')).toBeInTheDocument();
    });
  });

  it('size inherit works correctly', async () => {
    render(<Icon name="User" size="inherit" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon).toHaveAttribute('width', 'inherit');
      expect(icon).toHaveAttribute('height', 'inherit');
    });
  });

  it('color inherit works correctly', async () => {
    render(<Icon name="User" color="inherit" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('inherit');
    });
  });

  it('merges custom style with default style', async () => {
    render(
      <Icon name="User" style={{ marginTop: '10px', marginLeft: '5px' }} />
    );
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.marginTop).toBe('10px');
      expect(icon.style.marginLeft).toBe('5px');
    });
  });

  it('prevents click when disabled', async () => {
    const handleClick = vi.fn();
    render(<Icon name="User" onClick={handleClick} disabled />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      icon.click();
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  it('has pointer-events none when disabled', async () => {
    render(<Icon name="User" disabled />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.pointerEvents).toBe('none');
    });
  });

  it('applies success color from theme', async () => {
    render(<Icon name="User" color="success" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(76, 175, 80)'); // #4caf50
    });
  });

  it('applies warning color from theme', async () => {
    render(<Icon name="User" color="warning" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(255, 152, 0)'); // #ff9800
    });
  });

  it('applies info color from theme', async () => {
    render(<Icon name="User" color="info" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(33, 150, 243)'); // #2196f3
    });
  });

  it('applies disabled color from theme', async () => {
    render(<Icon name="User" color="disabled" />);
    await waitFor(() => {
      const icon = screen.getByTestId('icon-user');
      expect(icon.style.color).toBe('rgb(158, 158, 158)'); // #9e9e9e
    });
  });

  it('shows fallback icon when icon not found', async () => {
    render(<Icon name="NonExistentIcon" />);
    await waitFor(() => {
      // Should show SVG fallback
      const fallback = document.querySelector('svg[aria-label="NonExistentIcon"]');
      expect(fallback).toBeInTheDocument();
    });
  });
});
