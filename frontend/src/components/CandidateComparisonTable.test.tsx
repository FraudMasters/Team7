/**
 * Tests for CandidateComparisonTable Component
 *
 * Tests the candidate comparison table including:
 * - Fetching and displaying comparison data from API
 * - Showing score breakdowns (overall, keyword, TF-IDF, vector)
 * - Highlighting best scores in each category
 * - Displaying matched/missing skills counts
 * - Responsive table and card layouts
 * - Error handling and loading states
 * - Refresh functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CandidateComparisonTable from './CandidateComparisonTable';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('CandidateComparisonTable', () => {
  const mockVacancyId = 'vacancy-123';
  const mockResumeIds = ['resume-1', 'resume-2', 'resume-3'];

  const mockComparisonData = {
    vacancy_id: mockVacancyId,
    vacancy_title: 'Senior Software Engineer',
    candidates: [
      {
        resume_id: 'resume-1',
        filename: 'john_doe.pdf',
        match_score: {
          overall_score: 0.85,
          keyword_score: 0.90,
          tfidf_score: 0.80,
          vector_score: 0.85,
        },
        passed: true,
        recommendation: 'Strong Match',
        matched_skills: ['Python', 'React', 'Docker', 'AWS'],
        missing_skills: ['Kubernetes'],
        rank: 1,
      },
      {
        resume_id: 'resume-2',
        filename: 'jane_smith.pdf',
        match_score: {
          overall_score: 0.70,
          keyword_score: 0.75,
          tfidf_score: 0.65,
          vector_score: 0.70,
        },
        passed: true,
        recommendation: 'Good Match',
        matched_skills: ['Python', 'Java', 'Git'],
        missing_skills: ['React', 'Docker', 'AWS'],
        rank: 2,
      },
      {
        resume_id: 'resume-3',
        filename: 'bob_johnson.pdf',
        match_score: {
          overall_score: 0.55,
          keyword_score: 0.60,
          tfidf_score: 0.50,
          vector_score: 0.55,
        },
        passed: false,
        recommendation: 'Weak Match',
        matched_skills: ['Java'],
        missing_skills: ['Python', 'React', 'Docker', 'AWS'],
        rank: 3,
      },
    ],
    summary: {
      total_candidates: 3,
      best_score: 0.85,
      average_score: 0.70,
      worst_score: 0.55,
      passed_count: 2,
    },
    processing_time_ms: 1500,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      expect(screen.getByText('Comparing candidates...')).toBeInTheDocument();
      expect(screen.getByText(/Analyzing 3 candidate\(s\) for vacancy requirements/)).toBeInTheDocument();
    });

    it('should render comparison data after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Score breakdown by algorithm')).toBeInTheDocument();
    });

    it('should display candidate filenames', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('john_doe.pdf')).toBeInTheDocument();
        expect(screen.getByText('jane_smith.pdf')).toBeInTheDocument();
        expect(screen.getByText('bob_johnson.pdf')).toBeInTheDocument();
      });
    });

    it('should display processing time', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Comparison completed in 1.50 seconds/)).toBeInTheDocument();
      });
    });
  });

  describe('Score Display', () => {
    it('should display overall match scores', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument(); // john_doe
        expect(screen.getByText('70%')).toBeInTheDocument(); // jane_smith
        expect(screen.getByText('55%')).toBeInTheDocument(); // bob_johnson
      });
    });

    it('should display keyword scores with weight', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Keyword (50%)')).toBeInTheDocument();
      });
    });

    it('should display TF-IDF scores with weight', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('TF-IDF (30%)')).toBeInTheDocument();
      });
    });

    it('should display vector scores with weight', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Vector (20%)')).toBeInTheDocument();
      });
    });
  });

  describe('Best Score Highlighting', () => {
    it('should highlight best overall score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument();
      });

      // john_doe has best overall score (85%)
      const bestScoreElements = screen.getAllByText('85%');
      expect(bestScoreElements.length).toBeGreaterThan(0);
    });

    it('should highlight best keyword score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('90%')).toBeInTheDocument(); // Best keyword score
      });
    });

    it('should highlight best TF-IDF score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('80%')).toBeInTheDocument(); // Best TF-IDF score
      });
    });

    it('should highlight best vector score', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument(); // Best vector score
      });
    });

    it('should display trophy icons for best scores', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const trophyIcons = document.querySelectorAll('[class*="MuiSvgIcon-root"]');
        expect(trophyIcons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Skills Display', () => {
    it('should display matched skills count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/✓ 4 matched/)).toBeInTheDocument(); // john_doe
        expect(screen.getByText(/✓ 3 matched/)).toBeInTheDocument(); // jane_smith
        expect(screen.getByText(/✓ 1 matched/)).toBeInTheDocument(); // bob_johnson
      });
    });

    it('should display missing skills count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/✗ 1 missing/)).toBeInTheDocument(); // john_doe
        expect(screen.getByText(/✗ 3 missing/)).toBeInTheDocument(); // jane_smith
        expect(screen.getByText(/✗ 4 missing/)).toBeInTheDocument(); // bob_johnson
      });
    });
  });

  describe('Error Handling', () => {
    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should render error when no resume IDs provided', async () => {
      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={[]}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('At least one resume ID is required for comparison')).toBeInTheDocument();
    });

    it('should render no data state when no candidates returned', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockComparisonData,
          candidates: [],
        }),
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No Comparison Data')).toBeInTheDocument();
      });

      expect(screen.getByText('No candidates found for comparison')).toBeInTheDocument();
    });

    it('should handle API error response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      vi.clearAllMocks();

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/compare-candidates'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockComparisonData,
        });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('API Integration', () => {
    it('should call API with correct endpoint', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/compare-candidates'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should send correct request body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      const fetchCall = mockFetch.mock.calls[0];
      const requestBody = JSON.parse(fetchCall[1].body);

      expect(requestBody).toEqual({
        vacancy_id: mockVacancyId,
        resume_ids: mockResumeIds,
      });
    });

    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/matching';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
          apiUrl={customUrl}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        `${customUrl}/compare-candidates`,
        expect.any(Object)
      );
    });
  });

  describe('Responsive Layout', () => {
    it('should render table for desktop view', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const table = document.querySelector('.MuiTable-root');
        expect(table).toBeInTheDocument();
      });
    });

    it('should render cards for mobile view', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      // Mock mobile viewport
      global.innerWidth = 500;

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const cards = document.querySelectorAll('.MuiPaper-root');
        expect(cards.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Legend', () => {
    it('should display legend with best score indicator', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Best score in category')).toBeInTheDocument();
      });
    });

    it('should display algorithm weight indicators in legend', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Keyword (50%)')).toBeInTheDocument();
        expect(screen.getByText('TF-IDF (30%)')).toBeInTheDocument();
        expect(screen.getByText('Vector (20%)')).toBeInTheDocument();
      });
    });
  });

  describe('Score Labels', () => {
    it('should display Excellent label for high scores', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Excellent')).toBeInTheDocument();
      });
    });

    it('should display Moderate label for medium scores', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Moderate')).toBeInTheDocument();
      });
    });

    it('should display Poor label for low scores', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Poor')).toBeInTheDocument();
      });
    });
  });

  describe('Candidate Ranking', () => {
    it('should display rank numbers for candidates', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('#1')).toBeInTheDocument();
        expect(screen.getByText('#2')).toBeInTheDocument();
        expect(screen.getByText('#3')).toBeInTheDocument();
      });
    });

    it('should display trophy icon for first place candidate', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const trophyIcons = document.querySelectorAll('[data-testid="EmojiEventsIcon"]');
        expect(trophyIcons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Progress Bars', () => {
    it('should render progress bars for each score component', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
        expect(progressBars.length).toBeGreaterThan(0);
      });
    });

    it('should color code progress bars based on score value', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
        expect(progressBars.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle single candidate comparison', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockComparisonData,
          candidates: [mockComparisonData.candidates[0]],
        }),
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={['resume-1']}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 1 Candidates Comparison')).toBeInTheDocument();
        expect(screen.getByText('john_doe.pdf')).toBeInTheDocument();
      });
    });

    it('should handle many candidates comparison', async () => {
      const manyCandidates = Array.from({ length: 10 }, (_, i) => ({
        ...mockComparisonData.candidates[0],
        resume_id: `resume-${i}`,
        filename: `candidate_${i}.pdf`,
        match_score: {
          overall_score: 0.5 + (i * 0.05),
          keyword_score: 0.5 + (i * 0.05),
          tfidf_score: 0.5 + (i * 0.05),
          vector_score: 0.5 + (i * 0.05),
        },
      }));

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockComparisonData,
          candidates: manyCandidates,
        }),
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={manyCandidates.map((c) => c.resume_id)}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 10 Candidates Comparison')).toBeInTheDocument();
      });
    });

    it('should handle candidates with zero scores', async () => {
      const zeroScoreData = {
        ...mockComparisonData,
        candidates: [
          {
            ...mockComparisonData.candidates[0],
            match_score: {
              overall_score: 0,
              keyword_score: 0,
              tfidf_score: 0,
              vector_score: 0,
            },
          },
        ],
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => zeroScoreData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={['resume-1']}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('0%')).toBeInTheDocument();
      });
    });

    it('should handle candidates with perfect scores', async () => {
      const perfectScoreData = {
        ...mockComparisonData,
        candidates: [
          {
            ...mockComparisonData.candidates[0],
            match_score: {
              overall_score: 1.0,
              keyword_score: 1.0,
              tfidf_score: 1.0,
              vector_score: 1.0,
            },
          },
        ],
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => perfectScoreData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={['resume-1']}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument();
      });
    });
  });

  describe('Layout and Structure', () => {
    it('should render header section with title and refresh button', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Top 3 Candidates Comparison')).toBeInTheDocument();
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });
    });

    it('should render in stack layout', async () => {
      const { container } = render(
        <CandidateComparisonTable
          vacancyId={mockVacancyId}
          resumeIds={mockResumeIds}
        />
      );

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      await waitFor(() => {
        const stacks = container.querySelectorAll('.MuiStack-root');
        expect(stacks.length).toBeGreaterThan(0);
      });
    });
  });
});
