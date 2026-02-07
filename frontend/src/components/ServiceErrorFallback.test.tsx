/**
 * Tests for ServiceErrorFallback Component
 *
 * Tests the service error fallback component including:
 * - Basic rendering with different error types
 * - Retry functionality
 * - Display modes (fullPage, compact, alert)
 * - Service name display
 * - Secondary actions
 * - Error details expansion
 * - Pre-configured fallback components
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import ServiceErrorFallback, {
  ServiceErrorFallbackProps,
  NetworkErrorFallback,
  TimeoutErrorFallback,
  ServiceUnavailableFallback,
  BadGatewayFallback,
} from './ServiceErrorFallback';
import type { ApiError } from '@/types/api';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue || key,
  }),
}));

// Mock window.location for go home button
const mockLocation = { href: '' };
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('ServiceErrorFallback', () => {
  const defaultProps: ServiceErrorFallbackProps = {
    error: { detail: 'Test error message', status: 500 },
  };

  describe('Basic Rendering', () => {
    it('should render error title and message', () => {
      render(<ServiceErrorFallback {...defaultProps} />);

      expect(screen.getByText('Service Error')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('should render custom title when provided', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          title="Custom Error Title"
        />
      );

      expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
      expect(screen.queryByText('Service Error')).not.toBeInTheDocument();
    });

    it('should render custom message when provided', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          message="Custom error message"
        />
      );

      expect(screen.getByText('Custom error message')).toBeInTheDocument();
      expect(screen.queryByText('Test error message')).not.toBeInTheDocument();
    });

    it('should render service name when provided', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          serviceName="Candidate Service"
        />
      );

      expect(screen.getByText(/Test error message \(Candidate Service\)/)).toBeInTheDocument();
    });

    it('should handle Error objects', () => {
      render(
        <ServiceErrorFallback
          error={new Error('Standard JavaScript Error')}
        />
      );

      expect(screen.getByText('Standard JavaScript Error')).toBeInTheDocument();
    });
  });

  describe('Error Type Detection', () => {
    it('should display network error for status 0', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Network error', status: 0 }}
        />
      );

      expect(screen.getByText('Network Error')).toBeInTheDocument();
    });

    it('should display timeout error for status 408', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Timeout error', status: 408 }}
        />
      );

      expect(screen.getByText('Request Timeout')).toBeInTheDocument();
    });

    it('should display service unavailable for status 503', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Service unavailable', status: 503 }}
        />
      );

      expect(screen.getByText('Service Unavailable')).toBeInTheDocument();
    });

    it('should display bad gateway for status 502', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Bad gateway', status: 502 }}
        />
      );

      expect(screen.getByText('Service Unavailable')).toBeInTheDocument();
    });

    it('should detect timeout from error message', () => {
      render(
        <ServiceErrorFallback
          error={new Error('Request timeout after 30 seconds')}
        />
      );

      expect(screen.getByText('Request Timeout')).toBeInTheDocument();
    });

    it('should detect network error from error message', () => {
      render(
        <ServiceErrorFallback
          error={new Error('Network connection failed')}
        />
      );

      expect(screen.getByText('Network Error')).toBeInTheDocument();
    });
  });

  describe('Retry Functionality', () => {
    it('should show retry button when onRetry is provided', () => {
      const mockRetry = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={mockRetry}
        />
      );

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should not show retry button when showRetry is false', () => {
      const mockRetry = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={mockRetry}
          showRetry={false}
        />
      );

      expect(screen.queryByText('Retry')).not.toBeInTheDocument();
    });

    it('should not show retry button when onRetry is not provided', () => {
      render(<ServiceErrorFallback {...defaultProps} />);

      expect(screen.queryByText('Retry')).not.toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', async () => {
      const mockRetry = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={mockRetry}
        />
      );

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      expect(mockRetry).toHaveBeenCalledTimes(1);
    });

    it('should handle async retry function', async () => {
      const mockRetry = vi.fn().mockResolvedValue(undefined);

      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={mockRetry}
        />
      );

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      expect(mockRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Display Modes', () => {
    it('should render in fullPage mode by default', () => {
      const { container } = render(
        <ServiceErrorFallback {...defaultProps} />
      );

      expect(container.querySelector('paper')).toBeInTheDocument();
    });

    it('should render in compact mode', () => {
      const { container } = render(
        <ServiceErrorFallback
          {...defaultProps}
          mode="compact"
        />
      );

      expect(screen.getByText('Test error message')).toBeInTheDocument();
      // Compact mode doesn't have the full paper layout
      expect(container.querySelector('[class*="Paper"]')).toBeInTheDocument();
    });

    it('should render in alert mode', () => {
      const { container } = render(
        <ServiceErrorFallback
          {...defaultProps}
          mode="alert"
          onRetry={vi.fn()}
        />
      );

      // Alert mode uses MuiAlert
      expect(container.querySelector('[class*="MuiAlert"]')).toBeInTheDocument();
    });
  });

  describe('Secondary Actions', () => {
    it('should render secondary actions when provided', () => {
      const mockAction = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          secondaryActions={[
            { label: 'Go to Dashboard', onClick: mockAction },
          ]}
        />
      );

      expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
    });

    it('should call secondary action on click', () => {
      const mockAction = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          secondaryActions={[
            { label: 'Go to Dashboard', onClick: mockAction },
          ]}
        />
      );

      const actionButton = screen.getByText('Go to Dashboard');
      fireEvent.click(actionButton);

      expect(mockAction).toHaveBeenCalledTimes(1);
    });

    it('should render multiple secondary actions', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          secondaryActions={[
            { label: 'Action 1', onClick: vi.fn() },
            { label: 'Action 2', onClick: vi.fn() },
            { label: 'Action 3', onClick: vi.fn() },
          ]}
        />
      );

      expect(screen.getByText('Action 1')).toBeInTheDocument();
      expect(screen.getByText('Action 2')).toBeInTheDocument();
      expect(screen.getByText('Action 3')).toBeInTheDocument();
    });
  });

  describe('Home Button', () => {
    it('should show home button when showHomeButton is true', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showHomeButton={true}
        />
      );

      expect(screen.getByText('Go Home')).toBeInTheDocument();
    });

    it('should navigate to home when home button is clicked', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showHomeButton={true}
        />
      );

      const homeButton = screen.getByText('Go Home');
      fireEvent.click(homeButton);

      expect(window.location.href).toBe('/');
    });
  });

  describe('Error Details', () => {
    it('should not show error details by default', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showDetails={false}
        />
      );

      expect(screen.queryByText('Error Details:')).not.toBeInTheDocument();
    });

    it('should show error details when showDetails is true', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showDetails={true}
        />
      );

      expect(screen.getByText('Show Error Details')).toBeInTheDocument();
    });

    it('should expand error details when toggle is clicked', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showDetails={true}
        />
      );

      const toggleButton = screen.getByText('Show Error Details');
      fireEvent.click(toggleButton);

      expect(screen.getByText('Error Details:')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('should collapse error details when toggle is clicked again', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          showDetails={true}
        />
      );

      // Expand
      fireEvent.click(screen.getByText('Show Error Details'));
      expect(screen.getByText('Error Details:')).toBeInTheDocument();

      // Collapse
      fireEvent.click(screen.getByText('Hide Error Details'));
      expect(screen.queryByText('Error Details:')).not.toBeInTheDocument();
    });

    it('should display status code when available', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Error', status: 503 }}
          showDetails={true}
        />
      );

      // Expand details
      fireEvent.click(screen.getByText('Show Error Details'));

      expect(screen.getByText('Status Code: 503')).toBeInTheDocument();
    });
  });

  describe('Additional Info', () => {
    it('should render additional info when provided', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          additionalInfo={<div>Additional helpful information</div>}
        />
      );

      expect(screen.getByText('Additional helpful information')).toBeInTheDocument();
    });
  });

  describe('Pre-configured Fallbacks', () => {
    it('should render NetworkErrorFallback with correct defaults', () => {
      render(<NetworkErrorFallback />);

      expect(screen.getByText('Network Error')).toBeInTheDocument();
      expect(screen.getByText(/check your internet connection/)).toBeInTheDocument();
    });

    it('should render TimeoutErrorFallback with correct defaults', () => {
      render(<TimeoutErrorFallback />);

      expect(screen.getByText('Request Timeout')).toBeInTheDocument();
      expect(screen.getByText(/took too long to respond/)).toBeInTheDocument();
    });

    it('should render ServiceUnavailableFallback with correct defaults', () => {
      render(<ServiceUnavailableFallback />);

      expect(screen.getByText('Service Unavailable')).toBeInTheDocument();
      expect(screen.getByText(/temporarily unavailable/)).toBeInTheDocument();
    });

    it('should render BadGatewayFallback with correct defaults', () => {
      render(<BadGatewayFallback />);

      expect(screen.getByText('Service Unavailable')).toBeInTheDocument();
      expect(screen.getByText(/Bad gateway/)).toBeInTheDocument();
    });

    it('should allow override of pre-configured fallback props', () => {
      render(
        <NetworkErrorFallback
          serviceName="Custom Service"
          onRetry={vi.fn()}
        />
      );

      expect(screen.getByText(/Custom Service/)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper button labels', () => {
      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={vi.fn()}
          showHomeButton={true}
        />
      );

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /go home/i })).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      const mockRetry = vi.fn();

      render(
        <ServiceErrorFallback
          {...defaultProps}
          onRetry={mockRetry}
        />
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      retryButton.focus();

      expect(retryButton).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('should handle error with no detail message', () => {
      render(
        <ServiceErrorFallback
          error={{ status: 500 } as ApiError}
        />
      );

      // Should show default message
      expect(screen.getByText('Service Error')).toBeInTheDocument();
    });

    it('should handle empty error object', () => {
      render(
        <ServiceErrorFallback
          error={{} as ApiError}
        />
      );

      expect(screen.getByText('Service Error')).toBeInTheDocument();
    });

    it('should handle error with undefined status', () => {
      render(
        <ServiceErrorFallback
          error={{ detail: 'Some error' }}
        />
      );

      expect(screen.getByText('Some error')).toBeInTheDocument();
    });
  });
});
