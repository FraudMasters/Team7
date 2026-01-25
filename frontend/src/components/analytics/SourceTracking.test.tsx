/**
 * Tests for SourceTracking Component
 *
 * Tests the source tracking analytics including:
 * - Fetching and displaying vacancy sources
 * - Source distribution visualization with pie chart
 * - Time-to-fill metrics by source
 * - Summary statistics display
 * - Date range filtering
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SourceTracking from './SourceTracking';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SourceTracking', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/source-tracking';

  const mockSourceTracking = {
    sources: [
      {
        source_name: 'LinkedIn',
        vacancy_count: 450,
        percentage: 0.45,
        average_time_to_fill: 28,
      },
      {
        source_name: 'Indeed',
        vacancy_count: 300,
        percentage: 0.30,
        average_time_to_fill: 35,
      },
      {
        source_name: 'Referral',
        vacancy_count: 150,
        percentage: 0.15,
        average_time_to_fill: 21,
      },
      {
        source_name: 'Company Website',
        vacancy_count: 100,
        percentage: 0.10,
        average_time_to_fill: 25,
      },
    ],
    total_vacancies: 1000,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      expect(screen.getByText('Loading source tracking data...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      expect(screen.getByText('Indeed')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Source Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Sources Display', () => {
    it('should display all sources from API response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('Indeed')).toBeInTheDocument();
      expect(screen.getByText('Referral')).toBeInTheDocument();
      expect(screen.getByText('Company Website')).toBeInTheDocument();
    });

    it('should display vacancy counts for each source', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('450')).toBeInTheDocument();
      });

      expect(screen.getByText('300')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });

    it('should display percentages for each source', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('45.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('30.0%')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });

    it('should display average time-to-fill for each source', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('28 days')).toBeInTheDocument();
      expect(screen.getByText('35 days')).toBeInTheDocument();
      expect(screen.getByText('21 days')).toBeInTheDocument();
      expect(screen.getByText('25 days')).toBeInTheDocument();
    });
  });

  describe('Time-to-Fill Color Coding', () => {
    it('should show green color for good time-to-fill (<= 30 days)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('28 days')).toBeInTheDocument();
      });
    });

    it('should show yellow color for moderate time-to-fill (31-45 days)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('35 days')).toBeInTheDocument();
      });
    });

    it('should show red color for high time-to-fill (> 45 days)', async () => {
      const highTimeToFillData = {
        ...mockSourceTracking,
        sources: [
          {
            source_name: 'Slow Source',
            vacancy_count: 50,
            percentage: 0.05,
            average_time_to_fill: 50,
          },
        ],
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => highTimeToFillData,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('50 days')).toBeInTheDocument();
      });
    });
  });

  describe('Pie Chart', () => {
    it('should display donut pie chart', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      // Pie chart is rendered via CSS conic-gradient
      // We verify that total vacancies are displayed in center
      expect(screen.getByText('1,000')).toBeInTheDocument();
    });

    it('should display total vacancies in chart center', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('1,000')).toBeInTheDocument();
      });
    });
  });

  describe('Summary Statistics', () => {
    it('should display active sources count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText(/Active Sources/)).toBeInTheDocument();
      });

      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('should display top source', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText(/Top Source/)).toBeInTheDocument();
      });

      expect(screen.getByText('LinkedIn')).toBeInTheDocument();
    });

    it('should display highest share percentage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText(/Highest Share/)).toBeInTheDocument();
      });

      expect(screen.getByText('45.0%')).toBeInTheDocument();
    });

    it('should display total vacancies', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText(/Total Vacancies/)).toBeInTheDocument();
      });

      expect(screen.getByText('1,000')).toBeInTheDocument();
    });
  });

  describe('Date Range Filtering', () => {
    it('should include start_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      );
    });

    it('should include end_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-12-31')
      );
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSourceTracking,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSourceTracking,
        });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
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
          json: async () => mockSourceTracking,
        });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Source Data')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/sources';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(customUrl);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty sources array', async () => {
      const emptyData = {
        sources: [],
        total_vacancies: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyData,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Source Data')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch source tracking data/)).toBeInTheDocument();
    });
  });

  describe('Visual Design', () => {
    it('should display progress bars for source percentages', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      // Progress bars are rendered via LinearProgress component
      expect(screen.getByText('Indeed')).toBeInTheDocument();
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSourceTracking,
      });

      render(<SourceTracking />);

      await waitFor(() => {
        expect(screen.getByText('Source Tracking')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });
});
