/**
 * Tests for DiversityMetricsPanel Component
 *
 * Tests the diversity metrics panel including:
 * - Data fetching and rendering
 * - Loading and error states
 * - Gender distribution display
 * - Geographic distribution
 * - Education level breakdown
 * - Age group distribution
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import DiversityMetricsPanel from './DiversityMetricsPanel';

// Mock fetch globally
global.fetch = vi.fn();

describe('DiversityMetricsPanel', () => {
  const mockDiversityData = {
    gender: {
      male_count: 450,
      male_percentage: 45.0,
      female_count: 420,
      female_percentage: 42.0,
      non_binary_count: 80,
      non_binary_percentage: 8.0,
      other_count: 50,
      other_percentage: 5.0,
      total_candidates: 1000,
    },
    age_groups: [
      { age_group: '18-25', count: 200, percentage: 20.0 },
      { age_group: '26-35', count: 400, percentage: 40.0 },
      { age_group: '36-45', count: 250, percentage: 25.0 },
      { age_group: '46+', count: 150, percentage: 15.0 },
    ],
    education_levels: [
      { education_level: "Bachelor's Degree", count: 500, percentage: 50.0 },
      { education_level: "Master's Degree", count: 300, percentage: 30.0 },
      { education_level: 'PhD/Doctorate', count: 100, percentage: 10.0 },
      { education_level: 'High School', count: 100, percentage: 10.0 },
    ],
    geographic_distribution: [
      { location: 'New York, NY', count: 300, percentage: 30.0 },
      { location: 'San Francisco, CA', count: 250, percentage: 25.0 },
      { location: 'Austin, TX', count: 200, percentage: 20.0 },
      { location: 'Boston, MA', count: 150, percentage: 15.0 },
      { location: 'Seattle, WA', count: 100, percentage: 10.0 },
    ],
    total_analyzed: 1000,
    diversity_score: 0.75,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading spinner while fetching data', () => {
      (global.fetch as any).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<DiversityMetricsPanel />);

      expect(screen.getByText('Loading diversity metrics...')).toBeInTheDocument();
      expect(screen.getByText('This may take a few moments')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when fetch fails', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Diversity Metrics')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should display error message when response is not ok', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Diversity Metrics')).toBeInTheDocument();
        expect(
          screen.getByText('Failed to fetch diversity metrics: Internal Server Error')
        ).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /retry/i });
        expect(retryButton).toBeInTheDocument();
      });
    });

    it('should retry fetching data when retry button is clicked', async () => {
      const user = userEvent.setup();

      // First call fails
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Second call succeeds
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDiversityData,
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
      });
    });
  });

  describe('No Data State', () => {
    it('should display info message when no data is available', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ ...mockDiversityData, total_analyzed: 0 }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('No Diversity Data Available')).toBeInTheDocument();
        expect(
          screen.getByText('No diversity metrics data found. Start processing candidates to populate this dashboard.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Successful Data Rendering', () => {
    beforeEach(() => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });
    });

    it('should render header with title and refresh button', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
        expect(
          screen.getByText('Workforce diversity analytics and demographic insights')
        ).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it('should display summary statistics cards', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('1000')).toBeInTheDocument();
        expect(screen.getByText('Total Analyzed')).toBeInTheDocument();
        expect(screen.getByText('Gender Diversity')).toBeInTheDocument();
        expect(screen.getByText('Locations')).toBeInTheDocument();
        expect(screen.getByText('Education Levels')).toBeInTheDocument();
      });
    });

    it('should calculate gender diversity index correctly', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        // Gender diversity = (female_percentage + non_binary_percentage) / 100
        // (42 + 8) / 100 = 0.50 = 50%
        expect(screen.getByText('50%')).toBeInTheDocument();
      });
    });

    it('should display all gender distribution items', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Male')).toBeInTheDocument();
        expect(screen.getByText('Female')).toBeInTheDocument();
        expect(screen.getByText('Non-Binary')).toBeInTheDocument();
        expect(screen.getByText('Other')).toBeInTheDocument();

        expect(screen.getByText('45.0%')).toBeInTheDocument();
        expect(screen.getByText('42.0%')).toBeInTheDocument();
        expect(screen.getByText('8.0%')).toBeInTheDocument();
        expect(screen.getByText('5.0%')).toBeInTheDocument();
      });
    });

    it('should display top 5 geographic locations', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Top Geographic Locations')).toBeInTheDocument();
        expect(screen.getByText('New York, NY')).toBeInTheDocument();
        expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
        expect(screen.getByText('Austin, TX')).toBeInTheDocument();
        expect(screen.getByText('Boston, MA')).toBeInTheDocument();
        expect(screen.getByText('Seattle, WA')).toBeInTheDocument();
      });
    });

    it('should display education levels', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Education Level Distribution')).toBeInTheDocument();
        expect(screen.getByText("Bachelor's Degree")).toBeInTheDocument();
        expect(screen.getByText("Master's Degree")).toBeInTheDocument();
        expect(screen.getByText('PhD/Doctorate')).toBeInTheDocument();
        expect(screen.getByText('High School')).toBeInTheDocument();
      });
    });

    it('should display age groups', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Age Group Distribution')).toBeInTheDocument();
        expect(screen.getByText('18-25')).toBeInTheDocument();
        expect(screen.getByText('26-35')).toBeInTheDocument();
        expect(screen.getByText('36-45')).toBeInTheDocument();
        expect(screen.getByText('46+')).toBeInTheDocument();
      });
    });

    it('should show candidate counts for each metric', async () => {
      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        const candidatesText = screen.getAllByText(/candidates/i);
        expect(candidatesText.length).toBeGreaterThan(0);
      });
    });
  });

  describe('API Integration', () => {
    it('should call API with correct default URL', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/analytics/diversity-metrics')
        );
      });
    });

    it('should call API with custom URL', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel apiUrl="https://custom-api.com/metrics" />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('https://custom-api.com/metrics')
        );
      });
    });

    it('should include date range parameters in API call', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel startDate="2024-01-01" endDate="2024-12-31" />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('start_date=2024-01-01')
        );
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('end_date=2024-12-31')
        );
      });
    });

    it('should include department parameter in API call', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel department="Engineering" />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('department=Engineering')
        );
      });
    });

    it('should display department in header when provided', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel department="Engineering" />);

      await waitFor(() => {
        expect(
          screen.getByText('Workforce diversity analytics and demographic insights - Engineering')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refetch data when refresh button is clicked', async () => {
      const user = userEvent.setup();

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
      });

      expect(global.fetch).toHaveBeenCalledTimes(1);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty geographic distribution', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          geographic_distribution: [],
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
      });

      expect(screen.queryByText('Top Geographic Locations')).not.toBeInTheDocument();
    });

    it('should handle empty education levels', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          education_levels: [],
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
      });

      expect(screen.queryByText('Education Level Distribution')).not.toBeInTheDocument();
    });

    it('should handle empty age groups', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          age_groups: [],
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Diversity & Inclusion Metrics')).toBeInTheDocument();
      });

      expect(screen.queryByText('Age Group Distribution')).not.toBeInTheDocument();
    });

    it('should filter out gender categories with zero count', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          gender: {
            ...mockDiversityData.gender,
            non_binary_count: 0,
            non_binary_percentage: 0,
            other_count: 0,
            other_percentage: 0,
          },
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Male')).toBeInTheDocument();
        expect(screen.getByText('Female')).toBeInTheDocument();
        expect(screen.queryByText('Non-Binary')).not.toBeInTheDocument();
        expect(screen.queryByText('Other')).not.toBeInTheDocument();
      });
    });

    it('should limit geographic locations to top 5', async () => {
      const manyLocations = Array.from({ length: 10 }, (_, i) => ({
        location: `Location ${i + 1}`,
        count: 100 - i * 10,
        percentage: 10 - i,
      }));

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          geographic_distribution: manyLocations,
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Location 1')).toBeInTheDocument();
        expect(screen.getByText('Location 5')).toBeInTheDocument();
        expect(screen.queryByText('Location 6')).not.toBeInTheDocument();
      });
    });

    it('should limit education levels to 6', async () => {
      const manyEducationLevels = Array.from({ length: 10 }, (_, i) => ({
        education_level: `Education ${i + 1}`,
        count: 100 - i * 10,
        percentage: 10 - i,
      }));

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockDiversityData,
          education_levels: manyEducationLevels,
        }),
      });

      render(<DiversityMetricsPanel />);

      await waitFor(() => {
        expect(screen.getByText('Education 1')).toBeInTheDocument();
        expect(screen.getByText('Education 6')).toBeInTheDocument();
        expect(screen.queryByText('Education 7')).not.toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('should render summary cards in grid layout', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      const { container } = render(<DiversityMetricsPanel />);

      await waitFor(() => {
        const grids = container.querySelectorAll('.MuiGrid-container');
        expect(grids.length).toBeGreaterThan(0);
      });
    });

    it('should render cards with proper Material-UI structure', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockDiversityData,
      });

      const { container } = render(<DiversityMetricsPanel />);

      await waitFor(() => {
        const cards = container.querySelectorAll('.MuiCard-root');
        expect(cards.length).toBeGreaterThan(0);
      });
    });
  });
});
