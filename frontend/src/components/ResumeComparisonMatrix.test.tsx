/**
 * Tests for ResumeComparisonMatrix Component
 *
 * Tests the resume comparison matrix interface including:
 * - Fetching and displaying comparison data
 * - Displaying interactive skill matrix
 * - Showing performance summary cards
 * - Ranking display with visual indicators
 * - Experience verification details
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResumeComparisonMatrix from './ResumeComparisonMatrix';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ResumeComparisonMatrix', () => {
  const mockVacancyId = 'vacancy-123';
  const mockApiUrl = 'http://localhost:8000/api/comparisons';

  const mockMatrixData = {
    vacancy_id: mockVacancyId,
    comparisons: [
      {
        resume_id: 'resume-1',
        match_percentage: 85.5,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
          { skill: 'Python', matched: true, highlight: 'green' },
          { skill: 'React', matched: true, highlight: 'green' },
          { skill: 'TypeScript', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Docker', matched: false, highlight: 'red' },
        ],
        experience_verification: [
          {
            skill: 'Java',
            total_months: 48,
            required_months: 36,
            meets_requirement: true,
            projects: [
              {
                company: 'Tech Corp',
                position: 'Senior Developer',
                start_date: '2020-01-01',
                end_date: '2024-01-01',
                months: 48,
              },
            ],
          },
          {
            skill: 'Python',
            total_months: 24,
            required_months: 12,
            meets_requirement: true,
            projects: [],
          },
        ],
        overall_match: true,
      },
      {
        resume_id: 'resume-2',
        match_percentage: 65.0,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
          { skill: 'React', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Python', matched: false, highlight: 'red' },
          { skill: 'Docker', matched: false, highlight: 'red' },
          { skill: 'TypeScript', matched: false, highlight: 'red' },
        ],
        experience_verification: [
          {
            skill: 'Java',
            total_months: 30,
            required_months: 36,
            meets_requirement: false,
            projects: [],
          },
        ],
        overall_match: false,
      },
      {
        resume_id: 'resume-3',
        match_percentage: 45.5,
        matched_skills: [
          { skill: 'React', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Java', matched: false, highlight: 'red' },
          { skill: 'Python', matched: false, highlight: 'red' },
          { skill: 'Docker', matched: false, highlight: 'red' },
          { skill: 'TypeScript', matched: false, highlight: 'red' },
        ],
        overall_match: false,
      },
    ],
    all_unique_skills: ['Java', 'Python', 'React', 'Docker', 'TypeScript'],
    processing_time: 1.85,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      expect(screen.getByText('Building comparison matrix...')).toBeInTheDocument();
      expect(screen.getByText(/Analyzing 2 resumes against vacancy requirements/)).toBeInTheDocument();
    });

    it('should render matrix after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should render no data state when no comparisons exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          vacancy_id: mockVacancyId,
          comparisons: [],
          all_unique_skills: [],
        }),
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No Comparison Data')).toBeInTheDocument();
      });

      expect(
        screen.getByText('No comparison data found for the selected resumes and vacancy.')
      ).toBeInTheDocument();
    });

    it('should display processing time', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Matrix generated in 1.85 seconds/)).toBeInTheDocument();
      });
    });
  });

  describe('Header Section', () => {
    it('should display matrix icon and title', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.getByTestId('Grid4x4Icon')).toBeInTheDocument();
    });

    it('should display vacancy ID and resume/skill counts', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(`Vacancy: ${mockVacancyId}`)).toBeInTheDocument();
        expect(screen.getByText(/Comparing 3 resumes/)).toBeInTheDocument();
        expect(screen.getByText(/5 skills/)).toBeInTheDocument();
      });
    });
  });

  describe('Ranking Display', () => {
    it('should show ranking when showRanking is true', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
          showRanking={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('#1')).toBeInTheDocument();
        expect(screen.getByText('#2')).toBeInTheDocument();
        expect(screen.getByText('#3')).toBeInTheDocument();
      });
    });

    it('should hide ranking when showRanking is false', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
          showRanking={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.queryByText('#1')).not.toBeInTheDocument();
    });

    it('should display skill count in ranking tooltip', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
          showRanking={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('#1')).toBeInTheDocument();
      });

      // resume-1 has 4/5 skills matched
      expect(screen.getByText(/4\/\d+ skills/)).toBeInTheDocument();
    });
  });

  describe('Performance Summary Cards', () => {
    it('should display performance cards for each resume', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      });

      expect(screen.getByText('Rank #1')).toBeInTheDocument();
      expect(screen.getByText('Rank #2')).toBeInTheDocument();
      expect(screen.getByText('Rank #3')).toBeInTheDocument();
    });

    it('should display trophy icon for top performer', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Rank #1')).toBeInTheDocument();
      });

      expect(screen.getByTestId('EmojiEventsIcon')).toBeInTheDocument();
    });

    it('should display skill statistics in cards', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      });

      expect(screen.getByText('Matched Skills:')).toBeInTheDocument();
      expect(screen.getByText('Missing Skills:')).toBeInTheDocument();
      expect(screen.getByText('Total Skills:')).toBeInTheDocument();
    });

    it('should color-code performance cards by match percentage', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('86% Match')).toBeInTheDocument(); // resume-1
        expect(screen.getByText('65% Match')).toBeInTheDocument(); // resume-2
        expect(screen.getByText('46% Match')).toBeInTheDocument(); // resume-3
      });
    });
  });

  describe('Skills Matrix Table', () => {
    it('should display skills matrix with all required skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      expect(screen.getByText('Java')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Docker')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });

    it('should display check icons for matched skills with tooltips', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      const checkIcons = screen.getAllByTestId('CheckCircleIcon');
      expect(checkIcons.length).toBeGreaterThan(0);
    });

    it('should display cross icons for missing skills with tooltips', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      const crossIcons = screen.getAllByTestId('CancelIcon');
      expect(crossIcons.length).toBeGreaterThan(0);
    });

    it('should display legend below matrix', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      expect(screen.getByText('Has Skill')).toBeInTheDocument();
      expect(screen.getByText('Missing Skill')).toBeInTheDocument();
    });

    it('should display resume headers with match percentages', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      expect(screen.getByText('resume-1')).toBeInTheDocument();
      expect(screen.getByText('resume-2')).toBeInTheDocument();
      expect(screen.getByText('resume-3')).toBeInTheDocument();
    });
  });

  describe('Experience Verification', () => {
    it('should display experience verification when showDetails is true', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          showDetails={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Verification Summary')).toBeInTheDocument();
      });

      expect(screen.getByText(/Verified work experience/)).toBeInTheDocument();
    });

    it('should hide experience verification when showDetails is false', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          showDetails={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.queryByText('Experience Verification Summary')).not.toBeInTheDocument();
    });

    it('should display experience chips with skill and months', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          showDetails={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Verification Summary')).toBeInTheDocument();
      });

      // resume-1 has Java: 48mo, Python: 24mo
      expect(screen.getByText(/Java: \d+mo/)).toBeInTheDocument();
      expect(screen.getByText(/Python: \d+mo/)).toBeInTheDocument();
    });

    it('should color-code experience chips by requirement status', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          showDetails={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Verification Summary')).toBeInTheDocument();
      });

      // Should have chips for meets and doesn't meet requirements
      const chips = screen.getAllByRole('button');
      expect(chips.length).toBeGreaterThan(0);
    });

    it('should not display experience section when no experience data', async () => {
      const noExpData = {
        ...mockMatrixData,
        comparisons: mockMatrixData.comparisons.map((c) => ({
          ...c,
          experience_verification: undefined,
        })),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => noExpData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          showDetails={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.queryByText('Experience Verification Summary')).not.toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should show error when less than 2 resumes provided', async () => {
      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('At least 2 resumes are required for comparison')).toBeInTheDocument();
    });

    it('should show error when more than 5 resumes provided', async () => {
      render(
        <ResumeComparisonMatrix
          resumeIds={['r1', 'r2', 'r3', 'r4', 'r5', 'r6']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('Maximum 5 resumes can be compared at once')).toBeInTheDocument();
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh matrix when Refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      // Clear mock calls
      vi.clearAllMocks();

      // Click refresh
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      expect(mockFetch.mock.calls[0][0]).toContain('/compare-multiple');
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMatrixData,
        });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Comparison Failed')).toBeInTheDocument();
      });

      // Click retry
      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/comparisons';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
          apiUrl={customUrl}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        `${customUrl}/compare-multiple`,
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('Sorting', () => {
    it('should sort comparisons by match percentage descending', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockMatrixData,
      });

      render(
        <ResumeComparisonMatrix
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      });

      // Get all rank badges
      const rank1 = screen.getByText('Rank #1').closest('.MuiCard-root');
      const rank2 = screen.getByText('Rank #2').closest('.MuiCard-root');
      const rank3 = screen.getByText('Rank #3').closest('.MuiCard-root');

      // Verify order by checking which resume ID appears in which rank
      expect(rank1?.textContent).toContain('resume-1'); // 85.5%
      expect(rank2?.textContent).toContain('resume-2'); // 65.0%
      expect(rank3?.textContent).toContain('resume-3'); // 45.5%
    });
  });
});
