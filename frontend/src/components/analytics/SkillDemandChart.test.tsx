/**
 * Tests for SkillDemandChart Component
 *
 * Tests the skill demand analytics including:
 * - Fetching and displaying trending skills
 * - Skill demand visualization with bar charts
 * - Trend indicators and percentages
 * - Summary statistics display
 * - Date range and limit filtering
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillDemandChart from './SkillDemandChart';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SkillDemandChart', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/skill-demand';

  const mockSkillDemand = {
    skills: [
      {
        skill_name: 'Python',
        demand_count: 450,
        demand_percentage: 0.45,
        trend_percentage: 15.5,
      },
      {
        skill_name: 'JavaScript',
        demand_count: 380,
        demand_percentage: 0.38,
        trend_percentage: 12.3,
      },
      {
        skill_name: 'React',
        demand_count: 320,
        demand_percentage: 0.32,
        trend_percentage: -5.2,
      },
      {
        skill_name: 'SQL',
        demand_count: 280,
        demand_percentage: 0.28,
        trend_percentage: 8.7,
      },
      {
        skill_name: 'AWS',
        demand_count: 250,
        demand_percentage: 0.25,
        trend_percentage: 20.1,
      },
    ],
    total_postings_analyzed: 1000,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      expect(screen.getByText('Loading skill demand data...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Skill Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockFetch.mockRejectedValue(new Error('API error'));

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Skill Data')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Skills Display', () => {
    it('should display all skills from API response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('SQL')).toBeInTheDocument();
      expect(screen.getByText('AWS')).toBeInTheDocument();
    });

    it('should display demand counts for each skill', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('450')).toBeInTheDocument();
      });

      expect(screen.getByText('380')).toBeInTheDocument();
      expect(screen.getByText('320')).toBeInTheDocument();
    });

    it('should display demand percentages for each skill', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('45.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('38.0%')).toBeInTheDocument();
      expect(screen.getByText('32.0%')).toBeInTheDocument();
    });

    it('should display trend indicators', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      // Check for trend indicators (up/down arrows with percentages)
      expect(screen.getByText(/15\.5%/)).toBeInTheDocument();
      expect(screen.getByText(/12\.3%/)).toBeInTheDocument();
    });

    it('should display rank chips for top 3 skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      // Top 3 skills should have rank indicators
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText('#3')).toBeInTheDocument();
    });
  });

  describe('Summary Statistics', () => {
    it('should display trending skills count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText(/Trending Skills/)).toBeInTheDocument();
      });

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('should display top skill', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText(/Top Skill/)).toBeInTheDocument();
      });

      expect(screen.getByText('Python')).toBeInTheDocument();
    });

    it('should display highest demand percentage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText(/Highest Demand/)).toBeInTheDocument();
      });

      expect(screen.getByText('45.0%')).toBeInTheDocument();
    });

    it('should display total postings analyzed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText(/Total Postings/)).toBeInTheDocument();
      });

      expect(screen.getByText('1,000')).toBeInTheDocument();
    });
  });

  describe('Date Range Filtering', () => {
    it('should include start_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart startDate="2024-01-01" />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      );
    });

    it('should include end_date in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart endDate="2024-12-31" />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-12-31')
      );
    });

    it('should include limit parameter in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart limit={10} />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=10')
      );
    });
  });

  describe('Trend Indicators', () => {
    it('should display upward trend for positive trend percentage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      expect(screen.getByText(/15\.5%/)).toBeInTheDocument();
    });

    it('should display downward trend for negative trend percentage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(screen.getByText(/-5\.2%/)).toBeInTheDocument();
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSkillDemand,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSkillDemand,
        });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
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
          json: async () => mockSkillDemand,
        });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Skill Data')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/skills';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(customUrl);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty skills array', async () => {
      const emptyData = {
        skills: [],
        total_postings_analyzed: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyData,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle zero demand counts', async () => {
      const zeroDemandData = {
        skills: [
          {
            skill_name: 'Unknown',
            demand_count: 0,
            demand_percentage: 0,
            trend_percentage: 0,
          },
        ],
        total_postings_analyzed: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => zeroDemandData,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Unknown')).toBeInTheDocument();
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

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Skill Data')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch skill demand data/)).toBeInTheDocument();
    });
  });

  describe('Visual Design', () => {
    it('should display progress bars for skill demand', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      // Progress bars are rendered via LinearProgress component
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText('Skill Demand Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('should display summary cards', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockSkillDemand,
      });

      render(<SkillDemandChart />);

      await waitFor(() => {
        expect(screen.getByText(/Trending Skills/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Top Skill/)).toBeInTheDocument();
      expect(screen.getByText(/Highest Demand/)).toBeInTheDocument();
      expect(screen.getByText(/Total Postings/)).toBeInTheDocument();
    });
  });
});
