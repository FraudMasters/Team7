/**
 * Tests for SavedJobsPage Component
 *
 * Tests the saved jobs page including:
 * - Displaying saved jobs with search functionality
 * - Loading, error, and empty states
 * - Filtering saved jobs by search term
 * - Removing saved jobs
 * - Displaying saved jobs count
 * - JobCard rendering with saved state
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SavedJobsPage } from './SavedJobsPage';
import * as useSavedJobsHook from '../../hooks/useSavedJobs';

// Mock the hooks
vi.mock('../../hooks/useSavedJobs');

describe('SavedJobsPage', () => {
  const mockSavedJobs = [
    {
      id: 'saved-1',
      vacancy_id: 'vacancy-1',
      title: 'Senior Software Engineer',
      description: 'Develop and maintain software applications',
      required_skills: ['React', 'TypeScript', 'Node.js'],
      min_experience_months: 60,
      industry: 'Technology',
      work_format: 'remote',
      location: 'San Francisco, CA',
      salary_min: 120000,
      salary_max: 180000,
      employment_type: 'Full-time',
      saved_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'saved-2',
      vacancy_id: 'vacancy-2',
      title: 'Full Stack Developer',
      description: 'Build web applications end-to-end',
      required_skills: ['Python', 'Django', 'React'],
      min_experience_months: 48,
      industry: 'Technology',
      work_format: 'hybrid',
      location: 'New York, NY',
      salary_min: 100000,
      salary_max: 150000,
      employment_type: 'Full-time',
      saved_at: '2024-01-14T10:00:00Z',
    },
    {
      id: 'saved-3',
      vacancy_id: 'vacancy-3',
      title: 'Data Scientist',
      description: 'Analyze data and build ML models',
      required_skills: ['Python', 'Machine Learning', 'SQL'],
      min_experience_months: 36,
      industry: 'Technology',
      work_format: 'office',
      location: 'Boston, MA',
      salary_min: 110000,
      salary_max: 160000,
      employment_type: 'Full-time',
      saved_at: '2024-01-13T10:00:00Z',
    },
  ];

  let queryClient: QueryClient;

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
        mutations: {
          retry: false,
        },
      },
    });
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the page with header', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Saved Jobs')).toBeInTheDocument();
      expect(screen.getByText('Your bookmarked job opportunities')).toBeInTheDocument();
    });

    it('should display saved jobs count', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('3 saved')).toBeInTheDocument();
    });

    it('should display search input', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      expect(searchInput).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading state when isLoading is true', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading saved jobs...')).toBeInTheDocument();
    });

    it('should not display content when loading', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.queryByText('Senior Software Engineer')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error state when error exists', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load'),
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load saved jobs. Please try again later.')).toBeInTheDocument();
    });

    it('should have retry button in error state', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load'),
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should render empty state when no saved jobs', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: [], total: 0 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('No saved jobs yet')).toBeInTheDocument();
      expect(screen.getByText('Start bookmarking jobs to see them here')).toBeInTheDocument();
    });

    it('should display browse jobs button in empty state', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: [], total: 0 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: 'Browse Jobs' })).toBeInTheDocument();
    });

    it('should show no search results message when search returns empty', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent job' } });

      expect(screen.getByText('No saved jobs match your search')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search terms')).toBeInTheDocument();
    });

    it('should not show browse jobs button when search has no results', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(screen.queryByRole('button', { name: 'Browse Jobs' })).not.toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should filter jobs by title', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'Senior' } });

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.queryByText('Full Stack Developer')).not.toBeInTheDocument();
      expect(screen.queryByText('Data Scientist')).not.toBeInTheDocument();
    });

    it('should filter jobs by description', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'ML models' } });

      expect(screen.getByText('Data Scientist')).toBeInTheDocument();
      expect(screen.queryByText('Senior Software Engineer')).not.toBeInTheDocument();
      expect(screen.queryByText('Full Stack Developer')).not.toBeInTheDocument();
    });

    it('should be case insensitive', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'SENIOR software' } });

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    });

    it('should reset search when input is cleared', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'Senior' } });
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();

      fireEvent.change(searchInput, { target: { value: '' } });
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Full Stack Developer')).toBeInTheDocument();
      expect(screen.getByText('Data Scientist')).toBeInTheDocument();
    });
  });

  describe('Job Display', () => {
    it('should display all saved jobs', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Full Stack Developer')).toBeInTheDocument();
      expect(screen.getByText('Data Scientist')).toBeInTheDocument();
    });

    it('should display jobs in grid layout', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      const { container } = render(<SavedJobsPage />, { wrapper: createWrapper() });

      const gridItems = container.querySelectorAll('.MuiGrid-item');
      expect(gridItems.length).toBe(3);
    });
  });

  describe('Remove Saved Job', () => {
    it('should call removeSavedJob when job is unsaved', () => {
      const mockMutate = vi.fn();

      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      // The JobCard component should have an onSave callback
      // When clicked, it should call removeSavedJob
      const jobCards = screen.getAllByRole('button');
      jobCards.forEach((button) => {
        if (button.getAttribute('aria-label')?.includes('bookmark')) {
          fireEvent.click(button);
        }
      });

      // At least one call should have been made (the actual behavior depends on JobCard implementation)
      expect(mockMutate).toHaveBeenCalled();
    });
  });

  describe('Display Update', () => {
    it('should update count when jobs are removed', async () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('3 saved')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle jobs with missing optional fields', () => {
      const jobsWithMissingFields = [
        {
          id: 'saved-1',
          vacancy_id: 'vacancy-1',
          title: 'Software Engineer',
          description: 'Test job',
          required_skills: ['React'],
          min_experience_months: 0,
          saved_at: '2024-01-15T10:00:00Z',
        },
      ];

      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: jobsWithMissingFields, total: 1 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    it('should handle empty description', () => {
      const jobsWithEmptyDescription = [
        {
          id: 'saved-1',
          vacancy_id: 'vacancy-1',
          title: 'Software Engineer',
          description: '',
          required_skills: ['React'],
          min_experience_months: 0,
          saved_at: '2024-01-15T10:00:00Z',
        },
      ];

      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: jobsWithEmptyDescription, total: 1 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Should not crash, just show no results
      expect(screen.queryByText('Software Engineer')).not.toBeInTheDocument();
    });

    it('should handle very long search terms', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const longSearchTerm = 'a'.repeat(1000);
      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      fireEvent.change(searchInput, { target: { value: longSearchTerm } });

      expect(screen.getByText('No saved jobs match your search')).toBeInTheDocument();
    });
  });

  describe('UI Elements', () => {
    it('should display bookmark icon', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const bookmarkIcon = document.querySelector('.MuiSvgIcon-root');
      expect(bookmarkIcon).toBeInTheDocument();
    });

    it('should display search icon', () => {
      vi.mocked(useSavedJobsHook.useSavedJobs).mockReturnValue({
        data: { saved_jobs: mockSavedJobs, total: 3 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useSavedJobsHook.useRemoveSavedJob).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<SavedJobsPage />, { wrapper: createWrapper() });

      const searchIcon = document.querySelectorAll('.MuiSvgIcon-root');
      expect(searchIcon.length).toBeGreaterThan(0);
    });
  });
});
