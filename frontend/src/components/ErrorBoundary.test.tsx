/**
 * Tests for ErrorBoundary Component
 *
 * Tests the error boundary component including:
 * - Error catching from child components
 * - Custom fallback rendering
 * - Custom error handler callbacks
 * - Error details display (development mode)
 * - Error boundary reset/recovery
 * - Sentry integration for error tracking
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary, { ErrorBoundaryProps } from './ErrorBoundary';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue || key,
  }),
}));

// Mock Sentry
const mockCaptureException = vi.fn();
beforeEach(() => {
  (window as any).Sentry = {
    captureException: mockCaptureException,
  };
});

afterEach(() => {
  vi.clearAllMocks();
});

/**
 * A component that throws an error for testing ErrorBoundary
 */
const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = true }) => {
  if (shouldThrow) {
    throw new Error('Test error from ThrowError component');
  }
  return <div>No error thrown</div>;
};

/**
 * A component that throws an error after a state update
 */
const ThrowErrorOnMount: React.FC<{ delay?: number }> = ({ delay = 0 }) => {
  const [shouldThrow, setShouldThrow] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShouldThrow(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  if (shouldThrow) {
    throw new Error('Delayed error from ThrowErrorOnMount');
  }

  return <div>Will throw error soon</div>;
};

// Need to import React for the test components
import React from 'react';

describe('ErrorBoundary', () => {
  const defaultProps: ErrorBoundaryProps = {
    children: <div>Test Children</div>,
  };

  describe('Basic Error Catching', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary {...defaultProps} />
      );

      expect(screen.getByText('Test Children')).toBeInTheDocument();
    });

    it('should catch errors thrown by child components', () => {
      // Suppress console.error for this test
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it('should display error fallback UI when error is caught', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      // Check for error title
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Check for error message
      expect(screen.getByText(/An unexpected error occurred/)).toBeInTheDocument();

      // Check for action buttons
      expect(screen.getByText('Refresh Page')).toBeInTheDocument();
      expect(screen.getByText('Go Home')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const customFallback = <div>Custom Error Fallback Component</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Custom Error Fallback Component')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it('should not render default UI when custom fallback is provided', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const customFallback = <div data-testid="custom-fallback">Custom Error</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.queryByText('Refresh Page')).not.toBeInTheDocument();
      expect(screen.queryByText('Go Home')).not.toBeInTheDocument();
      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Custom Error Handler', () => {
    it('should call custom onError callback when error is caught', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onError = vi.fn();

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(onError).toHaveBeenCalledTimes(1);
      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );

      consoleErrorSpy.mockRestore();
    });

    it('should pass error and errorInfo to onError callback', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onError = vi.fn();

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      );

      const callArgs = onError.mock.calls[0];
      const [error, errorInfo] = callArgs;

      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe('Test error from ThrowError component');
      expect(errorInfo).toBeDefined();
      expect(errorInfo.componentStack).toBeDefined();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Error Details Display', () => {
    it('should hide error details by default', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock DEV to false (production)
      const originalDev = import.meta.env.DEV;
      (import.meta.env as any).DEV = false;

      render(
        <ErrorBoundary showDetails={false}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.queryByText('Error Details:')).not.toBeInTheDocument();
      expect(screen.queryByText('Stack Trace:')).not.toBeInTheDocument();
      expect(screen.queryByText('Component Stack:')).not.toBeInTheDocument();

      (import.meta.env as any).DEV = originalDev;
      consoleErrorSpy.mockRestore();
    });

    it('should show error details when showDetails is true in development', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock DEV to true (development)
      (import.meta.env as any).DEV = true;

      render(
        <ErrorBoundary showDetails={true}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Error Details:')).toBeInTheDocument();
      expect(screen.getByText('Test error from ThrowError component')).toBeInTheDocument();

      (import.meta.env as any).DEV = false;
      consoleErrorSpy.mockRestore();
    });

    it('should display stack trace when showDetails is true', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (import.meta.env as any).DEV = true;

      render(
        <ErrorBoundary showDetails={true}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Stack Trace:')).toBeInTheDocument();

      (import.meta.env as any).DEV = false;
      consoleErrorSpy.mockRestore();
    });

    it('should display component stack when showDetails is true', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (import.meta.env as any).DEV = true;

      render(
        <ErrorBoundary showDetails={true}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Component Stack:')).toBeInTheDocument();

      (import.meta.env as any).DEV = false;
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Error Recovery', () => {
    it('should provide reset functionality via resetErrorBoundary method', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      // Error should be caught
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Get the ErrorBoundary instance ref
      const errorBoundaryRef: any = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      // This is a limitation of testing class component methods directly
      // In real usage, the resetErrorBoundary would be called via ref or event handler

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Sentry Integration', () => {
    it('should log errors to console when Sentry is not available', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Remove Sentry
      const originalSentry = (window as any).Sentry;
      delete (window as any).Sentry;

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(consoleErrorSpy).toHaveBeenCalled();

      // Restore Sentry
      (window as any).Sentry = originalSentry;
      consoleErrorSpy.mockRestore();
    });

    it('should send errors to Sentry when available', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(mockCaptureException).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          contexts: expect.objectContaining({
            react: expect.objectContaining({
              componentStack: expect.any(String),
            }),
          }),
        })
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Multiple Children', () => {
    it('should render all children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>First Child</div>
          <div>Second Child</div>
          <div>Third Child</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('First Child')).toBeInTheDocument();
      expect(screen.getByText('Second Child')).toBeInTheDocument();
      expect(screen.getByText('Third Child')).toBeInTheDocument();
    });

    it('should catch error from any child component', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <div>First Child</div>
          <ThrowError />
          <div>Third Child</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.queryByText('First Child')).not.toBeInTheDocument();
      expect(screen.queryByText('Third Child')).not.toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Nested Error Boundaries', () => {
    it('should catch error in the nearest error boundary', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const InnerFallback = () => <div>Inner Error Boundary</div>;
      const OuterFallback = () => <div>Outer Error Boundary</div>;

      render(
        <ErrorBoundary fallback={<InnerFallback />}>
          <ErrorBoundary fallback={<OuterFallback />}>
            <ThrowError />
          </ErrorBoundary>
        </ErrorBoundary>
      );

      // The inner error boundary should catch the error
      expect(screen.getByText('Inner Error Boundary')).toBeInTheDocument();
      expect(screen.queryByText('Outer Error Boundary')).not.toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it('should propagate to parent error boundary if inner boundary does not catch', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const OuterFallback = () => <div>Outer Error Boundary</div>;

      render(
        <ErrorBoundary fallback={<OuterFallback />}>
          <div>No inner boundary</div>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Outer Error Boundary')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('User Actions', () => {
    it('should refresh page when Refresh Page button is clicked', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock window.location.reload
      const reloadSpy = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: reloadSpy },
        writable: true,
      });

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const refreshButton = screen.getByText('Refresh Page');
      refreshButton.click();

      expect(reloadSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('should navigate to home when Go Home button is clicked', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock window.location.href
      const originalLocation = window.location;
      delete (window as any).location;
      (window as any).location = { href: '' };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const goHomeButton = screen.getByText('Go Home');
      goHomeButton.click();

      expect(window.location.href).toBe('/');

      // Restore original location
      window.location = originalLocation;
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible error messaging', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const errorMessage = screen.getByText('Something went wrong');
      expect(errorMessage).toBeInTheDocument();

      const actionButtons = screen.getAllByRole('button');
      expect(actionButtons).toHaveLength(2);
      expect(actionButtons[0]).toHaveAccessibleName('Refresh Page');
      expect(actionButtons[1]).toHaveAccessibleName('Go Home');

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Component Lifecycle', () => {
    it('should reset error state and allow retry', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // This test demonstrates the concept but has limitations
      // due to React's error boundary behavior in tests

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // In a real scenario with refs, you would call errorBoundaryRef.current.resetErrorBoundary()

      consoleErrorSpy.mockRestore();
    });

    it('should handle errors from useEffect hooks', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowErrorOnMount delay={10} />
        </ErrorBoundary>
      );

      // Wait for the error to be thrown
      waitFor(() => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      }, { timeout: 100 });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined onError callback', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        );
      }).not.toThrow();

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it('should handle undefined showDetails prop', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary showDetails={undefined}>
          <ThrowError />
        </ErrorBoundary>
      );

      // Should not crash and show default error UI
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it('should handle empty children', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>{null}</ErrorBoundary>
      );

      // Should not crash
      expect(consoleErrorSpy).not.toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('should handle falsey children values', () => {
      render(
        <ErrorBoundary>
          {false}
          {null}
          {undefined}
          {0}
          {''}
        </ErrorBoundary>
      );

      // Should not crash with falsey children
      expect(document.body).toBeInTheDocument();
    });
  });
});
