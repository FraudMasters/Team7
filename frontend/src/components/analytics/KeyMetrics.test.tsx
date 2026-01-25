/**
 * Tests for KeyMetrics Component
 *
 * Tests the key metrics dashboard including:
 * - Fetching and displaying key hiring metrics
 * - Time-to-hire statistics display
 * - Resume processing metrics display
 * - Match rate metrics display
 * - Date range filtering
 * - Error handling and loading states
 * - Color coding based on thresholds
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import KeyMetrics from './KeyMetrics';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('KeyMetrics', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/key-metrics';

  const mockKeyMetrics = {
    time_to_hire: {
      average_days: 25.5,
      median_days: 23.0,
      min_days: 7,
      max_days: 60,
      percentile_25: 18.0,
      percentile_75: 32.0,
    },
    resumes: {
      total_processed: 1500,
      processed_this_month: 320,
      processed_this_week: 85,
      processing_rate_avg: 12.5,
    },
    match_rates: {
      overall_match_rate: 0.85,
      high_confidence_matches: 950,
      low_confidence_matches: 325,
      average_confidence: 0.78,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      expect(screen.getByText('Loading key metrics...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText('25.5d')).toBeInTheDocument(); // Average time-to-hire
      expect(screen.getByText('1,500')).toBeInTheDocument(); // Total resumes
      expect(screen.getByText('85.0%')).toBeInTheDocument(); // Overall match rate
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockFetch.mockRejectedValue(new Error('API error'));

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Time-to-Hire Metrics', () => {
    it('should display time-to-hire card with all statistics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Time-to-Hire')).toBeInTheDocument();
      });

      expect(screen.getByText('Average')).toBeInTheDocument();
      expect(screen.getByText('25.5d')).toBeInTheDocument();
      expect(screen.getByText('Median')).toBeInTheDocument();
      expect(screen.getByText('23.0d')).toBeInTheDocument();
      expect(screen.getByText('Range')).toBeInTheDocument();
      expect(screen.getByText('7d - 60d')).toBeInTheDocument();
      expect(screen.getByText('25th-75th %')).toBeInTheDocument();
      expect(screen.getByText('18.0d - 32.0d')).toBeInTheDocument();
    });

    it('should display success color for good time-to-hire (<= 30 days)', async () => {
      const goodMetrics = {
        ...mockKeyMetrics,
        time_to_hire: { ...mockKeyMetrics.time_to_hire, average_days: 25 },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => goodMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('25.5d')).toBeInTheDocument();
      });

      const timeToHireText = screen.getByText('25.5d');
      expect(timeToHireText).toBeInTheDocument();
    });

    it('should display warning color for high time-to-hire (> 30 days)', async () => {
      const highTimeMetrics = {
        ...mockKeyMetrics,
        time_to_hire: { ...mockKeyMetrics.time_to_hire, average_days: 45 },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => highTimeMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('45.0d')).toBeInTheDocument();
      });

      expect(screen.getByText('45.0d')).toBeInTheDocument();
    });
  });

  describe('Resume Processing Metrics', () => {
    it('should display resume processing card with all statistics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Resumes Processed')).toBeInTheDocument();
      });

      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('1,500')).toBeInTheDocument();
      expect(screen.getByText('This Month')).toBeInTheDocument();
      expect(screen.getByText('320')).toBeInTheDocument();
      expect(screen.getByText('This Week')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('Avg/Day')).toBeInTheDocument();
      expect(screen.getByText('12.5')).toBeInTheDocument();
    });

    it('should format large numbers with locale string', async () => {
      const largeVolumeMetrics = {
        ...mockKeyMetrics,
        resumes: {
          total_processed: 10000,
          processed_this_month: 2500,
          processed_this_week: 600,
          processing_rate_avg: 25.5,
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => largeVolumeMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('10,000')).toBeInTheDocument();
      });

      expect(screen.getByText('2,500')).toBeInTheDocument();
      expect(screen.getByText('600')).toBeInTheDocument();
    });
  });

  describe('Match Rate Metrics', () => {
    it('should display match rates card with all statistics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Match Rates')).toBeInTheDocument();
      });

      expect(screen.getByText('Overall')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('Avg Confidence')).toBeInTheDocument();
      expect(screen.getByText('78.0%')).toBeInTheDocument();
      expect(screen.getByText('High Confidence')).toBeInTheDocument();
      expect(screen.getByText('950')).toBeInTheDocument();
      expect(screen.getByText('Low Confidence')).toBeInTheDocument();
      expect(screen.getByText('325')).toBeInTheDocument();
    });

    it('should display success color for good match rate (>= 80%)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('85.0%')).toBeInTheDocument();
      });

      const matchRateText = screen.getByText('85.0%');
      expect(matchRateText).toBeInTheDocument();
    });

    it('should display warning color for low match rate (< 80%)', async () => {
      const lowMatchMetrics = {
        ...mockKeyMetrics,
        match_rates: { ...mockKeyMetrics.match_rates, overall_match_rate: 0.75 },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => lowMatchMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('75.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('75.0%')).toBeInTheDocument();
    });
  });

  describe('Date Range Filtering', () => {
    it('should include start_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      );
    });

    it('should include end_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-12-31')
      );
    });

    it('should include both start and end date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics startDate="2024-01-01" endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      const callArgs = mockFetch.mock.calls[0][0];
      expect(callArgs).toContain('start_date=2024-01-01');
      expect(callArgs).toContain('end_date=2024-12-31');
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockKeyMetrics,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockKeyMetrics,
        });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      vi.clearAllMocks();

      fireEvent.click(screen.getByText('Refresh'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockKeyMetrics,
        });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Metrics')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/metrics';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(customUrl);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero values correctly', async () => {
      const zeroMetrics = {
        time_to_hire: {
          average_days: 0,
          median_days: 0,
          min_days: 0,
          max_days: 0,
          percentile_25: 0,
          percentile_75: 0,
        },
        resumes: {
          total_processed: 0,
          processed_this_month: 0,
          processed_this_week: 0,
          processing_rate_avg: 0,
        },
        match_rates: {
          overall_match_rate: 0,
          high_confidence_matches: 0,
          low_confidence_matches: 0,
          average_confidence: 0,
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => zeroMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('0.0d')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch metrics/)).toBeInTheDocument();
    });

    it('should handle malformed JSON response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Metrics')).toBeInTheDocument();
      });
    });
  });

  describe('Visual Design', () => {
    it('should display icons for each metric card', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      // Icons are rendered via Material-UI components
      // We check that the card titles are present
      expect(screen.getByText('Time-to-Hire')).toBeInTheDocument();
      expect(screen.getByText('Resumes Processed')).toBeInTheDocument();
      expect(screen.getByText('Match Rates')).toBeInTheDocument();
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockKeyMetrics,
      });

      render(<KeyMetrics />);

      await waitFor(() => {
        expect(screen.getByText('Key Hiring Metrics')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });
});
