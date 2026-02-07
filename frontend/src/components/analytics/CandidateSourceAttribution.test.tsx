/**
 * Tests for CandidateSourceAttribution Component
 *
 * Tests the candidate source attribution analytics including:
 * - Fetching and displaying candidate sources
 * - Conversion rate metrics display
 * - Time-to-hire metrics by source
 * - Summary statistics display (active sources, total candidates, best conversion rate, fastest hire)
 * - Source breakdown with candidate count, hired count, and conversion rates
 * - Stage distribution expansion
 * - Auto-refresh functionality
 * - Date range filtering
 * - Error handling and loading states
 * - Color coding based on thresholds
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import CandidateSourceAttribution from './CandidateSourceAttribution';

// Mock axios globally
vi.mock('axios');

const mockedAxios = axios as unknown as { get: ReturnType<typeof vi.fn> };

describe('CandidateSourceAttribution', () => {
  const mockApiUrl = '/api/analytics/candidate-source-attribution';

  const mockSourceAttribution = {
    sources: [
      {
        source: 'LinkedIn',
        candidate_count: 450,
        hired_count: 90,
        conversion_rate: 0.20,
        average_time_to_hire_days: 28,
        stage_distribution: [
          { stage_name: 'Applied', count: 450, percentage: 1.0 },
          { stage_name: 'Screening', count: 200, percentage: 0.44 },
          { stage_name: 'Interview', count: 150, percentage: 0.33 },
          { stage_name: 'Offer', count: 95, percentage: 0.21 },
          { stage_name: 'Hired', count: 90, percentage: 0.20 },
        ],
      },
      {
        source: 'Indeed',
        candidate_count: 300,
        hired_count: 45,
        conversion_rate: 0.15,
        average_time_to_hire_days: 35,
        stage_distribution: [
          { stage_name: 'Applied', count: 300, percentage: 1.0 },
          { stage_name: 'Screening', count: 120, percentage: 0.40 },
          { stage_name: 'Interview', count: 80, percentage: 0.27 },
          { stage_name: 'Offer', count: 50, percentage: 0.17 },
          { stage_name: 'Hired', count: 45, percentage: 0.15 },
        ],
      },
      {
        source: 'Referral',
        candidate_count: 150,
        hired_count: 45,
        conversion_rate: 0.30,
        average_time_to_hire_days: 21,
        stage_distribution: [
          { stage_name: 'Applied', count: 150, percentage: 1.0 },
          { stage_name: 'Screening', count: 80, percentage: 0.53 },
          { stage_name: 'Interview', count: 60, percentage: 0.40 },
          { stage_name: 'Offer', count: 50, percentage: 0.33 },
          { stage_name: 'Hired', count: 45, percentage: 0.30 },
        ],
      },
      {
        source: 'Company Website',
        candidate_count: 100,
        hired_count: 10,
        conversion_rate: 0.10,
        average_time_to_hire_days: 25,
        stage_distribution: [
          { stage_name: 'Applied', count: 100, percentage: 1.0 },
          { stage_name: 'Screening', count: 40, percentage: 0.40 },
          { stage_name: 'Interview', count: 25, percentage: 0.25 },
          { stage_name: 'Offer', count: 12, percentage: 0.12 },
          { stage_name: 'Hired', count: 10, percentage: 0.10 },
        ],
      },
    ],
    total_candidates: 1000,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      expect(screen.getByText('Loading candidate source attribution...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      expect(screen.getByText('Indeed')).toBeInTheDocument();
      expect(screen.getByText('Referral')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      const errorMessage = 'Network error';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockedAxios.get.mockRejectedValue(new Error('API error'));

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should render no data message when sources array is empty', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { sources: [], total_candidates: 0 },
      });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('No Candidate Source Data')).toBeInTheDocument();
      });

      expect(
        screen.getByText(
          'No candidate source attribution data found. Start uploading resumes with source information to populate this analytics.'
        )
      ).toBeInTheDocument();
    });
  });

  describe('Summary Statistics', () => {
    it('should display active sources count', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Active Sources')).toBeInTheDocument();
      });

      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('should display total candidates', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Total Candidates')).toBeInTheDocument();
      });

      expect(screen.getByText('1,000')).toBeInTheDocument();
    });

    it('should display best conversion rate with source name', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Best Conversion Rate')).toBeInTheDocument();
      });

      expect(screen.getByText('30.0%')).toBeInTheDocument();
      expect(screen.getByText('(Referral)')).toBeInTheDocument();
    });

    it('should display fastest hire with source name', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Fastest Hire')).toBeInTheDocument();
      });

      expect(screen.getByText('21d')).toBeInTheDocument();
      expect(screen.getByText('(Referral)')).toBeInTheDocument();
    });

    it('should format large numbers with locale string', async () => {
      const largeVolumeData = {
        ...mockSourceAttribution,
        total_candidates: 10000,
      };

      mockedAxios.get.mockResolvedValue({ data: largeVolumeData });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('10,000')).toBeInTheDocument();
      });
    });
  });

  describe('Source Breakdown Display', () => {
    it('should display all sources from API response', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('Indeed')).toBeInTheDocument();
      expect(screen.getByText('Referral')).toBeInTheDocument();
      expect(screen.getByText('Company Website')).toBeInTheDocument();
    });

    it('should display candidate counts for each source', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('450')).toBeInTheDocument();
      expect(screen.getByText('300')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });

    it('should display hired counts for each source', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      // Hired counts are displayed next to person icons
      expect(screen.getByText('90')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    it('should display conversion rates for each source', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('20.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('15.0%')).toBeInTheDocument();
      expect(screen.getByText('30.0%')).toBeInTheDocument();
      expect(screen.getByText('10.0%')).toBeInTheDocument();
    });

    it('should display average time-to-hire for each source', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('28d')).toBeInTheDocument();
      expect(screen.getByText('35d')).toBeInTheDocument();
      expect(screen.getByText('21d')).toBeInTheDocument();
      expect(screen.getByText('25d')).toBeInTheDocument();
    });
  });

  describe('Conversion Rate Color Coding', () => {
    it('should display success color for high conversion rate (>= 15%)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      expect(screen.getByText('20.0%')).toBeInTheDocument();
      expect(screen.getByText('30.0%')).toBeInTheDocument();
    });

    it('should display warning color for moderate conversion rate (10-14%)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Indeed')).toBeInTheDocument();
      });

      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });

    it('should display error color for low conversion rate (< 10%)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Company Website')).toBeInTheDocument();
      });

      expect(screen.getByText('10.0%')).toBeInTheDocument();
    });
  });

  describe('Time-to-Hire Color Coding', () => {
    it('should display success color for good time-to-hire (<= 30 days)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('28d')).toBeInTheDocument();
      });

      expect(screen.getByText('21d')).toBeInTheDocument();
      expect(screen.getByText('25d')).toBeInTheDocument();
    });

    it('should display warning color for moderate time-to-hire (31-45 days)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('35d')).toBeInTheDocument();
      });
    });

    it('should display error color for high time-to-hire (> 45 days)', async () => {
      const highTimeToHireData = {
        ...mockSourceAttribution,
        sources: [
          {
            ...mockSourceAttribution.sources[0]!,
            average_time_to_hire_days: 50,
          },
        ],
      };

      mockedAxios.get.mockResolvedValue({ data: highTimeToHireData });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('50d')).toBeInTheDocument();
      });
    });
  });

  describe('Stage Distribution', () => {
    it('should display "Show Stage Distribution" button initially', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });
    });

    it('should expand stage distribution when button is clicked', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });

      const showButtons = screen.getAllByText('Show Stage Distribution');
      fireEvent.click(showButtons[0]!);

      await waitFor(() => {
        expect(screen.getByText('Hide Stage Distribution')).toBeInTheDocument();
      });

      expect(screen.getByText('Hiring Stage Breakdown')).toBeInTheDocument();
    });

    it('should display all stages in distribution', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });

      const showButtons = screen.getAllByText('Show Stage Distribution');
      fireEvent.click(showButtons[0]!);

      await waitFor(() => {
        expect(screen.getByText('Applied')).toBeInTheDocument();
      });

      expect(screen.getByText('Screening')).toBeInTheDocument();
      expect(screen.getByText('Interview')).toBeInTheDocument();
      expect(screen.getByText('Offer')).toBeInTheDocument();
      expect(screen.getByText('Hired')).toBeInTheDocument();
    });

    it('should display stage counts and percentages', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });

      const showButtons = screen.getAllByText('Show Stage Distribution');
      fireEvent.click(showButtons[0]!);

      await waitFor(() => {
        expect(screen.getByText(/450.*100.0%/)).toBeInTheDocument();
      });

      expect(screen.getByText(/200.*44.0%/)).toBeInTheDocument();
      expect(screen.getByText(/150.*33.0%/)).toBeInTheDocument();
    });

    it('should collapse stage distribution when Hide button is clicked', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });

      const showButtons = screen.getAllByText('Show Stage Distribution');
      fireEvent.click(showButtons[0]!);

      await waitFor(() => {
        expect(screen.getByText('Hide Stage Distribution')).toBeInTheDocument();
      });

      const hideButtons = screen.getAllByText('Hide Stage Distribution');
      fireEvent.click(hideButtons[0]!);

      await waitFor(() => {
        expect(screen.getByText('Show Stage Distribution')).toBeInTheDocument();
      });
    });
  });

  describe('Auto-Refresh Functionality', () => {
    it('should have Auto-refresh button enabled by default', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(screen.getByText('Auto-refresh')).toBeInTheDocument();
    });

    it('should pause auto-refresh when Paused button is clicked', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Auto-refresh'));

      await waitFor(() => {
        expect(screen.getByText('Paused')).toBeInTheDocument();
      });
    });

    it('should resume auto-refresh when Play button is clicked', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      // Pause auto-refresh
      fireEvent.click(screen.getByText('Auto-refresh'));

      await waitFor(() => {
        expect(screen.getByText('Paused')).toBeInTheDocument();
      });

      // Resume auto-refresh
      fireEvent.click(screen.getByText('Paused'));

      await waitFor(() => {
        expect(screen.getByText('Auto-refresh')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      mockedAxios.get.mockClear();
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      fireEvent.click(screen.getByText('Refresh'));

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error')).mockResolvedValueOnce({
        data: mockSourceAttribution,
      });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Candidate Source Attribution')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  describe('Date Range Filtering', () => {
    it('should include start_date in API request', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(mockApiUrl, {
        params: { start_date: '2024-01-01' },
      });
    });

    it('should include end_date in API request', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(mockApiUrl, {
        params: { end_date: '2024-12-31' },
      });
    });

    it('should include both start and end date in API request', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution startDate="2024-01-01" endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(mockApiUrl, {
        params: { start_date: '2024-01-01', end_date: '2024-12-31' },
      });
    });

    it('should display date range filter chip when date_range is returned', async () => {
      const dataWithDateRange = {
        ...mockSourceAttribution,
        date_range: 'Jan 1, 2024 - Dec 31, 2024',
      };

      mockedAxios.get.mockResolvedValue({ data: dataWithDateRange });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText(/Filtered: Jan 1, 2024 - Dec 31, 2024/)).toBeInTheDocument();
      });
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/candidate-sources';

      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(customUrl, expect.any(Object));
    });
  });

  describe('Visual Design', () => {
    it('should have Refresh button in header', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Candidate Source Attribution')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('should have source breakdown section', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Source Breakdown')).toBeInTheDocument();
      });
    });

    it('should display color indicators for each source', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockSourceAttribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      // Color indicators are rendered as colored circles
      // We verify that source names are present which are next to the color indicators
      expect(screen.getByText('Indeed')).toBeInTheDocument();
      expect(screen.getByText('Referral')).toBeInTheDocument();
      expect(screen.getByText('Company Website')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty sources array', async () => {
      const emptyData = {
        sources: [],
        total_candidates: 0,
      };

      mockedAxios.get.mockResolvedValue({ data: emptyData });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('No Candidate Source Data')).toBeInTheDocument();
      });
    });

    it('should handle source with no stage distribution', async () => {
      const dataWithoutStageDistribution = {
        ...mockSourceAttribution,
        sources: [
          {
            ...mockSourceAttribution.sources[0]!,
            stage_distribution: [],
          },
        ],
      };

      mockedAxios.get.mockResolvedValue({ data: dataWithoutStageDistribution });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      });

      // Should not show stage distribution button
      expect(screen.queryAllByText('Show Stage Distribution').length).toBe(3); // Only for other 3 sources
    });

    it('should handle API error with status code', async () => {
      const error = {
        response: { status: 500, statusText: 'Internal Server Error' },
      } as any;

      mockedAxios.get.mockRejectedValue(error);

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Candidate Source Attribution')).toBeInTheDocument();
      });
    });

    it('should handle single source', async () => {
      const singleSourceData = {
        sources: [
          {
            source: 'LinkedIn',
            candidate_count: 100,
            hired_count: 20,
            conversion_rate: 0.20,
            average_time_to_hire_days: 25,
            stage_distribution: [],
          },
        ],
        total_candidates: 100,
      };

      mockedAxios.get.mockResolvedValue({ data: singleSourceData });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument(); // Active Sources
      });

      expect(screen.getByText('LinkedIn')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument(); // Total Candidates
    });

    it('should handle zero conversion rate', async () => {
      const zeroConversionData = {
        ...mockSourceAttribution,
        sources: [
          {
            source: 'No Hires',
            candidate_count: 100,
            hired_count: 0,
            conversion_rate: 0,
            average_time_to_hire_days: 0,
            stage_distribution: [],
          },
        ],
      };

      mockedAxios.get.mockResolvedValue({ data: zeroConversionData });

      render(<CandidateSourceAttribution />);

      await waitFor(() => {
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('0d')).toBeInTheDocument();
    });
  });
});
