/**
 * Tests for TaxonomyAnalytics Component
 *
 * Tests the taxonomy analytics dashboard including:
 * - Fetching and displaying most used taxonomies
 * - Fetching and displaying most effective taxonomies
 * - Industry breakdown and filtering
 * - Success rate and match score metrics
 * - Summary statistics display
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TaxonomyAnalytics from './TaxonomyAnalytics';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('TaxonomyAnalytics', () => {
  const mockApiUrl = 'http://localhost:8000/api/analytics/taxonomy-usage';

  const mockTaxonomyData = {
    most_used_taxonomies: [
      {
        taxonomy_id: 'healthcare',
        taxonomy_name: 'Healthcare',
        usage_count: 245,
        avg_match_score: 78.5,
        success_rate: 0.82,
        total_candidates_matched: 1850,
        industry: 'healthcare',
      },
      {
        taxonomy_id: 'technology',
        taxonomy_name: 'Technology',
        usage_count: 198,
        avg_match_score: 75.2,
        success_rate: 0.79,
        total_candidates_matched: 1420,
        industry: 'technology',
      },
      {
        taxonomy_id: 'finance',
        taxonomy_name: 'Finance',
        usage_count: 156,
        avg_match_score: 82.1,
        success_rate: 0.87,
        total_candidates_matched: 980,
        industry: 'finance',
      },
      {
        taxonomy_id: 'manufacturing',
        taxonomy_name: 'Manufacturing',
        usage_count: 134,
        avg_match_score: 73.8,
        success_rate: 0.76,
        total_candidates_matched: 850,
        industry: 'manufacturing',
      },
      {
        taxonomy_id: 'retail',
        taxonomy_name: 'Retail',
        usage_count: 98,
        avg_match_score: 71.2,
        success_rate: 0.74,
        total_candidates_matched: 620,
        industry: 'retail',
      },
    ],
    most_effective_taxonomies: [
      {
        taxonomy_id: 'finance',
        taxonomy_name: 'Finance',
        usage_count: 156,
        avg_match_score: 82.1,
        success_rate: 0.87,
        total_candidates_matched: 980,
        industry: 'finance',
      },
      {
        taxonomy_id: 'healthcare',
        taxonomy_name: 'Healthcare',
        usage_count: 245,
        avg_match_score: 78.5,
        success_rate: 0.82,
        total_candidates_matched: 1850,
        industry: 'healthcare',
      },
      {
        taxonomy_id: 'technology',
        taxonomy_name: 'Technology',
        usage_count: 198,
        avg_match_score: 75.2,
        success_rate: 0.79,
        total_candidates_matched: 1420,
        industry: 'technology',
      },
      {
        taxonomy_id: 'manufacturing',
        taxonomy_name: 'Manufacturing',
        usage_count: 134,
        avg_match_score: 73.8,
        success_rate: 0.76,
        total_candidates_matched: 850,
        industry: 'manufacturing',
      },
      {
        taxonomy_id: 'retail',
        taxonomy_name: 'Retail',
        usage_count: 98,
        avg_match_score: 71.2,
        success_rate: 0.74,
        total_candidates_matched: 620,
        industry: 'retail',
      },
    ],
    industry_filter: null,
    total_taxonomies_analyzed: 5,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      expect(screen.getByText('Loading taxonomy analytics...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Healthcare')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Taxonomy Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show Retry button in error state', async () => {
      mockFetch.mockRejectedValue(new Error('API error'));

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Taxonomy Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should render info alert when no taxonomy data is available', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          most_used_taxonomies: [],
          most_effective_taxonomies: [],
          industry_filter: null,
          total_taxonomies_analyzed: 0,
        }),
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('No Taxonomy Analytics Data')).toBeInTheDocument();
      });
    });
  });

  describe('Most Used Taxonomies Display', () => {
    it('should display most used taxonomies section', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Most Used Taxonomies')).toBeInTheDocument();
      });
    });

    it('should display all taxonomy names from most used list', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
      });

      expect(screen.getByText('Technology')).toBeInTheDocument();
      expect(screen.getByText('Finance')).toBeInTheDocument();
      expect(screen.getByText('Manufacturing')).toBeInTheDocument();
      expect(screen.getByText('Retail')).toBeInTheDocument();
    });

    it('should display usage counts for each taxonomy', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('245')).toBeInTheDocument();
      });

      expect(screen.getByText('198')).toBeInTheDocument();
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    it('should display industry labels for taxonomies', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('healthcare')).toBeInTheDocument();
      });

      expect(screen.getByText('technology')).toBeInTheDocument();
      expect(screen.getByText('finance')).toBeInTheDocument();
    });

    it('should display success rate indicators', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
      });

      expect(screen.getByText('82.0%')).toBeInTheDocument();
      expect(screen.getByText('79.0%')).toBeInTheDocument();
    });
  });

  describe('Most Effective Taxonomies Display', () => {
    it('should display most effective taxonomies section', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Most Effective Taxonomies')).toBeInTheDocument();
      });
    });

    it('should display all taxonomy names from most effective list', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Most Effective Taxonomies')).toBeInTheDocument();
      });

      expect(screen.getByText('Finance')).toBeInTheDocument();
      expect(screen.getByText('Healthcare')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('should display match scores for each taxonomy', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Most Effective Taxonomies')).toBeInTheDocument();
      });

      expect(screen.getByText('82.1%')).toBeInTheDocument();
      expect(screen.getByText('78.5%')).toBeInTheDocument();
    });

    it('should display candidate matched counts', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Most Effective Taxonomies')).toBeInTheDocument();
      });

      expect(screen.getByText('980')).toBeInTheDocument();
      expect(screen.getByText('1,850')).toBeInTheDocument();
    });
  });

  describe('Summary Statistics', () => {
    it('should display total taxonomies count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Total Taxonomies/)).toBeInTheDocument();
      });

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('should display total usage count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Total Usage/)).toBeInTheDocument();
      });

      // Sum of all usage counts: 245 + 198 + 156 + 134 + 98 = 831
      expect(screen.getByText('831')).toBeInTheDocument();
    });

    it('should display average match score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Avg Match Score/)).toBeInTheDocument();
      });

      // Average of: 78.5 + 75.2 + 82.1 + 73.8 + 71.2 = 381.8 / 5 = 76.36
      expect(screen.getByText('76.4%')).toBeInTheDocument();
    });

    it('should display average success rate', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Avg Success Rate/)).toBeInTheDocument();
      });

      // Average of: 0.82 + 0.79 + 0.87 + 0.76 + 0.74 = 3.98 / 5 = 0.796 = 79.6%
      expect(screen.getByText('79.6%')).toBeInTheDocument();
    });
  });

  describe('Industry Filtering', () => {
    it('should include industry parameter in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics industry="healthcare" />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('industry=healthcare')
      );
    });

    it('should display industry filter in header when applied', async () => {
      const filteredData = {
        ...mockTaxonomyData,
        industry_filter: 'healthcare',
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => filteredData,
      });

      render(<TaxonomyAnalytics industry="healthcare" />);

      await waitFor(() => {
        expect(screen.getByText(/Filtered by: healthcare/)).toBeInTheDocument();
      });
    });
  });

  describe('Limit Parameter', () => {
    it('should include limit parameter in API request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics limit={5} />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=5')
      );
    });

    it('should display limited number of taxonomies', async () => {
      const limitedData = {
        ...mockTaxonomyData,
        most_used_taxonomies: mockTaxonomyData.most_used_taxonomies.slice(0, 3),
        most_effective_taxonomies: mockTaxonomyData.most_effective_taxonomies.slice(0, 3),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => limitedData,
      });

      render(<TaxonomyAnalytics limit={3} />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
      });

      // Should show 3 taxonomies
      expect(screen.getAllByText('#1')).toHaveLength(2); // 2 sections, each with #1
      expect(screen.getAllByText('#2')).toHaveLength(2);
      expect(screen.getAllByText('#3')).toHaveLength(2);
      expect(screen.queryByText('#4')).not.toBeInTheDocument();
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTaxonomyData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTaxonomyData,
        });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      mockFetch.mockClear();

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
          json: async () => mockTaxonomyData,
        });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Taxonomy Analytics')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/analytics/taxonomy';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics apiUrl={customUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining(customUrl));
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty taxonomies array', async () => {
      const emptyData = {
        most_used_taxonomies: [],
        most_effective_taxonomies: [],
        industry_filter: null,
        total_taxonomies_analyzed: 0,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('No Taxonomy Analytics Data')).toBeInTheDocument();
      });
    });

    it('should handle taxonomies with zero usage', async () => {
      const zeroUsageData = {
        most_used_taxonomies: [
          {
            taxonomy_id: 'unknown',
            taxonomy_name: 'Unknown',
            usage_count: 0,
            avg_match_score: 0,
            success_rate: 0,
            total_candidates_matched: 0,
            industry: 'unknown',
          },
        ],
        most_effective_taxonomies: [
          {
            taxonomy_id: 'unknown',
            taxonomy_name: 'Unknown',
            usage_count: 0,
            avg_match_score: 0,
            success_rate: 0,
            total_candidates_matched: 0,
            industry: 'unknown',
          },
        ],
        industry_filter: null,
        total_taxonomies_analyzed: 1,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => zeroUsageData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Unknown')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Taxonomy Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch taxonomy analytics/)).toBeInTheDocument();
    });

    it('should handle taxonomies without industry field', async () => {
      const noIndustryData = {
        most_used_taxonomies: [
          {
            taxonomy_id: 'general',
            taxonomy_name: 'General Skills',
            usage_count: 100,
            avg_match_score: 75.0,
            success_rate: 0.8,
            total_candidates_matched: 500,
          },
        ],
        most_effective_taxonomies: [
          {
            taxonomy_id: 'general',
            taxonomy_name: 'General Skills',
            usage_count: 100,
            avg_match_score: 75.0,
            success_rate: 0.8,
            total_candidates_matched: 500,
          },
        ],
        industry_filter: null,
        total_taxonomies_analyzed: 1,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => noIndustryData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('General Skills')).toBeInTheDocument();
      });

      expect(screen.getByText('General Skills')).toBeInTheDocument();
    });
  });

  describe('Visual Design', () => {
    it('should display rank chips for top 3 taxonomies', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
      });

      // Top 3 should have rank indicators in most used section
      expect(screen.getAllByText('#1')).toHaveLength(2); // Both sections
      expect(screen.getAllByText('#2')).toHaveLength(2);
      expect(screen.getAllByText('#3')).toHaveLength(2);
    });

    it('should have Refresh button in header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Taxonomy Usage Analytics')).toBeInTheDocument();
      });

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('should display summary cards', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Total Taxonomies/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Total Usage/)).toBeInTheDocument();
      expect(screen.getByText(/Avg Match Score/)).toBeInTheDocument();
      expect(screen.getByText(/Avg Success Rate/)).toBeInTheDocument();
    });

    it('should display section descriptions', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTaxonomyData,
      });

      render(<TaxonomyAnalytics />);

      await waitFor(() => {
        expect(screen.getByText(/Taxonomies ranked by frequency of usage/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Taxonomies ranked by average match score/)).toBeInTheDocument();
    });
  });
});
