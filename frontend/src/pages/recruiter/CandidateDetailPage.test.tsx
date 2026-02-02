/**
 * Tests for CandidateDetailPage Component
 *
 * Tests the candidate detail page including:
 * - Displaying candidate information with resume ID
 * - Tab navigation between Analysis and Vacancy Matches
 * - Error state when no candidate ID is provided
 * - Component rendering (AnalysisResults, VacancyMatchResults)
 * - Tab switching functionality
 * - Page header and title display
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import CandidateDetailPage from './CandidateDetailPage';

// Mock useParams
const mockUseParams = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => mockUseParams(),
  };
});

// Mock child components
vi.mock('@components/AnalysisResults', () => ({
  default: ({ resumeId }: { resumeId: string }) => (
    <div data-testid="analysis-results">Analysis Results for {resumeId}</div>
  ),
}));

vi.mock('@components/VacancyMatchResults', () => ({
  default: ({ resumeId }: { resumeId: string }) => (
    <div data-testid="vacancy-matches">Vacancy Matches for {resumeId}</div>
  ),
}));

describe('CandidateDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering - Valid Candidate ID', () => {
    it('should render the page with header', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Candidate Details')).toBeInTheDocument();
    });

    it('should display resume ID', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Resume ID: resume-123')).toBeInTheDocument();
    });

    it('should render tabs for navigation', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Analysis')).toBeInTheDocument();
      expect(screen.getByText('Vacancy Matches')).toBeInTheDocument();
    });

    it('should display Analysis tab as active by default', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();
      expect(screen.queryByTestId('vacancy-matches')).not.toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to Vacancy Matches tab when clicked', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const vacancyMatchesTab = screen.getByText('Vacancy Matches');
      fireEvent.click(vacancyMatchesTab);

      expect(screen.getByTestId('vacancy-matches')).toBeInTheDocument();
      expect(screen.queryByTestId('analysis-results')).not.toBeInTheDocument();
    });

    it('should switch back to Analysis tab when clicked', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // First switch to Vacancy Matches
      const vacancyMatchesTab = screen.getByText('Vacancy Matches');
      fireEvent.click(vacancyMatchesTab);

      // Then switch back to Analysis
      const analysisTab = screen.getByText('Analysis');
      fireEvent.click(analysisTab);

      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();
      expect(screen.queryByTestId('vacancy-matches')).not.toBeInTheDocument();
    });

    it('should maintain tab state through multiple switches', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // Start on Analysis tab
      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();

      // Switch to Vacancy Matches
      fireEvent.click(screen.getByText('Vacancy Matches'));
      expect(screen.getByTestId('vacancy-matches')).toBeInTheDocument();

      // Switch back to Analysis
      fireEvent.click(screen.getByText('Analysis'));
      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();

      // Switch to Vacancy Matches again
      fireEvent.click(screen.getByText('Vacancy Matches'));
      expect(screen.getByTestId('vacancy-matches')).toBeInTheDocument();
    });
  });

  describe('Error State - No Candidate ID', () => {
    it('should render error state when no candidate ID provided', () => {
      mockUseParams.mockReturnValue({});

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Candidate Not Found')).toBeInTheDocument();
    });

    it('should display error message when no candidate ID', () => {
      mockUseParams.mockReturnValue({});

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('No candidate ID provided. Please select a valid candidate from the candidates list.')).toBeInTheDocument();
    });

    it('should have retry button in error state', () => {
      mockUseParams.mockReturnValue({});

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const retryButton = screen.getByRole('button');
      expect(retryButton).toBeInTheDocument();
    });

    it('should not display tabs when no candidate ID', () => {
      mockUseParams.mockReturnValue({});

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.queryByText('Analysis')).not.toBeInTheDocument();
      expect(screen.queryByText('Vacancy Matches')).not.toBeInTheDocument();
    });

    it('should not display candidate details when no candidate ID', () => {
      mockUseParams.mockReturnValue({});

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.queryByText('Resume ID:')).not.toBeInTheDocument();
    });
  });

  describe('Component Rendering - Child Components', () => {
    it('should render AnalysisResults component with correct resume ID', () => {
      mockUseParams.mockReturnValue({ id: 'resume-456' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Analysis Results for resume-456')).toBeInTheDocument();
    });

    it('should render VacancyMatchResults component with correct resume ID', () => {
      mockUseParams.mockReturnValue({ id: 'resume-789' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // Switch to Vacancy Matches tab
      fireEvent.click(screen.getByText('Vacancy Matches'));

      expect(screen.getByText('Vacancy Matches for resume-789')).toBeInTheDocument();
    });

    it('should pass resume ID correctly to child components', () => {
      const resumeId = 'test-resume-id';
      mockUseParams.mockReturnValue({ id: resumeId });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // Analysis tab
      expect(screen.getByText(`Analysis Results for ${resumeId}`)).toBeInTheDocument();

      // Switch to Vacancy Matches tab
      fireEvent.click(screen.getByText('Vacancy Matches'));
      expect(screen.getByText(`Vacancy Matches for ${resumeId}`)).toBeInTheDocument();
    });
  });

  describe('Page Header', () => {
    it('should display page title with correct styling', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const title = screen.getByText('Candidate Details');
      expect(title).toBeInTheDocument();
      expect(title.tagName).toBe('H1');
    });

    it('should display resume ID in subtitle', () => {
      mockUseParams.mockReturnValue({ id: 'resume-abc123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Resume ID: resume-abc123')).toBeInTheDocument();
    });

    it('should display different resume IDs correctly', () => {
      mockUseParams.mockReturnValue({ id: 'resume-xyz-999' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Resume ID: resume-xyz-999')).toBeInTheDocument();
    });
  });

  describe('Tab Functionality', () => {
    it('should have correct aria-label on tabs', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const tabs = screen.getByRole('tablist');
      expect(tabs).toHaveAttribute('aria-label', 'candidate details tabs');
    });

    it('should render both tabs', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBe(2);
    });

    it('should change active tab styling', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const analysisTab = screen.getByRole('tab', { name: 'Analysis' });
      const vacancyMatchesTab = screen.getByRole('tab', { name: 'Vacancy Matches' });

      // Initially Analysis tab is active
      expect(analysisTab).toHaveAttribute('aria-selected', 'true');
      expect(vacancyMatchesTab).toHaveAttribute('aria-selected', 'false');

      // After clicking Vacancy Matches
      fireEvent.click(vacancyMatchesTab);
      expect(analysisTab).toHaveAttribute('aria-selected', 'false');
      expect(vacancyMatchesTab).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('Layout and Structure', () => {
    it('should use Container component', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      const { container } = render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const containers = container.querySelectorAll('.MuiContainer-root');
      expect(containers.length).toBeGreaterThan(0);
    });

    it('should use Box components for layout', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      const { container } = render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const boxes = container.querySelectorAll('.MuiBox-root');
      expect(boxes.length).toBeGreaterThan(0);
    });

    it('should render page transition wrapper', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // PageTransition should render its children
      expect(screen.getByText('Candidate Details')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string candidate ID', () => {
      mockUseParams.mockReturnValue({ id: '' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Candidate Not Found')).toBeInTheDocument();
    });

    it('should handle special characters in resume ID', () => {
      const specialId = 'resume-123-abc_#@!';
      mockUseParams.mockReturnValue({ id: specialId });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText(`Resume ID: ${specialId}`)).toBeInTheDocument();
    });

    it('should handle very long resume IDs', () => {
      const longId = 'resume-' + 'a'.repeat(100);
      mockUseParams.mockReturnValue({ id: longId });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText(`Resume ID: ${longId}`)).toBeInTheDocument();
    });

    it('should handle numeric resume IDs', () => {
      const numericId = '123456789';
      mockUseParams.mockReturnValue({ id: numericId });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText(`Resume ID: ${numericId}`)).toBeInTheDocument();
    });

    it('should handle undefined id parameter', () => {
      mockUseParams.mockReturnValue({ id: undefined });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Candidate Not Found')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should allow tab switching without errors', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // Rapid tab switching
      fireEvent.click(screen.getByText('Vacancy Matches'));
      fireEvent.click(screen.getByText('Analysis'));
      fireEvent.click(screen.getByText('Vacancy Matches'));
      fireEvent.click(screen.getByText('Analysis'));

      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();
    });

    it('should maintain state when switching tabs', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      // Switch to Vacancy Matches
      fireEvent.click(screen.getByText('Vacancy Matches'));
      expect(screen.getByTestId('vacancy-matches')).toBeInTheDocument();

      // Switch back to Analysis
      fireEvent.click(screen.getByText('Analysis'));
      expect(screen.getByTestId('analysis-results')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toBeInTheDocument();
      expect(h1).toHaveTextContent('Candidate Details');
    });

    it('should have accessible tabs', () => {
      mockUseParams.mockReturnValue({ id: 'resume-123' });

      render(
        <BrowserRouter>
          <CandidateDetailPage />
        </BrowserRouter>
      );

      const tablist = screen.getByRole('tablist');
      expect(tablist).toBeInTheDocument();

      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBe(2);
      expect(tabs[0]).toHaveAccessibleName();
      expect(tabs[1]).toHaveAccessibleName();
    });
  });
});
