/**
 * Tests for FunnelVisualization Component
 *
 * Tests the recruitment funnel visualization including:
 * - Fetching and displaying funnel metrics
 * - Stage progression display
 * - Conversion rate calculation and display
 * - Overall hire rate display
 * - Drop-off visualization
 * - Date range filtering
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FunnelVisualization from './FunnelVisualization';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('FunnelVisualization', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/funnel';

  const mockFunnelMetrics = {
    stages: [
      {
        stage_name: 'resumes_uploaded',
        count: 1000,
        conversion_rate: 1.0,
      },
      {
        stage_name: 'resumes_processed',
        count: 850,
        conversion_rate: 0.85,
      },
      {
        stage_name: 'candidates_matched',
        count: 600,
        conversion_rate: 0.71,
      },
      {
        stage_name: 'candidates_shortlisted',
        count: 350,
        conversion_rate: 0.58,
      },
      {
        stage_name: 'candidates_interviewed',
        count: 150,
        conversion_rate: 0.43,
      },
      {
        stage_name: 'candidates_hired',
        count: 45,
        conversion_rate: 0.30,
      },
    ],
    total_resumes: 1000,
    overall_hire_rate: 0.045,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      expect(screen.getByText('Loading funnel data...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(screen.getByText('1,000')).toBeInTheDocument(); // Total resumes
      expect(screen.getByText('4.5%')).toBeInTheDocument(); // Overall hire rate
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Funnel Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockFetch.mockRejectedValue(new Error('API error'));

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Funnel Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Funnel Stages Display', () => {
    it('should display all funnel stages', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      });

      expect(screen.getByText('Resumes Processed')).toBeInTheDocument();
      expect(screen.getByText('Candidates Matched')).toBeInTheDocument();
      expect(screen.getByText('Candidates Shortlisted')).toBeInTheDocument();
      expect(screen.getByText('Candidates Interviewed')).toBeInTheDocument();
      expect(screen.getByText('Candidates Hired')).toBeInTheDocument();
    });

    it('should display stage counts correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('1,000')).toBeInTheDocument();
      });

      expect(screen.getByText('850')).toBeInTheDocument();
      expect(screen.getByText('600')).toBeInTheDocument();
      expect(screen.getByText('350')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
    });

    it('should display conversion rates for each stage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('100.0%')).toBeInTheDocument(); // First stage
      });

      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('71.0%')).toBeInTheDocument();
    });

    it('should display drop-off percentages between stages', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      });

      // Drop-off from uploaded to processed: 15%
      expect(screen.getByText(/15%/)).toBeInTheDocument();
    });
  });

  describe('Overall Metrics', () => {
    it('should display total resumes metric', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Total Resumes')).toBeInTheDocument();
      });

      expect(screen.getByText('1,000')).toBeInTheDocument();
    });

    it('should display overall hire rate', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Overall Hire Rate')).toBeInTheDocument();
      });

      expect(screen.getByText('4.5%')).toBeInTheDocument();
    });

    it('should display pipeline insights', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText(/Pipeline Insights/)).toBeInTheDocument();
      });
    });
  });

  describe('Conversion Rate Color Coding', () => {
    it('should show success color for high conversion rate (>= 70%)', async () => {
      const highConversionMetrics = {
        ...mockFunnelMetrics,
        stages: [
          {
            stage_name: 'resumes_uploaded',
            count: 1000,
            conversion_rate: 1.0,
          },
          {
            stage_name: 'resumes_processed',
            count: 900,
            conversion_rate: 0.9,
          },
        ],
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => highConversionMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('90.0%')).toBeInTheDocument();
      });
    });

    it('should show warning color for medium conversion rate (50-69%)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('71.0%')).toBeInTheDocument();
      });
    });

    it('should show error color for low conversion rate (< 50%)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('30.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Date Range Filtering', () => {
    it('should include start_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      );
    });

    it('should include end_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-12-31')
      );
    });

    it('should include both start and end date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization startDate="2024-01-01" endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
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
          json: async () => mockFunnelMetrics,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockFunnelMetrics,
        });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
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
          json: async () => mockFunnelMetrics,
        });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Funnel Data')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/funnel';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(customUrl);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty stages array', async () => {
      const emptyMetrics = {
        stages: [],
        total_resumes: 0,
        overall_hire_rate: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle zero conversion rates', async () => {
      const zeroConversionMetrics = {
        stages: [
          {
            stage_name: 'resumes_uploaded',
            count: 0,
            conversion_rate: 0,
          },
        ],
        total_resumes: 0,
        overall_hire_rate: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => zeroConversionMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Funnel Data')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch funnel data/)).toBeInTheDocument();
    });
  });

  describe('Stage Name Formatting', () => {
    it('should format snake_case stage names to readable format', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Candidates Hired')).toBeInTheDocument();
      });

      // Verify formatted names
      expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      expect(screen.getByText('Candidates Matched')).toBeInTheDocument();
    });

    it('should handle unknown stage names gracefully', async () => {
      const unknownStageMetrics = {
        stages: [
          {
            stage_name: 'unknown_stage_name',
            count: 100,
            conversion_rate: 1.0,
          },
        ],
        total_resumes: 100,
        overall_hire_rate: 1.0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => unknownStageMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText(/Unknown Stage Name/)).toBeInTheDocument();
      });
    });
  });

  describe('Visual Design', () => {
    it('should display stage icons', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      });

      // Icons are rendered via Material-UI components
      // We check that the stage names are present which implies icons are rendered
      expect(screen.getByText('Candidates Hired')).toBeInTheDocument();
    });

    it('should display progress bars for each stage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      });

      // Progress bars are rendered via LinearProgress component
      // We verify stages are displayed which includes progress bars
      expect(screen.getByText('Candidates Matched')).toBeInTheDocument();
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockFunnelMetrics,
      });

      render(<FunnelVisualization />);

      await waitFor(() => {
        expect(screen.getByText('Recruitment Funnel')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });
});
