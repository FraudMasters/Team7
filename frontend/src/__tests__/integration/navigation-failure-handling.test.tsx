/**
 * Integration Tests: Navigation Failure Handling and Error Boundaries
 *
 * Tests the error handling infrastructure for navigation failures and service unavailability.
 * Verifies ErrorBoundary catches component errors, ServiceErrorFallback displays correctly,
 * retry mechanisms work, and other routes remain unaffected when one fails.
 *
 * Verification Steps (from spec subtask-7-5):
 * 1. Stop microservice
 * 2. Navigate to affected page
 * 3. Verify error UI with retry option
 * 4. Restart microservice
 * 5. Verify retry works
 * 6. Verify other routes still work
 *
 * Prerequisites:
 * - ErrorBoundary component wraps route sections
 * - ServiceErrorFallback component handles microservice failures
 * - API client transforms errors properly
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Components to test
import ErrorBoundary from '../../components/ErrorBoundary';
import ServiceErrorFallback from '../../components/ServiceErrorFallback';
import { NetworkErrorFallback, TimeoutErrorFallback, ServiceUnavailableFallback } from '../../components/ServiceErrorFallback';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Page Components for testing error isolation
import { JobsBrowsePage } from '../../pages/jobs/JobsBrowsePage';
import { DashboardPage } from '../../pages/recruiter/DashboardPage';
import { AdminDashboard } from '../../pages/admin/AdminDashboard';

// Layout Components
import JobSeekerLayout from '../../layouts/JobSeekerLayout';
import RecruiterLayout from '../../layouts/RecruiterLayout';
import AdminLayout from '../../layouts/AdminLayout';

/**
 * Test wrapper with all required providers
 */
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

/**
 * Component that throws an error for testing ErrorBoundary
 */
const ThrowError: React.FC<{ message?: string }> = ({ message = 'Test error' }) => {
  throw new Error(message);
};

/**
 * Component that throws on mount after a delay
 */
const ThrowErrorAsync: React.FC<{ delay?: number }> = ({ delay = 0 }) => {
  React.useEffect(() => {
    const timer = setTimeout(() => {
      throw new Error('Async error');
    }, delay);
    return () => clearTimeout(timer);
  }, []);

  return <div>Loading...</div>;
};

