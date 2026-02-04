import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Alert } from './Alert';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('Alert Component', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithTheme(<Alert message="Test message" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders message correctly', () => {
      renderWithTheme(<Alert message="Test alert message" />);
      expect(screen.getByText('Test alert message')).toBeInTheDocument();
    });

    it('renders title when provided', () => {
      renderWithTheme(<Alert title="Alert Title" message="Test message" />);
      expect(screen.getByText('Alert Title')).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      const { container } = renderWithTheme(
        <Alert message="Test" className="custom-alert" />
      );
      const alert = container.querySelector('.custom-alert');
      expect(alert).toBeInTheDocument();
    });

    it('renders with custom style', () => {
      const { container } = renderWithTheme(
        <Alert message="Test" style={{ margin: '10px' }} />
      );
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toHaveStyle({ margin: '10px' });
    });

    it('has correct role attribute', () => {
      renderWithTheme(<Alert message="Test" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders icon by default', () => {
      const { container } = renderWithTheme(<Alert message="Test" />);
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('does not render icon when showIcon is false', () => {
      const { container } = renderWithTheme(<Alert message="Test" showIcon={false} />);
      const icon = container.querySelector('svg');
      expect(icon).not.toBeInTheDocument();
    });

    it('renders close button when onClose is provided', () => {
      renderWithTheme(<Alert message="Test" onClose={() => {}} />);
      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('does not render close button when onClose is not provided', () => {
      const { container } = renderWithTheme(<Alert message="Test" />);
      const closeButton = container.querySelector('button[aria-label="Close"]');
      expect(closeButton).not.toBeInTheDocument();
    });
  });

  describe('Severity Levels', () => {
    it('renders with success severity', () => {
      const { container } = renderWithTheme(<Alert message="Test" severity="success" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });

    it('renders with info severity (default)', () => {
      const { container } = renderWithTheme(<Alert message="Test" severity="info" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });

    it('renders with warning severity', () => {
      const { container } = renderWithTheme(<Alert message="Test" severity="warning" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });

    it('renders with error severity', () => {
      const { container } = renderWithTheme(<Alert message="Test" severity="error" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('renders standard variant (default)', () => {
      const { container } = renderWithTheme(<Alert message="Test" variant="standard" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });

    it('renders filled variant', () => {
      const { container } = renderWithTheme(<Alert message="Test" variant="filled" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });

    it('renders outlined variant', () => {
      const { container } = renderWithTheme(<Alert message="Test" variant="outlined" />);
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      expect(alert).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('renders action buttons when provided', () => {
      const mockAction = { label: 'Retry', onClick: jest.fn() };
      renderWithTheme(<Alert message="Test" actions={[mockAction]} />);
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });

    it('calls action onClick when clicked', () => {
      const mockAction = { label: 'Undo', onClick: jest.fn() };
      renderWithTheme(<Alert message="Test" actions={[mockAction]} />);
      fireEvent.click(screen.getByRole('button', { name: 'Undo' }));
      expect(mockAction.onClick).toHaveBeenCalledTimes(1);
    });

    it('renders multiple action buttons', () => {
      const actions = [
        { label: 'Retry', onClick: jest.fn() },
        { label: 'Cancel', onClick: jest.fn() },
      ];
      renderWithTheme(<Alert message="Test" actions={actions} />);
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClose when close button is clicked', () => {
      const mockOnClose = jest.fn();
      renderWithTheme(<Alert message="Test" onClose={mockOnClose} />);
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('close button is keyboard accessible', () => {
      const mockOnClose = jest.fn();
      renderWithTheme(<Alert message="Test" onClose={mockOnClose} />);
      const closeButton = screen.getByRole('button', { name: /close/i });
      closeButton.focus();
      expect(document.activeElement).toBe(closeButton);
    });
  });

  describe('Accessibility', () => {
    it('has role="alert" by default', () => {
      renderWithTheme(<Alert message="Test" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('can have custom role', () => {
      renderWithTheme(<Alert message="Test" role="status" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('close button has aria-label', () => {
      renderWithTheme(<Alert message="Test" onClose={() => {}} />);
      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toHaveAttribute('aria-label', 'Close');
    });
  });

  describe('Edge Cases', () => {
    it('renders without title', () => {
      const { container } = renderWithTheme(<Alert message="Test" />);
      const title = container.querySelector('div[style*="font-weight"]');
      expect(title).not.toBeInTheDocument();
    });

    it('renders with empty actions array', () => {
      const { container } = renderWithTheme(<Alert message="Test" actions={[]} />);
      const actions = container.querySelector('div');
      expect(actions).toBeInTheDocument();
    });

    it('handles long text content', () => {
      const longMessage = 'This is a very long alert message that should wrap correctly and not overflow the container boundaries.';
      renderWithTheme(<Alert message={longMessage} />);
      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles special characters in message', () => {
      const message = 'Test <script>alert("xss")</script> message & special chars';
      renderWithTheme(<Alert message={message} />);
      expect(screen.getByText(/Test/)).toBeInTheDocument();
    });
  });

  describe('Combinations', () => {
    it('renders with all props combined', () => {
      const actions = [{ label: 'Action', onClick: jest.fn() }];
      const { container } = renderWithTheme(
        <Alert
          title="Title"
          message="Message"
          severity="error"
          variant="filled"
          actions={actions}
          onClose={() => {}}
          showIcon
        />
      );
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Message')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
      expect(container.querySelector('button[aria-label="Close"]')).toBeInTheDocument();
    });
  });
});
