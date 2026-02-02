/**
 * Tests for VacancyDetailPage Component
 *
 * Tests the vacancy detail page including:
 * - Displaying vacancy details with all fields
 * - Loading and error states
 * - Navigation to candidates and edit pages
 * - Display of industry, location, work format, salary
 * - Required skills display as chips
 * - Description rendering with proper formatting
 * - Action buttons functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { VacancyDetailPage } from './VacancyDetailPage';
import * as useJobsHook from '../../hooks/useJobs';

// Mock the hooks
vi.mock('../../hooks/useJobs');

// Mock navigate
const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
    useParams: () => ({ id: 'vacancy-123' }),
  };
});

describe('VacancyDetailPage', () => {
  const mockVacancy = {
    id: 'vacancy-123',
    title: 'Senior Software Engineer',
    description: 'We are looking for a talented software engineer to join our team.',
    required_skills: ['React', 'TypeScript', 'Node.js', 'AWS', 'Docker'],
    min_experience_months: 60,
    industry: 'Technology',
    work_format: 'remote',
    location: 'San Francisco, CA',
    salary_min: 120000,
    salary_max: 180000,
    employment_type: 'Full-time',
  };

  let queryClient: QueryClient;

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the page with vacancy title', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    });

    it('should display industry information', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('should display location information', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    });

    it('should display work format and experience', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/remote.*5\+ years/)).toBeInTheDocument();
    });

    it('should display salary information', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/120,000.*180,000/)).toBeInTheDocument();
    });

    it('should display required skills as chips', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Node.js')).toBeInTheDocument();
      expect(screen.getByText('AWS')).toBeInTheDocument();
      expect(screen.getByText('Docker')).toBeInTheDocument();
    });

    it('should display description with proper formatting', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('We are looking for a talented software engineer to join our team.')).toBeInTheDocument();
    });

    it('should display section headers', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Required Skills')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading state when isLoading is true', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading vacancy details...')).toBeInTheDocument();
    });

    it('should not display content when loading', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.queryByText('Senior Software Engineer')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error state when error exists', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Not found'),
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Vacancy Not Found')).toBeInTheDocument();
      expect(
        screen.getByText("The vacancy you're looking for doesn't exist or you don't have permission to view it.")
      ).toBeInTheDocument();
    });

    it('should render error state when vacancy is null', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Vacancy Not Found')).toBeInTheDocument();
    });

    it('should have back button in error state', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Not found'),
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const retryButton = screen.getByRole('button');
      expect(retryButton).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should display View Candidates button', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: 'View Candidates' })).toBeInTheDocument();
    });

    it('should display Edit Vacancy button', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: 'Edit Vacancy' })).toBeInTheDocument();
    });

    it('should navigate to candidates page when View Candidates is clicked', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const viewCandidatesButton = screen.getByRole('button', { name: 'View Candidates' });
      fireEvent.click(viewCandidatesButton);

      expect(mockedNavigate).toHaveBeenCalledWith('/recruiter/candidates');
    });

    it('should navigate to edit page when Edit Vacancy is clicked', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const editButton = screen.getByRole('button', { name: 'Edit Vacancy' });
      fireEvent.click(editButton);

      expect(mockedNavigate).toHaveBeenCalledWith('/recruiter/vacancies/vacancy-123/edit');
    });
  });

  describe('Layout and Structure', () => {
    it('should render in paper container', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      const { container } = render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const paper = container.querySelector('.MuiPaper-root');
      expect(paper).toBeInTheDocument();
    });

    it('should render dividers between sections', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      const { container } = render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const dividers = container.querySelectorAll('.MuiDivider-root');
      expect(dividers.length).toBeGreaterThan(0);
    });

    it('should use stack layout', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      const { container } = render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });
  });

  describe('Icons Display', () => {
    it('should display location icon', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should display work icon', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should display money icon for salary', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle vacancy with no salary max', () => {
      const vacancyWithoutMaxSalary = { ...mockVacancy, salary_max: undefined };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithoutMaxSalary,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/120,000/)).toBeInTheDocument();
    });

    it('should handle vacancy with no salary information', () => {
      const vacancyWithoutSalary = { ...mockVacancy, salary_min: undefined, salary_max: undefined };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithoutSalary,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.queryByText(/\$/)).not.toBeInTheDocument();
    });

    it('should handle vacancy with zero experience', () => {
      const vacancyWithNoExperience = { ...mockVacancy, min_experience_months: 0 };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithNoExperience,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/remote/)).toBeInTheDocument();
    });

    it('should handle vacancy with no location', () => {
      const vacancyWithoutLocation = { ...mockVacancy, location: undefined };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithoutLocation,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.queryByText('San Francisco, CA')).not.toBeInTheDocument();
    });

    it('should handle vacancy with no industry', () => {
      const vacancyWithoutIndustry = { ...mockVacancy, industry: undefined };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithoutIndustry,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.queryByText('Technology')).not.toBeInTheDocument();
    });

    it('should handle vacancy with empty skills array', () => {
      const vacancyWithNoSkills = { ...mockVacancy, required_skills: [] };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithNoSkills,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Required Skills')).toBeInTheDocument();
    });

    it('should handle multiline description', () => {
      const vacancyWithMultilineDescription = {
        ...mockVacancy,
        description: 'Line 1\nLine 2\nLine 3',
      };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: vacancyWithMultilineDescription,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Line 1')).toBeInTheDocument();
      expect(screen.getByText('Line 2')).toBeInTheDocument();
      expect(screen.getByText('Line 3')).toBeInTheDocument();
    });
  });

  describe('Work Format Display', () => {
    it('should display remote work format', () => {
      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: mockVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/remote/)).toBeInTheDocument();
    });

    it('should display hybrid work format', () => {
      const hybridVacancy = { ...mockVacancy, work_format: 'hybrid' };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: hybridVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/hybrid/)).toBeInTheDocument();
    });

    it('should display office work format', () => {
      const officeVacancy = { ...mockVacancy, work_format: 'office' };

      vi.mocked(useJobsHook.useJob).mockReturnValue({
        data: officeVacancy,
        isLoading: false,
        error: null,
      } as any);

      render(<VacancyDetailPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/office/)).toBeInTheDocument();
    });
  });
});
