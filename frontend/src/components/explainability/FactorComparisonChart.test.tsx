/**
 * Tests for FactorComparisonChart Component
 *
 * Tests the factor comparison chart visualization including:
 * - Displaying side-by-side factor comparisons
 * - View mode toggles (side-by-side, difference, normalized)
 * - LLM narrative display
 * - Key differences and winning/losing factors
 * - Loading, error, and empty states
 * - Refresh functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FactorComparisonChart from './FactorComparisonChart';
import { explainability, CompareCandidatesResponse } from '@/api/explainability';

// Mock the explainability API
vi.mock('@/api/explainability', () => ({
  explainability: {
    compareCandidates: vi.fn(),
  },
}));

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  Cell: () => <div data-testid="cell" />,
}));

describe('FactorComparisonChart', () => {
  const mockComparisonData: CompareCandidatesResponse = {
    vacancy_id: 'vacancy-123',
    candidate_a_name: 'John Doe',
    candidate_b_name: 'Jane Smith',
    candidate_a_score: 0.85,
    candidate_b_score: 0.72,
    score_difference: 0.13,
    narrative: 'John Doe has a stronger technical background with more years of experience in React and TypeScript.',
    key_differences: [
      'Years of Experience',
      'Technical Skills',
      'Education Level',
    ],
    winning_factors: [
      'Advanced React proficiency',
      '5 years of TypeScript experience',
    ],
    losing_factors: [
      'Less domain knowledge',
    ],
    recommendation: 'John Doe is recommended for this position based on technical qualifications.',
    provider: 'openai',
    model: 'gpt-4',
    generated_at: '2024-03-20T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      (explainability.compareCandidates as any).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      expect(screen.getByText('Comparing candidates...')).toBeInTheDocument();
      expect(screen.getByText('Analyzing factor-by-factor differences')).toBeInTheDocument();
    });

    it('should render with default title and description', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Factor-by-Factor Comparison')).toBeInTheDocument();
      });

      expect(screen.getByText('Visual comparison of key factors influencing candidate rankings')).toBeInTheDocument();
    });

    it('should render with custom title and description', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
          title="Custom Comparison"
          description="Custom description text"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Comparison')).toBeInTheDocument();
      });

      expect(screen.getByText('Custom description text')).toBeInTheDocument();
    });

    it('should display candidate names and scores', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('John Doe: 85.0%')).toBeInTheDocument();
      });

      expect(screen.getByText('Jane Smith: 72.0%')).toBeInTheDocument();
      expect(screen.getByText('Δ 13.0%')).toBeInTheDocument();
    });

    it('should render chart components', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
      });

      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  describe('View Mode Toggles', () => {
    it('should render view mode toggle buttons', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /side-by-side/i })).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /difference/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /normalized/i })).toBeInTheDocument();
    });

    it('should change view mode when toggle is clicked', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /difference/i })).toBeInTheDocument();
      });

      const differenceButton = screen.getByRole('button', { name: /difference/i });
      fireEvent.click(differenceButton);

      // Chart should re-render with difference view
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });

    it('should change to normalized view', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /normalized/i })).toBeInTheDocument();
      });

      const normalizedButton = screen.getByRole('button', { name: /normalized/i });
      fireEvent.click(normalizedButton);

      // Chart should re-render with normalized view
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  describe('LLM Narrative', () => {
    it('should display LLM narrative when showNarrative is true', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
          showNarrative={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis Summary')).toBeInTheDocument();
      });

      expect(screen.getByText(mockComparisonData.narrative)).toBeInTheDocument();
    });

    it('should not display LLM narrative when showNarrative is false', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
          showNarrative={false}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText('Analysis Summary')).not.toBeInTheDocument();
      });
    });
  });

  describe('Key Differences and Factors', () => {
    it('should display key differences', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Key Differences')).toBeInTheDocument();
      });

      expect(screen.getByText('Years of Experience')).toBeInTheDocument();
      expect(screen.getByText('Technical Skills')).toBeInTheDocument();
      expect(screen.getByText('Education Level')).toBeInTheDocument();
    });

    it('should display winning factors', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('John Doe Advantages')).toBeInTheDocument();
      });

      expect(screen.getByText('Advanced React proficiency')).toBeInTheDocument();
      expect(screen.getByText('5 years of TypeScript experience')).toBeInTheDocument();
    });

    it('should display losing factors', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Jane Smith Advantages')).toBeInTheDocument();
      });

      expect(screen.getByText('Less domain knowledge')).toBeInTheDocument();
    });
  });

  describe('Recommendation', () => {
    it('should display recommendation', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Recommendation')).toBeInTheDocument();
      });

      expect(screen.getByText(mockComparisonData.recommendation)).toBeInTheDocument();
    });
  });

  describe('Metadata', () => {
    it('should display provider, model, and timestamp', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Provider:/)).toBeInTheDocument();
      });

      expect(screen.getByText(/openai/)).toBeInTheDocument();
      expect(screen.getByText(/Model:/)).toBeInTheDocument();
      expect(screen.getByText(/gpt-4/)).toBeInTheDocument();
      expect(screen.getByText(/Generated:/)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error state when API fails', async () => {
      const errorMessage = 'Failed to fetch comparison';
      (explainability.compareCandidates as any).mockRejectedValue(
        new Error(errorMessage)
      );

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Comparison')).toBeInTheDocument();
      });

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should display retry button on error', async () => {
      (explainability.compareCandidates as any).mockRejectedValue(
        new Error('API Error')
      );

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should retry API call when retry button is clicked', async () => {
      (explainability.compareCandidates as any)
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Factor-by-Factor Comparison')).toBeInTheDocument();
      });
    });

    it('should display error when required props are missing', async () => {
      render(
        <FactorComparisonChart
          resumeAId=""
          resumeBId=""
          vacancyId=""
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resume IDs and Vacancy ID are required')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should have a refresh button', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it('should call API when refresh button is clicked', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(explainability.compareCandidates).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(explainability.compareCandidates).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('API Integration', () => {
    it('should call API with correct parameters', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
          useLLM={true}
        />
      );

      await waitFor(() => {
        expect(explainability.compareCandidates).toHaveBeenCalledWith({
          resume_a_id: 'resume-1',
          resume_b_id: 'resume-2',
          vacancy_id: 'vacancy-123',
          use_llm: true,
        });
      });
    });

    it('should use default useLLM value when not provided', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(mockComparisonData);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(explainability.compareCandidates).toHaveBeenCalledWith({
          resume_a_id: 'resume-1',
          resume_b_id: 'resume-2',
          vacancy_id: 'vacancy-123',
          use_llm: true,
        });
      });
    });
  });

  describe('Empty State', () => {
    it('should display empty state when data is null after loading', async () => {
      (explainability.compareCandidates as any).mockResolvedValue(null);

      render(
        <FactorComparisonChart
          resumeAId="resume-1"
          resumeBId="resume-2"
          vacancyId="vacancy-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No Comparison Data Available')).toBeInTheDocument();
      });

      expect(screen.getByText('Unable to compare the selected candidates. Please try again.')).toBeInTheDocument();
    });
  });
});
