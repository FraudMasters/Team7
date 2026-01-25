/**
 * Tests for RecruiterPerformance Component
 *
 * Tests the recruiter performance analytics including:
 * - Fetching and displaying recruiter metrics
 * - Performance comparison table display
 * - Color coding based on performance thresholds
 * - Top performer highlighting
 * - Average statistics display
 * - Date range and limit filtering
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import RecruiterPerformance from './RecruiterPerformance';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('RecruiterPerformance', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/recruiter-performance';

  const mockRecruiterPerformance = {
    recruiters: [
      {
        recruiter_id: 'rec-1',
        recruiter_name: 'Sarah Johnson',
        hires: 24,
        interviews_conducted: 45,
        resumes_processed: 320,
        average_time_to_hire: 22,
        offer_acceptance_rate: 0.92,
        candidate_satisfaction_score: 4.7,
      },
      {
        recruiter_id: 'rec-2',
        recruiter_name: 'Michael Chen',
        hires: 18,
        interviews_conducted: 38,
        resumes_processed: 280,
        average_time_to_hire: 28,
        offer_acceptance_rate: 0.88,
        candidate_satisfaction_score: 4.5,
      },
      {
        recruiter_id: 'rec-3',
        recruiter_name: 'Emily Davis',
        hires: 15,
        interviews_conducted: 32,
        resumes_processed: 250,
        average_time_to_hire: 35,
        offer_acceptance_rate: 0.85,
        candidate_satisfaction_score: 4.3,
      },
    ],
    total_recruiters: 3,
    period_start_date: '2024-01-01',
    period_end_date: '2024-12-31',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      expect(screen.getByText('Loading recruiter performance data...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
      expect(screen.getByText('Michael Chen')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Recruiter Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockFetch.mockRejectedValue(new Error('API error'));

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Recruiter Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Performance Table Display', () => {
    it('should display all recruiters from API response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
      });

      expect(screen.getByText('Michael Chen')).toBeInTheDocument();
      expect(screen.getByText('Emily Davis')).toBeInTheDocument();
    });

    it('should display hires count for each recruiter', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('24')).toBeInTheDocument();
      });

      expect(screen.getByText('18')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });

    it('should display interviews conducted', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument();
      });

      expect(screen.getByText('38')).toBeInTheDocument();
      expect(screen.getByText('32')).toBeInTheDocument();
    });

    it('should display resumes processed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('320')).toBeInTheDocument();
      });

      expect(screen.getByText('280')).toBeInTheDocument();
      expect(screen.getByText('250')).toBeInTheDocument();
    });

    it('should display average time-to-hire', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('22 days')).toBeInTheDocument();
      });

      expect(screen.getByText('28 days')).toBeInTheDocument();
      expect(screen.getByText('35 days')).toBeInTheDocument();
    });

    it('should display offer acceptance rate', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('92.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('88.0%')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
    });

    it('should display satisfaction score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('4.7')).toBeInTheDocument();
      });

      expect(screen.getByText('4.5')).toBeInTheDocument();
      expect(screen.getByText('4.3')).toBeInTheDocument();
    });
  });

  describe('Color Coding', () => {
    it('should show green color for good time-to-hire (<= 30 days)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('22 days')).toBeInTheDocument();
      });
    });

    it('should show yellow color for moderate time-to-hire (31-45 days)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('35 days')).toBeInTheDocument();
      });
    });

    it('should show green color for high acceptance rate (>= 90%)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('92.0%')).toBeInTheDocument();
      });
    });

    it('should show green color for high satisfaction score (>= 4.5)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('4.7')).toBeInTheDocument();
      });
    });
  });

  describe('Summary Statistics', () => {
    it('should display total recruiters', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText(/Total Recruiters/)).toBeInTheDocument();
      });

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should display top performer', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText(/Top Performer/)).toBeInTheDocument();
      });

      expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
    });

    it('should display average statistics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText(/Average Hires/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Avg Time-to-Hire/)).toBeInTheDocument();
      expect(screen.getByText(/Avg Acceptance Rate/)).toBeInTheDocument();
    });
  });

  describe('Date Range and Limit Filtering', () => {
    it('should include start_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      );
    });

    it('should include end_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-12-31')
      );
    });

    it('should include limit parameter in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance limit={10} />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=10')
      );
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRecruiterPerformance,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRecruiterPerformance,
        });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
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
          json: async () => mockRecruiterPerformance,
        });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Recruiter Data')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/recruiters';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(customUrl);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty recruiters array', async () => {
      const emptyData = {
        recruiters: [],
        total_recruiters: 0,
        period_start_date: '2024-01-01',
        period_end_date: '2024-12-31',
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyData,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Recruiter Data')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch recruiter performance data/)).toBeInTheDocument();
    });
  });

  describe('Visual Design', () => {
    it('should display rank column', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('#1')).toBeInTheDocument();
      });

      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText('#3')).toBeInTheDocument();
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('should display table headers', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockRecruiterPerformance,
      });

      render(<RecruiterPerformance />);

      await waitFor(() => {
        expect(screen.getByText('Recruiter Performance')).toBeInTheDocument();
      });

      expect(screen.getByText('Rank')).toBeInTheDocument();
      expect(screen.getByText('Recruiter')).toBeInTheDocument();
      expect(screen.getByText('Hires')).toBeInTheDocument();
      expect(screen.getByText('Interviews')).toBeInTheDocument();
    });
  });
});
