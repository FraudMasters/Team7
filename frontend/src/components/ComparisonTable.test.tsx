/**
 * Tests for ComparisonTable Component
 *
 * Tests the comparison table interface including:
 * - Fetching and displaying comparison data
 * - Displaying skill matrix with match indicators
 * - Showing rankings by match percentage
 * - Experience verification summaries
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ComparisonTable from './ComparisonTable';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ComparisonTable', () => {
  const mockVacancyId = 'vacancy-123';
  const mockApiUrl = 'http://localhost:8000/api/comparisons';

  const mockComparisonData = {
    vacancy_id: mockVacancyId,
    comparisons: [
      {
        resume_id: 'resume-1',
        match_percentage: 85.5,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
          { skill: 'Python', matched: true, highlight: 'green' },
          { skill: 'React', matched: true, highlight: 'green' },
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
        ],
        overall_match: true,
      },
      {
        resume_id: 'resume-2',
        match_percentage: 65.0,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
          { skill: 'Python', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'React', matched: false, highlight: 'red' },
          { skill: 'Docker', matched: false, highlight: 'red' },
        ],
        experience_verification: [
          {
            skill: 'Java',
            total_months: 24,
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
        ],
        overall_match: false,
      },
    ],
    all_unique_skills: ['Java', 'Python', 'React', 'Docker'],
    processing_time: 1.45,
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
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      expect(screen.getByText('Comparing resumes...')).toBeInTheDocument();
      expect(screen.getByText(/Analyzing 2 resumes against vacancy requirements/)).toBeInTheDocument();
    });

    it('should render comparison matrix after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      expect(screen.getByText('Experience Summary')).toBeInTheDocument();
    });

    it('should render ranking overview with correct order', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('#1')).toBeInTheDocument();
        expect(screen.getByText('#2')).toBeInTheDocument();
        expect(screen.getByText('#3')).toBeInTheDocument();
      });

      // resume-1 should be first with 85.5%
      expect(screen.getByText('resume-1')).toBeInTheDocument();
      expect(screen.getByText('86%')).toBeInTheDocument();
    });

    it('should display match percentage color coding', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('86%')).toBeInTheDocument(); // resume-1: Excellent
        expect(screen.getByText('65%')).toBeInTheDocument(); // resume-2: Moderate
        expect(screen.getByText('46%')).toBeInTheDocument(); // resume-3: Poor
      });

      expect(screen.getByText('Excellent')).toBeInTheDocument();
      expect(screen.getByText('Moderate')).toBeInTheDocument();
      expect(screen.getByText('Poor')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(
        <ComparisonTable
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
        <ComparisonTable
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
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Comparison completed in 1.45 seconds/)).toBeInTheDocument();
      });
    });
  });

  describe('Skills Matrix', () => {
    it('should display skill matrix table with all skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      // Check skills are displayed
      expect(screen.getByText('Java')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Docker')).toBeInTheDocument();
    });

    it('should display check icons for matched skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      // resume-1 has Java, Python, React
      const checkIcons = screen.getAllByTestId('CheckCircleIcon');
      expect(checkIcons.length).toBeGreaterThan(0);
    });

    it('should display cross icons for missing skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Skills Matrix')).toBeInTheDocument();
      });

      // resume-1 missing Docker
      const crossIcons = screen.getAllByTestId('CancelIcon');
      expect(crossIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Experience Summary', () => {
    it('should display experience verification data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Summary')).toBeInTheDocument();
      });

      expect(screen.getByText(/Matched Skills:/)).toBeInTheDocument();
      expect(screen.getByText(/Missing Skills:/)).toBeInTheDocument();
    });

    it('should display experience verification count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Summary')).toBeInTheDocument();
      });

      expect(screen.getByText(/Experience verified for 1 skill/)).toBeInTheDocument();
    });

    it('should not display experience section when no data', async () => {
      const noExperienceData = {
        ...mockComparisonData,
        comparisons: mockComparisonData.comparisons.map((c) => ({
          ...c,
          experience_verification: undefined,
        })),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => noExperienceData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Experience Summary')).toBeInTheDocument();
      });

      // Should not show experience verification text
      expect(screen.queryByText(/Experience verified for/)).not.toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should show error when less than 2 resumes provided', async () => {
      render(
        <ComparisonTable
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
        <ComparisonTable
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
    it('should refresh comparison when Refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
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
          json: async () => mockComparisonData,
        });

      render(
        <ComparisonTable
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
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
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
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume Comparison Matrix')).toBeInTheDocument();
      });

      // Get all ranking badges
      const rank1 = screen.getByText('#1').parentElement;
      const rank2 = screen.getByText('#2').parentElement;
      const rank3 = screen.getByText('#3').parentElement;

      // Verify order by checking which resume ID appears in which rank
      expect(rank1?.textContent).toContain('resume-1'); // 85.5%
      expect(rank2?.textContent).toContain('resume-2'); // 65.0%
      expect(rank3?.textContent).toContain('resume-3'); // 45.5%
    });
  });

  describe('Header Information', () => {
    it('should display vacancy ID and resume count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockComparisonData,
      });

      render(
        <ComparisonTable
          resumeIds={['resume-1', 'resume-2', 'resume-3']}
          vacancyId={mockVacancyId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(`Vacancy: ${mockVacancyId}`)).toBeInTheDocument();
        expect(screen.getByText(/Comparing 3 resumes/)).toBeInTheDocument();
      });
    });
  });
});