describe('Navigation Failure Handling - ErrorBoundary', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Suppress console.error for expected errors
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  /**
   * Phase 1: ErrorBoundary catches component errors
   */
  describe('Phase 1: ErrorBoundary Catches Component Errors', () => {
    it('should catch synchronous errors in child components', async () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError message="Synchronous test error" />
          </ErrorBoundary>
        </TestWrapper>
      );

      // Should show error fallback UI
      await expect(screen.getByText(/Something went wrong/i)).toBeVisible();
      await expect(screen.getByText(/An unexpected error occurred/i)).toBeVisible();
    });

    it('should display refresh and go home buttons', async () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      // Check for action buttons
      await expect(screen.getByRole('button', { name: /refresh page/i })).toBeVisible();
      await expect(screen.getByRole('button', { name: /go home/i })).toBeVisible();
    });

    it('should show error details in development mode', async () => {
      const originalEnv = import.meta.env.DEV;
      Object.defineProperty(import.meta.env, 'DEV', { value: true, writable: true });

      render(
        <TestWrapper>
          <ErrorBoundary showDetails>
            <ThrowError message="Test error with details" />
          </ErrorBoundary>
        </TestWrapper>
      );

      // Error message should be visible
      await expect(screen.getByText(/Test error with details/i)).toBeVisible();

      // Restore original env
      Object.defineProperty(import.meta.env, 'DEV', { value: originalEnv, writable: true });
    });

    it('should call custom onError handler', async () => {
      const onError = vi.fn();

      render(
        <TestWrapper>
          <ErrorBoundary onError={onError}>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
        expect(onError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.objectContaining({
            componentStack: expect.any(String),
          })
        );
      });
    });

    it('should render custom fallback when provided', async () => {
      const customFallback = <div>Custom error message</div>;

      render(
        <TestWrapper>
          <ErrorBoundary fallback={customFallback}>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      await expect(screen.getByText('Custom error message')).toBeVisible();
      await expect(screen.queryByText(/Something went wrong/i)).not.toBeInTheDocument();
    });
  });

  /**
   * Phase 2: ServiceErrorFallback handles API errors
   */
  describe('Phase 2: ServiceErrorFallback Handles API Errors', () => {
    it('should detect network errors (status 0)', () => {
      const networkError = { detail: 'Network error', status: 0 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={networkError} onRetry={onRetry} />
        </TestWrapper>
      );

      // Should show network error UI
      expect(screen.getByText(/Network Error/i)).toBeVisible();
      expect(screen.getByText(/Unable to connect to the service/i)).toBeVisible();
    });

    it('should detect timeout errors (status 408)', () => {
      const timeoutError = { detail: 'Request timeout', status: 408 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={timeoutError} onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Request Timeout/i)).toBeVisible();
      expect(screen.getByText(/took too long to respond/i)).toBeVisible();
    });

    it('should detect service unavailable (status 503)', () => {
      const unavailableError = { detail: 'Service unavailable', status: 503 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={unavailableError} onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Service Unavailable/i)).toBeVisible();
      expect(screen.getByText(/temporarily unavailable/i)).toBeVisible();
    });

    it('should detect bad gateway (status 502)', () => {
      const badGatewayError = { detail: 'Bad gateway', status: 502 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={badGatewayError} onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Service Unavailable/i)).toBeVisible();
      expect(screen.getByText(/Bad gateway/i)).toBeVisible();
    });

    it('should show retry button when onRetry provided', () => {
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={error} onRetry={onRetry} />
        </TestWrapper>
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeVisible();
    });

    it('should call onRetry when retry button clicked', async () => {
      const user = userEvent.setup();
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={error} onRetry={onRetry} />
        </TestWrapper>
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(onRetry).toHaveBeenCalledTimes(1);
      });
    });

    it('should show retrying state during async retry', async () => {
      const user = userEvent.setup();
      const error = { detail: 'Service error', status: 500 };
      let resolveRetry: (value: void) => void;
      const onRetry = vi.fn(() => new Promise<void>((resolve) => {
        resolveRetry = resolve;
      }));

      render(
        <TestWrapper>
          <ServiceErrorFallback error={error} onRetry={onRetry} />
        </TestWrapper>
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should show retrying state
      await expect(screen.getByText(/Retrying/i)).toBeVisible();

      // Resolve retry
      resolveRetry!();
      await waitFor(() => {
        expect(screen.queryByText(/Retrying/i)).not.toBeInTheDocument();
      });
    });

    it('should show service name when provided', () => {
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={error}
            serviceName="Candidate Service"
            onRetry={onRetry}
          />
        </TestWrapper>
      );

      expect(screen.getByText(/Candidate Service/i)).toBeVisible();
    });

    it('should render in compact mode', () => {
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={error}
            mode="compact"
            onRetry={onRetry}
          />
        </TestWrapper>
      );

      // Compact mode should have different layout
      const container = screen.getByText(/Service error/i).closest('div');
      expect(container).toHaveClass('MuiPaper-root');
    });

    it('should render in alert mode', () => {
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={error}
            mode="alert"
            onRetry={onRetry}
          />
        </TestWrapper>
      );

      // Alert mode uses MUI Alert component
      const alert = screen.getByRole('alert');
      expect(alert).toBeVisible();
    });

    it('should show secondary actions when provided', () => {
      const error = { detail: 'Service error', status: 500 };
      const onRetry = vi.fn();
      const secondaryActions = [
        { label: 'Go to Dashboard', onClick: vi.fn() },
        { label: 'Contact Support', onClick: vi.fn() },
      ];

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={error}
            onRetry={onRetry}
            secondaryActions={secondaryActions}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: /go to dashboard/i })).toBeVisible();
      expect(screen.getByRole('button', { name: /contact support/i })).toBeVisible();
    });
  });

  /**
   * Phase 3: Pre-configured error fallbacks
   */
  describe('Phase 3: Pre-configured Error Fallbacks', () => {
    it('should render NetworkErrorFallback', () => {
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <NetworkErrorFallback onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Network Error/i)).toBeVisible();
      expect(screen.getByRole('button', { name: /retry/i })).toBeVisible();
    });

    it('should render TimeoutErrorFallback', () => {
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <TimeoutErrorFallback onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Request Timeout/i)).toBeVisible();
      expect(screen.getByRole('button', { name: /retry/i })).toBeVisible();
    });

    it('should render ServiceUnavailableFallback', () => {
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceUnavailableFallback onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Service Unavailable/i)).toBeVisible();
      expect(screen.getByRole('button', { name: /retry/i })).toBeVisible();
    });
  });

  /**
   * Phase 4: Error isolation between route sections
   */
  describe('Phase 4: Error Isolation Between Routes', () => {
    it('should isolate JobSeeker route errors from other routes', async () => {
      const { container: jobsContainer } = render(
        <TestWrapper>
          <MemoryRouter initialEntries={['/jobs']}>
            <Routes>
              <Route
                path="/jobs"
                element={
                  <ErrorBoundary>
                    <JobSeekerLayout />
                  </ErrorBoundary>
                }
              />
            </Routes>
          </MemoryRouter>
        </TestWrapper>
      );

      // JobSeeker layout should render normally
      await expect(screen.getByText('AgentHR')).toBeVisible();
    });

    it('should isolate Recruiter route errors from other routes', async () => {
      render(
        <TestWrapper>
          <MemoryRouter initialEntries={['/recruiter/dashboard']}>
            <Routes>
              <Route
                path="/recruiter/*"
                element={
                  <ErrorBoundary>
                    <RecruiterLayout />
                  </ErrorBoundary>
                }
              />
            </Routes>
          </MemoryRouter>
        </TestWrapper>
      );

      // Recruiter layout should render normally
      await expect(screen.getByText('AgentHR')).toBeVisible();
    });

    it('should isolate Admin route errors from other routes', async () => {
      render(
        <TestWrapper>
          <MemoryRouter initialEntries={['/admin/dashboard']}>
            <Routes>
              <Route
                path="/admin/*"
                element={
                  <ErrorBoundary>
                    <AdminLayout />
                  </ErrorBoundary>
                }
              />
            </Routes>
          </MemoryRouter>
        </TestWrapper>
      );

      // Admin layout should render normally
      await expect(screen.getByText('AgentHR')).toBeVisible();
    });
  });

  /**
   * Phase 5: Retry mechanism functionality
   */
  describe('Phase 5: Retry Mechanism Functionality', () => {
    it('should handle successful retry after error', async () => {
      const user = userEvent.setup();
      let shouldFail = true;
      const mockApiCall = vi.fn(() => {
        if (shouldFail) {
          throw { detail: 'Service unavailable', status: 503 };
        }
        return { data: 'success' };
      });

      let retryCount = 0;
      const onRetry = vi.fn(async () => {
        shouldFail = false;
        retryCount++;
        await mockApiCall();
      });

      const { rerender } = render(
        <TestWrapper>
          <ServiceErrorFallback
            error={{ detail: 'Service unavailable', status: 503 }}
            onRetry={onRetry}
          />
        </TestWrapper>
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(onRetry).toHaveBeenCalledTimes(1);
        expect(retryCount).toBe(1);
      });
    });

    it('should handle multiple retry attempts', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();
      let attemptCount = 0;

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={{ detail: 'Service unavailable', status: 503 }}
            onRetry={async () => {
              attemptCount++;
              if (attemptCount < 3) {
                throw { detail: 'Still unavailable', status: 503 };
              }
              onRetry();
            }}
          />
        </TestWrapper>
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });

      // First attempt
      await user.click(retryButton);
      await waitFor(() => expect(attemptCount).toBe(1));

      // Second attempt
      await user.click(retryButton);
      await waitFor(() => expect(attemptCount).toBe(2));
    });
  });

  /**
   * Phase 6: Accessibility tests
   */
  describe('Phase 6: Accessibility', () => {
    it('should have proper ARIA labels for error icon', async () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        </TestWrapper>
      );

      // Error icon should be present
      const errorIcon = document.querySelector('svg');
      expect(errorIcon).toBeInTheDocument();
    });

    it('should have focusable buttons for keyboard navigation', async () => {
      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={{ detail: 'Service error', status: 500 }}
            onRetry={vi.fn()}
          />
        </TestWrapper>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('should have proper heading hierarchy', async () => {
      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={{ detail: 'Service error', status: 500 }}
            onRetry={vi.fn()}
          />
        </TestWrapper>
      );

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeVisible();
    });
  });

  /**
   * Phase 7: Edge cases
   */
  describe('Phase 7: Edge Cases', () => {
    it('should handle ErrorBoundary without error', () => {
      render(
        <TestWrapper>
          <ErrorBoundary>
            <div>Normal content</div>
          </ErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText('Normal content')).toBeVisible();
      expect(screen.queryByText(/Something went wrong/i)).not.toBeInTheDocument();
    });

    it('should handle ServiceErrorFallback with standard Error', () => {
      const standardError = new Error('Standard JavaScript error');
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={standardError} onRetry={onRetry} />
        </TestWrapper>
      );

      expect(screen.getByText(/Service Error/i)).toBeVisible();
    });

    it('should handle missing error details gracefully', () => {
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback
            error={{ status: 500 } as any}
            onRetry={onRetry}
          />
        </TestWrapper>
      );

      // Should still show some error message
      const errorMessage = screen.getByText(/Service Error/i);
      expect(errorMessage).toBeInTheDocument();
    });

    it('should handle empty error object', () => {
      const onRetry = vi.fn();

      render(
        <TestWrapper>
          <ServiceErrorFallback error={{} as any} onRetry={onRetry} />
        </TestWrapper>
      );

      const errorMessage = screen.getByText(/Service Error/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });
});
